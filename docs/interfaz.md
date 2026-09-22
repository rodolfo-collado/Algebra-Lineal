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

- Nombre visible: **PyGebra**; subtítulo en Inicio: **Aprende resolviendo**.
- Símbolo oficial: **Larga A**, negro en claro y blanco en oscuro.
  El header usa un derivado reproducible del SVG canónico, sin placa ni sombra.
- Base blanca/casi negra y grises neutros. Acento `#1A6560` en claro y
  `#7DCFC6` en oscuro, reservado para acciones, enlaces, selección y foco.
- [Identidad visual](identidad-visual.md) documenta la geometría y sus derivados.

El tema claro u oscuro se guarda en `localStorage` (`pygebra-tema`). Se lee
primero esta clave; si falta, se recupera y migra `algebra-lineal-tema`.
Si el almacenamiento está bloqueado, tema y menú siguen funcionando.
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
    ├── shell.css           # header, cajón de navegación, breadcrumbs, layout
    ├── components.css      # herramienta, paneles, botones, buscador, inicio por temas,
    │                       # relacionadas, explorar, desplegables, teclado, controles de
    │                       # estructura, guías, matrices
    └── modules.css         # formularios y resultados de sistemas, bases, vectores y matrices
```

Usa tokens semánticos (`--color-brand`, `--color-accent`, `--color-surface-raised`,
`--color-pivot`, …) en lugar de hexadecimales sueltos. Cada token existe en el
bloque claro y en `[data-theme="dark"]`.

## Movimiento funcional

Las animaciones son una mejora progresiva. Ningún estado, contenido o acción
depende de que una animación se ejecute.

- `--motion-fast` (120 ms) unifica el feedback de controles y chevrons;
  `--motion` (160 ms) se usa para entradas breves. No hay retrasos.
- Botones, steppers, teclas matemáticas y controles de navegación comparten
  pulsación de 1 px y borde interior; `:disabled` excluye hover y pulsación.
  El foco visible se conserva. No hay timers ni cambios en el motor del teclado.
- Radios, casillas y segmentos conservan controles HTML nativos y transiciones
  de fondo/borde. Seleccionar no cambia el peso de letra ni mueve opciones vecinas.
- Los chevrons comunican apertura/cierre. Donde el navegador admite
  [`::details-content`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/::details-content),
  el cuerpo completo entra con opacidad de 0.92 a 1. El cierre es inmediato;
  no se retiene contenido interactivo ni se interpola altura. Sin soporte,
  `<details>/<summary>` conserva todo su comportamiento nativo, también sin JS.
- El panel final usa la misma entrada, visible desde el primer instante, sin
  desplazamiento, espera ni clase añadida por JavaScript.
- No se animan celdas, cambios de dimensiones, regeneraciones de campos, perfiles
  del teclado, controles condicionales ni el desplazamiento del drawer. `hidden`,
  `disabled`, `inert`, Escape y restauración de foco mantienen sus contratos.
  El cambio de tema conserva su comportamiento, sin transición global de colores.

`prefers-reduced-motion: reduce` cancela animaciones y transiciones, incluido el
pseudo-elemento del disclosure. La pulsación no se desplaza; su borde interior,
selección y foco siguen dando feedback instantáneo. Se mantienen las orientaciones
estáticas que explican un estado (chevrons abiertos) o el layout (flecha entre
matrices en móvil), sin animarlas.

Para nuevos componentes: reutilizar estos tokens y estados, declarar cada
propiedad en `transition` (nunca `all`), activar desplazamientos solo dentro de
`prefers-reduced-motion: no-preference` y dejar visible el estado CSS por defecto.
Evitar animaciones por celda, bucles, timers, delays y dependencias nuevas.

## Principio: primero el problema, después las herramientas, al final las opciones

La interfaz reduce la carga cognitiva con divulgación progresiva: el Inicio
solo presenta temas, el menú aparece cuando se pide y, dentro de una
calculadora, el usuario elige el método, escribe el problema y resuelve. El
teclado, las opciones del resultado y las conexiones educativas se despliegan
solo cuando hacen falta. Al añadir módulos (Cálculo, Estadística, …) esta
jerarquía crece por áreas y temas, no con más tarjetas en el Inicio.

## Principio: solo la información que pide cada acción

La cantidad de información mostrada depende de la acción del usuario, no de
toda la información que el sistema sea capaz de producir. Los cálculos y
explicaciones comunes se presentan una sola vez y se reutilizan cuando varias
salidas dependen de ellos. Conversión de bases es la referencia: al pedir
varias bases, el resultado lista solo las escrituras marcadas y el
procedimiento muestra la expansión hacia decimal una vez, con una rama de
divisiones por cada destino que la necesita. La reducción elimina repetición,
no evidencia ni procedimiento educativo.

## Shell y navegación

`templates/calculadora/base.html` monta el header (`☰ Menú`, marca y selector
de tema), el cajón de navegación (`components/sidebar.html`), su fondo y el
contenido con sus breadcrumbs (`components/breadcrumbs.html`). Todo sale del
registro central `catalogo.py` a través de `context_processors.navegacion`,
que también marca la herramienta activa y calcula las relacionadas.

- El cajón es un menú bajo demanda en cualquier tamaño de pantalla: nace
  cerrado, el botón Menú lo abre y lo cierra (`aria-expanded`), y también se
  cierra con Escape, con un clic en el fondo o con el botón Cerrar del propio
  cajón en pantallas estrechas. Mientras está abierto, el contenido queda
  `inert`; al cerrarse, el foco vuelve al botón Menú. No se guarda ninguna
  preferencia de apertura: un overlay abierto al cargar taparía el contenido.
- Dentro, `details`/`summary` por categoría: funciona sin JavaScript y es
  accesible con teclado. `navigation.js` recuerda las categorías abiertas
  (`algebra-lineal-menu-secciones`) y abre los desplegables que contienen el
  destino de un ancla (`/#bases-numericas`) al llegar por la URL.
- El contenido ocupa una sola columna (`--content-max`): matrices grandes,
  procedimientos y comparaciones disponen de todo el ancho.
- El buscador (`components/search.html`) es un formulario `GET` a Inicio.
  `buscador.js` filtra al instante los elementos con `data-indice` de la lista
  indicada en `data-buscador`; los contenedores con `data-grupo` se ocultan
  cuando no tienen coincidencias y los `details` con coincidencias se abren.
  El índice lo calcula `Herramienta.indice`, el mismo que usa
  `buscar_herramientas` en Python. Solo hay un buscador principal, el del
  Inicio; el del cajón filtra el árbol y solo se ve con el menú abierto.

### Inicio por temas

`pages/inicio.html` presenta PyGebra, «Aprende resolviendo», «¿Qué quieres
resolver?» con su buscador y «Explorar por temas». Cada área disponible es
un `details` cerrado; al abrirla aparecen los temas, también plegados, y
cada tema despliega las herramientas de `catalogo.py`. Son filas con bordes
discretos: ninguna cuadrícula de tarjetas ni accesos duplicados. Las áreas
sin herramientas disponibles quedan dentro del menú y de la búsqueda GET,
sin ocupar el Inicio. Con `?q=` se muestran los resultados de búsqueda.

El recorrido es Inicio → área → tema → herramienta → resultado. Los
breadcrumbs abren las anclas de área y categoría con todos sus ancestros.
El drawer también pliega las áreas y conserva búsqueda, categorías,
Escape, backdrop, teclado, restauración de foco, `aria-expanded` e `inert`.

Sin JavaScript la navegación permanece visible en flujo, antes del contenido,
y el buscador usa su envío GET. En sistemas se puede resolver desde texto; la
cuadrícula dinámica y el teclado requieren JavaScript. Vectores, matrices y
Ax = b ofrecen además Aplicar en el servidor para preparar sus estructuras sin
JavaScript. Las antiguas pantallas de métodos de sistemas redirigen a una sola
herramienta con opciones de formulario; ya no se presentan como herramientas
distintas que comparten el mismo sistema.

## Estructura de una herramienta

`layouts/herramienta.html` define el orden común: contexto (área, categoría,
título, descripción), entrada, acción principal, resultado, explicación,
herramientas relacionadas y «También puedes explorar». Cada bloque es opcional:

```django
{% extends "calculadora/layouts/herramienta.html" %}
{% block tool_input %}…{% endblock %}
{% block tool_result %}…{% endblock %}
```

### Entrada → Resultado → Procedimiento plegable

Tras resolver, las herramientas principales (Resolver un sistema, Operaciones
con vectores, Operaciones con matrices y Resolver Ax = b) siguen un mismo
patrón dentro de `section#resultado`:

```html
<header class="results-heading">…<h2 id="results-title">…</h2></header>
<section class="panel panel-final"><h3>Resultado</h3> …</section>
<details class="disclosure disclosure-procedure" id="procedimiento">
    <summary><h3>Ver procedimiento</h3></summary> …
</details>
```

El procedimiento nace cerrado, también después de resolver, y se abre con
ratón, teclado o sin JavaScript. Explica *cómo* se llega (matrices
intermedias, operaciones, matriz final, equivalencias, desarrollo componente
a componente); el panel final dice *qué* se obtuvo. **El resultado se
presenta una sola vez: el procedimiento explica cómo se obtiene, pero no
crea un segundo resultado.** Una cadena puede terminar en la matriz o el
vector obtenido (`= (5, 7, 9)`), pero no hay otro bloque «Resultado»,
clasificación, solución o coeficientes dentro del procedimiento. Al comparar
métodos, cada uno es un sub-bloque cerrado (`disclosure-nested`) y el
resultado común aparece una vez. Conversión de bases e Inicio conservan su
presentación. No se guardan preferencias de apertura.

`components/related_tools.html` muestra las relacionadas como enlaces
discretos después de resolver y no aparece cuando la herramienta no declara
ninguna o ya se muestran exploraciones contextuales. Así se evita duplicar
los destinos. Las relaciones se declaran en el catálogo. Las
relaciones se reservan para módulos realmente distintos: las variantes de un
mismo problema (método, bloques del resultado) son opciones del formulario.

`components/explore.html` («También puedes explorar») aparece solo cuando la
vista entrega `exploraciones`, es decir, después de resolver y con contexto.
Son enlaces a rutas que ya existen; ningún destino se inventa.

### Desplegables

Las opciones avanzadas viven en `details.disclosure` con un `summary` real
(icono, título y chevrón): funcionan sin JavaScript, se abren con Enter o
Espacio y anuncian su estado. Los controles plegados siguen formando parte
del formulario, así que sus valores viajan igual en el envío.

Para los bloques plegables del resultado existe el componente
`{% disclosure %}` (`templatetags/componentes.py`, que renderiza
`components/disclosure.html`):

```django
{% load componentes %}
{% disclosure titulo="Ver procedimiento" id="procedimiento" clase="disclosure-procedure" %}
    …contenido…
{% enddisclosure %}
```

Acepta `nivel=4` (título como `h4`, para sub-bloques), `clase` y `abierto`.
El título va dentro del `summary` como encabezado real, así que la
jerarquía h2 → h3 → h4 se conserva y no hay botones dentro del `summary`.

### Divulgación progresiva en Resolver un sistema

La jerarquía del formulario es: Método y Tipo de entrada como selectores
segmentados (`.segmented`, radios reales, una sola selección) con una pista
de una línea para la opción elegida (`data-method-hint`, `data-input-hint`;
`matriz.js` cambia la visible), el problema (texto o cuadrícula), el teclado
plegado, «Opciones de resultado» plegadas y Resolver. Las opciones conservan
sus casillas y predeterminados (todo activo) y se despliegan solas cuando lo
elegido difiere de lo predeterminado (`opciones_abiertas`).

Tras resolver, «Ver procedimiento» (`#procedimiento`, cerrado) reúne la
matriz inicial, las operaciones por filas (`_procedimiento_metodo.html` con
`_pasos.html`), la matriz final con sus pivotes, el sistema resultante y la
sustitución regresiva (`_bloques_metodo.html`); al comparar, un sub-bloque
cerrado por método y la matriz inicial una vez. Antes, el panel «Resultado
final» muestra la clasificación, la solución, las columnas pivote
(`_pivotes.html`, la lectura directa de la matriz final) y las guías plegadas
(«Entender este resultado»). Si «Procedimiento» está desmarcado no hay
desplegable y la matriz final se muestra en el panel final, para que siga
visible sin repetirse; al comparar, cada matriz final y sistema resultante
nombran su método («Matriz escalonada · Gauss»).

`exploraciones.py` construye «También puedes explorar» tras resolver: el
mismo sistema con el otro método o comparando, los bloques que se dejaron sin
mostrar y Resolver Ax = b. Los enlaces a la propia herramienta llevan la
entrada por GET (`sistema` o las celdas `matriz_i_j` con `ecuaciones` y
`variables`, más `metodo` y `mostrar`); `SistemaForm.inicial_desde` solo
prepara el formulario, nunca resuelve por GET, e ignora valores inválidos.

## Teclado matemático contextual

`teclados.py` conserva `Tecla(etiqueta, insercion, nombre, retroceso)` y
`GrupoTeclas`, y los compone en perfiles declarativos (`Perfil`). La vista
publica únicamente los necesarios mediante `perfiles_para(...)`. Cada
herramienta incluye **una sola instancia** del componente dentro del formulario:

```django
{% include "calculadora/components/math_keyboard.html" %}
```

Los campos heredan `data-perfil` de su contenedor más cercano. En Sistemas,
`system-fields` declara `sistema` y `matrix-fields` declara `numerico`; el
teclado queda fuera de ambos fieldsets para poder alternarlos. Matrices,
Vectores y Ax = b comparten `numerico` (`−`, `a⁄b`). El componente publica los
perfiles con `json_script`; sus plantillas HTML inertes generan grupos y botones
con nombres accesibles y `type="button"`.

`teclado.js` no conoce herramientas ni sintaxis matemática. Delega `focusin`
en el formulario, conserva el último objetivo válido y observa cambios de
perfil, estructura, visibilidad o disponibilidad. Las celdas regeneradas heredan
su perfil; los campos eliminados, ocultos, deshabilitados o de solo lectura no
reciben inserciones. `setRangeText` respeta cursor y selección; `retroceso`
recoloca el cursor, se devuelve el foco y se emite un único evento `input`
que burbujea. No se intercepta la escritura física.

El teclado sigue plegado bajo «Teclado matemático»; tanto el desplegable como
el teclado nacen con `hidden` y solo se muestran si hay JavaScript y un campo
válido. Sin JavaScript los formularios y sus POST mantienen el comportamiento
anterior. Añadir un perfil consiste en registrarlo, publicarlo desde la vista
y declararlo en los campos, sin modificar el motor. No registres teclas sin
una inserción real detrás.

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
sin calcular. `vector-fields` declara `data-perfil="numerico"`, compartido
con las celdas de matrices y Ax = b, incluido el escalar cuando está presente.

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
reutiliza con `data-perfil="numerico"` en `matrix-fields`. Tab y flechas permiten recorrer las
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
`AB` y `Ax` y etiquetas distintas). El procedimiento va plegado después del
panel Resultado, que muestra la matriz una sola vez aunque se comparen los
métodos. `_expresion.html` escribe la expresión como una sola cadena
(operandos → desarrollo por entradas → matriz obtenida) y la comparten
`_procedimiento.html` (suma, resta, escalar y traspuesta) y
`_producto_fila_columna.html`; `_producto.html` pliega cada método en un
sub-bloque al comparar, y `_producto_fila_columna.html` y
`_producto_columnas.html` agrupan el desarrollo con `details`/`summary` por
fila o por columna, abiertos cuando el resultado tiene pocas entradas
(`ENTRADAS_DESPLEGADAS`). Las igualdades largas se parten en líneas en la fuente
de interfaz, donde los subíndices se leen mejor; las expresiones con matrices
se desplazan localmente. Resolver una ecuación matricial tiene su propio formulario.

## Expresiones matriciales

`/matrices/expresiones/` compone las operaciones ya existentes. El formulario
empieza con un símbolo; **Agregar símbolo** y **Eliminar** cambian la lista, y
el tipo o las dimensiones se ajustan en ese símbolo. Con JavaScript,
`expresiones.js` redibuja las celdas y conserva lo escrito. Sin JavaScript,
**Aplicar** pide al servidor la estructura nueva antes de calcular. El cálculo
no añade una opción a `CONFIGURACION`.

El resultado va primero. **Ver procedimiento** lista los nodos de abajo hacia
arriba y cada uno puede pedirse solo con **Calcular solo esta parte**. El
selector Exacto/Decimal es el de las demás herramientas de álgebra.

Si el texto trae un solo `=`, la misma página muestra el lado izquierdo, el
lado derecho y si coinciden para los valores definidos. No hay un selector
Expresión/Igualdad. El procedimiento de cada lado sigue plegado; las rutas de
**Calcular solo esta parte** son `izq:…` y `der:…`. Exacto/Decimal formatea
ambos lados después de la comparación exacta.

## Resolver Ax = b

`/matrices/ecuaciones/` resuelve `Ax = b` cuando x es la incógnita.
Es un formulario aparte, `EcuacionMatricialForm` (`forms_ecuaciones.py`): x es la incógnita,
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
Resolver un sistema, y `modules/ecuaciones/_metodos.html` incluye
`modules/sistemas/_procedimiento_metodo.html` con todos los bloques visibles
(`mostrar`) y las columnas pivote una vez. «Ver procedimiento» reúne
`_equivalencias.html` (ecuación matricial, ecuación vectorial con las
columnas de A, sistema equivalente y `[A | b]` con `matrix.html`) y la
eliminación (un sub-bloque cerrado por método al comparar); antes, el panel
Resultado (`.classification` con `data-kind` y la solución, conjunto solución
o contradicción) se muestra una vez, y después van plegados «Comprobar
solución» (`A · x = b`) e «Interpretar Ax = b» (combinación lineal de las
columnas de A).

## Conversión de bases

`/bases/conversion/` (`ConversionBasesForm`, `servicios_bases.py`,
`modules/bases/`) pide el número, una única base de origen (`<select>`) y las
bases de destino bajo **Convertir a**: un `fieldset` con `legend` y una casilla
real por base, descrito por su ayuda y sus errores (`aria-describedby`).
`conversion.js` oculta y desactiva la casilla de la base de origen al cargar y
al cambiar el origen, conserva las demás marcas y avisa en vivo si no queda
ningún destino; sin JavaScript se ven las cuatro casillas y el servidor rechaza
origen = destino, cero destinos, destinos repetidos, bases inexistentes, campos
ajenos o repetidos y números de más de `LONGITUD_MAXIMA` caracteres, siempre
con un mensaje comprensible. No hay botón de intercambio ni botones por par de
bases.

El resultado (`.base-results`) escribe el origen una sola vez y, debajo, una
escritura por destino con el nombre de su base, en el orden de las casillas.
El procedimiento (`_procedimiento.html`) aplica el
[principio de no repetición](#principio-solo-la-información-que-pide-cada-acción):
si el origen no es decimal, la ruta `origen → decimal intermedio → ramas`
(`.stage-route`) y la Etapa 1 (expansión posicional) aparecen una vez y cada
destino no decimal añade solo su etapa de divisiones; el destino decimal, si se
pidió, es ese valor intermedio y no genera una etapa propia. Con origen decimal
no hay etapa intermedia. Los datos llegan del servicio (`resultados`, `etapas`,
`intermedio`, `ramas`, `decimal_pedido`); la plantilla no calcula ni repite.
El único teclado cambia entre los perfiles `base-2`, `base-8`, `base-10` y
`base-16`. `conversion.js` actualiza `data-perfil` de `number-fields` al cambiar
el origen; recibe nombres, perfiles y dígitos en `bases-digitos`, derivados
del mismo registro. No contiene otra tabla de dígitos ni manipula teclados.
La selección multidestino de P16 mantiene sus controles y su contrato POST.

## Guía educativa

`frontend/web/calculadora/guias.py` define mensajes estáticos (`GuiaConcepto`)
para acompañar resultados. No es IA, no hace llamadas externas y no genera
matemática nueva: solo selecciona textos conceptuales según método y
clasificación. El parcial `components/concept_guide.html` los renderiza.

## Cómo añadir una herramienta

Sigue el flujo de [Desarrollo](desarrollo.md#añadir-una-herramienta).
En presentación, reutiliza `.panel`, `.segmented`, `.option`, `.btn`, `.matrix`,
`.disclosure`, `{% disclosure %}`, `.concept-guide`, `components/explore.html`,
el teclado contextual y los tokens compartidos, y sigue el patrón Entrada →
Resultado → Procedimiento plegable. Si muestra
matrices, usa `components/matriz.html`; para sistemas aumentados, `matrix.html`.
Ambos admiten `columnas_pivote`. No copies el `<head>`, header, sidebar o selector
de tema: extiende el layout común.

Hoy están disponibles las herramientas de sistemas de ecuaciones, las
operaciones con vectores (incluida la combinación lineal), las operaciones con
matrices (incluidos `AB` y `Ax`), Resolver Ax = b y la conversión de bases.
No agregues enlaces a pantallas que todavía no existen.

## Formato exacto y decimal

Sistemas, Vectores (incluida combinación lineal), Matrices (incluidos AB y Ax)
y Ax=b ofrecen un selector discreto junto al resultado. Exacto es el valor
predeterminado y el contenido del HTML sin JavaScript. Decimal permite elegir
un máximo de 2, 4, 6 u 8 decimales; el valor inicial es 4. Se recortan ceros
finales: `7/2` → `3.5`, `4` → `4`, `1/3` → `0.3333`.

`presentacion_numerica.py` calcula estas representaciones directamente del
numerador y denominador, con redondeo a la mitad al par. No usa `float`.
`templatetags/numeros.py` adapta el bloque de resultados ya calculados:
valores, expresiones, matrices intermedias, operaciones por filas, sustitución,
comprobación y etiquetas accesibles. Las expresiones heredadas conservan
sus literales racionales exactos; el adaptador los representa, sin evaluar
la expresión ni cambiar los índices. La entrada queda fuera del bloque.

`components/numeric_format.html` es el control compartido y `numeros.js`
solo cambia texto/atributos preparados por Python. Cambiar modo o precisión
no envía formularios ni ejecuta motores. Las igualdades de líneas redondeadas
usan `≈`; para matrices y cadenas repartidas en celdas, una nota de grupo
informa la precisión únicamente cuando existe aproximación.

Se guardan `pygebra-formato-numerico` y `pygebra-precision-decimal` en
`localStorage`, sin cookies ni estado de negocio. Si falla el almacenamiento,
se parte de Exacto y se pueden cambiar los controles durante esa visita.
Sin JavaScript los controles permanecen ocultos y la matemática exacta
continúa visible. Conversión de bases conserva su significado y no incluye
este selector. Los algoritmos y sus resultados `Fraction` no cambian.
