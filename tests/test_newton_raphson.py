"""Referencias, derivación y geometría del algoritmo explícito de Newton."""

import json
import math
import unittest

from backend.biseccion import biseccion
from backend.regla_falsa import regla_falsa
from backend.derivacion_real import DerivadaReal
from backend.funciones_reales import FuncionReal
from backend.newton_raphson import newton_raphson


def resolver(f="x^2-2", x=1.5, **opciones):
    return newton_raphson(FuncionReal(f), x, **opciones)


class NewtonTests(unittest.TestCase):
    def test_ejemplo_de_las_diapositivas(self):
        r = resolver("x³ - x - 2")
        self.assertEqual(r["derivada"], "3 · x^2 − 1")
        primero = r["iteraciones"][0]
        self.assertEqual(primero["xn"], 1.5)
        self.assertEqual(primero["fxn"], -0.125)
        self.assertEqual(primero["dfxn"], 5.75)
        self.assertEqual(primero["siguiente"], 1.5217391304347827)
        self.assertAlmostEqual(r["x"], 1.5213797068045676, places=8)

    def test_tangentes_y_residuo(self):
        f = FuncionReal("x^2-2")
        r = newton_raphson(f, 1.5)
        self.assertEqual(r["clasificacion"], "raiz_aproximada")
        self.assertAlmostEqual(r["x"], math.sqrt(2), places=8)
        self.assertLessEqual(r["residuo"], .0001)
        self.assertLessEqual(r["error_absoluto"], .0001)
        for p in r["iteraciones"]:
            self.assertEqual(p["fxn"], f(p["xn"]))
            self.assertEqual(p["dfxn"], 2 * p["xn"])
            self.assertAlmostEqual(p["fxn"] + p["dfxn"] * (p["siguiente"] - p["xn"]), 0.)
            self.assertEqual(p["residuo"], abs(f(p["siguiente"])))
            self.assertEqual(p["error_absoluto"], abs(p["siguiente"] - p["xn"]))
        self.assertEqual(r["fx"], f(r["x"]))
        json.dumps(r, allow_nan=False)

    def test_derivacion_compuesta_y_aliases(self):
        derivada = DerivadaReal(FuncionReal("ln(2x) + x² - sen(x)"))
        self.assertEqual(derivada.texto, "1 / x + 2 · x − cos(x)")
        for x in (0.25, 1., 2.5):
            self.assertAlmostEqual(derivada(x), 1/x + 2*x - math.cos(x))
        for x in (-1., 0.):
            with self.assertRaises(ValueError):
                derivada(x)

    def test_reglas_de_derivacion_para_operaciones_y_funciones_admitidas(self):
        for texto, x, esperado in [
                ("-x/(x+1)", 2., -1/9), ("x*sen(x)", 1., math.sin(1) + math.cos(1)),
                ("√(x) + exp(-x)", 4., .25 - math.exp(-4)), ("log10(x)", 1., 1/math.log(10)),
                ("tan(2x)", .25, 2 / math.cos(.5)**2), ("abs(x)", -2., -1.),
                ("abs(x²)", 0., 0.), ("x^(1+1)", -2., -4.), ("x^0", 0., 0.),
                ("x^-2", -2., .25), ("x^0.5", 4., .25), ("π + e", 0., 0.)]:
            with self.subTest(texto=texto):
                self.assertAlmostEqual(DerivadaReal(FuncionReal(texto))(x), esperado)

    def test_estados(self):
        for f, x, estado, clasificacion in [
                ("x^2-2", 0., "derivada", "no_aplicable"),
                ("abs(x)+1", 0., "dominio_derivada", "no_aplicable"),
                ("sqrt(x)+1", 0., "dominio_derivada", "no_aplicable"),
                ("tan(x)", math.pi/2, "dominio_inicial", "no_aplicable"),
                ("ln(x)", -1., "dominio_inicial", "no_aplicable"),
                ("x^3-2x+2", 0., "oscilacion", "sin_convergencia"),
                ("ln(x)", 4., "dominio", "sin_convergencia"),
                ("x^2", 0., "exacta", "raiz_aproximada"),
                ("1e20*(x-1)+1", 1., "estancamiento", "sin_convergencia"),
                ("1+1e-320*x", 1., "divergencia", "sin_convergencia")]:
            with self.subTest(f=f, estado=estado):
                r = resolver(f, x)
                self.assertEqual(r["estado"], estado)
                self.assertEqual(r["clasificacion"], clasificacion)
                self.assertEqual(r["convergio"], estado == "exacta")
                json.dumps(r, allow_nan=False)

    def test_corte_fuera_del_dominio_conserva_el_ultimo_punto_y_el_intento(self):
        r = resolver("ln(x)", 4.)
        self.assertEqual(r["x"], 4.)
        self.assertFalse(r["iteraciones"])
        intento = r["intento_final"]
        self.assertAlmostEqual(intento["siguiente"], 4. - 4. * math.log(4.))
        self.assertEqual(intento["dfxn"], .25)
        self.assertIsNone(intento["fsiguiente"])

    def test_ambas_condiciones_de_tolerancia(self):
        r = resolver("(1e10*x)^2+1", 1e-10, max_iteraciones=1)
        self.assertEqual(r["estado"], "limite")
        self.assertLess(r["error_absoluto"], .0001)
        self.assertGreaterEqual(r["residuo"], 1)
        r = resolver("1e-8*(x^2-2)", max_iteraciones=1)
        self.assertEqual(r["estado"], "limite")
        self.assertLess(r["residuo"], .0001)
        self.assertGreater(r["error_absoluto"], .0001)

    def test_escala_pequena_no_invalida_una_pendiente_util(self):
        self.assertEqual(resolver("1e-200*(x-2)")["x"], 2)

    def test_subdesbordamiento_en_metodos_cerrados_es_fallo_numerico(self):
        for metodo in (biseccion, regla_falsa):
            with self.subTest(metodo=metodo.__name__):
                r = metodo(FuncionReal("x³"), -1e-100, 1.0000000001e-100)
                self.assertEqual(r["estado"], "evaluacion")
                self.assertEqual(r["clasificacion"], "sin_convergencia")
                self.assertIsNone(r["residuo"])

    def test_parametros_y_sintaxis_invalidos(self):
        for opciones in [{"tolerancia": 0}, {"tolerancia": .001}, {"tolerancia": math.nan},
                         {"max_iteraciones": True}, {"max_iteraciones": 1001}, {"x": math.inf},
                         {"f": "x.__class__"}, {"f": "x^x"}]:
            with self.subTest(opciones=opciones), self.assertRaises(ValueError):
                resolver(**opciones)
