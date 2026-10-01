"""Presupuesto de entrada de Resolver un sistema (web y aplicación desktop).

El procedimiento guarda dos matrices por operación de fila y las convierte a
HTML. Por eso el límite es menor que el de las operaciones básicas de matrices:
admite un sistema cuadrado de 10 variables y rectangulares de hasta 120 celdas.
Con CSRF y las cuatro opciones de resultado, el POST usa 130 campos (de 1000).
Un literal se inspecciona como texto antes de Fraction: 100 dígitos por
componente y sin notación científica. En un sistema escrito, cada valor que
resulta de agrupar términos queda dentro de lo que produce un solo literal, así
que la matriz tiene las mismas cotas que la escrita celda por celda.
"""

# Reexportaciones para consumidores de la política histórica de Sistemas.
from backend.seguridad_numerica import (
    DIGITOS_MAXIMOS,
    MENSAJE_NUMERO_GRANDE,
    MENSAJE_NOTACION_CIENTIFICA,
    validar_literal_numerico,
)

ECUACIONES_MAXIMAS = 12
VARIABLES_MAXIMAS = 12
CELDAS_MAXIMAS = 120
LONGITUD_SISTEMA_MAXIMA = 10_000

MENSAJE_VALOR_AGRUPADO_GRANDE = (
    "Al agrupar los términos queda un número demasiado grande para esta herramienta."
)

# Lo mayor que produce un literal admitido: 100 cifras enteras y 100 decimales.
_NUMERADOR_MAXIMO = 10 ** (2 * DIGITOS_MAXIMOS)
_DENOMINADOR_MAXIMO = 10 ** DIGITOS_MAXIMOS


def validar_dimensiones(ecuaciones, variables):
    """Rechaza dimensiones sin recorrerlas ni construir estructuras proporcionales."""
    if type(ecuaciones) is not int or not 1 <= ecuaciones <= ECUACIONES_MAXIMAS:
        raise ValueError(f"Indica entre 1 y {ECUACIONES_MAXIMAS} ecuaciones.")
    if type(variables) is not int or not 1 <= variables <= VARIABLES_MAXIMAS:
        raise ValueError(f"Indica entre 1 y {VARIABLES_MAXIMAS} variables.")
    if ecuaciones * (variables + 1) > CELDAS_MAXIMAS:
        raise ValueError(
            f"La matriz aumentada admite hasta {CELDAS_MAXIMAS} celdas "
            "(ecuaciones × (variables + 1)). Reduce las dimensiones."
        )


def dimensiones_admitidas(ecuaciones, variables):
    """Para reconstrucción y GET: una estructura inválida se ignora."""
    try:
        validar_dimensiones(ecuaciones, variables)
    except ValueError:
        return False
    return True


def validar_longitud_sistema(texto):
    if len(texto) > LONGITUD_SISTEMA_MAXIMA:
        raise ValueError(
            f"El sistema admite hasta {LONGITUD_SISTEMA_MAXIMA} caracteres."
        )


def validar_valor_agrupado(valor):
    """Rechaza un coeficiente o término independiente mayor que un solo literal.

    Sumar términos semejantes o pasarlos de un lado a otro (1/p x1 + 1/q x1)
    no debe crear números que una celda de la matriz no admite.
    """
    if abs(valor.numerator) >= _NUMERADOR_MAXIMO or valor.denominator > _DENOMINADOR_MAXIMO:
        raise ValueError(MENSAJE_VALOR_AGRUPADO_GRANDE)
