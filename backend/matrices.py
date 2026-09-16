"""Utilidades generales sobre matrices, independientes de cualquier algoritmo."""

import random
from fractions import Fraction


def generar_matriz(cantidad_filas, cantidad_columnas):
    matriz = []

    # Ciclo para generar la matriz
    for _ in range(cantidad_filas):
        fila = []
        for _ in range(cantidad_columnas):
            fila.append(random.randint(0, 20))
        matriz.append(fila)

    return matriz


def copiar_matriz(matriz):
    copia = []

    for fila in matriz:
        copia.append(fila.copy())

    return copia


def convertir_matriz_a_fracciones(matriz):
    matriz_fracciones = []

    for fila in matriz:
        nueva_fila = []
        for numero in fila:
            nueva_fila.append(Fraction(numero))
        matriz_fracciones.append(nueva_fila)

    return matriz_fracciones


def es_matriz_rectangular(matriz):
    # Una matriz sin filas no tiene forma que comprobar.
    if not isinstance(matriz, (list, tuple)) or not matriz:
        return False
    if any(not isinstance(fila, (list, tuple)) for fila in matriz):
        return False

    cantidad_columnas = len(matriz[0])
    for fila in matriz:
        if len(fila) != cantidad_columnas:
            return False

    return True


def validar_matriz_rectangular(matriz):
    """Devuelve (es_valida, mensaje). Acepta cualquier matriz rectangular no vacia."""
    if not matriz:
        return False, "Error: La matriz está vacía."

    if not es_matriz_rectangular(matriz):
        return False, "Error: La matriz no es rectangular."

    if len(matriz[0]) == 0:
        return False, "Error: La matriz no tiene columnas."

    return True, ""


def formatear_fraccion(numero):
    if numero.denominator == 1:
        return str(numero.numerator)
    return f"{numero.numerator}/{numero.denominator}"


def validar_matriz(matriz):
    """Forma rectangular no vacía y entradas exactas; sin límites de interfaz."""
    valida, mensaje = validar_matriz_rectangular(matriz)
    if not valida:
        return valida, mensaje
    for fila in matriz:
        for valor in fila:
            if isinstance(valor, bool) or not isinstance(valor, (int, Fraction)):
                return False, "Cada entrada de la matriz debe ser un número exacto."
    return True, ""


def _exigir_matriz(matriz):
    valida, mensaje = validar_matriz(matriz)
    if not valida:
        raise ValueError(mensaje)


def dimensiones(matriz):
    """Dimensiones (filas, columnas) de una matriz válida."""
    _exigir_matriz(matriz)
    return len(matriz), len(matriz[0])


def _operar_entradas(a, b, signo):
    forma_a, forma_b = dimensiones(a), dimensiones(b)
    if forma_a != forma_b:
        raise ValueError(
            "Para sumar o restar, ambas matrices deben tener las mismas dimensiones: "
            f"A es {forma_a[0]}×{forma_a[1]} y B es {forma_b[0]}×{forma_b[1]}."
        )
    return [
        [Fraction(x) + signo * Fraction(y) for x, y in zip(fila_a, fila_b)]
        for fila_a, fila_b in zip(a, b)
    ]


def sumar_matrices(a, b):
    """C[i][j] = A[i][j] + B[i][j], con dimensiones iguales, incluso rectangulares."""
    return _operar_entradas(a, b, 1)


def restar_matrices(a, b):
    """C[i][j] = A[i][j] - B[i][j], sin modificar las entradas."""
    return _operar_entradas(a, b, -1)


def multiplicar_escalar_matriz(escalar, matriz):
    """Multiplica cada entrada por un entero o Fraction."""
    _exigir_matriz(matriz)
    if isinstance(escalar, bool) or not isinstance(escalar, (int, Fraction)):
        raise ValueError("El escalar debe ser un número exacto.")
    return [[Fraction(escalar) * Fraction(valor) for valor in fila] for fila in matriz]


def trasponer_matriz(matriz):
    """Intercambia filas y columnas: una matriz m×n produce una matriz n×m."""
    filas, columnas = dimensiones(matriz)
    return [[Fraction(matriz[i][j]) for i in range(filas)] for j in range(columnas)]


def resolver_operacion_matrices(operacion, a, b=None, escalar=None):
    """Resultado y evidencia por entrada, como datos exactos sin presentación.

    Los índices de los pasos empiezan en 1. En la traspuesta se conserva la
    posición de origen para explicar cómo cada fila pasa a ser una columna.
    """
    if operacion == "suma":
        resultado = sumar_matrices(a, b)
    elif operacion == "resta":
        resultado = restar_matrices(a, b)
    elif operacion == "escalar":
        resultado = multiplicar_escalar_matriz(escalar, a)
    elif operacion == "traspuesta":
        resultado = trasponer_matriz(a)
    else:
        raise ValueError("Selecciona una operación de matrices válida.")

    pasos = []
    for i, fila in enumerate(resultado):
        pasos_fila = []
        for j, valor in enumerate(fila):
            origen = (j + 1, i + 1) if operacion == "traspuesta" else (i + 1, j + 1)
            if operacion in ("suma", "resta"):
                operandos = (Fraction(a[i][j]), Fraction(b[i][j]))
            elif operacion == "escalar":
                operandos = (Fraction(escalar), Fraction(a[i][j]))
            else:
                operandos = (Fraction(a[j][i]),)
            pasos_fila.append({
                "posicion": (i + 1, j + 1), "origen": origen,
                "operandos": operandos, "resultado": valor,
            })
        pasos.append(pasos_fila)
    return {
        "operacion": operacion, "resultado": resultado, "pasos": pasos,
        "dimensiones_entrada": dimensiones(a),
        "dimensiones_resultado": dimensiones(resultado),
    }
