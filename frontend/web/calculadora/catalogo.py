"""Catálogo educativo en memoria: identidad, rutas y relaciones entre módulos."""

from dataclasses import dataclass
from typing import Literal


Estado = Literal["disponible", "proximamente"]


@dataclass(frozen=True)
class Categoria:
    id: str
    nombre: str


@dataclass(frozen=True)
class Modulo:
    id: str
    nombre: str
    descripcion: str
    categoria: Categoria
    estado: Estado = "proximamente"
    route_name: str | None = None
    relacionados: tuple[str, ...] = ()
    contenidos: tuple[str, ...] = ()


FUNDAMENTOS = Categoria("fundamentos", "Fundamentos")
VECTORES = Categoria("vectores", "Vectores")
MATRICES = Categoria("matrices", "Matrices")
SISTEMAS_LINEALES = Categoria("sistemas-lineales", "Sistemas lineales")
CATEGORIAS = (FUNDAMENTOS, VECTORES, MATRICES, SISTEMAS_LINEALES)

SISTEMAS = Modulo(
    id="sistemas",
    nombre="Sistemas de ecuaciones",
    descripcion=(
        "Resuelve sistemas mediante eliminación de Gauss o Gauss-Jordan "
        "y revisa el procedimiento paso a paso."
    ),
    categoria=SISTEMAS_LINEALES,
    estado="disponible",
    route_name="calculadora:sistemas",
    contenidos=("Gauss y Gauss-Jordan", "Clasificación de soluciones",
                "Columnas pivote", "Procedimiento paso a paso"),
)
MODULOS = (
    SISTEMAS,
    Modulo("sistemas-numericos", "Sistemas numéricos",
           "Conversión entre bases numéricas.", FUNDAMENTOS),
    Modulo("vectores", "Vectores",
           "Operaciones, ecuaciones vectoriales y combinaciones lineales.", VECTORES),
    Modulo("matrices", "Matrices",
           "Suma y multiplicación de matrices.", MATRICES),
)


def grupos_disponibles():
    """Omite categorías sin módulos disponibles, tanto en Inicio como en el menú."""
    return tuple(
        (categoria, modulos)
        for categoria in CATEGORIAS
        if (modulos := tuple(
            modulo for modulo in MODULOS
            if modulo.categoria == categoria and modulo.estado == "disponible"
        ))
    )


def relacionados_disponibles(modulo: Modulo) -> tuple[Modulo, ...]:
    """Las relaciones usan IDs; solo se presentan destinos ya disponibles."""
    por_id = {destino.id: destino for destino in MODULOS}
    return tuple(
        por_id[id_modulo] for id_modulo in modulo.relacionados
        if por_id[id_modulo].estado == "disponible"
    )


def contexto_navegacion(modulo: Modulo | None = None) -> dict:
    return {
        "grupos_modulos": grupos_disponibles(),
        "modulo_actual": modulo,
        "modulos_relacionados": relacionados_disponibles(modulo) if modulo else (),
    }
