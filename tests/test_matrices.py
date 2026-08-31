"""Pruebas de las utilidades generales sobre matrices."""

import unittest
from fractions import Fraction

from backend.matrices import (
    convertir_matriz_a_fracciones,
    copiar_matriz,
    es_matriz_rectangular,
    generar_matriz,
)


class PruebasCreacionDeMatrices(unittest.TestCase):
    def test_generar_matriz_respeta_las_dimensiones(self):
        matriz = generar_matriz(3, 4)

        self.assertEqual(len(matriz), 3)
        self.assertEqual([len(fila) for fila in matriz], [4, 4, 4])

    def test_generar_matriz_usa_enteros_entre_0_y_20(self):
        matriz = generar_matriz(4, 4)

        for fila in matriz:
            for numero in fila:
                self.assertIsInstance(numero, int)
                self.assertGreaterEqual(numero, 0)
                self.assertLessEqual(numero, 20)

    def test_copiar_matriz_devuelve_el_mismo_contenido(self):
        original = [[1, 2], [3, 4]]

        self.assertEqual(copiar_matriz(original), original)

    def test_copiar_matriz_no_comparte_las_filas(self):
        original = [[1, 2], [3, 4]]
        copia = copiar_matriz(original)

        copia[0][0] = 99

        self.assertEqual(original, [[1, 2], [3, 4]])

    def test_convertir_matriz_a_fracciones(self):
        convertida = convertir_matriz_a_fracciones([[1, 2], [3, 4]])

        for fila in convertida:
            for numero in fila:
                self.assertIsInstance(numero, Fraction)
        self.assertEqual(convertida, [[1, 2], [3, 4]])


class PruebasValidaciones(unittest.TestCase):
    def test_matriz_rectangular(self):
        self.assertTrue(es_matriz_rectangular([[1, 2], [3, 4]]))
        self.assertFalse(es_matriz_rectangular([[1, 2], [3]]))


if __name__ == "__main__":
    unittest.main()
