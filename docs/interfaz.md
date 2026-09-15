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
    └── modules.css         # formulario y resultados de sistemas
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

`components/related_tools.html` muestra las relacionadas de forma discreta.
Cuando la vista indica `formulario_compartido` e `ids_comparten_entrada` y ya
hay un resultado, cada relacionada se convierte en un botón `formaction` que
envía la misma entrada a la otra herramienta.

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
ecuaciones y variables) son botones aparte, con `aria-label`, dentro de un
grupo «Estructura de la matriz»; `matriz.js` los atiende. No los mezcles con
el teclado ni con la acción principal.

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
3. Reutiliza `.panel`, `.choice`, `.btn`, `.matrix`, `.concept-guide`, el
   teclado contextual y los tokens de `static/calculadora/styles/`.
4. Si muestra matrices, incluye `calculadora/components/matrix.html`; acepta
   `columnas_pivote` para resaltar columnas.
5. No copies el `<head>`, el header, la sidebar ni el selector de tema.

Hoy están disponibles las herramientas de sistemas de ecuaciones y la
conversión de bases (sistemas numéricos). No agregues enlaces a pantallas
que todavía no existen.
