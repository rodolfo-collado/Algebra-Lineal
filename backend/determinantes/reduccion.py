"""Determinante por triangularización sin normalizaciones y ajuste de signo."""

from fractions import Fraction

from backend.seguridad_numerica import multiplicar_exacto

from .comun import producto
from .triangularizacion import triangularizar


def reduccion(a):
    """det(A) = (−1)^s det(U), con s intercambios y det(U) producto de la diagonal."""
    datos = triangularizar(a)
    diagonal = [datos["u"][i][i] for i in range(len(datos["u"]))]
    # Conserva el caso singular sin formar productos grandes que acabarían multiplicados por cero.
    producto_diagonal = Fraction(0) if any(v == 0 for v in diagonal) else producto(diagonal)
    signo = (-1) ** datos["intercambios"]
    return {**datos, "diagonal": diagonal, "producto_diagonal": producto_diagonal,
            "signo": signo, "determinante": multiplicar_exacto(signo, producto_diagonal)}
