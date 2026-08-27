import unittest
from fractions import Fraction

from Semana_1.backend.sistemas import (
    analizar_sistema,
    obtener_tipo_sistema,
    resolver_gauss,
    resolver_gauss_jordan
)


class PruebasSistemas(unittest.TestCase):
    def test_solucion_unica_por_gauss(self):
        matriz = [[1, 1, 3], [1, -1, 1]]

        resultado = resolver_gauss(matriz)

        self.assertEqual(
            obtener_tipo_sistema(matriz),
            "Consistente de solución única"
        )
        self.assertEqual(resultado[4], [Fraction(2), Fraction(1)])
        self.assertEqual(
            analizar_sistema(matriz),
            ["Consistente de solución única."]
        )

    def test_solucion_unica_por_gauss_jordan(self):
        _, _, analisis = resolver_gauss_jordan(
            [[1, 1, 3], [1, -1, 1]]
        )

        self.assertEqual(analisis, [
            "Consistente de solución única.",
            "x1 = 2",
            "x2 = 1"
        ])

    def test_sistema_con_soluciones_infinitas(self):
        matriz = [[1, 1, 2], [2, 2, 4]]

        self.assertEqual(
            obtener_tipo_sistema(matriz),
            "Consistente de soluciones infinitas"
        )
        self.assertEqual(
            analizar_sistema(matriz),
            [
                "Consistente de soluciones infinitas.",
                "Tiene infinitas soluciones."
            ]
        )

    def test_sistema_inconsistente(self):
        matriz = [[1, 1, 2], [1, 1, 3]]

        self.assertEqual(obtener_tipo_sistema(matriz), "Inconsistente")
        self.assertEqual(
            analizar_sistema(matriz),
            ["Inconsistente.", "No tiene solución."]
        )

    def test_mas_ecuaciones_que_incognitas(self):
        matriz = [[1, 1, 2], [1, -1, 0], [2, 0, 2]]

        resultado = resolver_gauss(matriz)

        self.assertEqual(resultado[4], [Fraction(1), Fraction(1)])
        self.assertEqual(
            obtener_tipo_sistema(matriz),
            "Consistente de solución única"
        )

    def test_menos_ecuaciones_que_incognitas(self):
        matriz = [[1, 1, 1, 3]]

        self.assertEqual(
            obtener_tipo_sistema(matriz),
            "Consistente de soluciones infinitas"
        )

    def test_resolucion_no_depende_de_metadata(self):
        matriz = [[1, 1, 3], [1, -1, 1]]

        por_gauss = resolver_gauss(matriz)[4]
        por_gauss_jordan = resolver_gauss_jordan(matriz)[2]

        self.assertEqual(por_gauss, [Fraction(2), Fraction(1)])
        self.assertIn("x1 = 2", por_gauss_jordan)
        self.assertIn("x2 = 1", por_gauss_jordan)


if __name__ == "__main__":
    unittest.main()
