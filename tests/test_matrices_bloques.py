"""P26.3: composición y separación de bloques exactos, sin dependencias web."""

from fractions import Fraction
import unittest

from backend.matrices import aumentar_matrices, matriz_identidad, separar_bloques
from backend.seguridad_numerica import BITS_MAXIMOS, MENSAJE_CALCULO_GRANDE


class PruebasIdentidad(unittest.TestCase):
    def test_identidades_de_orden_uno_dos_y_tres(self):
        for orden, esperada in (
            (1, [[1]]),
            (2, [[1, 0], [0, 1]]),
            (3, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
        ):
            with self.subTest(orden=orden):
                identidad = matriz_identidad(orden)
                self.assertEqual(identidad, esperada)
                self.assertTrue(all(isinstance(valor, Fraction) for fila in identidad for valor in fila))

    def test_filas_y_llamadas_independientes(self):
        identidad = matriz_identidad(2)
        identidad[0][0] = Fraction(7)
        self.assertEqual(identidad[1], [0, 1])
        self.assertEqual(matriz_identidad(2), [[1, 0], [0, 1]])

    def test_orden_debe_ser_entero_positivo_sin_booleanos(self):
        for orden in (0, -1, True, False, 2.0, Fraction(2), "2", None):
            with self.subTest(orden=orden), self.assertRaises(ValueError):
                matriz_identidad(orden)


class PruebasAumentar(unittest.TestCase):
    def test_aumentar_con_identidad(self):
        self.assertEqual(
            aumentar_matrices([[3, 4], [5, 6]], matriz_identidad(2)),
            [[3, 4, 1, 0], [5, 6, 0, 1]],
        )

    def test_aumentar_con_una_columna(self):
        self.assertEqual(
            aumentar_matrices([[1, 2], [3, 4]], [[5], [6]]),
            [[1, 2, 5], [3, 4, 6]],
        )

    def test_aumentar_bloques_rectangulares_con_varias_columnas(self):
        izquierda = [[1, 2, 3], [4, 5, 6]]
        derecha = [[7, 8, 9, 10], [11, 12, 13, 14]]
        self.assertEqual(
            aumentar_matrices(izquierda, derecha),
            [[1, 2, 3, 7, 8, 9, 10], [4, 5, 6, 11, 12, 13, 14]],
        )

    def test_acepta_tuplas_y_conserva_fracciones_exactas(self):
        izquierda = ((Fraction(1, 3), 2), (3, Fraction(-5, 7)))
        derecha = ((Fraction(2, 9),), (4,))
        aumentada = aumentar_matrices(izquierda, derecha)
        self.assertEqual(aumentada, [[Fraction(1, 3), 2, Fraction(2, 9)], [3, Fraction(-5, 7), 4]])
        self.assertTrue(all(isinstance(valor, Fraction) for fila in aumentada for valor in fila))

    def test_no_comparte_filas_ni_muta_los_bloques(self):
        izquierda, derecha = [[1, 2], [3, 4]], [[5], [6]]
        aumentada = aumentar_matrices(izquierda, derecha)
        aumentada[0][0], aumentada[1][2] = Fraction(9), Fraction(8)
        self.assertEqual(izquierda, [[1, 2], [3, 4]])
        self.assertEqual(derecha, [[5], [6]])
        izquierda[1][0], derecha[0][0] = 11, 12
        self.assertEqual(aumentada, [[9, 2, 5], [3, 4, 8]])

    def test_rechaza_distinta_cantidad_de_filas(self):
        for izquierda, derecha in (([[1], [2]], [[3]]), ([[1]], [[2], [3]])):
            with self.subTest(izquierda=izquierda), self.assertRaises(ValueError):
                aumentar_matrices(izquierda, derecha)

    def test_ambos_bloques_deben_ser_matrices_exactas_no_vacias(self):
        invalidas = ([], [[]], [[1], [2, 3]], [[True]], [[1.5]], [["1/2"]], None)
        for invalida in invalidas:
            for izquierda, derecha in ((invalida, [[1]]), ([[1]], invalida)):
                with self.subTest(izquierda=izquierda, derecha=derecha), self.assertRaises(ValueError):
                    aumentar_matrices(izquierda, derecha)


class PruebasSeparar(unittest.TestCase):
    def test_separa_exactamente_en_el_corte_indicado(self):
        matriz = [[1, 2, Fraction(1, 3), 4, 5], [6, 7, 8, 9, Fraction(-2, 3)]]
        izquierda, derecha = separar_bloques(matriz, 2)
        self.assertEqual(izquierda, [[1, 2], [6, 7]])
        self.assertEqual(derecha, [[Fraction(1, 3), 4, 5], [8, 9, Fraction(-2, 3)]])
        self.assertEqual(aumentar_matrices(izquierda, derecha), matriz)
        self.assertTrue(all(isinstance(valor, Fraction) for fila in izquierda + derecha for valor in fila))

    def test_separa_aumento_de_una_columna_y_bloque_izquierdo_de_una_columna(self):
        matriz = [[1, 2, 3], [4, 5, 6]]
        self.assertEqual(separar_bloques(matriz, 2), ([[1, 2], [4, 5]], [[3], [6]]))
        self.assertEqual(separar_bloques(matriz, 1), ([[1], [4]], [[2, 3], [5, 6]]))

    def test_separar_acepta_tuplas_y_devuelve_copias_independientes(self):
        entrada = ((1, 2, 3), (4, 5, 6))
        izquierda, derecha = separar_bloques(entrada, 1)
        izquierda[0][0], derecha[1][0] = Fraction(9), Fraction(8)
        self.assertEqual(entrada, ((1, 2, 3), (4, 5, 6)))
        self.assertEqual(izquierda[1], [4])
        self.assertEqual(derecha[0], [2, 3])

    def test_modificar_la_entrada_no_afecta_los_bloques_separados(self):
        entrada = [[1, 2, 3], [4, 5, 6]]
        izquierda, derecha = separar_bloques(entrada, 1)
        entrada[0][0], entrada[1][2] = 7, 8
        self.assertEqual((izquierda, derecha), ([[1], [4]], [[2, 3], [5, 6]]))

    def test_corte_debe_ser_entero_y_dejar_dos_bloques_no_vacios(self):
        for corte in (0, -1, 4, 5, True, False, 1.0, Fraction(1), "1", None):
            with self.subTest(corte=corte), self.assertRaises(ValueError):
                separar_bloques([[1, 2, 3, 4]], corte)

    def test_rechaza_matrices_invalidas(self):
        for matriz in ([], [[]], [[1], [2, 3]], [[True, 1]], [[1.5, 1]], [["1/2", 1]], None):
            with self.subTest(matriz=matriz), self.assertRaises(ValueError):
                separar_bloques(matriz, 1)


class PruebasSeguridadBloques(unittest.TestCase):
    def test_ambos_bloques_rechazan_numeradores_y_denominadores_excesivos(self):
        for valor in (1 << BITS_MAXIMOS, Fraction(1, 1 << BITS_MAXIMOS)):
            for izquierda, derecha in (([[valor]], [[1]]), ([[1]], [[valor]])):
                with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                    aumentar_matrices(izquierda, derecha)

    def test_separar_valida_valores_en_ambos_lados_del_corte(self):
        for valor in (1 << BITS_MAXIMOS, Fraction(1, 1 << BITS_MAXIMOS)):
            for matriz in ([[valor, 1]], [[1, valor]]):
                with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                    separar_bloques(matriz, 1)


if __name__ == "__main__":
    unittest.main()
