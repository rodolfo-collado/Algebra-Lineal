"""Contrato de traducción y dominio del adaptador simbólico."""

import ast
from pathlib import Path
import unittest

import sympy as sp

from backend.calculo_simbolico import adaptar_funcion
from backend.funciones_reales import FuncionReal


class AdaptadorCalculoTests(unittest.TestCase):
    def test_equivalencia_en_puntos_reales(self):
        casos = (
            ("-x/(x+1)", (-2, 0, 2)),
            ("+π + e + 2sen(x)cos(x)", (-2, 0, 2)),
            ("ln(2x) + log(x) + log10(x)", (0.25, 1, 10)),
            ("√(x+1) + exp(-x) + abs(x)", (-1, 0, 2)),
            ("tan(2x)", (-0.2, 0, 0.2)),
            ("(x+1)⁻²", (-2, 0, 2)),
            ("x^(1+2)", (-2, 0, 2)),
            ("x^(1e16+1-1e16+0.5)", (0.25, 4)),
            ("x^(1/3) + x^(-0.5)", (0.25, 1, 4)),
            ("x^pi + x^e + x^ln(2)", (0.25, 1, 2)),
            ("0x10 + 0b11x + 1_2.5 + 2e-2", (-1, 0, 1)),
        )
        for texto, puntos in casos:
            with self.subTest(texto=texto):
                simbolica = adaptar_funcion(texto)
                numerica = FuncionReal(texto)
                for x in puntos:
                    valor = simbolica.expresion.evalf(subs={simbolica.variable: x})
                    self.assertAlmostEqual(float(valor), numerica(x), places=12)

    def test_decimales_y_constantes_exactos(self):
        self.assertEqual(adaptar_funcion("0.1+0.2").expresion, sp.Rational(3, 10))
        self.assertEqual(adaptar_funcion("π").expresion, sp.pi)
        self.assertEqual(adaptar_funcion("e").expresion, sp.E)

    def test_log10_conserva_la_base_en_operaciones_simbolicas(self):
        f = adaptar_funcion("log10(x)")
        self.assertEqual(sp.diff(f.expresion, f.variable), 1 / (f.variable * sp.log(10)))

    def test_restricciones_aun_si_la_expresion_se_cancela(self):
        original = " (x²-1)/(x-1) "
        f = adaptar_funcion(original)
        self.assertEqual(f.texto_original, original)
        self.assertEqual(f.expresion, f.variable + 1)
        self.assertEqual(f.dominio.conjunto, sp.S.Reals - sp.FiniteSet(1))
        self.assertEqual(f.dominio.removibles, sp.FiniteSet(1))
        self.assertEqual(len(f.dominio.restricciones), 1)

    def test_polo_y_agujero_en_la_misma_expresion(self):
        f = adaptar_funcion("(x-1)/(x^2-1)")
        self.assertEqual(f.dominio.conjunto, sp.S.Reals - sp.FiniteSet(-1, 1))
        self.assertEqual(f.dominio.removibles, sp.FiniteSet(1))

    def test_se_conserva_el_dominio_de_subexpresiones(self):
        casos = (
            ("0*(1/x)", sp.S.Reals - sp.FiniteSet(0)),
            ("(1/x)^0", sp.S.Reals - sp.FiniteSet(0)),
            ("1/(1/x)", sp.S.Reals - sp.FiniteSet(0)),
            ("0*(1/0)", sp.S.EmptySet),
            ("ln(x)+√(-x)", sp.S.EmptySet),
            ("ln(x)+√(-x)+ln(sen(x))", sp.S.EmptySet),
            ("ln(x^2-1)", sp.Interval.open(-sp.oo, -1) | sp.Interval.open(1, sp.oo)),
            ("√(x^2-1)", sp.Interval(-sp.oo, -1) | sp.Interval(1, sp.oo)),
        )
        for texto, esperado in casos:
            with self.subTest(texto=texto):
                self.assertEqual(adaptar_funcion(texto).dominio.conjunto, esperado)

    def test_dominios_de_funciones_y_potencias(self):
        casos = (
            ("ln(x)", sp.Interval.open(0, sp.oo)),
            ("√(x)", sp.Interval(0, sp.oo)),
            ("abs(x)", sp.S.Reals),
            ("sen(x)+cos(x)", sp.S.Reals),
            ("x^-2", sp.S.Reals - sp.FiniteSet(0)),
            ("x^(-1/2)", sp.Interval.open(0, sp.oo)),
            ("x^(1/3)", sp.Interval(0, sp.oo)),
            ("x^0", sp.S.Reals),
            ("x^pi", sp.Interval(0, sp.oo)),
            ("x^(1+1e-30)", sp.S.Reals),
        )
        for texto, esperado in casos:
            with self.subTest(texto=texto):
                self.assertEqual(adaptar_funcion(texto).dominio.conjunto, esperado)

    def test_tangente_con_argumento_afin(self):
        dominio = adaptar_funcion("tan(2x)").dominio
        self.assertIsNotNone(dominio.conjunto)
        self.assertEqual(dominio.conjunto.contains(sp.pi / 4), sp.S.false)
        self.assertEqual(dominio.conjunto.contains(0), sp.S.true)

    def test_dominio_inconcluso_conserva_restricciones(self):
        f = adaptar_funcion("ln(sen(x)) + √(x)")
        self.assertIsNone(f.dominio.conjunto)
        self.assertEqual([r.condicion.rel_op for r in f.dominio.restricciones], [">", ">="])
        self.assertIsNone(f.dominio.restricciones[0].conjunto)
        self.assertEqual(f.dominio.restricciones[1].conjunto, sp.Interval(0, sp.oo))
        self.assertEqual(f.dominio.removibles, sp.S.EmptySet)

    def test_rechaza_sintaxis_ajena_al_parser(self):
        casos = (
            "x.__class__", "__import__('os')", "sin(x, x)", "sin(x=x)", "x[0]",
            "[x for x in (1,)]", "lambda: x", "x^x", "True", "y+1", "x # comentario",
            ast.parse("x", mode="eval").body, FuncionReal("x"),
        )
        for entrada in casos:
            with self.subTest(entrada=entrada), self.assertRaises(ValueError):
                adaptar_funcion(entrada)

    def test_limites_y_operaciones_no_expandidas(self):
        ancho = "x"
        for _ in range(6):
            ancho = f"({ancho}+{ancho})"
        casos = ("x " + " " * 512, ancho, "sin(" * 25 + "x" + ")" * 25,
                 "9^9^9", "x^1025", "x^(1/0)")
        for texto in casos:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                adaptar_funcion(texto)
        expresion = adaptar_funcion("(x+1)^1024").expresion
        self.assertIs(expresion.func, sp.Pow)
        self.assertEqual(expresion.exp, 1024)
        dominio = adaptar_funcion("1/(x+1)^1024").dominio
        self.assertIsNone(dominio.conjunto)
        self.assertEqual(len(dominio.restricciones), 1)

    def test_el_adaptador_forma_parte_del_paquete_windows(self):
        spec = Path(__file__).resolve().parents[1] / "AlgebraLineal.spec"
        self.assertIn('"backend.calculo_simbolico"', spec.read_text(encoding="utf-8"))
