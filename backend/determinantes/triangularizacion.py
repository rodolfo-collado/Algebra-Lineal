"""Triangularización exacta para Determinantes, sin normalizar filas."""

from backend.operaciones_filas import buscar_fila_pivote, intercambiar_filas, reemplazar_fila
from backend.seguridad_numerica import dividir_exacto

from .comun import preparar


def triangularizar(a):
    """Devuelve U, pasos y cantidad de intercambios de una matriz cuadrada.

    Solo intercambia cuando el pivote actual es cero y hay uno no nulo debajo.
    Los reemplazos Fi ← Fi − (entrada/pivote)Fj conservan el determinante.
    Gauss y Gauss-Jordan mantienen sus algoritmos y normalizaciones originales.
    """
    u = preparar(a)
    pasos, intercambios = [], 0
    fila_pivote = 0
    for columna_pivote in range(len(u)):
        encontrada = buscar_fila_pivote(u, fila_pivote, columna_pivote)
        if encontrada is None:
            continue
        if encontrada != fila_pivote:
            intercambiar_filas(u, pasos, fila_pivote, encontrada)
            intercambios += 1
        pivote = u[fila_pivote][columna_pivote]
        for fila in range(fila_pivote + 1, len(u)):
            if u[fila][columna_pivote]:
                factor = dividir_exacto(u[fila][columna_pivote], pivote)
                reemplazar_fila(u, pasos, fila, fila_pivote, factor)
        fila_pivote += 1
    return {"u": u, "pasos": pasos, "intercambios": intercambios}
