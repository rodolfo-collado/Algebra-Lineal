"""Valores inmutables: los conjuntos anidados son elementos, nunca se aplanan."""

from dataclasses import dataclass
from fractions import Fraction
import json
from .intervalos import Recta, literal_recta


@dataclass(frozen=True)
class Conjunto:
    elementos: frozenset = frozenset()

    def __post_init__(self):
        object.__setattr__(self, "elementos", frozenset(self.elementos))
        if any(not es_elemento(e) for e in self.elementos):
            raise ValueError("Un elemento debe ser un número exacto, texto o conjunto.")


@dataclass(frozen=True)
class Par:
    primero: object
    segundo: object

    def __post_init__(self):
        if not es_elemento(self.primero) or not es_elemento(self.segundo):
            raise ValueError("Un par requiere dos valores matemáticos válidos.")


def es_elemento(valor):
    return isinstance(valor, (Fraction, str, Conjunto, Par, Recta))


def peso(valor):
    if isinstance(valor, Recta):
        return 1 + 3 * len(valor.intervalos)
    if isinstance(valor, Conjunto):
        return 1 + sum(peso(e) for e in valor.elementos)
    if isinstance(valor, Par):
        return 1 + peso(valor.primero) + peso(valor.segundo)
    return 1


def presentar(valor):
    if isinstance(valor, Recta):
        return literal_recta(valor)
    if isinstance(valor, Par):
        return f"par({presentar(valor.primero)}, {presentar(valor.segundo)})"
    if isinstance(valor, Conjunto):
        return "{" + ", ".join(sorted(presentar(e) for e in valor.elementos)) + "}" if valor.elementos else "∅"
    if isinstance(valor, str):
        return json.dumps(valor, ensure_ascii=False)
    return str(valor)
