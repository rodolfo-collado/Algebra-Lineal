"""Pruebas del escalonamiento por el metodo de Gauss."""

import unittest
from fractions import Fraction

from backend.gauss import aplicar_gauss
from backend.gauss_jordan import aplicar_gauss_jordan


class PruebasValidaciones(unittest.TestCase):
    def test_matriz_vacia_lanza_valueerror(self):
        with self.assertRaises(ValueError):
            aplicar_gauss([])

    def test_matriz_con_fila_vacia_lanza_valueerror(self):
        with self.assertRaises(ValueError):
            aplicar_gauss([[]])

    def test_matriz_dentada_lanza_valueerror(self):
        with self.assertRaises(ValueError):
            aplicar_gauss([[1, 2], [3, 4, 5]])

    def test_no_modifica_la_matriz_original(self):
        matriz = [[2, 1], [1, 1]]

        aplicar_gauss(matriz)

        self.assertEqual(matriz, [[2, 1], [1, 1]])


class PruebasFormaEscalonada(unittest.TestCase):
    def test_gauss_deja_forma_escalonada_y_no_reducida(self):
        matriz_escalonada, _, _ = aplicar_gauss([[1, 1, 3], [1, -1, 1]], 2)

        self.assertEqual(matriz_escalonada, [[1, 1, 3], [0, 1, 1]])

    def test_gauss_jordan_sobre_la_misma_matriz_si_reduce(self):
        matriz_reducida, _, _ = aplicar_gauss_jordan([[1, 1, 3], [1, -1, 1]], 2)

        self.assertEqual(matriz_reducida, [[1, 0, 2], [0, 1, 1]])

    def test_no_elimina_hacia_arriba(self):
        # La matriz ya está escalonada: Gauss no tiene nada que hacer, mientras
        # que Gauss-Jordan todavía debe limpiar por encima del pivote.
        matriz = [[1, 2, 3], [0, 1, 4]]

        escalonada, pasos_gauss, _ = aplicar_gauss(matriz)
        reducida, pasos_gauss_jordan, _ = aplicar_gauss_jordan(matriz)

        self.assertEqual(escalonada, [[1, 2, 3], [0, 1, 4]])
        self.assertEqual(pasos_gauss, [])
        self.assertEqual(reducida, [[1, 0, -5], [0, 1, 4]])
        self.assertEqual(len(pasos_gauss_jordan), 1)

    def test_debajo_de_cada_pivote_solo_quedan_ceros(self):
        matriz = [[1, 2, 3, 6], [2, -3, 2, 14], [3, 1, -1, -2]]
        matriz_escalonada, _, pivotes = aplicar_gauss(matriz, 3)

        for fila, columna in pivotes:
            self.assertEqual(matriz_escalonada[fila][columna], 1)
            for fila_inferior in range(fila + 1, len(matriz_escalonada)):
                self.assertEqual(matriz_escalonada[fila_inferior][columna], 0)

    def test_encima_de_los_pivotes_se_conservan_los_coeficientes(self):
        matriz_escalonada, _, _ = aplicar_gauss([[1, 2, 3, 6], [2, -3, 2, 14]], 3)

        self.assertEqual(matriz_escalonada[0], [1, 2, 3, 6])

    def test_matriz_ya_escalonada_no_genera_pasos(self):
        _, pasos, pivotes = aplicar_gauss([[1, 2, 3], [0, 1, 4]], 2)

        self.assertEqual(pasos, [])
        self.assertEqual(pivotes, [(0, 0), (1, 1)])


class PruebasPivotes(unittest.TestCase):
    def test_pivote_inicial_en_cero_provoca_intercambio(self):
        matriz_escalonada, pasos, pivotes = aplicar_gauss([[0, 1, 1], [1, 0, 2]], 2)

        self.assertEqual(pasos[0]["operacion"], "F1 <-> F2")
        self.assertEqual(matriz_escalonada, [[1, 0, 2], [0, 1, 1]])
        self.assertEqual(pivotes, [(0, 0), (1, 1)])

    def test_intercambio_con_varias_filas_en_cero(self):
        matriz = [[0, 0, 1], [0, 0, 2], [1, 1, 3]]
        matriz_escalonada, pasos, pivotes = aplicar_gauss(matriz, 2)

        self.assertEqual(pasos[0]["operacion"], "F1 <-> F3")
        self.assertEqual(matriz_escalonada[0], [1, 1, 3])
        self.assertEqual(pivotes, [(0, 0)])

    def test_columna_sin_pivote_se_salta(self):
        matriz_escalonada, _, pivotes = aplicar_gauss([[0, 1], [0, 2]])

        self.assertEqual(matriz_escalonada, [[0, 1], [0, 0]])
        self.assertEqual(pivotes, [(0, 1)])

    def test_matriz_de_solo_ceros_no_tiene_pivotes(self):
        matriz_escalonada, pasos, pivotes = aplicar_gauss([[0, 0], [0, 0]])

        self.assertEqual(matriz_escalonada, [[0, 0], [0, 0]])
        self.assertEqual(pasos, [])
        self.assertEqual(pivotes, [])

    def test_limitar_las_columnas_de_pivote(self):
        # La última columna queda fuera de la búsqueda de pivotes.
        matriz_escalonada, _, pivotes = aplicar_gauss([[1, 1, 2], [1, 1, 5]], 2)

        self.assertEqual(matriz_escalonada, [[1, 1, 2], [0, 0, 3]])
        self.assertEqual(pivotes, [(0, 0)])

    def test_mas_filas_que_columnas_deja_filas_nulas(self):
        matriz_escalonada, _, pivotes = aplicar_gauss([[1, 1, 3], [1, -1, 1], [2, 0, 4]], 2)

        self.assertEqual(matriz_escalonada, [[1, 1, 3], [0, 1, 1], [0, 0, 0]])
        self.assertEqual(pivotes, [(0, 0), (1, 1)])


class PruebasFracciones(unittest.TestCase):
    def test_el_escalonamiento_conserva_fracciones_exactas(self):
        matriz_escalonada, _, _ = aplicar_gauss([[2, 1, 5], [1, -1, 1]], 2)

        self.assertEqual(
            matriz_escalonada,
            [[1, Fraction(1, 2), Fraction(5, 2)], [0, 1, 1]]
        )

    def test_no_aparecen_floats(self):
        matriz_escalonada, _, _ = aplicar_gauss([[3, 0, 1], [0, 3, 1]], 2)

        for fila in matriz_escalonada:
            for numero in fila:
                self.assertNotIsInstance(numero, float)
                self.assertIsInstance(numero, Fraction)

    def test_entrada_con_fracciones(self):
        matriz = [[Fraction(1, 2), Fraction(1, 3), 1], [Fraction(1, 4), 1, 2]]
        matriz_escalonada, _, pivotes = aplicar_gauss(matriz, 2)

        self.assertEqual(matriz_escalonada[0], [1, Fraction(2, 3), 2])
        self.assertEqual(pivotes, [(0, 0), (1, 1)])


class PruebasRegistroDePasos(unittest.TestCase):
    def test_los_pasos_registran_la_matriz_antes_y_despues(self):
        _, pasos, _ = aplicar_gauss([[1, 1], [2, 2]], 1)

        self.assertEqual(len(pasos), 1)
        self.assertEqual(pasos[0]["antes"], [[1, 1], [2, 2]])
        self.assertEqual(pasos[0]["operacion"], "F2 = F2 - (2)F1")
        self.assertEqual(pasos[0]["despues"], [[1, 1], [0, 0]])

    def test_la_normalizacion_registra_su_operacion(self):
        _, pasos, _ = aplicar_gauss([[2, 1]], 1)

        self.assertEqual(pasos[0]["operacion"], "F1 = (1/2)F1")
        self.assertEqual(pasos[0]["despues"], [[1, Fraction(1, 2)]])


if __name__ == "__main__":
    unittest.main()
