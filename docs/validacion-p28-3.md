# Validación P28.3 — pegado sobre selecciones

Base: `origin/develop`, merge de #84 (`7eecdf54161e3f4a8c599af39c388197f64d86a2`,
10 de octubre de 2026). Rama: `feature/p28-3-pegado-selecciones`.

## Arquitectura y contrato

La implementación amplía el listener existente de `entradas.js`. La selección
sigue siendo propiedad de `seleccion_matricial.js`; el parser v1 y los límites
UTF-8 siguen en `copiar_matricial.js`. Se extrae la lectura TSV compartida y la
aplicación completa antes de los eventos. No se duplica selección, geometría,
parsing ni serialización. Tabla final y detalles: [contrato](pegado-matricial.md).

Sin selección ni máscara válida se conserva P27, incluido el valor único nativo,
normalización, mensajes, foco y `input`. Con selección: valor único rellena;
rectángulo exige dimensiones exactas; máscara exige igual cardinal y asigna por
fila/columna. Sin selección: máscara escribe solo sus coordenadas desde la celda,
si cabe todo su rectángulo. Hueco no toca; celda seleccionada vacía sí borra.

Metadata inválida/desconocida/incoherente tiene fallback TSV rectangular. No se
leen valores del JSON ni de HTML. No hay almacenamiento alternativo. El destino
real y los límites del protocolo mandan; 12×13 no se vuelve una matriz permitida.

Cada paste calcula y valida todos los destinos antes de escribir: dimensiones,
cardinal, capacidad, existencia, misma matriz, readonly/disabled/fieldset,
visibilidad y maxlength. Los eventos se emiten después de todas las asignaciones.
No se calcula ni envía automáticamente. Los resultados previos quedan stale
cuando sus entradas cambian. Selección y foco se conservan, también en errores.

El test añadido que espera las microtareas detectó que la reconciliación P28.1
quitaba celdas bloqueadas al actualizar el mensaje. Se corrigió en el modelo
compartido: coordenadas existentes conservan pertenencia aunque no sean editables;
nuevas selecciones siguen rechazando esas celdas y dimensiones/retiradas siguen
recortándose. La consulta `obtener(matriz, false)` permite planificar sin recortar
cambios estructurales pendientes durante el handler.

`aplicarPegado` devuelve `{input, anterior, nuevo}` sin guardar historial ni
exponer undo. P28.4 podrá consumir ese registro.

## Archivos modificados (11)

| Área | Archivos |
| --- | --- |
| Implementación compartida | `frontend/web/calculadora/static/calculadora/entradas.js`, `copiar_matricial.js`, `seleccion_matricial.js` |
| Runner existente | `tests/entrada_edicion_browser.js`, `tests/entrada_edicion_browser.py` |
| Contrato y evidencia | `docs/pegado-matricial.md`, `docs/validacion-p28-3.md`, `docs/seleccion-matricial.md`, `docs/copiado-matricial.md`, `docs/pruebas.md`, `docs/README.md` |

Sin cambios de backend, CSS, dependencias, versión ni plantillas de herramientas.

## Pruebas ejecutadas

Suite Python completa: **1640/1640**, en 215,113 s.
Django check, compileall, `uv lock --check`, sintaxis de los tres JS y del runner,
y `git diff --check` correctos. Comandos: [pruebas P28.3](pruebas.md#p283--pegado-sobre-selecciones).

Trece runners DOM en Browser: **551/551**.

| Runner | Resultado |
| --- | --- |
| `entrada_edicion_browser` | 243/243 |
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

El runner ampliado mantiene 179 casos anteriores y agrega 64. Los negativos del
parser v1 ahora comprueban también paste/fallback, incluido texto incompatible.
Se actualiza la expectativa del caso antiguo que ignoraba metadata con selección:
prueba fallback sin selección, pues P28.3 cambia expresamente el destino activo.

Cobertura: cuatro herramientas y B adicional; rectángulos 2×2 y 2×3, forma/cardinal
incompatibles y ausencia de mosaico; los siete comandos, Shift y Ctrl; máscaras
diagonal/triangular/arbitraria, origen interior y fuera de límites, orden por filas
y formas distintas; huecos frente a vacíos, filas vacías exteriores propias, vacíos
1×1; A/b y aislamiento A/B; metadata rota, excesiva, falsa, desconocida o incoherente;
64 KiB y UTF-8 inclusive/excesivo, 120 celdas y 13 columnas reales; atomicidad,
origen/destino bloqueados, fieldset, ocultos, retirados, maxlength y huecos bloqueados
que no son destinos; selección tras microtareas, observadores completos, foco,
events input sin change/submit, stale y rechazo que conserva resultado vigente,
dimensiones posteriores, flechas, Escape, teclado y copia P28.2.

Un intento paralelo de `escritorio_browser` falló en su caso de historial GET/POST;
la repetición aislada del runner completo pasó 27/27. No se modificó ese runner.
El primer QA del triangular tuvo datos fuente mal preparados por la acción fill
de la automatización sobre una selección existente. Se repitió con TSV externo,
fuente comprobada 1…16 y Ctrl+C/Ctrl+V reales; el resultado correcto se indica abajo.

## QA manual en Browser

Browser fue la superficie principal, sin fallback de navegador. Al arrancar,
un runner dentro del sandbox bloqueó el puerto sin poder atender peticiones;
se detuvo únicamente ese proceso y se usó el runner autorizado fuera del sandbox.
El servidor y páginas de QA son locales, exclusivos de pruebas.

Se realizaron acciones nativas de portapapeles, no ClipboardEvent sintético:

- Diagonal 4×4 → otra página PyGebra con todas las celdas a 7: resultado diagonal
  `1/2`, vacío, `9`, vacío; los doce huecos conservaron 7. Se verificaron los tres
  formatos copiados y foco en la celda inicial después de Ctrl+V.
- Rango 2×2 con vacíos → rango 2×2 interior de otra matriz: valores/vacíos correctos,
  cuatro celdas seleccionadas y foco en el extremo original.
- Triangular inferior 4×4 → superior de 10 celdas: recibió
  `1, 5, 6, 9, 10, 11, 13, 14, 15, 16`, en ese orden. Esto prueba que no traspone.
  Ctrl+C y Ctrl+V se efectuaron desde summary, que conservó el foco.
- Ctrl+clic en orden inverso sobre dos celdas → otro conjunto de dos celdas:
  recibió `4, 13` por orden de coordenadas, conservando su selección.
- Una celda vacía seleccionada 1×1 → celda destino seleccionada con valor:
  el destino quedó vacío, con la selección conservada y anuncio de éxito.
- TSV externo 4×4 sin metadata → matriz sin selección: recibió 1…16 por filas.
- Valor externo `1/2` → rango manual 2×2 a viewport 320×650: las cuatro celdas
  recibieron el valor, conservaron selección/foco y el teclado permaneció abierto.

El runner también comprobó las cuatro herramientas a **1280×650, 744×521 y
320×650**, en claro/oscuro, sin desborde horizontal. La comprobación manual móvil
usó un iframe de tamaño fijo servido por el runner con HTML/scripts reales.
La consola de la página destino revisada no mostró errores ni advertencias.

Evidencia local fuera del repositorio, en la carpeta de visualizaciones de esta
sesión: `suite-python.txt`, `regresiones-dom.json`, `p28-3-diagonal.png` y
`p28-3-mobile.png`. Los ClipboardEvent sintéticos viven exclusivamente en el
runner; no se usan en el código de producción.

## Límites y entrega

Sin QA nuevo de Excel, Google Sheets, WebView2, menú contextual nativo, lector de
pantalla físico, táctil físico ni alto contraste de Windows. No se implementó
historial/undo, selección de resultados/procedimientos/vectores, pegado especial,
mosaico ni escritura directa para llenar una selección.

Tres commits Conventional Commits: implementación, pruebas y documentación.
PR hacia `develop`; el estado de CI se informa por separado de estos resultados
locales. Sin merge, cambio de versión, tag ni release.
