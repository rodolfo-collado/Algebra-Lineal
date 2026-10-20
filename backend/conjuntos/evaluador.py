"""Evalúa valores y produce evidencia matemática; la interfaz decide cómo mostrarla."""

from dataclasses import dataclass

from backend.presupuesto_computacional import Estimacion
from .modelo import Conjunto, presentar
from .parser import Referencia


@dataclass(frozen=True)
class Resultado:
    valor: bool
    pasos: tuple[str, ...]
    estimacion: Estimacion


def evaluar_relacion(relacion, entorno):
    def resolver(operando):
        if isinstance(operando, Referencia):
            if operando.nombre not in entorno:
                raise ValueError(f"No existe el conjunto «{operando.nombre}». Defínelo o revisa su nombre.")
            return entorno[operando.nombre]
        return operando

    a, b = resolver(relacion.izquierda), resolver(relacion.derecha)
    operador = relacion.operador
    pasos = [f"Comparamos {presentar(a)} {operador} {presentar(b)}."]
    if operador in ("∈", "∉"):
        if not isinstance(b, Conjunto):
            raise ValueError("A la derecha de ∈ o ∉ debe haber un conjunto.")
        pertenece = a in b.elementos
        valor = pertenece if operador == "∈" else not pertenece
        pasos.append(f"{presentar(a)} {'aparece' if pertenece else 'no aparece'} como un elemento completo del conjunto derecho. No se descomponen los conjuntos anidados.")
        trabajo = len(b.elementos) + 1
    elif operador in ("⊆", "⊂"):
        if not isinstance(a, Conjunto) or not isinstance(b, Conjunto):
            raise ValueError("La inclusión requiere un conjunto a cada lado; un elemento individual no es un conjunto.")
        falta = next((e for e in a.elementos if e not in b.elementos), None)
        incluido = falta is None
        valor = incluido and (a != b if operador == "⊂" else True)
        pasos.append(f"El elemento {presentar(falta)} del conjunto izquierdo no pertenece al derecho." if not incluido else
                     "Cada elemento del conjunto izquierdo pertenece al derecho." if a.elementos else
                     "El conjunto vacío está incluido en todo conjunto: no tiene elementos que incumplan la inclusión.")
        if operador == "⊂":
            pasos.append("La inclusión propia exige además conjuntos distintos. " + ("Ambos son iguales." if a == b else "Los conjuntos son distintos."))
        trabajo = len(a.elementos) + len(b.elementos) + 1
    elif operador in ("=", "≠"):
        if type(a) is not type(b):
            raise ValueError("La igualdad requiere operandos del mismo tipo: conjuntos, números o textos.")
        valor = (a == b) if operador == "=" else (a != b)
        pasos.append("Los conjuntos son iguales cuando tienen exactamente los mismos elementos; el orden y las repeticiones no cuentan." if isinstance(a, Conjunto) else
                     "Comparamos los valores de los dos elementos del mismo tipo.")
        pasos.append("Los operandos coinciden." if a == b else "Los operandos son distintos.")
        trabajo = (len(a.elementos) + len(b.elementos) if isinstance(a, Conjunto) else 1) + 1
    else:
        raise ValueError("Relación no implementada.")
    return Resultado(valor, tuple(pasos), Estimacion("relacion_conjuntos", (), len(pasos), trabajo, len(pasos)))
