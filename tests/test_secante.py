"""Referencias de clase, geometría de cada secante y casos límite del método de la secante."""

import json
import math
import unittest
from fractions import Fraction

from backend.funciones_reales import FuncionReal
from backend.secante import secante


def resolver(f="x^3-x-2", x0=1, x1=2, **opciones):
    return secante(FuncionReal(f), x0, x1, **opciones)


class SecanteTests(unittest.TestCase):
    def test_diapositivas_22_y_23(self):
        r = resolver()
        primero = r["iteraciones"][0]
        # Diapositiva 22: f(1) = −2, f(2) = 4 y x₂ = 2 − [4(2 − 1)] / [4 − (−2)] = 4/3.
        self.assertEqual((primero["anterior"], primero["fanterior"]), (1., -2.))
        self.assertEqual((primero["actual"], primero["factual"]), (2., 4.))
        self.assertEqual((primero["numerador"], primero["denominador"]), (4., 6.))
        self.assertEqual(primero["siguiente"], 4 / 3)
        # Diapositiva 23, redondeada a seis decimales: anterior, actual y nueva aproximación.
        tabla = [(1.0, 2.0, 1.333333), (2.0, 1.333333, 1.462687), (1.333333, 1.462687, 1.531169),
                 (1.462687, 1.531169, 1.520926), (1.531169, 1.520926, 1.521376), (1.520926, 1.521376, 1.521380)]
        self.assertEqual([(round(p["anterior"], 6), round(p["actual"], 6), round(p["siguiente"], 6))
                          for p in r["iteraciones"]], tabla)
        self.assertEqual(r["estado"], "tolerancia")
        self.assertEqual(r["clasificacion"], "raiz_aproximada")
        self.assertAlmostEqual(r["x"], 1.521379707, places=8)

    def test_practica_integradora(self):
        r = resolver("x³ - 2x - 5", 2, 3, tolerancia=1e-6)
        self.assertTrue(r["convergio"])
        self.assertAlmostEqual(r["x"], 2.0945514815, places=9)
        self.assertLessEqual(r["residuo"], 1e-6)
        self.assertLessEqual(r["error_absoluto"], 1e-6)
        self.assertEqual(r["tolerancia"], 1e-6)

    def test_cada_fila_es_una_secante_y_desplaza_los_puntos(self):
        f = FuncionReal("x^3-2x-5")
        r = secante(f, 2, 3, 1e-6)
        for p, q in zip(r["iteraciones"], r["iteraciones"][1:]):
            # x₀ ← x₁ y x₁ ← x₂: la fila siguiente parte de los dos últimos puntos.
            self.assertEqual((q["anterior"], q["fanterior"]), (p["actual"], p["factual"]))
            self.assertEqual((q["actual"], q["factual"]), (p["siguiente"], p["fsiguiente"]))
        for p in r["iteraciones"]:
            self.assertEqual(p["fanterior"], f(p["anterior"]))
            self.assertEqual(p["factual"], f(p["actual"]))
            self.assertEqual(p["residuo"], abs(f(p["siguiente"])))
            self.assertEqual(p["error_absoluto"], abs(p["siguiente"] - p["actual"]))
            # El corte (siguiente, 0) está en la recta que une los dos puntos.
            pendiente = (Fraction(p["factual"]) - Fraction(p["fanterior"])) / (Fraction(p["actual"]) - Fraction(p["anterior"]))
            self.assertAlmostEqual(float(Fraction(p["factual"]) + pendiente * (Fraction(p["siguiente"]) - Fraction(p["actual"]))), 0, places=12)

    def test_no_exige_cambio_de_signo_ni_orden(self):
        # Los dos puntos a la derecha de la raíz y en orden descendente: sigue siendo válido.
        r = resolver("x^2-2", 3, 2)
        self.assertTrue(r["convergio"])
        self.assertAlmostEqual(r["x"], math.sqrt(2), places=7)
        self.assertGreater(r["iteraciones"][0]["fanterior"] * r["iteraciones"][0]["factual"], 0)

    def test_cambio_pequeno_con_residuo_grande_no_converge(self):
        # Escalar f por 10⁶ no mueve la raíz: en la iteración 6 el cambio ya cumple, el residuo no.
        r = resolver("1000000(x^3-x-2)", 1, 2)
        sexta = r["iteraciones"][5]
        self.assertTrue(sexta["error_absoluto"] <= 1e-4 < sexta["residuo"])
        self.assertEqual((r["estado"], len(r["iteraciones"])), ("tolerancia", 7))
        self.assertLessEqual(r["residuo"], 1e-4)
        for p in r["iteraciones"][:-1]:
            self.assertFalse(p["error_absoluto"] <= 1e-4 and p["residuo"] <= 1e-4)

    def test_raiz_inicial_exacta(self):
        r = resolver("x^2-4", 3, 2)
        self.assertEqual((r["estado"], r["x"], r["iteraciones"]), ("exacta", 2, []))
        r = resolver("x^2-4", 2, 3)
        self.assertEqual((r["estado"], r["x"], r["residuo"]), ("exacta", 2, 0))

    def test_denominador_nulo(self):
        # f(−1) = f(1): la primera secante es horizontal; no es aplicable con esos puntos.
        r = resolver("x^2-4", -1, 1)
        self.assertEqual((r["estado"], r["clasificacion"]), ("denominador", "no_aplicable"))
        self.assertEqual(r["intento_final"]["denominador"], 0)
        self.assertIsNone(r["intento_final"]["siguiente"])
        # Tras una iteración: x² + 1 desde 0 y 1 llega a −1, con f(−1) = f(1).
        r = resolver("x^2+1", 0, 1)
        self.assertEqual((r["estado"], r["clasificacion"], len(r["iteraciones"])), ("denominador", "sin_convergencia", 1))
        self.assertEqual(r["x"], -1)

    def test_denominador_dominado_por_el_redondeo(self):
        r = resolver("1 + 1e-13x", 0, 1)
        self.assertEqual(r["estado"], "denominador_pequeno")
        self.assertIsNone(r["intento_final"]["siguiente"])

    def test_dominio_no_finitos_y_divergencia(self):
        r = resolver("ln(x)", -1, 2)
        self.assertEqual((r["estado"], r["clasificacion"], r["x"]), ("dominio_inicial", "no_aplicable", None))
        self.assertIn("f(x₀)", r["mensaje"])
        self.assertIn("f(x₁)", resolver("ln(x)", 2, -1)["mensaje"])
        # El corte de la primera secante cae en x < 0, fuera del dominio de √x.
        r = resolver("√(x) - 0.1", 4, 9)
        self.assertEqual(r["estado"], "dominio")
        self.assertIsNotNone(r["intento_final"]["siguiente"])
        self.assertEqual(r["x"], 9)
        r = resolver("exp(-x)", 1, 2, max_iteraciones=30)
        self.assertEqual((r["estado"], r["clasificacion"]), ("limite", "sin_convergencia"))
        self.assertEqual(len(r["iteraciones"]), 30)
        r = resolver("1e300 + 1e290x", 0, 1e-300)
        self.assertIn(r["estado"], {"divergencia", "denominador", "denominador_pequeno"})

    def test_validacion_de_parametros(self):
        for x0, x1, opciones in [(1, 1, {}), (math.nan, 1, {}), (1, math.inf, {}), (1, 2, {"tolerancia": 0}),
                                 (1, 2, {"tolerancia": .001}), (1, 2, {"max_iteraciones": 0}),
                                 (1, 2, {"max_iteraciones": 1.5}), (1, 2, {"max_iteraciones": 1001})]:
            with self.subTest(x0=x0, x1=x1, opciones=opciones), self.assertRaises(ValueError):
                resolver("x^2-2", x0, x1, **opciones)

    def test_limite_de_iteraciones_y_json_estricto(self):
        r = resolver("x^3-x-2", 1, 2, max_iteraciones=2)
        self.assertEqual((r["estado"], len(r["iteraciones"])), ("limite", 2))
        self.assertEqual(r["x"], r["iteraciones"][-1]["siguiente"])
        for caso in (r, resolver("x^2+1", 0, 1), resolver("1e300 + 1e290x", 0, 1e-300), resolver("ln(x)", -1, 2)):
            json.dumps(caso, allow_nan=False)

    def test_estancamiento_o_ciclo_no_declaran_convergencia(self):
        r = resolver("x^3-2x+2", 0, 0.5, max_iteraciones=200)
        if not r["convergio"]:
            self.assertEqual(r["clasificacion"], "sin_convergencia")
        r = resolver("abs(x)^0.5", 1, -1)
        self.assertFalse(r["convergio"])


if __name__ == "__main__":
    unittest.main()
