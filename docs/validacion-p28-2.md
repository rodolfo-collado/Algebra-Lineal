# P28.2 — Copiado matricial inteligente

Base: `origin/develop`, merge #83, `143f22f2a1a34cce486ac23d5090b9033da9c1d0`.
Rama: `feature/p28-2-copiado-matricial`. Destino: `develop`.
Validación: 10 de octubre de 2026, America/Managua.

## Arquitectura y alcance

Un nuevo `copiar_matricial.js` consume el snapshot vigente de
`seleccionMatricial.activa()`. La API P28.1 y su modelo no cambian. Usa los inputs,
coordenadas ordenadas, límites y rectangularidad ya calculados; no interpreta
comandos matemáticos ni vuelve a separar A/b. La plantilla compartida carga el
módulo solo en las cuatro herramientas con selección de entrada.

El listener de `copy` escribe TSV literal, tabla HTML y JSON de geometría v1.
La selección textual en input/textarea/página prevalece. No cambia paste,
cut, foco, valores, resultado vigente, teclado ni Escape; no añade roles grid,
CSS, dependencias ni operaciones matemáticas. Reutiliza la única región viva
de selección para éxito/fallo. No persiste metadata ni consulta el portapapeles
fuera de la acción explícita de copiar.

Contrato completo: [copiado matricial](copiado-matricial.md). El parser reutilizable
queda publicado para P28.3, sin conectarse al flujo de pegado.

## Formatos y seguridad

- `text/plain`: TAB/LF con valores de `input.value`; vacíos para huecos.
- `text/html`: tabla mínima, fracciones válidas como `<td>=1/2</td>`, enteros y
  decimales literales, caracteres escapados y texto ajeno a números marcado como
  texto. Sin convertir fracciones a float ni copiar la representación Decimal.
- `application/x-pygebra-matrix-selection`: `{version, filas, columnas, forma,
  celdas}`; `forma` distingue `rectangulo`/`mascara`; pares relativos desde cero
  ordenados por fila y columna. Solo geometría, sin valores duplicados ni DOM.

El parser rechaza estructuras/versions desconocidas, campos extra, dimensiones,
pares, orden, duplicados, límites, forma y rectángulo mínimo incoherentes; exige
el mismo tamaño del TSV y huecos vacíos. Mantiene celdas vacías de los extremos,
acepta CRLF y no recorta valores. Límite de 12 filas, 13 columnas y 120 celdas de
rectángulo; metadata de 4 KiB y TSV de 64 KiB UTF-8. Se comprueba el tamaño
acumulado antes de construir el TSV y antes de generar HTML. Un fallo de escritura
limpia los formatos parciales del evento y no anuncia éxito.

No se autentica al emisor ni se confía en un tipo que diga PyGebra. P28.3 deberá
validar además destino y valores; metadata ausente/inválida tendrá fallback
rectangular. El texto nunca es fuente de verdad para una máscara.

El HTML `=fracción` procede de la prueba manual previa confirmada por Erving
en esta sesión. No es una nueva certificación de Excel ni garantiza su precisión
para racionales de 100 dígitos.

## Archivos modificados (10)

| Área | Archivos |
| --- | --- |
| Copia/utilidad nueva | `frontend/web/calculadora/static/calculadora/copiar_matricial.js` |
| Carga compartida | `frontend/web/calculadora/templates/calculadora/components/seleccion_matricial.html` |
| Runners y contrato HTTP | `tests/entrada_edicion_browser.js`, `tests/entrada_edicion_browser.py`, `tests/test_entrada_edicion.py` |
| Documentación | `docs/copiado-matricial.md`, `docs/seleccion-matricial.md`, `docs/pruebas.md`, `docs/README.md`, este informe |

No se modifica el archivo de selección, los renderizadores ni `entradas.js`.
El archivo local previo `backend/factorizacion_LU.py` no fue editado ni eliminado
por este incremento; dejó de estar presente durante la sesión y queda fuera del PR.

## Pruebas

Suite completa: **1640/1640**. Django check, compileall, lockfile, sintaxis JS y
`git diff --check` correctos. Comandos reproducibles: [pruebas](pruebas.md#p282--copiado-matricial).

Trece runners DOM en Browser: **487/487**.

| Runner | Resultado |
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
| `entrada_edicion_browser` | 179/179 |

El runner ampliado conserva los 108 casos anteriores y agrega 71. Cubre cada
comando matemático, rangos Shift, Ctrl inverso/arbitrario, coordenadas relativas,
rectángulos/máscaras, vacíos seleccionados/huecos, A/b, matrices rectangulares,
inputs actuales, matriz activa, tres formatos, fracciones, decimales, escape,
prioridad textual y fallos de escritura. Round-trip compara la geometría validada
contra la selección original; los casos negativos cubren JSON, esquema, versión,
dimensiones, área, orden, duplicados, incoherencias con TSV y límites UTF-8.
Paste sigue ignorando metadata aun con selección activa.

El primer intento del caso 12×13 fue rechazado por el límite previo de 120 celdas
de Reducción. Se corrigió la preparación del test y se añadió esa guarda al
protocolo; se probaron 12×10 y 9×13. No se aumentaron los límites de las herramientas.

## QA funcional/visual y compatibilidad realmente comprobada

Browser fue la superficie principal. Ctrl+C real desde summary después de
seleccionar con Enter/Tab produjo simultáneamente los tres tipos; leer el
portapapeles del navegador confirmó los literales y HTML esperados. Copiar una
diagonal conservó huecos y metadata. Ctrl+A dentro del input seguido de Ctrl+C
produjo solo el texto seleccionado, sin feedback matricial nuevo.

Ctrl+V real en otra página del runner recibió TSV, HTML y tipo propio en el evento
paste. El textarea del receptor recibió el texto tabulado con su acción nativa.
Esto comprueba transporte entre páginas y recepción en un editor de texto del
navegador; no es una prueba de Notepad, Excel ni Google Sheets.

QA directa dentro de iframes con viewport fijo **1280×650, 744×521 y 320×650**, en
claro y oscuro: selección visible, foco en summary, comandos por teclado y Ctrl+C,
estado anunciado en la región viva, sin desborde horizontal de la página de
PyGebra ni errores de consola relevantes. El control de viewport del navegador
no aplicó el tamaño a la pestaña existente; los iframes usan los tamaños exactos
y el mismo HTML/scripts reales. No se altera CSS para emular dispositivos.
El runner también verifica estos tamaños para las cuatro herramientas y temas.

Las capturas y logs locales se guardan fuera del repositorio en la carpeta de
visualizaciones de esta sesión: `p28-mobile-light.jpg`, `p28-mobile-dark.jpg`,
`p28-minimum-light.jpg`, `p28-minimum-dark.jpg`, `p28-desktop-light.jpg`,
`p28-desktop-dark.jpg` y `suite-python.txt`. El receptor y la página de viewports
pertenecen exclusivamente al runner de pruebas.

Sin QA nuevo de Excel, Sheets, WebView2, menú contextual nativo, lector de pantalla
físico, táctil físico ni alto contraste de Windows. P28.0 no se repitió; se conserva
la evidencia manual previa aportada por el usuario. Sin pegado de máscaras,
llenado, undo, resultados/procedimientos/vectores seleccionables ni pegado especial.

## Entrega

Tres commits atómicos Conventional Commits: implementación, pruebas y documentación.
PR hacia `develop`; CI se informa por separado, sin confundirlo con validación local.
Sin merge, cambio de versión, tag ni release.
