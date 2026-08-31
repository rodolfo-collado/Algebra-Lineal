"""Pruebas de la reduccion por Gauss-Jordan."""

import unittest
from fractions import Fraction

from backend.gauss_jordan import (
    aplicar_gauss_jordan,
    buscar_fila_pivote,
    obtener_rango,
    texto_factor,
)


class PruebasValidaciones(unittest.TestCase):
    def test_matriz_vacia_lanza_valueerror(self):
        with self.assertRaises(ValueError):
            aplicar_gauss_jordan([])

    def test_matriz_con_fila_vacia_lanza_valueerror(self):
        with self.assertRaises(ValueError):
            aplicar_gauss_jordan([[]])

    def test_matriz_dentada_lanza_valueerror(self):
        with self.assertRaises(ValueError):
            aplicar_gauss_jordan([[1, 2], [3, 4, 5]])


class PruebasDimensionesPequenas(unittest.TestCase):
    def test_matriz_de_1x1(self):
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[5]])

        self.assertEqual(matriz_reducida, [[1]])
        self.assertEqual(pivotes, [(0, 0)])

    def test_matriz_de_1xn(self):
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[2, 4, 6]])

        self.assertEqual(matriz_reducida, [[1, 2, 3]])
        self.assertEqual(pivotes, [(0, 0)])

    def test_matriz_de_nx1(self):
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[2], [4]])

        self.assertEqual(matriz_reducida, [[1], [0]])
        self.assertEqual(pivotes, [(0, 0)])


class PruebasMatricesRectangulares(unittest.TestCase):
    def test_matriz_de_2x3(self):
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[1, 2, 3], [4, 5, 6]])

        self.assertEqual(matriz_reducida, [[1, 0, -1], [0, 1, 2]])
        self.assertEqual(pivotes, [(0, 0), (1, 1)])

    def test_matriz_de_3x2(self):
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[1, 2], [3, 4], [5, 6]])

        self.assertEqual(matriz_reducida, [[1, 0], [0, 1], [0, 0]])
        self.assertEqual(pivotes, [(0, 0), (1, 1)])

    def test_matriz_de_2x4(self):
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[1, 2, 3, 4], [5, 6, 7, 8]])

        self.assertEqual(matriz_reducida, [[1, 0, -1, -2], [0, 1, 2, 3]])
        self.assertEqual(pivotes, [(0, 0), (1, 1)])

    def test_matriz_de_4x3(self):
        matriz = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [1, 0, 0]]
        matriz_reducida, _, pivotes = aplicar_gauss_jordan(matriz)

        self.assertEqual(
            matriz_reducida, [[1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0]]
        )
        self.assertEqual(pivotes, [(0, 0), (1, 1), (2, 2)])


class PruebasPivotes(unittest.TestCase):
    def test_buscar_fila_pivote(self):
        matriz = [[0, 1], [0, 2], [3, 4]]

        self.assertEqual(buscar_fila_pivote(matriz, 0, 0), 2)
        self.assertEqual(buscar_fila_pivote(matriz, 0, 1), 0)
        self.assertIsNone(buscar_fila_pivote([[0, 1], [0, 2]], 0, 0))

    def test_pivote_inicial_en_cero_provoca_intercambio(self):
        matriz_reducida, pasos, _ = aplicar_gauss_jordan([[0, 1, 1], [1, 0, 2]])

        self.assertEqual(pasos[0]["operacion"], "F1 <-> F2")
        self.assertEqual(matriz_reducida, [[1, 0, 2], [0, 1, 1]])

    def test_columna_sin_pivote_se_salta(self):
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[0, 1], [0, 2]])

        self.assertEqual(matriz_reducida, [[0, 1], [0, 0]])
        self.assertEqual(pivotes, [(0, 1)])

    def test_fila_completa_de_ceros(self):
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[1, 2], [0, 0]])

        self.assertEqual(matriz_reducida, [[1, 2], [0, 0]])
        self.assertEqual(pivotes, [(0, 0)])

    def test_varias_filas_quedan_en_cero(self):
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[1, 2], [2, 4], [3, 6]])

        self.assertEqual(matriz_reducida, [[1, 2], [0, 0], [0, 0]])
        self.assertEqual(pivotes, [(0, 0)])

    def test_matriz_de_solo_ceros_no_tiene_pivotes(self):
        matriz_reducida, pasos, pivotes = aplicar_gauss_jordan([[0, 0], [0, 0]])

        self.assertEqual(matriz_reducida, [[0, 0], [0, 0]])
        self.assertEqual(pivotes, [])
        self.assertEqual(pasos, [])

    def test_obtener_rango_de_una_matriz_sin_reducir(self):
        # El rango se calcula reduciendo, no contando filas no nulas.
        self.assertEqual(obtener_rango([[1, 2], [2, 4]]), 1)
        self.assertEqual(obtener_rango([[1, 2], [3, 4]]), 2)
        self.assertEqual(obtener_rango([[0, 0], [0, 0]]), 0)
        self.assertEqual(obtener_rango([[1, 2], [3, 4], [5, 6]]), 2)

    def test_texto_factor(self):
        self.assertEqual(texto_factor(Fraction(3)), "- (3)")
        self.assertEqual(texto_factor(Fraction(-3)), "+ (3)")
        self.assertEqual(texto_factor(Fraction(1, 2)), "- (1/2)")


class PruebasReduccion(unittest.TestCase):
    def test_matriz_cuadrada_se_reduce_a_la_identidad(self):
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[2, 1], [1, 1]])

        self.assertEqual(matriz_reducida, [[1, 0], [0, 1]])
        self.assertEqual(pivotes, [(0, 0), (1, 1)])

    def test_matriz_ya_reducida_no_genera_pasos(self):
        _, pasos, _ = aplicar_gauss_jordan([[1, 0], [0, 1]])

        self.assertEqual(pasos, [])

    def test_matriz_rectangular_ya_reducida_no_genera_pasos(self):
        _, pasos, _ = aplicar_gauss_jordan([[1, 0, 3], [0, 1, 4]])

        self.assertEqual(pasos, [])

    def test_los_pasos_registran_la_matriz_antes_y_despues(self):
        _, pasos, _ = aplicar_gauss_jordan([[1, 1], [2, 2]])

        self.assertEqual(len(pasos), 1)
        self.assertEqual(pasos[0]["antes"], [[1, 1], [2, 2]])
        self.assertEqual(pasos[0]["operacion"], "F2 = F2 - (2)F1")
        self.assertEqual(pasos[0]["despues"], [[1, 1], [0, 0]])

    def test_la_normalizacion_registra_su_operacion(self):
        _, pasos, _ = aplicar_gauss_jordan([[2, 1]])

        self.assertEqual(pasos[0]["operacion"], "F1 = (1/2)F1")
        self.assertEqual(pasos[0]["despues"], [[1, Fraction(1, 2)]])

    def test_gauss_jordan_opera_con_fracciones_exactas(self):
        matriz_reducida, _, _ = aplicar_gauss_jordan([[3, 0, 1], [0, 3, 1]])

        for fila in matriz_reducida:
            for numero in fila:
                self.assertIsInstance(numero, Fraction)
        self.assertEqual(matriz_reducida[0][2], Fraction(1, 3))

    def test_las_fracciones_no_se_convierten_a_float(self):
        matriz_reducida, _, _ = aplicar_gauss_jordan([[3, 2], [0, 4]])

        self.assertEqual(matriz_reducida, [[1, 0], [0, 1]])
        for fila in matriz_reducida:
            for numero in fila:
                self.assertNotIsInstance(numero, float)

    def test_limitar_las_columnas_de_pivote(self):
        # La última columna queda fuera de la búsqueda de pivotes.
        matriz_reducida, _, pivotes = aplicar_gauss_jordan([[1, 1, 2], [1, 1, 5]], 2)

        self.assertEqual(matriz_reducida, [[1, 1, 2], [0, 0, 3]])
        self.assertEqual(pivotes, [(0, 0)])

    def test_no_modifica_la_matriz_original(self):
        matriz = [[2, 1], [1, 1]]

        aplicar_gauss_jordan(matriz)

        self.assertEqual(matriz, [[2, 1], [1, 1]])


if __name__ == "__main__":
    unittest.main()
