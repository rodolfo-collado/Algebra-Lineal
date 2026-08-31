"""Pruebas de las utilidades generales sobre matrices."""

import unittest
from fractions import Fraction

from backend.matrices import (
    convertir_matriz_a_fracciones,
    copiar_matriz,
    es_matriz_rectangular,
    formatear_fraccion,
    generar_matriz,
    validar_matriz_rectangular,
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


class PruebasFormaDeLaMatriz(unittest.TestCase):
    def test_matriz_rectangular(self):
        self.assertTrue(es_matriz_rectangular([[1, 2], [3, 4]]))
        self.assertFalse(es_matriz_rectangular([[1, 2], [3]]))

    def test_matriz_vacia_no_es_rectangular_y_no_falla(self):
        self.assertFalse(es_matriz_rectangular([]))


class PruebasValidacionDeMatrices(unittest.TestCase):
    def test_matriz_vacia(self):
        self.assertEqual(
            validar_matriz_rectangular([]), (False, "Error: La matriz está vacía.")
        )

    def test_matriz_con_fila_vacia(self):
        self.assertEqual(
            validar_matriz_rectangular([[]]),
            (False, "Error: La matriz no tiene columnas."),
        )

    def test_matriz_no_rectangular(self):
        self.assertEqual(
            validar_matriz_rectangular([[1, 2], [3, 4, 5]]),
            (False, "Error: La matriz no es rectangular."),
        )

    def test_fila_vacia_entre_filas_con_datos(self):
        es_valida, mensaje = validar_matriz_rectangular([[1, 2], []])

        self.assertFalse(es_valida)
        self.assertEqual(mensaje, "Error: La matriz no es rectangular.")

    def test_matriz_de_una_fila_y_una_columna(self):
        self.assertEqual(validar_matriz_rectangular([[5]]), (True, ""))

    def test_matriz_de_una_fila_y_varias_columnas(self):
        self.assertEqual(validar_matriz_rectangular([[1, 2, 3]]), (True, ""))

    def test_matriz_de_varias_filas_y_una_columna(self):
        self.assertEqual(validar_matriz_rectangular([[1], [2], [3]]), (True, ""))


class PruebasFormatoDeFracciones(unittest.TestCase):
    def test_fraccion_entera_pierde_el_denominador(self):
        self.assertEqual(formatear_fraccion(Fraction(4, 2)), "2")

    def test_fraccion_no_entera_conserva_el_denominador(self):
        self.assertEqual(formatear_fraccion(Fraction(-5, 4)), "-5/4")


if __name__ == "__main__":
    unittest.main()
