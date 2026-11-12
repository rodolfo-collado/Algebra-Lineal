"""Validación y condiciones de aplicabilidad de los métodos cerrados."""

from .funciones_reales import finito
from .resultados_raices import ClasificacionRaices as Clasificacion


TOLERANCIA = 0.0001
MAX_ITERACIONES = 200


def preparar_intervalo(funcion, a, b, tolerancia, max_iteraciones, magnitud="precisión"):
    a, b, tolerancia = finito(a), finito(b), finito(tolerancia)
    if a >= b:
        raise ValueError("El extremo a debe ser menor que b.")
    if not 0 < tolerancia <= TOLERANCIA:
        raise ValueError(f"La {magnitud} debe ser positiva y no mayor que 0.0001.")
    if type(max_iteraciones) is not int or not 1 <= max_iteraciones <= 1000:
        raise ValueError("El máximo de iteraciones debe ser un entero entre 1 y 1000.")
    finito(b - a)
    inicial = {"a": a, "b": b, "fa": None, "fb": None}
    for clave, x in (("fa", a), ("fb", b)):
        try:
            inicial[clave] = funcion(x)
        except ValueError:
            pass

    try:
        funcion.rango(a, b)
        fa, fb = inicial["fa"], inicial["fb"]
        if fa is None or fb is None:
            raise ValueError("No se pudo evaluar la función en ambos extremos.")
    except ValueError as error:
        return inicial, tolerancia, ("dominio", Clasificacion.NO_APLICABLE, str(error))

    # Comparar signos sin multiplicar evita desbordamiento y subdesbordamiento.
    if fa != 0 and fb != 0 and (fa < 0) == (fb < 0):
        estado = "sin_cambio_de_signo"
        mensaje = "Los extremos tienen el mismo signo. El método no puede continuar con estos extremos."
        if funcion.signo_estricto(a, b):
            return inicial, tolerancia, (estado, Clasificacion.SIN_RAICES_DEMOSTRADO,
                mensaje + " La expresión mantiene un signo estricto en todo el intervalo, lo que demuestra que no tiene raíces allí.")
        return inicial, tolerancia, (estado, Clasificacion.NO_APLICABLE,
            mensaje + " Este resultado deja abierta la existencia de raíces dentro del intervalo.")
    return inicial, tolerancia, None
