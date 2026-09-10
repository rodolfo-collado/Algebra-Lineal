#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet('All', 'App', 'Installer')]
    [string]$Target = 'All',
    [string]$IsccPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))

function Invoke-BuildCommand {
    param([string]$Phase, [string]$Command, [string[]]$Arguments)
    Write-Host "`n$Phase"
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Phase falló (código $LASTEXITCODE). Revisa la salida anterior."
    }
}

function Find-InnoCompiler {
    if ($IsccPath) {
        if (-not (Test-Path -LiteralPath $IsccPath -PathType Leaf)) {
            throw "No existe el compilador indicado: $IsccPath"
        }
        return (Resolve-Path -LiteralPath $IsccPath).Path
    }
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($base in @(${env:ProgramFiles(x86)}, $env:ProgramFiles, "$env:LOCALAPPDATA\Programs")) {
        foreach ($version in @('6', '7')) {
            $candidate = Join-Path $base "Inno Setup $version\ISCC.exe"
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
        }
    }
    throw 'Falta Inno Setup 6.3 o posterior. Instálalo desde https://jrsoftware.org/isdl.php o usa -IsccPath.'
}

function Clear-BuildDirectory {
    param([ValidateSet('build\AlgebraLineal', 'dist\AlgebraLineal', 'dist\installer')][string]$RelativePath)
    $path = [IO.Path]::GetFullPath((Join-Path $projectRoot $RelativePath))
    if (-not $path.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "La limpieza está fuera del proyecto: $path"
    }
    if (Test-Path -LiteralPath $path) {
        $resolved = (Resolve-Path -LiteralPath $path).Path
        if ($resolved -ne $path) { throw "Ruta inesperada para limpieza: $resolved" }
        # No seguimos enlaces/junctions al limpiar artefactos generados.
        foreach ($entry in @((Get-Item -LiteralPath (Split-Path $path)), (Get-Item -LiteralPath $path)) + @(Get-ChildItem -LiteralPath $path -Force -Recurse)) {
            if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "La limpieza contiene un enlace: $($entry.FullName)"
            }
        }
        Write-Host "Limpiando $path"
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

function Prepare-WebView2Bootstrapper {
    $directory = Join-Path $projectRoot 'build\prerequisites'
    $path = Join-Path $directory 'MicrosoftEdgeWebview2Setup.exe'
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Write-Host 'Descargando el bootstrapper oficial de Microsoft WebView2...'
        # En PowerShell 5.1, algunos equipos aún usan TLS antiguo por defecto.
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        try {
            Invoke-WebRequest -UseBasicParsing -Uri 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile $path
        } catch {
            if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
            throw "No se pudo descargar WebView2. Comprueba la conexión. $($_.Exception.Message)"
        }
    }
    $signature = Get-AuthenticodeSignature -LiteralPath $path
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation(?:,|$)') {
        throw "El bootstrapper WebView2 no tiene una firma válida de Microsoft: $path. Elimínalo y vuelve a ejecutar el build."
    }
}

Push-Location $projectRoot
try {
    if ($env:OS -ne 'Windows_NT') { throw 'La distribución de Windows debe construirse en Windows.' }
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) { throw 'Falta uv en PATH. Instálalo desde https://docs.astral.sh/uv/ y abre una nueva terminal.' }
    $iscc = $null
    if ($Target -ne 'App') { $iscc = Find-InnoCompiler }
    Invoke-BuildCommand 'Comprobando uv.lock' $uv.Source @('lock', '--check')
    Invoke-BuildCommand 'Sincronizando dependencias bloqueadas' $uv.Source @('sync', '--locked', '--group', 'dev')

    $versionCode = "import pathlib,tomllib; print(tomllib.loads(pathlib.Path('pyproject.toml').read_text(encoding='utf-8'))['project']['version'])"
    $appVersion = & $uv.Source run --locked python -c $versionCode
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo leer la versión desde pyproject.toml.' }
    $appVersion = "$appVersion".Trim()
    if ($appVersion -notmatch '^\d+\.\d+\.\d+(\.\d+)?$') {
        throw "La versión '$appVersion' debe tener 3 o 4 componentes numéricos para Inno Setup."
    }
    Invoke-BuildCommand 'Comprobando Python x64' $uv.Source @('run', '--locked', 'python', '-c', "import platform,struct; assert struct.calcsize('P')==8 and platform.machine().lower() in ('amd64','x86_64'), 'Se requiere Python x64 para este instalador'")

    if ($Target -ne 'Installer') {
        Clear-BuildDirectory 'build\AlgebraLineal'
        Clear-BuildDirectory 'dist\AlgebraLineal'
        Invoke-BuildCommand 'Construyendo PyInstaller' $uv.Source @('run', '--locked', 'pyinstaller', '--noconfirm', '--clean', 'AlgebraLineal.spec')
    }
    $appPath = Join-Path $projectRoot 'dist\AlgebraLineal\AlgebraLineal.exe'
    if (-not (Test-Path -LiteralPath $appPath -PathType Leaf)) {
        throw "Falta $appPath. Genera primero el build con -Target App o ejecuta el script sin -Target."
    }
    Write-Host "Build PyInstaller: $appPath"
    if ($Target -ne 'App') {
        Prepare-WebView2Bootstrapper
        Clear-BuildDirectory 'dist\installer'
        Invoke-BuildCommand 'Compilando el instalador Inno Setup' $iscc @("/DAppVersion=$appVersion", "/DProjectRoot=$projectRoot", (Join-Path $projectRoot 'installer\AlgebraLineal.iss'))
        $installerPath = Join-Path $projectRoot "dist\installer\AlgebraLineal-Setup-$appVersion.exe"
        if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
            throw "Inno Setup terminó sin generar el instalador esperado: $installerPath"
        }
        $size = [math]::Round((Get-Item -LiteralPath $installerPath).Length / 1MB, 1)
        Write-Host "`nDistribución lista ($size MiB): $installerPath"
    }
} finally {
    Pop-Location
}
