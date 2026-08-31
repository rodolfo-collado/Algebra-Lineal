"""Pruebas de las operaciones elementales de fila compartidas por Gauss y Gauss-Jordan."""

import unittest
from fractions import Fraction

from backend.operaciones_filas import (
    buscar_fila_pivote,
    eliminar_en_columna,
    intercambiar_filas,
    normalizar_fila,
    registrar_paso,
    texto_factor,
)


class PruebasBusquedaDePivote(unittest.TestCase):
    def test_devuelve_la_primera_fila_no_nula(self):
        matriz = [[0, 1], [0, 2], [3, 4]]

        self.assertEqual(buscar_fila_pivote(matriz, 0, 0), 2)
        self.assertEqual(buscar_fila_pivote(matriz, 0, 1), 0)

    def test_respeta_la_fila_de_inicio(self):
        matriz = [[1, 1], [2, 2]]

        self.assertEqual(buscar_fila_pivote(matriz, 1, 0), 1)

    def test_columna_de_ceros_no_tiene_pivote(self):
        self.assertIsNone(buscar_fila_pivote([[0, 1], [0, 2]], 0, 0))


class PruebasTextoDelFactor(unittest.TestCase):
    def test_factor_positivo_se_resta(self):
        self.assertEqual(texto_factor(Fraction(3)), "- (3)")

    def test_factor_negativo_se_suma(self):
        self.assertEqual(texto_factor(Fraction(-3)), "+ (3)")

    def test_factor_fraccionario(self):
        self.assertEqual(texto_factor(Fraction(1, 2)), "- (1/2)")


class PruebasRegistroDePasos(unittest.TestCase):
    def test_el_paso_guarda_copias_independientes(self):
        matriz = [[1, 2]]
        pasos = []

        registrar_paso(pasos, matriz, "F1 = F1", matriz)
        matriz[0][0] = 99

        self.assertEqual(pasos[0]["antes"], [[1, 2]])
        self.assertEqual(pasos[0]["despues"], [[1, 2]])
        self.assertEqual(pasos[0]["operacion"], "F1 = F1")


class PruebasIntercambioDeFilas(unittest.TestCase):
    def test_intercambia_y_registra_la_operacion(self):
        matriz = [[0, 1], [1, 0]]
        pasos = []

        intercambiar_filas(matriz, pasos, 0, 1)

        self.assertEqual(matriz, [[1, 0], [0, 1]])
        self.assertEqual(pasos[0]["operacion"], "F1 <-> F2")


class PruebasNormalizacion(unittest.TestCase):
    def test_divide_la_fila_entre_el_pivote(self):
        matriz = [[Fraction(2), Fraction(1)]]
        pasos = []

        normalizar_fila(matriz, pasos, 0, Fraction(2))

        self.assertEqual(matriz, [[1, Fraction(1, 2)]])
        self.assertEqual(pasos[0]["operacion"], "F1 = (1/2)F1")


class PruebasEliminacion(unittest.TestCase):
    def test_hace_cero_las_filas_indicadas(self):
        matriz = [[Fraction(1), Fraction(1)], [Fraction(2), Fraction(2)]]
        pasos = []

        eliminar_en_columna(matriz, pasos, 0, 0, range(1, 2))

        self.assertEqual(matriz, [[1, 1], [0, 0]])
        self.assertEqual(pasos[0]["operacion"], "F2 = F2 - (2)F1")

    def test_una_fila_con_cero_no_genera_paso(self):
        matriz = [[Fraction(1), Fraction(1)], [Fraction(0), Fraction(5)]]
        pasos = []

        eliminar_en_columna(matriz, pasos, 0, 0, range(1, 2))

        self.assertEqual(pasos, [])

    def test_puede_eliminar_hacia_arriba(self):
        matriz = [[Fraction(1), Fraction(2)], [Fraction(0), Fraction(1)]]
        pasos = []

        eliminar_en_columna(matriz, pasos, 1, 1, range(0, -1, -1))

        self.assertEqual(matriz, [[1, 0], [0, 1]])
        self.assertEqual(pasos[0]["operacion"], "F1 = F1 - (2)F2")


if __name__ == "__main__":
    unittest.main()
