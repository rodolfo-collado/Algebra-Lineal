"""Representaciones de valores exactos, sin floats ni llamadas a los motores.

Las expresiones históricas del backend contienen literales racionales sin
pérdida (por ejemplo «x1 = 1/3 - 2/3x2»). El adaptador de texto transforma esos
literales, no evalúa expresiones ni modifica índices, operadores o variables.
"""

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
import re

PRECISIONES = (2, 4, 6, 8)
PRECISION_PREDETERMINADA = 4
# No confundir x1/F1, subíndices, URLs o divisiones espaciadas con literales.
_RACIONAL = re.compile(r"(?<![\w./])[+-]?[0-9]+/[0-9]+(?![0-9/])")


@dataclass(frozen=True)
class Representacion:
    exacto: str
    decimal: str
    es_aproximado: bool


def formatear_exacto(valor):
    """Contrato textual existente de Fraction; también admite enteros."""
    return str(Fraction(valor))


@lru_cache(maxsize=4096, typed=True)
def representar(valor: Fraction, precision=PRECISION_PREDETERMINADA):
    """Redondeo a la mitad al par usando solo cociente y residuo enteros.

    La precisión es cantidad máxima de posiciones decimales, no cifras
    significativas. Evita el límite de precisión de un contexto Decimal y
    conserva enteros grandes. Un valor que redondea a cero nunca muestra -0.
    """
    if type(precision) is not int or precision not in PRECISIONES:
        raise ValueError("La precisión debe ser 2, 4, 6 u 8 decimales.")
    if not isinstance(valor, (Fraction, int)) or isinstance(valor, bool):
        raise TypeError("La presentación requiere un Fraction o entero exacto.")
    valor = Fraction(valor)
    escala = 10 ** precision
    cociente, residuo = divmod(abs(valor.numerator) * escala, valor.denominator)
    if 2 * residuo > valor.denominator or (2 * residuo == valor.denominator and cociente % 2):
        cociente += 1
    entero, decimal = divmod(cociente, escala)
    signo = "-" if valor < 0 and cociente else ""
    texto = f"{signo}{entero}"
    if decimal:
        texto += "." + str(decimal).zfill(precision).rstrip("0")
    return Representacion(formatear_exacto(valor), texto, residuo != 0)


def representar_texto(texto, precision=PRECISION_PREDETERMINADA):
    """Adapta literales exactos de una expresión ya calculada, sin resolverla.

    Las igualdades de una línea con redondeo pasan a aproximaciones. Para
    matrices (valores repartidos en celdas) la UI muestra una nota de grupo.
    """
    aproximado = False

    def sustituir(coincidencia):
        nonlocal aproximado
        literal = coincidencia.group()
        try:
            valor = representar(Fraction(literal), precision)
        except ZeroDivisionError:
            return literal
        aproximado |= valor.es_aproximado
        # El + puede ser un operador pegado a su operando.
        return ("+" if literal.startswith("+") else "") + valor.decimal

    decimal = _RACIONAL.sub(sustituir, texto)
    if aproximado:
        decimal = decimal.replace("=", "≈")
    return Representacion(texto, decimal, aproximado)
