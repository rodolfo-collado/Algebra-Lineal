"""Conversión exacta: divisiones y multiplicaciones sucesivas, expansión posicional."""

from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction

from .digitos import digito_a_valor, potencia_entera, simbolo_de_valor
from .validacion import normalizar_numero, validar_base


# Un período puede ser enorme aunque la entrada sea corta. Nunca se trunca.
MAX_PASOS_FRACCIONARIOS = 1024


@dataclass(frozen=True)
class PasoDivision:
    """Un paso de división sucesiva: dividendo ÷ base = cociente, residuo."""

    dividendo: int
    base: int
    cociente: int
    residuo: int
    simbolo_residuo: str


@dataclass(frozen=True)
class PasoMultiplicacion:
    """Un dígito fraccionario obtenido de f·base = dígito + fracción restante."""

    fraccion_inicial: Fraction
    base: int
    producto: Fraction
    digito: int
    simbolo_digito: str
    fraccion_restante: Fraction


@dataclass(frozen=True)
class PasoExpansion:
    """Un término de la combinación lineal posicional d·base^posición."""

    digito: str
    valor: int
    posicion: int
    potencia: int | Fraction
    contribucion: int | Fraction


@dataclass(frozen=True)
class ConversionDesdeDecimal:
    """Divisiones enteras y multiplicaciones fraccionarias; período con índice desde cero."""

    valor_decimal: int | Fraction
    base_destino: int
    resultado: str
    pasos: tuple[PasoDivision, ...]
    multiplicaciones: tuple[PasoMultiplicacion, ...] = ()
    parte_entera: str = "0"
    parte_no_periodica: str = ""
    parte_periodica: str = ""
    inicio_periodo: int | None = None


@dataclass(frozen=True)
class ConversionHaciaDecimal:
    texto_original: str
    texto_normalizado: str
    base_origen: int
    resultado: int | Fraction
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
    valor_decimal: int | Fraction
    resultado: str
    hacia_decimal: ConversionHaciaDecimal | None
    desde_decimal: ConversionDesdeDecimal | None

    @property
    def etapas(self) -> tuple[ConversionHaciaDecimal | ConversionDesdeDecimal, ...]:
        return tuple(etapa for etapa in (self.hacia_decimal, self.desde_decimal) if etapa)


@dataclass(frozen=True)
class ResultadoDestino:
    """Escritura del valor en una base pedida y procedimiento desde decimal."""

    base_destino: int
    resultado: str
    desde_decimal: ConversionDesdeDecimal | None


@dataclass(frozen=True)
class ConversionMultiple:
    """Un número llevado a una o varias bases con el decimal obtenido una sola vez.

    ``hacia_decimal`` es la etapa compartida (expansión posicional) y solo
    existe cuando la base de origen no es decimal. ``destinos`` conserva el
    orden pedido; cada uno trae divisiones y multiplicaciones salvo el decimal, cuya
    escritura es el propio valor intermedio.
    """

    texto_original: str
    base_origen: int
    valor_decimal: int | Fraction
    hacia_decimal: ConversionHaciaDecimal | None
    destinos: tuple[ResultadoDestino, ...]

    @property
    def bases_destino(self) -> tuple[int, ...]:
        return tuple(destino.base_destino for destino in self.destinos)


def decimal_a_base(valor: int | Fraction, base_destino: int) -> ConversionDesdeDecimal:
    """Divide la parte entera y multiplica la fraccionaria, con aritmética exacta.

    En cada paso se divide el cociente anterior entre la base destino y se
    guarda el residuo. El número en la nueva base se obtiene leyendo los
    residuos desde el último hacia el primero (el primer residuo es el dígito
    menos significativo).

    La fracción restante se multiplica por la base, guardando el entero como
    dígito y repitiendo con la nueva fracción hasta cero o un ciclo. Un período
    que exceda MAX_PASOS_FRACCIONARIOS produce ValueError, nunca truncamiento.

    Ejemplo (13 → binario): 13÷2→6 r1, 6÷2→3 r0, 3÷2→1 r1, 1÷2→0 r1 → 1101₂.
    """
    validar_base(base_destino)
    if base_destino == 10:
        raise ValueError("La base destino debe ser distinta de decimal.")
    if not isinstance(valor, (int, Fraction)) or isinstance(valor, bool):
        raise ValueError("El valor decimal debe ser un entero o Fraction exacto.")
    if valor < 0:
        raise ValueError(
            "Este módulo convierte solo números no negativos."
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
    actual = valor // 1
    fraccion = Fraction(valor - actual)
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
    parte_entera = "".join(reversed(residuos)) or "0"
    multiplicaciones: list[PasoMultiplicacion] = []
    digitos: list[str] = []
    vistas: dict[Fraction, int] = {}
    inicio_periodo = None
    while fraccion:
        # La misma fracción produce los mismos dígitos a partir de aquí.
        if fraccion in vistas:
            inicio_periodo = vistas[fraccion]
            break
        if len(multiplicaciones) >= MAX_PASOS_FRACCIONARIOS:
            raise ValueError(
                f"La expansión en base {base_destino} supera el límite de seguridad de "
                f"{MAX_PASOS_FRACCIONARIOS} pasos fraccionarios sin terminar ni detectar "
                "un período. No se ha truncado ni aproximado el resultado."
            )
        vistas[fraccion] = len(digitos)
        producto = fraccion * base_destino
        digito = producto // 1
        restante = producto - digito
        simbolo = simbolo_de_valor(digito)
        multiplicaciones.append(
            PasoMultiplicacion(fraccion, base_destino, producto, digito, simbolo, restante)
        )
        digitos.append(simbolo)
        fraccion = restante

    parte_no_periodica = "".join(digitos[:inicio_periodo])
    parte_periodica = "".join(digitos[inicio_periodo:]) if inicio_periodo is not None else ""
    resultado = parte_entera
    if digitos:
        resultado += "." + parte_no_periodica
        if parte_periodica:
            resultado += f"({parte_periodica})"
    return ConversionDesdeDecimal(
        valor_decimal=valor,
        base_destino=base_destino,
        resultado=resultado,
        pasos=tuple(pasos),
        multiplicaciones=tuple(multiplicaciones),
        parte_entera=parte_entera,
        parte_no_periodica=parte_no_periodica,
        parte_periodica=parte_periodica,
        inicio_periodo=inicio_periodo,
    )


def base_a_decimal(texto: str, base_origen: int) -> ConversionHaciaDecimal:
    """Convierte un número en base 2, 8 o 16 a decimal por expansión posicional.

    Si el número tiene dígitos dₙ…d₁d₀ en base b, su valor decimal es la
    combinación lineal:

        dₙ·bⁿ + … + d₁·b¹ + d₀·b⁰ + d₋₁·b⁻¹ + …

    Cada paso del procedimiento guarda el dígito, su valor (A=10…F=15), la
    posición, la potencia b^posición y la contribución a la suma.
    """
    validar_base(base_origen)
    if base_origen == 10:
        raise ValueError("La base de origen debe ser distinta de decimal.")

    normalizado = normalizar_numero(texto, base_origen)
    # Quitar ceros a la izquierda para el cálculo, salvo el cero solo.
    entera, _, fraccionaria = normalizado.partition(".")
    entera = entera.lstrip("0") or "0"
    significativo = entera + fraccionaria
    n = len(entera)
    pasos: list[PasoExpansion] = []
    total = 0

    for indice, digito in enumerate(significativo):
        posicion = n - 1 - indice
        valor = digito_a_valor(digito)
        potencia = (
            potencia_entera(base_origen, posicion)
            if posicion >= 0
            else Fraction(1, potencia_entera(base_origen, -posicion))
        )
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


def parsear_decimal(texto: str) -> int | Fraction:
    """Interpreta dígitos decimales y un punto opcional sin perder precisión.

    Construye el valor acumulando dígitos (total = total·10 + d) sin usar
    conversiones automáticas de otras bases.
    """
    normalizado = normalizar_numero(texto, 10)
    entera, _, fraccionaria = normalizado.partition(".")
    significativo = entera + fraccionaria
    total = 0
    for digito in significativo:
        total = total * 10 + digito_a_valor(digito)
    return Fraction(total, potencia_entera(10, len(fraccionaria))) if fraccionaria else total


def escribir_decimal_exacto(valor: int | Fraction) -> str:
    """Escritura finita exacta para los denominadores 2ⁿ·5ᵐ del módulo.

    Escala a una potencia de diez; no redondea ni vuelve a interpretar el origen.
    También sirve para presentar los valores racionales de los pasos.
    """
    racional = Fraction(valor)
    denominador = racional.denominator
    exponentes = []
    for factor in (2, 5):
        exponente = 0
        while denominador % factor == 0:
            denominador //= factor
            exponente += 1
        exponentes.append(exponente)
    if denominador != 1:
        raise ValueError("Este valor no tiene una escritura decimal finita.")
    posiciones = max(exponentes)
    if not posiciones:
        return str(racional.numerator)
    escalado = abs(racional.numerator) * (10 ** posiciones // racional.denominator)
    digitos = str(escalado).zfill(posiciones + 1)
    signo = "-" if racional < 0 else ""
    return signo + digitos[:-posiciones] + "." + digitos[-posiciones:].rstrip("0")


def convertir_a_varias_bases(
    texto: str, base_origen: int, bases_destino: Iterable[int]
) -> ConversionMultiple:
    """Convierte un número a una o varias bases pasando por decimal una sola vez.

    No hay un algoritmo por cada par de bases: cualquier conversión se
    resuelve con los dos ya existentes. Si la base de origen no es decimal,
    una única expansión posicional obtiene el valor decimal; desde ese mismo
    valor, las divisiones y multiplicaciones escriben cada base pedida. Si decimal está
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
            resultados.append(ResultadoDestino(base, escribir_decimal_exacto(valor_decimal), None))
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
    si la de destino no es decimal, las divisiones y multiplicaciones lo escriben en
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
