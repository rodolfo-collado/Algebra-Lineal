"""Escalonamiento de matrices por el metodo de Gauss, registrando cada paso."""

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


def aplicar_gauss(matriz, columnas_pivote=None):
    """Escalona cualquier matriz rectangular y devuelve (escalonada, pasos, pivotes).

    Solo elimina hacia abajo, así que el resultado es una forma escalonada y no
    una forma reducida. columnas_pivote limita cuántas columnas iniciales pueden
    contener pivote; por defecto se consideran todas. Los pivotes son pares
    (fila, columna).
    """
    es_valida, mensaje = validar_matriz_rectangular(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    matriz_escalonada = convertir_matriz_a_fracciones(matriz)
    cantidad_filas = len(matriz_escalonada)
    cantidad_columnas = len(matriz_escalonada[0])
    if columnas_pivote is None:
        columnas_pivote = cantidad_columnas

    pasos = []
    pivotes = []
    fila_pivote = 0

    for columna in range(columnas_pivote):
        if fila_pivote >= cantidad_filas:
            break

        # Búsqueda del pivote
        fila_encontrada = buscar_fila_pivote(matriz_escalonada, fila_pivote, columna)
        if fila_encontrada is None:
            # Columna sin pivote: se salta sin avanzar la fila del pivote.
            continue

        # Intercambio de filas
        if fila_encontrada != fila_pivote:
            intercambiar_filas(matriz_escalonada, pasos, fila_pivote, fila_encontrada)

        # Normalización del pivote
        pivote = matriz_escalonada[fila_pivote][columna]
        if pivote != 1:
            normalizar_fila(matriz_escalonada, pasos, fila_pivote, pivote)

        # Eliminación hacia abajo
        eliminar_en_columna(
            matriz_escalonada,
            pasos,
            fila_pivote,
            columna,
            range(fila_pivote + 1, cantidad_filas)
        )

        pivotes.append((fila_pivote, columna))
        fila_pivote += 1

    return matriz_escalonada, pasos, pivotes
