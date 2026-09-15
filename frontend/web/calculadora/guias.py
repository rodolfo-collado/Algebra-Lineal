"""Guías educativas estáticas reutilizables. Sin IA ni llamadas externas."""

from dataclasses import dataclass
from typing import Literal


TipoGuia = Literal["observa", "pista", "por-que"]


@dataclass(frozen=True)
class GuiaConcepto:
    id: str
    titulo: str
    contenido: str
    tipo: TipoGuia = "observa"


GUIA_METODO_GAUSS = GuiaConcepto(
    id="metodo-gauss",
    titulo="Observa",
    contenido=(
        "Gauss se detiene en forma escalonada. "
        "Gauss-Jordan continúa hasta la forma escalonada reducida."
    ),
    tipo="observa",
)

GUIA_METODO_GAUSS_JORDAN = GuiaConcepto(
    id="metodo-gauss-jordan",
    titulo="Observa",
    contenido=(
        "Gauss-Jordan reduce por completo: cada pivote queda como 1 "
        "y elimina el resto de la columna."
    ),
    tipo="observa",
)

GUIA_COLUMNAS_PIVOTE = GuiaConcepto(
    id="columnas-pivote",
    titulo="¿Por qué importa?",
    contenido=(
        "Una columna pivote indica una variable determinada por el sistema. "
        "Las columnas sin pivote corresponden a variables libres."
    ),
    tipo="por-que",
)

GUIA_INCONSISTENTE = GuiaConcepto(
    id="fila-contradiccion",
    titulo="Pista",
    contenido=(
        "Una fila de la forma [0 0 0 | C], con C ≠ 0, representa una contradicción."
    ),
    tipo="pista",
)

GUIA_SOLUCION_UNICA = GuiaConcepto(
    id="solucion-unica",
    titulo="¿Por qué importa?",
    contenido=(
        "Hay tantas columnas pivote como variables: el sistema fija un único valor "
        "para cada una."
    ),
    tipo="por-que",
)

GUIA_INFINITAS = GuiaConcepto(
    id="soluciones-infinitas",
    titulo="Observa",
    contenido=(
        "Hay menos pivotes que variables. Las variables libres parametrizan "
        "una familia infinita de soluciones."
    ),
    tipo="observa",
)

_METODO = {
    "gauss": GUIA_METODO_GAUSS,
    "gauss_jordan": GUIA_METODO_GAUSS_JORDAN,
}

_CLASIFICACION = {
    "unica": GUIA_SOLUCION_UNICA,
    "infinitas": GUIA_INFINITAS,
    "inconsistente": GUIA_INCONSISTENTE,
}


def guias_para_resultado(
    *,
    metodo: str,
    clasificacion_clave: str,
    columnas_pivote: tuple[int, ...] | list[int] | None = None,
) -> tuple[GuiaConcepto, ...]:
    """Selecciona guías estáticas según el resultado ya calculado."""
    seleccion: list[GuiaConcepto] = []
    if metodo in _METODO:
        seleccion.append(_METODO[metodo])
    if columnas_pivote:
        seleccion.append(GUIA_COLUMNAS_PIVOTE)
    if clasificacion_clave in _CLASIFICACION:
        seleccion.append(_CLASIFICACION[clasificacion_clave])
    return tuple(seleccion)
