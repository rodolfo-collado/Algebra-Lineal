"""Determinante a partir de A = LU sin intercambios."""

from backend.factorizacion_lu import factorizar_lu

from .comun import producto


def lu(a):
    """Factoriza A y, si se pudo, multiplica la diagonal de U.

    det(L) = 1 porque L es triangular con unos en la diagonal, así que
    det(A) = det(L)·det(U) = det(U). Si LU se detuvo no hay `determinante`.
    """
    datos = factorizar_lu(a)
    if datos["aplicable"]:
        datos["diagonal"] = [datos["u"][i][i] for i in range(len(a))]
        # U es triangular: su determinante es el producto de la diagonal.
        datos["determinante"] = producto(datos["diagonal"])
    return datos
