from fractions import Fraction

from .matrices import (
    aplicar_gauss,
    aplicar_gauss_jordan,
    obtener_rango,
    validar_matriz
)


TIPO_SOLUCION_UNICA = "Consistente de solución única"
TIPO_SOLUCIONES_INFINITAS = "Consistente de soluciones infinitas"
TIPO_INCONSISTENTE = "Inconsistente"


def fila_contradictoria(fila, cantidad_incognitas):
    coeficientes_cero = all(
        fila[columna] == 0
        for columna in range(cantidad_incognitas)
    )
    return coeficientes_cero and fila[cantidad_incognitas] != 0


def obtener_tipo_sistema(matriz):
    es_valida, mensaje = validar_matriz(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    cantidad_incognitas = len(matriz[0]) - 1
    rango_coeficientes = obtener_rango(matriz, cantidad_incognitas)
    rango_aumentada = obtener_rango(matriz)
    hay_contradiccion = any(
        fila_contradictoria(fila, cantidad_incognitas)
        for fila in matriz
    )

    if hay_contradiccion or rango_coeficientes != rango_aumentada:
        return TIPO_INCONSISTENTE

    if rango_coeficientes == cantidad_incognitas:
        return TIPO_SOLUCION_UNICA

    return TIPO_SOLUCIONES_INFINITAS


def analizar_sistema(matriz):
    es_valida, mensaje = validar_matriz(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    tipo_sistema = obtener_tipo_sistema(matriz)
    if tipo_sistema == TIPO_INCONSISTENTE:
        return [f"{TIPO_INCONSISTENTE}.", "No tiene solución."]

    if tipo_sistema == TIPO_SOLUCION_UNICA:
        return [f"{TIPO_SOLUCION_UNICA}."]

    return [
        f"{TIPO_SOLUCIONES_INFINITAS}.",
        "Tiene infinitas soluciones."
    ]


def formatear_expresion_sustitucion(fila, columna, cantidad_incognitas):
    expresion = str(fila[cantidad_incognitas])
    for indice in range(columna + 1, cantidad_incognitas):
        coeficiente = fila[indice]
        if coeficiente == 0:
            continue

        expresion += f" - ({coeficiente})x{indice + 1}"

    return expresion


def sustitucion_regresiva(matriz_escalonada, pivotes, cantidad_incognitas=None):
    es_valida, mensaje = validar_matriz(matriz_escalonada)
    if not es_valida:
        raise ValueError(mensaje)

    cantidad_columnas = len(matriz_escalonada[0])
    if cantidad_incognitas is None:
        cantidad_incognitas = cantidad_columnas - 1

    if cantidad_incognitas < 0 or cantidad_incognitas >= cantidad_columnas:
        raise ValueError("La cantidad de incógnitas no es válida.")

    if len(pivotes) != cantidad_incognitas:
        raise ValueError(
            "La sustitución regresiva requiere un pivote para cada incógnita."
        )

    matriz = [
        [Fraction(numero) for numero in fila]
        for fila in matriz_escalonada
    ]
    soluciones = [Fraction(0) for _ in range(cantidad_incognitas)]
    pasos = []

    for fila, columna in reversed(pivotes):
        pivote = matriz[fila][columna]
        if pivote == 0:
            raise ValueError("No se puede dividir entre un pivote cero.")

        expresion = formatear_expresion_sustitucion(
            matriz[fila],
            columna,
            cantidad_incognitas
        )
        suma_conocida = sum(
            matriz[fila][indice] * soluciones[indice]
            for indice in range(columna + 1, cantidad_incognitas)
        )
        solucion = (
            matriz[fila][cantidad_incognitas] - suma_conocida
        ) / pivote
        soluciones[columna] = solucion
        pasos.append(
            f"Fila {fila + 1}: x{columna + 1} = {expresion} "
            f"= {solucion}"
        )

    return soluciones, pasos


def resolver_gauss(matriz):
    matriz_escalonada, pasos, pivotes = aplicar_gauss(matriz)
    analisis = analizar_sistema(matriz_escalonada)
    soluciones = None
    pasos_sustitucion = []

    if obtener_tipo_sistema(matriz_escalonada) == TIPO_SOLUCION_UNICA:
        soluciones, pasos_sustitucion = sustitucion_regresiva(
            matriz_escalonada,
            pivotes,
            len(matriz_escalonada[0]) - 1
        )

    return (
        matriz_escalonada,
        pasos,
        pivotes,
        analisis,
        soluciones,
        pasos_sustitucion
    )


def extraer_soluciones_gauss_jordan(matriz_reducida, pivotes):
    es_valida, mensaje = validar_matriz(matriz_reducida)
    if not es_valida:
        raise ValueError(mensaje)

    cantidad_incognitas = len(matriz_reducida[0]) - 1
    if len(pivotes) != cantidad_incognitas:
        raise ValueError("La matriz no tiene un pivote para cada incógnita.")

    soluciones = [Fraction(0) for _ in range(cantidad_incognitas)]
    for fila, columna in pivotes:
        soluciones[columna] = (
            Fraction(matriz_reducida[fila][cantidad_incognitas])
            / matriz_reducida[fila][columna]
        )

    return soluciones


def resolver_gauss_jordan(matriz):
    matriz_reducida, pasos, pivotes = aplicar_gauss_jordan(matriz)
    analisis = analizar_sistema(matriz_reducida)

    if obtener_tipo_sistema(matriz_reducida) == TIPO_SOLUCION_UNICA:
        soluciones = extraer_soluciones_gauss_jordan(
            matriz_reducida,
            pivotes
        )
        analisis.extend(
            f"x{indice} = {solucion}"
            for indice, solucion in enumerate(soluciones, start=1)
        )

    return matriz_reducida, pasos, analisis
