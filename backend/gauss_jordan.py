"""Reduccion de matrices por Gauss-Jordan, registrando cada paso."""

from backend.gauss import aplicar_gauss
from backend.operaciones_filas import eliminar_en_columna


def aplicar_gauss_jordan(matriz, columnas_pivote=None):
    """Reduce cualquier matriz rectangular y devuelve (reducida, pasos, pivotes).

    Parte de la forma escalonada de Gauss y solo añade la eliminación hacia
    arriba. columnas_pivote limita cuántas columnas iniciales pueden contener
    pivote; por defecto se consideran todas. Los pivotes son pares
    (fila, columna).
    """
    matriz_reducida, pasos, pivotes = aplicar_gauss(matriz, columnas_pivote)

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
