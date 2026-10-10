# Selección matricial de entrada (P28.1)

P28.1 prepara el estado que podrá consultar P28.2. Se aplica a las matrices
editables de Operaciones con matrices, Matriz inversa (A y la B adicional),
Resolver Ax=b (A) y Reducción por filas ([A | b]). No modifica valores, calcula,
envía formularios ni marca un resultado como desactualizado.

No incluye resultados, procedimientos, vectores, escalares, matrices simbólicas,
selección entre matrices, arrastre, persistencia ni deshacer. P28.2 consume este
modelo para [copiar al portapapeles](copiado-matricial.md), sin cambiar su API.
P28.3 consume el mismo modelo para [pegar sobre selecciones](pegado-matricial.md).
Sin selección ni máscara válida, P27 conserva su origen y capacidad habituales.

## Modelo y arquitectura

`seleccion_matricial.js` es el único propietario del modelo, los gestos y los
comandos. Reutiliza `entradasSeguras.filasDeMatriz`, la lectura de filas que también
usa el pegado, y el componente nativo `disclosure` para el control Seleccionar.
Las cuatro plantillas de herramienta incluyen una sola plantilla inerte del
menú y una región `role=status` por página; cada matriz recibe su propio control.

Un `Map` usa como identidad la tabla editable o `#matrix-grid`, nunca el nombre
del operando ni su índice de formulario. Cada estado contiene un conjunto de
coordenadas, celda actual, referencia, extremo del rango, tipo y comando de origen. Las
coordenadas comienzan en cero. Los inputs se vuelven a leer del DOM vigente al
sincronizar; las coordenadas sobrevivientes se aplican a los inputs nuevos.

Cada matriz conserva su conjunto mientras existe. Una sola referencia señala
cuál está activa. Activar otra conserva la selección anterior como inactiva:
borde discontinuo para la inactiva y doble para la activa. No se unen conjuntos
de matrices distintas. El foco sigue siendo el anillo exterior del input.

`tipo` distingue `rango`, `arbitraria` y `comando`; no hay selección cuando es
`null`. `rectangular` describe la geometría efectiva del conjunto: una selección
arbitraria o un comando también pueden llenar un rectángulo. `comando` conserva
el origen, por ejemplo `principal`; no es una regla que se regenere al crecer la
matriz. `celdaActual` sigue el último input enfocado; `referencia` es el ancla
que Shift conserva para extender/reducir un rango. Fila/Columna actual usan
`celdaActual`, también después de enfocar otra celda con una selección existente.
Ambas pueden existir sin seleccionar ninguna celda.

## Edición y controles

- Clic normal limpia la selección de esa matriz y establece la referencia, sin
  cancelar el evento nativo de edición. No borra selecciones guardadas en otras.
- Shift+clic sobre otra celda usa la referencia de esa misma matriz. Dentro del
  input ya enfocado se deja la selección textual nativa.
- Ctrl+clic agrega o quita una celda. Ctrl prevalece si también se pulsa Shift;
  Alt y Meta conservan el comportamiento nativo.
- Shift+flechas, con selección activa en esa matriz, forma el rectángulo entre
  referencia y destino, incluyendo reducción y límites. Sin selección conserva
  P27 y la selección textual. Flechas sin Shift siguen usando la guarda de P27:
  izquierda/derecha navegan solamente en los extremos del texto, sin selección
  textual, modificadores o composición IME.
- Escape se atiende en captura. La primera pulsación limpia la selección y
  cancela su acción por defecto. Teclado, buscador y navegación respetan
  `defaultPrevented`; siguientes pulsaciones pueden cerrar esos componentes.
- El menú usa summary y botones reales: Enter/Espacio abren, Tab recorre las
  opciones y Enter/Espacio ejecutan. El comando devuelve el foco al summary.
  Escape dentro del menú cerrado no intercepta otros componentes; dentro del
  menú abierto sin selección lo cierra y devuelve el foco a su summary.

Toda, fila y columna seleccionan A. Fila/columna requieren una celda actual.
Principal usa `min(filas, columnas)`. Secundaria y ambas triangulares requieren
A cuadrada; las triangulares incluyen la diagonal. Las opciones imposibles se
deshabilitan, siguiendo el patrón de botones de estructura de PyGebra.

En [A | b], **los siete comandos excluyen b**. Columna actual se deshabilita si
la celda actual está en b; Fila actual conserva la fila y selecciona solo sus
coeficientes de A. La selección manual (Ctrl, Shift+clic y Shift+flechas) puede
incluir b porque trabaja sobre las celdas editables de la cuadrícula completa,
como la navegación y el pegado existentes. El separador y la etiqueta b previos
se conservan; la ayuda del menú explica la distinción. En Ax=b, A y el vector b
ya están separados: b no recibe control ni estado de selección.

No se añadieron encabezados de filas/columnas ni roles ARIA grid. Reducción
conserva su marcado y rótulos matemáticos anteriores. La región viva anuncia
comandos, cambios de cantidad y limpieza, sin anunciar movimientos normales de
foco. Las celdas seleccionadas añaden una descripción accesible sin sustituir
su label ni las ayudas de error.

## Dimensiones y ciclo de vida

Los renderizadores notifican cambios estructurales. Operaciones y Reducción
conservan la identidad de su cuadrícula; Inversa y Ax=b llaman `redimensionar`
cuando sus renderizadores de dimensiones reemplazan la tabla. Se recortan las
coordenadas que ya no existen. P28.3 conserva las celdas seleccionadas que pasan
a readonly/disabled sin retirarse del DOM: un pegado falla completo, sin cambiar
su conjunto. Los gestos/API de sustitución siguen rechazando celdas no editables.
Si se pierde la referencia o
el extremo o la celda actual, se usa una celda sobreviviente; si desaparece todo
el conjunto por redimensionado, se limpian tipo, comando, referencia, extremo y
celda actual. Crecer no vuelve
a seleccionar las coordenadas descartadas ni añade otras automáticamente.

La selección manual es **posicional**, no sigue los valores: al cambiar columnas
una coordenada sobreviviente puede pasar a corresponder a b. Los comandos se
recortan además a A, de modo que una columna de A que pasa a ser b sale de ellos.

Cambiar de tipo o modo de entrada, quitar un operando o reemplazar una matriz
fuera del renderizador de dimensiones limpia su estado. Un MutationObserver
limitado a los formularios cubre cambios externos de nodos. Las consultas a la
API también sincronizan, sin esperar a ese observador. La limpieza elimina el
menú y sus descripciones; los nombres/reindexados no cambian la identidad.

## API interna para P28.2

`window.seleccionMatricial` se publica solo en estas cuatro herramientas:

| Método | Contrato |
| --- | --- |
| `activa()` | Snapshot de la única selección activa o `null`. |
| `obtener(matriz, actualizar = true)` | Snapshot de esa tabla/`#matrix-grid`, incluso sin celdas seleccionadas; `null` si no pertenece al alcance o fue retirada. P28.3 usa `false` para planificar antes de reconciliar cambios pendientes y poder rechazar destinos ausentes sin cambiar el conjunto durante paste. |
| `limpiar(matriz)` | Limpia ese conjunto. Sin argumento limpia el activo. Conserva referencia y celda actual válidas para continuar editando. |
| `reemplazar(matriz, celdas, opciones = {})` | Sustituye y activa un conjunto, sin enfocar ni editar inputs; devuelve `true`. Devuelve `false`, sin aplicar una parte, ante coordenadas inválidas/no editables o b dentro de un comando. Acepta conjunto vacío y elimina duplicados. |
| `sincronizar()` | Reconcilia cuadrículas, dimensiones, referencias, menús y estados retirados. |
| `redimensionar(anterior, nueva)` | Uso exclusivo de renderizadores: transfiere y recorta coordenadas cuando reemplazan una tabla por cambio de dimensiones. |

El snapshot contiene `matriz`, `nombre`, `activa`, `filas`, `columnas` (cuadrícula
completa), `columnasA`, `celdaActual`, `referencia`, `extremo`, `tipo`, `comando`, `rectangular`,
`celdas` y `limites`. `celdas` ya está ordenado por fila y columna y contiene
`{fila, columna, input}` con los inputs actuales. `limites` es `null` si el
conjunto está vacío; de otro modo incluye `filaInicio`, `filaFin`,
`columnaInicio`, `columnaFin`, todos inclusivos. Para conjuntos arbitrarios son
los límites envolventes, no una promesa de que todas sus celdas estén incluidas.

Los snapshots y coordenadas devueltos no exponen los contenedores internos.
Las referencias DOM de un snapshot son para uso inmediato: volver a consultar
después de un cambio estructural. `opciones` admite `referencia`, `extremo`,
`tipo`, `comando` y `etiqueta` para anunciar un comando. `rango` y `comando` los
producen los gestos y el menú; una sustitución externa usa `arbitraria` por
defecto. P28.2 no necesita leer clases CSS ni interpretar nombres de inputs.

```javascript
const api = window.seleccionMatricial;
const seleccion = api.activa();
if (seleccion) {
    const coordenadas = seleccion.celdas.map(({ fila, columna }) => ({ fila, columna }));
    api.reemplazar(seleccion.matriz, coordenadas);
    api.limpiar(seleccion.matriz);
}
```

El borde doble/discontinuo y el foco usan tokens existentes. En forced-colors
se usan Highlight y CanvasText; la identificación no depende solo del color.
El padding compensa el borde más grueso también en Ax=b estrecho y conserva
el tamaño de las celdas. Los errores mantienen su borde en los temas normales.

Pruebas, evidencia y límites físicos: [validación P28.1](validacion-p28-1.md).
