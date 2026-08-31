# Álgebra Lineal

Proyecto educativo en Python para implementar manualmente algoritmos de matrices
y álgebra lineal. El objetivo no es resolver operaciones rápido, sino escribir el
algoritmo paso a paso y entender cómo funciona por dentro.

La aplicación se usa desde la terminal, mediante un menú interactivo.

## Funcionalidades actuales

- Generar una matriz con valores aleatorios a partir de sus dimensiones.
- Crear una matriz ingresando cada elemento manualmente.
- Modificar un elemento en una posición dada.
- Consultar un elemento en una posición dada.
- Mostrar la matriz completa con las columnas alineadas.
- Reducir por Gauss-Jordan cualquier matriz rectangular, mostrando los pasos
  realizados y la matriz reducida.
- Resolver la matriz como sistema de ecuaciones, mostrando los pasos, la matriz
  reducida y la clasificación del sistema.

Reducir una matriz y resolver un sistema son dos operaciones distintas, y el menú
las separa. Gauss-Jordan no exige matrices cuadradas ni de la forma `n x (n+1)`:
funciona con cualquier matriz rectangular (`2 x 3`, `3 x 2`, `4 x 3`, etc.), y no
todas las columnas ni todas las filas tienen que terminar con un pivote.

Una matriz solo se interpreta como sistema de ecuaciones cuando se elige esa
opción del menú. En ese caso la **última columna** se toma explícitamente como los
términos independientes; el significado nunca se deduce de las dimensiones. Por
eso una matriz `3 x 3` puede ser una matriz cualquiera o el sistema de 3
ecuaciones y 2 variables, según la opción que se use.

La clasificación del sistema es una de estas tres:

```text
Consistente de solución única
Consistente de soluciones infinitas
Inconsistente
```

Los cálculos usan `fractions.Fraction`, así que los resultados son exactos y se
muestran como fracciones cuando no son enteros.

La interfaz de terminal usa colores, limpia la pantalla entre secciones y espera
una confirmación antes de volver al menú, para que los resultados se puedan leer
con calma.

## Requisitos

- [uv](https://docs.astral.sh/uv/) instalado. Consulta su documentación oficial
  para instalarlo en tu sistema.
- Python 3.13. La versión está fijada en `.python-version`, y `uv` la descarga por
  ti si todavía no la tienes.
- Una única dependencia externa, `colorama`, usada solo para dar color a la
  terminal. Los cálculos siguen apoyándose únicamente en la biblioteca estándar
  (`random` y `fractions`).

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

Para salir, elige la opción `8` del menú.

## Pruebas

Desde la raíz del repositorio:

```bash
uv run python -m unittest discover -v
```

Actualmente son 93 pruebas. Las de `tests/` cubren las reglas matemáticas del
backend (validaciones, matrices rectangulares, pivotes y clasificación de
sistemas), el formateo de salida y las restricciones académicas del proyecto.
Sirven para detectar regresiones cuando el proyecto crezca.

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
│   ├── gauss_jordan.py         # reducción paso a paso y rango
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
    ├── test_gauss_jordan.py
    ├── test_sistemas.py
    ├── test_salida.py
    ├── test_consola.py
    └── test_restricciones_proyecto.py
```

Dentro de `backend/` la dependencia también va en un solo sentido:

```text
sistemas  →  gauss_jordan  →  matrices
```

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
