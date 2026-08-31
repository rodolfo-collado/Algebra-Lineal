"""Pruebas de caracterizacion del formateo de matrices."""

import unittest
from fractions import Fraction

from salida import formatear_numero, obtener_lineas_matriz


class PruebasFormatoDeNumeros(unittest.TestCase):
    def test_fraccion_entera_se_muestra_sin_denominador(self):
        self.assertEqual(formatear_numero(Fraction(3, 1)), "3")

    def test_fraccion_no_entera_conserva_el_denominador(self):
        self.assertEqual(formatear_numero(Fraction(1, 2)), "1/2")

    def test_entero_normal(self):
        self.assertEqual(formatear_numero(7), "7")


class PruebasLineasDeMatriz(unittest.TestCase):
    def test_columnas_alineadas_con_ancho_minimo(self):
        lineas = obtener_lineas_matriz([[1, 2], [3, 4]])

        self.assertEqual(lineas, ["[   1   2 ]", "[   3   4 ]"])

    def test_el_ancho_se_ajusta_al_valor_mas_largo(self):
        lineas = obtener_lineas_matriz([[Fraction(1, 2), 100], [-3, 4]])

        self.assertEqual(lineas, ["[ 1/2 100 ]", "[  -3   4 ]"])


if __name__ == "__main__":
    unittest.main()
