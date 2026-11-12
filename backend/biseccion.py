"""Punto medio y selección manual del subintervalo (diapositivas 3 y 6)."""

from .funciones_reales import finito
from .metodos_cerrados import MAX_ITERACIONES, TOLERANCIA as PRECISION, preparar_intervalo
from .resultados_raices import ClasificacionRaices as Clasificacion


def biseccion(funcion, a, b, precision=PRECISION, max_iteraciones=MAX_ITERACIONES):
    inicial, precision, impedimento = preparar_intervalo(funcion, a, b, precision, max_iteraciones)
    a, b, fa, fb = (inicial[k] for k in ("a", "b", "fa", "fb"))
    filas = []

    def resultado(c, estado, mensaje, clasificacion=None):
        fc = funcion(c) if c is not None else None  # Verificación final independiente del valor guardado en la fila.
        convergio = estado in ("exacta", "longitud")
        clasificacion = clasificacion or (Clasificacion.RAIZ_APROXIMADA if convergio else Clasificacion.SIN_CONVERGENCIA)
        return {"clasificacion": clasificacion, "inicial": inicial, "max_iteraciones": max_iteraciones,
                "c": c, "fc": fc, "residuo": abs(fc) if fc is not None else None, "a": a, "b": b, "fa": fa, "fb": fb,
                "longitud": b - a, "precision": precision, "iteraciones": filas,
                "estado": estado, "convergio": convergio, "mensaje": mensaje}

    if impedimento:
        estado, clasificacion, mensaje = impedimento
        return resultado(None, estado, mensaje, clasificacion)

    if fa == 0 or fb == 0:
        c = a if fa == 0 else b
        a = b = c
        fa = fb = 0.
        return resultado(c, "exacta", "Raíz en un extremo: f(c) = 0.")
    anterior = None
    for i in range(1, max_iteraciones + 1):
        c = a + (b - a) / 2
        if c == a or c == b:
            return resultado(c, "estancamiento", "No converge a la precisión pedida: se alcanzó el límite de los números de máquina.")
        try:
            fc = funcion(c)
        except ValueError as error:
            return resultado(anterior, "evaluacion", str(error))
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
