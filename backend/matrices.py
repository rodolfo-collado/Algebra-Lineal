"""Utilidades generales sobre matrices, independientes de cualquier algoritmo."""

import random
from fractions import Fraction


def generar_matriz(cantidad_filas, cantidad_columnas):
    matriz = []

    # Ciclo para generar la matriz
    for _ in range(cantidad_filas):
        fila = []
        for _ in range(cantidad_columnas):
            fila.append(random.randint(0, 20))
        matriz.append(fila)

    return matriz


def copiar_matriz(matriz):
    copia = []

    for fila in matriz:
        copia.append(fila.copy())

    return copia


def convertir_matriz_a_fracciones(matriz):
    matriz_fracciones = []

    for fila in matriz:
        nueva_fila = []
        for numero in fila:
            nueva_fila.append(Fraction(numero))
        matriz_fracciones.append(nueva_fila)

    return matriz_fracciones


def es_matriz_rectangular(matriz):
    cantidad_columnas = len(matriz[0])

    for fila in matriz:
        if len(fila) != cantidad_columnas:
            return False

    return True


def formatear_numero_operacion(numero):
    if numero.denominator == 1:
        return str(numero.numerator)
    return f"{numero.numerator}/{numero.denominator}"
