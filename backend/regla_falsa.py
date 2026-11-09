"""Regla falsa clásica con error absoluto aproximado y confirmación por signos."""

from fractions import Fraction
import math

from .funciones_reales import finito
from .metodos_cerrados import MAX_ITERACIONES, TOLERANCIA, exigir_cambio_de_signo, preparar_intervalo


def interseccion_secante(a, b, fa, fb):
    """Corte con el eje x de la recta que une (a, f(a)) y (b, f(b))."""
    try:
        # Interpolar los floats como racionales evita desbordamiento y cancelación intermedios.
        a, b, fa, fb = map(Fraction, (a, b, fa, fb))
        return finito((a * fb - b * fa) / (fb - fa))
    except (ArithmeticError, ValueError) as error:
        raise ValueError("No se puede calcular xr: la recta secante excede el rango de los números de máquina.") from error


def confirmar_cercania(funcion, xr, fxr, a, b, tolerancia):
    """Buscar un cambio de signo a no más de una tolerancia hacia el otro extremo."""
    # Tras la sustitución xr es un extremo; la raíz quedó hacia el extremo opuesto.
    prueba = min(xr + tolerancia, b) if xr == a else max(xr - tolerancia, a)
    # La suma redondeada puede alejar el punto más de la tolerancia solicitada.
    if abs(Fraction(prueba) - Fraction(xr)) > Fraction(tolerancia):
        prueba = math.nextafter(prueba, xr)
    f_prueba = funcion(prueba)
    return prueba, f_prueba, f_prueba == 0 or (f_prueba < 0) != (fxr < 0)


def regla_falsa(funcion, a, b, tolerancia=TOLERANCIA, max_iteraciones=MAX_ITERACIONES):
    a, b, tolerancia, fa, fb = preparar_intervalo(funcion, a, b, tolerancia, max_iteraciones, "tolerancia")
    filas = []

    def resultado(xr, estado, mensaje):
        fxr = funcion(xr)  # Verificación final independiente del valor guardado en la fila.
        ultima = filas[-1] if filas and filas[-1]["xr"] == xr else {}
        return {"xr": xr, "fxr": fxr, "residuo": abs(fxr), "a": a, "b": b, "fa": fa, "fb": fb,
                "longitud": b - a, "tolerancia": tolerancia, "iteraciones": filas, "estado": estado,
                "convergio": estado in ("exacta", "tolerancia"), "mensaje": mensaje,
                "error_absoluto": ultima.get("error_absoluto"), "prueba": ultima.get("prueba"),
                "f_prueba": ultima.get("f_prueba"), "extremo_fijo": ultima.get("extremo_fijo"),
                "veces_fijo": ultima.get("veces_fijo", 0),
                # Solo un cambio de signo confirmado acota la distancia de xr a una raíz.
                "cota": min(tolerancia, math.nextafter(abs(ultima["prueba"] - xr), math.inf))
                if estado == "tolerancia" else None}

    if fa == 0 or fb == 0:
        xr = a if fa == 0 else b
        a = b = xr
        fa = fb = 0.
        return resultado(xr, "exacta", "Raíz en un extremo: f(xr) = 0.")
    exigir_cambio_de_signo(fa, fb)
    anterior = fijo = None
    veces_fijo = 0
    for i in range(1, max_iteraciones + 1):
        xr = interseccion_secante(a, b, fa, fb)
        if not a < xr < b:
            # El redondeo llevó xr a un extremo: ya no hay un punto nuevo que evaluar.
            return resultado(min(max(xr, a), b), "maquina",
                             "No converge a la tolerancia pedida: se alcanzó el límite de los números de máquina.")
        fxr = funcion(xr)
        error = None if anterior is None else abs(xr - anterior)
        fila = {"i": i, "a": a, "b": b, "fa": fa, "fb": fb, "xr": xr, "fxr": fxr, "error_absoluto": error}
        filas.append(fila)
        if fxr == 0:
            sustituido = None
            a = b = xr
            fa = fb = fxr
        elif (fa < 0) == (fxr < 0):
            sustituido = "a"
            a, fa = xr, fxr
        else:
            sustituido = "b"
            b, fb = xr, fxr
        # Regla Falsa suele mover un solo extremo: se cuenta cuánto lleva quieto el otro.
        quieto = {"a": "b", "b": "a"}.get(sustituido)
        veces_fijo = 0 if quieto is None else veces_fijo + 1 if quieto == fijo else 1
        fijo = quieto
        cumple = error is not None and error <= tolerancia
        prueba = f_prueba = None
        confirmada = False
        if cumple and fxr != 0:
            prueba, f_prueba, confirmada = confirmar_cercania(funcion, xr, fxr, a, b, tolerancia)
        fila.update({"sustituido": sustituido, "nuevo_a": a, "nuevo_b": b, "extremo_fijo": fijo,
                     "veces_fijo": veces_fijo, "cumple_tolerancia": cumple, "prueba": prueba,
                     "f_prueba": f_prueba, "confirmada": confirmada})
        if fxr == 0:
            return resultado(xr, "exacta", "Raíz encontrada: f(xr) = 0 en aritmética de máquina.")
        if confirmada:
            return resultado(xr, "tolerancia", "Convergencia: Ea no supera la tolerancia y un cambio de signo confirma una raíz a esa distancia de xr.")
        anterior = xr
    if cumple:
        return resultado(xr, "estancamiento", "No converge: Ea ya no supera la tolerancia, pero ninguna raíz quedó confirmada a esa distancia de xr. El método está estancado.")
    return resultado(xr, "limite", "No converge a la tolerancia pedida: se alcanzó el máximo de iteraciones.")
