"""Herramientas del módulo de sistemas: una sola vista y una sola matemática.

Cada herramienta cambia el contexto (título, acción principal, método fijo o
elegible, qué parte del resultado se destaca y qué bloques se muestran),
nunca el cálculo del backend.
"""

from dataclasses import dataclass
from typing import Literal


Enfoque = Literal["procedimiento", "clasificacion", "pivotes"]

# Bloques del resultado que van más allá de la matriz final y sus pivotes.
BLOQUES_COMPLETOS = frozenset({"clasificacion", "sistema-resultante", "sustitucion", "solucion"})


@dataclass(frozen=True)
class HerramientaSistemas:
    accion: str
    metodo_fijo: str | None = None
    enfoque: Enfoque = "procedimiento"
    # Título del bloque de resultado; sin él se usa el nombre del método aplicado.
    titulo_resultado: str | None = None
    # Una herramienta especializada muestra solo lo suyo; el resto queda para
    # «Resolver un sistema», que por eso sí aporta algo como relacionada.
    bloques: frozenset[str] = BLOQUES_COMPLETOS


# «sistemas» es el espacio general (/sistemas/), con el método a elegir.
HERRAMIENTAS = {
    "sistemas": HerramientaSistemas(accion="Resolver"),
    "gauss": HerramientaSistemas(accion="Resolver por Gauss", metodo_fijo="gauss"),
    "gauss-jordan": HerramientaSistemas(
        accion="Resolver por Gauss-Jordan", metodo_fijo="gauss_jordan",
    ),
    "clasificacion": HerramientaSistemas(
        accion="Clasificar el sistema",
        enfoque="clasificacion",
        titulo_resultado="Clasificación del sistema",
        bloques=frozenset({"clasificacion", "sistema-resultante"}),
    ),
    "columnas-pivote": HerramientaSistemas(
        accion="Identificar columnas pivote",
        enfoque="pivotes",
        titulo_resultado="Columnas pivote",
        bloques=frozenset(),
    ),
}
