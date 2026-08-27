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
from entradas import parsear_sistema  # noqa: E402
from opciones_menu import crear_sistema_ecuaciones  # noqa: E402


class PruebasGaussYSistemas(unittest.TestCase):
    def test_sistema_con_solucion_unica(self):
        matriz = [[1, 1, 3], [1, -1, 1]]

        resultado = resolver_gauss(matriz)

        self.assertEqual(
            obtener_tipo_sistema(resultado[0]),
            "Consistente de solución única"
        )
        self.assertEqual(resultado[4], [Fraction(2), Fraction(1)])
        self.assertEqual(
            analizar_sistema(matriz),
            ["Consistente de solución única."]
        )

    def test_gauss_jordan_extrae_la_solucion_unica(self):
        matriz = [[1, 1, 3], [1, -1, 1]]

        _, _, analisis = resolver_gauss_jordan(matriz)

        self.assertIn("x1 = 2", analisis)
        self.assertIn("x2 = 1", analisis)

    def test_entrada_de_sistema_produce_la_misma_matriz(self):
        respuestas = iter([
            "x1 + x2 = 3; x1 - x2 = 1"
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

    def test_rechaza_formatos_de_sistema_invalidos(self):
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

    def test_menu_maneja_entrada_invalida_sin_excepcion(self):
        with patch("builtins.input", return_value="x1 + = 3"):
            matriz = crear_sistema_ecuaciones()

        self.assertEqual(matriz, [])

    def test_sistema_con_infinitas_soluciones(self):
        matriz = [[1, 1, 2], [2, 2, 4]]

        self.assertEqual(
            obtener_tipo_sistema(matriz),
            "Consistente de soluciones infinitas"
        )
        self.assertTrue(
            any(
                "Consistente de soluciones infinitas" in linea
                for linea in analizar_sistema(matriz)
            )
        )
        self.assertEqual(
            analizar_sistema(matriz),
            [
                "Consistente de soluciones infinitas.",
                "Tiene infinitas soluciones."
            ]
        )

    def test_sistema_incompatible(self):
        matriz = [[1, 1, 2], [1, 1, 3]]

        self.assertEqual(obtener_tipo_sistema(matriz), "Inconsistente")
        self.assertTrue(
            any("Inconsistente" in linea for linea in analizar_sistema(matriz))
        )
        self.assertEqual(
            analizar_sistema(matriz),
            ["Inconsistente.", "No tiene solución."]
        )

    def test_mas_ecuaciones_que_incognitas_con_solucion_unica(self):
        matriz = [[1, 1, 2], [1, -1, 0], [2, 0, 2]]

        resultado = resolver_gauss(matriz)

        self.assertEqual(resultado[4], [Fraction(1), Fraction(1)])
        self.assertEqual(
            obtener_tipo_sistema(resultado[0]),
            "Consistente de solución única"
        )

    def test_menos_ecuaciones_que_incognitas(self):
        matriz = [[1, 1, 1, 3]]

        self.assertEqual(
            obtener_tipo_sistema(matriz),
            "Consistente de soluciones infinitas"
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
