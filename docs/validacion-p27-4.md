# P27.4 — Feedback de cálculo, errores y confirmaciones

Base: `origin/develop` en `50ba4d0`, merge de P27.3 (#72).
Rama: `feature/p27-4-feedback-errores`.
Validación realizada el 5 de octubre de 2026, America/Managua.

## Cambios por incidencia

| Incidencia | Comportamiento implementado |
| --- | --- |
| UI-55 | Matrices e inversa usan la misma confirmación, antes de la acción principal. La respuesta enfoca el aviso, muestra la operación pendiente y aclara que el cálculo completo aún no se ejecutó. Continuar conserva la firma y Cancelar conserva la entrada. |
| UI-56 | Los botones de cálculo y Continuar muestran «Calculando…», conservan su ancho mínimo y exponen `aria-busy`. Se bloquean nuevos submits del mismo formulario sin deshabilitar el submitter. |
| UI-58 | Si existe `#resultado`, se conserva su navegación. En una respuesta con errores sin resultado se enfoca el primer control inválido útil, o el alert cuando no hay control. |
| UI-59 | Django renderiza los errores de campo con `.field-error`, ID y asociación accesible. Los errores generales usan un único `.alert.error`; los de grupo aparecen una vez junto al grupo. Las celdas de sistemas y vectores tienen errores asociados individualmente. |
| UI-60 | Los mensajes de celdas conservan A, B, b y los nombres introducidos por el usuario. Los steppers no aplican `lower` a etiquetas matemáticas. |
| UI-37 | Cambiar origen sincroniza destinos sin crear un aviso. Las casillas y Convertir sí validan destinos vacíos. Un mensaje servidor y uno cliente no se muestran simultáneamente para el mismo error; corregir limpia el estado. |

Los siete formularios con `action` terminado en `#resultado` son reducción,
Ax=b, inversa, operaciones con matrices, vectores, bases y romanos. Se revisaron
sus POST válidos, inválidos y estructurales; las dos herramientas con confirmación
siguen usando sus servicios y firmas originales.

## Modelo compartido de submit y restauración

`feedback.js` usa `data-calculo` para distinguir las acciones principales de
Agregar, Eliminar, Aplicar, Cancelar y los steppers. El primer submit se procesa
en el burbujeo hasta `document`, después de los validadores del formulario:
si se canceló, no hay busy y se revela el problema; si continúa, se guarda el
texto y ancho del botón y se aplican texto, `aria-busy` y `aria-disabled`.

El guard de captura cancela los siguientes submits mientras ese formulario
está enviándose. El botón permanece habilitado como control HTTP: su
`name=value`, incluida la firma de Continuar, sigue viajando en el POST.
No se añade ningún campo al contrato ni se modifica el cálculo.

`pageshow` restaura texto, ancho y atributos y vacía el estado. Un documento
nuevo tiene un estado vacío. No se introduce spinner ni animación nueva.

## Política de foco y presentación de errores

1. Resultado presente: mantener la navegación nativa a `#resultado`.
2. Confirmación pendiente: enfocar el aviso completo.
3. Respuesta marcada con errores: primer control con `aria-invalid=true`.
4. Grupo inválido: primer control visible, habilitado y útil del grupo.
5. Sin control concreto: enfocar el alert general o el mensaje de campo/grupo.

Una dimensión inválida enfoca la dimensión; una celda inválida, esa celda;
una matriz completa, su primera celda útil; una expresión, Expresión; destinos
vacíos, la primera casilla disponible; un non-field error, su alert.
Se omiten `hidden`, `disabled`, `inert`, `display:none` y `visibility:hidden`.
Se abren los `details` que contienen el problema. Un GET normal conserva el foco.

El desplazamiento se calcula después del foco, con margen de cabecera y la
altura real del dock contextual, incluida su transformación durante la entrada.
El teclado de P27.3 sigue respondiendo al foco. No se oculta para revelar errores.

La clase compartida de formularios conserva la validación de Django y une los
IDs de error con `aria-describedby`, preservando las ayudas existentes. Los
mensajes de campo usan una lista `.errorlist.field-error` y un solo `role=alert`
por campo/grupo. Los alerts generales no incluyen otro alert dentro ni un resumen
duplicado. Los errores de dimensiones del servidor no generan a la vez otro
mensaje cliente. Los errores de matriz global no se copian a todas las celdas.

Sin JavaScript se mantienen los mensajes, acciones y validación servidor.
La edición de matriz aumentada conserva su limitación previa: necesita JavaScript;
el sistema textual sigue disponible como alternativa sin JS.

Se conservaron los filtros de nombres de bases y clasificación, y la convención
matemática de entradas aᵢⱼ para A en el procedimiento: no alteran el símbolo
definido por el usuario ni son el error de capitalización corregido aquí.

## Resultados completos de validación

| Comando | Resultado |
| --- | --- |
| `uv run --locked python -m unittest discover -v` en la base | 1549 pruebas, OK, 63.002 s. |
| `uv run --locked python -m unittest discover -v` con P27.4 | 1556 pruebas, OK, 63.029 s. |
| `uv run --locked python -m unittest tests.test_feedback -v` | 7 pruebas nuevas, OK. Incluyen las siete herramientas, ayuda existente, error general único, matriz global, confirmación y símbolos. |
| `uv run --locked python -m unittest tests.test_documentacion -v` tras añadir este informe | 2 pruebas, OK; enlaces y bloques Markdown válidos. |
| `uv run --locked python manage.py check` | Sin problemas, 0 silenciados. |
| `uv run --locked python -m compileall -q backend frontend tests main.py manage.py desktop.py` | OK, sin salida de errores. |
| `uv lock --check` | OK; 30 paquetes resueltos, lock sin cambios. |
| `git diff --check` | OK. Los avisos LF/CRLF de Git no son errores de whitespace. |
| `node --check` en feedback, conversión, matriz y runner nuevo | OK. |

Las expectativas antiguas actualizadas corresponden al cambio intencional de
HTML accesible, posición de la confirmación y preservación de A/B. La base pasó
completa antes de editar; no se cambiaron expectativas por una regresión previa.

| Runner DOM | Resultado |
| --- | --- |
| `uv run --locked python -m tests.feedback_browser` — puerto 8880 | 19/19 |
| `uv run --locked python -m tests.entradas_browser` — puerto 8878 | 19/19 |
| `uv run --locked python -m tests.operandos_browser` — puerto 8877 | 15/15 |
| `uv run --locked python -m tests.inversa_browser` — puerto 8879 | 7/7 |
| `uv run --locked python -m tests.teclado_browser` — puerto 8766 | 30/30 |
| `uv run --locked python -m tests.presentacion_browser` — puerto 8876 | 10/10 |
| Total | **100/100**, sin errores JavaScript |

El runner nuevo cubre los diez requisitos obligatorios: busy y submitter,
cancelación cliente, segundo envío, confirmación y firma, campo asociado, alert
general, URL sin/con resultado, matriz global, destinos y `pageshow`. Añade
expresión, matriz aumentada, vectores, visibilidad del foco y flujos sin JS.

Comprobación de regresión: retirar únicamente `preventDefault` del guard del
segundo submit mediante una respuesta JS interceptada hace fallar el caso de
busy/resubmit (18/19). El código del repositorio no se alteró para esta prueba.

## QA en navegador

Entorno: Edge instalado en Windows, automatizado con Playwright existente.
Browser plugin no disponible; no se instalaron dependencias. URL de la aplicación:
`http://127.0.0.1:8880/`. Los scripts auxiliares y capturas quedaron fuera del repo.

| Comprobación | 1280×650 | 744×521 |
| --- | --- | --- |
| Identidad, contenido real y ausencia de pantalla/overlay de error | PASS | PASS |
| Entrada válida → Calcular → busy → resultado | PASS | PASS |
| Segundo click/Enter durante POST detenido | Un único POST | Un único POST |
| Submit inválido → documento nuevo → celda/error visibles sobre el dock | PASS | PASS |
| Cálculo costoso → confirmación visible → Continuar con firma → resultado | PASS | PASS |
| Cambiar origen sin aviso → quitar destinos → aviso → corregir sin aviso | PASS | PASS |
| Consola: errores o warnings de aplicación | Ninguno | Ninguno |

La confirmación completa se vio entre y=187.59 y 397.50 en 1280×650, y entre
y=121.44 y 352.95 en 744×521. En el error de celda, campo y mensaje terminaron
aproximadamente entre y=68 y 151, por encima del dock (y=522 y y=460).
El foco tenía un contorno visible. El botón mantuvo el mismo ancho antes y durante
busy. El cuerpo del POST de Continuar contenía exactamente la firma mostrada.

Las capturas muestran confirmación, error con teclado, aviso/corrección de bases
y busy. La captura de busy usa el mismo handler con un SubmitEvent DOM para
mantener visible el estado; el POST real y su bloqueo se verificaron por separado.
La restauración de Atrás también pasó en navegador; esa navegación reportó
`persisted=false`. El caso `pageshow` con `persisted=true` se prueba en DOM.

## Riesgos restantes y alcance

- Se verificó Edge; no se ejecutó QA en Firefox/Safari ni otros viewports.
- Las asociaciones y roles se comprobaron en DOM; falta una sesión con lector de pantalla real.
- El navegador de QA no reutilizó bfcache en el retorno real; el handler de restauración de un documento persistido está cubierto por el runner.

No se cambiaron umbrales, algoritmos, versión, dependencias, menú ni el flujo de
procedimientos. No se creó tag/release ni se hizo merge.

## Archivos modificados

La siguiente lista incluye cambios y archivos nuevos del incremento:

- `docs/validacion-p27-4.md`
- `frontend/web/calculadora/forms.py`
- `frontend/web/calculadora/forms_ecuaciones.py`
- `frontend/web/calculadora/forms_expresiones.py`
- `frontend/web/calculadora/forms_feedback.py`
- `frontend/web/calculadora/forms_inversa.py`
- `frontend/web/calculadora/forms_matrices.py`
- `frontend/web/calculadora/forms_romanos.py`
- `frontend/web/calculadora/static/calculadora/conversion.js`
- `frontend/web/calculadora/static/calculadora/entradas.js`
- `frontend/web/calculadora/static/calculadora/feedback.js`
- `frontend/web/calculadora/static/calculadora/matriz.js`
- `frontend/web/calculadora/static/calculadora/styles/components.css`
- `frontend/web/calculadora/static/calculadora/styles/modules.css`
- `frontend/web/calculadora/static/calculadora/vectores.js`
- `frontend/web/calculadora/templates/calculadora/base.html`
- `frontend/web/calculadora/templates/calculadora/components/confirmacion_costo.html`
- `frontend/web/calculadora/templates/calculadora/components/errores_campo.html`
- `frontend/web/calculadora/templates/calculadora/components/errores_generales.html`
- `frontend/web/calculadora/templates/calculadora/components/errores_grupo.html`
- `frontend/web/calculadora/templates/calculadora/modules/bases/index.html`
- `frontend/web/calculadora/templates/calculadora/modules/ecuaciones/index.html`
- `frontend/web/calculadora/templates/calculadora/modules/expresiones/index.html`
- `frontend/web/calculadora/templates/calculadora/modules/inversa/_confirmacion.html`
- `frontend/web/calculadora/templates/calculadora/modules/inversa/index.html`
- `frontend/web/calculadora/templates/calculadora/modules/matrices/_dimension.html`
- `frontend/web/calculadora/templates/calculadora/modules/romanos/index.html`
- `frontend/web/calculadora/templates/calculadora/modules/sistemas/index.html`
- `frontend/web/calculadora/templates/calculadora/modules/vectores/_fila.html`
- `frontend/web/calculadora/templates/calculadora/modules/vectores/index.html`
- `frontend/web/calculadora/views.py`
- `tests/feedback_browser.js`
- `tests/feedback_browser.py`
- `tests/operandos_browser.js`
- `tests/test_conversion_bases_web.py`
- `tests/test_ecuaciones_matriciales_web.py`
- `tests/test_feedback.py`
- `tests/test_matrices_web.py`
- `tests/test_matriz_inversa_web.py`
- `tests/test_multiplicacion_matrices_web.py`
- `tests/test_numeros_romanos_web.py`
- `tests/test_presupuesto_sistemas.py`
- `tests/test_resolver_sistema.py`
