"""Algoritmos de conversión: divisiones sucesivas y expansión posicional."""

from collections.abc import Iterable
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


@dataclass(frozen=True)
class Conversion:
    """Conversión entre dos bases cualesquiera, compuesta por una o dos etapas.

    ``hacia_decimal`` existe cuando la base de origen no es decimal y
    ``desde_decimal`` cuando la de destino no lo es; entre ambas queda el
    valor decimal intermedio.
    """

    texto_original: str
    base_origen: int
    base_destino: int
    valor_decimal: int
    resultado: str
    hacia_decimal: ConversionHaciaDecimal | None
    desde_decimal: ConversionDesdeDecimal | None

    @property
    def etapas(self) -> tuple[ConversionHaciaDecimal | ConversionDesdeDecimal, ...]:
        return tuple(etapa for etapa in (self.hacia_decimal, self.desde_decimal) if etapa)


@dataclass(frozen=True)
class ResultadoDestino:
    """Escritura del valor en una base pedida; con sus divisiones si no es decimal."""

    base_destino: int
    resultado: str
    desde_decimal: ConversionDesdeDecimal | None


@dataclass(frozen=True)
class ConversionMultiple:
    """Un número llevado a una o varias bases con el decimal obtenido una sola vez.

    ``hacia_decimal`` es la etapa compartida (expansión posicional) y solo
    existe cuando la base de origen no es decimal. ``destinos`` conserva el
    orden pedido; cada uno trae divisiones sucesivas salvo el decimal, cuya
    escritura es el propio valor intermedio.
    """

    texto_original: str
    base_origen: int
    valor_decimal: int
    hacia_decimal: ConversionHaciaDecimal | None
    destinos: tuple[ResultadoDestino, ...]

    @property
    def bases_destino(self) -> tuple[int, ...]:
        return tuple(destino.base_destino for destino in self.destinos)


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


def convertir_a_varias_bases(
    texto: str, base_origen: int, bases_destino: Iterable[int]
) -> ConversionMultiple:
    """Convierte un número a una o varias bases pasando por decimal una sola vez.

    No hay un algoritmo por cada par de bases: cualquier conversión se
    resuelve con los dos ya existentes. Si la base de origen no es decimal,
    una única expansión posicional obtiene el valor decimal; desde ese mismo
    valor, las divisiones sucesivas escriben cada base pedida. Si decimal está
    entre los destinos, su escritura es el valor intermedio: no se convierte
    dos veces. Solo se calculan los destinos solicitados.

    Ejemplo: 17₈ → 15₁₀ (expansión, una vez) → 1111₂ y F₁₆ (divisiones por destino).
    """
    validar_base(base_origen)
    destinos = tuple(bases_destino)
    if not destinos:
        raise ValueError("Elige al menos una base de destino.")
    for base in destinos:
        validar_base(base)
    if len(set(destinos)) != len(destinos):
        raise ValueError("Las bases de destino no deben repetirse.")
    if base_origen in destinos:
        raise ValueError("La base de origen y la base de destino deben ser distintas.")

    hacia_decimal = None
    if base_origen == 10:
        valor_decimal = parsear_decimal(texto)
    else:
        hacia_decimal = base_a_decimal(texto, base_origen)
        valor_decimal = hacia_decimal.resultado

    resultados: list[ResultadoDestino] = []
    for base in destinos:
        if base == 10:
            resultados.append(ResultadoDestino(base, str(valor_decimal), None))
        else:
            desde_decimal = decimal_a_base(valor_decimal, base)
            resultados.append(ResultadoDestino(base, desde_decimal.resultado, desde_decimal))

    return ConversionMultiple(
        texto_original=texto.strip(),
        base_origen=base_origen,
        valor_decimal=valor_decimal,
        hacia_decimal=hacia_decimal,
        destinos=tuple(resultados),
    )


def convertir(texto: str, base_origen: int, base_destino: int) -> Conversion:
    """Convierte entre dos bases distintas pasando por decimal.

    Es el caso de un solo destino de ``convertir_a_varias_bases``: si la base
    de origen no es decimal, la expansión posicional obtiene el valor decimal;
    si la de destino no es decimal, las divisiones sucesivas lo escriben en
    esa base.

    Ejemplo: 1010₂ → 10₁₀ (expansión) → A₁₆ (divisiones).
    """
    conversion = convertir_a_varias_bases(texto, base_origen, (base_destino,))
    (destino,) = conversion.destinos
    return Conversion(
        texto_original=conversion.texto_original,
        base_origen=base_origen,
        base_destino=base_destino,
        valor_decimal=conversion.valor_decimal,
        resultado=destino.resultado,
        hacia_decimal=conversion.hacia_decimal,
        desde_decimal=destino.desde_decimal,
    )
