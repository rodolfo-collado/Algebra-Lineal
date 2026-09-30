"""Operaciones elementales de fila y registro de pasos.

Son las piezas que comparten Gauss y Gauss-Jordan: ninguna decide por si sola
hasta donde llega la reduccion.
"""

from fractions import Fraction

from backend.matrices import copiar_matriz, formatear_fraccion
from backend.seguridad_numerica import (
    dividir_exacto, multiplicar_exacto, restar_exacto, validar_matriz_exacta,
)


def buscar_fila_pivote(matriz, fila_inicio, columna):
    # Búsqueda del pivote: primera fila con un valor distinto de cero
    for fila in range(fila_inicio, len(matriz)):
        if matriz[fila][columna] != 0:
            return fila

    return None


def registrar_paso(pasos, matriz_antes, operacion, matriz_despues):
    validar_matriz_exacta(matriz_antes)
    validar_matriz_exacta(matriz_despues)
    pasos.append({
        "antes": copiar_matriz(matriz_antes),
        "operacion": operacion,
        "despues": copiar_matriz(matriz_despues)
    })


def texto_factor(factor):
    if factor < 0:
        return f"+ ({formatear_fraccion(-factor)})"

    return f"- ({formatear_fraccion(factor)})"


def intercambiar_filas(matriz, pasos, fila_a, fila_b):
    validar_matriz_exacta(matriz)
    matriz_antes = copiar_matriz(matriz)
    matriz[fila_a], matriz[fila_b] = matriz[fila_b], matriz[fila_a]

    # Registro del paso
    operacion = f"F{fila_a + 1} <-> F{fila_b + 1}"
    registrar_paso(pasos, matriz_antes, operacion, matriz)


def normalizar_fila(matriz, pasos, fila, pivote):
    validar_matriz_exacta(matriz)
    matriz_antes = copiar_matriz(matriz)
    matriz[fila] = [dividir_exacto(numero, pivote) for numero in matriz[fila]]

    # Registro del paso
    factor = formatear_fraccion(dividir_exacto(Fraction(1, 1), pivote))
    operacion = f"F{fila + 1} = ({factor})F{fila + 1}"
    registrar_paso(pasos, matriz_antes, operacion, matriz)


def eliminar_en_columna(matriz, pasos, fila_pivote, columna, filas_objetivo):
    """Hace cero la columna operando toda la fila, incluidos bloques aumentados."""
    validar_matriz_exacta(matriz)
    for fila in filas_objetivo:
        factor = matriz[fila][columna]
        if factor == 0:
            continue

        matriz_antes = copiar_matriz(matriz)
        matriz[fila] = [
            restar_exacto(
                matriz[fila][indice], multiplicar_exacto(factor, matriz[fila_pivote][indice])
            )
            for indice in range(len(matriz[fila]))
        ]

        # Registro del paso
        operacion = (
            f"F{fila + 1} = F{fila + 1} "
            f"{texto_factor(factor)}F{fila_pivote + 1}"
        )
        registrar_paso(pasos, matriz_antes, operacion, matriz)
