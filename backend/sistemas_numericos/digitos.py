"""Equivalencia de dígitos y potencias enteras para bases 2, 8, 10 y 16.

En hexadecimal, los valores 10–15 se escriben A–F. Esta capa traduce entre el
valor numérico del residuo o del dígito y el símbolo que ve el estudiante.
"""

BASES_SOPORTADAS = frozenset({2, 8, 10, 16})

NOMBRES_BASE = {
    2: "binario",
    8: "octal",
    10: "decimal",
    16: "hexadecimal",
}

# Subíndices tipográficos para notación académica (1011₂, 1A₁₆).
SUBINDICES_BASE = {
    2: "₂",
    8: "₈",
    10: "₁₀",
    16: "₁₆",
}

_SIMBOLOS = "0123456789ABCDEF"


def simbolo_de_valor(valor: int) -> str:
    """Residuo o valor de dígito (0–15) → símbolo visible; 10→A … 15→F."""
    if not 0 <= valor <= 15:
        raise ValueError(f"No hay símbolo hexadecimal para el valor {valor}.")
    return _SIMBOLOS[valor]


def digito_a_valor(digito: str) -> int:
    """Símbolo de un dígito → valor numérico; acepta a–f y normaliza a 0–15."""
    if len(digito) != 1:
        raise ValueError("Cada dígito debe ser un solo carácter.")
    caracter = digito.upper()
    if caracter in _SIMBOLOS:
        return _SIMBOLOS.index(caracter)
    raise ValueError(f"{digito} no es un dígito hexadecimal válido.")


def potencia_entera(base: int, exponente: int) -> int:
    """Calcula base^exponente por multiplicaciones sucesivas (exponente ≥ 0).

    Equivale a la potencia posicional de la expansión
    dₙ·bⁿ + … + d₁·b¹ + d₀·b⁰ sin delegar en conversiones de base.
    """
    if exponente < 0:
        raise ValueError("El exponente posicional no puede ser negativo.")
    if base < 2:
        raise ValueError("La base debe ser al menos 2.")
    resultado = 1
    for _ in range(exponente):
        resultado *= base
    return resultado
