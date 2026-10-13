"""Recomendaciones didácticas, independientes del determinante y del presupuesto."""

import unittest
from fractions import Fraction as F
from random import Random
from unittest.mock import patch

from backend.determinantes import analizar_matriz_para_determinante as analizar
from backend.factorizacion_lu import factorizar_lu
from backend.seguridad_numerica import BITS_MAXIMOS


def densa(n):
    return [[n + 1 if i == j else 1 for j in range(n)] for i in range(n)]


class Recomendador(unittest.TestCase):
    def test_1x1_y_2x2_usan_la_regla_mas_corta(self):
        for a, metodo in (([[0]], "cofactores"), ([[F(-3, 7)]], "cofactores"),
                          ([[2, 1], [3, 4]], "directo_2x2"), ([[0, 1], [1, 0]], "directo_2x2")):
            with self.subTest(a=a):
                self.assertEqual(analizar(a)["metodo_recomendado"], metodo)

    def test_3x3_densa_prefiere_sarrus(self):
        d = analizar([[1, 2, 3], [4, 5, 6], [7, 8, 10]])
        self.assertEqual(d["metodo_recomendado"], "sarrus")
        self.assertEqual(d["costos"], {"cofactores": 30, "sarrus": 25})

    def test_3x3_con_muchos_ceros_prefiere_cofactores(self):
        d = analizar([[2, 0, 0], [1, 3, 4], [5, 6, 7]])
        self.assertEqual(d["metodo_recomendado"], "cofactores")
        self.assertEqual(d["expansion"], {"eje": "fila", "indice": 1, "ceros": 2})
        self.assertEqual(d["costos"]["cofactores"], 12)

    def test_fila_y_columna_favorables_siguen_la_expansion_del_motor(self):
        a = [[2, 0, 0, 0], [1, 3, 4, 5], [6, 7, 8, 9], [1, 2, 3, 5]]
        for matriz, eje in ((a, "fila"), (list(map(list, zip(*a))), "columna")):
            with self.subTest(eje=eje):
                d = analizar(matriz)
                self.assertEqual(d["metodo_recomendado"], "cofactores")
                self.assertEqual(d["expansion"], {"eje": eje, "indice": 1, "ceros": 3})
                self.assertEqual(d["costos"]["cofactores"], 45)

    def test_menores_con_ceros_se_analizan_recursivamente(self):
        a = [[2, 0, 0, 0], [1, 3, 0, 0], [1, 1, 4, 0], [1, 1, 1, 5]]
        d = analizar(a)
        self.assertEqual(d["metodo_recomendado"], "cofactores")
        self.assertEqual(d["costos"]["cofactores"], 27)

    def test_una_fila_con_ceros_no_basta_si_el_menor_es_denso(self):
        a = densa(6)
        a[0] = [7, 0, 0, 0, 0, 0]
        d = analizar(a)
        self.assertEqual(d["expansion"]["ceros"], 5)
        self.assertGreater(d["costos"]["cofactores"], d["costos"]["lu"])
        self.assertEqual(d["metodo_recomendado"], "lu")

    def test_triangular_superior_incluida_singular_no_necesita_eliminacion(self):
        for n in (3, 4, 7):
            for ultimo in (2, 0):
                a = [[2 if i == j else 1 if j > i else 0 for j in range(n)] for i in range(n)]
                a[-1][-1] = ultimo
                with self.subTest(n=n, ultimo=ultimo):
                    d = analizar(a)
                    self.assertEqual((d["metodo_recomendado"], d["razon"]),
                                     ("reduccion", "triangular_superior"))
                    self.assertIsNone(d["lu"])

    def test_triangular_con_cero_diagonal_inicial_o_interior_no_asume_cero_reemplazos(self):
        for a in ([[0, 1, 1], [0, 2, 1], [0, 0, 2]],
                  [[2, 1, 1, 1], [0, 0, 1, 1], [0, 0, 3, 1], [0, 0, 0, 4]]):
            with self.subTest(a=a):
                self.assertEqual(analizar(a)["metodo_recomendado"], "cofactores")
                self.assertTrue(factorizar_lu(a)["pasos"])

    def test_triangular_inferior_grande_respeta_limite_de_cofactores(self):
        a = [[2 if i == j else 1 if j < i else 0 for j in range(7)] for i in range(7)]
        d = analizar(a)
        self.assertEqual(d["metodo_recomendado"], "lu")
        self.assertNotIn("cofactores", d["costos"])

    def test_lu_buena_opcion_en_densas_de_4_y_7(self):
        for n in (4, 7):
            with self.subTest(n=n):
                a = densa(n)
                d = analizar(a)
                self.assertEqual(d["metodo_recomendado"], "lu")
                self.assertTrue(d["lu"]["aplicable"])
                self.assertTrue(factorizar_lu(a)["aplicable"])

    def test_lu_no_se_recomienda_si_falla_un_pivote_inicial_o_posterior(self):
        casos = (
            ([[0, 1, 2, 3], [2, 3, 4, 5], [1, 4, 8, 2], [3, 5, 2, 7]], 1),
            ([[1, 1, 1, 1], [1, 1, 2, 3], [1, 2, 3, 4], [2, 3, 4, 7]], 2),
        )
        for a, fila in casos:
            with self.subTest(fila=fila):
                d = analizar(a)
                self.assertEqual((d["metodo_recomendado"], d["razon"]),
                                 ("reduccion", "lu_necesita_intercambio"))
                self.assertFalse(d["lu"]["aplicable"])
                self.assertEqual(d["lu"]["pivote_nulo"], {"fila": fila, "columna": fila})
                self.assertEqual(d["lu"]["pivote_nulo"], factorizar_lu(a)["pivote_nulo"])

    def test_columnas_nulas_se_saltan_sin_avanzar_la_fila(self):
        for a in ([[0, 2, 1, 3], [0, 4, 5, 7], [0, 2, 4, 8], [0, 6, 9, 10]],
                  [[0, 1, 2, 3], [0, 2, 4, 6], [0, 0, 1, 2], [0, 0, 2, 5]]):
            with self.subTest(a=a):
                d, lu = analizar(a)["lu"], factorizar_lu(a)
                self.assertEqual(d["aplicable"], lu["aplicable"])
                self.assertEqual(d["pivote_nulo"], lu["pivote_nulo"])

    def test_comprobacion_de_lu_coincide_con_el_motor_en_fracciones_y_singulares(self):
        rng = Random(130)
        for _ in range(100):
            a = [[F(rng.randint(-2, 3), rng.randint(1, 3)) for _ in range(4)] for _ in range(4)]
            original = [fila[:] for fila in a]
            d, lu = analizar(a), factorizar_lu(a)
            self.assertEqual(a, original)
            if d["lu"] is not None:
                self.assertEqual(d["lu"]["aplicable"], lu["aplicable"])
                self.assertEqual(d["lu"]["pivote_nulo"], lu["pivote_nulo"])
            if d["metodo_recomendado"] == "lu":
                self.assertTrue(lu["aplicable"])

    def test_el_analisis_no_calcula_el_determinante_ni_consulta_el_presupuesto(self):
        with patch("backend.determinantes.calcular_determinante", side_effect=AssertionError("calculó")), \
                patch("backend.factorizacion_lu.factorizar_lu", side_effect=AssertionError("factorizó")), \
                patch("backend.determinantes.presupuesto.estimar_determinante", side_effect=AssertionError("presupuestó")):
            self.assertEqual(analizar(densa(4))["metodo_recomendado"], "lu")

    def test_limite_numerico_no_se_confunde_con_intercambio(self):
        grande = 1 << 7000
        a = [[F(1, grande), 1, 1, 1], [grande, 1, 1, 1], [1, 2, 3, 4], [2, 3, 4, 7]]
        d = analizar(a)
        self.assertIsNone(d["lu"]["aplicable"])
        self.assertIsNone(d["lu"]["pivote_nulo"])
        self.assertEqual((d["metodo_recomendado"], d["razon"]), ("reduccion", "lu_no_verificada"))

    def test_validacion_comun_rechaza_entradas_invalidas(self):
        for a in ([], [[]], [[1, 2]], [[1], [1, 2]], [[True]], [[0.5]], [["1"]], [[1 << BITS_MAXIMOS]]):
            with self.subTest(a=a), self.assertRaises(ValueError):
                analizar(a)


if __name__ == "__main__":
    unittest.main()
