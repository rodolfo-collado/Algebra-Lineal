# Álgebra Lineal

Proyecto educativo en Python para implementar manualmente algoritmos de matrices
y álgebra lineal. El objetivo no es resolver operaciones rápido, sino escribir el
algoritmo paso a paso y entender cómo funciona por dentro.

La aplicación se usa desde la terminal, mediante un menú interactivo.

## Funcionalidades actuales

- Generar una matriz con valores aleatorios a partir de sus dimensiones.
- Crear una matriz ingresando cada elemento manualmente.
- Crear un sistema de ecuaciones, escribiéndolo directamente como texto o
  ingresando sus coeficientes uno por uno.
- Modificar un elemento en una posición dada.
- Consultar un elemento en una posición dada.
- Mostrar la matriz completa con las columnas alineadas.
- Resolver el sistema por **Gauss**, mostrando la eliminación hacia abajo, la
  matriz escalonada, la sustitución regresiva y las soluciones.
- Resolver el sistema por **Gauss-Jordan**, mostrando la reducción completa, la
  matriz reducida y las soluciones.

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

- **Gauss** solo elimina hacia abajo. Deja la matriz escalonada y, cuando la
  solución es única, despeja las variables de abajo hacia arriba mediante
  sustitución regresiva.
- **Gauss-Jordan** continúa eliminando hacia arriba hasta la forma reducida, y
  las soluciones se leen directamente de la última columna.

Para el mismo sistema los dos llegan a la misma clasificación y, cuando hay
solución única, a las mismas soluciones.

La clasificación del sistema es una de estas tres:

```text
Consistente de solución única
Consistente de soluciones infinitas
Inconsistente
```

Cuando hay infinitas soluciones o el sistema es inconsistente no se ejecuta la
sustitución regresiva: no se inventan valores para las variables libres.

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
- Una única dependencia externa, `colorama`, usada solo para dar color a la
  terminal. Los cálculos y la interpretación de los sistemas siguen apoyándose
  únicamente en la biblioteca estándar (`random`, `fractions` y `re`).

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

```bash
uv run python main.py
```

Para salir, elige la opción `9` del menú.

## Pruebas

Desde la raíz del repositorio:

```bash
uv run python -m unittest discover -v
```

Actualmente son 269 pruebas. Las de `tests/` cubren las reglas matemáticas del
backend (validaciones, matrices rectangulares, pivotes, escalonamiento,
sustitución regresiva y clasificación de sistemas), el parser de sistemas, la
equivalencia entre Gauss y Gauss-Jordan, el flujo de la terminal y las
restricciones académicas del proyecto. Sirven para detectar regresiones cuando el
proyecto crezca.

Para comprobar que todo el código compila:

```bash
uv run python -m compileall -q backend frontend tests main.py
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
├── pyproject.toml              # metadata y dependencias declaradas
├── uv.lock                     # versiones exactas resueltas por uv
├── .python-version             # versión de Python del proyecto
├── README.md
├── CONTRIBUTING.md
├── .github/
│   └── workflows/
│       └── ci.yml              # integración continua
├── backend/
│   ├── matrices.py             # utilidades generales y validaciones
│   ├── operaciones_filas.py    # operaciones elementales y registro de pasos
│   ├── gauss.py                # escalonamiento hacia abajo
│   ├── gauss_jordan.py         # reducción completa y rango
│   ├── parser_sistemas.py      # texto de ecuaciones → matriz aumentada
│   └── sistemas.py             # matriz aumentada, clasificación y soluciones
├── frontend/
│   └── terminal/
│       ├── menu.py             # bucle del menú y navegación
│       ├── opciones.py         # qué hace cada opción del menú
│       ├── entradas.py         # lectura y validación de datos del usuario
│       ├── salida.py           # formateo e impresión de matrices y pasos
│       └── consola.py          # colores, limpieza de pantalla y pausas
└── tests/
    ├── test_matrices.py
    ├── test_operaciones_filas.py
    ├── test_gauss.py
    ├── test_gauss_jordan.py
    ├── test_parser_sistemas.py
    ├── test_sistemas.py
    ├── test_entradas.py
    ├── test_opciones.py
    ├── test_menu.py
    ├── test_salida.py
    ├── test_consola.py
    └── test_restricciones_proyecto.py
```

Dentro de `backend/` la dependencia también va en un solo sentido, donde `→`
significa «depende de»:

```text
sistemas  →  gauss_jordan  →  gauss  →  operaciones_filas  →  matrices
```

Gauss-Jordan no repite el escalonamiento: llama a `aplicar_gauss` y solo añade la
eliminación hacia arriba, así que la diferencia entre los dos métodos está en un
único bloque de código.

`parser_sistemas.py` queda fuera de esa cadena porque no depende de ningún otro
módulo del proyecto: recibe texto y devuelve una matriz, o lanza `ValueError`. Eso
permitirá reutilizarlo tal cual desde otra interfaz.

`backend/` contiene lógica pura: no usa `input()` ni `print()` y no depende de
ninguna interfaz. `frontend/terminal/` es quien consume el backend y concentra
toda la interacción por consola. La dependencia va siempre en un sentido:

```text
frontend  →  backend
```

Esa separación deja espacio para añadir más adelante otra interfaz bajo
`frontend/` sin tocar la lógica matemática.

## Desarrollo

El flujo de ramas, las convenciones de commits y las reglas para contribuir están
en [CONTRIBUTING.md](CONTRIBUTING.md).
