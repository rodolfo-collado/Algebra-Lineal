"""Costo previsto de cada método, sin calcular el determinante ni generar menores."""

from backend.presupuesto_computacional import Estimacion, estimar_gauss, perfil_numerico

from .cofactores import MENSAJE_ORDEN_MAXIMO, ORDEN_MAXIMO_COFACTORES


def estimar_determinante(a, metodo):
    """Cota del cálculo y del procedimiento conservado para A con el método pedido.

    Cofactores cuenta el árbol completo de menores (crece como n!) y rechaza
    más de ORDEN_MAXIMO_COFACTORES; LU y reducción usan la cota de Gauss más
    una corrección por paso. Usa el factor numérico de Gauss como referencia
    del tamaño de los números.
    """
    n = len(a)
    base = estimar_gauss(n, n, perfil=perfil_numerico(a))
    factor = base.factor_numerico
    if metodo == "cofactores":
        if n > ORDEN_MAXIMO_COFACTORES:
            raise ValueError(MENSAJE_ORDEN_MAXIMO)
        # Por nivel k: k menores de (k − 1)², 3 operaciones y unos 6 textos por término.
        nodos, operaciones, celdas = 1, 0, 1
        for k in range(2, n + 1):
            nodos, operaciones, celdas = 1 + k * nodos, k * (operaciones + 3), k * (celdas + (k - 1) ** 2 + 6)
        return Estimacion("cofactores", (n, n), nodos, operaciones * factor, celdas * factor, factor)
    if metodo in ("directo_2x2", "sarrus"):
        return Estimacion(metodo, (n, n), 6, 24 * factor, 36 * factor, factor)
    return Estimacion(metodo, (n, n), base.pasos, base.calculo + (n + base.pasos) * factor,
                      base.procedimiento + 3 * n * n, factor)
