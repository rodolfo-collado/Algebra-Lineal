"""Referencias e invariantes del algoritmo explícito de Newton."""
import json
import math
import unittest
from backend.funciones_reales import FuncionReal
from backend.newton_raphson import newton_raphson


def resolver(f="x^2-2", d="2x", x=1.5, **opciones):
    return newton_raphson(FuncionReal(f), FuncionReal(d), x, **opciones)


class NewtonTests(unittest.TestCase):
    def test_referencias_y_tangentes(self):
        for f, d, raiz in [("x^2-2", "2x", math.sqrt(2)), ("x^3-x-2", "3x^2-1", 1.5213797068045676)]:
            r = resolver(f, d)
            self.assertTrue(r["convergio"])
            self.assertAlmostEqual(r["x"], raiz, places=8)
            self.assertLessEqual(r["residuo"], .0001)
            self.assertLessEqual(r["error_absoluto"], .0001)
            for p in r["iteraciones"]:
                self.assertAlmostEqual(p["siguiente"], p["xn"]-p["fxn"]/p["dfxn"])
                self.assertEqual(p["residuo"], abs(p["fsiguiente"]))
                self.assertEqual(p["error_absoluto"], abs(p["siguiente"]-p["xn"]))
            json.dumps(r, allow_nan=False)

    def test_estados(self):
        for f, d, x, estado in [("x^2-2", "2x", 0, "derivada"),
            ("x^3-2x+2", "3x^2-2", 0, "oscilacion"),
            ("ln(x)", "1/x", 4, "dominio"), ("x^2", "2x", 0, "exacta"),
            ("1", "1e20", 1, "estancamiento"), ("x+1", "1e-320", 1, "divergencia"),
            ("x+1", "1/x", 0, "dominio")]:
            with self.subTest(estado=estado):
                r=resolver(f,d,x)
                self.assertEqual(r["estado"], estado)
                self.assertEqual(r["convergio"], estado == "exacta")
                json.dumps(r, allow_nan=False)

    def test_no_confunde_cambio_pequeno_con_residuo(self):
        r=resolver("x^2+1", "1e10", max_iteraciones=2)
        self.assertFalse(r["convergio"])
        self.assertLess(r["error_absoluto"], .0001)
        self.assertGreater(r["residuo"], 1)
        self.assertEqual(resolver(max_iteraciones=1)["estado"], "limite")

    def test_escala_pequena_no_invalida_una_pendiente_util(self):
        self.assertEqual(resolver("1e-200*(x-2)", "1e-200")["x"], 2)

    def test_validacion_y_dominio_inicial(self):
        for opciones in [{"tolerancia":0}, {"tolerancia":.001}, {"tolerancia":float("nan")},
                         {"max_iteraciones":True}, {"max_iteraciones":1001}]:
            with self.assertRaises(ValueError): resolver(**opciones)
        with self.assertRaises(ValueError): resolver("ln(x)", "1/x", -1)
        with self.assertRaises(ValueError): resolver(x=float("inf"))
