"""Sistemas numéricos: núcleo matemático independiente de la web.

Conversión entre bases con algoritmos elementales (divisiones, multiplicaciones y
expansión posicional). No usa ``bin``, ``oct``, ``hex`` ni ``int(texto, base)``:
la conversión se construye paso a paso para poder mostrarla en el procedimiento
académico. La numeración romana no es posicional y vive aparte, en ``romanos``.
"""

from .conversion import (
    Conversion,
    ConversionDesdeDecimal,
    ConversionHaciaDecimal,
    ConversionMultiple,
    PasoDivision,
    PasoExpansion,
    PasoMultiplicacion,
    ResultadoDestino,
    base_a_decimal,
    convertir,
    convertir_a_varias_bases,
    decimal_a_base,
    escribir_decimal_exacto,
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
from .romanos import (
    LONGITUD_ROMANA_MAXIMA,
    ConversionARomano,
    ConversionDesdeRomano,
    GrupoRomano,
    SimboloRomano,
    decimal_a_romano,
    romano_a_decimal,
)
from .validacion import normalizar_numero, validar_base

__all__ = [
    "BASES_SOPORTADAS",
    "LONGITUD_ROMANA_MAXIMA",
    "NOMBRES_BASE",
    "SUBINDICES_BASE",
    "Conversion",
    "ConversionARomano",
    "ConversionDesdeDecimal",
    "ConversionDesdeRomano",
    "ConversionHaciaDecimal",
    "ConversionMultiple",
    "GrupoRomano",
    "PasoDivision",
    "PasoExpansion",
    "PasoMultiplicacion",
    "ResultadoDestino",
    "SimboloRomano",
    "base_a_decimal",
    "convertir",
    "convertir_a_varias_bases",
    "decimal_a_base",
    "decimal_a_romano",
    "escribir_decimal_exacto",
    "digito_a_valor",
    "normalizar_numero",
    "parsear_decimal",
    "potencia_entera",
    "romano_a_decimal",
    "simbolo_de_valor",
    "validar_base",
]
