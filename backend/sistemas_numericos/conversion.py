"""Algoritmos de conversión: divisiones sucesivas y expansión posicional."""

from dataclasses import dataclass

from .digitos import digito_a_valor, potencia_entera, simbolo_de_valor
from .validacion import normalizar_numero, validar_base


@dataclass(frozen=True)
class PasoDivision:
    """Un paso de división sucesiva: dividendo ÷ base = cociente, residuo."""

    dividendo: int
    base: int
    cociente: int
    residuo: int
    simbolo_residuo: str


@dataclass(frozen=True)
class PasoExpansion:
    """Un término de la combinación lineal posicional d·base^posición."""

    digito: str
    valor: int
    posicion: int
    potencia: int
    contribucion: int


@dataclass(frozen=True)
class ConversionDesdeDecimal:
    valor_decimal: int
    base_destino: int
    resultado: str
    pasos: tuple[PasoDivision, ...]


@dataclass(frozen=True)
class ConversionHaciaDecimal:
    texto_original: str
    texto_normalizado: str
    base_origen: int
    resultado: int
    pasos: tuple[PasoExpansion, ...]


def decimal_a_base(valor: int, base_destino: int) -> ConversionDesdeDecimal:
    """Convierte un entero decimal no negativo a otra base por divisiones sucesivas.

    En cada paso se divide el cociente anterior entre la base destino y se
    guarda el residuo. El número en la nueva base se obtiene leyendo los
    residuos desde el último hacia el primero (el primer residuo es el dígito
    menos significativo).

    Ejemplo (13 → binario): 13÷2→6 r1, 6÷2→3 r0, 3÷2→1 r1, 1÷2→0 r1 → 1101₂.
    """
    validar_base(base_destino)
    if base_destino == 10:
        raise ValueError("La base destino debe ser distinta de decimal.")
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise ValueError("El valor decimal debe ser un entero.")
    if valor < 0:
        raise ValueError(
            "Este módulo convierte solo números enteros no negativos."
        )

    if valor == 0:
        return ConversionDesdeDecimal(
            valor_decimal=0,
            base_destino=base_destino,
            resultado="0",
            pasos=(),
        )

    pasos: list[PasoDivision] = []
    residuos: list[str] = []
    actual = valor
    while actual > 0:
        # División entera: cociente y residuo de n = q·b + r, 0 ≤ r < b.
        cociente = actual // base_destino
        residuo = actual % base_destino
        simbolo = simbolo_de_valor(residuo)
        pasos.append(
            PasoDivision(
                dividendo=actual,
                base=base_destino,
                cociente=cociente,
                residuo=residuo,
                simbolo_residuo=simbolo,
            )
        )
        residuos.append(simbolo)
        actual = cociente

    # Lectura inversa: el último residuo es el dígito de mayor peso.
    resultado = "".join(reversed(residuos))
    return ConversionDesdeDecimal(
        valor_decimal=valor,
        base_destino=base_destino,
        resultado=resultado,
        pasos=tuple(pasos),
    )


def base_a_decimal(texto: str, base_origen: int) -> ConversionHaciaDecimal:
    """Convierte un número en base 2, 8 o 16 a decimal por expansión posicional.

    Si el número tiene dígitos dₙ…d₁d₀ en base b, su valor decimal es la
    combinación lineal:

        dₙ·bⁿ + … + d₁·b¹ + d₀·b⁰

    Cada paso del procedimiento guarda el dígito, su valor (A=10…F=15), la
    posición, la potencia b^posición y la contribución a la suma.
    """
    validar_base(base_origen)
    if base_origen == 10:
        raise ValueError("La base de origen debe ser distinta de decimal.")

    normalizado = normalizar_numero(texto, base_origen)
    # Quitar ceros a la izquierda para el cálculo, salvo el cero solo.
    significativo = normalizado.lstrip("0") or "0"
    n = len(significativo)
    pasos: list[PasoExpansion] = []
    total = 0

    for indice, digito in enumerate(significativo):
        posicion = n - 1 - indice
        valor = digito_a_valor(digito)
        potencia = potencia_entera(base_origen, posicion)
        contribucion = valor * potencia
        total += contribucion
        pasos.append(
            PasoExpansion(
                digito=digito,
                valor=valor,
                posicion=posicion,
                potencia=potencia,
                contribucion=contribucion,
            )
        )

    return ConversionHaciaDecimal(
        texto_original=texto.strip(),
        texto_normalizado=normalizado,
        base_origen=base_origen,
        resultado=total,
        pasos=tuple(pasos),
    )


def parsear_decimal(texto: str) -> int:
    """Interpreta un entero decimal no negativo a partir de dígitos 0–9.

    Construye el valor acumulando dígitos (total = total·10 + d) sin usar
    conversiones automáticas de otras bases.
    """
    normalizado = normalizar_numero(texto, 10)
    significativo = normalizado.lstrip("0") or "0"
    total = 0
    for digito in significativo:
        total = total * 10 + digito_a_valor(digito)
    return total
