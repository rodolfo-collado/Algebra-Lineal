# Interfaz visual

La aplicación desktop y Django en desarrollo comparten la misma interfaz.

No hace falta un framework frontend: las herramientas nuevas reutilizan
plantillas Django, CSS propio y JavaScript mínimo, todos locales.

## Identidad

- Nombre: **Álgebra Lineal**
- Subtítulo: Aprende resolviendo
- Marca: una cuadrícula `[A | b]` en `assets/` y en el header
- Paleta: verde esmeralda como acento principal y azul profundo para la
  columna de términos independientes, con equivalencia clara y oscura

El tema claro u oscuro se guarda en `localStorage` (`algebra-lineal-tema`).
Si el usuario no ha elegido, se respeta `prefers-color-scheme`. El icono del
selector representa el tema activo: sol en claro, luna en oscuro.

Todo debe funcionar sin Internet. No uses Google Fonts, CDN ni iconos remotos.

## Principio: la interfaz habla matemáticas

El usuario no tiene por qué conocer la sintaxis del parser. Lo que se muestra
es notación matemática (`x₁`, `−`, `a⁄b`) y lo que se envía es la sintaxis
interna (`x1`, `-`, `/`). Cuando una herramienta necesite símbolos, declara un
teclado contextual (ver abajo) en lugar de pedir al usuario que los escriba.

## Sistema visual

Los estilos están organizados así:

```text
static/calculadora/
├── styles.css              # importa el resto
└── styles/
    ├── tokens.css          # colores, tipografía, radios, sombras, medidas del shell
    ├── base.css            # reset ligero, foco visible y utilidades
    ├── shell.css           # header, sidebar, cajón móvil, breadcrumbs, layout
    ├── components.css      # herramienta, paneles, botones, buscador, inicio,
    │                       # relacionadas, teclado, controles de estructura, guías, matrices
    └── modules.css         # formularios y resultados de sistemas, bases, vectores y matrices
```

Usa tokens semánticos (`--color-brand`, `--color-accent`, `--color-surface-raised`,
`--color-pivot`, …) en lugar de hexadecimales sueltos. Cada token existe en el
bloque claro y en `[data-theme="dark"]`.

## Shell y navegación

`templates/calculadora/base.html` monta el header, la barra lateral
(`components/sidebar.html`), el fondo del cajón móvil y el contenido con sus
breadcrumbs (`components/breadcrumbs.html`). Todo sale del registro central
`catalogo.py` a través de `context_processors.navegacion`, que también marca
la herramienta activa y calcula las relacionadas.

- La sidebar usa `details`/`summary` por categoría: funciona sin JavaScript y
  es accesible con teclado. `navigation.js` recuerda las categorías abiertas,
  oculta la barra en escritorio (`algebra-lineal-menu`) y la convierte en cajón
  hasta 880 px, con `inert` sobre el contenido mientras está abierto.
- El buscador (`components/search.html`) es un formulario `GET` a Inicio.
  `buscador.js` filtra al instante los elementos con `data-indice` de la lista
  indicada en `data-buscador`; los contenedores con `data-grupo` se ocultan
  cuando no tienen coincidencias. El índice lo calcula `Herramienta.indice`,
  el mismo que usa `buscar_herramientas` en Python.

## Estructura de una herramienta

`layouts/herramienta.html` define el orden común: contexto (área, categoría,
título, descripción), entrada, acción principal, resultado, explicación y
herramientas relacionadas. Cada bloque es opcional:

```django
{% extends "calculadora/layouts/herramienta.html" %}
{% block tool_input %}…{% endblock %}
{% block tool_result %}…{% endblock %}
```

`components/related_tools.html` muestra las relacionadas como enlaces
discretos y no aparece cuando la herramienta no declara ninguna. Las
relaciones se reservan para módulos realmente distintos: las variantes de un
mismo problema (método, bloques del resultado) son opciones del formulario.

## Teclado matemático contextual

`teclados.py` declara `Tecla(etiqueta, insercion, nombre, retroceso)` agrupadas
en un `TecladoContextual`. Cada herramienta incluye solo el teclado que
necesita:

```django
{% include "calculadora/components/math_keyboard.html" with teclado=teclado_sistema campos_id="system-fields" %}
```

`teclado.js` inserta `insercion` en el campo activo del contenedor
`campos_id`. El teclado nace con `hidden` y solo se muestra cuando el script
existe: sin JavaScript no aparenta funcionar. No registres teclas sin una
operación real detrás.

Los controles que cambian la estructura de una entrada (agregar o quitar
ecuaciones y variables; componentes y vectores) son botones aparte, con
`aria-label`, dentro de un grupo «Estructura de la matriz» o «Estructura de
los vectores»; `matriz.js` y `vectores.js` los atienden. No los mezcles con
el teclado ni con la acción principal.

## Vectores

`components/vector.html` escribe un vector en horizontal, `(1, 2, 3)`, como
texto corriente con paréntesis propios: se parte en varias líneas si hace
falta y nunca provoca scroll horizontal. Acepta `nombre` («u =») y
`destacado` para el resultado.

La entrada de Operaciones con vectores es una fila por vector,
`u = ( [ ] [ ] [ ] )`, con una celda `nombre_i` por componente
(`modules/vectores/_fila.html`). La dimensión `n` y la cantidad de vectores
generadores son campos numéricos con botones +/−; `vectores.js` redibuja las
filas con el mismo marcado del parcial y conserva lo escrito. Sin JavaScript,
el botón «Aplicar» (`name="ajustar"`) pide al servidor redibujar la estructura
sin calcular. El teclado contextual es el de la cuadrícula de matrices
(`TECLADO_MATRIZ`: `−` y `a⁄b`), incluido con `campos_id="vector-fields"`.

### Matrices (P13A y P13B)

Una sola herramienta `/matrices/operaciones/` selecciona suma, resta, escalar,
traspuesta, multiplicación de matrices (`AB`) o matriz por vector (`Ax`).
`opciones_matrices.CONFIGURACION` define, por operación, las entradas
necesarias, la forma de cada una como `(campo de filas, campo de columnas)`
—`None` en las columnas señala un vector columna—, los campos de estructura
con su etiqueta, el texto de la forma (`A: {m}×{n} · B: {n}×{p} → AB: {m}×{p}`),
los métodos del procedimiento con sus etiquetas, la presencia del escalar y la
ayuda; el formulario y JavaScript comparten esos datos mediante `json_script`.
Las dimensiones van de 1 a 10 por razones de interfaz. A y B comparten
estructura en suma/resta; en `AB` las filas de B son las columnas de A y solo
se pide `columnas_b`; en `Ax` la dimensión de x es la de las columnas de A.

`MatricesForm` vive en `forms_matrices.py` para no ampliar el formulario común.
Genera campos Django `celda_A_i_j` / `celda_B_i_j` / `celda_x_i_0` con labels
(«Matriz A, fila 1, columna 2», «Vector x, componente 3») y errores asociados,
valida el conjunto exacto de campos y rechaza duplicados. Usa el parser existente
para convertir números a valores exactos. Los campos `columnas_b` y `metodo`
existen siempre, pero quedan **deshabilitados y ocultos** cuando la operación no
los usa: así no viajan en el POST y el botón Aplicar sin JavaScript puede
habilitarlos con su valor inicial al cambiar de operación. En el envío de
cálculo el contrato es estricto: si llegan y la operación no los usa, el POST se
rechaza («campos que no corresponden a la operación seleccionada»); solo Aplicar
los tolera, porque al cambiar de operación el navegador aún envía la estructura
anterior. Cuando la operación los necesita, `clean()` exige que lleguen. El
botón Aplicar valida las dimensiones y conserva las entradas al regenerar, sin
calcular. La edición dinámica utiliza plantillas HTML inertes que incluyen los
mismos componentes del servidor; `matrices.js` reetiqueta las dimensiones y los
métodos, muestra u oculta los controles y genera la cuadrícula de cada entrada
con su forma. No mantiene matrices ocultas dentro del formulario. El teclado se
reutiliza con `campos_id="matrix-fields"`. Tab y flechas permiten recorrer las
celdas.

`components/matriz_entrada.html` y `matriz_celda.html` representan la cuadrícula
(con `vector` cambia la leyenda y las etiquetas a «Vector x»);
`components/matriz.html` muestra valores o expresiones con corchetes, sin columna
aumentada por defecto, y con una sola columna dibuja un vector columna. Acepta
`matriz`, `etiqueta`, `aumentada` y `columnas_pivote`. `matrix.html` es el
adaptador de sistemas con `aumentada=True`. Cada cuadrícula y expresión ancha
tiene scroll local accesible con teclado. Los estilos usan los tokens comunes
de ambos temas.

El backend entrega resultado y pasos por posición con operandos exactos; en la
traspuesta, también identifica la posición de origen; en `AB` y `Ax`, los
productos `aᵢₖbₖⱼ` calculados una vez, agrupados por entrada (`pasos`) y por
columna (`columnas`, con coeficientes, columnas escaladas y columna obtenida).
La capa de presentación solo formatea esos datos: `servicios_matrices.py`
escribe las igualdades (`c₂₃ = fila₂(A) · columna₃(B) = … = 9/2`, `Ab₁ = 2a₁ −
a₂ + 3a₃`) y decide qué bloques mostrar según el método elegido
(`fila_columna`, `columnas` o `comparar`, con identificadores compartidos entre
`AB` y `Ax` y etiquetas distintas). Resultado precede a Procedimiento y se
muestra una sola vez aunque se comparen los métodos. Las plantillas
`_expresion.html`, `_producto.html`, `_producto_fila_columna.html` y
`_producto_columnas.html` agrupan el procedimiento con `details`/`summary` por
fila o por columna, abiertos cuando el resultado tiene pocas entradas
(`ENTRADAS_DESPLEGADAS`). Las igualdades largas se parten en líneas en la fuente
de interfaz, donde los subíndices se leen mejor; las expresiones con matrices
se desplazan localmente. P13B no resuelve ecuaciones matriciales.

## Guía educativa

`frontend/web/calculadora/guias.py` define mensajes estáticos (`GuiaConcepto`)
para acompañar resultados. No es IA, no hace llamadas externas y no genera
matemática nueva: solo selecciona textos conceptuales según método y
clasificación. El parcial `components/concept_guide.html` los renderiza.

## Cómo añadir una herramienta

1. Regístrala en `catalogo.HERRAMIENTAS` con categoría, descripción, palabras
   clave, relaciones e invitación. Con `estado="proximamente"` aparece en el
   árbol y en Inicio sin enlaces.
2. Crea la vista y la ruta con nombre, y una plantilla que extienda
   `calculadora/layouts/herramienta.html`.
3. Reutiliza `.panel`, `.segmented`, `.option`, `.btn`, `.matrix`, `.concept-guide`, el
   teclado contextual y los tokens de `static/calculadora/styles/`.
4. Si muestra matrices, incluye `calculadora/components/matriz.html`; usa
   `matrix.html` para matrices aumentadas de sistemas. Ambos admiten `columnas_pivote`.
5. No copies el `<head>`, el header, la sidebar ni el selector de tema.

Hoy están disponibles las herramientas de sistemas de ecuaciones, las
operaciones con vectores (incluida la combinación lineal), las operaciones con
matrices (incluidos `AB` y `Ax`) y la conversión de bases (sistemas numéricos).
No agregues enlaces a pantallas que todavía no existen.
