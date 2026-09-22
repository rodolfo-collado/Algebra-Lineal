"""Capa de integración entre Django y el backend matemático existente."""

from fractions import Fraction

from .presentacion_numerica import formatear_exacto
from backend.parser_sistemas import parsear_sistema
from backend.sistemas import (
    INCONSISTENTE,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
    resolver_sistema_gauss,
    resolver_sistema_gauss_jordan,
)


_CLASIFICACION_CLAVE = {
    SOLUCION_UNICA: "unica",
    SOLUCIONES_INFINITAS: "infinitas",
    INCONSISTENTE: "inconsistente",
}

_RESOLVERS = {
    "gauss": ("Gauss", resolver_sistema_gauss, "matriz_escalonada", "Matriz escalonada"),
    "gauss_jordan": (
        "Gauss-Jordan",
        resolver_sistema_gauss_jordan,
        "matriz_reducida",
        "Matriz reducida",
    ),
}


def clave_clasificacion(clasificacion):
    """Clave corta (unica, infinitas, inconsistente) que usan plantillas y CSS."""
    return _CLASIFICACION_CLAVE.get(clasificacion, "")


def formatear_matriz(matriz):
    """Convierte los valores exactos del backend a celdas legibles en HTML."""
    return [
        [formatear_exacto(Fraction(valor)) for valor in fila]
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
        valor = formatear_exacto(Fraction(paso["valor"]))
        expresion = paso["expresion"]
        texto = f"x{paso['variable']} = {valor}"
        if expresion != valor:
            texto = f"x{paso['variable']} = {expresion} = {valor}"
        adaptados.append(texto)

    return adaptados


def resolver_entrada_web(
    tipo_entrada, metodo, *, texto=None, matriz_aumentada=None
):
    """Converge cualquier entrada web en una matriz y delega al backend."""
    if tipo_entrada == "sistema":
        matriz_inicial = parsear_sistema(texto or "")
    elif tipo_entrada == "matriz":
        if matriz_aumentada is None:
            raise ValueError("La matriz aumentada no está completa.")
        matriz_inicial = matriz_aumentada
    else:
        raise ValueError("Selecciona un tipo de entrada válido.")

    try:
        _, resolver, _, _ = _RESOLVERS[metodo]
    except KeyError:
        raise ValueError("Selecciona un método de resolución válido.") from None

    return presentar_resolucion(resolver(matriz_inicial), metodo, matriz_inicial)


def presentar_resolucion(resultado, metodo, matriz_inicial):
    """Adapta a la plantilla un sistema ya resuelto por Gauss o Gauss-Jordan.

    Lo comparten Resolver un sistema y Resolver Ax = b: el segundo resuelve
    [A | b] con los mismos motores y muestra el procedimiento con las mismas
    plantillas, sin volver a calcular nada.
    """
    nombre_metodo, _, clave_matriz, etiqueta_matriz = _RESOLVERS[metodo]

    return {
        "metodo": nombre_metodo,
        "matriz_inicial": formatear_matriz(matriz_inicial),
        "pasos": adaptar_pasos(resultado["pasos"]),
        "matriz_final": formatear_matriz(resultado[clave_matriz]),
        "columnas_pivote": resultado["columnas_pivote"],
        "etiqueta_matriz": etiqueta_matriz,
        "mostrar_sistema_resultante": not resultado["solucion_directa"],
        "ecuaciones_resultantes": resultado["ecuaciones_resultantes"],
        "clasificacion": resultado["clasificacion"],
        "clasificacion_clave": clave_clasificacion(resultado["clasificacion"]),
        "justificacion": resultado["justificacion"],
        "solucion_general": resultado["solucion_general"],
        "sustitucion": adaptar_sustitucion(
            resultado.get("pasos_sustitucion", [])
        ),
    }


def resolver_sistema_web(texto, metodo):
    """Mantiene la entrada textual de P6 como una API pequeña y reutilizable."""
    return resolver_entrada_web("sistema", metodo, texto=texto)
