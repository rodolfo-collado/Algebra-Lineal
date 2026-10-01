"""Seguridad de literales e intermedios exactos, independiente del costo estimado."""

from fractions import Fraction
import sys

DIGITOS_MAXIMOS = 100
MENSAJE_NUMERO_GRANDE = "El número es demasiado grande para esta herramienta."
MENSAJE_NOTACION_CIENTIFICA = (
    "Esta herramienta no admite notación científica. "
    "Escribe el número como entero, fracción o decimal."
)
MENSAJE_CALCULO_GRANDE = (
    "El cálculo produjo números demasiado grandes para mostrarlos de forma segura."
)

# Hasta unas 3613 cifras por componente: deja margen para Exacto/Decimal.
BITS_MAXIMOS = 12_000


def _es_notacion_cientifica(cuerpo):
    # No se interpreta el exponente ni se construye una potencia de diez.
    hubo_digito = False
    for caracter in cuerpo:
        if caracter in "eE" and hubo_digito:
            return True
        if caracter.isdigit():
            hubo_digito = True
    return False


def _exigir_digitos(parte):
    if len(parte) > DIGITOS_MAXIMOS:
        raise ValueError(MENSAJE_NUMERO_GRANDE)


def _rechazar_digitos_excesivos(cuerpo):
    if "_" in cuerpo:
        # Conserva el límite histórico de Sistemas para separadores de Fraction.
        if sum(caracter.isdigit() for caracter in cuerpo) > DIGITOS_MAXIMOS:
            raise ValueError(MENSAJE_NUMERO_GRANDE)
        return
    if "/" in cuerpo:
        numerador, barra, denominador = cuerpo.partition("/")
        if barra and numerador.isdigit() and denominador.isdigit():
            _exigir_digitos(numerador)
            _exigir_digitos(denominador)
        return
    if "." in cuerpo:
        entera, punto, fraccion = cuerpo.partition(".")
        if (
            punto
            and "." not in fraccion
            and (not entera or entera.isdigit())
            and (not fraccion or fraccion.isdigit())
            and (entera or fraccion)
        ):
            _exigir_digitos(entera)
            _exigir_digitos(fraccion)
        return
    if cuerpo.isdigit():
        _exigir_digitos(cuerpo)


def validar_literal_numerico(texto):
    """Inspecciona texto antes de Fraction; el parser conserva su propia gramática."""
    if not isinstance(texto, str):
        return
    compacto = "".join(texto.split())
    if not compacto:
        return
    cuerpo = compacto[1:] if compacto[0] in "+-" else compacto
    if not cuerpo:
        return
    if _es_notacion_cientifica(cuerpo):
        raise ValueError(MENSAJE_NOTACION_CIENTIFICA)
    _rechazar_digitos_excesivos(cuerpo)


def validar_valor_exacto(valor):
    """Devuelve el valor o lo rechaza sin convertir sus enteros a texto."""
    limite_texto = sys.get_int_max_str_digits()
    # 2**(3*d) < 10**d: también respeta una configuración más restrictiva.
    limite = min(BITS_MAXIMOS, 3 * limite_texto) if limite_texto else BITS_MAXIMOS
    if max(valor.numerator.bit_length(), valor.denominator.bit_length()) > limite:
        raise ValueError(MENSAJE_CALCULO_GRANDE)
    return valor


def _operandos(a, b):
    return Fraction(validar_valor_exacto(a)), Fraction(validar_valor_exacto(b))


def validar_matriz_exacta(matriz):
    for fila in matriz:
        for valor in fila:
            validar_valor_exacto(valor)


def sumar_exacto(a, b):
    a, b = _operandos(a, b)
    return validar_valor_exacto(a + b)


def restar_exacto(a, b):
    a, b = _operandos(a, b)
    return validar_valor_exacto(a - b)


def multiplicar_exacto(a, b):
    a, b = _operandos(a, b)
    return validar_valor_exacto(a * b)


def dividir_exacto(a, b):
    a, b = _operandos(a, b)
    return validar_valor_exacto(a / b)
