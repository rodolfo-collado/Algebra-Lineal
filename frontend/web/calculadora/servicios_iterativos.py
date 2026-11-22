"""Ejemplos y presentación de Jacobi y Gauss-Seidel en Ax = b."""

from fractions import Fraction
from math import ceil, floor, log10

from backend.sistemas_iterativos import METODOS, resolver_iterativo

from .servicios_ecuaciones import incognitas

COMPARAR_ITERATIVOS = "comparar_iterativos"

# Word §1 y diapositiva 9. La práctica de la diapositiva 28 compara tres vueltas.
EJEMPLOS = {
    "clase": (
        ((10, -1, 2, 0), (-1, 11, -1, 3), (2, -1, 10, -1), (0, 3, -1, 8)),
        (6, 25, -11, 15),
    ),
    "diapositiva-28": (
        ((8, -1, 1, 0), (-1, 10, -2, 1), (1, -2, 9, -1), (0, 1, -1, 7)),
        (8, 7, -4, 5),
    ),
}


def iniciales_ejemplo(clave):
    if clave not in EJEMPLOS:
        return {}
    a, b = EJEMPLOS[clave]
    inicial = {"filas": len(a), "columnas": len(a), "metodo": COMPARAR_ITERATIVOS}
    for i, fila in enumerate(a):
        inicial.update({f"celda_A_{i}_{j}": str(valor) for j, valor in enumerate(fila)})
        inicial[f"celda_b_{i}_0"] = str(b[i])
    if clave == "diapositiva-28":
        inicial["max_iteraciones"] = 3
    return inicial


def resolver_iterativos_web(entrada):
    metodo = entrada["metodo"]
    metodos = dict(METODOS) if metodo == COMPARAR_ITERATIVOS else (metodo,)
    return [
        _presentar(resolver_iterativo(
            entrada["a"], entrada["b"], nombre, inicial=entrada["inicial"],
            tolerancia=entrada["tolerancia"], max_iteraciones=entrada["max_iteraciones"],
        ))
        for nombre in metodos
    ]


def _numero(valor):
    return format(valor, ".10g").replace("-", "−")


def _presentar(calculo):
    variables = incognitas(len(calculo.final.x))
    filas = [
        {"k": paso.k, "x": [_numero(x) for x in paso.x],
         "cambio": _numero(paso.cambio) if paso.cambio is not None else "—",
         "norma": _numero(paso.norma_residuo)}
        for paso in calculo.iteraciones
    ]
    activa = filas[min(1, calculo.final.k)]
    desarrollo = []
    for i, despeje in enumerate(calculo.despejes):
        terminos = [
            {"j": t.columna, "variable": variables[t.columna],
             "signo": "+" if t.coeficiente < 0 else "−",
             "factor": "" if abs(t.coeficiente) == 1 else f"{_numero(abs(t.coeficiente))}·",
             "origen": "nueva" if t.usa_nuevo else "anterior",
             "valor": (activa if t.usa_nuevo else filas[0])["x"][t.columna]}
            for t in despeje.terminos
        ]
        desarrollo.append({
            "variable": variables[i], "valor": activa["x"][i], "independiente": _numero(despeje.independiente),
            "diagonal": _numero(despeje.diagonal), "terminos": terminos,
        })
    mensajes = {
        "convergio": "Convergió. El cambio máximo y el residuo quedaron por debajo de la tolerancia.",
        "limite": f"No convergió en {calculo.limite} iteraciones. Se muestra la última aproximación.",
        "rango": f"En la iteración {calculo.final.k + 1} se superó el rango numérico. "
                 "Se muestra el último vector con valores finitos.",
    }
    return {
        "clave": calculo.metodo, "metodo": dict(METODOS)[calculo.metodo],
        "estado": calculo.estado, "mensaje": mensajes[calculo.estado],
        "tolerancia": _numero(calculo.tolerancia),
        "filas_no_dominantes": calculo.filas_no_dominantes,
        "variables": variables, "filas": filas, "final": filas[-1],
        "residuo_final": [_numero(ri) for ri in calculo.final.residuo],
        "desarrollo": desarrollo, "activa": activa,
        "grafica": _grafica(calculo.iteraciones),
    }


def _orden_decimal(valor):
    if isinstance(valor, Fraction):
        return log10(valor.numerator) - log10(valor.denominator)
    return log10(valor)


def _grafica(iteraciones):
    if len(iteraciones) < 3:
        return None

    cambio = [paso.cambio for paso in iteraciones]
    residuo = [paso.norma_residuo for paso in iteraciones]
    ordenes = [_orden_decimal(valor) for valor in cambio + residuo if valor is not None and valor > 0]
    if not ordenes:
        return None

    menor = floor(min(ordenes))
    mayor = max(ceil(max(ordenes)), menor + 1)
    hay_ceros = 0 in cambio or 0 in residuo

    def puntos(serie):
        pares = []
        for k, valor in enumerate(serie):
            if valor is None:
                continue
            x = 100 + 451 * k / (len(serie) - 1)
            y = 150 if valor == 0 else 126 - 108 * (_orden_decimal(valor) - menor) / (mayor - menor)
            pares.append(f"{x:.2f},{y:.2f}")
        return " ".join(pares)

    return {
        "cambio": puntos(cambio), "residuo": puntos(residuo),
        "superior": f"1e{mayor}", "inferior": f"1e{menor}",
        "ceros": hay_ceros, "ultima": iteraciones[-1].k,
    }
