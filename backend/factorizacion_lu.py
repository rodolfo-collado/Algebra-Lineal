"""Factorización exacta A = LU sin intercambios de filas.

Es independiente de Determinantes: devuelve L, U y los pasos para que otra
herramienta (por ejemplo, resolver Ax = b) pueda reutilizarlos.
"""

from fractions import Fraction

from backend.matrices import matriz_identidad, validar_matriz
from backend.operaciones_filas import reemplazar_fila
from backend.seguridad_numerica import dividir_exacto, validar_matriz_exacta


def factorizar_lu(a):
    """Devuelve `aplicable`, `l`, `u` y `pasos` de A = LU, sin modificar A.

    U se obtiene solo con reemplazos Fi ← Fi − m·Fj, sin normalizar pivotes,
    y L guarda cada multiplicador m bajo su diagonal de unos. Si un pivote es 0
    con un número distinto de cero debajo, se detiene: `aplicable` es False y
    `pivote_nulo` indica su posición (fila y columna, desde 1).
    """
    valida, mensaje = validar_matriz(a)
    if not valida:
        raise ValueError(mensaje)
    if len(a) != len(a[0]):
        raise ValueError("La factorización LU de este método requiere una matriz cuadrada.")
    validar_matriz_exacta(a)
    n = len(a)
    u = [[Fraction(valor) for valor in fila] for fila in a]
    l, pasos = matriz_identidad(n), []
    for j in range(n):
        if u[j][j] == 0:
            if any(u[i][j] for i in range(j + 1, n)):
                # Un pivote cero detiene LU porque este método no intercambia filas.
                return {"aplicable": False, "l": l, "u": u, "pasos": pasos,
                        "pivote_nulo": {"fila": j + 1, "columna": j + 1}}
            # Columna ya nula bajo el pivote: no hay nada que eliminar.
            continue
        for i in range(j + 1, n):
            if u[i][j]:
                # L guarda los multiplicadores usados para construir U.
                l[i][j] = dividir_exacto(u[i][j], u[j][j])
                reemplazar_fila(u, pasos, i, j, l[i][j])
    return {"aplicable": True, "l": l, "u": u, "pasos": pasos, "pivote_nulo": None}
