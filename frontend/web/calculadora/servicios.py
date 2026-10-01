"""Capa de integración entre Django y el backend matemático existente."""

from fractions import Fraction

from .opciones_sistemas import metodos_a_resolver
from .presentacion_numerica import formatear_exacto
from backend.parser_sistemas import analizar_sistema
from backend.presupuesto_computacional import ESTIMADORES, combinar_estimaciones, perfil_numerico
from backend.presupuesto_sistemas import validar_dimensiones
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


def _leer_entrada(tipo_entrada, texto, matriz_aumentada):
    """(matriz aumentada, reescritas) de la entrada web, con el presupuesto de entrada aplicado."""
    reescritas = None
    if tipo_entrada == "sistema":
        matriz_inicial, reescritas = analizar_sistema(texto or "", limitar_entrada=True)
    elif tipo_entrada == "matriz":
        if matriz_aumentada is None:
            raise ValueError("La matriz aumentada no está completa.")
        matriz_inicial = matriz_aumentada
    else:
        raise ValueError("Selecciona un tipo de entrada válido.")

    validar_dimensiones(len(matriz_inicial), len(matriz_inicial[0]) - 1 if matriz_inicial else 0)
    return matriz_inicial, reescritas


def estimar_entrada_web(tipo_entrada, metodo, *, texto=None, matriz_aumentada=None):
    """Costo previsto de resolver la entrada, sin resolverla; «Comparar ambos» suma los dos métodos.

    Lee la entrada con el mismo presupuesto que `resolver_entrada_web`. Todavía
    no decide nada: ninguna entrada válida se rechaza por su costo.
    """
    matriz, _ = _leer_entrada(tipo_entrada, texto, matriz_aumentada)
    try:
        estimadores = [ESTIMADORES[clave] for clave in metodos_a_resolver(metodo)]
    except KeyError:
        raise ValueError("Selecciona un método de resolución válido.") from None

    filas, columnas = len(matriz), len(matriz[0])
    perfil = perfil_numerico(matriz)
    # Los pivotes solo se buscan en las columnas de coeficientes, como en los motores.
    return combinar_estimaciones(
        *(estimar(filas, columnas, columnas_pivote=columnas - 1, perfil=perfil) for estimar in estimadores),
        operacion=metodo,
    )


def resolver_entrada_web(
    tipo_entrada, metodo, *, texto=None, matriz_aumentada=None
):
    """Converge cualquier entrada web en una matriz y delega al backend.

    El texto pasa por el parser con presupuesto numérico; las ecuaciones que
    hubo que llevar a la forma estándar acompañan al procedimiento. La matriz
    llega ya validada: SistemaForm revisa cada celda antes de convertirla.
    """
    matriz_inicial, reescritas = _leer_entrada(tipo_entrada, texto, matriz_aumentada)

    try:
        _, resolver, _, _ = _RESOLVERS[metodo]
    except KeyError:
        raise ValueError("Selecciona un método de resolución válido.") from None

    presentado = presentar_resolucion(resolver(matriz_inicial), metodo, matriz_inicial)
    if tipo_entrada == "sistema":
        presentado["reescritas"] = reescritas
    return presentado


def presentar_resolucion(resultado, metodo, matriz_inicial):
    """Adapta a la plantilla un sistema ya resuelto por Gauss o Gauss-Jordan.

    Lo comparten Reducción por filas y Resolver Ax = b: el segundo resuelve
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
