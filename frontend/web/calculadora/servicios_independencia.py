"""Presentación de una resolución exacta de independencia lineal."""

import re

from backend.expresiones import crear_expresion, formatear_expresion

from .servicios import adaptar_pasos, formatear_matriz
from .servicios_matrices import subindice
from .servicios_vectores import termino_combinacion, texto_vector

_INDICE = re.compile(r"([αvF])([0-9]+)")
_VECTOR_NULO = "𝟎"
_VECTOR_COEFICIENTES = "𝛂"


def _alfa(indice):
    return f"α{subindice(indice)}"


def _vector(indice):
    return f"v{subindice(indice)}"


def _subindices(texto):
    return _INDICE.sub(lambda simbolo: simbolo[1] + subindice(int(simbolo[2])), texto)


def _combinar_simbolicamente(coeficientes):
    return _subindices(formatear_expresion(crear_expresion(0, coeficientes), "v"))


def _presentar_relacion(relacion, vectores):
    terminos = {
        indice: coeficiente
        for indice, coeficiente in enumerate(relacion["coeficientes"], 1)
        if coeficiente
    }

    verificacion = "".join(
        termino_combinacion(coeficiente, texto_vector(vectores[indice - 1]), posicion == 0)
        for posicion, (indice, coeficiente) in enumerate(terminos.items())
    )
    despeje = None
    if relacion["combinacion"]:
        despeje = f"{_vector(relacion['vector_despejado'])} = {_combinar_simbolicamente(relacion['combinacion'])}"

    return {
        "igualdad": f"{_combinar_simbolicamente(terminos)} = {_VECTOR_NULO}",
        "despeje": despeje,
        "asignacion": ", ".join(
            f"{_alfa(variable)} = {valor}" for variable, valor in relacion["asignacion_libres"].items()
        ),
        "coeficientes": texto_vector(relacion["coeficientes"]),
        "verificacion": f"{verificacion} = {texto_vector(relacion['verificacion'])}",
    }


def presentar_independencia(resolucion):
    sistema = resolucion["sistema"]
    vectores = resolucion["vectores"]
    indices = range(1, len(vectores) + 1)
    planteamiento = " + ".join(f"{_alfa(i)}{_vector(i)}" for i in indices)
    pasos = adaptar_pasos(sistema["pasos"])
    for paso in pasos:
        paso["operacion"] = _subindices(paso["operacion"])
    return {
        "planteamiento": f"{planteamiento} = {_VECTOR_NULO}",
        "vector_nulo": _VECTOR_NULO,
        "vector_coeficientes": _VECTOR_COEFICIENTES,
        "columnas": " ".join(_vector(i) for i in indices),
        "cantidad": len(vectores),
        "rango": resolucion["rango"],
        "es_independiente": resolucion["es_independiente"],
        "pivotes": ", ".join(map(str, sistema["columnas_pivote"])),
        "variables_libres": ", ".join(_alfa(i) for i in sistema["variables_libres"]),
        "cantidad_libres": len(sistema["variables_libres"]),
        "matriz_aumentada": formatear_matriz(resolucion["matriz_aumentada"]),
        "matriz_reducida": formatear_matriz(sistema["matriz_reducida"]),
        "columnas_pivote": sistema["columnas_pivote"],
        "ecuaciones": [_subindices(linea) for linea in resolucion["ecuaciones"]],
        "solucion": [_subindices(linea) for linea in sistema["solucion_general"]],
        "pasos": pasos,
        "relacion": _presentar_relacion(resolucion["relacion"], vectores) if resolucion["relacion"] else None,
    }
