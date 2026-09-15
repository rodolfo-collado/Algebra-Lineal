"""Conexiones entre operaciones del módulo de sistemas, sin rutas artificiales."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Comparacion:
    metodo: str
    titulo: str
    descripcion: str


COMPARACIONES = {
    "gauss": Comparacion(
        "gauss_jordan", "Ver el mismo sistema con Gauss-Jordan",
        "Compara el procedimiento usando reducción completa.",
    ),
    "gauss_jordan": Comparacion(
        "gauss", "Ver el mismo sistema con Gauss",
        "Compara el procedimiento usando eliminación y sustitución.",
    ),
}
