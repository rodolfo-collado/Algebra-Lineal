"""Interpretacion de una matriz aumentada como sistema de ecuaciones."""

from fractions import Fraction

from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import formatear_fraccion, validar_matriz_rectangular


def analizar_resultado_gauss_jordan(matriz, pivotes):
    cantidad_variables = len(matriz[0]) - 1

    # Fila del tipo 0 = k, con k distinto de 0
    for fila in matriz:
        coeficientes_en_cero = True
        for columna in range(cantidad_variables):
            if fila[columna] != 0:
                coeficientes_en_cero = False
                break

        if coeficientes_en_cero and fila[cantidad_variables] != 0:
            return [
                "Sistema incompatible.",
                "Apareció una fila del tipo 0 = k, con k distinto de 0.",
                "No tiene solución."
            ]

    if len(pivotes) < cantidad_variables:
        return [
            "Sistema compatible indeterminado.",
            "Tiene infinitas soluciones porque no hay pivote para cada variable."
        ]

    soluciones = [Fraction(0) for _ in range(cantidad_variables)]
    for fila, columna in pivotes:
        soluciones[columna] = matriz[fila][cantidad_variables]

    resultado = ["Sistema compatible determinado.", "Solución única:"]
    for indice, solucion in enumerate(soluciones):
        resultado.append(f"x{indice + 1} = {formatear_fraccion(solucion)}")

    return resultado


def resolver_gauss_jordan(matriz):
    es_valida, mensaje = validar_matriz_rectangular(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    # Los pivotes solo se buscan en las columnas de coeficientes.
    cantidad_variables = len(matriz[0]) - 1
    matriz_reducida, pasos, pivotes = aplicar_gauss_jordan(matriz, cantidad_variables)
    analisis = analizar_resultado_gauss_jordan(matriz_reducida, pivotes)

    return matriz_reducida, pasos, analisis
