"""Expresiones numéricas compuestas con las operaciones de matrices y vectores.

El parser produce un árbol; el evaluador lo recorre y llama a las primitivas
de `backend.matrices` y `backend.vectores`. No resuelve ecuaciones ni símbolos
desconocidos: un incremento posterior puede comparar árboles o sustituir una
matriz incógnita sin cambiar este lenguaje.
"""

from backend.expresiones_matriciales.evaluador import Evaluacion, Paso, aplanar, evaluar
from backend.expresiones_matriciales.nodos import estructura
from backend.expresiones_matriciales.parser import analizar

__all__ = ["Evaluacion", "Paso", "analizar", "aplanar", "estructura", "evaluar"]
