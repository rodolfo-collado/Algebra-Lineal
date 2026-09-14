#requires -Version 5.1
<# Prueba real en una cuenta Windows sin una instalación previa de Álgebra Lineal.
   Instala, abre el acceso directo, resuelve por HTTP, cierra, reabre y desinstala.
   La revisión visual de pywebview se realiza además de esta prueba automatizada. #>
[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$InstallerPath)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$installer = (Resolve-Path -LiteralPath $InstallerPath).Path
$registryPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D0455B79-7F5E-4C78-9F3B-F47187E9A83A}_is1'
$startShortcut = Join-Path ([Environment]::GetFolderPath('Programs')) 'Álgebra Lineal\Álgebra Lineal.lnk'
$desktopShortcut = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Álgebra Lineal.lnk'
foreach ($existing in @($registryPath, $startShortcut, $desktopShortcut)) {
    if (Test-Path -LiteralPath $existing) { throw "Ya existe $existing. Usa una cuenta limpia para esta prueba." }
}
$installRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs'))
$installDirectory = [IO.Path]::GetFullPath((Join-Path $installRoot ('AlgebraLineal-Smoke-' + [guid]::NewGuid().ToString('N'))))
if (-not $installDirectory.StartsWith($installRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'La carpeta de prueba queda fuera de Programs.'
}
$process = $null

function Wait-AppUrl {
    param([Diagnostics.Process]$AppProcess)
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        if ($AppProcess.HasExited) { throw 'El ejecutable terminó antes de abrir el servidor.' }
        $listeners = @(Get-NetTCPConnection -State Listen -OwningProcess $AppProcess.Id -ErrorAction SilentlyContinue)
        foreach ($listener in $listeners) {
            if ($listener.LocalAddress -ne '127.0.0.1') { throw 'El servidor escucha fuera de loopback.' }
            $url = "http://127.0.0.1:$($listener.LocalPort)/"
            try {
                $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2
                if ($response.StatusCode -eq 200) { return $url }
            } catch { }
        }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)
    throw 'Django no respondió dentro de 30 segundos.'
}

try {
    $setup = Start-Process -FilePath $installer -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/TASKS=desktopicon', ('/DIR="' + $installDirectory + '"')) -WindowStyle Hidden -PassThru -Wait
    if ($setup.ExitCode -ne 0) { throw "El instalador falló: $($setup.ExitCode)" }
    $appPath = Join-Path $installDirectory 'AlgebraLineal.exe'
    foreach ($path in @($appPath, $startShortcut, $desktopShortcut, $registryPath)) {
        if (-not (Test-Path -LiteralPath $path)) { throw "El instalador no creó $path" }
    }
    $shell = New-Object -ComObject WScript.Shell
    foreach ($shortcutPath in @($startShortcut, $desktopShortcut)) {
        $shortcut = $shell.CreateShortcut($shortcutPath)
        if ($shortcut.TargetPath -ne $appPath -or $shortcut.WorkingDirectory -ne $installDirectory) {
            throw "El acceso directo depende de una ruta incorrecta: $shortcutPath"
        }
    }

    # El subsistema PE debe ser Windows GUI (2), no consola (3).
    $bytes = [IO.File]::ReadAllBytes($appPath)
    $peOffset = [BitConverter]::ToInt32($bytes, 0x3c)
    if ([BitConverter]::ToUInt16($bytes, $peOffset + 24 + 68) -ne 2) { throw 'El ejecutable no es windowed.' }

    for ($attempt = 1; $attempt -le 2; $attempt++) {
        Start-Process -FilePath $startShortcut -WorkingDirectory $installDirectory -WindowStyle Normal
        $deadline = [DateTime]::UtcNow.AddSeconds(15)
        do {
            $candidates = @(Get-Process AlgebraLineal -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $appPath })
            if ($candidates.Count -eq 1) { $process = $candidates[0]; break }
            Start-Sleep -Milliseconds 250
        } while ([DateTime]::UtcNow -lt $deadline)
        if (-not $process -or $process.HasExited) { throw 'El acceso directo no abrió la aplicación.' }
        # Conserva el handle antes del cierre para poder consultar ExitCode
        # aunque el proceso se haya obtenido mediante Get-Process.
        $null = $process.Handle
        $url = Wait-AppUrl $process
        # Django responde antes de que .NET/WebView2 termine de crear la ventana.
        $deadline = [DateTime]::UtcNow.AddSeconds(30)
        do {
            $process.Refresh()
            if ($process.HasExited) { throw 'La aplicación terminó antes de crear la ventana.' }
            if ($process.MainWindowHandle -ne [IntPtr]::Zero) { break }
            Start-Sleep -Milliseconds 250
        } while ([DateTime]::UtcNow -lt $deadline)
        if ($process.MainWindowHandle -eq [IntPtr]::Zero) { throw 'pywebview no creó la ventana nativa.' }
        $homeResponse = Invoke-WebRequest -UseBasicParsing -Uri $url
        if (-not $homeResponse.Content.Contains('href="/sistemas/"')) { throw 'Inicio no enlaza al módulo de sistemas.' }
        $systemsUrl = $url + 'sistemas/'
        foreach ($method in @('gauss', 'gauss_jordan')) {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $systemsUrl -SessionVariable webSession
            $csrf = [regex]::Match($response.Content, 'name="csrfmiddlewaretoken" value="([^"]+)"').Groups[1].Value
            if (-not $csrf) { throw 'Django no entregó un token CSRF.' }
            $response = Invoke-WebRequest -UseBasicParsing -Uri $systemsUrl -Method Post -WebSession $webSession -Headers @{ Referer = $systemsUrl } -Body @{
                csrfmiddlewaretoken = $csrf
                tipo_entrada = 'sistema'
                metodo = $method
                sistema = 'x1 + 2x2 + x3 = 4; x3 = 2'
            }
            $text = [regex]::Replace($response.Content, '<[^>]+>', '')
            foreach ($expected in @('Columnas pivote: C1, C3', 'Consistente de soluciones infinitas', 'x3 = 2')) {
                if (-not $text.Contains($expected)) { throw "Falta '$expected' en $method ($url)." }
            }
        }
        foreach ($asset in @('styles.css', 'matriz.js', 'tema.js', 'navigation.js', 'mark.svg')) {
            $response = Invoke-WebRequest -UseBasicParsing -Uri ($url + 'static/calculadora/' + $asset)
            if ($response.StatusCode -ne 200) { throw "No se sirvió el recurso $asset" }
        }
        if (-not $process.CloseMainWindow()) { throw 'La ventana nativa no respondió al cierre.' }
        if (-not $process.WaitForExit(10000)) { throw 'La aplicación no terminó limpiamente.' }
        if ($process.ExitCode -ne 0) { throw "La aplicación terminó con código $($process.ExitCode)" }
        $listener = @(Get-NetTCPConnection -State Listen -OwningProcess $process.Id -ErrorAction SilentlyContinue)
        if ($listener.Count) { throw 'El servidor sigue escuchando después del cierre.' }
        $process = $null
        Write-Host "Apertura ${attempt}: acceso directo, Django/Waitress, ambos métodos, recursos y cierre OK."
    }
} finally {
    if ($process -and -not $process.HasExited) {
        $process.CloseMainWindow() | Out-Null
        if (-not $process.WaitForExit(10000)) { $process.Kill(); $process.WaitForExit() }
    }
    $uninstaller = Join-Path $installDirectory 'unins000.exe'
    if (Test-Path -LiteralPath $uninstaller) {
        $uninstall = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') -WindowStyle Hidden -PassThru -Wait
        if ($uninstall.ExitCode -ne 0) { throw "La desinstalación falló: $($uninstall.ExitCode)" }
    }
}
foreach ($path in @($installDirectory, $registryPath, $startShortcut, $desktopShortcut)) {
    if (Test-Path -LiteralPath $path) { throw "La desinstalación dejó $path" }
}
Write-Host "Distribución verificada fuera del repositorio y desinstalada: $installDirectory"
