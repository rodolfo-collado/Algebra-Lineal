"""Determinantes exactos, independientes de la interfaz.

Cada método recibe A y devuelve datos estructurados (sin texto de interfaz).
Todos los métodos que se pueden aplicar a una misma A dan el mismo determinante.
"""

from .cofactores import ORDEN_MAXIMO_COFACTORES, cofactores
from .comun import directo_2x2, preparar
from .lu import lu
from .recomendacion import analizar_matriz_para_determinante
from .reduccion import reduccion
from .sarrus import sarrus

METODOS = {
    "directo_2x2": directo_2x2,
    "cofactores": cofactores,
    "sarrus": sarrus,
    "lu": lu,
    "reduccion": reduccion,
}
# La fórmula directa y Sarrus solo existen para un tamaño.
ORDEN_EXIGIDO = {"directo_2x2": 2, "sarrus": 3}
METODO_PREDETERMINADO = "reduccion"


def calcular_determinante(a, metodo=METODO_PREDETERMINADO, expansion="auto"):
    """Valida A, ejecuta el método pedido y devuelve `metodo`, `matriz`, `aplicable` y su evidencia.

    `expansion` solo la usa Cofactores ("auto", "fila_i" o "columna_j").
    LU devuelve `aplicable` False cuando necesitaría intercambiar filas.
    """
    if not isinstance(metodo, str) or metodo not in METODOS:
        raise ValueError("Selecciona un método válido para calcular el determinante.")
    a = preparar(a)
    datos = cofactores(a, expansion) if metodo == "cofactores" else METODOS[metodo](a)
    return {"metodo": metodo, "matriz": a, "aplicable": True, **datos}
