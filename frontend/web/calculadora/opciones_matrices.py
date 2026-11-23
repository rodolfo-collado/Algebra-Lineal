"""Opciones de las herramientas de matrices; los límites son de interfaz, no matemáticos."""

from backend.operandos import OPERANDOS_MAXIMOS

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


# Ejemplos de Operaciones: cada uno carga sus operandos y su expresión (GET ?plantilla=…),
# también sin JavaScript. Son datos de partida editables, no operaciones aparte.
# (id, rótulo, expresión, operandos como (nombre, tipo, valores)); un vector es una lista.
PLANTILLAS = (
    ("suma-vectores", "u + v", "u + v", (("u", "vector", [1, 2, 3]), ("v", "vector", [4, -1, 0]))),
    ("escalar-vector", "2u − 3v", "2u - 3v", (("u", "vector", [1, 2, 3]), ("v", "vector", [4, -1, 0]))),
    ("combinacion-lineal", "Coeficientes: x1 u + x2 v = b", "x1 u + x2 v = b",
     (("u", "vector", [1, 2]), ("v", "vector", [3, 1]), ("b", "vector", [5, 5]))),
    ("producto", "AB", "AB", (("A", "matriz", [[1, 2], [3, 4]]), ("B", "matriz", [[0, 1], [1, 0]]))),
    ("matriz-vector", "Ax", "Ax", (("A", "matriz", [[1, 2], [3, 4]]), ("x", "vector", [1, -1]))),
    ("propiedad-traspuesta", "(AB)ᵀ = BᵀAᵀ", "(AB)ᵀ = BᵀAᵀ",
     (("A", "matriz", [[1, 2, 0], [3, 4, 1]]), ("B", "matriz", [[1, 0], [2, 1], [0, 5]]))),
)
# La antigua Operaciones con vectores abre el ejemplo equivalente a su operación.
PLANTILLA_DE_OPERACION_VECTORIAL = {
    "suma": "suma-vectores", "resta": "suma-vectores", "escalar": "escalar-vector", "combinacion": "combinacion-lineal",
}


def estado_plantilla(identificador):
    """El estado plano del formulario (como el de Aplicar) para un ejemplo; None si no existe."""
    plantilla = next((p for p in PLANTILLAS if p[0] == identificador), None)
    if plantilla is None:
        return None
    _, _, expresion, operandos = plantilla
    plano = {"expresion": expresion, "cantidad": len(operandos), "metodo": METODO_PREDETERMINADO}
    for indice, (nombre, tipo, valores) in enumerate(operandos):
        filas = valores if tipo == "matriz" else [[valor] for valor in valores]
        plano.update({f"nombre_{indice}": nombre, f"tipo_{indice}": tipo, f"filas_{indice}": len(filas)})
        if tipo == "matriz":
            plano[f"columnas_{indice}"] = len(filas[0])
        for i, fila in enumerate(filas):
            for j, valor in enumerate(fila):
                plano[f"celda_{indice}_{i}_{j}"] = str(valor)
    return plano


def datos_operacion_vectorial(post):
    """Traduce el POST de la antigua Operaciones con vectores al formulario de Operaciones.

    v1 … vk (y b, k) pasan a ser operandos con los mismos nombres y la operación, la
    expresión equivalente: v1 + v2, v1 - v2, k v1 o x1 v1 + x2 v2 = b. Las celdas viajan tal
    cual: el formulario de Operaciones las valida con sus propios mensajes.
    """
    operacion = post.get("operacion", "suma")
    try:
        dimension = int(post.get("dimension", 0))
        cantidad = 1 if operacion == "escalar" else int(post.get("vectores") or 2)
    except (TypeError, ValueError):
        dimension = cantidad = 0
    # Un número absurdo no construye miles de campos: uno más que el tope basta para que se rechace.
    dimension = min(dimension, DIMENSION_MAXIMA + 1)
    cantidad = min(cantidad, OPERANDOS_MAXIMOS + 1)
    vectores = [f"v{i}" for i in range(1, max(cantidad, 0) + 1)]
    if operacion == "combinacion":
        expresion = " + ".join(f"x{i} {v}" for i, v in enumerate(vectores, 1)) + " = b"
        if len(expresion) > 400:  # Con decenas de generadores, sin espacios cabe en el campo: x1v1+x2v2+… = b.
            expresion = "+".join(f"x{i}{v}" for i, v in enumerate(vectores, 1)) + " = b"
        vectores.append("b")
    elif operacion == "escalar":
        expresion = "k v1"
    else:
        expresion = (" - " if operacion == "resta" else " + ").join(vectores)
    datos = {"expresion": expresion, "metodo": METODO_PREDETERMINADO}
    operandos = [("k", "escalar")] if operacion == "escalar" else []
    operandos += [(nombre, "vector") for nombre in vectores]
    datos["cantidad"] = str(len(operandos))
    for indice, (nombre, tipo) in enumerate(operandos):
        datos[f"nombre_{indice}"], datos[f"tipo_{indice}"] = nombre, tipo
        if tipo == "escalar":
            datos[f"celda_{indice}_0_0"] = post.get("escalar", "")
            continue
        datos[f"filas_{indice}"] = str(dimension)
        for componente in range(max(dimension, 0)):
            datos[f"celda_{indice}_{componente}_0"] = post.get(f"{nombre}_{componente}", "")
    for clave in ("csrfmiddlewaretoken", "ajustar"):
        if clave in post:
            datos[clave] = post[clave]
    return datos
