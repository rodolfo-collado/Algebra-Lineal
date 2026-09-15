"""Validación de bases y de números escritos en una base dada."""

from .digitos import BASES_SOPORTADAS, NOMBRES_BASE, digito_a_valor


def validar_base(base: int) -> int:
    """Acepta únicamente las bases del módulo: 2, 8, 10 y 16."""
    if base not in BASES_SOPORTADAS:
        raise ValueError(
            "La base debe ser 2 (binario), 8 (octal), 10 (decimal) o 16 (hexadecimal)."
        )
    return base


def normalizar_numero(texto: str, base: int) -> str:
    """Limpia y valida un número en la base indicada; devuelve dígitos normalizados.

    - Recorta espacios extremos.
    - Rechaza vacíos, signos y caracteres ajenos a la base.
    - En hexadecimal, normaliza a–f → A–F.
    - Conserva ceros iniciales (útiles en la presentación); el valor numérico
      lo interpreta la conversión.
    """
    validar_base(base)
    if texto is None:
        raise ValueError("Ingresa un número.")

    limpio = texto.strip()
    if not limpio:
        raise ValueError("Ingresa un número.")

    if limpio[0] in "+-":
        raise ValueError(
            "Este módulo convierte solo números enteros no negativos."
        )

    if any(caracter.isspace() for caracter in limpio):
        raise ValueError("El número no debe contener espacios en medio.")

    digitos = []
    for caracter in limpio:
        try:
            valor = digito_a_valor(caracter)
        except ValueError:
            if base == 16:
                raise ValueError(
                    f"{caracter.upper() if caracter.isalpha() else caracter} "
                    "no es un dígito hexadecimal válido."
                ) from None
            nombre = NOMBRES_BASE[base]
            raise ValueError(
                f"El dígito {caracter} no es válido en un número {nombre}."
            ) from None

        if valor >= base:
            nombre = NOMBRES_BASE[base]
            if base == 16:
                raise ValueError(
                    f"{caracter.upper()} no es un dígito hexadecimal válido."
                )
            raise ValueError(
                f"El dígito {caracter} no es válido en un número {nombre}."
            )

        # Presentación académica: A–F en mayúsculas.
        digitos.append(caracter.upper() if valor >= 10 else caracter)

    return "".join(digitos)
