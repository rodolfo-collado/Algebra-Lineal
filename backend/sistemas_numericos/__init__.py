"""Conversión entre bases numéricas: núcleo matemático independiente de la web.

Algoritmos elementales (divisiones sucesivas y expansión posicional). No usa
``bin``, ``oct``, ``hex`` ni ``int(texto, base)``: la conversión se construye
paso a paso para poder mostrarla en el procedimiento académico.
"""

from .conversion import (
    ConversionDesdeDecimal,
    ConversionHaciaDecimal,
    PasoDivision,
    PasoExpansion,
    base_a_decimal,
    decimal_a_base,
    parsear_decimal,
)
from .digitos import (
    BASES_SOPORTADAS,
    NOMBRES_BASE,
    SUBINDICES_BASE,
    digito_a_valor,
    potencia_entera,
    simbolo_de_valor,
)
from .validacion import normalizar_numero, validar_base

__all__ = [
    "BASES_SOPORTADAS",
    "NOMBRES_BASE",
    "SUBINDICES_BASE",
    "ConversionDesdeDecimal",
    "ConversionHaciaDecimal",
    "PasoDivision",
    "PasoExpansion",
    "base_a_decimal",
    "decimal_a_base",
    "digito_a_valor",
    "normalizar_numero",
    "parsear_decimal",
    "potencia_entera",
    "simbolo_de_valor",
    "validar_base",
]
