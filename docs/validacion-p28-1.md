# P28.1 — Modelo de selección matricial

Base: `origin/develop`, `a129c6f67c962a2613f8045afbd0b135bba79632`, que incluye
PyGebra 0.9.0 y Operandos + teclado matemático visual (#82).
Rama: `feature/p28-1-seleccion-matricial`. Destino: `develop`.
Validación: 9–10 de octubre de 2026, America/Managua.

## Inspección y arquitectura

| Superficie | Infraestructura reutilizada | Integración |
| --- | --- | --- |
| Operaciones | Tablas de símbolos, memoria por tipo y `expresiones.js` | Estado por tabla; renombrar conserva identidad, cambiar tipo o eliminar limpia. |
| Inversa | `matriz_entrada`, renderizador de A y B adicional | Transferencia explícita al redimensionar; cambiar aplicación elimina B; vector b excluido. |
| Ax=b | Tablas separadas A/b y renderizador de `ecuaciones.js` | Selección solo en A; x y vector b excluidos. |
| Reducción | `input[data-cell]`, memoria de dimensiones y `[A | b]` | Selección manual de cuadrícula completa; comandos sobre A; alternar a texto limpia. |
| Compartidos | `entradas.js`, teclado contextual, `disclosure`, tokens y runners DOM | Una lectura de filas para pegado y selección; Escape consumido antes de otros componentes. |

`seleccion_matricial.js` contiene todo el modelo y sus gestos/comandos. Un Map
asocia cada tabla editable con coordenadas, celda actual, referencia, extremo, tipo y comando
de origen. Una sola matriz tiene selección activa; las demás conservan su propio
conjunto inactivo. El estado no depende del nombre ni de la posición del operando.

La API consulta selección activa, celdas ordenadas e inputs vigentes, dimensiones,
límites y geometría rectangular, y permite limpiar/reemplazar conjuntos. Los
renderizadores recortan coordenadas al cambiar dimensiones y notifican reemplazos.
El observador de formularios y las consultas sincronizadas eliminan estados retirados.
Contrato completo y ejemplos: [selección matricial](seleccion-matricial.md).

## Comportamiento y decisiones

- Clic normal mantiene la edición y establece referencia sin crear selección.
  Shift+clic dentro del input enfocado conserva la selección textual.
- Shift+flechas solo consume el evento con selección matricial activa en esa matriz.
  Las flechas normales conservan las guardas P27, selección textual e IME.
- El primer Escape limpia la selección. Teclado y buscador respetan
  `defaultPrevented`; otra pulsación puede cerrar o limpiar esos componentes.
- Los siete comandos actúan solo sobre A en `[A | b]`, incluida Toda/Fila/Columna.
  La columna actual se deshabilita si la celda actual está en b. La selección manual
  sí puede incluir b, para conservar la geometría de navegación y pegado existentes.
- Principal admite matrices rectangulares. Secundaria y triangulares se deshabilitan
  fuera de matrices cuadradas; las triangulares incluyen la diagonal. Se adopta
  este dominio conservador porque la triangularidad usual corresponde a matrices
  cuadradas. La ayuda lo explica.
- Los conjuntos son posicionales y no se regeneran al crecer. Un comando se recorta
  además a A si una columna pasa a ser b al redimensionar.
- El menú compacto se integra junto a la cuadrícula y se envuelve cuando falta
  espacio. Usa summary/botones nativos y nombres accesibles por matriz. Los cambios
  importantes se anuncian en una región viva, sin ruido por cada foco.
- Bordes doble/discontinuo distinguen selección activa/inactiva; el anillo de foco
  queda fuera. Se reutilizan tokens y colores del sistema en forced-colors.

No se cambia el diseño solicitado fuera de estas decisiones de dominio y b.
Sin resultados/procedimientos/vectores seleccionables, arrastre, nuevos encabezados,
conversión a ARIA grid, persistencia, formatos de portapapeles ni undo.
P28.0 ya estaba validado manualmente y no se repitió.

## Archivos

Rutas relativas al repositorio; no se cambia backend matemático ni dependencias.

| Área | Archivos |
| --- | --- |
| Modelo nuevo | `frontend/web/calculadora/static/calculadora/seleccion_matricial.js` |
| Infraestructura compartida | `frontend/web/calculadora/static/calculadora/entradas.js`, `teclado.js`, `buscador.js` |
| Ciclo de vida por herramienta | `frontend/web/calculadora/static/calculadora/expresiones.js`, `inversa.js`, `ecuaciones.js`, `matriz.js` |
| Presentación | `frontend/web/calculadora/static/calculadora/styles/modules.css` |
| Menú compartido nuevo | `frontend/web/calculadora/templates/calculadora/components/seleccion_matricial.html` |
| Cuatro inclusiones | `frontend/web/calculadora/templates/calculadora/modules/expresiones/index.html`, `inversa/index.html`, `ecuaciones/index.html`, `sistemas/index.html` |
| Runners/contratos ampliados | `tests/entrada_edicion_browser.js`, `tests/entrada_edicion_browser.py`, `tests/pulido_browser.js`, `tests/test_entrada_edicion.py` |
| Documentación | `docs/seleccion-matricial.md`, `docs/validacion-p28-1.md`, `docs/pruebas.md`, `docs/README.md` |

## Verificación

Comandos y acceso a los runners: [pruebas](pruebas.md#p281--selección-matricial).

- Runner P27/P28.1: **108/108**; con forced-colors activo: **112/112**.
- Pulido: **16/16**, incluida altura del primer viewport, separación de etiquetas
  y nombres accesibles de los siete comandos tras renombrar un operando.
- Suite completa: **1640/1640**.
- Doce runners anteriores: **308/308**; junto con P28.1, **416/416** en los trece
  runners normales. Forced-colors repite los 108 y añade cuatro comprobaciones.
- `manage.py check`, compileall de backend/frontend/tests, `uv lock --check`,
  sintaxis de ocho scripts y dos runners JS, y `git diff --check`: correctos.

| Runner existente | Resultado final |
| --- | --- |
| `operandos_browser` | 23/23 |
| `entradas_browser` | 19/19 |
| `inversa_browser` | 7/7 |
| `feedback_browser` | 19/19 |
| `buscador_browser` | 16/16 |
| `pulido_browser` | 16/16 |
| `residual_browser` | 39/39 |
| `claridad_browser` | 30/30 |
| `teclado_browser` | 32/32 |
| `presentacion_browser` | 14/14 |
| `escritorio_browser` | 27/27 |
| `resultado_browser` | 66/66 |
| `entrada_edicion_browser` | 108/108; 112/112 con forced-colors |

El runner ampliado cubre las cuatro herramientas, los siete comandos, rectangularidad,
gestos, Escape, texto, flechas, teclado matemático, API atómica, dimensiones/columnas,
celda actual independiente del ancla de Shift,
reemplazos, dos matrices, tipos, B adicional, resultado vigente y POST sin persistencia.
Mide selección/foco/menú y desborde a 1280×650, 744×521 y 320×650 en claro/oscuro.

QA directa en Browser: Ctrl/Shift reales, teclado y menú operable con Enter,
consumo de Escape por orden, foco seleccionado en claro/oscuro, menú sin modificadores
a 320 px y ventana mínima 744×521. Sin desborde de página ni errores de consola
en esas interacciones. Las capturas locales conservan claro, oscuro, móvil, mínimo
y forced-colors. Chrome con foco y forced-colors emulados complementa Browser,
cuya API no ofrece esa emulación; no se inyecta una paleta artificial.

La prueba de mutación quitó temporalmente la guarda de Escape del teclado: los
cuatro casos por herramienta fallaron y volvieron a pasar al restaurarla.
Durante la validación se corrigieron tres regresiones de disposición/nombres
detectadas por Pulido. La ejecución interrumpida por el límite de uso detectó dos
enlaces al informe todavía no creado; se completó el documento antes del cierre.
Historial de escritorio tuvo un fallo intermitente al compartir una sesión con
otros runners; dos ejecuciones aisladas confirmaron 27/27 (la última con el runner
original sin instrumentación). No se alteró la navegación de escritorio ni se
relajaron sus asserts. Resultados necesitó más de 120 segundos para completar
sus 66 casos de renderizado; con tiempo suficiente pasó sin errores de consola.

## Límites y entrega

No se volvió a probar el portapapeles de WebView2. No se valida aquí un lector
de pantalla físico, alto contraste nativo de Windows, gestos táctiles físicos
ni el instalador. Los viewports y forced-colors son emulación, no certificación
de esos entornos.

Sin merge, versión, tag ni release. El archivo preexistente no rastreado
`backend/factorizacion_LU.py` queda fuera del incremento. CI se informa por
separado al abrir el PR; las comprobaciones locales no sustituyen su resultado.
