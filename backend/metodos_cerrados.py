"""Condiciones que comparten los métodos cerrados: intervalo, tolerancia y cambio de signo."""

from .funciones_reales import finito


TOLERANCIA = 0.0001
MAX_ITERACIONES = 200


def preparar_intervalo(funcion, a, b, tolerancia, max_iteraciones, magnitud="precisión"):
    """Validar la entrada y devolver a, b, la tolerancia, f(a) y f(b)."""
    a, b, tolerancia = finito(a), finito(b), finito(tolerancia)
    if a >= b:
        raise ValueError("El extremo a debe ser menor que b.")
    if not 0 < tolerancia <= TOLERANCIA:
        raise ValueError(f"La {magnitud} debe ser positiva y no mayor que 0.0001.")
    if type(max_iteraciones) is not int or not 1 <= max_iteraciones <= 1000:
        raise ValueError("El máximo de iteraciones debe ser un entero entre 1 y 1000.")
    finito(b - a)
    funcion.rango(a, b)
    return a, b, tolerancia, funcion(a), funcion(b)


def exigir_cambio_de_signo(fa, fb):
    # Se comparan signos: multiplicar f(a)·f(b) podría desbordarse o redondearse a cero.
    if (fa < 0) == (fb < 0):
        raise ValueError("Los extremos deben tener signos opuestos, o contener una raíz en un extremo.")
