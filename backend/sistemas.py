"""Interpretacion explicita de una matriz aumentada como sistema de ecuaciones."""

from fractions import Fraction

from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import validar_matriz_rectangular

SOLUCION_UNICA = "Consistente de solución única"
SOLUCIONES_INFINITAS = "Consistente de soluciones infinitas"
INCONSISTENTE = "Inconsistente"


def contar_variables(matriz_aumentada):
    return len(matriz_aumentada[0]) - 1


def validar_matriz_aumentada(matriz_aumentada):
    """Devuelve (es_valida, mensaje). Hacen falta coeficientes y una columna final."""
    es_valida, mensaje = validar_matriz_rectangular(matriz_aumentada)
    if not es_valida:
        return False, mensaje

    if contar_variables(matriz_aumentada) < 1:
        return False, (
            "Error: Una matriz aumentada necesita al menos una columna de "
            "coeficientes y una de términos independientes."
        )

    return True, ""


def tiene_fila_inconsistente(matriz_reducida, cantidad_variables):
    # Fila del tipo 0 = k, con k distinto de 0
    for fila in matriz_reducida:
        coeficientes_en_cero = True
        for columna in range(cantidad_variables):
            if fila[columna] != 0:
                coeficientes_en_cero = False
                break

        if coeficientes_en_cero and fila[cantidad_variables] != 0:
            return True

    return False


def clasificar_sistema(matriz_reducida, pivotes, cantidad_variables):
    if tiene_fila_inconsistente(matriz_reducida, cantidad_variables):
        return INCONSISTENTE

    # Sin un pivote por variable quedan variables sin determinar.
    if len(pivotes) < cantidad_variables:
        return SOLUCIONES_INFINITAS

    return SOLUCION_UNICA


def obtener_soluciones(matriz_reducida, pivotes, cantidad_variables):
    """Solo tiene sentido cuando cada variable tiene su pivote."""
    soluciones = [Fraction(0) for _ in range(cantidad_variables)]

    for fila, columna in pivotes:
        soluciones[columna] = matriz_reducida[fila][cantidad_variables]

    return soluciones


def resolver_sistema(matriz_aumentada):
    """Resuelve el sistema tomando la ultima columna como terminos independientes.

    Devuelve un diccionario con la matriz reducida, los pasos, la clasificacion
    y las soluciones (vacias si no hay solucion unica).
    """
    es_valida, mensaje = validar_matriz_aumentada(matriz_aumentada)
    if not es_valida:
        raise ValueError(mensaje)

    # Los pivotes solo se buscan en las columnas de coeficientes.
    cantidad_variables = contar_variables(matriz_aumentada)
    matriz_reducida, pasos, pivotes = aplicar_gauss_jordan(
        matriz_aumentada, cantidad_variables
    )
    clasificacion = clasificar_sistema(matriz_reducida, pivotes, cantidad_variables)

    soluciones = []
    if clasificacion == SOLUCION_UNICA:
        soluciones = obtener_soluciones(matriz_reducida, pivotes, cantidad_variables)

    return {
        "matriz_reducida": matriz_reducida,
        "pasos": pasos,
        "clasificacion": clasificacion,
        "soluciones": soluciones
    }
