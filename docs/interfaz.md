# Interfaz visual

[Índice de documentación](README.md) · [Portada](../README.md)

La aplicación desktop y Django en desarrollo comparten la misma interfaz.

Esta guía conserva las decisiones de UI/UX. Los ejemplos de uso están en
[Funcionalidades](funcionalidades.md) y la organización del código en
[Arquitectura](arquitectura.md). Las rutas abreviadas de componentes y recursos
se entienden dentro de `frontend/web/calculadora/`.

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
  Escape o el fondo cierran el cajón y devuelven el foco al botón Menú.
- El buscador (`components/search.html`) es un formulario `GET` a Inicio.
  `buscador.js` filtra al instante los elementos con `data-indice` de la lista
  indicada en `data-buscador`; los contenedores con `data-grupo` se ocultan
  cuando no tienen coincidencias. El índice lo calcula `Herramienta.indice`,
  el mismo que usa `buscar_herramientas` en Python.

El recorrido es Inicio → área → categoría → herramienta → resultado. Los
breadcrumbs de área y categoría enlazan a su sección del Inicio. Límites sigue
marcado como «Próximamente», sin enlace a una pantalla inexistente.

Sin JavaScript la navegación permanece visible y el buscador usa su envío GET.
En sistemas se puede resolver desde texto; la cuadrícula dinámica y el teclado
requieren JavaScript. Vectores, matrices y Ax = b ofrecen además Aplicar en el
servidor para preparar sus estructuras sin JavaScript. Las antiguas pantallas de
métodos de sistemas redirigen a una sola herramienta con opciones de formulario;
ya no se presentan como herramientas distintas que comparten el mismo sistema.

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

## Matrices

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
se desplazan localmente. Resolver una ecuación matricial tiene su propio formulario.

## Resolver Ax = b

`/matrices/ecuaciones/` es la segunda herramienta de Matrices y un formulario
aparte, `EcuacionMatricialForm` (`forms_ecuaciones.py`): x es la incógnita,
así que no es una operación más de `MatricesForm`. Ambos heredan de
`FormularioCeldas` (`forms_matrices.py`), que genera las celdas
`celda_<nombre>_<i>_<j>` con sus labels, rechaza campos repetidos, compara el
conjunto exacto de celdas recibidas con el esperado y convierte los números
con el parser común. Solo se piden las filas y columnas de A: b se genera con
m componentes (`celda_b_i_0`) y x se muestra con
`components/matriz.html` como columna `x₁ … xₙ` sin celdas, con un texto
`sr-only` que explica cuántas componentes desconocidas tiene. La fila de
entrada «A · x = b» (`.equation-entry`) se desplaza localmente cuando A es
ancha; en pantallas estrechas las celdas se compactan para que 2×2 quepa
entero. `ecuaciones.js` regenera A, b y x con las mismas plantillas inertes
de matrices y actualiza `A (m×n) · x (n) = b (m)`; sin JavaScript, Aplicar
redibuja la misma estructura. El método (`opciones_ecuaciones.py`) reutiliza
`METODOS`, el predeterminado y `metodos_a_resolver` de `opciones_sistemas.py`.

`servicios_ecuaciones.py` no calcula: llama a
`backend.ecuaciones_matriciales.resolver_ecuacion_matricial` por cada método
y formatea el enunciado (`Ax = b tiene solución única.`), el vector x, la
comprobación `A · x = Ax = b`, la interpretación como combinación lineal
(`b = 3a₁ + 2a₂`, escrita con `combinacion_columnas` de
`servicios_matrices.py`) y la cadena de equivalencias. La eliminación se
presenta con `servicios.presentar_resolucion`, la misma adaptación de
Resolver un sistema, y las plantillas `modules/ecuaciones/_metodos.html`
incluyen `modules/sistemas/_pasos.html` y `_bloques_metodo.html` con todos
los bloques visibles (`mostrar`) y las columnas pivote de cada método. El
resultado (`.classification` con `data-kind`, solución, comprobación e
interpretación) precede a `_equivalencias.html` (ecuación matricial, ecuación
vectorial con las columnas de A, sistema equivalente y `[A | b]` con
`matrix.html`) y a los paneles de eliminación; al comparar, el resultado se
muestra una vez y hay un panel por método.

## Guía educativa

`frontend/web/calculadora/guias.py` define mensajes estáticos (`GuiaConcepto`)
para acompañar resultados. No es IA, no hace llamadas externas y no genera
matemática nueva: solo selecciona textos conceptuales según método y
clasificación. El parcial `components/concept_guide.html` los renderiza.

## Cómo añadir una herramienta

Sigue el flujo de [Desarrollo](desarrollo.md#añadir-una-herramienta).
En presentación, reutiliza `.panel`, `.segmented`, `.option`, `.btn`, `.matrix`,
`.concept-guide`, el teclado contextual y los tokens compartidos. Si muestra
matrices, usa `components/matriz.html`; para sistemas aumentados, `matrix.html`.
Ambos admiten `columnas_pivote`. No copies el `<head>`, header, sidebar o selector
de tema: extiende el layout común.

Hoy están disponibles las herramientas de sistemas de ecuaciones, las
operaciones con vectores (incluida la combinación lineal), las operaciones con
matrices (incluidos `AB` y `Ax`), Resolver Ax = b y la conversión de bases.
No agregues enlaces a pantallas que todavía no existen.
