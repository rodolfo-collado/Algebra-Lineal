# Pegado sobre selecciones matriciales (P28.3)

El listener de `paste` sigue en `entradas.js`, compartido con P27. Consume
`seleccionMatricial.obtener(matriz, false)` de [P28.1](seleccion-matricial.md) y
`copiadoMatricial.parsear(metadata, texto)` de [P28.2](copiado-matricial.md).
No hay otro modelo de selección, parser de metadata ni serializador.
`entradasSeguras.bloqueDeTexto` concentra la lectura TSV de ambos consumidores.
No cambia backend, CSS, plantillas de herramientas, dependencias ni versión.

## Tabla de decisión

«Máscara» significa metadata v1 válida con `forma: "mascara"`, coherente con el
TSV. Un rectángulo propio válido usa las reglas rectangulares, sin reinterpretar
sus valores como una máscara. La geometría efectiva del destino viene del
modelo, independientemente de Shift/Ctrl o del comando que lo seleccionó.

| Origen | Destino | Regla |
| --- | --- | --- |
| Un valor, incluido vacío | Sin selección | Pegado nativo P27 en el texto de la celda. |
| TSV rectangular, con o sin metadata rectangular | Sin selección | P27: bloque desde la celda, si cabe; sin redimensionar. |
| Un valor | Cualquier selección activa de esa matriz | Rellenar todas sus celdas. |
| Rectángulo mayor que 1×1 | Selección rectangular | Filas **y** columnas exactamente iguales; asignar por filas. |
| Rectángulo mayor que 1×1 | Selección no rectangular | Rechazar, aunque el cardinal sea igual. |
| Máscara | Sin selección | La celda es la esquina superior izquierda del rectángulo envolvente; escribir solo sus coordenadas. |
| Máscara | Cualquier selección activa | Igual número de celdas seleccionadas; emparejar por fila y luego columna. |

No hay trasposición, mosaico, repetición de bloques, cálculo automático ni llenado
por escritura directa. Los siete comandos matemáticos conservan su decisión de
seleccionar solo A. Las selecciones manuales de Reducción pueden incluir b;
el pegado recibe sus coordenadas, sin volver a decidir A/b. Ax=b mantiene su
vector b separado y con paste P27. Operaciones A/B e Inversa A/B son destinos
independientes; no se buscan celdas fuera de la cuadrícula destinataria.

## Metadata, texto y fallback

1. Leer `text/plain` del evento.
2. Si existe el MIME propio, validarlo con el parser v1 existente contra ese texto.
3. Solo una metadata válida puede aportar geometría. Los valores siempre se leen
   del TSV en sus coordenadas; el JSON sigue transportando únicamente geometría.
4. Metadata ausente, JSON roto, más de 4 KiB, versión desconocida, dimensiones,
   coordenadas, duplicados, orden, forma o TSV incoherentes: ignorarla y aplicar
   la regla rectangular al texto. Si el texto tampoco es compatible, rechazar
   sin cambios. No deducir máscaras a partir de vacíos.

No se lee HTML ni se ejecutan fórmulas o código. No hay respaldo en almacenamiento
local. El MIME no autentica la página de origen: una metadata externa válida
recibe las mismas comprobaciones de destino que cualquier otra.

Sin selección y sin máscara válida se mantiene P27 exactamente: recorte de
líneas vacías exteriores y espacios exteriores de valores, delimitadores TAB y
LF/CRLF, valor único nativo, límites, mensajes, foco, eventos y dimensiones.
La metadata rectangular no cambia esa ruta, incluso para una columna con filas
vacías en sus extremos. En la ruta nueva, metadata válida conserva esas filas
y los literales completos; texto externo/fallback conserva la normalización P27.

Una posición ausente de `celdas` es un **hueco**: no se escribe ni se vacía su
destino. Una coordenada presente cuyo valor TSV es `""` es una **celda
seleccionada vacía**: sí vacía su destino. Esto también permite copiar una celda
vacía 1×1 y vaciar toda una selección. Sin texto ni metadata válida, por ejemplo
un portapapeles que contiene solo HTML, no se borra nada.

## Atomicidad y límites

Antes de asignar valores se construye la lista completa de destinos y valores.
Se comprueban forma/cardinal, capacidad del rectángulo envolvente de la máscara,
existencia de cada destino en la misma matriz, `readonly`, `disabled` (incluido
fieldset), elementos ocultos y `maxlength`. Ningún input se modifica al fallar.
Los huecos de una máscara no son destinos y no requieren escribir sus inputs.
La lectura de filas vigente manda: no se continúa hacia otra matriz ni se
redimensiona para acomodar datos.

La ruta nueva limita el texto a 64 KiB UTF-8 antes de dividirlo. El parser v1
mantiene 4 KiB de metadata, 12 filas, 13 columnas y 120 posiciones en el
rectángulo. Esos máximos no autorizan crear matrices: Inversa y Ax=b mantienen
sus dimensiones, Operaciones su presupuesto total de operandos y Reducción su
tope real de 120 celdas, incluida b. Por ejemplo 12×10 y 9×13 pueden existir en
Reducción; 12×13 se rechaza al dimensionar. El paste P27 no recibe límites nuevos.

No se añade una validación numérica distinta del contrato de edición: el pegado
permite editar/borrar literales y la validación matemática y de seguridad sigue
en los formularios/backend al calcular. `required` no impide vaciar una celda
seleccionada; posteriormente impedirá enviar entradas incompletas como antes.

## Selección, foco y mensajes

Éxito y fallo conservan el conjunto seleccionado. La consulta sin sincronización
evita recortarlo durante la planificación. Las celdas que siguen existiendo pero
se vuelven no editables conservan su pertenencia: el paste se rechaza completo.
Los cambios estructurales externos siguen el ciclo P28.1: recortan coordenadas
retiradas al redimensionar y limpian matrices eliminadas o cuyo tipo cambió.

El foco permanece donde estaba, incluida la celda de origen o el summary de
«Seleccionar» al usar un comando matemático. Solo ese summary y los inputs
matriciales admiten paste de selección; pegar en un input/textarea ajeno no
redirige datos a una selección que quedó activa. Una selección de otra matriz
tampoco cambia el destino.

Todos los valores se asignan antes de emitir un `input` con propagación por cada
destino, igual que P27. No se añade `change`, submit ni cálculo. `resultado.js`
observa el bloque completo y marca un resultado previo como desactualizado si
cambiaron sus entradas. Las flechas, Escape y el teclado matemático conservan
P28.1/P27; un paste no limpia la selección ni cierra el teclado.

Se reutilizan las regiones de estado del formulario, `role=status` y
`aria-live=polite`, visibles junto a las acciones. No hay alertas ni modales:

- «El bloque copiado es de 2×3 y la selección es de 3×2.»
- «Se copiaron 6 celdas, pero hay 5 seleccionadas.»
- «La selección copiada no cabe desde esta celda.»
- «Los datos copiados no son compatibles con esta selección.»

Los errores añaden «No se pegó ningún valor.». El éxito anuncia el número de
valores aplicados, incluyendo vacíos seleccionados.

## Preparación para P28.4

`entradasSeguras.aplicarPegado(cambios)` recibe pares `[input, valor]` ya
validados, aplica todos y después emite los eventos. Devuelve un registro de
`{input, anterior, nuevo}` para cada destino. P28.3 no retiene ese registro,
no implementa historial ni expone un control para deshacer. P28.4 podrá usarlo
sin duplicar la aplicación, con sus propias comprobaciones del DOM vigente.

Pruebas y límites de QA: [validación P28.3](validacion-p28-3.md).
