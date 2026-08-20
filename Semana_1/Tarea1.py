# ===== TAREA 1: DIFERENCIAS ENTRE ARRAYS Y MATRICES =====

# -> Indicaciones

# - Clasifique dos sistemas
# - Explique lo que es un array vs una matriz
# - Interprete A[1,2] en una matriz de 2x3

lista = [ 1, 3, 5]
matriz = [[1, 2, 3],[4, 5, 6]]

print(f"""
----> ARRAY:
Estructura de datos que almacena elementos de forma ordenada y puede tener una o más dimensiones.

Ejemplo: 

{lista}

----> MATRIZ:
Estructura bidimensional organizada en filas y columnas. En Python puro puede representarse mediante una lista de listas.

Ejemplo:
""")

for i in matriz:
    print(*i)

print("\n En la matriz anterior, la posición A[1,2] corresponde al número 2. Porque está en la fila 1 y la columna 2.")

