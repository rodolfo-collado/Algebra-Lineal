"""Opciones de «Resolver Ax = b»: dimensiones, método y textos de la ecuación matricial.

Segunda herramienta de la categoría Matrices, distinta de Operaciones con
matrices: allí x se conoce y Ax se calcula; aquí A y b se conocen y x es la
incógnita. El usuario solo elige las dimensiones de A (m×n): b tiene m
componentes y x tiene n, así que la interfaz no pide medidas independientes.
Los métodos son los de Resolver un sistema, con Gauss-Jordan predeterminado.
"""

from .opciones_matrices import DIMENSION_MAXIMA, DIMENSION_MINIMA, DIMENSION_PREDETERMINADA
from .opciones_sistemas import METODO_PREDETERMINADO, METODOS, metodos_a_resolver, titulo_resultado

__all__ = [
    "AYUDA_METODOS", "DIMENSION_MAXIMA", "DIMENSION_MINIMA", "DIMENSION_PREDETERMINADA", "ENTRADAS",
    "METODO_PREDETERMINADO", "METODOS", "NOMBRE_INCOGNITA", "forma_texto", "metodos_a_resolver",
    "titulo_resultado",
]

# A es la matriz editable y b el vector columna editable; x no se captura.
ENTRADAS = ("A", "b")
NOMBRE_INCOGNITA = "x"

AYUDA_METODOS = (
    "Gauss se detiene en la forma escalonada y resuelve por sustitución regresiva; Gauss-Jordan "
    "continúa hasta la forma escalonada reducida. Comparar ambos muestra los dos procedimientos."
)


def forma_texto(filas: int, columnas: int) -> str:
    """«A (3×2) · x (2) = b (3)»: las dimensiones de x y b derivan de las de A."""
    return f"A ({filas}×{columnas}) · x ({columnas}) = b ({filas})"
