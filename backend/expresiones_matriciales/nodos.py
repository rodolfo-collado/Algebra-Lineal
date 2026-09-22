"""Árbol de una expresión matricial, separado del texto y del cálculo.

Cada nodo guarda la operación, sus hijos y el tramo de texto del que salió.
El resultado, el tipo y las dimensiones aparecen al evaluar: el parser no calcula.
"""

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Nodo:
    texto: str
    inicio: int
    fin: int

    def hijos(self):
        return ()


@dataclass(frozen=True)
class Numero(Nodo):
    valor: Fraction

    @property
    def operacion(self):
        return "numero"


@dataclass(frozen=True)
class Simbolo(Nodo):
    nombre: str

    @property
    def operacion(self):
        return "simbolo"


@dataclass(frozen=True)
class Negacion(Nodo):
    operando: Nodo

    @property
    def operacion(self):
        return "negacion"

    def hijos(self):
        return (self.operando,)


@dataclass(frozen=True)
class Suma(Nodo):
    izquierda: Nodo
    derecha: Nodo

    @property
    def operacion(self):
        return "suma"

    def hijos(self):
        return (self.izquierda, self.derecha)


@dataclass(frozen=True)
class Resta(Nodo):
    izquierda: Nodo
    derecha: Nodo

    @property
    def operacion(self):
        return "resta"

    def hijos(self):
        return (self.izquierda, self.derecha)


@dataclass(frozen=True)
class Producto(Nodo):
    izquierda: Nodo
    derecha: Nodo

    @property
    def operacion(self):
        return "producto"

    def hijos(self):
        return (self.izquierda, self.derecha)


def estructura(nodo):
    """Forma del árbol sin texto ni posiciones: así `AB` y `A*B` se comparan."""
    if isinstance(nodo, Numero):
        return ("numero", nodo.valor)
    if isinstance(nodo, Simbolo):
        return ("simbolo", nodo.nombre)
    if isinstance(nodo, Negacion):
        return ("negacion", estructura(nodo.operando))
    if isinstance(nodo, (Suma, Resta, Producto)):
        return (nodo.operacion, estructura(nodo.izquierda), estructura(nodo.derecha))
    raise TypeError(f"Nodo desconocido: {type(nodo).__name__}")
