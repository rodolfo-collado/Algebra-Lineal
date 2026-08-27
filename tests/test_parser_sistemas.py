import unittest
from fractions import Fraction

from Semana_1.backend.parser_sistemas import parsear_sistema


class PruebasParserSistemas(unittest.TestCase):
    def test_parsea_sistema_directo(self):
        texto = "x1 + x2 = 3; x1 - x2 = 1"

        self.assertEqual(
            parsear_sistema(texto),
            [[1, 1, 3], [1, -1, 1]]
        )

    def test_parsea_variables_ausentes_y_tres_incognitas(self):
        texto = "x1 - 3x2 - 5x3 = 0; x2 + x3 = 3"

        self.assertEqual(
            parsear_sistema(texto),
            [[1, -3, -5, 0], [0, 1, 1, 3]]
        )

    def test_parsea_variables_ausentes_en_ecuaciones(self):
        texto = "x1 + x3 = 5; x2 - x3 = 2"

        self.assertEqual(
            parsear_sistema(texto),
            [[1, 0, 1, 5], [0, 1, -1, 2]]
        )

    def test_parsea_coeficientes_implicitos(self):
        self.assertEqual(
            parsear_sistema("-x1 + x2 = -4"),
            [[-1, 1, -4]]
        )

    def test_parsea_fracciones_decimales_y_espacios(self):
        matriz = parsear_sistema(" 0.5 x1 + 3/4x2 = 5/2 ")

        self.assertEqual(
            matriz,
            [[Fraction(1, 2), Fraction(3, 4), Fraction(5, 2)]]
        )

    def test_rechaza_formatos_invalidos(self):
        entradas_invalidas = [
            "x1 + = 3",
            "x0 + x1 = 4",
            "x1 + abc = 2",
            "x1 + x2",
            "x1 = 2 = 3"
        ]

        for texto in entradas_invalidas:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    parsear_sistema(texto)


if __name__ == "__main__":
    unittest.main()
