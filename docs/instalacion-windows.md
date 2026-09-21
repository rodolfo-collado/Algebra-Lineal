# Instalación y distribución de Windows

[Índice de documentación](README.md) · [Portada](../README.md)

## Instalar como usuario

1. Descarga `AlgebraLineal-Setup-x.y.z.exe` desde la [última release estable](https://github.com/rodolfo-collado/Algebra-Lineal/releases/latest).
   Si aún no hay releases publicadas, espera la primera publicación estable.
2. Ejecuta el instalador: decide si quieres un acceso directo en el escritorio y
   pulsa **Instalar**.
3. Abre **Álgebra Lineal** desde el menú Inicio o el acceso directo opcional del escritorio.

No necesitas Git, Python, uv, PyInstaller, terminal ni acceso al repositorio.
El instalador no pide elegir una carpeta: la aplicación se instala para tu usuario
en `%LOCALAPPDATA%\Programs\AlgebraLineal`, sin solicitar privilegios de
administrador, y la pantalla **Listo para Instalar** muestra esa ubicación antes
de continuar. El asistente sigue el tema claro u oscuro de Windows y la aplicación
funciona sin una consola detrás.
Para quitarla, usa **Configuración → Aplicaciones → Álgebra Lineal → Desinstalar**.

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
los archivos y accesos directos de Álgebra Lineal; conserva WebView2, que puede ser
utilizado por otras aplicaciones.

CI conserva builds temporales; el workflow de [releases](releases.md) publica
la distribución estable después de validar un tag de `main`. El paquete no está
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
[Inno Setup 6.3 o posterior](https://jrsoftware.org/isdl.php). Inno Setup convierte
la carpeta construida en un instalador con accesos directos y desinstalador.
CI utiliza Inno Setup 6.7.3. PowerShell 5.1 o posterior es suficiente.

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
$installer = Get-Item .\dist\installer\AlgebraLineal-Setup-*.exe
& $installer.FullName /DIR="C:\Otra\Ruta"
```

```text
dist/
├── AlgebraLineal/
│   ├── AlgebraLineal.exe
│   └── _internal/              # Python, dependencias, templates y recursos locales
└── installer/
    └── AlgebraLineal-Setup-<version>.exe
```

`build/` y `dist/` están ignorados por Git. El script descarga el bootstrapper
desde Microsoft, comprueba su firma Authenticode y lo reutiliza en
`build/prerequisites/`. Puedes borrar ese archivo para descargarlo de nuevo.
Al instalar, se ejecuta desde `{app}\prerequisites`, solo si falta WebView2; la
aplicación se ejecuta desde su carpeta instalada. La detección consulta las
claves oficiales `pv` de HKCU y HKLM (vista de 32 bits para la instalación por
equipo), exige un runtime compatible con pywebview y evita el fallback a MSHTML.
Consulta la [distribución de WebView2](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution).

El job de Windows de `.github/workflows/ci.yml` instala Inno Setup desde su
distribución oficial firmada, construye ambos artefactos y ejecuta las pruebas.
Ejecuta también el smoke real y conserva el instalador como artifact temporal
para revisión (la retención se configura en el workflow). El job Linux conserva
sus verificaciones. Ninguno crea una Release.

## Comprobar la distribución real

En una cuenta Windows **sin una instalación previa de Álgebra Lineal**, ejecuta:

```powershell
$installer = Get-Item .\dist\installer\AlgebraLineal-Setup-*.exe
.\scripts\test_windows_distribution.ps1 -InstallerPath $installer.FullName
```

La prueba instala en una carpeta nueva de `%LOCALAPPDATA%\Programs` fuera del
repositorio. Comprueba ambos accesos directos y que el ejecutable sea `windowed`,
abre desde Inicio, resuelve por Gauss y Gauss-Jordan, las cuatro operaciones
matriciales básicas, los productos `AB` y `Ax` comparando métodos y la ecuación
`Ax = b` (solución fraccionaria comparando métodos y un caso
rectangular 3×2) a través del Django/Waitress empaquetado, solicita CSS/JS
(incluidos `matrices.js` y `ecuaciones.js`) e icono, cierra la ventana y
verifica que el proceso y el servidor terminan. Repite la apertura y luego
desinstala comprobando que se eliminaron archivos, registro y accesos directos.
Si esta máquina ya tiene
Álgebra Lineal instalada, el script se detiene a propósito: necesita una
cuenta o entorno limpio para no modificar esa instalación.

Completa esa prueba con una revisión visual: instalar normalmente, abrir desde
el acceso directo, resolver un sistema, verificar **Columnas pivote: C1, C3**,
cambiar entre tema claro y oscuro, cerrar, reabrir y desinstalar. La prueba por
HTTP no sustituye la inspección visual de pywebview. Para probar ausencia real
de WebView2, utiliza una VM limpia; no desinstales el runtime compartido de tu PC.

Consulta también [Pruebas](pruebas.md) y [Releases y checksums](releases.md).
