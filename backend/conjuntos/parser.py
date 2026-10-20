"""Una relación entre dos operandos; las definiciones pertenecen a literales.py."""

from dataclasses import dataclass

from .literales import Lector, validar_nombre

OPERADORES = (("∈", "Pertenece"), ("∉", "No pertenece"), ("⊆", "Está incluido"),
              ("⊂", "Está incluido propiamente"), ("=", "Es igual"), ("≠", "Es distinto"))


@dataclass(frozen=True)
class Referencia:
    nombre: str


@dataclass(frozen=True)
class Relacion:
    izquierda: object
    operador: str
    derecha: object


def _operando(lector, profundidad=0):
    if lector.actual().texto == "(":
        lector.presupuesto.elemento(profundidad)
        lector.tomar()
        valor = _operando(lector, profundidad + 1)
        lector.exigir(")")
        return valor
    if lector.actual().tipo == "nombre":
        lector.presupuesto.elemento(profundidad)
        return Referencia(validar_nombre(lector.tomar().texto))
    return lector.literal(profundidad)


def analizar_relacion(texto, *, presupuesto=None):
    lector = Lector(texto, presupuesto)
    izquierda = _operando(lector)
    operador = lector.tomar().texto
    if operador not in dict(OPERADORES):
        raise ValueError("Escribe una relación con ∈, ∉, ⊆, ⊂, = o ≠ entre dos operandos.")
    derecha = _operando(lector)
    lector.fin()
    return Relacion(izquierda, operador, derecha)


def renombrar_referencias(texto, cambios):
    """Renombrado simultáneo por tokens; no toca texto entre comillas ni partes de nombres."""
    lector = Lector(texto)
    for token in reversed(lector.tokens):
        if token.tipo == "nombre" and token.texto in cambios:
            texto = texto[:token.inicio] + cambios[token.texto] + texto[token.fin:]
    return texto
