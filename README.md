# Álgebra Lineal

Proyecto educativo en Python para implementar manualmente algoritmos de matrices
y álgebra lineal. El objetivo no es resolver operaciones rápido, sino escribir el
algoritmo paso a paso y entender cómo funciona por dentro.

La aplicación se puede usar desde la terminal, mediante un menú interactivo, o
desde una interfaz desktop local. Django sigue siendo la capa de presentación;
la ventana nativa solo muestra esa interfaz, con identidad visual propia, tema
claro/oscuro y funcionamiento completo sin Internet. La estructura de la
interfaz está pensada para ir añadiendo más temas del curso como módulos, sin
rediseñar la aplicación cada vez.

## Funcionalidades actuales

- Generar una matriz con valores aleatorios a partir de sus dimensiones.
- Crear una matriz ingresando cada elemento manualmente.
- Crear un sistema de ecuaciones, escribiéndolo directamente como texto o
  ingresando sus coeficientes uno por uno.
- Modificar un elemento en una posición dada.
- Consultar un elemento en una posición dada.
- Mostrar la matriz completa con las columnas alineadas.
- Resolver el sistema por **Gauss**, mostrando la eliminación hacia abajo, la
  matriz escalonada y la sustitución regresiva.
- Resolver el sistema por **Gauss-Jordan**, mostrando la reducción completa y la
  matriz reducida.
- Traducir la matriz resultante de vuelta a su sistema de ecuaciones, clasificarlo
  y mostrar el conjunto solución completo: valores exactos cuando la solución es
  única, variables libres identificadas y variables pivote despejadas en función
  de ellas cuando hay infinitas, y la contradicción a la vista cuando no hay
  solución.
- Resolver sistemas desde la interfaz desktop o Django mediante texto o una
  matriz aumentada editable, sin reemplazar la interfaz de terminal.
- Usar una interfaz visual propia, con tema claro u oscuro, matrices con
  notación de corchetes y el procedimiento paso a paso como pieza central.

El menú principal es este:

```text
1. Generar matriz
2. Crear matriz
3. Crear sistema de ecuaciones
4. Modificar elemento
5. Consultar elemento
6. Ver matriz
7. Resolver por Gauss
8. Resolver por Gauss-Jordan
9. Salir
```

Los cálculos usan `fractions.Fraction`, así que los resultados son exactos y se
muestran como fracciones cuando no son enteros.

La interfaz de terminal usa colores, limpia la pantalla entre secciones y espera
una confirmación antes de volver al menú, para que los resultados se puedan leer
con calma.

## Sistemas de ecuaciones

La opción `Crear sistema de ecuaciones` abre un submenú:

```text
1. Ingresar sistema directamente
2. Ingresar coeficientes manualmente
3. Volver
```

En el ingreso directo se escribe el sistema completo, separando las ecuaciones
con `;`:

```text
x1 - 3x2 - 5x3 = 0; x2 + x3 = 3
```

que produce esta matriz aumentada:

```text
[  1  -3  -5   0 ]
[  0   1   1   3 ]
```

Las variables son `x1`, `x2`, `x3`, … con índice desde 1. Se admiten espacios
libres, coeficientes implícitos (`x1` vale `1x1` y `-x2` vale `-1x2`), variables
ausentes (valen cero), enteros, fracciones (`1/2x1`) y decimales (`0.5x1`). El
lado derecho del `=` debe ser un número.

El ingreso manual pide la cantidad de variables y de ecuaciones, y luego cada
coeficiente y cada término independiente. Ambas formas producen exactamente la
misma matriz aumentada, así que son intercambiables.

Volver al menú, o escribir un sistema con un formato inválido, deja intacta la
matriz activa: solo un sistema creado correctamente la reemplaza.

## Resolver un sistema

Una matriz solo se interpreta como sistema de ecuaciones cuando se elige uno de
los dos métodos de resolución. En ese caso la **última columna** se toma
explícitamente como los términos independientes; el significado nunca se deduce
de las dimensiones. Por eso una matriz `3 x 3` puede ser una matriz cualquiera o
el sistema de 3 ecuaciones y 2 variables, según la opción que se use. Da igual si
la matriz se creó con `Crear matriz` o con `Crear sistema de ecuaciones`.

La diferencia entre los dos métodos está en el procedimiento:

- **Gauss** solo elimina hacia abajo y deja la matriz escalonada. Cuando la
  solución es única muestra además la sustitución regresiva paso a paso.
- **Gauss-Jordan** continúa eliminando hacia arriba hasta la forma reducida.

Para el mismo sistema los dos llegan siempre a la misma clasificación y a la
misma solución final.

La clasificación del sistema es una de estas tres:

```text
Consistente de solución única
Consistente de soluciones infinitas
Inconsistente
```

## Interpretación del resultado

La salida se adapta a la clasificación obtenida. La matriz, la clasificación y
la solución siempre se muestran; el **sistema resultante** se conserva cuando
ayuda a interpretar una forma escalonada, una variable libre o una
contradicción. Si la matriz ya permite leer directamente `x1 = C1`, `x2 = C2`,
etc., no se repiten esas mismas ecuaciones antes de la solución.

Por ejemplo, una solución única leída directamente se presenta de forma breve:

```text
Consistente de solución única

x1 = 3
x2 = 2/3
```

En Gauss, el sistema resultante sí se mantiene cuando permite seguir la
sustitución regresiva. Las filas nulas (`0 = 0`) no cambian por sí solas la
clasificación: si todas las variables tienen pivote, la solución sigue siendo
única.

La **solución** es la interpretación final del conjunto solución. Si falta algún
pivote, las variables de esas columnas quedan libres y las demás se despejan en
función de ellas:

```text
Sistema resultante

x1 - 5x3 = 1
x2 + x3 = 4

Clasificación

Consistente de soluciones infinitas

Solución

La variable x3 no tiene pivote, por lo que es libre.

x1 = 1 + 5x3
x2 = 4 - x3
x3 es libre
```

El despeje es simbólico y sigue hasta que ninguna variable pivote dependa de otra
variable pivote. Para `x1 + x2 + x3 = 5` junto a `x2 + x3 = 2`, la solución es
`x1 = 3`, no `x1 = 5 - x2 - x3`. Todo se calcula con fracciones exactas, y las
variables se listan de `x1` a `xn` aunque algunas sean libres.

Cuando existe una fila contradictoria, se muestra su posición y su contenido
exacto. Por ejemplo:

```text
0 = 5

En la fila 3 se obtiene [0 0 0 | 5], que equivale a 0 = 5.

Como esta igualdad es imposible, el sistema es inconsistente y no tiene solución.
```

La evidencia estructurada —fila contradictoria, filas redundantes, columnas sin
pivote y valores como `Fraction`— se calcula en `backend/`. La terminal solo la
presenta, de modo que cualquier otra interfaz puede reutilizar la misma
interpretación sin reconstruir conclusiones matemáticas.

Gauss-Jordan sigue sirviendo para reducir **cualquier matriz rectangular**
(`2 x 3`, `3 x 2`, `4 x 3`, etc.), sin exigir matrices cuadradas ni de la forma
`n x (n+1)`, y sin suponer que toda fila o toda columna acabe con pivote. Esa
capacidad vive en `backend/gauss_jordan.py` y se puede reutilizar, aunque el menú
esté orientado a resolver sistemas.

## Requisitos

- [uv](https://docs.astral.sh/uv/) instalado. Consulta su documentación oficial
  para instalarlo en tu sistema.
- Python 3.13. La versión está fijada en `.python-version`, y `uv` la descarga por
  ti si todavía no la tienes.
- `colorama`, usada solo para dar color a la terminal.
- `Django`, usado únicamente como capa de presentación web.
- `waitress`, usado como servidor WSGI local de la aplicación desktop.
- `pywebview`, usado para mostrar Django en una ventana nativa.
- `PyInstaller`, disponible como dependencia de desarrollo para generar Windows.

Los cálculos y la interpretación de los sistemas siguen apoyándose en nuestra
implementación del backend y en la biblioteca estándar (`random`, `fractions` y
`re`).

## Instalación

Desde la raíz del repositorio:

```bash
uv sync
```

`pyproject.toml` declara qué necesita el proyecto y `uv.lock` fija las versiones
exactas que se resolvieron a partir de esa declaración. `uv sync` construye el
entorno en `.venv/` usando ambos archivos, así que todos los colaboradores
trabajan con las mismas versiones.

## Ejecución

Desde la raíz del repositorio:

### Terminal

```bash
uv run python main.py
```

Para salir, elige la opción `9` del menú.

### Django en desarrollo

Desde la raíz del repositorio, inicia el servidor de desarrollo:

```bash
uv run python manage.py runserver
```

Abre <http://127.0.0.1:8000/> en el navegador. La interfaz permite elegir el
tipo de entrada —sistema de ecuaciones o matriz aumentada— y el método Gauss o
Gauss-Jordan. El selector de tema recuerda la preferencia en el navegador; si
no hay una elección previa, respeta el modo claro u oscuro del sistema. En el
modo matricial indica las dimensiones y completa una cuadrícula con la última
columna reservada para los términos independientes:

```text
       x1   x2   b
F1    [ 1 ] [ 2 ] | [ 4 ]
F2    [ 2 ] [-1 ] | [ 7 ]
```

Ambos modos muestran la matriz inicial, los pasos, la clasificación y la
solución. Django solo coordina la entrada y la presentación: la capa de
integración converge en una matriz aumentada y delega los cálculos a `backend/`.

### Aplicación de escritorio durante desarrollo

Desde Windows, el launcher inicia Django con Waitress en un puerto efímero de
`127.0.0.1` y abre una ventana nativa con pywebview. No usa `runserver` ni abre
un navegador externo:

```bash
uv run python desktop.py
```

La readiness se comprueba con un `HTTP GET /` antes de crear la ventana. Al
cerrarla, el launcher llama a `server.close()` y espera el final del thread de
Waitress.

### Generar distribución de Windows

La configuración reproducible está en `AlgebraLineal.spec`. Desde la raíz del
repositorio ejecuta:

```bash
uv run pyinstaller --noconfirm --clean AlgebraLineal.spec
```

La distribución confiable es `onedir`: copia la carpeta completa
`dist/AlgebraLineal/` y ejecuta `AlgebraLineal.exe` desde ella. El `.spec`
incluye explícitamente los templates, CSS, JavaScript e icono local de Django, y
configura la aplicación sin consola adicional (`windowed`). `dist/` y `build/`
están ignorados por Git.

En Windows, pywebview usa el backend WebView2. La distribución no descarga ese
runtime silenciosamente: se espera que Windows 10/11 ya lo tenga instalado. Si
no está disponible, instala manualmente Microsoft Edge WebView2 Runtime y
vuelve a abrir `AlgebraLineal.exe`.

### Usuario final

El usuario solo necesita abrir `AlgebraLineal.exe` dentro de la carpeta
`AlgebraLineal/`. No necesita Python, `uv`, una terminal, un navegador manual ni
Internet para usar la calculadora: CSS, JavaScript, tipografías del sistema e
icono van empaquetados con la distribución.

## Pruebas

Desde la raíz del repositorio:

```bash
uv run python -m unittest discover -v
```

Las de `tests/` cubren las reglas matemáticas del backend (validaciones, matrices
rectangulares, pivotes, escalonamiento, sustitución regresiva y clasificación de
sistemas), las expresiones lineales y su formato, la traducción de una matriz a
su sistema, el conjunto solución con variables libres, el parser de sistemas, la
equivalencia entre Gauss y Gauss-Jordan, el flujo de la terminal, la interfaz web
de Django —incluidas sus entradas textual y matricial—, la infraestructura
desktop y que la interfaz no cargue fuentes ni scripts remotos. Sirven para
detectar regresiones cuando el proyecto crezca.

Para comprobar que todo el código compila:

```bash
uv run python -m compileall -q backend frontend tests main.py manage.py desktop.py
```

## Restricciones matemáticas

Este es un proyecto educativo: **los algoritmos de álgebra lineal deben
implementarse manualmente**.

Está prohibido utilizar:

- NumPy;
- SciPy;
- SymPy para resolver operaciones de álgebra lineal;
- funciones de librerías externas que calculen directamente Gauss, Gauss-Jordan,
  rango, determinantes, sistemas de ecuaciones u operaciones equivalentes;
- cualquier librería que sustituya el desarrollo manual del algoritmo.

La implementación debe construirse con herramientas estándar de Python: listas,
listas anidadas, `if` / `else`, `for`, `while`, funciones, operaciones aritméticas
y estructuras propias del lenguaje.

`fractions.Fraction` sí está permitido: pertenece a la biblioteca estándar y
únicamente representa números racionales con exactitud, no resuelve ningún
algoritmo por sí mismo.

`colorama` también está permitido, pero únicamente para dar color a la terminal:
no participa en ningún cálculo ni sustituye ningún algoritmo.

`tests/test_restricciones_proyecto.py` comprueba esta regla de forma automática:
analiza los imports del código con `ast` y revisa las dependencias declaradas en
`pyproject.toml`, así que la prohibición ya no depende de una revisión manual.

## Estructura actual

El proyecto separa la lógica matemática de la interfaz:

```text
Algebra-Lineal/
├── main.py                     # punto de entrada de la aplicación
├── manage.py                   # punto de entrada de Django
├── desktop.py                  # launcher Waitress + pywebview
├── AlgebraLineal.spec          # configuración reproducible de PyInstaller
├── pyproject.toml              # metadata y dependencias declaradas
├── uv.lock                     # versiones exactas resueltas por uv
├── .python-version             # versión de Python del proyecto
├── README.md
├── CONTRIBUTING.md
├── assets/                     # icono local de la aplicación
├── docs/
│   └── interfaz.md             # cómo reutilizar el sistema visual
├── .github/
│   └── workflows/
│       └── ci.yml              # integración continua
├── backend/
│   ├── matrices.py             # utilidades generales y validaciones
│   ├── operaciones_filas.py    # operaciones elementales y registro de pasos
│   ├── expresiones.py          # expresiones lineales exactas y su formato
│   ├── gauss.py                # escalonamiento hacia abajo
│   ├── gauss_jordan.py         # reducción completa y rango
│   ├── parser_sistemas.py      # texto de ecuaciones → matriz aumentada
│   └── sistemas.py             # clasificación, sistema resultante y solución
├── frontend/
│   ├── terminal/               # interfaz de línea de comandos
│   │   ├── menu.py             # bucle del menú y navegación
│   │   ├── opciones.py         # qué hace cada opción del menú
│   │   ├── entradas.py         # lectura y validación de datos del usuario
│   │   ├── salida.py           # formateo e impresión de matrices y pasos
│   │   └── consola.py          # colores, limpieza de pantalla y pausas
│   └── web/
│       ├── algebra_web/        # configuración, rutas y entradas WSGI/ASGI
│       └── calculadora/        # formulario, vistas, adaptador y recursos web
└── tests/
    ├── test_matrices.py
    ├── test_operaciones_filas.py
    ├── test_expresiones.py
    ├── test_gauss.py
    ├── test_gauss_jordan.py
    ├── test_parser_sistemas.py
    ├── test_sistemas.py
    ├── test_entradas.py
    ├── test_opciones.py
    ├── test_menu.py
    ├── test_salida.py
    ├── test_consola.py
    ├── test_web.py
    ├── test_desktop.py
    ├── test_recursos_interfaz.py
    └── test_restricciones_proyecto.py

La guía breve de la interfaz —plantilla base, header, tokens y tema— está en
[docs/interfaz.md](docs/interfaz.md).
```

Dentro de `backend/` la dependencia también va en un solo sentido, donde `→`
significa «depende de»:

```text
sistemas  →  gauss_jordan  →  gauss  →  operaciones_filas  →  matrices
sistemas  →  expresiones   →  matrices
```

Gauss-Jordan no repite el escalonamiento: llama a `aplicar_gauss` y solo añade la
eliminación hacia arriba, así que la diferencia entre los dos métodos está en un
único bloque de código.

`expresiones.py` representa a mano una expresión lineal como una constante más un
coeficiente por variable, y es lo que permite despejar sin manipular texto: primero
se calcula la expresión con `Fraction` y solo al final se escribe. `sistemas.py`
usa esa misma pieza para traducir matrices a ecuaciones y para construir el
conjunto solución, de modo que Gauss y Gauss-Jordan comparten la interpretación
entera.

`parser_sistemas.py` queda fuera de esa cadena porque no depende de ningún otro
módulo del proyecto: recibe texto y devuelve una matriz, o lanza `ValueError`. Eso
permitirá reutilizarlo tal cual desde otra interfaz.

`backend/` contiene lógica pura: no usa `input()` ni `print()` y no depende de
ninguna interfaz. `frontend/terminal/` es quien consume el backend y concentra
toda la interacción por consola. La dependencia va siempre en un sentido:

```text
frontend/terminal  →  backend
frontend/web        →  backend
```

Esa separación deja espacio para añadir más adelante otra interfaz bajo
`frontend/` sin tocar la lógica matemática.

La interfaz web sigue el mismo sentido de dependencia para ambos tipos de
entrada:

```text
texto ───────────────→ parser_sistemas.py ─┐
cuadrícula ──────────→ matriz aumentada ────┼→ servicios.py → sistemas.py
                                            └──────────────→ gauss / gauss-jordan
```

`forms.py` valida dimensiones y celdas con las utilidades existentes del parser;
`servicios.py` adapta matrices, pasos y mensajes para los templates, pero no
recalcula operaciones, clasificaciones ni soluciones. `matriz.js` solo genera la
cuadrícula y cambia su visibilidad. `tema.js` guarda el tema claro u oscuro en
el almacenamiento local del WebView.

La arquitectura completa de las interfaces queda así:

```text
frontend/terminal
        │
        └──────────────→ backend

frontend/web
        │
        └──────────────→ backend

desktop.py
        ↓
     Waitress (127.0.0.1:<puerto efímero>)
        ↓
     Django WSGI
        ↓
frontend/web
        ↓
     backend
```

El launcher es infraestructura de ejecución y no contiene parser, operaciones
de filas, Gauss, Gauss-Jordan ni interpretación matemática.

## Desarrollo

El flujo de ramas, las convenciones de commits y las reglas para contribuir están
en [CONTRIBUTING.md](CONTRIBUTING.md).
