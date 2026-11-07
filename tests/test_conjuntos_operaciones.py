"""Operaciones P2 sobre el mismo dominio exacto y las relaciones de P1."""

from dataclasses import FrozenInstanceError
from fractions import Fraction
import unittest

from backend.conjuntos.evaluador import evaluar_expresion
from backend.conjuntos.literales import analizar_literal
from backend.conjuntos.parser import analizar_expresion, analizar_relacion, renombrar_referencias
from backend.conjuntos.presupuesto import Presupuesto


class OperacionesConjuntosTests(unittest.TestCase):
    def calcular(self, texto, **opciones):
        entorno = {"A": analizar_literal('{1, 2, {1}, "1"}'),
                   "B": analizar_literal('{2, 3, {1}}'),
                   "U": analizar_literal('{1, 2, 3, {1}, "1"}')}
        return evaluar_expresion(analizar_expresion(texto), entorno, **opciones)

    def test_operaciones_exactas_anidadas_y_vacias(self):
        for texto, esperado in (
            ('A ∪ B', '{1, 2, 3, {1}, "1"}'),
            ('A ∩ B', '{2, {1}}'), ('A ∖ B', '{1, "1"}'),
            ('∁(A, U)', '{3}'), ('∁(∅, U)', '{1, 2, 3, {1}, "1"}'),
            ('∁(U, U)', '{}'), ('∅ ∪ ∅', '{}'), ('A ∩ ∅', '{}'),
            ('∅ ∖ A', '{}'), ('A ∖ A', '{}'), ('∁(∅, ∅)', '{}'),
            ('{1/2, 0.5, .5} ∪ {2/4}', '{1/2}'),
        ):
            with self.subTest(texto=texto):
                self.assertEqual(self.calcular(texto).valor, analizar_literal(esperado))
        self.assertEqual(self.calcular('|{1, 1.0, {1}, {{1}}, "1", ∅}|').valor, Fraction(5))
        self.assertIs(type(self.calcular('|∅|').valor), Fraction)

    def test_precedencia_agrupacion_y_asociatividad(self):
        for texto, esperado in (
            ('{1} ∪ {2} ∩ {3}', '{1}'),
            ('({1} ∪ {2}) ∩ {2}', '{2}'),
            ('{1,2} ∖ {2} ∪ {2}', '{1,2}'),
            ('{1,2} ∖ ({2} ∪ {1})', '{}'),
            ('{1,2} ∖ {1} ∖ {2}', '{}'),
            ('{1,2} ∖ {2} ∩ {3}', '{1,2}'),
            ('∁(A ∩ B, U) ∩ B', '{3}'),
        ):
            with self.subTest(texto=texto):
                self.assertEqual(self.calcular(texto).valor, analizar_literal(esperado))

    def test_operaciones_participan_en_relaciones(self):
        for texto, esperado in (
            ('A ∪ B = U', True), ('A ∩ B ⊂ A', True),
            ('{1} ∈ A ∩ B', True), ('{1} ⊆ A ∩ B', False),
            ('|A ∩ B| ∈ {2}', True), ('|A| = 4', True),
            ('|A| ≠ "4"', None), ('∁(A,U) ⊆ U', True),
        ):
            with self.subTest(texto=texto):
                if esperado is None:
                    with self.assertRaises(ValueError):
                        self.calcular(texto)
                else:
                    self.assertIs(self.calcular(texto).valor, esperado)
                    self.assertEqual(analizar_relacion(texto), analizar_expresion(texto))

    def test_errores_de_tipos_universo_y_sintaxis(self):
        for texto in ('1 ∪ A', 'A ∩ "A"', 'A ∖ 1', '|1|', '||A||',
                      '∁(A, 1)', '∁(1,U)', '∁(A,B)', '∁({∅},∅)',
                      '∁(A)', '∁(A,U,B)', '∁A', 'A = B = U', '(A = B)',
                      'A + B', 'A - B', 'A ∪', '{A ∪ B}', 'A[0]',
                      '__import__("os")', 'par(1,2)', '|A', 'A|', 'A B'):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                self.calcular(texto)

    def test_evidencia_estructurada_e_inmutable(self):
        resultado = self.calcular('A ∩ B ⊆ A')
        self.assertEqual([p.operador for p in resultado.procedimiento], ['∩', '⊆'])
        paso = resultado.procedimiento[0]
        self.assertEqual(paso.resultado, analizar_literal('{2,{1}}'))
        self.assertEqual(len(paso.operandos), 2)
        self.assertEqual(paso.regla, 'interseccion')
        self.assertTrue(paso.explicacion)
        self.assertEqual(resultado.procedimiento[-1].regla, 'inclusion')
        with self.assertRaises(FrozenInstanceError):
            paso.regla = 'otra'
        self.assertGreater(resultado.estimacion.calculo, 0)
        self.assertGreater(resultado.estimacion.procedimiento, len(resultado.pasos))

    def test_operaciones_no_modifican_valores_y_hechos_no_confunden_relaciones(self):
        entorno = {'A': analizar_literal('{1,{1}}'), 'B': analizar_literal('{{1}}')}
        originales = dict(entorno)
        for texto in ('A ∪ B', 'A ∩ B', 'A ∖ B', '∁(B,A)', '|A|'):
            evaluar_expresion(analizar_expresion(texto), entorno)
            self.assertEqual(entorno, originales)
        for texto, campo, esperado in (('1 ∉ B', 'pertenece', False),
                                       ('A ⊆ B', 'incluido', False),
                                       ('A ⊂ A', 'iguales', True)):
            paso = evaluar_expresion(analizar_relacion(texto), entorno).procedimiento[-1]
            self.assertIs(getattr(paso, campo), esperado)
        paso = evaluar_expresion(analizar_relacion('A ⊆ B'), entorno).procedimiento[-1]
        self.assertEqual(paso.testigo, Fraction(1))

    def test_renombrado_y_presupuesto_acumulado(self):
        self.assertEqual(renombrar_referencias('∁(A,AA) ∪ {"A"}', {'A': 'S'}), '∁(S,AA) ∪ {"A"}')
        presupuesto = Presupuesto()
        self.calcular('A ∪ B', presupuesto=presupuesto)
        consumido = presupuesto.calculo
        self.calcular('A ∪ B', presupuesto=presupuesto)
        self.assertEqual(presupuesto.calculo, 2 * consumido)
        with self.assertRaisesRegex(ValueError, 'presupuesto'):
            self.calcular('A ∪ B', presupuesto=Presupuesto(calculo=45000))
        with self.assertRaisesRegex(ValueError, 'presupuesto'):
            self.calcular('A ∪ B', presupuesto=Presupuesto(procedimiento=45000))
        for texto in ('(' * 51 + 'A' + ')' * 51, ' ∪ '.join(['A'] * 100),
                      '∁(' * 51 + 'A' + ',U)' * 51):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                self.calcular(texto)
        self.assertEqual(self.calcular(' ∪ '.join(['∅'] * 50)).valor, analizar_literal('{}'))

    def test_presupuesto_real_no_se_reinicia_entre_operaciones(self):
        presupuesto = Presupuesto()
        conjunto = analizar_literal('{' + ','.join(map(str, range(250))) + '}', presupuesto=presupuesto)
        arbol = analizar_expresion(' ∪ '.join(['A'] * 49), presupuesto=presupuesto)
        with self.assertRaisesRegex(ValueError, 'presupuesto'):
            evaluar_expresion(arbol, {'A': conjunto}, presupuesto=presupuesto)

    def test_p1_conserva_entradas_grandes_y_operandos_repetidos(self):
        presupuesto = Presupuesto()
        conjunto = analizar_literal('{' + ','.join(map(str, range(850))) + '}', presupuesto=presupuesto)
        arbol = analizar_relacion('A = A', presupuesto=presupuesto)
        self.assertIs(evaluar_expresion(arbol, {'A': conjunto}, presupuesto=presupuesto).valor, True)

    def test_tabla_de_pertenencia_de_todos_los_subconjuntos_pequenos(self):
        universo = analizar_literal('{0,1,2}')
        for mascara_a in range(8):
            a = analizar_literal('{' + ','.join(str(i) for i in range(3) if mascara_a & (1 << i)) + '}')
            for mascara_b in range(8):
                b = analizar_literal('{' + ','.join(str(i) for i in range(3) if mascara_b & (1 << i)) + '}')
                for op in ('∪', '∩', '∖'):
                    resultado = evaluar_expresion(analizar_expresion(f'A {op} B'), {'A': a, 'B': b}).valor
                    for i in range(3):
                        en_a, en_b = bool(mascara_a & (1 << i)), bool(mascara_b & (1 << i))
                        esperado = (en_a or en_b) if op == '∪' else ((en_a and en_b) if op == '∩' else (en_a and not en_b))
                        self.assertEqual(Fraction(i) in resultado.elementos, esperado)
                complemento = evaluar_expresion(analizar_expresion('∁(A,U)'), {'A': a, 'U': universo}).valor
                for i in range(3):
                    self.assertEqual(Fraction(i) in complemento.elementos, not bool(mascara_a & (1 << i)))
