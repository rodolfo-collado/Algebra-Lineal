"""Conexiones educativas que se ofrecen después de resolver («También puedes explorar»).

No calculan nada nuevo: cada enlace vuelve a la propia herramienta con la misma
entrada preparada por GET (otro método u otro bloque del resultado) o lleva a
una herramienta existente que aporta otra lectura del mismo problema. Solo se
enlazan rutas del catálogo que ya están disponibles.
"""

from dataclasses import dataclass
from urllib.parse import urlencode

from django.urls import reverse

from . import catalogo
from .opciones_sistemas import BLOQUES, METODOS


@dataclass(frozen=True)
class Exploracion:
    texto: str
    url: str


INVITACIONES_METODOS = {
    "gauss": "Resolver el mismo sistema con Gauss",
    "gauss_jordan": "Resolver el mismo sistema con Gauss-Jordan",
    "comparar": "Comparar Gauss y Gauss-Jordan con este sistema",
}

# Un bloque que el usuario dejó sin mostrar se ofrece como siguiente paso.
INVITACIONES_BLOQUES = {
    "procedimiento": "Ver el procedimiento paso a paso",
    "clasificacion": "Ver la clasificación del sistema",
    "pivotes": "Ver las columnas pivote",
    "sistema-resultante": "Ver el sistema resultante",
}


def enlace_sistema(entrada, metodo, mostrar):
    """Vuelve a Resolver un sistema con la misma entrada preparada; nada se resuelve por GET."""
    parametros = [*entrada, ("metodo", metodo), ("mostrar_definido", "1")]
    parametros += [("mostrar", clave) for clave, _ in BLOQUES if clave in mostrar]
    return f"{reverse('calculadora:sistemas')}?{urlencode(parametros)}"


def exploraciones_sistema(entrada, metodo, mostrar):
    """Conexiones tras resolver: el otro método, comparar, los bloques omitidos y Ax = b.

    `entrada` son los pares (campo, valor) que reproducen lo escrito, como texto
    o como celdas de la matriz aumentada.
    """
    exploraciones = []
    if metodo != "comparar":
        for clave, _ in METODOS:
            if clave != metodo:
                exploraciones.append(
                    Exploracion(INVITACIONES_METODOS[clave], enlace_sistema(entrada, clave, mostrar))
                )
    for clave, _ in BLOQUES:
        if clave not in mostrar:
            exploraciones.append(
                Exploracion(INVITACIONES_BLOQUES[clave], enlace_sistema(entrada, metodo, (*mostrar, clave)))
            )
    ecuacion = catalogo.ECUACIONES_MATRICIALES
    if ecuacion.disponible:
        exploraciones.append(
            Exploracion("Plantear un sistema como ecuación matricial Ax = b", ecuacion.ruta)
        )
    return tuple(exploraciones)
