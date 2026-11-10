"""Newton-Raphson explícito con derivada manual y trazabilidad de cada tangente."""

from fractions import Fraction
import math

from .funciones_reales import finito
from .metodos_cerrados import MAX_ITERACIONES, TOLERANCIA


def newton_raphson(funcion, derivada, x0, tolerancia=TOLERANCIA, max_iteraciones=MAX_ITERACIONES):
    x, tolerancia = finito(x0), finito(tolerancia)
    if not 0 < tolerancia <= TOLERANCIA:
        raise ValueError("La tolerancia debe ser positiva y no mayor que 0.0001.")
    if type(max_iteraciones) is not int or not 1 <= max_iteraciones <= 1000:
        raise ValueError("El máximo de iteraciones debe ser un entero entre 1 y 1000.")
    fx = finito(funcion(x))
    filas, visitados = [], {x}

    def resultado(estado, mensaje):
        verificado = finito(funcion(x))
        return {"x": x, "fx": verificado, "residuo": abs(verificado), "x0": float(x0),
                "tolerancia": tolerancia, "iteraciones": filas, "estado": estado,
                "convergio": estado in ("exacta", "tolerancia"), "mensaje": mensaje,
                "error_absoluto": filas[-1]["error_absoluto"] if filas else None}

    if fx == 0:
        return resultado("exacta", "El punto inicial ya da f(x₀) = 0 en aritmética de máquina.")
    for i in range(1, max_iteraciones + 1):
        try:
            dfx = finito(derivada(x))
        except (ValueError, ArithmeticError):
            return resultado("dominio", "La derivada no está definida o no es finita en la aproximación actual.")
        if dfx == 0:
            return resultado("derivada", "La derivada es cero: la tangente no permite calcular otra aproximación.")
        try:
            # La resta racional evita desbordamientos intermedios y cancelación innecesaria.
            nuevo = finito(Fraction(x) - Fraction(fx) / Fraction(dfx))
            cambio = finito(abs(Fraction(nuevo) - Fraction(x)))
        except (ValueError, ArithmeticError):
            return resultado("divergencia", "La pendiente es demasiado pequeña respecto de f(x), o el salto excede el rango de máquina.")
        try:
            fnuevo = finito(funcion(nuevo))
        except (ValueError, ArithmeticError):
            return resultado("dominio", "El siguiente corte de la tangente sale del dominio o produce un valor no finito. Se conserva la última aproximación válida.")
        filas.append({"i": i, "xn": x, "fxn": fx, "dfxn": dfx, "siguiente": nuevo,
                      "fsiguiente": fnuevo, "residuo": abs(fnuevo), "error_absoluto": cambio})
        repetido = nuevo in visitados
        quieto = nuevo == x
        x, fx = nuevo, fnuevo
        if fx == 0:
            return resultado("exacta", "f(x) = 0 en aritmética de máquina.")
        if quieto:
            return resultado("estancamiento", "La máquina repite la aproximación sin obtener cero; no se declara convergencia.")
        if repetido:
            return resultado("oscilacion", "Se repite una aproximación anterior: el método entró en un ciclo sin convergencia.")
        if cambio <= tolerancia and abs(fx) <= tolerancia:
            return resultado("tolerancia", "El cambio y el residuo no superan la tolerancia solicitada.")
        visitados.add(x)
    return resultado("limite", "Se alcanzó el máximo de iteraciones sin cumplir el criterio de convergencia; puede haber divergencia u oscilación.")
