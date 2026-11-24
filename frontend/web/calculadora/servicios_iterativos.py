"""Ejemplos y presentación de Jacobi y Gauss-Seidel en Ax = b.

Los números de máquina (aproximaciones, cambio, residuo) viajan como float y la plantilla
los muestra con el filtro `flotante` del formato global; los coeficientes ingresados se
escriben exactos, como en el resto de Ax = b. Aquí no se calcula nada del método.
"""

from fractions import Fraction

from backend.sistemas_iterativos import METODOS, resolver_iterativo

from .presentacion_numerica import formatear_exacto
from .servicios_ecuaciones import incognitas

COMPARAR_ITERATIVOS = "comparar_iterativos"

# Word §1 y diapositiva 9. La práctica de la diapositiva 28 compara tres vueltas.
EJEMPLOS = {
    "clase": (
        "Ejemplo de clase · solución (1, 2, −1, 1)",
        ((10, -1, 2, 0), (-1, 11, -1, 3), (2, -1, 10, -1), (0, 3, -1, 8)),
        (6, 25, -11, 15),
    ),
    "diapositiva-28": (
        "Práctica de la diapositiva 28 · 3 iteraciones",
        ((8, -1, 1, 0), (-1, 10, -2, 1), (1, -2, 9, -1), (0, 1, -1, 7)),
        (8, 7, -4, 5),
    ),
    # Sin dominancia diagonal: las aproximaciones crecen hasta agotar el límite.
    "sin-dominancia": (
        "Sin dominancia diagonal · las aproximaciones crecen",
        ((1, 2), (3, 1)),
        (5, 5),
    ),
}


def lista_ejemplos():
    return [(clave, titulo) for clave, (titulo, *_datos) in EJEMPLOS.items()]


def iniciales_ejemplo(clave):
    if clave not in EJEMPLOS:
        return {}
    _titulo, a, b = EJEMPLOS[clave]
    inicial = {"filas": len(a), "columnas": len(a), "metodo": COMPARAR_ITERATIVOS}
    for i, fila in enumerate(a):
        inicial.update({f"celda_A_{i}_{j}": str(valor) for j, valor in enumerate(fila)})
        inicial[f"celda_b_{i}_0"] = str(b[i])
    if clave == "diapositiva-28":
        inicial["max_iteraciones"] = 3
    return inicial


def resolver_iterativos_web(entrada):
    """Uno o los dos métodos con el mismo x⁽⁰⁾, tolerancia y límite."""
    metodo = entrada["metodo"]
    metodos = dict(METODOS) if metodo == COMPARAR_ITERATIVOS else (metodo,)
    calculos = [
        resolver_iterativo(entrada["a"], entrada["b"], nombre, inicial=entrada["inicial"],
                           tolerancia=entrada["tolerancia"], max_iteraciones=entrada["max_iteraciones"])
        for nombre in metodos
    ]
    a = [[Fraction(valor) for valor in fila] for fila in entrada["a"]]
    b = [Fraction(valor) for valor in entrada["b"]]
    resultados = [_presentar(calculo, a, b) for calculo in calculos]
    primero = calculos[0]
    return {
        "metodos": resultados,
        "comparar": len(resultados) > 1,
        "titulo": _titulo_comparacion(calculos) if len(calculos) > 1 else resultados[0]["titulo"],
        "variables": resultados[0]["variables"],
        "tolerancia": float(primero.tolerancia),
        "limite": primero.limite,
        "inicial": primero.iteraciones[0].x,
        "dominancia": [
            {"fila": i, "diagonal": formatear_exacto(diagonal), "resto": formatear_exacto(resto),
             "cumple": diagonal > resto}
            for i, (diagonal, resto) in enumerate(primero.dominancia, 1)
        ],
        "filas_no_dominantes": primero.filas_no_dominantes,
    }


def _iteraciones(k):
    return "1 iteración" if k == 1 else f"{k} iteraciones"


def _frase(calculo):
    k = calculo.final.k
    if calculo.estado == "convergio":
        return f"converge en {_iteraciones(k)}"
    if calculo.estado == "limite":
        return f"no converge en {_iteraciones(k)}"
    return f"supera el rango numérico en la iteración {k + 1}"


def _titulo_comparacion(calculos):
    nombres = dict(METODOS)
    if all(c.estado == "convergio" for c in calculos):
        rapido, lento = sorted(calculos, key=lambda c: c.final.k)
        if rapido.final.k == lento.final.k:
            return f"Ambos convergen en {_iteraciones(rapido.final.k)}"
        return (f"{nombres[rapido.metodo]} converge en {rapido.final.k} y "
                f"{nombres[lento.metodo]} en {_iteraciones(lento.final.k)}")
    return "; ".join(f"{nombres[c.metodo]} {_frase(c)}" for c in calculos)


def _mensaje(calculo):
    final = calculo.final
    if calculo.estado == "convergio":
        if calculo.iteraciones[0].norma_residuo == 0 and final.k == 1:
            return "x⁽⁰⁾ ya satisface Ax = b: la iteración 1 lo confirma con cambio 0."
        return f"En la iteración {final.k}, el cambio máximo y el residuo son menores que la tolerancia."
    if calculo.estado == "rango":
        return (f"En la iteración {final.k + 1} se superó el rango numérico. "
                "Se muestra el último vector con valores finitos.")
    mensaje = "El cambio y el residuo no bajaron ambos de la tolerancia: se muestra la última aproximación."
    if final.k > 1 and final.cambio > calculo.iteraciones[1].cambio:
        mensaje += " El cambio máximo crece: las aproximaciones se alejan entre sí."
    return mensaje


def _termino_despejado(coeficiente):
    """−aᵢⱼxⱼ al pasar al otro lado: signo opuesto y el factor solo si |aᵢⱼ| ≠ 1."""
    magnitud = abs(coeficiente)
    texto = formatear_exacto(magnitud)
    factor = "" if magnitud == 1 else (texto if magnitud.denominator == 1 else f"({texto})")
    return ("+" if coeficiente < 0 else "−"), factor


def _presentar(calculo, a, b):
    variables = incognitas(len(a))
    filas = [{"k": paso.k, "x": paso.x, "cambio": paso.cambio, "norma": float(paso.norma_residuo)}
             for paso in calculo.iteraciones]
    # Sin JavaScript se lee la iteración 1; sistemas_iterativos.js sustituye después los valores.
    anterior, actual = filas[0]["x"], filas[min(1, len(filas) - 1)]["x"]
    despejes = []
    for i, despeje in enumerate(calculo.despejes):
        terminos = []
        for termino in despeje.terminos:
            signo, factor = _termino_despejado(a[i][termino.columna])
            terminos.append({"j": termino.columna, "variable": variables[termino.columna], "signo": signo,
                             "factor": factor, "origen": "nuevo" if termino.usa_nuevo else "anterior",
                             "valor": (actual if termino.usa_nuevo else anterior)[termino.columna]})
        despejes.append({"i": i, "variable": variables[i], "independiente": formatear_exacto(b[i]),
                         "diagonal": formatear_exacto(a[i][i]), "terminos": terminos, "valor": actual[i]})
    # r = b − Ax es exacto en el motor; Ax se lee como b − r.
    verificacion = [{"variable": variables[i], "ax": float(b[i] - r), "b": formatear_exacto(b[i]), "r": float(r)}
                    for i, r in enumerate(calculo.final.residuo)]
    return {
        "clave": calculo.metodo, "metodo": dict(METODOS)[calculo.metodo],
        "estado": calculo.estado, "frase": _frase(calculo), "mensaje": _mensaje(calculo),
        "titulo": f"{dict(METODOS)[calculo.metodo]} {_frase(calculo)}",
        "variables": variables, "filas": filas, "final": filas[-1],
        # Los mismos criterios estrictos y exactos del motor, para leerlos junto a ε.
        "cumple_cambio": calculo.final.cambio is not None and Fraction(calculo.final.cambio) < calculo.tolerancia,
        "cumple_residuo": calculo.final.norma_residuo < calculo.tolerancia,
        "despejes": despejes, "verificacion": verificacion,
    }
