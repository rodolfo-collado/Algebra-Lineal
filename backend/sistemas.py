"""Interpretacion de una matriz reducida como sistema de ecuaciones."""

from fractions import Fraction

from backend.gauss_jordan import aplicar_gauss_jordan, obtener_rango
from backend.matrices import formatear_numero_operacion


def analizar_resultado_gauss_jordan(matriz, pivotes, tipo_matriz):
    filas = len(matriz)
    columnas = len(matriz[0])

    if tipo_matriz == "cuadrada":
        rango = obtener_rango(matriz, columnas)
        if rango == filas:
            return ["La matriz cuadrada es invertible y se redujo a la identidad."]

        return [
            "La matriz cuadrada es singular.",
            "No se consiguieron pivotes en todas las columnas.",
            "Si se interpreta como sistema homogéneo, tiene infinitas soluciones."
        ]

    columnas_coeficientes = columnas - 1
    rango_coeficientes = obtener_rango(matriz, columnas_coeficientes)

    for fila in matriz:
        coeficientes_en_cero = True
        for columna in range(columnas_coeficientes):
            if fila[columna] != 0:
                coeficientes_en_cero = False
                break

        if coeficientes_en_cero and fila[-1] != 0:
            return [
                "Sistema incompatible.",
                "Apareció una fila del tipo 0 = k, con k distinto de 0.",
                "No tiene solución."
            ]

    if rango_coeficientes < columnas_coeficientes:
        return [
            "Sistema compatible indeterminado.",
            "Tiene infinitas soluciones porque no hay pivote para cada variable."
        ]

    soluciones = [Fraction(0) for _ in range(columnas_coeficientes)]
    for fila, columna in pivotes:
        if columna < columnas_coeficientes:
            soluciones[columna] = matriz[fila][-1]

    resultado = ["Sistema compatible determinado.", "Solución única:"]
    for indice, solucion in enumerate(soluciones):
        resultado.append(f"x{indice + 1} = {formatear_numero_operacion(solucion)}")

    return resultado


def resolver_gauss_jordan(matriz):
    matriz_reducida, pasos, pivotes, tipo_matriz = aplicar_gauss_jordan(matriz)
    analisis = analizar_resultado_gauss_jordan(matriz_reducida, pivotes, tipo_matriz)

    return matriz_reducida, pasos, analisis
