"""Conexiones entre operaciones del módulo de sistemas, sin rutas artificiales."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Comparacion:
    metodo: str
    titulo: str
    descripcion: str


COMPARACIONES = {
    "gauss": Comparacion(
        "gauss_jordan",
        "Comparar procedimiento",
        "Resuelve este mismo sistema con reducción completa.",
    ),
    "gauss_jordan": Comparacion(
        "gauss",
        "Comparar procedimiento",
        "Resuelve este mismo sistema con eliminación y sustitución.",
    ),
}
