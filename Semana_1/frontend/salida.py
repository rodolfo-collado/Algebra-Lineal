from fractions import Fraction

from .terminal import (
    colorear_operacion,
    mostrar_advertencia,
    mostrar_error,
    mostrar_exito,
    mostrar_info,
    mostrar_titulo
)


def formatear_numero(numero):
    if isinstance(numero, Fraction):
        if numero.denominator == 1:
            return str(numero.numerator)
        return f"{numero.numerator}/{numero.denominator}"

    return str(numero)


def obtener_lineas_matriz(matriz):
    valores = [
        [formatear_numero(numero) for numero in fila]
        for fila in matriz
    ]
    anchos = [
        max(3, max(len(fila[indice]) for fila in valores))
        for indice in range(len(valores[0]))
    ]

    lineas = []
    for fila in valores:
        linea = "[ "
        for indice, numero in enumerate(fila):
            linea += f"{numero:>{anchos[indice]}} "
        lineas.append(linea + "]")
    return lineas


def imprimir_matriz(matriz):
    for linea in obtener_lineas_matriz(matriz):
        print(linea)


def imprimir_paso(paso):
    matriz_antes = obtener_lineas_matriz(paso["antes"])
    matriz_despues = obtener_lineas_matriz(paso["despues"])
    texto_operacion = f"  {paso['operacion']}  "
    operacion_coloreada = colorear_operacion(texto_operacion)
    alto = max(len(matriz_antes), len(matriz_despues))
    ancho_antes = max(len(linea) for linea in matriz_antes)
    ancho_operacion = len(texto_operacion)

    for indice in range(alto):
        linea_antes = (
            matriz_antes[indice]
            if indice < len(matriz_antes)
            else " " * ancho_antes
        )
        linea_despues = (
            matriz_despues[indice]
            if indice < len(matriz_despues)
            else ""
        )
        texto_operacion = (
            operacion_coloreada
            if indice == alto // 2
            else " " * ancho_operacion
        )
        print(f"{linea_antes:<{ancho_antes}}{texto_operacion}{linea_despues}")


def imprimir_pasos(pasos):
    if not pasos:
        mostrar_info("No fue necesario realizar operaciones por filas.")
        return

    mostrar_titulo("\n==== Pasos realizados ====\n")
    for indice, paso in enumerate(pasos, start=1):
        print(f"Paso {indice}:")
        imprimir_paso(paso)
        print()


def mostrar_analisis(analisis):
    mostrar_titulo("\n==== Análisis ====")
    for linea in analisis:
        if linea.startswith("Consistente de solución única"):
            mostrar_exito(linea)
        elif linea.startswith("Consistente de soluciones infinitas"):
            mostrar_advertencia(linea)
        elif linea.startswith("Inconsistente") or linea.startswith("No tiene"):
            mostrar_error(linea)
        else:
            print(linea)


def mostrar_soluciones(soluciones):
    if soluciones is None:
        return

    mostrar_titulo("\n==== Soluciones ====")
    for indice, solucion in enumerate(soluciones, start=1):
        print(f"x{indice} = {formatear_numero(solucion)}")
