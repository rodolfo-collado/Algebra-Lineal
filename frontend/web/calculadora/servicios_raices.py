"""Muestras para Plotly; la exploración no ejecuta el método numérico."""

from backend.funciones_reales import finito


def verificacion_inicial(inicial):
    def signo(y):
        return "positivo" if y > 0 else "negativo" if y < 0 else "cero"

    return {**inicial, "signo_a": signo(inicial["fa"]), "signo_b": signo(inicial["fb"])}


def muestrear(funcion, a, b):
    a, b = finito(a), finito(b)
    if a >= b:
        raise ValueError("El extremo a debe ser menor que b.")
    ancho = finito(b - a)
    puntos = {"x": [], "y": []}
    anterior = None
    for i in range(801):
        x = a + ancho * (i / 800)
        try:
            y = funcion(x)
        except ValueError:
            y = anterior = None
        else:
            previo, anterior = anterior, x
            if previo is not None:
                # No unir muestras válidas si el tramo entre ellas puede cruzar un hueco.
                try:
                    funcion.rango(previo, x)
                except ValueError:
                    y = None
        puntos["x"].append(x)
        puntos["y"].append(y)
    return puntos
