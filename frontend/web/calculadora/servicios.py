"""Capa de integración entre Django y el backend matemático existente."""

from fractions import Fraction

from backend.matrices import formatear_fraccion
from backend.parser_sistemas import parsear_sistema
from backend.sistemas import (
    resolver_sistema_gauss,
    resolver_sistema_gauss_jordan,
)


_RESOLVERS = {
    "gauss": ("Gauss", resolver_sistema_gauss, "matriz_escalonada", "Matriz escalonada"),
    "gauss_jordan": (
        "Gauss-Jordan",
        resolver_sistema_gauss_jordan,
        "matriz_reducida",
        "Matriz reducida",
    ),
}


def formatear_matriz(matriz):
    """Convierte los valores exactos del backend a celdas legibles en HTML."""
    return [
        [formatear_fraccion(Fraction(valor)) for valor in fila]
        for fila in matriz
    ]


def adaptar_pasos(pasos):
    """Conserva los pasos del backend y adapta sus matrices para la plantilla."""
    return [
        {
            "numero": indice + 1,
            "operacion": paso["operacion"],
            "antes": formatear_matriz(paso["antes"]),
            "despues": formatear_matriz(paso["despues"]),
        }
        for indice, paso in enumerate(pasos)
    ]


def adaptar_sustitucion(pasos):
    """Prepara la sustitución ya calculada por el backend para mostrarla."""
    adaptados = []
    for paso in pasos:
        valor = formatear_fraccion(Fraction(paso["valor"]))
        expresion = paso["expresion"]
        texto = f"x{paso['variable']} = {valor}"
        if expresion != valor:
            texto = f"x{paso['variable']} = {expresion} = {valor}"
        adaptados.append(texto)

    return adaptados


def resolver_sistema_web(texto, metodo):
    """Parsea y resuelve un sistema delegando todo cálculo al backend."""
    try:
        nombre_metodo, resolver, clave_matriz, etiqueta_matriz = _RESOLVERS[metodo]
    except KeyError:
        raise ValueError("Selecciona un método de resolución válido.") from None

    matriz_inicial = parsear_sistema(texto)
    resultado = resolver(matriz_inicial)

    return {
        "metodo": nombre_metodo,
        "matriz_inicial": formatear_matriz(matriz_inicial),
        "pasos": adaptar_pasos(resultado["pasos"]),
        "matriz_final": formatear_matriz(resultado[clave_matriz]),
        "etiqueta_matriz": etiqueta_matriz,
        "mostrar_sistema_resultante": not resultado["solucion_directa"],
        "ecuaciones_resultantes": resultado["ecuaciones_resultantes"],
        "clasificacion": resultado["clasificacion"],
        "justificacion": resultado["justificacion"],
        "solucion_general": resultado["solucion_general"],
        "sustitucion": adaptar_sustitucion(
            resultado.get("pasos_sustitucion", [])
        ),
    }
