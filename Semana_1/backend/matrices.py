import random
from fractions import Fraction


def generar_matriz(filas, columnas):
    return [
        [random.randint(0, 20) for _ in range(columnas)]
        for _ in range(filas)
    ]


def copiar_matriz(matriz):
    return [fila.copy() for fila in matriz]


def es_matriz_rectangular(matriz):
    if not matriz or not matriz[0]:
        return False

    cantidad_columnas = len(matriz[0])
    return all(len(fila) == cantidad_columnas for fila in matriz)


def validar_matriz(matriz):
    if not matriz:
        return False, "Error: La matriz no puede estar vacía."

    if not es_matriz_rectangular(matriz):
        return False, "Error: La matriz debe ser rectangular."

    return True, ""


def validar_dimensiones_gauss_jordan(matriz):
    """Conserva el nombre existente y valida solo la estructura."""
    return validar_matriz(matriz)


def convertir_matriz_a_fracciones(matriz):
    return [
        [Fraction(numero) for numero in fila]
        for fila in matriz
    ]


def buscar_fila_pivote(matriz, fila_inicio, columna):
    for fila in range(fila_inicio, len(matriz)):
        if matriz[fila][columna] != 0:
            return fila

    return None


def registrar_paso(pasos, matriz_antes, operacion, matriz_despues):
    pasos.append({
        "antes": copiar_matriz(matriz_antes),
        "operacion": operacion,
        "despues": copiar_matriz(matriz_despues)
    })


def formatear_numero_operacion(numero):
    numero = Fraction(numero)
    if numero.denominator == 1:
        return str(numero.numerator)

    return f"{numero.numerator}/{numero.denominator}"


def texto_factor(factor):
    if factor < 0:
        return f"+ ({formatear_numero_operacion(-factor)})"

    return f"- ({formatear_numero_operacion(factor)})"


def aplicar_gauss(matriz):
    """Devuelve la forma escalonada, los pasos y los pivotes.

    La última columna siempre es el término independiente y no se usa como
    columna de pivote. Las columnas anteriores representan x1, x2, etc.
    """
    es_valida, mensaje = validar_matriz(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    matriz_escalonada = convertir_matriz_a_fracciones(matriz)
    pasos = []
    cantidad_filas = len(matriz_escalonada)
    cantidad_columnas = len(matriz_escalonada[0])
    limite_columnas_pivote = cantidad_columnas - 1
    fila_pivote = 0
    pivotes = []

    for columna in range(limite_columnas_pivote):
        if fila_pivote >= cantidad_filas:
            break

        fila_encontrada = buscar_fila_pivote(
            matriz_escalonada,
            fila_pivote,
            columna
        )
        if fila_encontrada is None:
            continue

        if fila_encontrada != fila_pivote:
            matriz_antes = copiar_matriz(matriz_escalonada)
            matriz_escalonada[fila_pivote], matriz_escalonada[fila_encontrada] = (
                matriz_escalonada[fila_encontrada],
                matriz_escalonada[fila_pivote]
            )
            registrar_paso(
                pasos,
                matriz_antes,
                f"F{fila_pivote + 1} <-> F{fila_encontrada + 1}",
                matriz_escalonada
            )

        pivote = matriz_escalonada[fila_pivote][columna]
        if pivote != 1:
            matriz_antes = copiar_matriz(matriz_escalonada)
            matriz_escalonada[fila_pivote] = [
                numero / pivote
                for numero in matriz_escalonada[fila_pivote]
            ]
            factor_pivote = formatear_numero_operacion(Fraction(1, 1) / pivote)
            registrar_paso(
                pasos,
                matriz_antes,
                f"F{fila_pivote + 1} = ({factor_pivote})F{fila_pivote + 1}",
                matriz_escalonada
            )

        for fila in range(fila_pivote + 1, cantidad_filas):
            factor = matriz_escalonada[fila][columna]
            if factor == 0:
                continue

            matriz_antes = copiar_matriz(matriz_escalonada)
            matriz_escalonada[fila] = [
                matriz_escalonada[fila][columna_actual]
                - factor * matriz_escalonada[fila_pivote][columna_actual]
                for columna_actual in range(cantidad_columnas)
            ]
            operacion = (
                f"F{fila + 1} = F{fila + 1} "
                f"{texto_factor(factor)}F{fila_pivote + 1}"
            )
            registrar_paso(
                pasos,
                matriz_antes,
                operacion,
                matriz_escalonada
            )

        pivotes.append((fila_pivote, columna))
        fila_pivote += 1

    return matriz_escalonada, pasos, pivotes


def aplicar_gauss_jordan(matriz):
    """Reutiliza Gauss y solo agrega la eliminación sobre los pivotes."""
    matriz_reducida, pasos, pivotes = aplicar_gauss(matriz)
    cantidad_columnas = len(matriz_reducida[0])

    for fila_pivote, columna in reversed(pivotes):
        for fila in range(fila_pivote - 1, -1, -1):
            factor = matriz_reducida[fila][columna]
            if factor == 0:
                continue

            matriz_antes = copiar_matriz(matriz_reducida)
            matriz_reducida[fila] = [
                matriz_reducida[fila][columna_actual]
                - factor * matriz_reducida[fila_pivote][columna_actual]
                for columna_actual in range(cantidad_columnas)
            ]
            operacion = (
                f"F{fila + 1} = F{fila + 1} "
                f"{texto_factor(factor)}F{fila_pivote + 1}"
            )
            registrar_paso(
                pasos,
                matriz_antes,
                operacion,
                matriz_reducida
            )

    return matriz_reducida, pasos, pivotes


def obtener_rango(matriz, columnas_limite=None):
    es_valida, mensaje = validar_matriz(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    matriz_trabajo = convertir_matriz_a_fracciones(matriz)
    cantidad_filas = len(matriz_trabajo)
    cantidad_columnas = len(matriz_trabajo[0])

    if columnas_limite is None:
        columnas_limite = cantidad_columnas
    if columnas_limite < 0 or columnas_limite > cantidad_columnas:
        raise ValueError("El límite de columnas no es válido.")

    fila_pivote = 0
    rango = 0
    for columna in range(columnas_limite):
        if fila_pivote >= cantidad_filas:
            break

        fila_encontrada = buscar_fila_pivote(
            matriz_trabajo,
            fila_pivote,
            columna
        )
        if fila_encontrada is None:
            continue

        matriz_trabajo[fila_pivote], matriz_trabajo[fila_encontrada] = (
            matriz_trabajo[fila_encontrada], matriz_trabajo[fila_pivote]
        )
        pivote = matriz_trabajo[fila_pivote][columna]

        for fila in range(fila_pivote + 1, cantidad_filas):
            factor = matriz_trabajo[fila][columna] / pivote
            if factor == 0:
                continue

            matriz_trabajo[fila] = [
                matriz_trabajo[fila][columna_actual]
                - factor * matriz_trabajo[fila_pivote][columna_actual]
                for columna_actual in range(cantidad_columnas)
            ]

        rango += 1
        fila_pivote += 1

    return rango
