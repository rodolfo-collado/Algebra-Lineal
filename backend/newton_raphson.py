"""Newton-Raphson explícito con derivación automática y trazabilidad de cada tangente."""

from fractions import Fraction

from .derivacion_real import DerivadaReal
from .funciones_reales import finito
from .metodos_cerrados import MAX_ITERACIONES, TOLERANCIA
from .resultados_raices import ClasificacionRaices as Clasificacion


def newton_raphson(funcion, x0, tolerancia=TOLERANCIA, max_iteraciones=MAX_ITERACIONES):
    x0, tolerancia = finito(x0), finito(tolerancia)
    if not 0 < tolerancia <= TOLERANCIA:
        raise ValueError("La tolerancia debe ser positiva y no mayor que 0.0001.")
    if type(max_iteraciones) is not int or not 1 <= max_iteraciones <= 1000:
        raise ValueError("El máximo de iteraciones debe ser un entero entre 1 y 1000.")
    x, fx = x0, None
    derivada = intento_final = None
    filas, visitados = [], {x}

    def resultado(estado, mensaje):
        convergio = estado in ("exacta", "tolerancia")
        if convergio:
            clasificacion = Clasificacion.RAIZ_APROXIMADA
        elif not filas and estado in ("derivada", "dominio_inicial", "dominio_derivada", "derivacion"):
            clasificacion = Clasificacion.NO_APLICABLE
        else:
            clasificacion = Clasificacion.SIN_CONVERGENCIA
        verificado = finito(funcion(x)) if fx is not None else None
        return {"clasificacion": clasificacion, "derivada": derivada.texto if derivada else None,
                "x": x if verificado is not None else None, "fx": verificado, "x0": x0,
                "residuo": abs(verificado) if verificado is not None else None,
                "tolerancia": tolerancia, "max_iteraciones": max_iteraciones,
                "iteraciones": filas, "intento_final": intento_final, "estado": estado,
                "convergio": convergio, "mensaje": mensaje,
                "error_absoluto": filas[-1]["error_absoluto"] if filas else None}

    try:
        derivada = DerivadaReal(funcion)
    except (ValueError, ArithmeticError) as error:
        return resultado("derivacion", f"No se pudo obtener la derivada real de esta expresión. {error}")
    try:
        fx = funcion(x0)
    except ValueError as error:
        return resultado("dominio_inicial", str(error))

    if fx == 0:
        return resultado("exacta", "El punto inicial ya da f(x₀) = 0 en aritmética de máquina.")
    for i in range(1, max_iteraciones + 1):
        intento_final = {"i": i, "xn": x, "fxn": fx, "dfxn": None, "siguiente": None,
                         "fsiguiente": None, "residuo": None, "error_absoluto": None}
        try:
            dfx = finito(derivada(x))
        except (ValueError, ArithmeticError):
            return resultado("dominio_derivada", "La derivada no está definida o no es finita en la aproximación actual.")
        intento_final["dfxn"] = dfx
        if dfx == 0:
            return resultado("derivada", "La derivada es cero: la tangente no permite calcular otra aproximación.")
        try:
            # La resta racional evita desbordamientos intermedios y cancelación innecesaria.
            nuevo = finito(Fraction(x) - Fraction(fx) / Fraction(dfx))
            cambio = finito(abs(Fraction(nuevo) - Fraction(x)))
        except (ValueError, ArithmeticError):
            return resultado("divergencia", "La pendiente es demasiado pequeña respecto de f(x), o el salto excede el rango de máquina.")
        intento_final.update(siguiente=nuevo, error_absoluto=cambio)
        try:
            fnuevo = finito(funcion(nuevo))
        except (ValueError, ArithmeticError):
            return resultado("dominio", "El siguiente corte de la tangente sale del dominio o produce un valor no finito. Se conserva la última aproximación válida.")
        intento_final.update(fsiguiente=fnuevo, residuo=abs(fnuevo))
        filas.append(intento_final)
        intento_final = None
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
