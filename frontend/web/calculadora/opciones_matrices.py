"""Configuración de la herramienta; los límites son de interfaz, no matemáticos."""

DIMENSION_MINIMA = 1
DIMENSION_MAXIMA = 10
DIMENSION_PREDETERMINADA = 2
OPERACION_PREDETERMINADA = "suma"

# Cómo ver el procedimiento de AB y Ax. Los identificadores se comparten: las
# etiquetas cambian con la operación, la matemática no.
METODO_PREDETERMINADO = "fila_columna"
METODOS_COMPARADOS = ("fila_columna", "columnas")
# Con más entradas en el resultado, los grupos del procedimiento nacen plegados.
ENTRADAS_DESPLEGADAS = 12

# Cada operación declara qué campos de estructura usa (con su etiqueta) y la
# forma de cada matriz de entrada como (campo de filas, campo de columnas);
# None en las columnas indica un vector columna, que se dibuja como matriz n×1.
DIMENSIONES_COMUNES = (("filas", "Filas"), ("columnas", "Columnas"))
FORMA_A = {"A": ("filas", "columnas")}

CONFIGURACION = {
    "suma": {
        "etiqueta": "Suma", "matrices": ("A", "B"), "escalar": False,
        "formas": {**FORMA_A, "B": ("filas", "columnas")}, "dimensiones": DIMENSIONES_COMUNES,
        "forma_texto": "{m}×{n} en cada matriz de entrada.", "metodos": (), "ayuda_metodos": "",
        "expresion": "A + B", "simbolo": "+", "formula": "cᵢⱼ = aᵢⱼ + bᵢⱼ",
        "ayuda": "Suma las entradas en la misma posición. A y B comparten filas y columnas.",
    },
    "resta": {
        "etiqueta": "Resta", "matrices": ("A", "B"), "escalar": False,
        "formas": {**FORMA_A, "B": ("filas", "columnas")}, "dimensiones": DIMENSIONES_COMUNES,
        "forma_texto": "{m}×{n} en cada matriz de entrada.", "metodos": (), "ayuda_metodos": "",
        "expresion": "A − B", "simbolo": "−", "formula": "cᵢⱼ = aᵢⱼ − bᵢⱼ",
        "ayuda": "Resta las entradas en la misma posición. A y B comparten filas y columnas.",
    },
    "escalar": {
        "etiqueta": "Multiplicación por escalar", "matrices": ("A",), "escalar": True,
        "formas": FORMA_A, "dimensiones": DIMENSIONES_COMUNES,
        "forma_texto": "{m}×{n} en cada matriz de entrada.", "metodos": (), "ayuda_metodos": "",
        "expresion": "k·A", "simbolo": "·", "formula": "(kA)ᵢⱼ = k · aᵢⱼ",
        "ayuda": "El escalar k multiplica cada entrada de A.",
    },
    "traspuesta": {
        "etiqueta": "Traspuesta", "matrices": ("A",), "escalar": False,
        "formas": FORMA_A, "dimensiones": DIMENSIONES_COMUNES,
        "forma_texto": "{m}×{n} en cada matriz de entrada.", "metodos": (), "ayuda_metodos": "",
        "expresion": "Aᵀ", "simbolo": "", "formula": "(Aᵀ)ᵢⱼ = Aⱼᵢ",
        "ayuda": "Las filas de A pasan a ser las columnas de Aᵀ.",
    },
    "producto": {
        "etiqueta": "Multiplicación de matrices", "matrices": ("A", "B"), "escalar": False,
        # Las filas de B son las columnas de A: la interfaz no permite un producto imposible.
        "formas": {**FORMA_A, "B": ("columnas", "columnas_b")},
        "dimensiones": (("filas", "Filas de A"), ("columnas", "Columnas de A = filas de B"), ("columnas_b", "Columnas de B")),
        "forma_texto": "A: {m}×{n} · B: {n}×{p} → AB: {m}×{p}.",
        "metodos": (("fila_columna", "Fila por columna"), ("columnas", "Por columnas"), ("comparar", "Comparar ambos")),
        "ayuda_metodos": (
            "Fila por columna calcula cada entrada cᵢⱼ como filaᵢ(A) · columnaⱼ(B). Por columnas obtiene cada "
            "columna Abⱼ como combinación lineal de las columnas de A. Comparar ambos muestra los dos procedimientos."
        ),
        "expresion": "AB", "simbolo": "·",
        "formula": "cᵢⱼ = filaᵢ(A) · columnaⱼ(B) = aᵢ₁b₁ⱼ + aᵢ₂b₂ⱼ + … + aᵢₙbₙⱼ",
        "ayuda": "AB existe solo si el número de columnas de A coincide con el número de filas de B: A (m×n) · B (n×p) da AB (m×p).",
    },
    "matriz_vector": {
        "etiqueta": "Matriz por vector (Ax)", "matrices": ("A", "x"), "escalar": False,
        "formas": {**FORMA_A, "x": ("columnas", None)},
        "dimensiones": (("filas", "Filas de A"), ("columnas", "Columnas de A = componentes de x")),
        "forma_texto": "A ({m}×{n}) · x ({n}) → Ax ({m}).",
        "metodos": (("fila_columna", "Regla fila-vector"), ("columnas", "Combinación lineal de columnas"), ("comparar", "Comparar ambos")),
        "ayuda_metodos": (
            "La regla fila-vector calcula cada entrada (Ax)ᵢ como filaᵢ(A) · x. La combinación lineal escribe "
            "Ax = x₁a₁ + … + xₙaₙ con las columnas de A. Comparar ambos muestra los dos procedimientos."
        ),
        "expresion": "Ax", "simbolo": "·",
        "formula": "(Ax)ᵢ = filaᵢ(A) · x = aᵢ₁x₁ + aᵢ₂x₂ + … + aᵢₙxₙ",
        "ayuda": "x es un vector columna con tantas componentes como columnas tiene A: A (m×n) · x (n) da Ax (m).",
    },
}
OPERACIONES = tuple((clave, opcion["etiqueta"]) for clave, opcion in CONFIGURACION.items())
CAMPOS_DIMENSION = ("filas", "columnas", "columnas_b")


def es_vector(opcion, nombre):
    """Una entrada sin campo de columnas es un vector columna."""
    return opcion["formas"][nombre][1] is None


def metodos_a_mostrar(metodo):
    return METODOS_COMPARADOS if metodo == "comparar" else (metodo,)
