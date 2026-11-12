"""Método de la secante explícito: dos aproximaciones, la recta que las une y su corte con el eje x.

xₙ₊₁ = xₙ − f(xₙ)·(xₙ − xₙ₋₁) / [f(xₙ) − f(xₙ₋₁)]. No exige cambio de signo: x₀ y x₁ no son
extremos de un intervalo, solo los dos primeros puntos de la recta.
"""

from fractions import Fraction

from .funciones_reales import finito
from .metodos_cerrados import MAX_ITERACIONES, TOLERANCIA
from .resultados_raices import ClasificacionRaices as Clasificacion

# Por debajo de esta fracción de |f| la diferencia f(xₙ) − f(xₙ₋₁) es del orden del redondeo de
# las evaluaciones (unas miles de ulp): la pendiente de la secante ya no significa nada.
DENOMINADOR_RELATIVO = 1e-12


def _flotante(valor):
    """Cifra para mostrar; None si no cabe en un float (solo afecta a la lectura)."""
    try:
        return finito(valor)
    except (ValueError, ArithmeticError):
        return None


def secante(funcion, x0, x1, tolerancia=TOLERANCIA, max_iteraciones=MAX_ITERACIONES):
    x0, x1, tolerancia = finito(x0), finito(x1), finito(tolerancia)
    if x0 == x1:
        raise ValueError("x₀ y x₁ deben ser distintos: la secante necesita dos puntos.")
    if not 0 < tolerancia <= TOLERANCIA:
        raise ValueError("La tolerancia debe ser positiva y no mayor que 0.0001.")
    if type(max_iteraciones) is not int or not 1 <= max_iteraciones <= 1000:
        raise ValueError("El máximo de iteraciones debe ser un entero entre 1 y 1000.")
    x, fx = x1, None
    filas, intento_final = [], None

    def resultado(estado, mensaje):
        convergio = estado in ("exacta", "tolerancia")
        if convergio:
            clasificacion = Clasificacion.RAIZ_APROXIMADA
        elif not filas and estado in ("dominio_inicial", "denominador", "denominador_pequeno"):
            clasificacion = Clasificacion.NO_APLICABLE
        else:
            clasificacion = Clasificacion.SIN_CONVERGENCIA
        verificado = finito(funcion(x)) if fx is not None else None
        return {"clasificacion": clasificacion, "x": x if verificado is not None else None,
                "fx": verificado, "x0": x0, "x1": x1,
                "residuo": abs(verificado) if verificado is not None else None,
                "tolerancia": tolerancia, "max_iteraciones": max_iteraciones,
                "iteraciones": filas, "intento_final": intento_final, "estado": estado,
                "convergio": convergio, "mensaje": mensaje,
                "error_absoluto": filas[-1]["error_absoluto"] if filas else None}

    evaluaciones = []
    for nombre, punto in (("x₀", x0), ("x₁", x1)):
        try:
            evaluaciones.append(finito(funcion(punto)))
        except (ValueError, ArithmeticError) as error:
            return resultado("dominio_inicial", f"No se puede evaluar f({nombre}). {error}")
    xa, fa = x0, evaluaciones[0]
    fx = evaluaciones[1]
    if fx == 0:
        return resultado("exacta", "El punto x₁ ya da f(x₁) = 0 en aritmética de máquina.")
    if fa == 0:
        x, fx = x0, fa
        return resultado("exacta", "El punto x₀ ya da f(x₀) = 0 en aritmética de máquina.")
    visitados = {x0, x1}

    for i in range(1, max_iteraciones + 1):
        intento_final = {"i": i, "anterior": xa, "fanterior": fa, "actual": x, "factual": fx,
                         "numerador": None, "denominador": None, "siguiente": None,
                         "fsiguiente": None, "residuo": None, "error_absoluto": None}
        # Aritmética racional: la diferencia y el producto son exactos; solo el resultado se redondea.
        denominador = Fraction(fx) - Fraction(fa)
        numerador = Fraction(fx) * (Fraction(x) - Fraction(xa))
        intento_final.update(numerador=_flotante(numerador), denominador=_flotante(denominador))
        if denominador == 0:
            return resultado("denominador", "f(xₙ) − f(xₙ₋₁) = 0: la secante es horizontal y no corta el eje x.")
        if abs(denominador) <= DENOMINADOR_RELATIVO * max(abs(Fraction(fa)), abs(Fraction(fx))):
            return resultado("denominador_pequeno", "f(xₙ) − f(xₙ₋₁) es casi nulo frente a f: la pendiente de la "
                                                     "secante queda dominada por el redondeo y el paso no es fiable.")
        try:
            nuevo = finito(Fraction(x) - numerador / denominador)
            cambio = finito(abs(Fraction(nuevo) - Fraction(x)))
        except (ValueError, ArithmeticError):
            return resultado("divergencia", "La secante es casi horizontal: su corte con el eje x excede el rango de máquina.")
        intento_final.update(siguiente=nuevo, error_absoluto=cambio)
        try:
            fnuevo = finito(funcion(nuevo))
        except (ValueError, ArithmeticError):
            return resultado("dominio", "El corte de la secante sale del dominio o produce un valor no finito. Se conserva la última aproximación válida.")
        intento_final.update(fsiguiente=fnuevo, residuo=abs(fnuevo))
        filas.append(intento_final)
        intento_final = None
        repetido = nuevo in visitados
        quieto = nuevo == x
        # Se desplazan los dos puntos: xₙ₋₁ ← xₙ y xₙ ← xₙ₊₁.
        xa, fa, x, fx = x, fx, nuevo, fnuevo
        if fx == 0:
            return resultado("exacta", "f(x) = 0 en aritmética de máquina.")
        if quieto:
            return resultado("estancamiento", "La máquina repite la aproximación sin obtener cero; no se declara convergencia.")
        if repetido:
            return resultado("oscilacion", "Se repite una aproximación anterior: el método entró en un ciclo sin convergencia.")
        # Un cambio pequeño no basta: el residuo también debe cumplir la tolerancia.
        if cambio <= tolerancia and abs(fx) <= tolerancia:
            return resultado("tolerancia", "El cambio y el residuo no superan la tolerancia solicitada.")
        visitados.add(x)
    return resultado("limite", "Se alcanzó el máximo de iteraciones sin cumplir el criterio de convergencia; puede haber divergencia u oscilación.")
