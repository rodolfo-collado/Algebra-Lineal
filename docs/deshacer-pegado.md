# Deshacer último pegado matricial (P28.4)

PyGebra ofrece **un solo nivel global por página**. El botón Deshacer revierte
únicamente el último pegado matricial atómico que cambió valores. No hay pila,
redo, Ctrl+Z global, persistencia, localStorage ni sessionStorage. Escribir,
borrar manualmente, usar el teclado matemático, cambiar opciones o dimensiones
no crea operaciones deshacibles.

## Integración y registro

`deshacer_pegado.js`, cargado después de `entradas.js` en la base compartida,
encapsula el único registro. El listener de paste sigue en `entradas.js` y
reutiliza la selección P28.1, la metadata P28.2 y la planificación P28.3.
`entradasSeguras.aplicarPegado` conserva su contrato: asigna todo antes de emitir
`input` y devuelve `{input, anterior, nuevo}` por destino. No se duplica el
parser ni la aplicación de valores.

El registro contiene:

| Dato | Uso |
| --- | --- |
| `matriz`, `form` | Referencias exactas a la cuadrícula y formulario originales; nunca buscar otra matriz por nombre reutilizado. |
| `dimensiones` | Longitudes de las filas, incluida b cuando pertenece a la cuadrícula. |
| `tipo` | Tipo del operando, cuando existe ese selector. |
| `cambios` | Solo destinos cuyo literal cambió: `input`, `fila`, `columna`, `anterior`, `nuevo`, en orden por filas y columnas. |
| `foco` | Coordenadas de la celda de contexto del pegado; no guarda la selección. |
| `estado` | Región del mensaje y de su acción en el formulario. |

No guarda HTML, portapapeles, metadata, origen, DOM serializado, estado visual
ni resultados. Las referencias DOM se conservan **solo mientras el registro
es válido**. Un observador temporal invalida y libera el registro al retirar
o reconstruir la cuadrícula o sus inputs; comprobar las coordenadas contra los
inputs originales impide escribir sobre reemplazos que reutilizan nombres.

La API interna es `window.deshacerPegado`:

- `estado(form)`: región exclusiva del pegado, sin sobrescribir presupuesto o avisos de vectores.
- `pegar(destinos, matriz, contexto)`: consume el registro anterior, aplica los destinos prevalidados con P28.3 y conserva los cambios reales devueltos.
- `puedeDeshacer()`: comprueba coherencia y mutaciones pendientes; invalida si falla.
- `deshacer()`: valida todo, consume y restaura; devuelve si restauró valores.
- `invalidar()`: descarta el registro sin restaurar nada.

## Creación, reemplazo e invalidación

Crean undo rectángulos, un valor sobre cualquier selección, máscaras sobre una
celda o selección y bloques tradicionales P27: todos pasan por la misma aplicación
atómica, incluidos b separado de Ax=b, B de Inversa y los bloques de Vectores.
El pegado nativo de texto en una celda sin selección sigue siendo edición normal
y no crea undo.

Cada pegado exitoso reemplaza el anterior, incluso en otra matriz. Un éxito sin
cambios consume el registro anterior y anuncia «Pegado sin cambios.»; no ofrece
una acción vacía. Una mezcla de cuatro destinos con dos literales distintos crea
undo de **dos celdas**. Un pegado rechazado conserva el registro anterior seguro.

La decisión conservadora es invalidar ante cualquier `input` o `change` posterior
en **la misma cuadrícula**, aunque sea una celda no afectada; editar otra matriz
conserva undo. Las reconstrucciones por dimensiones, tipo, reemplazo o eliminación,
movimientos de filas y cambios de readonly/disabled/hidden/maxlength también lo
invalidan. Nunca se recupera undo al volver al tamaño o tipo anterior, ni se
redimensiona para restaurar. Seleccionar, limpiar selección, copiar, navegar con
flechas, cambiar foco o cambiar un método sin reconstrucción no lo invalidan.

Al recargar, enviar o navegar el registro desaparece. `pagehide` lo descarta
también si el navegador conserva el documento en su caché de navegación (bfcache).

## Comprobación final y atomicidad

Antes de cambiar **una sola celda**, se entregan al validador las mutaciones
pendientes del observador y se comprueba:

1. Cuadrícula original conectada al formulario original, visible y del mismo tipo.
2. Mismas dimensiones; cada coordenada resuelve exactamente al input original.
3. Todos los destinos siguen perteneciendo a esa cuadrícula y formulario, son
   inputs de texto editables, no están readonly, disabled (incluido fieldset),
   ocultos ni ausentes; su maxlength admite el literal anterior.
4. Cada valor actual coincide **exactamente como texto** con el `nuevo` registrado.

Un fallo descarta undo, anuncia discretamente que ya no puede deshacerse y cambia
cero valores. Incluso una modificación programática sin `input` es detectada
por la comparación final. No existe restauración parcial ni rollback posterior.

Al pasar todas las comprobaciones, se consume el registro y se aplica la lista
de valores anteriores con la misma función P28.3. Después de todas las asignaciones
se emite un `input` con propagación por cada celda restaurada, en orden. No hay
`change`, submit, cálculo automático ni una operación nueva para rehacer.

## Mensaje, selección, foco y resultado

Antes de Calcular aparece «4 celdas pegadas.» junto al botón real **Deshacer**,
con `type=button`, alcanzable mediante Tab y activable con Enter/Espacio. No hay
modal, confirmación, alerta ni temporizador. La región `role=status`,
`aria-live=polite`, `aria-atomic=true` contiene solo el mensaje; el botón está
fuera para evitar un anuncio redundante. El layout permite saltos de línea y
usa los colores y el foco de los botones compartidos, también en forced-colors.
Un nuevo éxito consume el registro anterior antes de emitir input, para anunciar
solo el éxito final y evitar un mensaje de invalidación intermedio.

Tras usarlo: «Pegado deshecho: 4 celdas restauradas.». El botón se oculta y el foco
vuelve a la celda de contexto, otra celda editable de esa matriz o un control
seguro del formulario. Si B quedó dentro de Aplicaciones y propiedades cerrado,
abre ese desplegable antes de enfocar la celda. No se recrea la selección de
origen: se conserva el conjunto actual válido. Una invalidación pasiva no roba foco; si el botón tenía
foco, permanece con `aria-disabled=true` hasta salir de él y luego se oculta.

Pegado → resultado desactualizado; Deshacer → **sigue desactualizado**, incluso
si restaura los valores que produjeron ese resultado. `resultado.js` no vuelve
a marcarlo vigente: el usuario debe recalcular explícitamente.

Pruebas y límites: [validación P28.4](validacion-p28-4.md).
