"""Validación y piezas exactas que comparten los métodos y Matriz inversa."""

from fractions import Fraction

from backend.matrices import validar_matriz
from backend.seguridad_numerica import multiplicar_exacto, restar_exacto, validar_matriz_exacta


def preparar(a):
    """Valida una matriz cuadrada exacta y devuelve una copia con Fraction."""
    valida, mensaje = validar_matriz(a)
    if not valida:
        raise ValueError(mensaje)
    if len(a) != len(a[0]):
        raise ValueError(f"Solo las matrices cuadradas tienen determinante: A es {len(a)}×{len(a[0])}.")
    validar_matriz_exacta(a)
    return [[Fraction(v) for v in fila] for fila in a]


def producto(valores):
    """Multiplica valores usando la protección numérica común."""
    total = Fraction(1)
    for valor in valores:
        total = multiplicar_exacto(total, valor)
    return total


def directo_2x2(a):
    """Devuelve `ad`, `bc` y `determinante` = ad − bc de A = [[a, b], [c, d]].

    Es la única implementación de ad − bc: la usan Determinantes y la regla
    2×2 de Matriz inversa.
    """
    a = preparar(a)
    if len(a) != 2:
        raise ValueError("La fórmula directa ad − bc solo se aplica a matrices 2×2.")
    ad = multiplicar_exacto(a[0][0], a[1][1])
    bc = multiplicar_exacto(a[0][1], a[1][0])
    return {"ad": ad, "bc": bc, "determinante": restar_exacto(ad, bc)}


def determinante_desde_reduccion(pasos, diagonal):
    """Recupera det(A) de una reducción ya hecha (Gauss o Gauss-Jordan).

    La matriz final es triangular, así que su determinante es el producto de
    `diagonal`. Cada paso anota cómo cambió det: un intercambio lo multiplicó
    por −1 y dividir una fila entre su pivote lo dividió entre ese pivote.
    Multiplicar por esas correcciones deshace los cambios; los reemplazos no
    cambian det.
    """
    if any(v == 0 for v in diagonal):
        return Fraction(0)
    factores = [paso.get("correccion_determinante", 1) for paso in pasos]
    return producto([*diagonal, *factores])
