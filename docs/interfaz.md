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
En la app de escritorio también se conserva entre aperturas (ver [Escritorio](#escritorio)).
Si el almacenamiento está bloqueado, tema y menú siguen funcionando.
Si el usuario no ha elegido, se respeta `prefers-color-scheme`. El icono del
selector representa el tema activo: sol en claro, luna en oscuro.
Tema anuncia la acción de cambiar al tema opuesto y solo aparece cuando JavaScript lo hace operativo.

Todo debe funcionar sin Internet. No uses Google Fonts, CDN ni iconos remotos.

## Principio: la interfaz habla matemáticas

El usuario no tiene por qué conocer la sintaxis del parser. Lo que se muestra
es notación matemática (`x₁`, `−`, `a⁄b`) y lo que se envía es la sintaxis
interna (`x1`, `-`, `/`). Cuando una herramienta necesite símbolos, declara un
teclado contextual (ver abajo) en lugar de pedir al usuario que los escriba.

Los resultados de Reducción por filas, Resolver Ax = b y Combinación lineal
presentan las incógnitas como `x₁, x₂, …` con el filtro `incognitas`
(`templatetags/numeros.py`). Solo cambia la presentación: servicios, parser,
campos, cuadrícula de entrada, placeholders y ayudas de sintaxis siguen en
`x1`, y una misma salida nunca mezcla ambas formas. Operaciones con matrices
conserva su notación lineal ASCII (`x1 a1 + x2 a2`, `[3, 1, 0]^T`), coherente
en sí misma. Los nombres de vectores (`v1`, `v2`, …) son identificadores.

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
    │                       # estructura, matrices
    └── modules.css         # formularios y resultados de sistemas, bases, vectores y matrices
```

Usa tokens semánticos (`--color-brand`, `--color-accent`, `--color-surface-raised`,
`--color-pivot`, …) en lugar de hexadecimales sueltos. Cada token existe en el
bloque claro y en `[data-theme="dark"]`.

### Formularios

Contrato común de los formularios de herramienta (P27.8):

- **Escala.** `--text-xs` (0.8rem) para metadatos, como los encabezados `x1` y `F1`
  de la cuadrícula; `--text-sm` (0.875rem) para etiquetas, leyendas, ayudas,
  opciones, errores y títulos de desplegables; `--text-base` (1rem) para títulos de
  sección y valores. No sustituye todos los tamaños de la aplicación.
- **Etiquetas.** Una sola regla para `legend` y para todo `label` visible de
  `.workspace` (las píldoras `.option` y `.segment` tienen la suya): `--text-sm`,
  peso 600 y `--space-1` hasta su control, también en el campo principal. Son
  `<label for>` reales: Nombre y Tipo de cada símbolo van encima de su control, como
  Filas y Columnas, y `expresiones.js` conserva la asociación al reindexar. Los
  formularios usan `label_suffix = ""`: ninguna etiqueta termina en «:» automático.
  Las ayudas (`.field-help`) van en `--text-sm`, regulares y en `--color-muted`.
- **Bordes de campo.** `--color-border-input` (`#858585` en claro, `#7a7a7a` en
  oscuro) delimita inputs, selects, textareas, celdas, el buscador y los botones del
  stepper; alcanza al menos 3:1 sobre todas las superficies donde viven (relaciones en
  la [validación P27.8](validacion-p27-8.md)). Prioridad: normal < hover
  (`--color-muted`) < foco (`--color-brand` y anillo) < error (`--color-danger`, que
  se mantiene con hover y foco); deshabilitado vuelve a `--color-border` con
  opacidad. Paneles, tarjetas, píldoras y botones con texto conservan `--color-border`.
- **Placeholders.** `::placeholder` usa `--color-muted` con opacidad 1: como mínimo
  5,49:1 en claro y 6,74:1 en oscuro en los campos probados; sigue siendo más tenue
  que un valor escrito.

## Movimiento funcional

Las animaciones son una mejora progresiva. Ningún estado, contenido o acción
depende de que una animación se ejecute.

- `--motion-fast` (120 ms) unifica el feedback de controles y chevrons;
  `--motion` (160 ms) se usa para entradas breves. No hay retrasos.
- Botones, steppers, teclas matemáticas y controles de navegación comparten
  pulsación de 1 px y borde interior; `:disabled` excluye hover y pulsación.
  El foco visible se conserva.
- Radios, casillas y segmentos conservan controles HTML nativos y transiciones
  de fondo/borde. Seleccionar no cambia el peso de letra ni mueve opciones vecinas.
- Los chevrons comunican apertura/cierre. Donde el navegador admite
  [`::details-content`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Selectors/::details-content),
  el cuerpo completo entra con opacidad de 0.92 a 1. El cierre es inmediato;
  no se retiene contenido interactivo ni se interpola altura. Sin soporte,
  `<details>/<summary>` conserva todo su comportamiento nativo, también sin JS.
- El panel final usa la misma entrada, visible desde el primer instante, sin
  desplazamiento, espera ni clase añadida por JavaScript.
- El dock entra en 160 ms con opacidad y 10 px de desplazamiento, y sale en
  120 ms. Su etiqueta y acento verde lo identifican; en modo compacto se oculta
  la etiqueta. Al salir pierde destino e interacción inmediatamente, conserva
  las teclas durante la transición y aplica `hidden` al finalizar. Un nuevo
  foco cancela ese cierre; cambiar de campo compatible no reinicia la entrada.
  Con movimiento reducido la apertura y el cierre son inmediatos.
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
  accesible con teclado. `navigation.js` recuerda las categorías abiertas solo
  durante la ejecución (`sessionStorage`, clave `algebra-lineal-menu-secciones`):
  un arranque nuevo parte limpio y se retira la copia en `localStorage` de
  versiones anteriores. También abre los desplegables que contienen el
  destino de un ancla (`/#bases-numericas`) al llegar por la URL.
- Una página restaurada del historial (`pageshow` con `persisted`) vuelve con
  el cajón cerrado, `data-drawer` retirado, fondo oculto, `main` sin `inert`,
  `aria-expanded="false"` y el foco fuera del cajón (pasa al botón Menú).
- El contenido ocupa una sola columna (`--content-max`): matrices grandes,
  procedimientos y comparaciones disponen de todo el ancho.
- La cabecera es fija. `html { scroll-padding-top: cabecera + 1.5rem }` reserva su
  altura para todo desplazamiento automático: Tab y Shift+Tab, anclas como
  `#resultado` y `scrollIntoView`. Dentro del procedimiento abierto, lo enfocable
  añade la franja del summary sticky (`scroll-margin-top`). El teclado matemático solo
  reserva el final de la página.
- El buscador (`components/search.html`) es un formulario `GET` a Inicio.
  `buscador.js` consulta el índice completo publicado por `catalogo.py`, incluidas
  las próximas, con la misma semántica y orden del servidor. Inicio conserva
  una fila por herramienta: al filtrar traslada esas filas a una lista ordenada;
  al limpiar restaura los temas y su apertura. El cajón conserva su árbol,
  oculta grupos sin coincidencias y abre los que coinciden; limpiar restaura
  los grupos sin alterar la memoria de categorías.
  Se ignoran `de`, `a`, `al`, `el`, `la`, `los`, `las`, `un`, `una`, `calcular`,
  `hallar`, `método` y `pasar`. Una consulta formada solo por esos términos
  no encuentra herramientas. Las acciones útiles se declaran como palabras
  clave: invertir, multiplicar, sumar, restar, transponer, convertir y reducir.
  En un GET se ocultan las filas que no coinciden y se enfoca la región de
  resultados con contorno visible. El status live nace vacío; al editar oculta
  el encabezado/recuento anterior y anuncia solo la consulta actual. Volver al
  valor exacto restaura el estado servidor. Los vacíos ofrecen enlaces `?q=`.
  Escape lateral con texto limpia sin cerrar el Menú; vacío puede cerrarlo.

### Inicio por temas

`pages/inicio.html` presenta PyGebra, «Aprende resolviendo», «¿Qué quieres
resolver?» con su buscador y «Explorar por temas». Cada área disponible es
un `details` cerrado; al abrirla aparecen los temas plegados, salvo los que
tienen exactamente una herramienta disponible (`Categoria.herramienta_unica`):
nacen abiertos para mostrarla sin otro clic. Esa apertura no se guarda y el
buscador restaura lo que el usuario abrió o cerró. Cada tema despliega las
herramientas de `catalogo.py`. Son filas con bordes
discretos: ninguna cuadrícula de tarjetas ni accesos duplicados. Las áreas
sin herramientas disponibles permanecen ocultas en Inicio y se encuentran
tanto por GET como en vivo. Cálculo muestra «Próximamente» en el Menú.
Con `?q=` se muestran únicamente las coincidencias; todas las filas permanecen
en el DOM para permitir cambiar la consulta sin otro envío.

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

`layouts/herramienta.html` define el orden común: título y descripción (área y
tema ya están en las migas, así que no hay kicker encima del título), entrada,
acción principal, resultado, explicación, herramientas relacionadas y «También
puedes explorar». Cada bloque es opcional:

```django
{% extends "calculadora/layouts/herramienta.html" %}
{% block tool_input %}…{% endblock %}
{% block tool_result %}…{% endblock %}
```

### Entrada → Procedimiento plegable → Resultado

Tras resolver, todas las herramientas con resultado (Reducción por filas,
Operaciones con vectores, Operaciones con matrices,
Resolver Ax = b, Matriz inversa, Conversión de bases y Conversión de números romanos) siguen
un mismo patrón dentro de `section#resultado`:

```html
<header class="results-heading">…<h2 id="results-title">…</h2></header>
<details class="disclosure disclosure-procedure" id="procedimiento">
    <summary><h3>Ver procedimiento</h3></summary> …
</details>
<section class="panel panel-final"><h3>Resultado</h3> …</section>
```

El procedimiento nace cerrado, también después de resolver, y se abre con
ratón, teclado o sin JavaScript. Se puede ignorar: el resultado va justo
después, fuera del `details`, así que se ve igual con el procedimiento abierto
o cerrado. El orden se decide en el HTML, no con CSS: el lector de pantalla y
el foco del teclado recorren lo mismo que se ve. El procedimiento explica
*cómo* se llega (matrices intermedias, operaciones, matriz final,
equivalencias, desarrollo componente a componente); el panel final dice *qué*
se obtuvo. **El resultado se presenta una sola vez: el procedimiento explica
cómo se obtiene, pero no crea un segundo resultado.** Una cadena puede
terminar en la matriz o el vector obtenido (`= (5, 7, 9)`), pero no hay otro
bloque «Resultado», clasificación, solución o coeficientes dentro del
procedimiento. Al comparar métodos, cada uno es un sub-bloque cerrado
(`disclosure-nested`) y el resultado común aparece una vez. Inicio conserva su
presentación. No se guardan preferencias de apertura.

Mientras está abierto, solo el `summary` principal del procedimiento permanece
sticky bajo la cabecera, con fondo sólido y foco visible. Los disclosures
anidados conservan su posición. Plegarlo desde abajo acerca el bloque cerrado
y el Resultado, sin animar el salto ni interferir con el teclado contextual.

P27.6 declara `data-entrada-calculo` en el formulario y
`data-resultado="vigente"` en el resultado de un POST válido. `resultado.js`
compara los datos enviados al cálculo cuando recibe `input`, `change` o
`entrada-cambiada` (cambios estructurales hechos con JS). La primera modificación
cambia a `desactualizado` y añade una única nota `role="status"`: «Cambiaste los
datos. Este resultado corresponde a la entrada anterior. Vuelve a calcular para
actualizarlo». El contenido sigue legible, seleccionable y desplazable; el panel
final usa un borde secundario discontinuo. Ediciones posteriores no vuelven a
anunciarlo y el siguiente POST válido entrega un documento vigente.

Números, matrices, vectores, expresiones, operación, método, dimensiones y
opciones que cambian el cálculo o el procedimiento sí lo desactualizan.
Exacto/Decimal y precisión son presentación fuera del formulario; tema, Menú,
foco, apertura de Opciones/procedimiento y teclado sin insertar datos tampoco
lo desactualizan. CSRF y la firma de confirmación no son entrada matemática.
No se detecta la vuelta exacta A → B → A. `feedback.js` sigue siendo el único
responsable de busy, foco de errores y confirmaciones; en `pageshow` restaura
la espera. Menú, tema y formato numérico tienen su propio `pageshow`,
independiente e idempotente (ver [Escritorio](#escritorio)).

`components/related_tools.html` muestra las relacionadas como enlaces
discretos después de resolver y no aparece cuando la herramienta no declara
ninguna o ya se muestran exploraciones contextuales. Así se evita duplicar
los destinos. Reutiliza la sección y el título de `components/explore.html`:
ambas dicen «También puedes explorar», sin puntos suspensivos. Cada enlace muestra nombre e `invitacion`: una frase breve que
explica cuándo usar esa alternativa. Reducción orienta desde el sistema escrito
o la matriz aumentada; Ax = b desde A y b conocidos. Operaciones con matrices
también enlaza a Matriz inversa; Ax = b no propone resolver por inversión.
Las relaciones se declaran en el catálogo. Las
relaciones se reservan para módulos realmente distintos: las variantes de un
mismo problema (método, bloques del resultado) son opciones del formulario.

`components/explore.html` («También puedes explorar») aparece solo cuando la
vista entrega `exploraciones`, es decir, después de resolver y con contexto.
Son enlaces a rutas que ya existen; ningún destino se inventa.

### Desplegables

Todo bloque plegable de una herramienta —opciones, ayuda, aplicaciones,
procedimiento, sub-bloques y grupos de un producto— usa el componente
`{% disclosure %}` (`templatetags/componentes.py`, que renderiza
`components/disclosure.html`); las plantillas de `modules/` no escriben
`<details>` a mano. Solo la navegación (Menú e Inicio por temas) conserva sus
propios `details`, con el chevrón a la derecha de cada fila.

```django
{% load componentes %}
{% disclosure titulo="Opciones de resultado" id="opciones-resultado" abierto=opciones_abiertas icono="opciones" %}
    …contenido…
{% enddisclosure %}
```

- El título va dentro del `summary` como encabezado real: h3 por defecto y
  `nivel=4`, `5` o `6` en sub-bloques y grupos, así que la jerarquía se conserva y
  no hay botones dentro del `summary`.
- El chevrón va siempre primero, con el mismo tamaño y color, y gira al abrir.
- `icono="opciones"` añade el engranaje solo a las opciones de configuración
  («Opciones de resultado», «Opciones del procedimiento»).
- `detalle` añade un resumen secundario: los grupos por fila o columna de AB y Ax
  muestran, por ejemplo, `c₁₁ = 3, c₁₂ = 6`.
- `clase` elige la variante: `disclosure-procedure` (Ver procedimiento),
  `disclosure-nested` (un método al comparar) y `procedure-group` (grupos de un
  producto, abiertos solo cuando el resultado es pequeño). `abierto` decide el
  estado inicial, como antes.
- Hover común (un matiz de `--color-text` sobre cualquier fondo, también sobre el
  summary sticky), foco visible y al menos 2.5rem de alto. Solo el summary
  principal del procedimiento abierto es sticky.

Funcionan sin JavaScript, se abren con Enter o Espacio y anuncian su estado. Los
controles plegados siguen formando parte del formulario, así que sus valores viajan
igual en el envío.

### Divulgación progresiva en Reducción por filas

La jerarquía del formulario es: Método y Tipo de entrada como selectores
segmentados (`.segmented`, radios reales, una sola selección) con una pista
de una línea para la opción elegida (`data-method-hint`, `data-input-hint`;
`matriz.js` cambia la visible), el problema (el campo «Ecuaciones» —la opción
ya dice «Sistema de ecuaciones»— o la cuadrícula, a 1rem de las pistas),
«Opciones de resultado» plegadas y Resolver. El teclado aparece al enfocar
una entrada compatible y desaparece al salir. Las opciones conservan
sus casillas y predeterminados (todo activo) y se despliegan solas cuando lo
elegido difiere de lo predeterminado (`opciones_abiertas`).

Tras resolver, «Ver procedimiento» (`#procedimiento`, cerrado) reúne la
forma estándar de las ecuaciones escritas con términos en ambos lados (solo si
alguna cambió: `resultado.reescritas`, que da `analizar_sistema`), la
matriz inicial, las operaciones por filas (`_procedimiento_metodo.html` con
`_pasos.html`), la matriz final con sus pivotes, el sistema resultante y la
sustitución regresiva (`_bloques_metodo.html`); al comparar, un sub-bloque
cerrado por método y la matriz inicial una vez. Después, el panel
«Resultado» muestra la clasificación, la solución y las columnas pivote
(`_pivotes.html`, la lectura directa de la matriz final). Su leyenda nombra el
bloque donde se resaltan («Los pivotes se resaltan en la matriz reducida del
procedimiento.»): matriz escalonada, reducida o ambas al comparar, y «del
procedimiento» solo cuando la matriz está dentro del desplegable. Sin
procedimiento ni comparación, la cabecera del resultado no lleva kicker. Si «Procedimiento»
está desmarcado no hay desplegable y la matriz final se muestra en el panel
final, para que siga visible sin repetirse; al comparar, cada matriz final y
sistema resultante nombran su método («Matriz escalonada · Gauss»).

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
teclado queda fuera de ambos fieldsets para poder alternarlos. Celdas de matrices,
vectores numéricos y Ax = b comparten `numerico` (`−`, `a⁄b`). En Operaciones,
la expresión usa `expresion` (`( )`, `ᵀ`, `+`, `−`, `=`, `a⁄b`) y las componentes
de vectores lineales usan `lineal` (x₁…x₆, `+`, `−`, `a⁄b`). Los nombres de
operandos y los números romanos no tienen teclado matemático. `sistema` ofrece
x₁…x₆ y «Nueva ecuación» inserta solo un salto de línea. El componente publica los
perfiles con `json_script`; sus plantillas HTML inertes generan grupos y botones
con nombres accesibles y `type="button"`.

`teclado.js` no conoce herramientas ni sintaxis matemática. Delega el foco en
el documento: solo el campo compatible activo puede ser objetivo; no existe
fallback al primer campo ni se conserva el destino al pasar a otro control.
Las celdas regeneradas heredan su perfil; un observador invalida campos eliminados,
ocultos, deshabilitados o de solo lectura y actualiza cambios de perfil.
`mousedown` de las teclas conserva el foco del campo. `execCommand("insertText")`
respeta cursor, selección y Ctrl+Z en Chromium; reafirmar la selección antes y
después separa esta edición de la escritura física. `setRangeText` es el fallback
de inserción si no está disponible (sin garantía de undo en ese navegador).
`retroceso` recoloca el cursor y se emite un único `input`. Las teclas usan
`tabindex="-1"` y nombres accesibles que comienzan con su etiqueta visible.
Escape oculta sin editar; el teclado físico siempre sigue disponible.

En Operaciones, el contenedor de la expresión declara `data-operandos="#symbol-list"`.
El teclado lee los campos `data-campo="nombre"` de esa lista, respetando sus nombres
y mayúsculas, y se actualiza con `input`, `change` y cambios de estructura. No guarda
otro catálogo de operandos. Separa **Operandos**, **Notación** y **Operadores**;
la traspuesta muestra e inserta `ᵀ`, que el lexer interpreta igual que `^T`.
No ofrece inversas ni potencias: no pertenecen al lenguaje de expresiones.
Los operandos se desplazan en su propia fila; en móvil ocupan una fila sobre las
herramientas matemáticas, con reserva inferior para mantener visible el campo.

El dock nace con `hidden`, sin botón de apertura, y aparece al enfocar una
entrada compatible. Se oculta al pasar a Opciones, Calcular, Menú, Tema u otro
control. Entre entradas compatibles permanece visible y adapta su perfil.
Es fijo, alineado con la columna principal y debajo de la cabecera y del menú.
La reserva estable al final y `scroll-padding` evitan tapar el campo o mover
Calcular al ocultarlo. Con altura ≤640 px oculta título y ayuda; en móvil, los
operandos conservan su fila y los nombres de los grupos. Las teclas que no caben
se desplazan dentro del dock. Sin JavaScript no se ve el teclado
y los formularios siguen funcionando. Añadir un perfil consiste en registrarlo,
publicarlo desde la vista y declararlo en los campos, sin modificar el motor. No registres teclas sin
una inserción real detrás.

Los controles que cambian la estructura de una entrada (agregar o quitar
ecuaciones y variables; componentes y vectores) son botones aparte, con
`aria-label`, dentro de un grupo «Estructura de la matriz» o «Estructura de
los vectores»; `matriz.js` y `vectores.js` los atienden. No los mezcles con
el teclado ni con la acción principal.

## Vectores

`components/vector.html` escribe un vector en horizontal, `(1, 2, 3)`, como
texto corriente con paréntesis propios: se parte en varias líneas si hace
falta y nunca provoca scroll horizontal. Acepta `nombre` («v1 =») y
`destacado` para el resultado.

La entrada de Operaciones con vectores es una fila por vector,
`v1 = ( [ ] [ ] [ ] )`, con una celda `nombre_i` por componente
(`modules/vectores/_fila.html`). La dimensión `n` y la cantidad de vectores
generadores son campos numéricos con botones +/−; `vectores.js` redibuja las
filas con el mismo marcado del parcial y conserva lo escrito. Sin JavaScript,
el botón «Aplicar» (`name="ajustar"`) pide al servidor redibujar la estructura
sin calcular. `vector-fields` declara `data-perfil="numerico"`, compartido
con las celdas de matrices y Ax = b, incluido el escalar cuando está presente.

Los vectores se llaman `v1`, `v2`, … en todas las operaciones (`k·v1` en la
multiplicación por escalar; `v1 … vk` y `b` en la combinación): agregar uno
nunca renombra a los anteriores y la memoria por nombre conserva los valores
al cambiar de operación. La cabecera del resultado es solo su título: un
kicker con el nombre de la operación lo repetiría.

La lista de vectores se desplaza horizontalmente como una unidad: nombres y
componentes de cada columna permanecen alineados, también con valores de distinto
ancho. El × pertenece a su fila y queda después de la última componente; bajo
760 px caben tres componentes junto a él. **Agregar
vector** lleva el foco a la primera componente del nuevo; quitar uno lo lleva a la
fila que ocupa su lugar o, si era el último, a la anterior. Un `role="status"` bajo
Agregar dice «Se agregó el vector v3.» o «Se eliminó el vector v3.»; los botones ±
de la cantidad también avisan, sin mover el foco.

## Operaciones con matrices

Una sola herramienta, `/matrices/operaciones/`, para operaciones simples y
compuestas (P26.6): el formulario es el de operandos y expresión, así que `A + B`,
`2A`, `AB`, `Ax`, `Aᵀ` y `A(B + C) - 2D` siguen el mismo flujo. No hay un modo
«sencillo» aparte ni un selector de operación. Las plantillas viven en
`modules/expresiones/` (el motor es el de expresiones) y reutilizan los
parciales de procedimiento de `modules/matrices/`.

El formulario (`ExpresionMatricialForm`, `forms_expresiones.py`) empieza con dos
matrices 2×2, A y B. Cada símbolo es un bloque `symbol-card` con nombre, tipo
—«Con valores» (matriz, vector, escalar) y, aparte, «Simbólicos» (matriz
desconocida, vector simbólico, vector lineal) como `optgroup`—, dimensiones y
celdas `celda_<índice>_<i>_<j>` con labels reales («Matriz A, fila 1, columna
2»). **Agregar símbolo**, **Eliminar** y **Aplicar** funcionan sin JavaScript;
con JavaScript, `expresiones.js` redibuja la cuadrícula conservando lo escrito,
propone nombres libres (A … Z, después A1, B1 …) y mueve el foco con las flechas
dentro de la cuadrícula de cada símbolo. El contrato HTTP es estricto: el
servidor reconstruye el conjunto exacto de campos de la estructura declarada y
rechaza celdas de más, de menos, campos desconocidos o repetidos.

Cada operando es un `fieldset` con nombre accesible («Operando A»): Nombre y Tipo
arriba y, juntas, Filas y Columnas con **Eliminar** a la derecha, lejos de sus + y
−. Los botones dicen a qué operando pertenecen («Eliminar operando A», «Agregar una
fila a A», «Quitar una componente de u»): el servidor los escribe
(`rotulos_dimension`) y `expresiones.js` los actualiza al renombrar. En escritorio
van dos tarjetas por fila y una matriz de seis columnas o más ocupa la fila entera;
el orden del DOM y de Tab no cambia. Al agregar, el foco va al nombre del operando
nuevo; al eliminar, al nombre del siguiente, al del anterior o a **Agregar
operando**, y la región `role="status"` dice «Se agregó el operando C.» o «Se eliminó
el operando B.». La expresión mide las dos líneas de `rows`, sin la altura mínima del
área de texto de sistemas.

Bajo la expresión, una ayuda breve con ejemplos (`A + B`, `2A - B`, `AB`, `Ax`,
`A(B + C)`, `Aᵀ`, también `A^T`) y un desplegable «Cómo se escribe» con la
multiplicación implícita, la traspuesta, el orden de las operaciones, `=` y los
tipos simbólicos. Las opciones avanzadas no compiten con la entrada: **Opciones
del procedimiento** es un `{% disclosure %}` cerrado con la presentación de los
productos (radios `metodo`: fila por columna, por columnas o comparar ambos) y se
abre solo cuando el valor enviado no es el predeterminado.

El presupuesto común (50 operandos, 900 celdas, 990 campos) se comprueba antes de
crear campos; los topes viajan como `data-*` del campo oculto `cantidad` y
`expresiones.js` aplica la misma regla: agregar, redimensionar o cambiar de tipo
no se aplican si no caben, y un aviso `role="status"` lo explica. La expresión se
analiza en `clean()` para contar operandos, operaciones y entradas antes de
evaluar.

Tras calcular, **Ver procedimiento** va primero y plegado. Lista un paso por nodo
del árbol, en el orden en que se calculó (hijos primero), cada uno con su
subexpresión y dimensiones como encabezado (h4) y su procedimiento debajo:

- suma, resta, escalar y traspuesta usan `matrices/_por_entrada.html` (la regla
  por entrada, los traslados de fila a columna en la traspuesta y la cadena
  `_expresion.html`: operandos → desarrollo por entradas → matriz obtenida);
- `AB` y `Ax` usan `matrices/_metodos_producto.html`, que muestra la lectura
  elegida o, al comparar, un sub-bloque cerrado por lectura (h5), con
  `_producto_fila_columna.html` y `_producto_columnas.html` y sus grupos por fila
  o columna abiertos cuando el resultado tiene pocas entradas
  (`ENTRADAS_DESPLEGADAS`);
- los vectores y escalares, una línea por componente.

Cada paso intermedio cierra con su valor (el que usa el paso siguiente) y ofrece
**Calcular solo esta parte**; el último no repite su valor: el resultado aparece
una sola vez, en el panel Resultado. En una igualdad, el procedimiento separa
«Lado izquierdo» y «Lado derecho» (pasos en h5), los dos valores se muestran en
paneles y el veredicto cierra la página; cada lado puede pedirse solo (`izq:…`,
`der:…`). Si A es una matriz desconocida, x un vector simbólico y el otro lado un
vector lineal, el resultado es la matriz y, plegado, cómo se obtuvo.

El backend entrega resultado y pasos por posición con operandos exactos; en la
traspuesta, también la posición de origen; en `AB` y `Ax`, los productos
`aᵢₖbₖⱼ` calculados una vez, agrupados por entrada (`pasos`) y por columna
(`columnas`). `servicios_matrices.py` solo escribe esos datos
(`presentar_producto`, `presentar_por_entrada`): `c₂₃ = fila₂(A) · columna₃(B) =
… = 9/2`, `Ab₁ = 2a₁ − a₂ + 3a₃` o, dentro de una expresión mayor,
`(A(B + C))₁₁ = fila₁(A) · columna₁(B + C)`. `opciones_matrices.py` guarda los
nombres de las lecturas y sus identificadores compartidos entre `AB` y `Ax`.

`components/matriz_entrada.html` y `matriz_celda.html` (Resolver Ax = b e
inversa) representan cuadrículas editables; `components/matriz.html` muestra
valores o expresiones con corchetes, sin columna aumentada por defecto, y con
una sola columna dibuja un vector columna. `matrix.html` es el adaptador de
sistemas con `aumentada=True`.

Las celdas editables (`.matrix-input`) crecen con su valor (`field-sizing:
content`) entre `--celda-min` (4.25rem; bajo 760 px, 3rem en Ax = b y 3.2rem en
Vectores) y 7rem (18rem en un vector lineal): `-11/13`, `123/456` o `3.14159` se
leen completos mientras se editan. En tablas y en la cuadrícula aumentada la
columna toma el ancho de su valor más largo, así que sus celdas siguen alineadas,
y la cuadrícula se desplaza en lugar de comprimirse. Más allá del máximo, el input
conserva cursor y desplazamiento. Sin soporte de `field-sizing` queda el ancho fijo. `.matrix-scroll` contiene `.matrix-content` con
ambos corchetes y todas las columnas. `.matrix-equation` permite wrap sin crear
otro scroll alrededor de la misma matriz; los hijos flex/grid pueden reducirse
con `min-width: 0` y columnas `minmax(0, 1fr)`. Las notas largas envuelven texto,
sin ocultar overflow de la página.

Los pares Antes → Después usan flex con wrap. `presentacion.js` mide el ancho
natural de ambas matrices y la transición: conserva la fila si cabe y coloca
la flecha hacia abajo en su propia fila cuando deben apilarse. No depende del
orden de la matriz ni de un breakpoint específico.

El mismo script observa tamaño/contenido y reevalúa al cargar, redimensionar,
abrir disclosures o cambiar la presentación numérica. Añade `tabindex="0"`
solo a salidas con `scrollWidth > clientWidth + 1`, con nombre accesible y anillo
normal de foco; lo retira al dejar de desbordar. Las entradas se recorren por sus
inputs, nunca por sus contenedores. Sin JS el HTML no añade paradas Tab mudas.

`/matrices/expresiones/` es solo compatibilidad: GET 301 y POST 308 hacia
`/matrices/operaciones/`, sin plantilla ni tarjeta propias.

## Resolver Ax = b

`/matrices/ecuaciones/` resuelve `Ax = b` cuando x es la incógnita.
Es un formulario aparte, `EcuacionMatricialForm` (`forms_ecuaciones.py`): x es la incógnita,
así que no es una operación más de Operaciones con matrices. Ambos heredan de
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
Reducción por filas, y `modules/ecuaciones/_metodos.html` incluye
`modules/sistemas/_procedimiento_metodo.html` con todos los bloques visibles
(`mostrar`) y las columnas pivote una vez. «Ver procedimiento» reúne
`_equivalencias.html` (ecuación matricial, ecuación vectorial con las
columnas de A, sistema equivalente y `[A | b]` con `matrix.html`) y la
eliminación (un sub-bloque cerrado por método al comparar); después, el
panel Resultado (`.classification` con `data-kind` y la solución, conjunto
solución o contradicción) se muestra una vez, y tras él van plegados
«Comprobar solución» (`A · x = b`) e «Interpretar Ax = b» (combinación lineal
de las columnas de A), que parten de la solución.

## Matriz inversa

`/matrices/inversa/` (`InversaForm` en `forms_inversa.py`,
`servicios_inversa.py`, `modules/inversa/`) reutiliza `FormularioCeldas`,
`_dimension.html` y las plantillas de celdas. Como A es cuadrada, un solo
control, **Filas y columnas**, define su tamaño. `inversa.js` regenera la
cuadrícula y desactiva el radio **Método para matrices 2×2** fuera de 2×2 (el
servidor también lo desactiva y rechaza un envío manipulado). Los nombres de
los métodos no llevan fórmulas; la regla `ad − bc` solo aparece dentro del
procedimiento.

En **Aplicaciones y propiedades** (`{% disclosure %}` con `id="aplicaciones"`),
cada opción dice antes de elegirla qué calcula o comprueba —«Comprueba (AB)⁻¹ =
B⁻¹A⁻¹.», «Calcula x = A⁻¹b y comprueba Ax = b.»— en una línea secundaria junto a
su radio, que la describe con `aria-describedby` (`AYUDAS_FUNCIONES` en
`servicios_inversa.py`, `RadiosConAyuda` en `forms_inversa.py`). Los algoritmos,
las opciones y la verificación no cambian.

El procedimiento de Gauss-Jordan reutiliza `modules/sistemas/_pasos.html` con
`columnas_izquierda = n`, así que el separador de `[A | I]` se ve en todas las
matrices. El resultado (`A⁻¹ =` o «La matriz no tiene inversa.») va al final y
usa Exacto / Decimal.

Si se solicitó Verificar, Resultado añade la conclusión breve de la
comprobación real del servicio: `A·A⁻¹ = A⁻¹·A = I ✓` solo cuando ambos
productos son identidad. Si falla un producto se indica `≠ I`; si A no es
invertible se indica que la verificación no está disponible. Los productos
completos siguen dentro del procedimiento. También funciona con la regla 2×2
y las aplicaciones adicionales, sin recalcular ni duplicar matrices.

Cuando la estimación es pesada, el formulario muestra arriba un aviso
(`_confirmacion.html`, `.confirmation`) en tonos neutros con acento verde,
nunca con el estilo `.alert` de los errores: dice que la matriz es válida, el
tiempo aproximado y pregunta si continuar. **Cancelar** reutiliza `ajustar`
y **Continuar** envía una firma de la entrada que el servidor comprueba. En
móvil, los dos botones ocupan cada uno su fila. Editar la matriz oculta el
aviso. Consulta [Matriz inversa](matriz-inversa.md#presupuesto-y-confirmación).

## Conversión de bases

`/bases/conversion/` (`ConversionBasesForm`, `servicios_bases.py`,
`modules/bases/`) pide primero la base de origen (`<select>`), que decide qué
dígitos valen, el teclado y la validación en vivo; después el número y las
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
Va después de «Ver procedimiento», plegado con `{% disclosure %}` como en las
demás herramientas. El procedimiento (`_procedimiento.html`) aplica el
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

La expectativa histórica del runner DOM que comprobaba solo `01` se corrigió
en P27.3: el contrato de `base-N` incluye dígitos, punto decimal y signo (`01.-`
para base 2), como ya comprobaban las pruebas Python y la validación del número.

## Conversión de números romanos

`/romanos/conversion/` (`ConversionRomanosForm`, `servicios_romanos.py`,
`modules/romanos/`) pide la dirección con un `.segmented` (Arábigo → romano o
Romano → arábigo) y un único campo de hasta 15 caracteres, descrito por su
ayuda (`aria-describedby`). Etiqueta (**Número arábigo** o **Número romano**)
y ayuda tienen un `span[data-direccion]` por dirección y el CSS (`:has`)
muestra el de la dirección marcada, también sin JavaScript. Si lo escrito
solo se convierte en la otra dirección, el error lo sugiere
(`sugerir_direccion`); si no vale en ninguna, queda el mensaje original. No tiene teclado matemático ni selector Exacto /
Decimal: trabaja con enteros y símbolos romanos, y no necesita JavaScript.
Los valores enviados (`decimal_a_romano` y `romano_a_decimal`) llevan el
nombre de las funciones del backend; lo que se lee siempre es «arábigo».
Sigue Entrada → Procedimiento plegable → Resultado: `{% disclosure %}` guarda
la descomposición por órdenes decimales o la lectura de izquierda a derecha,
con la suma o la resta de cada fila entre paréntesis, y el panel final
reutiliza `.base-results` (el origen una vez y, debajo, la escritura obtenida).
El servidor rechaza campos ajenos o repetidos y direcciones inexistentes con
un mensaje propio. Conversión de bases y esta herramienta se sugieren entre sí
tras convertir.

## Cómo añadir una herramienta

Sigue el flujo de [Desarrollo](desarrollo.md#añadir-una-herramienta).
En presentación, reutiliza `.panel`, `.segmented`, `.option`, `.btn`, `.matrix`,
`.disclosure`, `{% disclosure %}`, `components/explore.html`,
el teclado contextual y los tokens compartidos, y sigue el patrón Entrada →
Procedimiento plegable → Resultado. Si muestra
matrices, usa `components/matriz.html`; para sistemas aumentados, `matrix.html`.
Ambos admiten `columnas_pivote`. No copies el `<head>`, header, sidebar o selector
de tema: extiende el layout común.

Hoy están disponibles las herramientas de sistemas de ecuaciones, las
operaciones con vectores (incluida la combinación lineal), las operaciones con
matrices (incluidos `AB` y `Ax`), Resolver Ax = b, la matriz inversa, la
conversión de bases y la de números romanos.
No agregues enlaces a pantallas que todavía no existen.

## Formato exacto y decimal

Sistemas, Vectores (incluida combinación lineal), Matrices (incluidos AB y Ax),
Ax=b y Matriz inversa ofrecen un selector discreto junto al resultado cuando al
menos un texto numérico del bloque tiene representaciones distintas. En salidas
enteras o textuales sin variantes permanece oculto y la preferencia global se conserva.
Exacto es el valor
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
`localStorage`, sin cookies ni estado de negocio; en escritorio también entre
aperturas. Al cargar y al restaurar del historial, `numeros.js` aplica la
preferencia vigente sin recalcular, sin `input`/`change` (el resultado no queda
desactualizado) y sin repetir el aviso si no cambió. Los dos selectores llevan
`autocomplete="off"` para que volver con el historial no restaure un valor
antiguo. Si falla el almacenamiento,
se parte de Exacto y se pueden cambiar los controles durante esa visita.
Sin JavaScript los controles permanecen ocultos y la matemática exacta
continúa visible. Conversión de bases conserva su significado y no incluye
este selector. Los algoritmos y sus resultados `Fraction` no cambian.

## Escritorio

La app de escritorio muestra esta misma interfaz en WebView2, sin barra de
navegador. Django publica una única señal declarativa, `<html data-desktop>`,
solo con `DESKTOP_MODE`; la web normal no la recibe y conserva el
comportamiento de su navegador.

- **Historial.** No hay botones Atrás/Adelante ni barra de direcciones: la
  navegación visible siguen siendo migas, Menú, buscador y relacionadas. Los
  botones laterales del ratón los atiende WebView2. `navigation.js` añade
  Alt+← (`history.back()`) y Alt+→ (`history.forward()`) solo con
  `data-desktop` y sin pila propia; ignora Ctrl, Shift, AltGr (Ctrl+Alt),
  composición IME y eventos ya atendidos. Las cuadrículas dejan Alt+flecha al
  historial; Ctrl+←/→ y las flechas sin modificador no cambian.
- **Volver con el historial.** WebView2 no usa bfcache: volver recarga la
  página desde su caché, también un resultado POST, sin pedir reenvío. Los
  formularios de cálculo llevan `autocomplete="off"`: al volver muestran los
  datos que produjeron el resultado, no ediciones posteriores que lo dejarían
  vigente por error. En navegadores con bfcache, `pageshow` restaura Menú, tema
  y formato numérico (secciones anteriores).
- **Preferencias.** Entre aperturas solo se conservan `pygebra-tema`,
  `pygebra-formato-numerico` y `pygebra-precision-decimal`. WebView2 corre en
  modo privado y Django las guarda en `%LOCALAPPDATA%\PyGebra\preferencias.json`
  (`POST /preferencias/` con CSRF, lista blanca de claves y valores, escritura
  atómica) y las pinta como `data-pygebra-…` en `<html>`. Durante la ejecución
  manda `localStorage`. No se guardan URL, herramienta, formularios, matrices,
  resultados, procedimientos, scroll, foco, Menú ni historial: cada arranque
  abre Inicio con el cajón cerrado.
- **Clic derecho.** El menú nativo de WebView2 se filtra a Cortar, Copiar,
  Pegar y Seleccionar todo (sin Imprimir, Emoji ni «Más herramientas»); sin
  acciones de edición no aparece. Es edición real del navegador: los eventos
  `input`, deshacer y el aviso de resultado desactualizado funcionan, y el foco
  no sale del campo, así que el teclado matemático sigue abierto. En la web no
  se sustituye el menú del navegador.
- **Atajos del navegador.** Siguen desactivados (F5, Ctrl+R, Ctrl+P, Ctrl+F,
  F12 y DevTools). `ALGEBRA_DESKTOP_DEBUG=1` devuelve los de pywebview, con su
  menú completo, solo para diagnóstico.

### Páginas de error

`templates/404.html` reutiliza la interfaz normal: Menú y buscador ayudan a
encontrar la herramienta. `400.html`, `403.html`, `403_csrf.html` y `500.html`
extienden `calculadora/errores/base.html`: marca PyGebra, mensaje breve e
«Ir al inicio» hacia la raíz `/`, sin catálogo, `reverse()` ni JavaScript, porque
Django renderiza el 500 sin request. Nunca muestran traceback, motivo técnico
ni datos del error. Django solo las usa con `DEBUG=False`, siempre en escritorio.

## Entrada y edición de datos (P27.9)

`entradas.js` atiende el evento `paste`, tanto de Ctrl+V como del menú contextual,
con tres adaptaciones pequeñas al DOM existente: tablas editables, matriz
aumentada y filas de vectores. Solo usa `text/plain`: TAB separa columnas y LF
o CRLF separan filas. Ignora las líneas vacías de los extremos (la terminación de
una hoja de cálculo o un salto de más al copiar un resultado); una línea vacía
interior sigue siendo una fila y se valida igual. Conserva celdas vacías y
espacios internos, recortando únicamente los extremos. Las comas
permanecen dentro del valor. Una sola celda conserva el paste nativo.

- **Destino.** Reducción por filas [A | b]; A y b de Ax=b; A y B/b opcionales de
  Inversa; matrices y vectores editables de Operaciones; componentes de Vectores.
  Cada tabla se limita a su símbolo. En Vectores, filas = vectores visibles y
  columnas = componentes: una columna pegada recorre vectores, una fila recorre
  componentes. No incluye el escalar k, resultados, procedimiento ni incógnitas.
- **Todo o nada.** Antes de escribir comprueba que el bloque sea rectangular,
  que quepa completo desde la celda inicial, que todos los destinos sean editables
  y que ningún valor exceda su `maxlength`. Si falla, conserva todas las entradas
  y anuncia el motivo; no redimensiona ni hace pegados parciales.
- **Estado y foco.** Aplica todos los valores antes de emitir un `input` por celda.
  Reutiliza `resultado.js` para stale, conservando el resultado previo y el teclado
  contextual. Mantiene el foco inicial. Reutiliza el status de símbolos/vectores
  o crea un `role=status` en el formulario: «Se pegaron N valores.» No calcula,
  envía, interpreta HTML ni valida aritmética. Los límites numéricos existentes
  siguen en el servidor; el límite de 200 caracteres de componentes lineales se
  conserva también después de reconstruirlas.
- **Matriz aumentada lista.** La primera elección propone 3 ecuaciones × 3
  variables: 3 filas con 3 coeficientes y b, visualmente 3×4. Las dimensiones
  explícitas, valores y errores POST prevalecen. Alternar con texto conserva la
  memoria durante la página, sin almacenamiento entre herramientas/sesiones.
  Sin JS, Reducción mantiene el fallback textual; las demás herramientas mantienen
  Aplicar/POST.
- **Flechas.** Las cinco cuadrículas comparten la guarda de edición: ← navega
  solo en posición 0 y → solo al final, sin selección. Modificadores, AltGr,
  composición y eventos ya atendidos conservan el comportamiento nativo;
  Alt+←/→ sigue disponible para el historial desktop. ↑/↓ conservan sus destinos.
- **Forma libre.** La ayuda asociada mediante `aria-describedby` explica x1,
  x2, … con x minúscula, enteros/fracciones/punto decimal y ecuaciones separadas
  por `;` o saltos de línea. Advierte sobre x/y/z, X1, coma decimal y `;` final
  vacío. Ejemplo: `2x1 - x2 = 3; x1 + 4x2 = 7`. El placeholder anterior es válido
  y se conserva, sin `;` al final del sistema.

Sin transferencia automática (UI-74), CSV/Excel, drag & drop ni gestor de undo.
El undo de una sola celda queda al navegador; no se promete undo atómico de bloques.
Evidencia y límites en [validación P27.9](validacion-p27-9.md).
