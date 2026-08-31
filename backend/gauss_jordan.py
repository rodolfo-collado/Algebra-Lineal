"""Reduccion de matrices por Gauss-Jordan, registrando cada paso."""

from fractions import Fraction

from backend.matrices import (
    convertir_matriz_a_fracciones,
    copiar_matriz,
    es_matriz_rectangular,
    formatear_numero_operacion
)


def obtener_tipo_gauss_jordan(matriz):
    filas = len(matriz)
    columnas = len(matriz[0])

    if filas == columnas:
        return "cuadrada"

    if columnas == filas + 1:
        return "aumentada"

    return None


def validar_dimensiones_gauss_jordan(matriz):
    if not es_matriz_rectangular(matriz):
        return False, "Error: La matriz no es rectangular."

    tipo_matriz = obtener_tipo_gauss_jordan(matriz)
    if tipo_matriz is None:
        filas = len(matriz)
        columnas = len(matriz[0])
        return False, (
            f"Error: La matriz es de {filas}x{columnas}. "
            "Para Gauss-Jordan use matrices nxn o nx(n+1)."
        )

    return True, tipo_matriz


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


def texto_factor(factor):
    if factor < 0:
        return f"+ ({formatear_numero_operacion(-factor)})"

    return f"- ({formatear_numero_operacion(factor)})"


def aplicar_gauss_jordan(matriz):
    es_valida, mensaje = validar_dimensiones_gauss_jordan(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    matriz_reducida = convertir_matriz_a_fracciones(matriz)
    pasos = []
    filas = len(matriz_reducida)
    columnas = len(matriz_reducida[0])
    tipo_matriz = obtener_tipo_gauss_jordan(matriz_reducida)
    columnas_pivote = columnas - 1 if tipo_matriz == "aumentada" else columnas
    fila_pivote = 0
    pivotes = []

    for columna in range(columnas_pivote):
        if fila_pivote >= filas:
            break

        fila_encontrada = buscar_fila_pivote(matriz_reducida, fila_pivote, columna)
        if fila_encontrada is None:
            continue

        if fila_encontrada != fila_pivote:
            matriz_antes = copiar_matriz(matriz_reducida)
            matriz_reducida[fila_pivote], matriz_reducida[fila_encontrada] = (
                matriz_reducida[fila_encontrada],
                matriz_reducida[fila_pivote]
            )
            operacion = f"F{fila_pivote + 1} <-> F{fila_encontrada + 1}"
            registrar_paso(pasos, matriz_antes, operacion, matriz_reducida)

        pivote = matriz_reducida[fila_pivote][columna]
        if pivote != 1:
            matriz_antes = copiar_matriz(matriz_reducida)
            matriz_reducida[fila_pivote] = [
                numero / pivote for numero in matriz_reducida[fila_pivote]
            ]
            factor_pivote = formatear_numero_operacion(Fraction(1, 1) / pivote)
            operacion = f"F{fila_pivote + 1} = ({factor_pivote})F{fila_pivote + 1}"
            registrar_paso(pasos, matriz_antes, operacion, matriz_reducida)

        for fila in range(fila_pivote + 1, filas):
            factor = matriz_reducida[fila][columna]
            if factor == 0:
                continue

            matriz_antes = copiar_matriz(matriz_reducida)
            matriz_reducida[fila] = [
                matriz_reducida[fila][columna_actual]
                - factor * matriz_reducida[fila_pivote][columna_actual]
                for columna_actual in range(columnas)
            ]
            operacion = (
                f"F{fila + 1} = F{fila + 1} "
                f"{texto_factor(factor)}F{fila_pivote + 1}"
            )
            registrar_paso(pasos, matriz_antes, operacion, matriz_reducida)

        pivotes.append((fila_pivote, columna))
        fila_pivote += 1

    for fila_pivote, columna in reversed(pivotes):
        for fila in range(fila_pivote - 1, -1, -1):
            factor = matriz_reducida[fila][columna]
            if factor == 0:
                continue

            matriz_antes = copiar_matriz(matriz_reducida)
            matriz_reducida[fila] = [
                matriz_reducida[fila][columna_actual]
                - factor * matriz_reducida[fila_pivote][columna_actual]
                for columna_actual in range(columnas)
            ]
            operacion = (
                f"F{fila + 1} = F{fila + 1} "
                f"{texto_factor(factor)}F{fila_pivote + 1}"
            )
            registrar_paso(pasos, matriz_antes, operacion, matriz_reducida)

    return matriz_reducida, pasos, pivotes, tipo_matriz


def obtener_rango(matriz, columnas_limite):
    rango = 0

    for fila in matriz:
        for columna in range(columnas_limite):
            if fila[columna] != 0:
                rango += 1
                break

    return rango
