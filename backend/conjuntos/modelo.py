"""Valores inmutables: los conjuntos anidados son elementos, nunca se aplanan."""

from dataclasses import dataclass
from fractions import Fraction
import json


@dataclass(frozen=True)
class Conjunto:
    elementos: frozenset["Fraction | str | Conjunto"] = frozenset()

    def __post_init__(self):
        object.__setattr__(self, "elementos", frozenset(self.elementos))
        if any(not isinstance(e, (Fraction, str, Conjunto)) for e in self.elementos):
            raise ValueError("Un elemento debe ser un número exacto, texto o conjunto.")


def presentar(valor):
    if isinstance(valor, Conjunto):
        return "{" + ", ".join(sorted(presentar(e) for e in valor.elementos)) + "}" if valor.elementos else "∅"
    if isinstance(valor, str):
        return json.dumps(valor, ensure_ascii=False)
    return str(valor)
