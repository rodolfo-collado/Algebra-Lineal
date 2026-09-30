# Matrices aumentadas por bloques

[Índice de documentación](README.md) · [Algoritmos](algoritmos.md)

P26.3 formaliza infraestructura para `[A | B]`. Si `A` es `m×n` y `B` es
`m×p`, su aumento es `m×(n+p)`: cada fila concatena las filas correspondientes
de ambos bloques. `[A | b]` tiene `p=1`; `[A | I]`, con `A` cuadrada de orden
`n`, tiene `p=n`.

## Auditoría del soporte previo

- Gauss ya admitía matrices rectangulares y `columnas_pivote`; Gauss-Jordan
  reutilizaba su escalonamiento y añadía eliminación hacia arriba.
- Las operaciones de fila ya afectaban todas las columnas, con valores exactos
  protegidos y registro completo de las matrices antes/después.
- `backend.matrices` ya validaba formas, dimensiones y valores; faltaban las
  primitivas explícitas de identidad, aumento y separación.
- Sistemas, su parser y servicios, y Resolver `Ax = b` interpretan la última
  columna como `b`. Conservan esa interpretación, clasificación y sustitución.
- `matrix.html` y `matriz.html` separaban únicamente la última columna.
  Ahora aceptan el corte explícito sin alterar el caso predeterminado.

Las regresiones comparan ambos motores, entradas, servicios y resultados de
Django contra el árbol original de `develop` tras el PR #60.

## API del backend

Las primitivas están en `backend.matrices` y no dependen de Django:

| Primitiva | Contrato |
| --- | --- |
| `matriz_identidad(orden)` | Devuelve `I_n` para un entero positivo `n`; cada fila es independiente. |
| `aumentar_matrices(izquierda, derecha)` | Devuelve `[A | B]`; exige matrices no vacías, rectangulares y con igual número de filas. Los anchos pueden diferir. |
| `separar_bloques(matriz, columnas_izquierda)` | Devuelve `(A, B)` mediante un corte entero `1 <= columnas_izquierda < columnas`; ambos bloques quedan no vacíos. |

Los bloques admiten enteros y `Fraction`; las salidas contienen `Fraction` en
listas nuevas, sin modificar ni compartir filas con la entrada. Se reutilizan
`dimensiones`, `validar_matriz` y `validar_matriz_exacta` para comprobar forma,
valores exactos y límite numérico antes de copiar. Se rechazan texto, flotantes
y booleanos. Una columna `b` es `[[b1], [b2], ...]`, que también se puede
construir con `vector_columna`.

## Contrato de reducción

```python
reducida, pasos, pivotes = aplicar_gauss_jordan(
    aumentar_matrices(a, b),
    columnas_pivote=columnas_de_a,
)
```

`columnas_pivote=n` limita los pivotes a las columnas `0` a `n-1` de `A`.
Se devuelven pares `(fila, columna)` de base cero. Una columna sin pivote se
salta sin avanzar la fila pivote; `B` no crea pivotes adicionales. Las
operaciones afectan la fila completa, incluido todo `B`: `[A | B]` pasa a
`[R | C]` con el mismo algoritmo que `[A | b]`. Cada paso conserva `antes`,
`operacion` y `despues` completos, sin modificar la matriz de entrada.

## Preparación de `[A | I]`

Este flujo es infraestructura reutilizable; P26.3 no añade una función pública
`inversa(A)` ni una herramienta web de Matriz inversa:

```python
from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import (
    aumentar_matrices,
    dimensiones,
    matriz_identidad,
    separar_bloques,
)

a = [[3, 4], [5, 6]]
filas, columnas = dimensiones(a)
if filas != columnas:
    raise ValueError("La preparación [A | I] requiere una matriz cuadrada.")

n = columnas
identidad = matriz_identidad(n)
aumentada = aumentar_matrices(a, identidad)
reducida, pasos, pivotes = aplicar_gauss_jordan(aumentada, columnas_pivote=n)
izquierda, derecha = separar_bloques(reducida, n)
izquierda_es_identidad = izquierda == identidad
rango_de_a = len(pivotes)
```

En el ejemplo, la izquierda es `I_2` y la derecha es
`[[-3, 2], [5/2, -3/2]]`, con fracciones exactas. Para `A` cuadrada, si
`len(pivotes) < n`, la izquierda no llegó a `I_n`; compararla exactamente con
la identidad aporta la misma evidencia. No se calculan determinantes. P26.4
compone exactamente este flujo en `backend/matriz_inversa.py`, interpreta el
bloque derecho y define el mensaje de una matriz sin inversa: consulta
[Matriz inversa](matriz-inversa.md).

## Presentación y procedimiento

`matrix.html` acepta `columnas_izquierda=n`; `matriz.html` dibuja el separador
antes de la columna `n+1` en una sola tabla, seguido de todas las columnas de
`B`. El resaltado de pivotes es independiente del corte. Los componentes de
procedimiento propagan `resultado.columnas_izquierda` o el contexto
`columnas_izquierda` a la matriz inicial, antes/después de cada operación y
matriz final. Sin corte explícito, Sistemas conserva la separación de su última
columna y el HTML predeterminado de `[A | b]` es idéntico al de la base.

## Presupuesto y seguridad numérica

P26.2 ya considera el ancho completo y las columnas admitidas para pivotes:

```python
estimacion = estimar_gauss_jordan(n, 2 * n, columnas_pivote=n)
```

Se estiman operaciones sobre `2*n` columnas y matrices completas antes/después,
con hasta `n` pivotes. Se conservan referencias de tiempo, categorías, umbrales
y confirmaciones, sin recalibración.

P26.2.1 protege numeradores y denominadores con `BITS_MAXIMOS` y, si es más
restrictivo, el límite de conversión a texto de Python. Las operaciones siguen
usando `dividir_exacto`, `multiplicar_exacto` y `restar_exacto`; el registro
valida ambas matrices. El crecimiento extremo conserva el mensaje controlado
«El cálculo produjo números demasiado grandes para mostrarlos de forma
segura», sin caminos alternativos de aritmética sin validar.

P26.4 reutiliza las primitivas, la reducción, los pivotes, el corte
presentacional y el presupuesto en el módulo de
[Matriz inversa](matriz-inversa.md).
