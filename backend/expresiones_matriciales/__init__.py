"""Expresiones numéricas compuestas con las operaciones de matrices y vectores.

El parser produce un árbol; el evaluador lo recorre y llama a las primitivas
de `backend.matrices` y `backend.vectores`. Una igualdad son dos árboles de
ese mismo lenguaje, evaluados y comparados con los valores ya definidos.
No resuelve `Ax = b` ni acepta símbolos sin valor.
"""

from backend.expresiones_matriciales.evaluador import Comparacion, Evaluacion, Paso, aplanar, evaluar
from backend.expresiones_matriciales.nodos import Igualdad, estructura
from backend.expresiones_matriciales.parser import analizar, analizar_entrada

__all__ = [
    "Comparacion", "Evaluacion", "Igualdad", "Paso",
    "analizar", "analizar_entrada", "aplanar", "estructura", "evaluar",
]
