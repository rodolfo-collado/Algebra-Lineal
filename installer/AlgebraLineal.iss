; Compilar mediante scripts/build_windows.ps1. La versión viene de pyproject.toml.
#ifndef AppVersion
  #error Falta /DAppVersion. Usa scripts\build_windows.ps1.
#endif
#ifndef ProjectRoot
  #define ProjectRoot ExtractFileDir(SourcePath)
#endif
#define AppName "PyGebra"
#define AppExe "AlgebraLineal.exe"
; Mismo identificador que desktop.APP_USER_MODEL_ID. No depende de la versión.
#define AppUserModelId "PyGebra.Desktop"
; Mismo nombre que desktop.APP_MUTEX_NAME: existe mientras alguna instancia está abierta.
#define AppMutexName "PyGebra.Desktop.Ejecutandose"

[Setup]
AppId={{D0455B79-7F5E-4C78-9F3B-F47187E9A83A}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Proyecto PyGebra
AppPublisherURL=https://github.com/rodolfo-collado/Algebra-Lineal
DefaultDirName={localappdata}\Programs\AlgebraLineal
UsePreviousAppDir=yes
; Instalación por usuario en una carpeta fija: no se pregunta la carpeta, pero el
; resumen previo a instalar la muestra. /DIR sigue disponible para casos avanzados
; y una instalación previa conserva su carpeta (UsePreviousAppDir).
DisableDirPage=yes
AlwaysShowDirOnReadyPage=yes
DefaultGroupName={#AppName}
UsePreviousGroup=no
DisableProgramGroupPage=yes
; Flujo corto: tareas → resumen → instalación → final.
DisableWelcomePage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir={#ProjectRoot}\dist\installer
OutputBaseFilename=PyGebra-Setup-{#AppVersion}
SetupIconFile={#ProjectRoot}\assets\brand\app\pygebra.ico
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
; Apariencia moderna que sigue el tema claro/oscuro de Windows sin estilos externos.
WizardStyle=modern dynamic windows11
CloseApplications=yes
RestartApplications=no
; Dos instaladores de PyGebra no se ejecutan a la vez.
SetupMutex=PyGebra.Setup

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
; El bootstrapper se ejecuta desde una carpeta instalada, nunca desde el checkout.
Source: "{#ProjectRoot}\build\prerequisites\MicrosoftEdgeWebview2Setup.exe"; DestDir: "{app}\prerequisites"; Flags: ignoreversion; Check: NeedsWebView2; AfterInstall: InstallWebView2
Source: "{#ProjectRoot}\dist\AlgebraLineal\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; onedir: sobrescribir dejaría módulos y DLL de la versión anterior en _internal. La
; carpeta solo contiene archivos generados por PyInstaller; los datos del usuario viven
; en %LOCALAPPDATA%\PyGebra. Corre después de cerrar la app y antes de copiar [Files].
Type: filesandordirs; Name: "{app}\_internal"
; Solo los accesos de la instalación histórica por usuario, nunca su contenido.
Type: files; Name: "{userprograms}\Álgebra Lineal\Álgebra Lineal.lnk"
Type: files; Name: "{userdesktop}\Álgebra Lineal.lnk"

; La barra de tareas muestra el icono del acceso directo, no el de la ventana.
; IconFilename apunta al pygebra.ico ya incluido por PyInstaller, no al icono
; cacheado de AlgebraLineal.exe. AppUserModelID coincide con desktop.py.
[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\assets\brand\app\pygebra.ico"; AppUserModelID: "{#AppUserModelId}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon; IconFilename: "{app}\_internal\assets\brand\app\pygebra.ico"; AppUserModelID: "{#AppUserModelId}"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName}"; Flags: nowait postinstall skipifsilent; Check: WebView2Installed
; Actualización lanzada desde PyGebra (/SILENT /ACTUALIZAR=1): vuelve a abrirla al terminar.
Filename: "{app}\{#AppExe}"; Flags: nowait; Check: RelaunchAfterUpdate

[Code]
const
  WebView2Key = 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';

function RuntimeInRegistry(Root: Integer): Boolean;
var
  Version: String;
  PackedVersion: Int64;
begin
  Result := False;
  if RegQueryStringValue(Root, WebView2Key, 'pv', Version) then
    if StrToVersion(Version, PackedVersion) then
      Result := ComparePackedVersion(PackedVersion, PackVersionComponents(86, 0, 622, 0)) >= 0;
end;

function WebView2Installed: Boolean;
begin
  Result := RuntimeInRegistry(HKCU64) or RuntimeInRegistry(HKCU32) or RuntimeInRegistry(HKLM32);
end;

function NeedsWebView2: Boolean;
begin
  Result := not WebView2Installed;
end;

function IsUpdateRun: Boolean;
begin
  Result := ExpandConstant('{param:ACTUALIZAR|0}') = '1';
end;

function RelaunchAfterUpdate: Boolean;
begin
  Result := IsUpdateRun and WebView2Installed;
end;

{ PyGebra lanza el instalador y se cierra justo después: en ese caso se espera hasta
  15 s a que termine. Si sigue abierta (o es una instalación manual) se pide cerrarla.
  En modo /SUPPRESSMSGBOXES la respuesta es Cancelar: nunca se reemplazan archivos en uso. }
function InitializeSetup: Boolean;
var
  Attempts: Integer;
begin
  Result := True;
  Attempts := 0;
  while IsUpdateRun and CheckForMutexes('{#AppMutexName}') and (Attempts < 30) do
  begin
    Sleep(500);
    Attempts := Attempts + 1;
  end;
  while CheckForMutexes('{#AppMutexName}') do
    if SuppressibleMsgBox('PyGebra está abierto. Ciérralo y pulsa Aceptar para continuar, ' +
      'o pulsa Cancelar para salir del instalador.', mbError, MB_OKCANCEL, IDCANCEL) = IDCANCEL then
    begin
      Result := False;
      Exit;
    end;
end;

{ Como no se pregunta la carpeta, el resumen es el único lugar donde se informa.
  El memo no ajusta líneas largas, así que cada dato ocupa una línea corta. }
function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
begin
  Result := MemoDirInfo + NewLine + NewLine +
    'Accesos directos:' + NewLine + Space + 'Menú Inicio';
  if WizardIsTaskSelected('desktopicon') then
    Result := Result + NewLine + Space + 'Escritorio';
  Result := Result + NewLine + NewLine + 'Microsoft Edge WebView2 Runtime:' + NewLine;
  if NeedsWebView2 then
    Result := Result + Space + 'Se instalará como requisito desde Microsoft.' + NewLine +
      Space + 'Mantén la conexión a Internet durante la instalación.'
  else
    Result := Result + Space + 'Ya está disponible en este equipo.';
end;

procedure InstallWebView2;
var
  ExitCode: Integer;
begin
  if WebView2Installed then
    Exit;
  WizardForm.StatusLabel.Caption := 'Instalando Microsoft Edge WebView2 Runtime...';
  if not Exec(ExpandConstant('{app}\prerequisites\MicrosoftEdgeWebview2Setup.exe'),
    '/silent /install', ExpandConstant('{app}\prerequisites'), SW_HIDE,
    ewWaitUntilTerminated, ExitCode) then
    RaiseException('No se pudo iniciar la instalación de Microsoft Edge WebView2 Runtime. ' +
      'Vuelve a ejecutar este instalador. Código: ' + IntToStr(ExitCode));
  Log('WebView2: código de salida ' + IntToStr(ExitCode));
  if (ExitCode <> 0) or not WebView2Installed then
    RaiseException('No se pudo instalar Microsoft Edge WebView2 Runtime. ' +
      'Comprueba tu conexión a Internet y vuelve a ejecutar este instalador. ' +
      'Si el equipo no tiene Internet, instala primero el runtime Evergreen con el ' +
      'instalador sin conexión de https://developer.microsoft.com/microsoft-edge/webview2/ ' +
      'y vuelve a intentarlo. Código: ' + IntToStr(ExitCode));
end;
