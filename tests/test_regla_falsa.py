"""Regla falsa clásica: secante, signos, error absoluto y límites de máquina."""

from fractions import Fraction
import math
import unittest

from backend.funciones_reales import FuncionReal
from backend.regla_falsa import confirmar_cercania, interseccion_secante, regla_falsa


class ReglaFalsaTests(unittest.TestCase):
    def test_iteraciones_preservan_formula_signos_y_error_absoluto(self):
        f = FuncionReal("x^2-2")
        r = regla_falsa(f, 1, 2)
        self.assertEqual(r["estado"], "tolerancia")
        self.assertAlmostEqual(r["iteraciones"][0]["xr"], 4 / 3)
        anterior = None
        for p in r["iteraciones"]:
            self.assertLess(p["a"], p["xr"])
            self.assertLess(p["xr"], p["b"])
            self.assertAlmostEqual(p["xr"], (p["a"]*p["fb"] - p["b"]*p["fa"])/(p["fb"]-p["fa"]))
            self.assertEqual(p["fxr"], f(p["xr"]))
            self.assertEqual(p["error_absoluto"], None if anterior is None else abs(p["xr"]-anterior))
            self.assertNotEqual(f(p["nuevo_a"]) < 0, f(p["nuevo_b"]) < 0)
            self.assertEqual(p["sustituido"], "a")
            self.assertEqual(p["extremo_fijo"], "b")
            self.assertEqual(p["veces_fijo"], p["i"])
            anterior = p["xr"]
        self.assertEqual(r["fxr"], f(r["xr"]))
        self.assertLessEqual(r["error_absoluto"], r["tolerancia"])
        self.assertLessEqual(abs(r["xr"]-math.sqrt(2)), r["cota"])
        self.assertLessEqual(r["cota"], r["tolerancia"])
        self.assertGreater(r["longitud"], .5)

    def test_sustituye_tambien_el_extremo_derecho(self):
        r = regla_falsa(FuncionReal("2-x^2"), -2, -1)
        self.assertTrue(r["convergio"])
        self.assertTrue(all(p["sustituido"] == "b" for p in r["iteraciones"]))
        self.assertLessEqual(abs(r["xr"]+math.sqrt(2)), r["cota"])

    def test_raices_en_extremos_y_secante_sin_error_inventado(self):
        for a, b, cantidad in [(0, 2, 0), (-2, 0, 0), (-1, 2, 1)]:
            with self.subTest(a=a, b=b):
                r = regla_falsa(FuncionReal("x"), a, b)
                self.assertEqual((r["estado"], r["xr"], r["fxr"]), ("exacta", 0, 0))
                self.assertEqual(len(r["iteraciones"]), cantidad)
                self.assertIsNone(r["error_absoluto"])
                self.assertIsNone(r["cota"])
                self.assertIsNone(r["extremo_fijo"])
                self.assertEqual(r["veces_fijo"], 0)

    def test_ea_y_residuo_pequenos_no_bastan_para_converger(self):
        r = regla_falsa(FuncionReal("1e-200*(x^20-1)"), 0, 2)
        self.assertEqual(r["estado"], "estancamiento")
        self.assertFalse(r["convergio"])
        self.assertLess(r["error_absoluto"], 1e-4)
        self.assertLess(r["residuo"], 1e-4)
        self.assertGreater(abs(r["xr"]-1), .9)
        self.assertIsNone(r["cota"])
        self.assertFalse(any(p["confirmada"] for p in r["iteraciones"]))

    def test_limite_y_maquina_no_declaran_convergencia(self):
        for tol, limite, estado in [(1e-4, 1, "limite"), (1e-30, 200, "maquina")]:
            r = regla_falsa(FuncionReal("x^2-2"), 1, 2, tol, limite)
            self.assertEqual(r["estado"], estado)
            self.assertFalse(r["convergio"])
            self.assertIsNone(r["cota"])

    def test_tolerancias_menores_y_escala_de_funcion(self):
        for escala in ("1", "1e200", "1e-200", "-1e200"):
            for tol in (1e-4, 1e-8, 1e-12):
                with self.subTest(escala=escala, tol=tol):
                    r = regla_falsa(FuncionReal(f"{escala}*(x^2-2)"), 1, 2, tol)
                    self.assertTrue(r["convergio"])
                    self.assertLessEqual(abs(r["xr"]-math.sqrt(2)), tol)
                    self.assertLessEqual(r["cota"], tol)

    def test_secante_no_desborda_ni_pierde_productos_pequenos(self):
        for a, b, fa, fb, esperado in [
            (0., 4e200, -1e200, 1e200, 2e200),
            (-1., 1., -1e308, 1e308, 0.),
            (0., 2e-10, -1e-310, 1e-310, 1e-10),
            (0., 1., -1e-200, 1., 1e-200),
            (0., 1e200, -1e-200, 1e200, 1e-200),
        ]:
            with self.subTest(a=a, b=b, fa=fa, fb=fb):
                xr = interseccion_secante(a, b, fa, fb)
                self.assertEqual(xr, esperado)
                self.assertTrue(math.isfinite(xr))
        for texto, a, b, raiz in [("x/2-1e200", 0, 4e200, 2e200),
                                  ("1e-300*(x-1e-10)", 0, 2e-10, 1e-10)]:
            r = regla_falsa(FuncionReal(texto), a, b)
            self.assertEqual((r["estado"], r["xr"]), ("exacta", raiz))

    def test_prueba_no_sale_del_intervalo_ni_de_la_tolerancia_por_redondeo(self):
        for xr, a, b in [(1e12, 1e12, 1e12+1), (-1e12, -1e12-1, -1e12)]:
            prueba, _, confirmada = confirmar_cercania(lambda x: -1 if x == xr else 1, xr, -1, a, b, 1e-4)
            self.assertLessEqual(abs(Fraction(prueba)-Fraction(xr)), Fraction(1e-4))
            self.assertFalse(confirmada)
        for xr, a, b in [(0., 0., .00005), (.00005, 0., .00005)]:
            prueba, _, confirmada = confirmar_cercania(lambda x: x-.000025, xr, xr-.000025, a, b, 1e-4)
            self.assertTrue(a <= prueba <= b)
            self.assertTrue(confirmada)

    def test_mismo_signo_cercano_no_excluye_otras_raices(self):
        f = lambda x: (x-.00002)*(x-.00004)*(x-1)
        _, _, confirmada = confirmar_cercania(f, 0., f(0.), 0., 2., 1e-4)
        self.assertFalse(confirmada)
        self.assertEqual(f(.00002), 0)

    def test_dominio_entrada_y_presupuesto_se_validan_antes_de_iterar(self):
        for texto, a, b in [("x^2+1", -1, 1), ("1/x", -1, 1), ("tan(x)", 1, 2),
                            ("log(x)", 0, 2), ("sqrt(x)", -1, 1), ("x", 1, 1),
                            ("x", 2, 1), ("x", math.nan, 1), ("x", 0, math.inf)]:
            with self.subTest(texto=texto, a=a, b=b), self.assertRaises(ValueError):
                regla_falsa(FuncionReal(texto), a, b)
        for tol in (0, -1, .001, math.nan, math.inf):
            with self.assertRaises(ValueError):
                regla_falsa(FuncionReal("x"), -1, 1, tol)
        for limite in (0, 1001, True, 1.5):
            with self.assertRaises(ValueError):
                regla_falsa(FuncionReal("x"), -1, 1, max_iteraciones=limite)
