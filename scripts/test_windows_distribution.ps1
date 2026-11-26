#requires -Version 5.1
<# Prueba real en una cuenta limpia de Windows sin una instalación previa de PyGebra.
   Instala, abre el acceso directo, resuelve por HTTP, cierra, reabre y desinstala.
   -PreviousInstallerPath prueba además la actualización desde una release publicada: la
   histórica 0.8.0 (Álgebra Lineal) o cualquier PyGebra posterior. Comprueba que no quedan
   archivos obsoletos en _internal, que no se duplican accesos ni registros y que la
   identidad (AppId, AUMID) se conserva.
   -AutoUpdate recorre la autoactualización con el actualizador de la versión anterior:
   desde su ventana abierta busca, descarga, verifica e instala el candidato, que debe
   cerrarla, actualizar y reabrirla con las mismas preferencias y accesos.
     Real: la base publicada instalada y abierta (WebView2, Waitress, mutex), su código de
     actualizaciones/ (consulta, descarga, SHA-256, lanzamiento de Inno, cierre propio y
     limpieza de la descarga), el instalador candidato con /SILENT /ACTUALIZAR=1 y la
     reapertura. Los pasos se piden por HTTP a los mismos endpoints que usa el botón.
     Simulado: GitHub. Un proxy HTTPS local (HTTPS_PROXY) responde como api.github.com y
     github.com con el candidato y su SHA256SUMS.txt, firmado por una CA de prueba que se
     instala en LocalMachine\Root solo durante la prueba. Por eso -AutoUpdate se niega a
     correr fuera de GitHub Actions o Windows Sandbox. También ensaya dos fallos: GitHub
     caído (error_conexion) y un SHA256SUMS.txt que no coincide (checksum_invalido).
   La revisión visual de pywebview se realiza además de esta prueba automatizada. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$InstallerPath,
    [string]$PreviousInstallerPath,
    [switch]$PreviousDesktopIcon,
    [switch]$AutoUpdate,
    [string]$InstallerSha256
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($AutoUpdate -and (-not $PreviousInstallerPath -or $InstallerSha256 -notmatch '^[0-9a-fA-F]{64}$')) {
    throw '-AutoUpdate requiere -PreviousInstallerPath y el SHA-256 del candidato en -InstallerSha256.'
}
$installer = (Resolve-Path -LiteralPath $InstallerPath).Path
$preferencesFile = Join-Path $env:LOCALAPPDATA 'PyGebra\preferencias.json'
if ($AutoUpdate) {
    # La CA de prueba y las preferencias tocan la cuenta: solo en un Windows desechable.
    if ($env:GITHUB_ACTIONS -ne 'true' -and $env:USERNAME -ne 'WDAGUtilityAccount') {
        throw '-AutoUpdate instala una CA de prueba: ejecútalo solo en GitHub Actions o en Windows Sandbox.'
    }
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw '-AutoUpdate necesita permisos de administrador para confiar temporalmente en la CA de prueba.'
    }
    if (Test-Path -LiteralPath $preferencesFile) { throw "Ya existe $preferencesFile. Usa una cuenta limpia para esta prueba." }
    if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash -ne $InstallerSha256.ToUpperInvariant()) {
        throw 'El SHA-256 del instalador candidato no coincide con -InstallerSha256.'
    }
    if ((Split-Path $installer -Leaf) -notmatch '^PyGebra-Setup-(\d+\.\d+\.\d+)\.exe$') { throw 'El candidato no se llama PyGebra-Setup-X.Y.Z.exe.' }
    $candidateVersion = $Matches[1]
}
$fakeGitHub = $null
$registryPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D0455B79-7F5E-4C78-9F3B-F47187E9A83A}_is1'
$startShortcut = Join-Path ([Environment]::GetFolderPath('Programs')) 'PyGebra\PyGebra.lnk'
$desktopShortcut = Join-Path ([Environment]::GetFolderPath('Desktop')) 'PyGebra.lnk'
$legacyStartShortcut = Join-Path ([Environment]::GetFolderPath('Programs')) 'Álgebra Lineal\Álgebra Lineal.lnk'
$legacyDesktopShortcut = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Álgebra Lineal.lnk'
$legacyShortcuts = @($legacyStartShortcut, $legacyDesktopShortcut)
$expectsDesktopIcon = -not $AutoUpdate -or $PreviousDesktopIcon
$expectedShortcuts = @($startShortcut)
if ($expectsDesktopIcon) { $expectedShortcuts += $desktopShortcut }
foreach ($existing in @($registryPath, $startShortcut, $desktopShortcut) + $legacyShortcuts) {
    if (Test-Path -LiteralPath $existing) { throw "Ya existe $existing. Usa una cuenta limpia para esta prueba." }
}
$installRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs'))
$installDirectory = [IO.Path]::GetFullPath((Join-Path $installRoot ('AlgebraLineal-Smoke-' + [guid]::NewGuid().ToString('N'))))
if (-not $installDirectory.StartsWith($installRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'La carpeta de prueba queda fuera de Programs.'
}
$process = $null
$setup = $null
$appPath = Join-Path $installDirectory 'AlgebraLineal.exe'
$unrelatedFile = $null
$obsoleteFile = $null
$uninstallRoot = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall'

function Get-PyGebraRegistrations {
    return @(Get-ChildItem -LiteralPath $uninstallRoot -ErrorAction SilentlyContinue | ForEach-Object {
        Get-ItemProperty -LiteralPath $_.PSPath } | Where-Object {
        $_.PSObject.Properties['DisplayName'] -and $_.DisplayName -in @('PyGebra', 'Álgebra Lineal') })
}

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

function Wait-AppProcess {
    param([int]$Seconds = 15)
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    do {
        $candidates = @(Get-Process AlgebraLineal -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $appPath })
        if ($candidates.Count -eq 1) {
            # Guarda el handle para poder comprobar el código de salida tras el cierre.
            $null = $candidates[0].Handle
            return $candidates[0]
        }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)
    throw 'No se encontró una instancia única de PyGebra en la carpeta de prueba.'
}

function Wait-AppWindow {
    param([Diagnostics.Process]$AppProcess)
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        $AppProcess.Refresh()
        if ($AppProcess.HasExited) { throw 'La aplicación terminó antes de crear la ventana.' }
        if ($AppProcess.MainWindowHandle -ne [IntPtr]::Zero) {
            if ($AppProcess.MainWindowTitle -ne 'PyGebra') { throw 'La ventana no se presenta como PyGebra.' }
            return
        }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)
    throw 'pywebview no creó la ventana nativa.'
}

# Texto de cada celda de una tabla de matriz; el formato Exacto/Decimal envuelve los
# valores no enteros en <span data-numeric>, así que se retiran las etiquetas internas.
function Get-CellTexts {
    param([string]$TableHtml)
    return @([regex]::Matches($TableHtml, '(?s)<td[^>]*>(.*?)</td>') | ForEach-Object {
        [regex]::Replace($_.Groups[1].Value, '<[^>]+>', '').Trim()
    })
}

# GitHub simulado para -AutoUpdate: proxy HTTPS (CONNECT) que termina TLS con un certificado
# de api.github.com/github.com firmado por una CA temporal y sirve la release del candidato.
# Responde a las mismas rutas que construye actualizador/releases.py; cualquier otra es 404.
function Start-FakeGitHub {
    param([string]$Version, [string]$InstallerFile, [string]$Sha256)
    $name = "PyGebra-Setup-$Version.exe"
    $sums = "$($Sha256.ToLowerInvariant())  $name`n"
    $repository = 'Collado-Labs/Algebra-Lineal'
    $state = [hashtable]::Synchronized(@{
        ApiRoute = "api.github.com/repos/$repository/releases/latest"
        SumsRoute = "github.com/$repository/releases/download/v$Version/SHA256SUMS.txt"
        InstallerRoute = "github.com/$repository/releases/download/v$Version/$name"
        ApiDown = $false
        BadSums = $false
        Sums = $sums
        # Misma longitud que la buena, para que el fallo sea del SHA-256 y no del tamaño.
        WrongSums = ('0' * 64) + "  $name`n"
        InstallerFile = $InstallerFile
        Log = [Collections.ArrayList]::Synchronized((New-Object Collections.ArrayList))
        Errors = [Collections.ArrayList]::Synchronized((New-Object Collections.ArrayList))
    })
    $state.ApiJson = ConvertTo-Json -Compress -Depth 4 @{
        tag_name = "v$Version"; draft = $false; prerelease = $false
        assets = @(@{ name = $name; size = (Get-Item -LiteralPath $InstallerFile).Length },
                   @{ name = 'SHA256SUMS.txt'; size = [Text.Encoding]::UTF8.GetByteCount($sums) })
    }
    $server = @{ State = $state; Ca = $null; Leaf = $null; Listener = $null; Shell = $null; Handle = $null }
    $lifetime = (Get-Date).AddHours(2)
    $server.Ca = New-SelfSignedCertificate -Subject 'CN=PyGebra CA temporal de pruebas' -CertStoreLocation 'Cert:\CurrentUser\My' -KeyUsage CertSign, CRLSign, DigitalSignature -TextExtension @('2.5.29.19={critical}{text}ca=1&pathlength=0') -NotAfter $lifetime
    $server.Leaf = New-SelfSignedCertificate -DnsName 'api.github.com', 'github.com' -Signer $server.Ca -CertStoreLocation 'Cert:\CurrentUser\My' -NotAfter $lifetime
    # LocalMachine\Root no pide confirmación interactiva (CurrentUser\Root sí).
    $root = New-Object Security.Cryptography.X509Certificates.X509Store('Root', 'LocalMachine')
    $root.Open('ReadWrite')
    try { $root.Add((New-Object Security.Cryptography.X509Certificates.X509Certificate2(, $server.Ca.RawData))) } finally { $root.Close() }
    $server.Listener = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback, 0)
    $server.Listener.Start()
    $server.Port = $server.Listener.LocalEndpoint.Port
    $serve = {
        param($Listener, $Certificate, $State)
        function Read-Head([IO.Stream]$Stream) {
            $bytes = New-Object IO.MemoryStream
            while ($bytes.Length -lt 16384) {
                $value = $Stream.ReadByte()
                if ($value -lt 0) { break }
                $bytes.WriteByte([byte]$value)
                $n = $bytes.Length
                $buffer = $bytes.GetBuffer()
                if ($n -ge 4 -and $buffer[$n - 4] -eq 13 -and $buffer[$n - 3] -eq 10 -and $buffer[$n - 2] -eq 13 -and $buffer[$n - 1] -eq 10) { break }
            }
            return [Text.Encoding]::ASCII.GetString($bytes.ToArray())
        }
        while ($true) {
            try { $client = $Listener.AcceptTcpClient() } catch { break }
            try {
                $network = $client.GetStream()
                $connect = Read-Head $network
                if ($connect -notmatch '^CONNECT ([A-Za-z0-9.-]+):443 HTTP/1\.[01]\r\n') { throw "El proxy recibió algo distinto de CONNECT: $($connect.Split("`r")[0])" }
                $hostName = $Matches[1]
                $established = [Text.Encoding]::ASCII.GetBytes("HTTP/1.1 200 Connection established`r`n`r`n")
                $network.Write($established, 0, $established.Length)
                $tls = New-Object Net.Security.SslStream($network, $false)
                $tls.AuthenticateAsServer($Certificate, $false, [Security.Authentication.SslProtocols]::Tls12, $false)
                $request = Read-Head $tls
                $route = $hostName + ($request -split ' ')[1]
                [void]$State.Log.Add($route)
                $status, $text, $file = 404, 'No existe', $null
                if ($route -eq $State.ApiRoute) {
                    if ($State.ApiDown) { $status, $text = 503, 'GitHub simulado no disponible' } else { $status, $text = 200, $State.ApiJson }
                } elseif ($route -eq $State.SumsRoute) {
                    $status = 200
                    $text = if ($State.BadSums) { $State.WrongSums } else { $State.Sums }
                } elseif ($route -eq $State.InstallerRoute) {
                    $status, $text, $file = 200, $null, $State.InstallerFile
                }
                $body = if ($file) { $null } else { [Text.Encoding]::UTF8.GetBytes($text) }
                $length = if ($file) { (Get-Item -LiteralPath $file).Length } else { $body.Length }
                $reason = @{ 200 = 'OK'; 404 = 'Not Found'; 503 = 'Service Unavailable' }[$status]
                $head = [Text.Encoding]::ASCII.GetBytes("HTTP/1.1 $status $reason`r`nContent-Type: application/octet-stream`r`nContent-Length: $length`r`nConnection: close`r`n`r`n")
                $tls.Write($head, 0, $head.Length)
                if ($file) {
                    $source = [IO.File]::OpenRead($file)
                    try { $source.CopyTo($tls) } finally { $source.Dispose() }
                } else {
                    $tls.Write($body, 0, $body.Length)
                }
                $tls.Flush()
            } catch {
                [void]$State.Errors.Add($_.Exception.Message)
            } finally {
                $client.Close()
            }
        }
    }
    $server.Shell = [PowerShell]::Create()
    [void]$server.Shell.AddScript($serve).AddArgument($server.Listener).AddArgument($server.Leaf).AddArgument($state)
    $server.Handle = $server.Shell.BeginInvoke()
    return $server
}

function Stop-FakeGitHub {
    param($Server)
    if ($Server.Listener) { $Server.Listener.Stop() }
    if ($Server.Shell) {
        if ($Server.Handle) { $Server.Handle.AsyncWaitHandle.WaitOne(10000) | Out-Null }
        $Server.Shell.Dispose()
    }
    if ($Server.Ca) {
        $root = New-Object Security.Cryptography.X509Certificates.X509Store('Root', 'LocalMachine')
        $root.Open('ReadWrite')
        try {
            foreach ($trusted in @($root.Certificates.Find('FindByThumbprint', $Server.Ca.Thumbprint, $false))) { $root.Remove($trusted) }
        } finally { $root.Close() }
    }
    foreach ($certificate in @($Server.Leaf, $Server.Ca)) {
        if ($certificate) { Remove-Item -LiteralPath ('Cert:\CurrentUser\My\' + $certificate.Thumbprint) -ErrorAction SilentlyContinue }
    }
}

# Un paso del actualizador de la app abierta, igual que el botón de actualizaciones.js.
function Invoke-UpdateAction {
    param([string]$Url, $Session, [string]$Token, [string]$Action)
    $response = Invoke-WebRequest -UseBasicParsing -Uri ($Url + "actualizaciones/$Action/") -Method Post -WebSession $Session -Headers @{
        Referer = $Url + 'actualizaciones/'
        'X-CSRFToken' = $Token
    }
    return $response.Content | ConvertFrom-Json
}

# Sigue el estado como lo hace la página mientras hay un paso en curso.
function Wait-UpdateState {
    param([string]$Url, $Session)
    $deadline = [DateTime]::UtcNow.AddSeconds(180)
    do {
        $state = (Invoke-WebRequest -UseBasicParsing -Uri ($Url + 'actualizaciones/estado/') -WebSession $Session).Content | ConvertFrom-Json
        if ($state.estado -notin @('buscando', 'descargando', 'verificando')) { return $state }
        Start-Sleep -Milliseconds 500
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "El actualizador siguió en $($state.estado) durante 180 segundos."
}

function Get-UpdateFolders {
    return @(Get-ChildItem -LiteralPath ([IO.Path]::GetTempPath()) -Directory -Filter 'PyGebra-actualizacion-*' -ErrorAction SilentlyContinue | ForEach-Object FullName)
}

try {
    $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/TASKS=desktopicon')
    if ($PreviousInstallerPath) {
        $previous = (Resolve-Path -LiteralPath $PreviousInstallerPath).Path
        $previousTasks = '/TASKS='
        if ($PreviousDesktopIcon) { $previousTasks = '/TASKS=desktopicon' }
        $baseline = Start-Process -FilePath $previous -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', $previousTasks, ('/DIR="' + $installDirectory + '"')) -WindowStyle Hidden -PassThru -Wait
        if ($baseline.ExitCode -ne 0) { throw "La instalación previa falló: $($baseline.ExitCode)" }
        $oldRegistration = Get-ItemProperty -LiteralPath $registryPath
        $oldVersion = $oldRegistration.DisplayVersion
        if (-not (Test-Path -LiteralPath $appPath)) { throw 'La base no instaló AlgebraLineal.exe.' }
        $oldDirectory = $oldRegistration.InstallLocation.TrimEnd('\')
        if ($oldDirectory -ne $installDirectory) { throw 'La base no usó la carpeta de prueba.' }
        if ($oldRegistration.DisplayName -eq 'Álgebra Lineal') {
            # Base histórica 0.8.0: otro nombre, mismo AppId y accesos «Álgebra Lineal».
            if ($oldRegistration.Publisher -ne 'Proyecto Álgebra Lineal' -or $oldVersion -ne '0.8.0' -or
                -not (Test-Path -LiteralPath $legacyStartShortcut)) { throw 'La base no es la instalación histórica publicada 0.8.0.' }
            $baseStartShortcut = $legacyStartShortcut
            $baseDesktopShortcut = $legacyDesktopShortcut
        } else {
            if ($oldRegistration.DisplayName -ne 'PyGebra' -or $oldRegistration.Publisher -ne 'Proyecto PyGebra' -or
                -not (Test-Path -LiteralPath $startShortcut)) { throw "La base $oldVersion no es una instalación publicada de PyGebra." }
            $baseStartShortcut = $startShortcut
            $baseDesktopShortcut = $desktopShortcut
        }
        if ((Test-Path -LiteralPath $baseDesktopShortcut) -ne [bool]$PreviousDesktopIcon) { throw 'El acceso de escritorio de la base no coincide con la tarea seleccionada.' }
        $baseShell = New-Object -ComObject Shell.Application
        $baseItem = $baseShell.NameSpace((Split-Path $baseStartShortcut)).ParseName((Split-Path $baseStartShortcut -Leaf))
        if ($baseItem.ExtendedProperty('System.AppUserModel.ID') -ne 'PyGebra.Desktop') { throw 'El AUMID de la base no es PyGebra.Desktop.' }
        # Un archivo ajeno en el grupo del menú Inicio debe sobrevivir a la actualización.
        $unrelatedFile = Join-Path (Split-Path $baseStartShortcut) ('P27.2-preserve-' + [guid]::NewGuid().ToString('N') + '.txt')
        [IO.File]::WriteAllText($unrelatedFile, 'preservar')
        # Simula un módulo de la versión anterior que ya no forma parte de la nueva.
        $obsoleteFile = Join-Path $installDirectory ('_internal\obsoleto-' + [guid]::NewGuid().ToString('N') + '\modulo.pyd')
        New-Item -ItemType Directory -Path (Split-Path $obsoleteFile) -Force | Out-Null
        [IO.File]::WriteAllText($obsoleteFile, 'obsoleto')
        Write-Host "Base $oldVersion verificada: $($oldRegistration.DisplayName), mismo AppId, AUMID PyGebra.Desktop, $oldDirectory (escritorio: $PreviousDesktopIcon)."
        # Sin /DIR: el candidato debe recuperar la carpeta de la base por AppId.
    } else {
        $arguments += ('/DIR="' + $installDirectory + '"')
    }
    if ($AutoUpdate) {
        if ([version]$candidateVersion -le [version]$oldVersion) {
            throw "La base $oldVersion debe ser anterior al candidato $candidateVersion para que su actualizador lo ofrezca."
        }
        $fakeGitHub = Start-FakeGitHub -Version $candidateVersion -InstallerFile $installer -Sha256 $InstallerSha256
        # El acceso directo hereda el entorno: solo esta instancia usa el GitHub simulado.
        $env:HTTPS_PROXY = "http://127.0.0.1:$($fakeGitHub.Port)"
        $updateFoldersBefore = Get-UpdateFolders
        Start-Process -FilePath $baseStartShortcut -WorkingDirectory $installDirectory -WindowStyle Normal
        $process = Wait-AppProcess
        $oldId = $process.Id
        $oldUrl = Wait-AppUrl $process
        Wait-AppWindow $process
        $oldHome = Invoke-WebRequest -UseBasicParsing -Uri $oldUrl -SessionVariable preferencesSession
        $csrf = [regex]::Match($oldHome.Content, 'name="csrf-token" content="([^"]+)"').Groups[1].Value
        if (-not $csrf) { throw 'La versión anterior no publicó el token para guardar preferencias.' }
        $precision = if ($PreviousDesktopIcon) { '8' } else { '6' }
        $expectedPreferences = @{
            'pygebra-tema' = 'dark'
            'pygebra-formato-numerico' = 'decimal'
            'pygebra-precision-decimal' = $precision
        }
        foreach ($preference in $expectedPreferences.GetEnumerator()) {
            $response = Invoke-WebRequest -UseBasicParsing -Uri ($oldUrl + 'preferencias/') -Method Post -WebSession $preferencesSession -Headers @{
                Referer = $oldUrl
                'X-CSRFToken' = $csrf
            } -Body @{ clave = $preference.Key; valor = $preference.Value }
            if ($response.StatusCode -ne 204) { throw "No se guardó $($preference.Key) en la versión anterior." }
        }

        $updatePage = $oldUrl + 'actualizaciones/'
        $updateHome = Invoke-WebRequest -UseBasicParsing -Uri $updatePage -SessionVariable updateSession
        $updateToken = [regex]::Match($updateHome.Content, 'name="csrf-token" content="([^"]+)"').Groups[1].Value
        if (-not $updateToken -or -not $updateHome.Content.Contains('data-actualizador')) { throw 'La base no muestra la página de actualizaciones.' }

        # Fallo 1: GitHub no responde. La app lo dice y no ofrece nada.
        $fakeGitHub.State.ApiDown = $true
        $state = Invoke-UpdateAction $oldUrl $updateSession $updateToken 'buscar'
        if ($state.estado -ne 'error_conexion') { throw "Con GitHub caído se esperaba error_conexion, no $($state.estado)." }
        $fakeGitHub.State.ApiDown = $false
        # Fallo 2: el SHA256SUMS.txt publicado no coincide con el instalador descargado.
        $fakeGitHub.State.BadSums = $true
        $state = Invoke-UpdateAction $oldUrl $updateSession $updateToken 'buscar'
        if ($state.estado -ne 'disponible' -or $state.version_disponible -ne $candidateVersion) { throw "La base no ofreció $candidateVersion ($($state.estado))." }
        $null = Invoke-UpdateAction $oldUrl $updateSession $updateToken 'descargar'
        $state = Wait-UpdateState $oldUrl $updateSession
        if ($state.estado -ne 'checksum_invalido') { throw "Con un SHA-256 distinto se esperaba checksum_invalido, no $($state.estado)." }
        if (@(Get-UpdateFolders | Where-Object { $_ -notin $updateFoldersBefore }).Count) { throw 'La descarga rechazada quedó en %TEMP%.' }
        if ($process.HasExited -or (Get-Item -LiteralPath $appPath).VersionInfo.ProductVersion -ne $oldVersion) { throw 'Un instalador rechazado alteró la versión instalada.' }
        $fakeGitHub.State.BadSums = $false
        Write-Host "Errores del actualizador ${oldVersion}: GitHub caído y SHA-256 distinto se informan sin tocar la instalación ni dejar descargas."

        # Recorrido correcto: buscar, descargar y verificar, instalar.
        $state = Invoke-UpdateAction $oldUrl $updateSession $updateToken 'buscar'
        if ($state.estado -ne 'disponible') { throw "Se esperaba disponible, no $($state.estado)." }
        $null = Invoke-UpdateAction $oldUrl $updateSession $updateToken 'descargar'
        $state = Wait-UpdateState $oldUrl $updateSession
        if ($state.estado -ne 'listo') { throw "La descarga verificada terminó en $($state.estado)." }
        $downloads = @(Get-UpdateFolders | Where-Object { $_ -notin $updateFoldersBefore })
        if ($downloads.Count -ne 1) { throw "Se esperaba una carpeta de descarga; hay $($downloads.Count)." }
        $downloaded = Join-Path $downloads[0] "PyGebra-Setup-$candidateVersion.exe"
        if ((Get-FileHash -LiteralPath $downloaded -Algorithm SHA256).Hash -ne $InstallerSha256.ToUpperInvariant()) { throw 'La descarga no es el candidato.' }
        $state = Invoke-UpdateAction $oldUrl $updateSession $updateToken 'instalar'
        if ($state.estado -ne 'instalando') { throw "Instalar terminó en $($state.estado)." }
        $setup = @(Get-Process -Name "PyGebra-Setup-$candidateVersion" -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $downloaded })
        if ($setup.Count -ne 1) { throw 'La app no lanzó el instalador descargado.' }
        $setup = $setup[0]
        $null = $setup.Handle
        # La app se cierra sola (cerrar_aplicacion) y el instalador espera a que suelte el mutex.
        if (-not $process.WaitForExit(30000)) { throw 'La versión anterior no se cerró sola tras lanzar el instalador.' }
        if ($process.ExitCode -ne 0) { throw "La versión anterior terminó con código $($process.ExitCode)." }
        if (-not $setup.WaitForExit(180000)) { throw 'El instalador no terminó dentro de 180 segundos.' }
        $expectedRoutes = @($fakeGitHub.State.ApiRoute) * 3 + @($fakeGitHub.State.SumsRoute, $fakeGitHub.State.InstallerRoute) * 2
        if ((@($fakeGitHub.State.Log | Sort-Object) -join "`n") -ne (@($expectedRoutes | Sort-Object) -join "`n")) {
            throw "La base no habló solo con el GitHub simulado: $($fakeGitHub.State.Log -join ', ')"
        }
        if ($fakeGitHub.State.Errors.Count) { throw "Errores del GitHub simulado: $($fakeGitHub.State.Errors -join ' | ')" }
        # La CA de prueba deja de ser de confianza en cuanto termina la parte simulada.
        Stop-FakeGitHub $fakeGitHub
        $fakeGitHub = $null
        Remove-Item Env:\HTTPS_PROXY
    } else {
        $setup = Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -PassThru -Wait
    }
    if ($setup.ExitCode -ne 0) { throw "El instalador falló: $($setup.ExitCode)" }
    if ($AutoUpdate) {
        $process = Wait-AppProcess -Seconds 60
        if ($process.Id -eq $oldId) { throw 'La actualización no abrió una nueva instancia.' }
        # El auxiliar de temporales.py borra la descarga cuando el instalador ya salió.
        $deadline = [DateTime]::UtcNow.AddSeconds(30)
        while ((Test-Path -LiteralPath $downloads[0]) -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 250 }
        if (Test-Path -LiteralPath $downloads[0]) { throw "La descarga sigue en %TEMP% tras la actualización: $($downloads[0])" }
    }
    foreach ($path in @($appPath, $registryPath) + $expectedShortcuts) {
        if (-not (Test-Path -LiteralPath $path)) { throw "El instalador no creó $path" }
    }
    if (-not $expectsDesktopIcon -and (Test-Path -LiteralPath $desktopShortcut)) {
        throw 'La actualización creó un acceso de escritorio que el usuario no eligió.'
    }
    foreach ($path in $legacyShortcuts) {
        if (Test-Path -LiteralPath $path) { throw "La actualización dejó un acceso histórico: $path" }
    }
    if ($unrelatedFile -and [IO.File]::ReadAllText($unrelatedFile) -ne 'preservar') { throw 'La migración modificó un archivo ajeno.' }
    if ($obsoleteFile -and (Test-Path -LiteralPath (Split-Path $obsoleteFile))) { throw "La actualización conservó un archivo obsoleto en _internal: $obsoleteFile" }
    # Una sola entrada de desinstalación (el mismo AppId) y un solo acceso por ubicación.
    $registrations = @(Get-PyGebraRegistrations)
    if ($registrations.Count -ne 1) { throw "Se esperaba una sola entrada de PyGebra en Aplicaciones; hay $($registrations.Count)." }
    $linkShell = New-Object -ComObject WScript.Shell
    foreach ($folder in @((Split-Path $startShortcut), [Environment]::GetFolderPath('Desktop'))) {
        $links = @(Get-ChildItem -LiteralPath $folder -Filter '*.lnk' -ErrorAction SilentlyContinue | Where-Object {
            $linkShell.CreateShortcut($_.FullName).TargetPath -eq $appPath })
        $count = if (-not $expectsDesktopIcon -and $folder -eq (Split-Path $desktopShortcut)) { 0 } else { 1 }
        if ($links.Count -ne $count) { throw "Cantidad incorrecta de accesos a PyGebra en $folder. Hay $($links.Count), se esperaban $count." }
    }
    $details = (Get-Item -LiteralPath $appPath).VersionInfo
    if ($details.ProductName -ne 'PyGebra' -or $details.FileDescription -ne 'PyGebra' -or
        $details.CompanyName -ne 'Proyecto PyGebra' -or $details.OriginalFilename -ne 'AlgebraLineal.exe' -or
        $details.FileVersion -ne $details.ProductVersion) { throw 'Metadatos de Windows incorrectos.' }
    if ((Split-Path $installer -Leaf) -ne "PyGebra-Setup-$($details.ProductVersion).exe") { throw 'Nombre o versión incorrectos del instalador.' }
    if ($AutoUpdate -and $details.ProductVersion -ne $candidateVersion) {
        throw "La actualización dejó $($details.ProductVersion) en lugar del candidato $candidateVersion."
    }
    $registration = Get-ItemProperty -LiteralPath $registryPath
    if ($registration.DisplayName -ne 'PyGebra' -or $registration.Publisher -ne 'Proyecto PyGebra' -or
        $registration.DisplayVersion -ne $details.ProductVersion -or
        $registration.InstallLocation.TrimEnd('\') -ne $installDirectory) { throw 'Identidad o carpeta incorrectas en el registro de desinstalación.' }
    $shell = New-Object -ComObject WScript.Shell
    $shellApplication = New-Object -ComObject Shell.Application
    $expectedIcon = Join-Path $installDirectory '_internal\assets\brand\app\pygebra.ico'
    if (-not (Test-Path -LiteralPath $expectedIcon -PathType Leaf)) {
        throw "La distribución no incluye el icono de PyGebra: $expectedIcon"
    }
    foreach ($shortcutPath in $expectedShortcuts) {
        $shortcut = $shell.CreateShortcut($shortcutPath)
        if ($shortcut.TargetPath -ne $appPath -or $shortcut.WorkingDirectory -ne $installDirectory) {
            throw "El acceso directo depende de una ruta incorrecta: $shortcutPath"
        }
        $location = [string]$shortcut.IconLocation
        $iconPath = $location
        $iconIndex = 0
        if ($location -match '^(.*),(\d+)$') {
            $iconPath = $Matches[1]
            $iconIndex = [int]$Matches[2]
        }
        if ($iconIndex -ne 0 -or [IO.Path]::GetFullPath($iconPath) -ne [IO.Path]::GetFullPath($expectedIcon)) {
            throw "El acceso directo no usa pygebra.ico: $shortcutPath -> $location"
        }
        $item = $shellApplication.NameSpace((Split-Path $shortcutPath)).ParseName((Split-Path $shortcutPath -Leaf))
        if ($item.ExtendedProperty('System.AppUserModel.ID') -ne 'PyGebra.Desktop') {
            throw "El acceso directo no declara AppUserModelID PyGebra.Desktop: $shortcutPath"
        }
    }
    Write-Host "Identidad verificada: PyGebra, Proyecto PyGebra, EXE $($details.ProductVersion), accesos PyGebra, AUMID PyGebra.Desktop y ningún acceso histórico."

    # El subsistema PE debe ser Windows GUI (2), no consola (3).
    $bytes = [IO.File]::ReadAllBytes($appPath)
    $peOffset = [BitConverter]::ToInt32($bytes, 0x3c)
    if ([BitConverter]::ToUInt16($bytes, $peOffset + 24 + 68) -ne 2) { throw 'El ejecutable no es windowed.' }

    for ($attempt = 1; $attempt -le 2; $attempt++) {
        if (-not ($AutoUpdate -and $attempt -eq 1)) {
            Start-Process -FilePath $startShortcut -WorkingDirectory $installDirectory -WindowStyle Normal
            $process = Wait-AppProcess
        }
        $url = Wait-AppUrl $process
        # Django responde antes de que .NET/WebView2 termine de crear la ventana.
        Wait-AppWindow $process
        $homeResponse = Invoke-WebRequest -UseBasicParsing -Uri $url
        if ($AutoUpdate) {
            foreach ($preference in $expectedPreferences.GetEnumerator()) {
                if (-not $homeResponse.Content.Contains(('data-{0}="{1}"' -f $preference.Key, $preference.Value))) {
                    throw "No se conservó $($preference.Key) después de actualizar."
                }
            }
            if ($attempt -eq 1) {
                $state = (Invoke-WebRequest -UseBasicParsing -Uri ($url + 'actualizaciones/estado/')).Content | ConvertFrom-Json
                if ($state.estado -ne 'inicial' -or $state.version_instalada -ne $candidateVersion) {
                    throw "La app reabierta informa $($state.version_instalada) ($($state.estado)) en lugar de $candidateVersion."
                }
                Write-Host "Autoactualización $oldVersion → $($details.ProductVersion): cierre, reapertura, preferencias y accesos verificados."
            }
        }
        if (-not $homeResponse.Content.Contains('href="/matrices/reduccion/"')) { throw 'Inicio no enlaza a Reducción por filas.' }
        $systemsUrl = $url + 'matrices/reduccion/'
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
            foreach ($expected in @('Columnas pivote: C1, C3', 'Consistente de soluciones infinitas', 'x₃ = 2')) {
                if (-not $text.Contains($expected)) { throw "Falta '$expected' en $method ($url)." }
            }
        }
        # Operaciones con matrices (P26.6): las operaciones básicas son expresiones del mismo formulario,
        # con matrices rectangulares y fracciones. Se declaran A, B y k aunque cada expresión use parte.
        $matricesUrl = $url + 'matrices/operaciones/'
        $expectedMatrices = [ordered]@{
            'A + B' = @('2', '4', '6', '8', '10', '12')
            'A - B' = @('0', '0', '0', '0', '0', '0')
            'kA' = @('1/2', '1', '3/2', '2', '5/2', '3')
            'A^T' = @('1', '4', '2', '5', '3', '6')
        }
        foreach ($expression in $expectedMatrices.Keys) {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $matricesUrl -SessionVariable matrixSession
            $matrixCsrf = [regex]::Match($response.Content, 'name="csrfmiddlewaretoken" value="([^"]+)"').Groups[1].Value
            $matrixBody = @{ csrfmiddlewaretoken = $matrixCsrf; expresion = $expression; cantidad = '3'
                nombre_0 = 'A'; tipo_0 = 'matriz'; filas_0 = '2'; columnas_0 = '3'
                nombre_1 = 'B'; tipo_1 = 'matriz'; filas_1 = '2'; columnas_1 = '3'
                nombre_2 = 'k'; tipo_2 = 'escalar'; celda_2_0_0 = '1/2' }
            for ($row = 0; $row -lt 2; $row++) {
                for ($column = 0; $column -lt 3; $column++) {
                    $value = [string](1 + 3 * $row + $column)
                    $matrixBody["celda_0_${row}_${column}"] = $value
                    $matrixBody["celda_1_${row}_${column}"] = $value
                }
            }
            $response = Invoke-WebRequest -UseBasicParsing -Uri $matricesUrl -Method Post -WebSession $matrixSession -Headers @{ Referer = $matricesUrl } -Body $matrixBody
            $resultTable = [regex]::Match($response.Content, '(?s)<table[^>]*aria-label="Resultado"[^>]*>(.*?)</table>').Groups[1].Value
            $cells = Get-CellTexts $resultTable
            if (($cells -join ',') -ne ($expectedMatrices[$expression] -join ',')) { throw "Resultado incorrecto de matrices: $expression" }
            if (-not $response.Content.Contains('id="procedimiento"')) { throw "Falta procedimiento de matrices: $expression" }
            if (-not $response.Content.Contains('data-numeric-controls')) { throw "Falta el selector Exacto/Decimal en matrices: $expression" }
        }
        # P13B: AB (2x3 por 3x2) y Ax (2x3 por x de 3) comparando las dos lecturas del producto.
        $productBodies = @(
            @{ expresion = 'AB'; cantidad = '2'; metodo = 'comparar'
               nombre_0 = 'A'; tipo_0 = 'matriz'; filas_0 = '2'; columnas_0 = '3'
               celda_0_0_0 = '1'; celda_0_0_1 = '2'; celda_0_0_2 = '3'; celda_0_1_0 = '4'; celda_0_1_1 = '5'; celda_0_1_2 = '6'
               nombre_1 = 'B'; tipo_1 = 'matriz'; filas_1 = '3'; columnas_1 = '2'
               celda_1_0_0 = '7'; celda_1_0_1 = '8'; celda_1_1_0 = '9'; celda_1_1_1 = '10'; celda_1_2_0 = '11'; celda_1_2_1 = '12' },
            @{ expresion = 'Ax'; cantidad = '2'; metodo = 'comparar'
               nombre_0 = 'A'; tipo_0 = 'matriz'; filas_0 = '2'; columnas_0 = '3'
               celda_0_0_0 = '1'; celda_0_0_1 = '2'; celda_0_0_2 = '-1'; celda_0_1_0 = '0'; celda_0_1_1 = '-5'; celda_0_1_2 = '3'
               nombre_1 = 'x'; tipo_1 = 'vector'; filas_1 = '3'
               celda_1_0_0 = '4'; celda_1_1_0 = '3'; celda_1_2_0 = '7' }
        )
        $expectedProducts = @{ AB = @('58', '64', '139', '154'); Ax = @('3', '6') }
        foreach ($productBody in $productBodies) {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $matricesUrl -SessionVariable productSession
            $productBody.csrfmiddlewaretoken = [regex]::Match($response.Content, 'name="csrfmiddlewaretoken" value="([^"]+)"').Groups[1].Value
            $response = Invoke-WebRequest -UseBasicParsing -Uri $matricesUrl -Method Post -WebSession $productSession -Headers @{ Referer = $matricesUrl } -Body $productBody
            $resultTable = [regex]::Match($response.Content, '(?s)<table[^>]*aria-label="Resultado"[^>]*>(.*?)</table>').Groups[1].Value
            $cells = Get-CellTexts $resultTable
            if (($cells -join ',') -ne ($expectedProducts[$productBody.expresion] -join ',')) { throw "Resultado incorrecto de matrices: $($productBody.expresion)" }
            # P18: un «Ver procedimiento» plegado con un sub-bloque por lectura.
            if (-not $response.Content.Contains('id="procedimiento"')) { throw "Falta un procedimiento comparado de matrices: $($productBody.expresion)" }
            if (([regex]::Matches($response.Content, 'class="disclosure disclosure-nested"')).Count -ne 2) { throw "Faltan las dos lecturas comparadas de matrices: $($productBody.expresion)" }
        }
        # La ruta histórica de Expresiones matriciales lleva a la misma herramienta.
        $response = Invoke-WebRequest -UseBasicParsing -Uri ($url + 'matrices/expresiones/')
        if (-not $response.Content.Contains('action="/matrices/operaciones/#resultado"')) { throw 'La ruta histórica de expresiones no lleva a Operaciones con matrices.' }
        # P14: Ax = b con x desconocido. Solución fraccionaria comparando métodos y un caso rectangular 3x2.
        $equationsUrl = $url + 'matrices/ecuaciones/'
        $response = Invoke-WebRequest -UseBasicParsing -Uri $equationsUrl
        if (-not $response.Content.Contains('aria-label="Vector incógnita x, no editable"')) { throw 'Resolver Ax = b no muestra el vector incógnita.' }
        $equationBodies = @(
            @{ filas = '2'; columnas = '2'; metodo = 'comparar'
               celda_A_0_0 = '2'; celda_A_0_1 = '0'; celda_A_1_0 = '0'; celda_A_1_1 = '3'; celda_b_0_0 = '1'; celda_b_1_0 = '1' },
            @{ filas = '3'; columnas = '2'; metodo = 'gauss_jordan'
               celda_A_0_0 = '1'; celda_A_0_1 = '0'; celda_A_1_0 = '0'; celda_A_1_1 = '1'; celda_A_2_0 = '1'; celda_A_2_1 = '1'
               celda_b_0_0 = '2'; celda_b_1_0 = '3'; celda_b_2_0 = '5' }
        )
        $expectedEquations = @(
            @{ x = @('1/2', '1/3'); markers = @('Ax = b tiene solución única.', 'b = (1/2)a₁ + (1/3)a₂', 'id="procedimiento"', 'class="disclosure disclosure-nested"') },
            @{ x = @('2', '3'); markers = @('Ax = b tiene solución única.', 'A (3×2) · x (2) = b (3)', 'x₁ = 2', 'x₂ = 3', 'id="procedimiento"') }
        )
        for ($case = 0; $case -lt $equationBodies.Count; $case++) {
            $equationBody = $equationBodies[$case]
            $response = Invoke-WebRequest -UseBasicParsing -Uri $equationsUrl -SessionVariable equationSession
            $equationBody.csrfmiddlewaretoken = [regex]::Match($response.Content, 'name="csrfmiddlewaretoken" value="([^"]+)"').Groups[1].Value
            $response = Invoke-WebRequest -UseBasicParsing -Uri $equationsUrl -Method Post -WebSession $equationSession -Headers @{ Referer = $equationsUrl } -Body $equationBody
            $solutionTable = [regex]::Match($response.Content, '(?s)<table[^>]*aria-label="Vector solución x"[^>]*>(.*?)</table>').Groups[1].Value
            $cells = Get-CellTexts $solutionTable
            if (($cells -join ',') -ne ($expectedEquations[$case].x -join ',')) { throw "Resultado incorrecto de Ax = b (caso $($case + 1))." }
            foreach ($marker in $expectedEquations[$case].markers) {
                if (-not $response.Content.Contains($marker)) { throw "Falta '$marker' en Ax = b (caso $($case + 1))." }
            }
        }
        foreach ($asset in @('styles.css', 'matriz.js', 'expresiones.js', 'ecuaciones.js', 'numeros.js', 'tema.js', 'navigation.js', 'buscador.js', 'teclado.js', 'favicon.svg', 'favicon.ico')) {
            $response = Invoke-WebRequest -UseBasicParsing -Uri ($url + 'static/calculadora/' + $asset)
            if ($response.StatusCode -ne 200) { throw "No se sirvió el recurso $asset" }
        }
        if (-not $process.CloseMainWindow()) { throw 'La ventana nativa no respondió al cierre.' }
        if (-not $process.WaitForExit(10000)) { throw 'La aplicación no terminó limpiamente.' }
        if ($process.ExitCode -ne 0) { throw "La aplicación terminó con código $($process.ExitCode)" }
        $listener = @(Get-NetTCPConnection -State Listen -OwningProcess $process.Id -ErrorAction SilentlyContinue)
        if ($listener.Count) { throw 'El servidor sigue escuchando después del cierre.' }
        $process = $null
        Write-Host "Apertura ${attempt}: acceso directo, Django/Waitress, ambos métodos, P13A, P13B, P14, recursos y cierre OK."
    }
} finally {
    if ($fakeGitHub) { Stop-FakeGitHub $fakeGitHub }
    if ($AutoUpdate) { Remove-Item Env:\HTTPS_PROXY -ErrorAction SilentlyContinue }
    if ($setup -and -not $setup.HasExited) {
        $setup.Kill()
        $setup.WaitForExit()
    }
    if ($process -and -not $process.HasExited) {
        $process.CloseMainWindow() | Out-Null
        if (-not $process.WaitForExit(10000)) { $process.Kill(); $process.WaitForExit() }
    }
    $uninstaller = Join-Path $installDirectory 'unins000.exe'
    if (Test-Path -LiteralPath $uninstaller) {
        $uninstall = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') -WindowStyle Hidden -PassThru -Wait
        if ($uninstall.ExitCode -ne 0) { throw "La desinstalación falló: $($uninstall.ExitCode)" }
    }
    if ($unrelatedFile) {
        if ([IO.File]::ReadAllText($unrelatedFile) -ne 'preservar') { throw 'La desinstalación modificó un archivo ajeno.' }
        Remove-Item -LiteralPath $unrelatedFile
    }
}
foreach ($path in @($installDirectory, $registryPath, $startShortcut, $desktopShortcut) + $legacyShortcuts) {
    if (Test-Path -LiteralPath $path) { throw "La desinstalación dejó $path" }
}
if ($AutoUpdate) {
    # Las preferencias viven fuera de {app}: la desinstalación las conserva. Las creó esta prueba.
    if (-not (Test-Path -LiteralPath $preferencesFile)) { throw 'La desinstalación borró las preferencias del usuario.' }
    foreach ($path in @($preferencesFile, [IO.Path]::ChangeExtension($preferencesFile, '.lock'))) {
        Remove-Item -LiteralPath $path -ErrorAction SilentlyContinue
    }
}
Write-Host "Distribución verificada fuera del repositorio y desinstalada: $installDirectory"
