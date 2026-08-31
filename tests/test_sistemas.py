"""Pruebas de la resolucion de sistemas de ecuaciones."""

import unittest
from fractions import Fraction

from backend.sistemas import (
    INCONSISTENTE,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
    resolver_sistema,
)


class PruebasSolucionUnica(unittest.TestCase):
    def test_dos_ecuaciones_y_dos_variables(self):
        resultado = resolver_sistema([[1, 1, 3], [1, -1, 1]])

        self.assertEqual(resultado["matriz_reducida"], [[1, 0, 2], [0, 1, 1]])
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [2, 1])

    def test_tres_ecuaciones_y_tres_variables(self):
        matriz = [[1, 2, 3, 6], [2, -3, 2, 14], [3, 1, -1, -2]]
        resultado = resolver_sistema(matriz)

        self.assertEqual(
            resultado["matriz_reducida"],
            [[1, 0, 0, 1], [0, 1, 0, -2], [0, 0, 1, 3]],
        )
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [1, -2, 3])

    def test_solucion_no_entera_se_conserva_como_fraccion(self):
        resultado = resolver_sistema([[2, 0, 1], [0, 1, 1]])

        self.assertEqual(resultado["soluciones"], [Fraction(1, 2), 1])
        self.assertIsInstance(resultado["soluciones"][0], Fraction)

    def test_ecuacion_redundante_deja_solucion_unica(self):
        # 2 ecuaciones y 1 variable: la segunda es el doble de la primera.
        resultado = resolver_sistema([[1, 2], [2, 4]])

        self.assertEqual(resultado["matriz_reducida"], [[1, 2], [0, 0]])
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [2])


class PruebasSolucionesInfinitas(unittest.TestCase):
    def test_ecuaciones_proporcionales(self):
        resultado = resolver_sistema([[1, 1, 2], [2, 2, 4]])

        self.assertEqual(resultado["matriz_reducida"], [[1, 1, 2], [0, 0, 0]])
        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertEqual(resultado["soluciones"], [])


class PruebasInconsistencia(unittest.TestCase):
    def test_ecuaciones_contradictorias(self):
        resultado = resolver_sistema([[1, 1, 2], [1, 1, 5]])

        self.assertEqual(resultado["matriz_reducida"], [[1, 1, 2], [0, 0, 3]])
        self.assertEqual(resultado["clasificacion"], INCONSISTENTE)
        self.assertEqual(resultado["soluciones"], [])

    def test_matriz_cuadrada_se_interpreta_como_aumentada(self):
        # 2 ecuaciones y 1 variable: x = 1/2 y x = 1 se contradicen.
        resultado = resolver_sistema([[2, 1], [1, 1]])

        self.assertEqual(
            resultado["matriz_reducida"],
            [[1, Fraction(1, 2)], [0, Fraction(1, 2)]],
        )
        self.assertEqual(resultado["clasificacion"], INCONSISTENTE)


class PruebasValidacionDeSistemas(unittest.TestCase):
    def test_matriz_vacia_lanza_valueerror(self):
        with self.assertRaises(ValueError):
            resolver_sistema([])

    def test_una_sola_columna_no_es_matriz_aumentada(self):
        with self.assertRaises(ValueError):
            resolver_sistema([[1], [2]])


if __name__ == "__main__":
    unittest.main()
