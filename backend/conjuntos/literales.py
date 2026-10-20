"""Gramática cerrada de datos; no evalúa código ni permite referencias dentro de literales."""

from dataclasses import dataclass
from fractions import Fraction
import json
import keyword
import re

from backend.parser_sistemas import convertir_a_numero
from .modelo import Conjunto
from .presupuesto import Presupuesto

NOMBRE = r"[A-Za-z][A-Za-z0-9_]*"
RESERVADOS = frozenset(keyword.kwlist) | {
    "in", "not", "true", "false", "none", "union", "interseccion", "diferencia",
    "potencia", "par", "intervalo", "vacio",
}
_TOKEN = re.compile(
    rf'(?P<texto>"(?:[^"\\\x00-\x1f]|\\["\\/bfnrt]|\\u[0-9a-fA-F]{{4}})*")'
    rf'|(?P<numero>[+-]?\s*(?:[0-9]+\.[0-9]+|\.[0-9]+|[0-9]+(?:\s*/\s*[0-9]+)?))'
    rf'|(?P<nombre>{NOMBRE})|(?P<signo>[{{}},∅()∈∉⊆⊂=≠])'
)


def validar_nombre(nombre):
    if not re.fullmatch(NOMBRE, nombre) or nombre.lower() in {n.lower() for n in RESERVADOS}:
        raise ValueError("Usa un nombre único que comience con una letra A–Z, seguido de letras, cifras o guion bajo; evita palabras reservadas.")
    return nombre


@dataclass(frozen=True)
class Token:
    tipo: str
    texto: str
    inicio: int
    fin: int


class Lector:
    def __init__(self, texto, presupuesto=None):
        self.presupuesto = presupuesto if presupuesto is not None else Presupuesto()
        self.presupuesto.texto(texto)
        self.tokens = []
        posicion = 0
        while posicion < len(texto):
            if texto[posicion].isspace():
                posicion += 1
                continue
            token = _TOKEN.match(texto, posicion)
            if not token:
                raise ValueError(f"Símbolo o texto inválido en la posición {posicion + 1}. Usa llaves, números o texto entre comillas dobles.")
            self.tokens.append(Token(token.lastgroup, token[0], posicion, token.end()))
            posicion = token.end()
        self.indice = 0

    def actual(self):
        return self.tokens[self.indice] if self.indice < len(self.tokens) else Token("fin", "", 0, 0)

    def tomar(self):
        token = self.actual()
        self.indice += 1
        return token

    def exigir(self, texto):
        if self.actual().texto != texto:
            raise ValueError(f"Se esperaba «{texto}»; revisa separadores y cierres.")
        self.tomar()

    def fin(self):
        if self.actual().tipo != "fin":
            raise ValueError(f"Texto inesperado «{self.actual().texto}». Escribe una sola relación o un literal completo.")

    def literal(self, profundidad=0):
        self.presupuesto.elemento(profundidad)
        token = self.tomar()
        if token.texto == "∅":
            return Conjunto()
        if token.texto == "{":
            elementos = []
            if self.actual().texto != "}":
                elementos.append(self.literal(profundidad + 1))
                while self.actual().texto == ",":
                    self.tomar()
                    elementos.append(self.literal(profundidad + 1))
            self.exigir("}")
            return Conjunto(frozenset(elementos))
        if token.tipo == "numero":
            return Fraction(convertir_a_numero(token.texto, limitar_entrada=True))
        if token.tipo == "texto":
            valor = json.loads(token.texto)
            # Un surrogate aislado no se puede presentar como UTF-8 en la web.
            if any(0xD800 <= ord(c) <= 0xDFFF for c in valor):
                raise ValueError("El texto contiene un carácter Unicode incompleto.")
            return valor
        raise ValueError("Se esperaba un número, texto entre comillas dobles o un conjunto entre llaves; los literales no admiten nombres ni comprensión.")


def analizar_literal(texto, *, presupuesto=None):
    lector = Lector(texto, presupuesto)
    valor = lector.literal()
    lector.fin()
    if not isinstance(valor, Conjunto):
        raise ValueError("La definición debe contener un conjunto: usa {…} o ∅.")
    return valor


def analizar_definicion(texto, *, presupuesto=None):
    lector = Lector(texto, presupuesto)
    nombre = validar_nombre(lector.tomar().texto)
    lector.exigir("=")
    valor = lector.literal()
    lector.fin()
    if not isinstance(valor, Conjunto):
        raise ValueError("A la derecha de = debe haber un conjunto entre llaves o ∅.")
    return nombre, valor
