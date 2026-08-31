"""Reduccion de matrices por Gauss-Jordan, registrando cada paso."""

from fractions import Fraction

from backend.matrices import (
    convertir_matriz_a_fracciones,
    copiar_matriz,
    formatear_fraccion,
    validar_matriz_rectangular
)


def buscar_fila_pivote(matriz, fila_inicio, columna):
    # Búsqueda del pivote: primera fila con un valor distinto de cero
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
        return f"+ ({formatear_fraccion(-factor)})"

    return f"- ({formatear_fraccion(factor)})"


def intercambiar_filas(matriz, pasos, fila_a, fila_b):
    matriz_antes = copiar_matriz(matriz)
    matriz[fila_a], matriz[fila_b] = matriz[fila_b], matriz[fila_a]

    # Registro del paso
    operacion = f"F{fila_a + 1} <-> F{fila_b + 1}"
    registrar_paso(pasos, matriz_antes, operacion, matriz)


def normalizar_fila(matriz, pasos, fila, pivote):
    matriz_antes = copiar_matriz(matriz)
    matriz[fila] = [numero / pivote for numero in matriz[fila]]

    # Registro del paso
    factor = formatear_fraccion(Fraction(1, 1) / pivote)
    operacion = f"F{fila + 1} = ({factor})F{fila + 1}"
    registrar_paso(pasos, matriz_antes, operacion, matriz)


def eliminar_en_columna(matriz, pasos, fila_pivote, columna, filas_objetivo):
    """Hace cero la columna en las filas indicadas usando la fila del pivote."""
    for fila in filas_objetivo:
        factor = matriz[fila][columna]
        if factor == 0:
            continue

        matriz_antes = copiar_matriz(matriz)
        matriz[fila] = [
            matriz[fila][indice] - factor * matriz[fila_pivote][indice]
            for indice in range(len(matriz[fila]))
        ]

        # Registro del paso
        operacion = (
            f"F{fila + 1} = F{fila + 1} "
            f"{texto_factor(factor)}F{fila_pivote + 1}"
        )
        registrar_paso(pasos, matriz_antes, operacion, matriz)


def aplicar_gauss_jordan(matriz, columnas_pivote=None):
    """Reduce cualquier matriz rectangular y devuelve (reducida, pasos, pivotes).

    columnas_pivote limita cuántas columnas iniciales pueden contener pivote;
    por defecto se consideran todas. Los pivotes son pares (fila, columna).
    """
    es_valida, mensaje = validar_matriz_rectangular(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    matriz_reducida = convertir_matriz_a_fracciones(matriz)
    cantidad_filas = len(matriz_reducida)
    cantidad_columnas = len(matriz_reducida[0])
    if columnas_pivote is None:
        columnas_pivote = cantidad_columnas

    pasos = []
    pivotes = []
    fila_pivote = 0

    for columna in range(columnas_pivote):
        if fila_pivote >= cantidad_filas:
            break

        # Búsqueda del pivote
        fila_encontrada = buscar_fila_pivote(matriz_reducida, fila_pivote, columna)
        if fila_encontrada is None:
            # Columna sin pivote: se salta sin avanzar la fila del pivote.
            continue

        # Intercambio de filas
        if fila_encontrada != fila_pivote:
            intercambiar_filas(matriz_reducida, pasos, fila_pivote, fila_encontrada)

        # Normalización del pivote
        pivote = matriz_reducida[fila_pivote][columna]
        if pivote != 1:
            normalizar_fila(matriz_reducida, pasos, fila_pivote, pivote)

        # Eliminación hacia abajo
        eliminar_en_columna(
            matriz_reducida,
            pasos,
            fila_pivote,
            columna,
            range(fila_pivote + 1, cantidad_filas)
        )

        pivotes.append((fila_pivote, columna))
        fila_pivote += 1

    # Eliminación hacia arriba
    for fila, columna in reversed(pivotes):
        eliminar_en_columna(
            matriz_reducida,
            pasos,
            fila,
            columna,
            range(fila - 1, -1, -1)
        )

    return matriz_reducida, pasos, pivotes


def obtener_rango(matriz):
    """Rango de cualquier matriz rectangular: cantidad de pivotes tras reducirla."""
    _, _, pivotes = aplicar_gauss_jordan(matriz)

    return len(pivotes)
