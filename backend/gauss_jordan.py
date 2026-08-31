"""Reduccion de matrices por Gauss-Jordan, registrando cada paso."""

from backend.matrices import (
    convertir_matriz_a_fracciones,
    validar_matriz_rectangular
)
from backend.operaciones_filas import (
    buscar_fila_pivote,
    eliminar_en_columna,
    intercambiar_filas,
    normalizar_fila
)


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
