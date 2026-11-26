"""Regresiones del evaluador compartido por los métodos de raíces."""

import math
import unittest

from backend.biseccion import biseccion
from backend.derivacion_real import DerivadaReal
from backend.funciones_reales import FuncionReal
from backend.newton_raphson import newton_raphson
from backend.regla_falsa import regla_falsa
from backend.resultados_raices import evidencia_muestreo
from backend.secante import secante
from frontend.web.calculadora.servicios_raices import muestrear


class PotenciasVariablesTests(unittest.TestCase):
    def test_notaciones_y_evaluaciones(self):
        casos = [
            ("e^(1/x)+(2x/tanx)", "e**(1/x)+2*x/tan(x)", -1.8,
             math.exp(1 / -1.8) + 2 * (-1.8) / math.tan(-1.8)),
            ("x^(sen(x))", "x**sin(x)", 1.7, 1.7**math.sin(1.7)),
            ("2exp(x)", "2*exp(x)", 0.5, 2*math.exp(0.5)),
            ("2tanx", "2*tan(x)", 0.5, 2*math.tan(0.5)),
        ]
        for visual, explicita, x, esperado in casos:
            with self.subTest(visual=visual):
                f, g = FuncionReal(visual), FuncionReal(explicita)
                self.assertEqual(f.clave, g.clave)
                self.assertAlmostEqual(f(x), esperado)
                self.assertAlmostEqual(g(x), esperado)

    def test_rango_incluye_valores_interiores_de_potencias_no_monotonas(self):
        for texto, a, b in (("x^x", .1, .9), ("x^(-x)", .2, 2), ("x^(sin(x))", .5, 2)):
            with self.subTest(texto=texto):
                f = FuncionReal(texto)
                minimo, maximo = f.rango(a, b)
                for i in range(101):
                    valor = f(a + (b - a) * (i / 100))
                    self.assertLessEqual(minimo, valor)
                    self.assertGreaterEqual(maximo, valor)

    def test_derivadas_de_potencias_variables_y_compuestas(self):
        casos = [
            ("e^x", .5, math.exp(.5)),
            ("e^(1/x)", -2, -math.exp(-.5) / 4),
            ("2^x", 3, 8 * math.log(2)),
            ("x^x", 2, 4 * (1 + math.log(2))),
            ("(x+1)^(sin(x))", .5, 1.5**math.sin(.5) *
             (math.cos(.5) * math.log(1.5) + math.sin(.5) / 1.5)),
            ("0^x", 1, 0),
        ]
        for texto, x, esperado in casos:
            with self.subTest(texto=texto):
                derivada = DerivadaReal(FuncionReal(texto))
                self.assertAlmostEqual(derivada(x), esperado, places=12)

    def test_dominio_real_depende_de_base_y_exponente(self):
        f = FuncionReal("(-2)^x")
        self.assertEqual(f(3), -8)
        for calcular, args in ((f, (.5,)), (f.rango, (1, 2)), (DerivadaReal(f), (2,))):
            with self.subTest(calcular=calcular), self.assertRaises(ValueError):
                calcular(*args)
        f = FuncionReal("0^x")
        self.assertEqual(f(1), 0)
        lo, hi = f.rango(1, 2)
        self.assertLessEqual(lo, 0)
        self.assertGreaterEqual(hi, 0)
        for x in (-1, 0):
            with self.subTest(x=x), self.assertRaises(ValueError):
                f(x)
        self.assertEqual(FuncionReal("x^0")(0), 1)

    def test_diagnosticos_de_dominio_y_limites_numericos(self):
        for texto, x, mensaje in [
            ("(-2)^x", .5, "base negativa"),
            ("tan(x)", math.pi/2, "tangente"),
            ("exp(x)", 1000, "desbordamiento"),
            ("2^x", 1024, "desbordamiento"),
            ("e^(1/x)", -.001, "subdesbordamiento"),
            ("x", math.inf, "no finito"),
        ]:
            with self.subTest(texto=texto, x=x):
                with self.assertRaises(ValueError) as error:
                    FuncionReal(texto)(x)
                self.assertIn(mensaje, str(error.exception).lower())


class MetodosPotenciasVariablesTests(unittest.TestCase):
    def test_raices_con_los_cuatro_metodos(self):
        for texto, a, b, x0, esperada in [
            ("e^x-2", 0, 1, .5, math.log(2)),
            ("2^x-8", 2.1, 4, 2.8, 3),
            ("x^x-4", 1, 2.5, 1.8, 2),
            ("e^(1/x)+2x/tan(x)", -2, -1.6, -1.8, -1.7314791865119594),
        ]:
            for metodo, args, clave in [
                (biseccion, (a, b), "c"), (regla_falsa, (a, b), "xr"),
                (newton_raphson, (x0,), "x"), (secante, (a, b), "x"),
            ]:
                with self.subTest(texto=texto, metodo=metodo.__name__):
                    f = FuncionReal(texto)
                    r = metodo(f, *args, 1e-8)
                    self.assertEqual(r["clasificacion"], "raiz_aproximada", r["mensaje"])
                    self.assertTrue(r["convergio"])
                    self.assertAlmostEqual(r[clave], esperada, delta=1e-8)
                    self.assertEqual(r["residuo"], abs(f(r[clave])))

    def test_raiz_en_el_borde_del_dominio_discontinuo(self):
        f = FuncionReal("sqrt((2x^3)/(x-3))")
        self.assertEqual(f(0), 0)
        for x in (1, 3):
            with self.subTest(x=x), self.assertRaises(ValueError):
                f(x)
        for metodo, args, clave in [
            (biseccion, (-1, 0), "c"), (regla_falsa, (-1, 0), "xr"),
            (newton_raphson, (0,), "x"), (secante, (-1, 0), "x"),
        ]:
            with self.subTest(metodo=metodo.__name__):
                r = metodo(f, *args)
                self.assertEqual((r["estado"], r[clave], r["residuo"]), ("exacta", 0, 0))
        puntos = muestrear(f, -1, 4)
        self.assertEqual(puntos["y"][puntos["x"].index(0)], 0)
        self.assertIsNone(puntos["y"][puntos["x"].index(3)])
        self.assertGreater(puntos["y"][0], 0)
        self.assertGreater(puntos["y"][-1], 0)

    def test_exponencial_positiva_sin_falsos_ceros_ni_convergencia(self):
        f = FuncionReal("e^(1/x)")
        for metodo in (biseccion, regla_falsa):
            with self.subTest(metodo=metodo.__name__):
                r = metodo(f, -2, -1)
                self.assertEqual(r["clasificacion"], "sin_raices_demostrado")
                self.assertFalse(metodo(f, -.002, -.001)["convergio"])
        for metodo, casos in [(newton_raphson, [(-.001,), (-.005,)]),
                              (secante, [(-.002, -.001), (-.0051, -.005)])]:
            for args in casos:
                with self.subTest(metodo=metodo.__name__, args=args):
                    r = metodo(f, *args)
                    self.assertFalse(r["convergio"], r["mensaje"])
                    self.assertNotEqual(r["residuo"], 0)
        ordenadas = muestrear(f, -.005, .005)["y"]
        self.assertIn(None, ordenadas)
        evidencia = evidencia_muestreo(ordenadas)
        self.assertGreater(evidencia["evidencia"]["muestras_validas"], 0)
        self.assertEqual(evidencia["evidencia"]["ceros_calculados"], 0)
        self.assertEqual(evidencia["clasificacion"], "exploracion_no_concluyente")

    def test_discontinuidades_no_generan_raices_ni_cambios_de_signo_en_grafica(self):
        for texto, a, b, polo in [("1/(x-2)", 1, 3.1, 2), ("tan(x)", 1, 2, math.pi/2)]:
            f = FuncionReal(texto)
            with self.subTest(texto=texto):
                for metodo in (biseccion, regla_falsa):
                    r = metodo(f, a, b)
                    self.assertEqual(r["clasificacion"], "no_aplicable")
                    self.assertFalse(r["convergio"])
                self.assertEqual(newton_raphson(f, polo)["estado"], "dominio_inicial")
                self.assertEqual(secante(f, a, polo)["estado"], "dominio_inicial")
                ordenadas = muestrear(f, a, b)["y"]
                self.assertIn(None, ordenadas)
                self.assertLess(ordenadas[0] * ordenadas[-1], 0)
                self.assertEqual(evidencia_muestreo(ordenadas)["clasificacion"], "exploracion_no_concluyente")

    def test_secante_rechaza_un_paso_pequeno_que_cruza_un_polo(self):
        polo = math.pi / 2
        x0, x1 = polo - 5e-5, polo + 3e-5
        # La escala hace que ambos umbrales numéricos se cumplan incluso cerca del polo.
        resultado = secante(FuncionReal("1e-10*tan(x)"), x0, x1)
        self.assertLess(resultado["iteraciones"][-1]["siguiente"], polo)
        self.assertLessEqual(resultado["residuo"], resultado["tolerancia"])
        self.assertLessEqual(resultado["error_absoluto"], resultado["tolerancia"])
        self.assertEqual(resultado["estado"], "continuidad")
        self.assertFalse(resultado["convergio"])

    def test_raiz_par_sin_cambio_de_signo(self):
        f = FuncionReal("x^2")
        for metodo in (biseccion, regla_falsa):
            with self.subTest(metodo=metodo.__name__):
                r = metodo(f, -1, 1)
                self.assertEqual((r["estado"], r["clasificacion"]), ("sin_cambio_de_signo", "no_aplicable"))
        self.assertEqual(newton_raphson(f, 0)["estado"], "exacta")
        self.assertEqual(secante(f, -1, 0)["estado"], "exacta")
        evidencia = evidencia_muestreo(muestrear(f, -1, 1)["y"])
        self.assertEqual(evidencia["clasificacion"], "indicios_numericos")
        self.assertEqual(evidencia["evidencia"]["cambios_de_signo"], 0)
