"""Bisección manual: referencia del profesor, dominio y límites numéricos."""

import math
import unittest

from backend.biseccion import biseccion
from backend.funciones_reales import FuncionReal


POLINOMIO = "x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10"


class BiseccionTests(unittest.TestCase):
    def test_trece_iteraciones_del_profesor_con_valores_recalculados(self):
        r = biseccion(FuncionReal(POLINOMIO), .55, 1.1)
        esperados = [.825, .6875, .75625, .790625, .7734375, .76484375,
                     .760546875, .7626953125, .76376953125, .764306640625,
                     .7640380859375, .76390380859375, .763970947265625]
        self.assertTrue(r["convergio"])
        self.assertEqual(len(r["iteraciones"]), 13)
        for fila, c in zip(r["iteraciones"], esperados):
            self.assertAlmostEqual(fila["c"], c, places=14)
            self.assertAlmostEqual(fila["fc"], c**4 - 5*c**3 + .5*c**2 - 11*c + 10)
        self.assertIsNone(r["iteraciones"][0]["error_relativo"])
        self.assertAlmostEqual(r["iteraciones"][1]["error_relativo"], 20)
        self.assertLess(r["longitud"], .0001)
        self.assertGreater(abs(r["fc"]), .0001)  # El residuo no es la longitud.
        self.assertAlmostEqual(r["fc"], -.000669776157657509)

    def test_intervalos_de_la_segunda_raiz(self):
        f = FuncionReal(POLINOMIO)
        r, s = biseccion(f, 5, 5.5), biseccion(f, 5.2, 5.3)
        self.assertEqual([len(r["iteraciones"]), len(s["iteraciones"])], [13, 10])
        self.assertTrue(r["convergio"] and s["convergio"])
        self.assertLess(abs(r["c"] - s["c"]), .0001)
        self.assertLessEqual(max(r["a"], s["a"]), min(r["b"], s["b"]))

    def test_raices_en_extremos_y_en_punto_medio(self):
        for a, b, c, cantidad in [(0, 2, 0, 0), (-2, 0, 0, 0), (-1, 1, 0, 1)]:
            r = biseccion(FuncionReal("x"), a, b)
            self.assertTrue(r["convergio"])
            self.assertEqual((r["c"], len(r["iteraciones"])), (c, cantidad))
            self.assertEqual(r["fc"], 0)

    def test_sin_cambio_de_signo(self):
        with self.assertRaisesRegex(ValueError, "signos"):
            biseccion(FuncionReal("x^2 + 1"), -1, 1)

    def test_dominio_y_discontinuidad_no_son_raices(self):
        for texto, a, b in [("1/x", -1, 1), ("1/(x-0.3)", 0, 1),
                            ("tan(x)", 1, 2), ("tan(x)", math.pi/2, 2),
                            ("tan(x)", -2, -math.pi/2), ("log(x)", -1, 2), ("sqrt(x)", -1, 1)]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                biseccion(FuncionReal(texto), a, b)

    def test_validacion_de_intervalo_precision_y_limite(self):
        for a, b, tol in [(1, 0, .0001), (0, 0, .0001), (0, math.inf, .0001),
                          (math.nan, 1, .0001), (0, 1, .001), (0, 1, 0),
                          (0, 1, -1), (0, 1, math.nan), (0, 1, math.inf)]:
            with self.subTest(a=a, b=b, tol=tol), self.assertRaises(ValueError):
                biseccion(FuncionReal("x-.3"), a, b, tol)
        for limite in [0, 1001, 2.5, True]:
            with self.assertRaises(ValueError):
                biseccion(FuncionReal("x-.3"), 0, 1, max_iteraciones=limite)

    def test_limite_de_iteraciones_y_estancamiento_no_convergen(self):
        r = biseccion(FuncionReal("x^2-2"), 1, 2, max_iteraciones=1)
        self.assertFalse(r["convergio"])
        self.assertEqual(r["estado"], "limite")
        r = biseccion(FuncionReal("x^2-2"), 1, 2, 1e-30)
        self.assertFalse(r["convergio"])
        self.assertEqual(r["estado"], "estancamiento")

    def test_precision_menor_y_longitud_estricta(self):
        r = biseccion(FuncionReal("x^2-2"), 1, 2, 1e-8)
        self.assertTrue(r["convergio"])
        self.assertLess(r["longitud"], 1e-8)
        r = biseccion(FuncionReal("x-.0001234567"), 0, .0002)
        self.assertEqual(len(r["iteraciones"]), 2)

    def test_error_relativo_no_definido_cuando_una_aproximacion_es_cero(self):
        r = biseccion(FuncionReal("x+.2"), -1, 3)
        self.assertEqual(r["iteraciones"][1]["c"], 0)
        self.assertIsNone(r["iteraciones"][1]["error_relativo"])
        self.assertTrue(r["convergio"])


class FuncionesRealesTests(unittest.TestCase):
    def test_multiplicacion_implicita_equivale_a_explicita(self):
        for implicita, explicita in [
            ("5x^3", "5*x^3"), ("0.5x^2", "0.5*x^2"), ("11x", "11*x"),
            ("2(x+1)", "2*(x+1)"), ("x(x+1)", "x*(x+1)"),
            ("(x+1)(x-1)", "(x+1)*(x-1)"), ("2sin(x)", "2*sin(x)"),
            ("pi x", "pi*x"), ("1/2x", "1/2*x"), ("e(x+1)", "e*(x+1)"),
            ("sin(x)cos(x)", "sin(x)*cos(x)"), ("1e-3x+2E+2(x+1)", "1e-3*x+2E+2*(x+1)"),
        ]:
            with self.subTest(texto=implicita):
                f, g = FuncionReal(implicita), FuncionReal(explicita)
                self.assertEqual(f.clave, g.clave)
                for x in [-2, 0, .75, 2]:
                    self.assertEqual(f(x), g(x))
                self.assertEqual(f.rango(-1, 1), g.rango(-1, 1))

    def test_profesor_implicito_conserva_las_trece_iteraciones(self):
        explicita = biseccion(FuncionReal(POLINOMIO), .55, 1.1)
        implicita = biseccion(FuncionReal(POLINOMIO.replace("*", "")), .55, 1.1)
        self.assertEqual(implicita, explicita)
        self.assertEqual(len(implicita["iteraciones"]), 13)

    def test_no_adivina_nombres_ni_notacion_cientifica_incompleta(self):
        for texto in ["xx", "sinx", "xpi", "2e", "2e+", "1.2.3x", "2 3x", "sin x", "foo(x)",
                      "2__import__('os')", "x[0]", "x#comentario", "x " * 100, "2x " * 180]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                FuncionReal(texto)

    def test_sintaxis_matematica_y_funciones_permitidas(self):
        for texto, x, esperado in [("-x^2", 2, -4), ("sin(pi/2)+cos(0)", 0, 2),
                                    ("exp(-x)-x", 0, 1), ("sqrt(x)+ln(e)", 4, 3),
                                    ("abs(x)+log10(100)", -2, 4), ("2**3**2", 0, 512)]:
            with self.subTest(texto=texto):
                self.assertAlmostEqual(FuncionReal(texto)(x), esperado)

    def test_rechaza_codigo_y_sintaxis_ajena(self):
        for texto in ["__import__('os')", "x.__class__", "[x][0]", "lambda: 1", "x if x else 0",
                      "sum([1])", "sin(x,1)", "sin(x=1)", "True", "y+1", "x%2", "", "1e999", "x+1e-400", "0e"+"9"*100]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                FuncionReal(texto)

    def test_presupuesto_dominio_overflow_underflow_y_complejos(self):
        for texto in ["x+"*300+"1", "("*250+"x"+")"*250]:
            with self.assertRaises(ValueError):
                FuncionReal(texto)
        for texto in ["1/0", "exp(1000)", "exp(-1000)", "(-1)^0.5", "10^1000", "1e-300*1e-300"]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                FuncionReal(texto)(0)

    def test_rango_continuo_conservador(self):
        for texto in [POLINOMIO, "1/(x^2+1)", "sin(x)+cos(x)", "abs(x)", "exp(x)"]:
            f = FuncionReal(texto)
            lo, hi = f.rango(-1, 1)
            for x in [-1, -.5, 0, .5, 1]:
                self.assertLessEqual(lo, f(x))
                self.assertGreaterEqual(hi, f(x))
