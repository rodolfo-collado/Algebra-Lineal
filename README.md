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
- Resolver por Gauss-Jordan matrices cuadradas (`n x n`) o aumentadas (`n x (n+1)`),
  mostrando los pasos realizados, la matriz reducida y un análisis del resultado.

El análisis distingue entre sistema compatible determinado, compatible
indeterminado e incompatible; para matrices cuadradas indica si son invertibles o
singulares. Los cálculos usan `fractions.Fraction`, así que los resultados son
exactos y se muestran como fracciones cuando no son enteros.

## Requisitos

- Python 3.10 o superior. El menú usa `match` / `case`, disponible desde esa versión.
- Sin dependencias externas: el proyecto solo utiliza la biblioteca estándar
  (`random` y `fractions`). Por eso no hay `requirements.txt`.

## Ejecución

Desde la raíz del repositorio:

```bash
python main.py
```

En Windows también funciona:

```bash
py -3 main.py
```

Para salir, elige la opción `7` del menú.

## Pruebas

Desde la raíz del repositorio:

```bash
python -m unittest discover -v
```

Las pruebas de `tests/` caracterizan el comportamiento actual del backend
matemático y del formateo de salida. Sirven para detectar regresiones cuando el
proyecto se reorganice.

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

## Estructura actual

El proyecto separa la lógica matemática de la interfaz:

```text
Algebra-Lineal/
├── main.py                     # punto de entrada de la aplicación
├── README.md
├── CONTRIBUTING.md
├── backend/
│   └── logica_matrices.py      # Gauss-Jordan, validaciones y análisis
├── frontend/
│   └── terminal/
│       ├── menu.py             # bucle del menú y acciones de cada opción
│       ├── entradas.py         # lectura y validación de datos del usuario
│       └── salida.py           # formateo e impresión de matrices y pasos
└── tests/
    ├── test_logica_matrices.py
    └── test_salida.py
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
