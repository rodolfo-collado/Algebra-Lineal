"""Operaciones elementales de fila y registro de pasos.

Son las piezas que comparten Gauss, Gauss-Jordan y LU: ninguna decide por si
sola hasta donde llega la reduccion. Los intercambios y normalizaciones anotan
en su paso `correccion_determinante`, el factor que recupera det(A).
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
    # Intercambiar dos filas cambia el signo del determinante.
    pasos[-1]["correccion_determinante"] = -1


def normalizar_fila(matriz, pasos, fila, pivote):
    validar_matriz_exacta(matriz)
    matriz_antes = copiar_matriz(matriz)
    matriz[fila] = [dividir_exacto(numero, pivote) for numero in matriz[fila]]

    # Registro del paso
    factor = formatear_fraccion(dividir_exacto(Fraction(1, 1), pivote))
    operacion = f"F{fila + 1} = ({factor})F{fila + 1}"
    registrar_paso(pasos, matriz_antes, operacion, matriz)
    # Dividir la fila entre el pivote divide det(A); multiplicar por él lo recupera.
    pasos[-1]["correccion_determinante"] = pivote


def eliminar_en_columna(matriz, pasos, fila_pivote, columna, filas_objetivo):
    """Hace cero la columna operando toda la fila, incluidos bloques aumentados."""
    validar_matriz_exacta(matriz)
    for fila in filas_objetivo:
        factor = matriz[fila][columna]
        if factor == 0:
            continue

        reemplazar_fila(matriz, pasos, fila, fila_pivote, factor)


def reemplazar_fila(matriz, pasos, fila, fila_pivote, factor):
    """Aplica Fi ← Fi − factor·Fj sin exigir un pivote normalizado.

    Gauss, Gauss-Jordan y LU comparten este reemplazo; no cambia el determinante.
    """
    matriz_antes = copiar_matriz(matriz)
    matriz[fila] = [
        restar_exacto(valor, multiplicar_exacto(factor, pivote))
        for valor, pivote in zip(matriz[fila], matriz[fila_pivote])
    ]
    operacion = f"F{fila + 1} = F{fila + 1} {texto_factor(factor)}F{fila_pivote + 1}"
    registrar_paso(pasos, matriz_antes, operacion, matriz)
