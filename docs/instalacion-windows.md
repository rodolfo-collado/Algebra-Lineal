# Instalación y distribución de Windows

[Índice de documentación](README.md) · [Portada](../README.md)

## Instalar como usuario

1. Descarga `PyGebra-Setup-x.y.z.exe` desde la [última release estable](https://github.com/Collado-Labs/Algebra-Lineal/releases/latest).
2. Ejecuta el instalador: decide si quieres un acceso directo en el escritorio y
   pulsa **Instalar**.
3. Abre **PyGebra** desde el menú Inicio o el acceso directo opcional del escritorio.

No necesitas Git, Python, uv, PyInstaller, terminal ni acceso al repositorio.
El instalador no pide elegir una carpeta: la aplicación se instala para tu usuario
en `%LOCALAPPDATA%\Programs\AlgebraLineal`, sin solicitar privilegios de
administrador, y la pantalla **Listo para Instalar** muestra esa ubicación antes
de continuar. El asistente sigue el tema claro u oscuro de Windows y la aplicación
funciona sin una consola detrás.
Para quitarla, usa **Configuración → Aplicaciones → PyGebra → Desinstalar**.

Requiere Windows 10 1809 o posterior / Windows 11, compatible con aplicaciones x64.
Si falta **Microsoft Edge WebView2 Runtime**, el instalador te avisa y ejecuta el
bootstrapper oficial de Microsoft incluido en el paquete. Solo en ese caso
necesitas Internet durante la instalación. Una vez instalado, la calculadora
funciona sin Internet. En un equipo sin conexión, instala previamente WebView2
con el instalador **Evergreen Standalone** de
[Microsoft](https://developer.microsoft.com/microsoft-edge/webview2/).

Si Microsoft no puede instalar el runtime, la instalación muestra instrucciones
para corregirlo y volver a intentarlo. El ejecutable también comprueba el runtime
antes de iniciar y muestra un mensaje legible si falta. La desinstalación elimina
los archivos y accesos directos de PyGebra; conserva WebView2, que puede ser
utilizado por otras aplicaciones.

PyGebra guarda solo tus preferencias de presentación (tema, Exacto/Decimal y
precisión) en `%LOCALAPPDATA%\PyGebra\preferencias.json`, fuera de la carpeta
instalada. Las actualizaciones lo conservan y la desinstalación no lo borra;
puedes eliminarlo a mano para volver a los valores iniciales.

## Actualizar PyGebra

En la app de escritorio, abre **Opciones → Actualizaciones** y pulsa
**Buscar actualizaciones**. La consulta se inicia al pulsar el botón.

1. PyGebra compara tu versión con la última publicación estable de GitHub.
2. Si hay una versión más reciente, selecciona el botón de descarga. PyGebra
   descarga el instalador y `SHA256SUMS.txt`, y comprueba que el hash del EXE
   coincide con el publicado.
3. Cuando aparezca **Instalar y reiniciar PyGebra**, pulsa el botón para continuar.
   La aplicación vuelve a comprobar el SHA-256, abre el instalador y se cierra.
4. El instalador actualiza la misma instalación, conserva las preferencias y
   vuelve a abrir PyGebra.

A partir de v0.20.0, la pantalla indica en qué paso está la actualización
(buscar, descargar, verificar o instalar) y muestra el avance real durante la
descarga. Usa una escena clara u oscura según el tema elegido y respeta la
preferencia de movimiento reducido.

[![Pantalla Actualizaciones de PyGebra v0.20.0 en tema oscuro, lista para iniciar la búsqueda.](capturas/actualizaciones/inicial-oscuro.webp)](capturas/actualizaciones/inicial-oscuro.webp)

Si hay un error de conexión o la verificación falla, el actualizador muestra
un mensaje y PyGebra sigue disponible. Puedes volver a buscar o usar el
instalador de GitHub tras [verificar su SHA-256](releases.md#verificar-una-descarga).

### Distribución y verificación

Desde v0.20.0, el actualizador valida los certificados HTTPS con la API de
certificados de Windows (CryptoAPI). Windows puede obtener los certificados
raíz que falten al validar la consulta a GitHub y las descargas. PyGebra
comprueba también el nombre del servidor y verifica por separado el SHA-256
del instalador.

Desde v0.20.0, cada intento usa una carpeta `PyGebra-actualizacion-*` bajo
`%TEMP%`. Un fallo de descarga descarta los archivos de ese intento. Cuando
se cierra PyGebra, la limpieza espera si el instalador aún necesita el EXE.
El instalador se inicia con `/SILENT /ACTUALIZAR=1`, espera a que cierre
PyGebra, reemplaza `_internal` y mantiene el mismo AppId y AUMID.

CI conserva builds temporales; el workflow de [releases](releases.md) publica
la distribución estable al promover a `main`, tras validar el candidato y superar
CI, build y smoke. GitHub Actions crea el tag automáticamente. El paquete no está
firmado digitalmente: Windows puede mostrar el editor como desconocido.

## Construir el instalador

La cadena de distribución mantiene el launcher y su configuración `onedir` y
`windowed` en `AlgebraLineal.spec`:

```text
Código → PyInstaller → dist/AlgebraLineal/ → Inno Setup → instalador .exe
```

El análisis estático de PyInstaller no ve los módulos que Django importa por
nombre (context processors, vistas, servicios y las librerías de
`{% load %}` en `templatetags/`), y su hook de Django no localiza `settings`
porque vive en `frontend/web/algebra_web/`. Por eso `hiddenimports` en
`AlgebraLineal.spec` los enumera explícitamente: cada módulo nuevo de ese tipo
se añade ahí, y `tests/test_desktop.py` comprueba que las librerías de
`templatetags/` estén en la lista. Si falta uno, la aplicación instalada
responde `500` aunque la suite pase.

En una PC de desarrollo Windows con Python x64, instala **uv** e
[Inno Setup 6.6.0 o posterior](https://jrsoftware.org/isdl.php). Inno Setup convierte
la carpeta construida en un instalador con accesos directos y desinstalador.
La versión 6.6.0 introduce `WizardStyle=modern dynamic windows11`, que el
instalador usa para seguir el tema de Windows. CI valida la distribución con
Inno Setup 6.7.3. PowerShell 5.1 o posterior es suficiente.

Desde la raíz, un solo comando genera la distribución completa:

```powershell
.\scripts\build_windows.ps1
```

El script valida herramientas y Python x64, ejecuta `uv lock --check` y
`uv sync --locked --group dev`, limpia los artefactos de esa fase, construye el
`.spec`, verifica el ejecutable, prepara WebView2, compila Inno Setup y comprueba
el instalador. Cada comando conserva su salida y un fallo detiene el proceso.
La versión se lee de **`project.version` en `pyproject.toml`** y se pasa a Inno
Setup; no se mantiene otra copia manual. El script admite tres o cuatro
componentes numéricos; la política de publicación usa solo tres (`X.Y.Z`), según
[Versionado](releases.md#versionado).

El `.spec` también genera `build/windows-version-info.txt` mediante
`scripts/windows_version_info.py`, sin dependencias adicionales. El recurso
`VSVersionInfo` identifica `AlgebraLineal.exe` como **PyGebra** en Propiedades →
Detalles y las APIs de Windows: producto y descripción PyGebra, compañía
Proyecto PyGebra, nombre original AlgebraLineal.exe y versiones de archivo y
producto tomadas de `pyproject.toml`. El build verifica estos valores incluso
con `-Target Installer`, para impedir empaquetar un EXE obsoleto.

También puedes construir por fases:

```powershell
# Solo PyInstaller (no requiere Inno Setup):
.\scripts\build_windows.ps1 -Target App

# Solo instalador, usando el build ya existente:
.\scripts\build_windows.ps1 -Target Installer

# Si ISCC.exe está en una ubicación personalizada:
.\scripts\build_windows.ps1 -IsccPath 'C:\Herramientas\Inno Setup 6\ISCC.exe'
```

`-Target Installer` empaqueta la carpeta existente: si cambiaste el código,
ejecuta primero `-Target App` o usa el comando completo. El equivalente directo
para PyInstaller, después de sincronizar dependencias, sigue siendo:

```powershell
uv run --locked pyinstaller --noconfirm --clean AlgebraLineal.spec
```

La configuración del instalador vive en `installer/AlgebraLineal.iss`. El script
invoca `ISCC.exe` con `/DAppVersion` y `/DProjectRoot`; para evitar omisiones de
prerrequisitos se recomienda compilarla mediante `-Target Installer`.

El asistente usa `WizardStyle=modern dynamic windows11`, un estilo integrado en
Inno Setup que sigue el tema claro u oscuro de Windows sin archivos de estilo
externos. La página de carpeta está desactivada (`DisableDirPage=yes`): la
instalación por usuario va siempre a `%LOCALAPPDATA%\Programs\AlgebraLineal` y
la página **Listo para Instalar** muestra esa ubicación, los accesos directos y
el estado de WebView2 (`AlwaysShowDirOnReadyPage=yes` + `UpdateReadyMemo`). Al
instalar una versión sobre otra existente se reutiliza la carpeta y la entrada de
**Aplicaciones instaladas** de la instalación previa. Para instalaciones avanzadas
o automatizadas sigue funcionando el parámetro estándar de Inno Setup, con o sin
`/VERYSILENT`:

```powershell
$installer = Get-Item .\dist\installer\PyGebra-Setup-*.exe
& $installer.FullName /DIR="C:\Otra\Ruta"
```

```text
dist/
├── AlgebraLineal/
│   ├── AlgebraLineal.exe
│   └── _internal/              # Python, dependencias, templates y recursos locales
└── installer/
    └── PyGebra-Setup-<version>.exe
```

`build/` y `dist/` están ignorados por Git. El script descarga el bootstrapper
desde Microsoft, comprueba su firma Authenticode y lo reutiliza en
`build/prerequisites/`. Puedes borrar ese archivo para descargarlo de nuevo.
Al instalar, se ejecuta desde `{app}\prerequisites`, solo si falta WebView2; la
aplicación se ejecuta desde su carpeta instalada. La detección consulta las
claves oficiales `pv` de HKCU y HKLM (vista de 32 bits para la instalación por
equipo), exige un runtime compatible con pywebview y evita el fallback a MSHTML.
Consulta la [distribución de WebView2](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution).

En `.github/workflows/ci.yml`, la suite Python de Windows corre en paralelo con
el empaquetado. El job de empaquetado usa Inno Setup de la distribución oficial
firmada, construye la aplicación y el instalador, prueba la instalación limpia y
la actualización desde la última release estable, y conserva el instalador como
artifact temporal para revisión. El check «Distribución de Windows» exige que
ambos jobs pasen. Ubuntu ejecuta su propia suite y verificaciones.

## Comprobar la distribución real

En una cuenta Windows **sin una instalación previa de PyGebra**, ejecuta:

```powershell
$installer = Get-Item .\dist\installer\PyGebra-Setup-*.exe
.\scripts\test_windows_distribution.ps1 -InstallerPath $installer.FullName
```

La prueba instala en una carpeta nueva de `%LOCALAPPDATA%\Programs` fuera del
repositorio. Comprueba ambos accesos directos y que el ejecutable sea `windowed`,
abre desde Inicio, resuelve por Gauss y Gauss-Jordan, las cuatro operaciones
matriciales básicas escritas como expresiones (`A + B`, `A - B`, `kA`, `A^T`),
los productos `AB` y `Ax` comparando lecturas, la ruta histórica de expresiones y la ecuación
`Ax = b` (solución fraccionaria comparando métodos y un caso
rectangular 3×2) a través del Django/Waitress empaquetado, leyendo las celdas
exactas que el formato Exacto/Decimal envuelve en `<span data-numeric>`,
solicita CSS/JS (incluidos `expresiones.js`, `ecuaciones.js` y `numeros.js`) e
icono, cierra la ventana y
verifica que el proceso y el servidor terminan. Repite la apertura y luego
desinstala comprobando que se eliminaron archivos, registro y accesos directos.
Si esta máquina ya tiene
PyGebra instalada, el script se detiene a propósito: necesita una
cuenta o entorno limpio para no modificar esa instalación.

### Actualizar desde una versión publicada

La actualización mantiene el AppId `{D0455B79-7F5E-4C78-9F3B-F47187E9A83A}`,
el AUMID `PyGebra.Desktop`, `AlgebraLineal.exe` y la carpeta previa
(`UsePreviousAppDir=yes`). `UsePreviousGroup=no` crea el grupo PyGebra.
`[InstallDelete]` elimina primero `{app}\_internal` completo: en un paquete
PyInstaller `onedir`, sobrescribir dejaría módulos y DLL obsoletos de la versión
anterior. Esa carpeta solo contiene archivos generados; las preferencias viven
en `%LOCALAPPDATA%\PyGebra`. Después elimina únicamente los `.lnk` históricos
del usuario: `Start Menu\Programs\Álgebra Lineal\Álgebra Lineal.lnk` y
`Desktop\Álgebra Lineal.lnk`. No borra otros directorios ni archivos ajenos.

Antes de tocar archivos, el instalador comprueba el mutex
`PyGebra.Desktop.Ejecutandose` que abre la app: si PyGebra sigue abierta pide
cerrarla (en una actualización lanzada desde la app espera hasta 15 s a que se
cierre sola). `SetupMutex` impide ejecutar dos instaladores a la vez.

CI ejecuta este escenario en cada build: descarga la última release publicada,
verifica su SHA-256 e instala el candidato encima. Para probarlo a mano en una
cuenta limpia, descarga un instalador **publicado** (0.8.0, 0.9.0 o posterior)
y verifica su SHA-256. Después ejecuta el smoke con ambos instaladores:

```powershell
$installer = Get-Item .\dist\installer\PyGebra-Setup-*.exe
.\scripts\test_windows_distribution.ps1 -InstallerPath $installer.FullName `
  -PreviousInstallerPath 'C:\Pruebas\AlgebraLineal-Setup-0.8.0.exe' -PreviousDesktopIcon
# Repetir sin -PreviousDesktopIcon para cubrir el acceso opcional ausente.
```

El script reconoce la base (histórica «Álgebra Lineal» 0.8.0 o PyGebra),
comprueba su identidad y su AUMID, crea un archivo obsoleto dentro de `_internal`
que la actualización debe eliminar, instala el candidato
**sin `/DIR`** para comprobar que recupera la carpeta previa, exige los accesos
PyGebra y la ausencia de ambos históricos, consulta nombre/publisher/versión
en el registro de desinstalación, verifica los metadatos del EXE, abre dos veces
la aplicación y desinstala sin dejar accesos huérfanos. También exige una única
entrada de PyGebra en Aplicaciones y un único acceso en Inicio y en el escritorio. Un archivo ajeno creado
por la prueba en el grupo antiguo debe sobrevivir a actualización y
desinstalación; el script retira únicamente ese archivo de prueba al terminar.

### Autoactualización desde la app instalada

`-AutoUpdate` recorre lo que hace un usuario en **Actualizaciones**: la versión
anterior, instalada y abierta, busca, descarga, verifica e instala el candidato con
su propio actualizador, se cierra sola y el instalador la reabre. CI lo ejecuta tras
las otras dos pruebas, con la release publicada más reciente **anterior** al
candidato como base (sin acceso de escritorio).

| Parte | Real o simulada |
|---|---|
| Base publicada instalada, ventana WebView2, Waitress y mutex | Real |
| Código de `actualizador/` de la base: consulta, descarga a `%TEMP%`, SHA-256, lanzamiento con `/SILENT /NORESTART /ACTUALIZAR=1`, cierre propio y borrado de la descarga | Real |
| Botón de la página | Sustituido: el script pide los mismos `POST /actualizaciones/<paso>/` que envía `actualizaciones.js` y sigue `/actualizaciones/estado/` |
| Instalador candidato: espera al mutex, `[InstallDelete]`, accesos, registro y reapertura | Real |
| Preferencias en `%LOCALAPPDATA%\PyGebra` guardadas desde la base | Real (se comprueban en las dos aperturas y tras desinstalar) |
| GitHub (`api.github.com` y `github.com/.../releases/download/`) | **Simulado**: un proxy HTTPS local (`HTTPS_PROXY`) sirve el candidato y un `SHA256SUMS.txt` con su SHA-256. Las descargas no pasan por la redirección de GitHub a su CDN |
| Certificado de GitHub | **Simulado**: una CA temporal se añade a `LocalMachine\Root` solo durante la prueba y se retira al terminar |

También ensaya dos fallos con la app abierta: GitHub no disponible
(`error_conexion`) y un `SHA256SUMS.txt` que no coincide (`checksum_invalido`).
En ambos la versión instalada no cambia y no queda nada en `%TEMP%`.

Como confía temporalmente en una CA, el script se niega a ejecutarse fuera de
GitHub Actions o de Windows Sandbox (usuario `WDAGUtilityAccount`) y exige
permisos de administrador. Para probarlo en local, mapea en una Sandbox los dos
instaladores y el script, y ejecuta en ella:

```powershell
$sha256 = (Get-FileHash C:\Pruebas\PyGebra-Setup-0.20.3.exe -Algorithm SHA256).Hash
.\test_windows_distribution.ps1 -InstallerPath C:\Pruebas\PyGebra-Setup-0.20.3.exe `
  -PreviousInstallerPath C:\Pruebas\PyGebra-Setup-0.20.2.exe -AutoUpdate -InstallerSha256 $sha256
```

La Sandbox puede tener la red desactivada: así se comprueba además que la base no
llega al GitHub real.

La inspección visual de Inicio, búsqueda de Windows, `shell:AppsFolder`, el
asistente (incluido «Abrir PyGebra») y Configuración → Aplicaciones complementa
las comprobaciones automatizadas del registro y los accesos.

Completa esa prueba con una revisión visual: instalar normalmente, abrir desde
el acceso directo, resolver un sistema, verificar **Columnas pivote: C1, C3**,
cambiar entre tema claro y oscuro, cerrar, reabrir y desinstalar. La prueba por
HTTP no sustituye la inspección visual de pywebview. Para probar ausencia real
de WebView2, utiliza una VM limpia; no desinstales el runtime compartido de tu PC.

Consulta también [Pruebas](pruebas.md) y [Releases y checksums](releases.md).
