from fractions import Fraction
import unittest
from unittest.mock import patch

from backend.conjuntos.evaluador import evaluar_expresion
from backend.conjuntos.literales import analizar_literal
from backend.conjuntos.modelo import Conjunto, Par
from backend.conjuntos.parser import analizar_expresion
from backend.conjuntos.presupuesto import Presupuesto


def calcular(texto, entorno=None, presupuesto=None):
    presupuesto = presupuesto or Presupuesto()
    return evaluar_expresion(analizar_expresion(texto, presupuesto=presupuesto), entorno or {}, presupuesto=presupuesto)


class GeneracionTests(unittest.TestCase):
    def test_potencia_vacio_anidacion_y_relaciones(self):
        self.assertEqual(calcular('potencia(∅)').valor, analizar_literal('{∅}'))
        self.assertEqual(calcular('potencia({1,2,2})').valor, analizar_literal('{∅,{1},{2},{1,2}}'))
        self.assertIs(calcular('{∅} ∈ potencia({∅})').valor, True)
        self.assertEqual(calcular('|potencia({1,{1}})|').valor, Fraction(4))

    def test_pares_y_productos(self):
        self.assertIs(calcular('par(1,2) ≠ par(2,1)').valor, True)
        self.assertIs(calcular('par(1,2) ∈ {1} × {2}').valor, True)
        with self.assertRaises(ValueError):
            calcular('par(1,2) = {1,2}')
        self.assertEqual(calcular('∅ × {1}').valor, Conjunto())
        self.assertEqual(calcular('|{1,1.0,{1}} × {"1",2}|').valor, Fraction(4))
        self.assertEqual(calcular('{1} × {2} × {3}').valor,
                         Conjunto(frozenset([Par(Par(Fraction(1), Fraction(2)), Fraction(3))])))
        self.assertEqual(calcular('{1} ∪ {2} × {3}').valor, analizar_literal('{1,par(2,3)}'))

    def test_reserva_antes_de_generar(self):
        a = analizar_literal('{' + ','.join(map(str, range(20))) + '}')
        with patch('backend.conjuntos.generacion.Par', side_effect=AssertionError('Generó antes de reservar')):
            with self.assertRaisesRegex(ValueError, 'presupuesto'):
                calcular('A × A', {'A': a}, Presupuesto(procedimiento=44999))
        with self.assertRaisesRegex(ValueError, 'presupuesto'):
            calcular('potencia(A)', {'A': a})
        for texto in ('potencia(1)', '1 × {}', 'par(1)', '(1,2)', 'potencia({1}, {2})'):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                calcular(texto)
