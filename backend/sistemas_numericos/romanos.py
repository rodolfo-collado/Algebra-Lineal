"""Numeración romana: conversión entre decimal y romano en el intervalo 1–3999.

No es un sistema posicional de base n, así que no reutiliza la conversión de
bases: tiene su propia tabla de símbolos, una lectura de izquierda a derecha y
una comprobación de escritura canónica. Usa la notación moderna convencional:
I, V, X, L, C, D y M, con las restas IV, IX, XL, XC, CD y CM.
"""

from dataclasses import dataclass

from .digitos import digito_a_valor


MAXIMO = 3999
# MMMDCCCLXXXVIII (3888) es la escritura más larga del intervalo.
LONGITUD_ROMANA_MAXIMA = 15

MENSAJE_INTERVALO = "Ingresa un número entero entre 1 y 3999."


@dataclass(frozen=True)
class SimboloRomano:
    """Una entrada de la tabla: un símbolo (L = 50) o un par que resta (CM = 900)."""

    simbolos: str
    valor: int

    @property
    def resta(self) -> tuple[int, int] | None:
        """(mayor, menor) de un par sustractivo: CM → (1000, 100)."""
        if len(self.simbolos) == 1:
            return None
        menor, mayor = self.simbolos
        return _POR_SIMBOLOS[mayor].valor, _POR_SIMBOLOS[menor].valor


# Tabla canónica descendente: los siete símbolos y las seis restas admitidas.
TABLA = tuple(
    SimboloRomano(simbolos, valor)
    for simbolos, valor in (
        ("M", 1000), ("CM", 900), ("D", 500), ("CD", 400),
        ("C", 100), ("XC", 90), ("L", 50), ("XL", 40),
        ("X", 10), ("IX", 9), ("V", 5), ("IV", 4), ("I", 1),
    )
)
_POR_SIMBOLOS = {entrada.simbolos: entrada for entrada in TABLA}


@dataclass(frozen=True)
class GrupoRomano:
    """Un orden decimal (millares, centenas, decenas o unidades) y su escritura.

    ``partes`` son las entradas de la tabla usadas, en orden: 60 → L y X.
    """

    valor: int
    simbolos: str
    partes: tuple[SimboloRomano, ...]


@dataclass(frozen=True)
class ConversionARomano:
    """1963 → MCMLXIII, con un grupo por orden decimal: M, CM, LX y III."""

    valor: int
    resultado: str
    grupos: tuple[GrupoRomano, ...]


@dataclass(frozen=True)
class ConversionDesdeRomano:
    """MCMLXIII → 1963, con cada símbolo o par leído de izquierda a derecha."""

    texto_original: str
    texto_normalizado: str
    resultado: int
    lecturas: tuple[SimboloRomano, ...]


def _escribir(valor: int) -> tuple[SimboloRomano, ...]:
    """Recorre la tabla de mayor a menor y usa cada entrada mientras quepa."""
    partes = []
    for entrada in TABLA:
        while valor >= entrada.valor:
            partes.append(entrada)
            valor -= entrada.valor
    return tuple(partes)


def _leer_entero(texto: str) -> int:
    """Lee un entero escrito solo con dígitos decimales y, si acaso, un - inicial.

    Acumula las cifras (total·10 + d) sin conversiones automáticas; el
    intervalo 1–3999 lo comprueba ``decimal_a_romano``.
    """
    limpio = (texto or "").strip()
    if not limpio or len(limpio) > LONGITUD_ROMANA_MAXIMA:
        raise ValueError(MENSAJE_INTERVALO)
    negativo = limpio.startswith("-")
    cifras = limpio[1:] if negativo else limpio
    if not cifras or any(cifra not in "0123456789" for cifra in cifras):
        raise ValueError("Ingresa un número entero entre 1 y 3999, escrito solo con dígitos.")
    total = 0
    for cifra in cifras:
        total = total * 10 + digito_a_valor(cifra)
    return -total if negativo else total


def decimal_a_romano(valor: int | str) -> ConversionARomano:
    """Escribe un entero del 1 al 3999 en números romanos.

    El número se separa por órdenes decimales (1963 = 1000 + 900 + 60 + 3) y
    cada parte se escribe con la tabla canónica: 1000 → M, 900 → CM,
    60 → LX y 3 → III. Unidos en orden dan MCMLXIII.

    Acepta el entero o su escritura decimal («1963»), que se valida antes de
    convertir.
    """
    if isinstance(valor, str):
        valor = _leer_entero(valor)
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(MENSAJE_INTERVALO)
    if valor == 0:
        raise ValueError(f"La numeración romana no tiene cero. {MENSAJE_INTERVALO}")
    if valor < 0:
        raise ValueError(f"La numeración romana no tiene números negativos. {MENSAJE_INTERVALO}")
    if valor > MAXIMO:
        raise ValueError(
            f"La notación romana convencional llega hasta 3999 (MMMCMXCIX). {MENSAJE_INTERVALO}"
        )

    grupos = []
    restante = valor
    for orden in (1000, 100, 10, 1):
        cifra, restante = divmod(restante, orden)
        if cifra:
            partes = _escribir(cifra * orden)
            grupos.append(
                GrupoRomano(cifra * orden, "".join(parte.simbolos for parte in partes), partes)
            )
    return ConversionARomano(valor, "".join(grupo.simbolos for grupo in grupos), tuple(grupos))


def _normalizar_romano(texto: str) -> str:
    """Recorta, valida los caracteres y pasa a mayúsculas antes de leer nada."""
    limpio = (texto or "").strip()
    if not limpio:
        raise ValueError("Ingresa un número romano.")
    if len(limpio) > LONGITUD_ROMANA_MAXIMA:
        raise ValueError(
            f"Un número romano del 1 al 3999 tiene como máximo {LONGITUD_ROMANA_MAXIMA} símbolos."
        )
    for caracter in limpio:
        if caracter.isspace():
            raise ValueError("Escribe el número romano sin espacios.")
        # Se compara con el ASCII antes de upper(): «ı».upper() también da «I».
        if caracter not in "IVXLCDMivxlcdm":
            raise ValueError(f"«{caracter}» no es un símbolo romano. Usa solo I, V, X, L, C, D y M.")
    return limpio.upper()


def romano_a_decimal(texto: str) -> ConversionDesdeRomano:
    """Lee un número romano canónico de izquierda a derecha y suma sus valores.

    Un par que resta (IV, IX, XL, XC, CD, CM) se reconoce antes que sus dos
    símbolos por separado: MCMLXIII = M + CM + L + X + I + I + I
    = 1000 + 900 + 50 + 10 + 1 + 1 + 1 = 1963. Obtener un valor no basta: la
    entrada debe coincidir con la escritura canónica de ese valor, así que
    IIII, VV, IC o MMMM se rechazan.
    """
    normalizado = _normalizar_romano(texto)
    lecturas = []
    posicion = 0
    while posicion < len(normalizado):
        entrada = (
            _POR_SIMBOLOS.get(normalizado[posicion:posicion + 2])
            or _POR_SIMBOLOS[normalizado[posicion]]
        )
        lecturas.append(entrada)
        posicion += len(entrada.simbolos)

    valores = [entrada.valor for entrada in lecturas]
    # Fuera de orden no hay una lectura aditiva fiable: IC no es CI, así que no se sugiere nada.
    if any(anterior < siguiente for anterior, siguiente in zip(valores, valores[1:])):
        raise ValueError(
            f"{normalizado} no es una representación romana válida: los símbolos van de mayor "
            "a menor valor y solo se admiten las restas IV, IX, XL, XC, CD y CM."
        )
    total = sum(valores)
    if total > MAXIMO:
        raise ValueError(
            f"{normalizado} no es una representación romana válida: la notación convencional "
            "llega hasta 3999 (MMMCMXCIX)."
        )
    canonica = decimal_a_romano(total).resultado
    if canonica != normalizado:
        raise ValueError(
            f"{normalizado} no es una representación romana válida. "
            f"Para {total} se escribe {canonica}."
        )
    return ConversionDesdeRomano(texto.strip(), normalizado, total, tuple(lecturas))
