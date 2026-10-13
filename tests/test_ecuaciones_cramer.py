"""Cramer conserva exactamente la evidencia del único motor de Determinantes."""

import unittest
from copy import deepcopy
from fractions import Fraction as F
from unittest.mock import patch

from backend import ecuaciones_matriciales as ecuaciones
from backend.determinantes import calcular_determinante
from backend.matrices import multiplicar_matriz_vector
from backend.sistemas import SOLUCION_UNICA

A_CLASE = [[3, -2], [-5, 4]]
B_CLASE = [6, 8]
A3 = [[2, 1, 3], [0, 4, 2], [1, 0, 5]]
B3 = [12, 2, 17]


class PruebasCramer(unittest.TestCase):
    def resolver(self, a=A_CLASE, b=B_CLASE, metodo="directo_2x2"):
        return ecuaciones.resolver_ecuacion_matricial(a, b, "cramer", metodo)

    def test_diapos_matrices_determinantes_cocientes_y_verificacion(self):
        a, b = deepcopy(A_CLASE), list(B_CLASE)
        esperadas = [a, [[6, -2], [8, 4]], [[3, 6], [-5, 8]]]
        with patch.object(ecuaciones, "calcular_determinante", wraps=calcular_determinante) as motor:
            r = self.resolver(a, b)
        self.assertEqual([c.args for c in motor.call_args_list], [(m, "directo_2x2") for m in esperadas])
        self.assertEqual((a, b), (A_CLASE, B_CLASE))
        evidencia = r["cramer"]
        calculos = [evidencia["principal"], *(e["calculo"] for e in evidencia["reemplazos"])]
        self.assertEqual([c["matriz"] for c in calculos], esperadas)
        self.assertEqual([c["determinante"] for c in calculos], [2, 40, 54])
        self.assertEqual([(c["ad"], c["bc"]) for c in calculos], [(12, 10), (24, -16), (24, -30)])
        self.assertEqual([e["columna"] for e in evidencia["reemplazos"]], [1, 2])
        self.assertEqual([e["valor"] for e in evidencia["reemplazos"]], [20, 27])
        self.assertEqual(r["x"], [20, 27])
        self.assertEqual(r["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(r["verificacion"], B_CLASE)

    def test_todos_los_metodos_conservan_su_evidencia_y_no_usan_sistemas(self):
        for metodo in ("sarrus", "cofactores", "lu", "reduccion"):
            with self.subTest(metodo=metodo), \
                    patch.object(ecuaciones, "resolver_sistema_gauss", side_effect=AssertionError("Gauss")), \
                    patch.object(ecuaciones, "aplicar_gauss_jordan", side_effect=AssertionError("Jordan")):
                r = self.resolver(A3, B3, metodo)
                calculos = [r["cramer"]["principal"], *(e["calculo"] for e in r["cramer"]["reemplazos"])]
                self.assertEqual([c["determinante"] for c in calculos], [30, 60, -30, 90])
                self.assertEqual(r["x"], [2, -1, 3])
                self.assertEqual(r["verificacion"], B3)
                for calculo in calculos:
                    self.assertEqual(calculo, calcular_determinante(calculo["matriz"], metodo))

    def test_fracciones_negativos_y_uno_por_uno(self):
        for a, x in (([[F(-1, 2), F(1, 3)], [F(3, 4), -2]], [F(2, 3), F(-5, 7)]),
                     ([[-4]], [F(-3, 2)]), ([[2, 0], [0, -3]], [0, F(-1, 3)])):
            b = multiplicar_matriz_vector(a, x)
            for metodo in ("cofactores", "reduccion"):
                with self.subTest(a=a, metodo=metodo):
                    r = self.resolver(a, b, metodo)
                    self.assertEqual(r["x"], x)
                    self.assertEqual(r["verificacion"], b)
                    self.assertTrue(all(isinstance(v, F) for v in r["x"]))

    def test_reemplazo_solo_cambia_una_columna_y_no_comparte_filas(self):
        a, b = deepcopy(A3), list(B3)
        matrices = ecuaciones.matrices_de_cramer(a, b)
        for columna, matriz in enumerate(matrices):
            for i, fila in enumerate(matriz):
                self.assertEqual(fila[columna], b[i])
                self.assertEqual(fila[:columna] + fila[columna + 1:], a[i][:columna] + a[i][columna + 1:])
        matrices[0][0][1] = 999
        self.assertEqual((a, b), (A3, B3))
        self.assertEqual(matrices[1][0][1], B3[0])

    def test_d_cero_detiene_sin_calcular_di_ni_clasificar(self):
        for b in ([3, 6], [3, 7]):
            with self.subTest(b=b), patch.object(ecuaciones, "calcular_determinante", wraps=calcular_determinante) as motor:
                r = self.resolver([[1, 2], [2, 4]], b)
                self.assertEqual(motor.call_count, 1)
                self.assertEqual(r["cramer"]["principal"]["determinante"], 0)
                self.assertEqual(r["cramer"]["reemplazos"], [])
                for nombre in ("clasificacion", "x", "verificacion", "b_en_generado"):
                    self.assertIsNone(r[nombre])
                self.assertIn("Gauss o Gauss-Jordan", r["justificacion"][0])

    def test_lu_no_aplicable_en_a_o_en_una_ai_no_cambia_de_motor(self):
        for a, b, llamadas in (([[0, 1], [1, 0]], [1, 2], 1), ([[2, 1], [1, 2]], [0, 3], 2)):
            with self.subTest(a=a), patch.object(ecuaciones, "calcular_determinante", wraps=calcular_determinante) as motor:
                r = self.resolver(a, b, "lu")
                self.assertEqual(motor.call_count, llamadas)
                self.assertTrue(all(c.args[1] == "lu" for c in motor.call_args_list))
                self.assertEqual(r["cramer"]["motivo"], "metodo_determinante")
                self.assertIsNone(r["x"])
                self.assertIsNone(r["clasificacion"])
                self.assertIn("Reducción por filas", r["justificacion"][0])

    def test_rectangulares_y_entradas_invalidas_se_rechazan(self):
        for a, b in (([[1, 2, 3]], [1]), ([[1], [2]], [1, 2])):
            with self.subTest(a=a), patch.object(ecuaciones, "calcular_determinante", side_effect=AssertionError("calculó")):
                with self.assertRaisesRegex(ValueError, "requiere una matriz A cuadrada"):
                    self.resolver(a, b)
        for a, b in (([[1]], [True]), ([[1.5]], [1]), ([[1]], [1, 2]), ([[1, 2], [3]], [1, 2])):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                self.resolver(a, b, "cofactores")

    def test_metodo_determinante_invalido_o_de_otro_tamano(self):
        for metodo in ("inventado", "sarrus", "", None, [], True):
            with self.subTest(metodo=metodo), self.assertRaises(ValueError):
                self.resolver(metodo=metodo)

    def test_seguridad_numerica_se_conserva(self):
        with patch("backend.seguridad_numerica.BITS_MAXIMOS", 16), self.assertRaises(ValueError):
            self.resolver([[1]], [2 ** 17], "cofactores")
        with patch("backend.seguridad_numerica.BITS_MAXIMOS", 16), self.assertRaises(ValueError):
            self.resolver([[F(1, 32768)]], [32768], "cofactores")

    def test_regresion_gauss_jordan_y_lu_con_el_mismo_sistema(self):
        for metodo in ("gauss", "gauss_jordan", "lu"):
            with self.subTest(metodo=metodo):
                r = ecuaciones.resolver_ecuacion_matricial(A_CLASE, B_CLASE, metodo)
                self.assertEqual(r["x"], [20, 27])
                self.assertEqual(r["verificacion"], B_CLASE)
                self.assertNotIn("cramer", r)
