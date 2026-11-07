"""Geometría acotada para dibujar; los extremos y pertenencia siguen siendo exactos."""

from fractions import Fraction
from .intervalos import contiene


def datos_recta(recta, punto=None):
    extremos = [v for i in recta.intervalos for v in (i.inferior,i.superior) if v is not None]
    minimo, maximo = (min(extremos),max(extremos)) if extremos else (Fraction(-1),Fraction(1))
    margen = (maximo - minimo) / 4 if maximo != minimo else Fraction(1)
    minimo -= margen
    maximo += margen
    def posicion(valor, infinito):
        return infinito if valor is None else float(10 + 80 * (valor - minimo) / (maximo - minimo))
    tramos = tuple({'x1': posicion(i.inferior,2), 'x2': posicion(i.superior,98),
                    'inferior': None if i.inferior is None else str(i.inferior),
                    'superior': None if i.superior is None else str(i.superior),
                    'cerrado_inferior': i.cerrado_inferior, 'cerrado_superior': i.cerrado_superior}
                   for i in recta.intervalos)
    return {'tramos': tramos, 'punto': None if punto is None else str(punto),
            'pertenece': None if punto is None else contiene(recta,punto),
            'x_punto': None if punto is None else posicion(punto,50)}
