"""Pruebas del analisis de sistemas de ecuaciones."""

import unittest
from fractions import Fraction

from backend.sistemas import resolver_gauss_jordan


class PruebasSistemas(unittest.TestCase):
    def test_sistema_con_solucion_unica(self):
        matriz_reducida, _, analisis = resolver_gauss_jordan([[1, 1, 3], [1, -1, 1]])

        self.assertEqual(matriz_reducida, [[1, 0, 2], [0, 1, 1]])
        self.assertEqual(
            analisis,
            ["Sistema compatible determinado.", "Solución única:", "x1 = 2", "x2 = 1"],
        )

    def test_sistema_de_tres_ecuaciones_con_solucion_unica(self):
        matriz = [[1, 2, 3, 6], [2, -3, 2, 14], [3, 1, -1, -2]]
        matriz_reducida, _, analisis = resolver_gauss_jordan(matriz)

        self.assertEqual(matriz_reducida, [[1, 0, 0, 1], [0, 1, 0, -2], [0, 0, 1, 3]])
        self.assertEqual(
            analisis,
            [
                "Sistema compatible determinado.",
                "Solución única:",
                "x1 = 1",
                "x2 = -2",
                "x3 = 3",
            ],
        )

    def test_solucion_no_entera_se_reporta_como_fraccion(self):
        matriz_reducida, _, analisis = resolver_gauss_jordan([[2, 0, 1], [0, 1, 1]])

        self.assertEqual(matriz_reducida, [[1, 0, Fraction(1, 2)], [0, 1, 1]])
        self.assertEqual(analisis[2], "x1 = 1/2")

    def test_sistema_con_infinitas_soluciones(self):
        matriz_reducida, _, analisis = resolver_gauss_jordan([[1, 1, 2], [2, 2, 4]])

        self.assertEqual(matriz_reducida, [[1, 1, 2], [0, 0, 0]])
        self.assertEqual(
            analisis,
            [
                "Sistema compatible indeterminado.",
                "Tiene infinitas soluciones porque no hay pivote para cada variable.",
            ],
        )

    def test_sistema_inconsistente(self):
        matriz_reducida, _, analisis = resolver_gauss_jordan([[1, 1, 2], [1, 1, 5]])

        self.assertEqual(matriz_reducida, [[1, 1, 2], [0, 0, 3]])
        self.assertEqual(
            analisis,
            [
                "Sistema incompatible.",
                "Apareció una fila del tipo 0 = k, con k distinto de 0.",
                "No tiene solución.",
            ],
        )

    def test_matriz_cuadrada_invertible(self):
        matriz_reducida, _, analisis = resolver_gauss_jordan([[2, 1], [1, 1]])

        self.assertEqual(matriz_reducida, [[1, 0], [0, 1]])
        self.assertEqual(
            analisis, ["La matriz cuadrada es invertible y se redujo a la identidad."]
        )

    def test_matriz_cuadrada_singular(self):
        matriz_reducida, _, analisis = resolver_gauss_jordan([[1, 2], [2, 4]])

        self.assertEqual(matriz_reducida, [[1, 2], [0, 0]])
        self.assertEqual(
            analisis,
            [
                "La matriz cuadrada es singular.",
                "No se consiguieron pivotes en todas las columnas.",
                "Si se interpreta como sistema homogéneo, tiene infinitas soluciones.",
            ],
        )


if __name__ == "__main__":
    unittest.main()
