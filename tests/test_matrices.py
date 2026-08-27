import unittest
from fractions import Fraction

from Semana_1.backend.matrices import (
    aplicar_gauss,
    aplicar_gauss_jordan,
    validar_dimensiones_gauss_jordan
)


class PruebasMatrices(unittest.TestCase):
    def test_gauss_no_hace_eliminacion_hacia_arriba(self):
        matriz = [[1, 1, 3], [1, -1, 1]]

        escalonada, _, _ = aplicar_gauss(matriz)

        self.assertEqual(
            escalonada,
            [
                [Fraction(1), Fraction(1), Fraction(3)],
                [Fraction(0), Fraction(1), Fraction(1)]
            ]
        )

    def test_gauss_jordan_reutiliza_gauss_en_matriz_rectangular(self):
        matriz = [[1, 2, 3], [4, 5, 6]]

        es_valida, _ = validar_dimensiones_gauss_jordan(matriz)
        escalonada, pasos_gauss, pivotes = aplicar_gauss(matriz)
        reducida, pasos_jordan, _ = aplicar_gauss_jordan(matriz)

        self.assertTrue(es_valida)
        self.assertEqual(len(pivotes), 2)
        self.assertEqual(
            escalonada[1],
            [Fraction(0), Fraction(1), Fraction(2)]
        )
        self.assertEqual(
            reducida,
            [
                [Fraction(1), Fraction(0), Fraction(-1)],
                [Fraction(0), Fraction(1), Fraction(2)]
            ]
        )
        self.assertGreater(len(pasos_jordan), len(pasos_gauss))

    def test_los_calculos_se_conservan_como_fracciones(self):
        matriz = [[1, 2, 1], [0, 3, 1]]

        reducida, _, _ = aplicar_gauss_jordan(matriz)

        self.assertIsInstance(reducida[0][2], Fraction)
        self.assertEqual(reducida[0][2], Fraction(1, 3))


if __name__ == "__main__":
    unittest.main()
