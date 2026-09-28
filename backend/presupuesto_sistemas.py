"""Presupuesto de entrada de Resolver un sistema (web y aplicación desktop).

El procedimiento guarda dos matrices por operación de fila y las convierte a
HTML. Por eso el límite es menor que el de las operaciones básicas de matrices:
admite un sistema cuadrado de 10 variables y rectangulares de hasta 120 celdas.
Con CSRF y las cuatro opciones de resultado, el POST usa 130 campos (de 1000).
"""

ECUACIONES_MAXIMAS = 12
VARIABLES_MAXIMAS = 12
CELDAS_MAXIMAS = 120
LONGITUD_SISTEMA_MAXIMA = 10_000


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
