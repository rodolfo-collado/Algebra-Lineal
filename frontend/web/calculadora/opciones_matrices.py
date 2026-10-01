"""Opciones de las herramientas de matrices; los límites son de interfaz, no matemáticos."""

DIMENSION_MINIMA = 1
DIMENSION_MAXIMA = 10
DIMENSION_PREDETERMINADA = 2

# Cómo se explica cada producto AB o Ax de una expresión. Es solo presentación:
# el producto se calcula una vez y cada lectura agrupa los mismos productos aᵢₖbₖⱼ.
METODO_PREDETERMINADO = "fila_columna"
METODOS = (("fila_columna", "Fila por columna"), ("columnas", "Por columnas"), ("comparar", "Comparar ambos"))
# En Ax las mismas lecturas conservan sus nombres pedagógicos.
METODOS_MATRIZ_VECTOR = (
    ("fila_columna", "Regla fila-vector"), ("columnas", "Combinación lineal de columnas"), ("comparar", "Comparar ambos"),
)
METODOS_COMPARADOS = ("fila_columna", "columnas")
AYUDA_METODOS = (
    "Solo cambia la explicación: el resultado es el mismo. Fila por columna calcula cada entrada "
    "como una fila de la izquierda por una columna de la derecha; por columnas obtiene cada columna "
    "del producto como combinación lineal de las columnas de la izquierda. En una matriz por un vector "
    "son la regla fila-vector y la combinación lineal de columnas."
)
# Con más entradas en el resultado, los grupos del procedimiento nacen plegados.
ENTRADAS_DESPLEGADAS = 12


def metodos_a_mostrar(metodo):
    return METODOS_COMPARADOS if metodo == "comparar" else (metodo,)
