"""Muestras para Plotly; la exploración no ejecuta el método numérico."""

from backend.funciones_reales import finito


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
            # No unir dos muestras si el tramo entre ellas cruza un hueco del dominio.
            if anterior is not None:
                funcion.rango(anterior, x)
        except ValueError:
            y = None
        puntos["x"].append(x)
        puntos["y"].append(y)
        anterior = x
    return puntos
