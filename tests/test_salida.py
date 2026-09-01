"""Pruebas de caracterizacion del formateo de matrices."""

import unittest
from fractions import Fraction

from frontend.terminal.salida import (
    formatear_numero,
    imprimir_paso,
    obtener_lineas_matriz,
)
from tests.ayudas import capturar, sin_ansi


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


class PruebasTextoSinColor(unittest.TestCase):
    """El texto matematico se genera limpio; el color se aplica al imprimir."""

    def test_formatear_numero_no_incluye_codigos_ansi(self):
        self.assertNotIn("\x1b", formatear_numero(Fraction(-11, 7)))

    def test_obtener_lineas_matriz_no_incluye_codigos_ansi(self):
        lineas = obtener_lineas_matriz([[Fraction(-11, 7), 2], [3, 4]])

        for linea in lineas:
            self.assertNotIn("\x1b", linea)

    def test_fraccion_negativa_se_alinea_correctamente(self):
        lineas = obtener_lineas_matriz([[Fraction(-11, 7), 2], [3, 4]])

        self.assertEqual(lineas, ["[ -11/7   2 ]", "[     3   4 ]"])


class PruebasPasoDeReduccion(unittest.TestCase):
    PASO = {
        "antes": [[1, 1, 3], [1, -1, 1]],
        "operacion": "F2 = F2 - (1)F1",
        "despues": [[1, 1, 3], [0, -2, -2]]
    }

    def test_los_codigos_ansi_no_descuadran_las_matrices(self):
        salida = sin_ansi(capturar(imprimir_paso, self.PASO))

        self.assertEqual(
            salida.splitlines(),
            [
                "[   1   1   3 ]                   [   1   1   3 ]",
                "[   1  -1   1 ]  F2 = F2 - (1)F1  [   0  -2  -2 ]"
            ]
        )

    def test_solo_la_operacion_lleva_color(self):
        lineas = capturar(imprimir_paso, self.PASO).splitlines()

        self.assertNotIn("\x1b", lineas[0])
        self.assertIn("\x1b[0m", lineas[1])


if __name__ == "__main__":
    unittest.main()
