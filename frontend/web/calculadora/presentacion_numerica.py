"""Representaciones de valores exactos, sin floats ni llamadas a los motores.

Las expresiones históricas del backend contienen literales racionales sin
pérdida (por ejemplo «x1 = 1/3 - 2/3x2»). El adaptador de texto transforma esos
literales, no evalúa expresiones ni modifica índices, operadores o variables.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from functools import lru_cache
import re

from backend.seguridad_numerica import validar_valor_exacto

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
    return str(validar_valor_exacto(Fraction(valor)))


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
    valor = validar_valor_exacto(Fraction(valor))
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


# Por encima, el decimal llano tendría decenas de cifras: mantisa × 10ⁿ.
FLOTANTE_LLANO_MAXIMO = 1e15
SUPERINDICES = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _redondear(decimal, decimales):
    return format(decimal.quantize(Decimal(1).scaleb(-decimales), ROUND_HALF_EVEN).normalize(), "f")


def representar_flotante(valor, distinto_de=None):
    """Texto exacto y variantes decimales de un float para numeric_results y numeros.js.

    El valor de referencia es el decimal más corto que identifica al float (repr):
    0.1 se lee 0.1, no su expansión binaria. Devuelve (texto, variantes); variantes
    es None cuando ninguna precisión cambia el texto. Las precisiones y el redondeo
    son los de `representar`; un valor distinto de cero nunca se lee como 0: si
    redondea a cero, conserva su primera cifra significativa. Con `distinto_de` (la
    tolerancia junto a la que se lee), gana cifras hasta no leerse igual que ese valor:
    0.0000829 frente a ε = 0.0001 se lee 0.00008, no 0.0001.
    """
    if valor == 0:
        return "0", None
    decimal, potencia = Decimal(repr(valor)), ""
    if abs(valor) >= FLOTANTE_LLANO_MAXIMO:
        # Mantisa y potencia de diez (−8.08 × 10³⁸); los decimales elegidos se aplican a la mantisa.
        exponente = decimal.adjusted()
        decimal = decimal.scaleb(-exponente)
        potencia = f" × 10{str(exponente).translate(SUPERINDICES)}"
    exacto = format(decimal.normalize(), "f") + potencia
    decimales, aproximados = {}, []
    for precision in PRECISIONES:
        texto = representar(Fraction(decimal), precision).decimal
        if texto == "0":
            # 0.00004663 con 4 decimales: 0.00005, no 0.
            texto = _redondear(decimal, -decimal.adjusted())
        if distinto_de is not None and not potencia and valor != distinto_de:
            referencia, cifras = Decimal(repr(float(distinto_de))), precision
            while texto == _redondear(referencia, cifras) and cifras < 17:
                cifras += 1
                texto = _redondear(decimal, cifras)
        texto += potencia
        decimales[str(precision)] = texto
        if texto != exacto:
            aproximados.append(str(precision))
    if not aproximados:
        return exacto, None
    return exacto, {"exacto": exacto, "decimales": decimales, "aproximados": aproximados}
