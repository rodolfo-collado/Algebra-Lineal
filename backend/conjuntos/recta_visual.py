"""Geometría acotada para dibujar; los extremos y pertenencia siguen siendo exactos."""

from fractions import Fraction
from .intervalos import contiene


def notacion_recta(recta):
    """Notación habitual: [0, 1) ∪ (2, +∞); un punto aislado es {a} y el vacío es ∅."""
    def tramo(i):
        if i.inferior is not None and i.inferior == i.superior:
            return '{' + str(i.inferior) + '}'
        return (('[' if i.cerrado_inferior else '(') + ('−∞' if i.inferior is None else str(i.inferior)) + ', '
                + ('+∞' if i.superior is None else str(i.superior)) + (']' if i.cerrado_superior else ')'))
    return ' ∪ '.join(tramo(i) for i in recta.intervalos) or '∅'


def datos_recta(recta, punto=None, filas=()):
    """Tramos del resultado y, opcionalmente, de los operandos (`filas`: pares etiqueta, recta)
    sobre una misma escala, para compararlos alineados. Solo x1/x2/x_punto/escala son aproximados."""
    rectas = (recta, *(r for _, r in filas))
    extremos = [v for r in rectas for i in r.intervalos for v in (i.inferior, i.superior) if v is not None]
    if punto is not None:
        extremos.append(punto)
    minimo, maximo = (min(extremos), max(extremos)) if extremos else (Fraction(-1), Fraction(1))
    margen = (maximo - minimo) / 4 if maximo != minimo else Fraction(1)
    minimo -= margen
    maximo += margen

    def posicion(valor, infinito):
        return infinito if valor is None else float(10 + 80 * (valor - minimo) / (maximo - minimo))

    def tramos(r):
        return tuple({'x1': posicion(i.inferior, 2), 'x2': posicion(i.superior, 98),
                      'inferior': None if i.inferior is None else str(i.inferior),
                      'superior': None if i.superior is None else str(i.superior),
                      'cerrado_inferior': i.cerrado_inferior, 'cerrado_superior': i.cerrado_superior,
                      'notacion': notacion_recta(type(r)((i,)))}
                     for i in r.intervalos)

    return {'tramos': tramos(recta), 'notacion': notacion_recta(recta),
            'filas': tuple({'etiqueta': etiqueta, 'notacion': notacion_recta(r), 'tramos': tramos(r)} for etiqueta, r in filas),
            # Escala aproximada: solo sirve para proponer un punto al pulsar sobre la recta.
            'escala': (float(minimo), float(maximo)),
            'punto': None if punto is None else str(punto),
            'pertenece': None if punto is None else contiene(recta, punto),
            'x_punto': None if punto is None else posicion(punto, 50)}
