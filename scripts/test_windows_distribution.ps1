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

# Texto de cada celda de una tabla de matriz; el formato Exacto/Decimal envuelve los
# valores no enteros en <span data-numeric>, así que se retiran las etiquetas internas.
function Get-CellTexts {
    param([string]$TableHtml)
    return @([regex]::Matches($TableHtml, '(?s)<td[^>]*>(.*?)</td>') | ForEach-Object {
        [regex]::Replace($_.Groups[1].Value, '<[^>]+>', '').Trim()
    })
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
        # Operaciones básicas con matrices: rectangular, fracciones y las cuatro variantes.
        $matricesUrl = $url + 'matrices/operaciones/'
        $expectedMatrices = @{
            suma = @('2', '4', '6', '8', '10', '12')
            resta = @('0', '0', '0', '0', '0', '0')
            escalar = @('1/2', '1', '3/2', '2', '5/2', '3')
            traspuesta = @('1', '4', '2', '5', '3', '6')
        }
        foreach ($operation in @('suma', 'resta', 'escalar', 'traspuesta')) {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $matricesUrl -SessionVariable matrixSession
            $matrixCsrf = [regex]::Match($response.Content, 'name="csrfmiddlewaretoken" value="([^"]+)"').Groups[1].Value
            $matrixBody = @{ csrfmiddlewaretoken = $matrixCsrf; operacion = $operation; filas = '2'; columnas = '3' }
            for ($row = 0; $row -lt 2; $row++) {
                for ($column = 0; $column -lt 3; $column++) {
                    $value = [string](1 + 3 * $row + $column)
                    $matrixBody["celda_A_${row}_${column}"] = $value
                    if ($operation -in @('suma', 'resta')) { $matrixBody["celda_B_${row}_${column}"] = $value }
                }
            }
            if ($operation -eq 'escalar') { $matrixBody.escalar = '1/2' }
            $response = Invoke-WebRequest -UseBasicParsing -Uri $matricesUrl -Method Post -WebSession $matrixSession -Headers @{ Referer = $matricesUrl } -Body $matrixBody
            $resultTable = [regex]::Match($response.Content, '(?s)<table[^>]*aria-label="Matriz resultado"[^>]*>(.*?)</table>').Groups[1].Value
            $cells = Get-CellTexts $resultTable
            if (($cells -join ',') -ne ($expectedMatrices[$operation] -join ',')) { throw "Resultado incorrecto de matrices: $operation" }
            if (-not $response.Content.Contains('id="procedimiento"')) { throw "Falta procedimiento de matrices: $operation" }
            if (-not $response.Content.Contains('data-numeric-controls')) { throw "Falta el selector Exacto/Decimal en matrices: $operation" }
        }
        # P13B: AB (2x3 por 3x2) y Ax (2x3 por x de 3) comparando los dos métodos.
        $productBodies = @(
            @{ operacion = 'producto'; filas = '2'; columnas = '3'; columnas_b = '2'; metodo = 'comparar'
               celda_A_0_0 = '1'; celda_A_0_1 = '2'; celda_A_0_2 = '3'; celda_A_1_0 = '4'; celda_A_1_1 = '5'; celda_A_1_2 = '6'
               celda_B_0_0 = '7'; celda_B_0_1 = '8'; celda_B_1_0 = '9'; celda_B_1_1 = '10'; celda_B_2_0 = '11'; celda_B_2_1 = '12' },
            @{ operacion = 'matriz_vector'; filas = '2'; columnas = '3'; metodo = 'comparar'
               celda_A_0_0 = '1'; celda_A_0_1 = '2'; celda_A_0_2 = '-1'; celda_A_1_0 = '0'; celda_A_1_1 = '-5'; celda_A_1_2 = '3'
               celda_x_0_0 = '4'; celda_x_1_0 = '3'; celda_x_2_0 = '7' }
        )
        $expectedProducts = @{ producto = @('58', '64', '139', '154'); matriz_vector = @('3', '6') }
        foreach ($productBody in $productBodies) {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $matricesUrl -SessionVariable productSession
            $productBody.csrfmiddlewaretoken = [regex]::Match($response.Content, 'name="csrfmiddlewaretoken" value="([^"]+)"').Groups[1].Value
            $response = Invoke-WebRequest -UseBasicParsing -Uri $matricesUrl -Method Post -WebSession $productSession -Headers @{ Referer = $matricesUrl } -Body $productBody
            $resultTable = [regex]::Match($response.Content, '(?s)<table[^>]*aria-label="Matriz resultado"[^>]*>(.*?)</table>').Groups[1].Value
            $cells = Get-CellTexts $resultTable
            if (($cells -join ',') -ne ($expectedProducts[$productBody.operacion] -join ',')) { throw "Resultado incorrecto de matrices: $($productBody.operacion)" }
            # P18: un «Ver procedimiento» plegado con un sub-bloque por método.
            if (-not $response.Content.Contains('id="procedimiento"')) { throw "Falta un procedimiento comparado de matrices: $($productBody.operacion)" }
            if (([regex]::Matches($response.Content, 'class="disclosure disclosure-nested"')).Count -ne 2) { throw "Faltan los dos métodos comparados de matrices: $($productBody.operacion)" }
        }
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
            @{ x = @('2', '3'); markers = @('Ax = b tiene solución única.', 'A (3×2) · x (2) = b (3)', 'x1 = 2', 'x2 = 3', 'id="procedimiento"') }
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
        foreach ($asset in @('styles.css', 'matriz.js', 'matrices.js', 'ecuaciones.js', 'numeros.js', 'tema.js', 'navigation.js', 'buscador.js', 'teclado.js', 'favicon.svg', 'favicon.ico')) {
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
