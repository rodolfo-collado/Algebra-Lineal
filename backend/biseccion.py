"""Punto medio y selección manual del subintervalo (diapositivas 3 y 6)."""

from .funciones_reales import finito
from .metodos_cerrados import MAX_ITERACIONES, TOLERANCIA as PRECISION, exigir_cambio_de_signo, preparar_intervalo


def biseccion(funcion, a, b, precision=PRECISION, max_iteraciones=MAX_ITERACIONES):
    a, b, precision, fa, fb = preparar_intervalo(funcion, a, b, precision, max_iteraciones)
    filas = []

    def resultado(c, estado, mensaje):
        fc = funcion(c)  # Verificación final independiente del valor guardado en la fila.
        return {"c": c, "fc": fc, "a": a, "b": b, "fa": fa, "fb": fb,
                "longitud": b - a, "precision": precision, "iteraciones": filas,
                "estado": estado, "convergio": estado in ("exacta", "longitud"), "mensaje": mensaje}

    if fa == 0 or fb == 0:
        c = a if fa == 0 else b
        a = b = c
        fa = fb = 0.
        return resultado(c, "exacta", "Raíz en un extremo: f(c) = 0.")
    exigir_cambio_de_signo(fa, fb)
    anterior = None
    for i in range(1, max_iteraciones + 1):
        c = a + (b - a) / 2
        if c == a or c == b:
            return resultado(c, "estancamiento", "No converge a la precisión pedida: se alcanzó el límite de los números de máquina.")
        fc = funcion(c)
        error = abs((c - anterior) / c) * 100 if anterior is not None and c != 0 else None
        if error is not None:
            try:
                error = finito(error)
            except ValueError:
                error = None
        fila = {"i": i, "a": a, "b": b, "c": c, "fa": fa, "fb": fb, "fc": fc,
                "error_relativo": error}
        filas.append(fila)
        if fc == 0:
            a = b = c
            fa = fb = fc
        elif (fa < 0) != (fc < 0):
            b, fb = c, fc
        else:
            a, fa = c, fc
        fila.update({"nuevo_a": a, "nuevo_b": b, "longitud": b - a})
        if fc == 0:
            return resultado(c, "exacta", "Raíz encontrada: f(c) = 0 en aritmética de máquina.")
        if b - a < precision:
            return resultado(c, "longitud", "Convergencia por longitud del intervalo, con dominio y cambio de signo verificados.")
        anterior = c
    return resultado(c, "limite", "No converge a la precisión pedida: se alcanzó el máximo de iteraciones.")
