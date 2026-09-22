"""Expresiones compuestas con las operaciones de matrices y vectores.

El parser produce un árbol; el evaluador lo recorre y llama a las primitivas
de `backend.matrices` y `backend.vectores` cuando todo es numérico. Una
igualdad numérica compara esos valores. Una matriz desconocida declarada,
multiplicada por un vector simbólico, se determina comparando coeficientes
de formas lineales. Hallar x con A y b numéricos sigue en ecuaciones matriciales.
Un nombre que no esté definido sigue siendo un error.
"""

from backend.expresiones_matriciales.evaluador import Comparacion, Evaluacion, Paso, aplanar, evaluar
from backend.expresiones_matriciales.lineal import Determinacion, FormaLineal, analizar_lineal, coef_vector
from backend.expresiones_matriciales.nodos import Igualdad, estructura
from backend.expresiones_matriciales.parser import analizar, analizar_entrada

__all__ = [
    "Comparacion", "Determinacion", "Evaluacion", "FormaLineal", "Igualdad", "Paso",
    "analizar", "analizar_entrada", "analizar_lineal", "aplanar", "coef_vector",
    "estructura", "evaluar",
]
