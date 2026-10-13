# Menú de edición de entradas

[Índice de documentación](README.md)

Un clic derecho sobre una entrada abre un menú contextual de PyGebra con las
acciones de edición que tienen sentido para ella: **Rellenar aleatoriamente**,
**Limpiar** y, en las matrices, los comandos de **Seleccionar**. Sustituye al chip
«Seleccionar» que acompañaba a cada matriz: la interfaz no gana botones
permanentes y las acciones aparecen donde se edita. No cambia ningún motor
matemático ni el contrato de los formularios: todo lo que el menú escribe pasa
por las mismas validaciones del servidor al calcular.

## Dónde aparece

Se abre con clic derecho, Shift+F10 o la tecla Menú sobre:

- celdas de matrices: Operaciones con matrices (tipo Matriz), Matriz inversa (A
  y B), Determinantes (A), Resolver Ax = b (A) y Reducción por filas ([A | b]);
- vectores: b de Resolver Ax = b y de Matriz inversa, operandos de tipo Vector y
  cada vector de Operaciones con vectores (v1, v2, …, b);
- escalares: operandos de tipo Escalar y k de Operaciones con vectores;
- el número de Conversión de números romanos (arábigo o romano, según la dirección).

En el resto de la página (dimensiones, nombres, expresión, sistema escrito,
vectores lineales, resultados, procedimientos, Conversión de bases, Inicio) queda
el menú del navegador. También queda si el puntero lo abre con texto seleccionado
dentro del campo: así Cortar, Copiar y Pegar siguen a mano. En escritorio ese menú
es el de WebView2, filtrado a Cortar, Copiar, Pegar y Seleccionar todo. Ctrl+C,
Ctrl+V y Ctrl+X funcionan igual que antes en todas las celdas.

## Opciones según la entrada

El menú se titula con la entrada («Matriz A», «Vector v2», «Escalar k»,
«Matriz aumentada [A | b]», «Número romano») y solo muestra lo que aplica:

| Entrada | Opciones |
| --- | --- |
| Matriz | Rellenar aleatoriamente; Limpiar, si tiene algún valor; Seleccionar con los comandos posibles; Quitar selección, si esa matriz tiene una. Debajo, los gestos: Shift+clic, Ctrl+clic y Esc. |
| [A \| b] | Lo mismo, con el aviso «Los comandos seleccionan solo A». Desde una celda de b no aparece Columna actual. |
| Vector, escalar, número | Rellenar aleatoriamente; Limpiar, si tiene un valor. |

Secundaria y triangulares solo aparecen en matrices cuadradas; Fila y Columna
actual se refieren a la celda del clic derecho. Las reglas de cada comando son
las de [selección matricial](seleccion-matricial.md).

## Rellenar aleatoriamente y Limpiar

- **Cuadrículas.** Enteros de −9 a 9, uniformes, en todas las celdas de esa
  matriz, vector o escalar. Son números pequeños para probar un procedimiento
  rápido, y siempre cambia al menos un valor. Las dimensiones no cambian.
- **Número arábigo.** Un entero de 1 a 3999.
- **Número romano.** El mismo intervalo escrito con la tabla canónica del backend:
  `servicios_romanos.numeracion_romana()` la entrega en el `json_script`
  `datos-numeracion-romana`, así que el navegador escribe igual que
  `decimal_a_romano` y no guarda otra copia de los símbolos ni del máximo.
- **Limpiar.** Vacía todas las celdas de esa entrada y conserva dimensiones,
  tipo, nombre, las demás entradas, métodos y opciones. No reinicia la herramienta.

Ninguna de las dos acciones cambia la selección. En las cuadrículas usan la misma
aplicación atómica que el [pegado](pegado-matricial.md): un `input` por celda, el
resultado anterior queda desactualizado y aparece un aviso («Matriz A: 4 celdas
con enteros aleatorios.», «Matriz A: 4 celdas vaciadas.») con el único
[Deshacer](deshacer-pegado.md) de la página, compartido con el pegado. Editar esa
entrada lo invalida. En un campo suelto (k y el número romano) la edición es la
nativa, así que Ctrl+Z la deshace como cualquier escritura.

## Teclado, foco y teclado matemático

- El clic derecho abre el menú junto al puntero; Shift+F10 y la tecla Menú, bajo
  el campo (Chromium los envía con `button = -1`). Siempre queda dentro de la
  ventana: debajo si cabe, encima si no y, si tampoco, lo más abajo posible.
- El foco entra en la primera opción. ↑ y ↓ recorren las opciones en círculo,
  Inicio y Fin van a los extremos, Enter o Espacio ejecutan. Escape y Tab cierran
  y devuelven el foco al campo; pulsar fuera cierra sin robar el foco.
- Escape dentro del menú solo cierra el menú: no limpia la selección.
- El teclado matemático sigue abierto mientras se usa el menú y la acción
  devuelve el foco al campo.
- `role=menu` nombrado por su título, opciones `menuitem` (botones `type=button`
  sin `name`), el grupo «Seleccionar» y un separador. Las ayudas visibles se
  asocian con `aria-describedby`; el foco usa el anillo de PyGebra.

## Arquitectura

- `components/menu_edicion.html`: una plantilla inerte con todas las opciones,
  identificadas por `data-accion` o `data-seleccionar`, y el script. La incluyen
  las siete herramientas con entradas compatibles.
- `menu_edicion.js`: un solo menú por página. `entradaDe(campo)` decide qué se
  edita (sus celdas, la cuadrícula que permite deshacer, la matriz seleccionable
  y el generador de valores); `preparar()` oculta lo que no aplica; `ACCIONES`
  ejecuta Rellenar, Limpiar y Quitar selección. Los comandos llaman a
  `seleccionMatricial.comando()` y su disponibilidad sale de `obtener().comandos`.
- `deshacer_pegado.js` acepta textos propios en `pegar(destinos, cuadricula,
  contexto, textos)` y ubica su aviso aunque no haya `.workspace-actions`, como
  en Resolver Ax = b con una confirmación de costo pendiente.
- `teclado.js` trata el menú (`[data-edicion-menu]`) como parte de la edición del
  campo, para no cerrar el dock.

### Añadir otra acción

Una acción nueva, por ejemplo **Restablecer**, necesita un botón
`data-accion="restablecer"` en la plantilla, su entrada en `ACCIONES` (calcula
los valores y llama a `escribir()` con sus textos, de modo que hereda el aviso y
el Deshacer) y su condición en `preparar()`. Restablecer no se añadió: además
habría que guardar los valores con que se abrió la herramienta, porque los
renderizadores crean las celdas sin valor por defecto.

## Pruebas

- `tests/test_menu_edicion.py` (CI): dónde se carga, opciones y atributos del
  menú, comandos alineados con el modelo, enteros aceptados por la conversión y
  la protección numérica comunes, extremos calculados en cada herramienta, datos
  romanos iguales a los del backend y cada entero del 1 al 3999 escrito como lo
  lee `romano_a_decimal`.
- `uv run --locked python -m tests.menu_edicion_browser` y abrir
  `http://127.0.0.1:8890/__pruebas/`: alcance por herramienta, opciones por tipo,
  Rellenar y Limpiar con deshacer, POST reales con los valores generados, los
  3999 romanos escritos por el navegador validados por el backend, selección,
  teclado, foco, teclado matemático y diseño en tres tamaños y dos temas.
