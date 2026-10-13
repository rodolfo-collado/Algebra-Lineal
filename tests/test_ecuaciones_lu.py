"""LU de Ax=b: factorización compartida y evidencia de las dos reducciones."""

import random
import unittest
from copy import deepcopy
from fractions import Fraction as F
from unittest.mock import patch

from backend import ecuaciones_matriciales as ecuaciones
from backend.factorizacion_lu import factorizar_lu
from backend.matrices import matriz_identidad, multiplicar_matrices, multiplicar_matriz_vector
from backend.sistemas import INCONSISTENTE, SOLUCION_UNICA, SOLUCIONES_INFINITAS

A_CLASE = [[3, -7, -2, 2], [-3, 5, 1, 0], [6, -4, 0, -5], [-9, 5, -5, 12]]
B_CLASE = [-9, 5, 7, 11]
Y_CLASE = [-9, -4, 5, 1]
X_CLASE = [3, 4, -6, -1]


class PruebasLU(unittest.TestCase):
    def comprobar_etapa(self, etapa, derecha):
        final = [fila + [valor] for fila, valor in zip(matriz_identidad(len(derecha)), derecha)]
        self.assertTrue(etapa["es_identidad"])
        self.assertEqual(etapa["matriz_final"], final)
        anterior = etapa["matriz_inicial"]
        for paso in etapa["pasos"]:
            self.assertEqual(paso["antes"], anterior)
            self.assertNotIn("<->", paso["operacion"])
            anterior = paso["despues"]
        self.assertEqual(anterior, final)

    def test_ejemplo_de_clase_factoriza_y_resuelve_ambas_etapas(self):
        a, b = deepcopy(A_CLASE), list(B_CLASE)
        with patch.object(ecuaciones, "factorizar_lu", wraps=factorizar_lu) as factorizar:
            r = ecuaciones.resolver_ecuacion_matricial(a, b, "lu")
        factorizar.assert_called_once_with(a)
        self.assertEqual((a, b), (A_CLASE, B_CLASE))
        self.assertEqual(r["y"], Y_CLASE)
        self.assertEqual(r["x"], X_CLASE)
        self.assertEqual(r["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(r["verificacion"], B_CLASE)
        l, u = r["factorizacion"]["l"], r["factorizacion"]["u"]
        self.assertEqual(multiplicar_matrices(l, u), A_CLASE)
        ly, ux = r["etapas_lu"]
        self.assertEqual(ly["matriz_inicial"], [fila + [valor] for fila, valor in zip(l, B_CLASE)])
        self.assertEqual(ux["matriz_inicial"], [fila + [valor] for fila, valor in zip(u, Y_CLASE)])
        self.comprobar_etapa(ly, Y_CLASE)
        self.comprobar_etapa(ux, X_CLASE)

    def test_fracciones_negativos_y_uno_por_uno(self):
        for a, b, x in (([[F(-1, 2), F(1, 3)], [F(3, 4), -2]], [F(-1, 6), F(-5, 4)], [1, 1]),
                        ([[2, 0], [0, -3]], [1, 1], [F(1, 2), F(-1, 3)]),
                        ([[-4]], [6], [F(-3, 2)]), ([[1]], [0], [0])):
            with self.subTest(a=a):
                r = ecuaciones.resolver_ecuacion_matricial(a, b, "lu")
                self.assertEqual(r["x"], x)
                self.assertEqual(r["verificacion"], b)
                self.comprobar_etapa(r["etapas_lu"][0], r["y"])
                self.comprobar_etapa(r["etapas_lu"][1], x)
                self.assertTrue(all(isinstance(valor, F) for valor in r["x"] + r["y"]))

    def test_intercambio_necesario_inicial_o_posterior_detiene_lu(self):
        for a in ([[0, 1], [1, 0]], [[1, 1, 0], [1, 1, 1], [0, 1, 1]]):
            with self.subTest(a=a), patch.object(ecuaciones, "aplicar_gauss_jordan", side_effect=AssertionError("redujo")):
                r = ecuaciones.resolver_ecuacion_matricial(a, [1] * len(a), "lu")
                self.assertFalse(r["factorizacion"]["aplicable"])
                self.assertEqual(r["etapas_lu"], [])
                self.assertIsNone(r["clasificacion"])
                self.assertIsNone(r["x"])
                self.assertIsNone(r["verificacion"])
                self.assertIsNone(r["b_en_generado"])
                self.assertIn("Usa Gauss o Gauss-Jordan", r["justificacion"][0])

    def test_singular_se_clasifica_sin_fingir_identidad_o_solucion_unica(self):
        for a, b, clasificacion in (([[1, 2], [2, 4]], [3, 6], SOLUCIONES_INFINITAS),
                                    ([[1, 2], [2, 4]], [3, 7], INCONSISTENTE),
                                    ([[0, 2], [0, 4]], [2, 4], SOLUCIONES_INFINITAS),
                                    ([[0]], [1], INCONSISTENTE)):
            with self.subTest(a=a, b=b):
                r = ecuaciones.resolver_ecuacion_matricial(a, b, "lu")
                self.assertTrue(r["factorizacion"]["aplicable"])
                self.assertEqual(r["clasificacion"], clasificacion)
                self.assertTrue(r["etapas_lu"][0]["es_identidad"])
                self.assertFalse(r["etapas_lu"][1]["es_identidad"])
                self.assertIsNone(r["x"])
                self.assertIsNone(r["verificacion"])
                jordan = ecuaciones.resolver_ecuacion_matricial(a, b)
                self.assertEqual(r["solucion_general"], jordan["solucion_general"])

    def test_rectangulares_rechazadas_antes_de_factorizar(self):
        for a in ([[1, 0, 1], [0, 1, 1]], [[1, 0], [0, 1], [1, 1]]):
            with self.subTest(a=a), patch.object(ecuaciones, "factorizar_lu", side_effect=AssertionError("factorizó")):
                with self.assertRaisesRegex(ValueError, "requiere una matriz A cuadrada"):
                    ecuaciones.resolver_ecuacion_matricial(a, [1] * len(a), "lu")

    def test_entradas_invalidas_se_rechazan(self):
        for a, b in (([[1]], [True]), ([[1.5]], [1]), ([[1, 2], [3]], [1, 2]), ([[1]], [1, 2])):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                ecuaciones.resolver_ecuacion_matricial(a, b, "lu")

    def test_seguridad_numerica_en_factorizacion_y_reducciones(self):
        with patch("backend.seguridad_numerica.BITS_MAXIMOS", 16):
            with self.assertRaises(ValueError):
                ecuaciones.resolver_ecuacion_matricial([[1]], [2 ** 17], "lu")
            # Entradas pequeñas: un reemplazo en [L|b] crece por encima del límite.
            with self.assertRaises(ValueError):
                ecuaciones.resolver_ecuacion_matricial([[1, 0], [256, 1]], [256, -1], "lu")

    def test_sistemas_exactos_generados_coinciden_con_gauss_y_jordan(self):
        generador = random.Random(94)
        for n in range(1, 6):
            for _ in range(5):
                l = [[F(generador.randint(-3, 3), 2) if i > j else F(i == j) for j in range(n)] for i in range(n)]
                u = [[F(generador.choice((-3, -1, 1, 2)), 3) if i <= j else F(0) for j in range(n)] for i in range(n)]
                a = multiplicar_matrices(l, u)
                x = [F(generador.randint(-4, 4), 3) for _ in range(n)]
                b = multiplicar_matriz_vector(a, x)
                r = ecuaciones.resolver_ecuacion_matricial(a, b, "lu")
                self.assertEqual(r["x"], x)
                self.assertEqual(multiplicar_matrices(r["factorizacion"]["l"], r["factorizacion"]["u"]), a)
                self.comprobar_etapa(r["etapas_lu"][0], r["y"])
                self.comprobar_etapa(r["etapas_lu"][1], x)
                for metodo in ("gauss", "gauss_jordan"):
                    self.assertEqual(ecuaciones.resolver_ecuacion_matricial(a, b, metodo)["x"], x)
