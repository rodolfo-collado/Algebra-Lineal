import sys
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).parent / "Semana_1"))

from logica_matrices import (  # noqa: E402
    aplicar_gauss,
    aplicar_gauss_jordan,
    analizar_sistema,
    obtener_tipo_sistema,
    resolver_gauss,
    resolver_gauss_jordan,
    validar_dimensiones_gauss_jordan
)
from opciones_menu import crear_sistema_ecuaciones  # noqa: E402


class PruebasGaussYSistemas(unittest.TestCase):
    def test_sistema_con_solucion_unica(self):
        matriz = [[1, 1, 3], [1, -1, 1]]

        resultado = resolver_gauss(matriz)

        self.assertEqual(
            obtener_tipo_sistema(resultado[0]),
            "compatible determinado"
        )
        self.assertEqual(resultado[4], [Fraction(2), Fraction(1)])

    def test_gauss_jordan_extrae_la_solucion_unica(self):
        matriz = [[1, 1, 3], [1, -1, 1]]

        _, _, analisis = resolver_gauss_jordan(matriz)

        self.assertIn("x1 = 2", analisis)
        self.assertIn("x2 = 1", analisis)

    def test_entrada_de_sistema_produce_la_misma_matriz(self):
        respuestas = iter([
            "1", "s", "1", "n", "3", "s", "1", "-1", "1", "n"
        ])

        with patch("builtins.input", side_effect=respuestas):
            matriz = crear_sistema_ecuaciones()

        matriz_manual = [[1, 1, 3], [1, -1, 1]]
        self.assertEqual(matriz, matriz_manual)
        self.assertEqual(
            resolver_gauss(matriz)[4],
            resolver_gauss(matriz_manual)[4]
        )
        _, _, analisis = resolver_gauss_jordan(matriz)
        self.assertIn("x1 = 2", analisis)
        self.assertIn("x2 = 1", analisis)

    def test_sistema_con_infinitas_soluciones(self):
        matriz = [[1, 1, 2], [2, 2, 4]]

        self.assertEqual(
            obtener_tipo_sistema(matriz),
            "compatible indeterminado"
        )
        self.assertTrue(
            any(
                "compatible indeterminado" in linea
                for linea in analizar_sistema(matriz)
            )
        )

    def test_sistema_incompatible(self):
        matriz = [[1, 1, 2], [1, 1, 3]]

        self.assertEqual(obtener_tipo_sistema(matriz), "incompatible")
        self.assertTrue(
            any("Sistema incompatible" in linea for linea in analizar_sistema(matriz))
        )

    def test_mas_ecuaciones_que_incognitas_con_solucion_unica(self):
        matriz = [[1, 1, 2], [1, -1, 0], [2, 0, 2]]

        resultado = resolver_gauss(matriz)

        self.assertEqual(resultado[4], [Fraction(1), Fraction(1)])
        self.assertEqual(
            obtener_tipo_sistema(resultado[0]),
            "compatible determinado"
        )

    def test_menos_ecuaciones_que_incognitas(self):
        matriz = [[1, 1, 1, 3]]

        self.assertEqual(
            obtener_tipo_sistema(matriz),
            "compatible indeterminado"
        )

    def test_matriz_rectangular_general(self):
        matriz = [[1, 2, 3], [4, 5, 6]]

        es_valida, _ = validar_dimensiones_gauss_jordan(matriz)
        escalonada, pasos, pivotes = aplicar_gauss(matriz)
        reducida, pasos_jordan, _ = aplicar_gauss_jordan(matriz)

        self.assertTrue(es_valida)
        self.assertEqual(len(pivotes), 2)
        self.assertEqual(escalonada[1], [Fraction(0), Fraction(1), Fraction(2)])
        self.assertEqual(
            reducida,
            [
                [Fraction(1), Fraction(0), Fraction(-1)],
                [Fraction(0), Fraction(1), Fraction(2)]
            ]
        )
        self.assertGreater(len(pasos_jordan), len(pasos))

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


if __name__ == "__main__":
    unittest.main()
