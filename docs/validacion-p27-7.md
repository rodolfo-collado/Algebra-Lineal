# P27.7 — Experiencia de escritorio

Base: `origin/develop` en `396985a`, merge de P27.6 (#75).
Rama: `feature/p27-7-experiencia-escritorio`.
Validación: 5 y 6 de octubre de 2026, America/Managua.

## Alcance y resultado

| Incidencia | Comportamiento |
| --- | --- |
| UI-18 | Solo con `<html data-desktop>`: Alt+← → `history.back()` y Alt+→ → `history.forward()`, sin pila propia ni controles visibles. Se ignoran Ctrl, Shift, AltGr, composición IME y eventos ya atendidos. Las cuadrículas de Matrices y Vectores dejan Alt+flecha al historial, como ya hacían las otras tres. La web no intercepta nada. |
| UI-19 | `pageshow` restaurado cierra el Menú (`data-drawer`, sidebar, fondo, `inert`, `aria-expanded`, foco fuera) y vuelve a aplicar tema, Exacto/Decimal y precisión sin recalcular, sin stale y sin repetir anuncios. La espera de P27.4 sigue en `feedback.js`. Formularios de cálculo y selectores de formato con `autocomplete="off"` (ver hallazgos). |
| UI-61 | 404 propio con la interfaz normal; 400, 403, CSRF y 500 con una base mínima sin catálogo, `reverse()` ni JavaScript. Identidad PyGebra, mensaje breve, «Ir al inicio»; sin traceback ni datos internos. |
| UI-69 | Ventana maximizada (no pantalla completa) con barra de título, `resizable=True` y `min_size`. Al restaurar vuelve a un tamaño centrado que cabe en el área útil del monitor principal; no se guarda tamaño, posición ni monitor. |
| UI-70 | Entre aperturas solo `pygebra-tema`, `pygebra-formato-numerico` y `pygebra-precision-decimal`, en `%LOCALAPPDATA%\PyGebra\preferencias.json`. WebView2 sigue en modo privado y Waitress en puerto efímero. Categorías del Menú en `sessionStorage`. |
| UI-71 | Menú contextual nativo de WebView2 filtrado a Cortar, Copiar, Pegar y Seleccionar todo; sin acciones útiles no aparece. Atajos del navegador y DevTools siguen desactivados. |

No hay cambios matemáticos, de versión, dependencias, AppId, AppUserModelId,
`AlgebraLineal.exe` ni carpeta de instalación. No se hace merge, tag ni release.

## Decisiones distintas de la propuesta inicial

Erving aprobó dos cambios tras la inspección en WebView2 real (6 de octubre):

1. **UI-70: archivo propio en lugar de perfil WebView2 persistente y puerto
   preferido.** Con `private_mode=False` y un perfil propio, WebView2 guardó en
   disco lo enviado en un formulario (`Web Data`, tabla
   `autofill_edge_field_values`) aunque el campo tenía `autocomplete="off"`,
   además de un `History` con las URL visitadas (los enlaces «También puedes
   explorar» llevan el sistema del usuario) y la caché HTTP con páginas de
   resultado. Waitress fija `SO_REUSEADDR`: en Windows una segunda instancia
   enlazaba el mismo puerto sin error, y un ocupante normal devolvía WinError
   10013, no 10048. El archivo propio guarda solo las tres claves, no depende del
   origen y evita el puerto preferido (8765 era además el del servidor de
   desarrollo).
2. **UI-71: menú nativo filtrado en lugar de un menú propio en JavaScript.**
   `ContextMenuRequested` (SDK 1.0.3856 incluido en pywebview 6.2.1) permite
   quitar elementos. El menú original de un campo editable traía Emoji,
   Deshacer/Rehacer, Pegar como texto sin formato, Imprimir, Dirección de
   escritura y «Más herramientas». Pegar nativo no pide permisos de portapapeles
   ni un puente Python, y el foco no sale del campo. Costo: se accede por
   `window.native.webview`, atributo interno de pywebview; si cambia, la ventana
   queda sin menú, como antes. Las etiquetas siguen el idioma de Windows.

Complementos dentro de la dirección acordada:

- **Geometría al restaurar (UI-69).** En este equipo, al restaurar la ventana
  maximizada volvía a 1100×760 lógicos y se salía por debajo de la pantalla.
- **`autocomplete="off"` (UI-19).** WebView2 no usa bfcache: volver recarga desde
  la caché y restaura los formularios después de los scripts diferidos. Se
  observó el selector en Decimal con valores exactos (preferencia Exacto) y un
  campo editado con el resultado marcado como vigente.
- **Escrituras en serie.** `numeros.js` envía formato y precisión a la vez y
  Waitress usa varios hilos; un cerrojo evita que una escritura pise a otra y que
  Windows rechace el reemplazo mientras otro hilo lee el archivo.

## Arquitectura final

```text
desktop.py ─ Django (DESKTOP_MODE, DEBUG=False) ─ Waitress 127.0.0.1:<efímero>
    └─ pywebview/WebView2 (modo privado) ── carga http://127.0.0.1:<puerto>/
            └─ POST /preferencias/ ─ Django ─ %LOCALAPPDATA%\PyGebra\preferencias.json
```

Ruta: `desktop.preferences_path()` → `%LOCALAPPDATA%\PyGebra\preferencias.json`,
fuera de Program Files, de la carpeta instalada, de `_MEIPASS`, del repositorio y
de temporales. Sin una carpeta de usuario absoluta no se guarda nada. Las
actualizaciones lo conservan y la desinstalación no lo borra.

| Se conserva entre aperturas | Solo durante la ejecución o nunca |
| --- | --- |
| tema claro/oscuro | categorías del Menú (`sessionStorage`) |
| Exacto/Decimal | cajón, URL, herramienta, formularios, matrices, vectores |
| precisión decimal | expresiones, resultados, procedimientos, stale, scroll, foco, historial |

Una segunda instancia usa otro puerto y su propia sesión privada, y comparte el
mismo archivo de preferencias; no hay single-instance ni sincronización de la UI.
Las actualizaciones del JSON se coordinan entre procesos mediante
`preferencias.lock`, un archivo vacío sin datos del usuario.

La auditoría independiente del 6 de octubre encontró pérdida de preferencias
por peticiones fuera de orden y por escrituras entre instancias. Se corrigen con
envíos en serie, solo del control cambiado, y un lock que cubre lectura y reemplazo.
También se limpian temporales ante errores de escritura y se captura el fallo
de registro del menú contextual para conservar el menú desactivado.

## Pruebas automatizadas

| Comando | Resultado |
| --- | --- |
| `uv run --locked python --version` | Python 3.13.3 |
| `uv run --locked python -m unittest discover -v` | 1597 pruebas, OK (1 omitida) |
| `uv run --locked python manage.py check` | sin problemas |
| `uv run --locked python -m compileall -q backend frontend tests main.py manage.py desktop.py` | OK |
| `uv lock --check` · `git diff --check` | OK |

Runners DOM:

| Runner | Resultado |
| --- | --- |
| `tests.escritorio_browser` (P27.7, 8882) | 25/25 en el Browser integrado |
| teclado · buscador · feedback | 30/30 · 16/16 · 19/19 |
| presentación · resultado · entradas · operandos · inversa | 10/10 · 66/66 · 19/19 · 15/15 · 7/7 |

El panel del Browser estaba oculto y ahí `requestAnimationFrame` no avanza: el
runner P27.7 espera con temporizador y los demás se ejecutaron en Chrome headless
por CDP con foco emulado. Sin foco emulado, teclado (5/30), buscador (15/16) y
feedback (18/19) fallaban igual en `origin/develop`: dependen del foco de la
ventana, no de P27.7. La consola solo registró los estados HTTP esperados de
las páginas de error cargadas a propósito.

## QA real en WebView2

`desktop.py` desde el código, configuración de release (sin depuración),
runtime 154.0.4258.53.

| Comprobación | Resultado |
| --- | --- |
| Abre maximizada, en Inicio y con el Menú cerrado | ✓ en tres arranques |
| Restaurar y redimensionar | ✓ cabe en el área útil tras la corrección; no vuelve a maximizarse |
| Categoría del Menú tras cerrar y reabrir | ✓ no se recuerda |
| Volver tras GET y tras POST | ✓ con `history.back()`/`forward()` en WebView2 durante la inspección: resultado y datos recuperados, sin diálogo de reenvío |
| Copiar · Cortar · Pegar desde el menú nativo | ✓ portapapeles verificado; `deleteByCut` e `insertFromPaste`; el foco sigue en el campo y el teclado matemático abierto |
| Menú nativo filtrado | ✓ solo las cuatro acciones; estados nativos (sin selección, Cortar/Copiar desactivados) |
| Shift+F10 | ✓ abre el mismo menú filtrado |
| DevTools y atajos | `AreDevToolsEnabled` y `AreBrowserAcceleratorKeysEnabled` en `False` al iniciar; el hook no los toca |
| Escape con el menú abierto | no concluyente (ver abajo) |

**Escape/foco: limitación de la herramienta de QA.** El menú se cerró, pero tras
el Escape sintético (SendInput o la herramienta de control de Windows) el primer
plano pasó a `TextInputHost.exe` («Experiencia de entrada de Windows»), así que
una tecla posterior no llegaba a PyGebra y no se pudo concluir si el foco vuelve
al campo. Erving detuvo esa automatización; se considera una limitación de la
QA, no un fallo de PyGebra. Seleccionar una acción (Cortar, Copiar, Pegar)
dejó el primer plano en PyGebra.

Tampoco se ejecutaron con teclas o botones físicos: Alt+←/→ real, botones
laterales del ratón, F5/Ctrl+P/Ctrl+F/F12, Copiar sobre texto de resultado y el
cierre y reapertura con tema oscuro, Decimal y precisión 8. Los cubren el runner
(incluido un «arranque nuevo» sin `localStorage` ni `sessionStorage`), el smoke
Waitress y las pruebas Python; conviene confirmarlos a mano en la app instalada.

## Build Windows

`scripts/build_windows.ps1 -Target App` compila con PyInstaller y el paquete
incluye `frontend.web.calculadora.preferencias` y las plantillas de error. El
smoke de instalación, dos aperturas y desinstalación queda a cargo del job
Windows de CI: en esta cuenta sigue una instalación residual antigua que el
script exige no tener.

## Archivos

- `desktop.py`, `frontend/web/algebra_web/settings.py`
- `frontend/web/calculadora/preferencias.py` (nuevo), `views.py`, `urls.py`,
  `context_processors.py`
- `templates/400.html`, `403.html`, `403_csrf.html`, `404.html`, `500.html`,
  `calculadora/errores/base.html`, `components/tema_inicial.html` (nuevos)
- `templates/calculadora/base.html`, `components/numeric_format.html` y los
  siete `modules/*/index.html`
- `static/calculadora/navigation.js`, `tema.js`, `numeros.js`, `matriz.js`,
  `vectores.js`
- `tests/test_escritorio.py`, `tests/test_paginas_error.py`,
  `tests/escritorio_browser.py`/`.js` (nuevos),
  `tests/test_desktop.py`, `tests/buscador_browser.js`,
  `tests/presentacion_browser.py`
- `docs/arquitectura.md`, `docs/ejecucion.md`, `docs/instalacion-windows.md`,
  `docs/interfaz.md`, `docs/pruebas.md`, `docs/validacion-p27-7.md` (nuevo)
