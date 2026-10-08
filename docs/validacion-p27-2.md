# P27.2 — identidad PyGebra en Windows y distribución

Validación del 5 de octubre de 2026. Rama `feature/p27-2-identidad-pygebra`,
creada desde `origin/develop` en `709a75a` (incluye P27.1). Versión conservada:
`0.8.0`; no se crea tag, release ni merge.

## Resultado por requisito

| Requisito | Implementación |
| --- | --- |
| UI-01 | `AppName=PyGebra` identifica el asistente, Inicio, escritorio, desinstalador y registro de Aplicaciones. `UsePreviousGroup=no` evita reutilizar el grupo histórico; `[InstallDelete]` borra solo los dos `.lnk` históricos del usuario. AppId, AUMID y directorio previo se conservan. |
| UI-02 | `AppPublisher=Proyecto PyGebra`; la URL del repositorio no cambia. |
| UI-03 | El aviso de WebView2 pide volver a ejecutar el instalador de PyGebra. `APP_TITLE=PyGebra` permanece. |
| UI-04 | README, instalación, ejecución, identidad visual y releases utilizan PyGebra. La identidad visual distingue el producto de sus nombres técnicos. |
| UI-05 | El `.spec` genera un recurso `VSVersionInfo` desde `pyproject.toml`, sin dependencias nuevas. El build comprueba los metadatos del EXE, también al empaquetar una aplicación existente con `-Target Installer`. |
| UI-06 | Instalador `PyGebra-Setup-<versión>.exe` en Inno Setup, build, CI, release, checksums, fixtures y documentación. El artifact interno `algebra-lineal-windows` permanece. |

Los metadatos leídos del EXE construido mediante las APIs de Windows son:

```text
ProductName:      PyGebra
FileDescription:  PyGebra
CompanyName:      Proyecto PyGebra
OriginalFilename: AlgebraLineal.exe
FileVersion:      0.8.0
ProductVersion:   0.8.0
```

`scripts/windows_version_info.py` admite tres o cuatro componentes numéricos
de hasta 65535, completa el cuarto con cero para el recurso binario y conserva
la versión original en los campos de texto. Las pruebas cubren versiones futuras,
rechazo de formatos inválidos, generación determinista y serialización real
con PyInstaller en Windows.

## Nombres técnicos conservados

- `AlgebraLineal.exe` (archivo, proceso y `OriginalFilename`).
- `AlgebraLineal` en `%LOCALAPPDATA%\Programs\AlgebraLineal`,
  `dist/AlgebraLineal` y `build/AlgebraLineal`.
- `AlgebraLineal.spec` e `installer/AlgebraLineal.iss`.
- `AlgebraLineal-Waitress` (thread) y `AlgebraLineal-Smoke-<GUID>`
  (carpetas temporales de las pruebas existentes).
- Repositorio `rodolfo-collado/Algebra-Lineal`, proyecto `algebra-lineal`,
  paquete `frontend.web.algebra_web` y módulo Django `frontend.web.calculadora`.
- `ALGEBRA_DESKTOP`, `ALGEBRA_DESKTOP_DEBUG` y claves internas/localStorage.
- AppId `{D0455B79-7F5E-4C78-9F3B-F47187E9A83A}` y AUMID `PyGebra.Desktop`.

## Pruebas ejecutadas

| Verificación | Resultado |
| --- | --- |
| `uv run --locked python -m unittest discover -v` | OK: 1547 pruebas. |
| `uv run --locked python -m unittest tests.test_instalador tests.test_release tests.test_desktop -v` | OK: 76 pruebas. |
| `uv run --locked python manage.py check` | Sin incidencias. |
| `uv run --locked python -m compileall -q backend frontend tests main.py manage.py desktop.py` | OK. |
| `uv lock --check` | OK; pyproject y lockfile no cambian. |
| `git diff --check` | OK. |
| Build Windows: `scripts/build_windows.ps1` con Inno Setup instalado | OK; `AlgebraLineal.exe` y `PyGebra-Setup-0.8.0.exe` generados. |
| Parser PowerShell del smoke | Sin errores de sintaxis; archivos `.ps1` conservan UTF-8 con BOM para PowerShell 5.1. |
| Mutación temporal del límite de versión | La suite falla al invertir la condición; tras restaurarla, las tres pruebas de VersionInfo pasan. |
| Instalación limpia | OK en Windows Sandbox: dos aperturas y desinstalación. |
| Actualización real desde 0.8.0 con acceso de escritorio histórico | OK en Windows Sandbox. |
| Actualización real desde 0.8.0 sin acceso de escritorio histórico | OK en Windows Sandbox. |

El entorno de herramientas omite `OS`; para el build local se estableció
`$env:OS='Windows_NT'` y se indicó `-IsccPath` explícitamente. No se cambió
la lógica del script para esta particularidad del entorno.

## Actualización desde la release publicada 0.8.0

Base descargada de [v0.8.0](https://github.com/rodolfo-collado/Algebra-Lineal/releases/tag/v0.8.0):
`AlgebraLineal-Setup-0.8.0.exe`. SHA-256 verificado contra `SHA256SUMS.txt`:

```text
6bba9c42b1ebfebdc0439951704f80a245339bc9fddf97aeea665ab867e37263
```

Candidato local `PyGebra-Setup-0.8.0.exe`, SHA-256:

```text
4ecbb1828d952bfd10199aaaa4e51ac5b33be9f16f72de7b64e2b9b1cb297aa6
```

La cuenta habitual contiene accesos a una instalación existente. El smoke se
detuvo en su comprobación inicial sin instalar ni desinstalar nada. La alternativa
que movía esos accesos fue rechazada por la revisión automática y no se ejecutó.
Se preparó Windows Sandbox con registro y perfil independientes, entrada de
instaladores en solo lectura y una carpeta de salida para logs. La instalación
habitual no se comparte con el sandbox.

La prueba distingue instalación limpia, actualización con acceso histórico de
escritorio y actualización sin ese acceso. En cada actualización verifica
la base histórica, mismo AppId/AUMID, candidato instalado sin `/DIR`, carpeta
previa conservada, nuevos accesos, ausencia de históricos, registro de
desinstalación, metadatos del EXE, dos aperturas y desinstalación. Un archivo
ajeno del grupo histórico debe sobrevivir y solo se retira el archivo de prueba.

**Resultado real: PASS**, ejecutado con PowerShell 5.1.26100.9549 dentro de
Windows Sandbox, usuario `WDAGUtilityAccount`. No se usó una simulación de
accesos ni una recompilación de 0.8.0: la base es el instalador publicado
identificado por el checksum anterior. El candidato conserva la versión 0.8.0
porque este incremento no autoriza un bump.

Los tres logs locales están en `build/p27-2/sandbox-output/`:

- `smoke-clean.log`: instalación limpia, identidad PyGebra, dos aperturas y limpieza.
- `upgrade-desktop.log`: base histórica con escritorio, migración y limpieza.
- `upgrade-no-desktop.log`: base histórica sin escritorio, migración y limpieza.
- `result.txt` contiene `PASS`; `transcript.log` identifica cuenta y PowerShell.

Extracto de la actualización con escritorio:

```text
Base 0.8.0 verificada: Álgebra Lineal, Proyecto Álgebra Lineal, mismo AppId,
AUMID PyGebra.Desktop [...] (escritorio: True).
Identidad verificada: PyGebra, Proyecto PyGebra, EXE 0.8.0, accesos PyGebra,
AUMID PyGebra.Desktop y ningún acceso histórico.
Apertura 1: acceso directo, Django/Waitress [...] recursos y cierre OK.
Apertura 2: acceso directo, Django/Waitress [...] recursos y cierre OK.
Distribución verificada fuera del repositorio y desinstalada [...]
```

Carpetas temporales reales, conservadas al actualizar y eliminadas al desinstalar,
bajo `C:\Users\WDAGUtilityAccount\AppData\Local\Programs\`:

```text
Limpia:              AlgebraLineal-Smoke-3fc4ddb0625d4a3db3963f3fe79e2b6b
Con escritorio:      AlgebraLineal-Smoke-56e2bed5311a4c7bbc80f77b9ce70ed4
Sin escritorio:      AlgebraLineal-Smoke-7bbd4acca2ea43a9be67324603e23fb1
```

**Pendiente manual:** inspección visual de búsqueda, `shell:AppsFolder`, asistente
y Configuración de Windows. La comprobación automatizada del registro y los
accesos no sustituye esa inspección.

## Clasificación de la búsqueda final

| Patrón | Coincidencias legítimas restantes |
| --- | --- |
| `Álgebra Lineal` | Área académica del catálogo, navegación, breadcrumbs y sus pruebas; descripciones internas Django; migración de los accesos históricos, documentación y assertions negativas. No se cambia UI-07. |
| `Proyecto Álgebra Lineal` | Comprobación de la identidad de la base 0.8.0 en el smoke. Ningún publisher del candidato usa este texto. |
| `AlgebraLineal-Setup` | Solo el instalador publicado 0.8.0 utilizado para la migración y las pruebas de clasificación. Los consumidores de instaladores nuevos usan PyGebra. |
| `AlgebraLineal` | EXE, carpetas, spec/iss, thread, procesos, documentación técnica y pruebas de compatibilidad listados arriba. |

Se revisaron las apariciones con `rg` y `git grep`, clasificándolas antes de
editar y al finalizar. No quedaron usos incorrectos como identidad visible
del candidato. Los enlaces `/releases/latest` se conservan.

## Archivos modificados

1. `.github/workflows/ci.yml`
2. `.github/workflows/release.yml`
3. `AlgebraLineal.spec`
4. `README.md`
5. `desktop.py`
6. `docs/ejecucion.md`
7. `docs/identidad-visual.md`
8. `docs/instalacion-windows.md`
9. `docs/releases.md`
10. `docs/validacion-p27-2.md` (nuevo)
11. `installer/AlgebraLineal.iss`
12. `scripts/build_windows.ps1`
13. `scripts/test_windows_distribution.ps1`
14. `scripts/windows_version_info.py` (nuevo)
15. `tests/test_desktop.py`
16. `tests/test_instalador.py`
17. `tests/test_release.py`

Los instaladores y logs locales de `build/p27-2/` y `dist/` están ignorados
por Git; no se incluyen en los commits ni se publican como release.

Referencias de implementación: [UsePreviousGroup](https://jrsoftware.org/ishelp/topic_setup_usepreviousgroup.htm),
[InstallDelete](https://jrsoftware.org/ishelp/topic_installdeletesection.htm),
[spec de PyInstaller](https://pyinstaller.org/en/stable/spec-files.html) y
[configuración de Windows Sandbox](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file).
