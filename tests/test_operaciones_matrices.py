"""Aritmética exacta y dominio de P13A, sin dependencias de Django."""

import unittest
from copy import deepcopy
from fractions import Fraction as F

from backend.matrices import (
    dimensiones, multiplicar_escalar_matriz, resolver_operacion_matrices,
    restar_matrices, sumar_matrices, trasponer_matriz, validar_matriz,
)


class PruebasSumaMatrices(unittest.TestCase):
    def test_uno_por_uno(self):
        self.assertEqual(sumar_matrices([[2]], [[3]]), [[5]])

    def test_dos_por_dos(self):
        self.assertEqual(sumar_matrices([[1, 2], [3, 4]], [[5, 6], [7, 8]]), [[6, 8], [10, 12]])

    def test_rectangular(self):
        self.assertEqual(sumar_matrices([[1, 2, 3], [4, 5, 6]], [[6, 5, 4], [3, 2, 1]]), [[7, 7, 7], [7, 7, 7]])

    def test_fracciones(self):
        self.assertEqual(sumar_matrices([[F(1, 2), F(-7, 3)]], [[F(1, 3), F(1, 6)]]), [[F(5, 6), F(-13, 6)]])

    def test_negativos(self):
        self.assertEqual(sumar_matrices([[-2, 3]], [[1, -5]]), [[-1, -2]])

    def test_ceros(self):
        self.assertEqual(sumar_matrices([[0], [0]], [[2], [-3]]), [[2], [-3]])

    def test_dimensiones_incompatibles(self):
        for a, b in (([[1, 2]], [[1], [2]]), ([[1]], [[1, 2]]), ([[1]], [[1], [2]])):
            with self.subTest(a=a, b=b), self.assertRaisesRegex(ValueError, "mismas dimensiones"):
                sumar_matrices(a, b)


class PruebasRestaMatrices(unittest.TestCase):
    def test_uno_por_uno(self):
        self.assertEqual(restar_matrices([[2]], [[3]]), [[-1]])

    def test_dos_por_dos(self):
        self.assertEqual(restar_matrices([[5, 6], [7, 8]], [[1, 2], [3, 4]]), [[4, 4], [4, 4]])

    def test_rectangular(self):
        self.assertEqual(restar_matrices([[1, 2], [3, 4], [5, 6]], [[6, 5], [4, 3], [2, 1]]), [[-5, -3], [-1, 1], [3, 5]])

    def test_fracciones(self):
        self.assertEqual(restar_matrices([[F(1, 2), F(-7, 3)]], [[F(1, 3), F(1, 6)]]), [[F(1, 6), F(-5, 2)]])

    def test_negativos(self):
        self.assertEqual(restar_matrices([[-2, 3]], [[-1, -5]]), [[-1, 8]])

    def test_ceros(self):
        self.assertEqual(restar_matrices([[0], [0]], [[2], [-3]]), [[-2], [3]])

    def test_dimensiones_incompatibles(self):
        for a, b in (([[1, 2]], [[1], [2]]), ([[1]], [[1, 2]]), ([[1]], [[1], [2]])):
            with self.subTest(a=a, b=b), self.assertRaisesRegex(ValueError, "mismas dimensiones"):
                restar_matrices(a, b)


class PruebasEscalarMatriz(unittest.TestCase):
    def test_positivo(self):
        self.assertEqual(multiplicar_escalar_matriz(2, [[1, 3], [4, -2]]), [[2, 6], [8, -4]])

    def test_negativo(self):
        self.assertEqual(multiplicar_escalar_matriz(-3, [[2], [-4]]), [[-6], [12]])

    def test_cero(self):
        self.assertEqual(multiplicar_escalar_matriz(0, [[1, F(1, 3), -5]]), [[0, 0, 0]])

    def test_fraccion(self):
        self.assertEqual(multiplicar_escalar_matriz(F(1, 2), [[2, 4], [6, 8]]), [[1, 2], [3, 4]])

    def test_rectangular_con_fracciones(self):
        self.assertEqual(multiplicar_escalar_matriz(F(-2, 3), [[1, F(1, 2), -3], [0, 3, 6]]), [[F(-2, 3), F(-1, 3), 2], [0, -2, -4]])

    def test_escalar_invalido(self):
        for k in (True, False, 0.5, "1/2", None, [], complex(1, 1)):
            with self.subTest(k=k), self.assertRaisesRegex(ValueError, "escalar"):
                multiplicar_escalar_matriz(k, [[1]])


class PruebasTraspuesta(unittest.TestCase):
    def test_cuadrada(self):
        self.assertEqual(trasponer_matriz([[1, 2], [3, 4]]), [[1, 3], [2, 4]])

    def test_dos_por_tres(self):
        self.assertEqual(trasponer_matriz([[1, 2, 3], [4, 5, 6]]), [[1, 4], [2, 5], [3, 6]])

    def test_tres_por_dos(self):
        self.assertEqual(trasponer_matriz([[1, 4], [2, 5], [3, 6]]), [[1, 2, 3], [4, 5, 6]])

    def test_vector_fila(self):
        self.assertEqual(trasponer_matriz([[1, 2, 3, 4]]), [[1], [2], [3], [4]])

    def test_vector_columna(self):
        self.assertEqual(trasponer_matriz([[1], [2], [3], [4]]), [[1, 2, 3, 4]])

    def test_uno_por_uno(self):
        self.assertEqual(trasponer_matriz([[F(-7, 3)]]), [[F(-7, 3)]])

    def test_doble_traspuesta(self):
        a = [[1, F(1, 3), 0], [-5, F(-3, 7), 10]]
        self.assertEqual(trasponer_matriz(trasponer_matriz(a)), a)


class PruebasDominioYPasos(unittest.TestCase):
    def test_estructuras_invalidas_sin_errores_internos(self):
        for matriz in (None, 2, "matriz", {}, [], [[]], [1], [[1], 2], [[1], [2, 3]], [[True]], [[1.5]], [["2"]], [[None]]):
            with self.subTest(matriz=matriz):
                self.assertFalse(validar_matriz(matriz)[0])
                for operacion in ("suma", "resta", "escalar", "traspuesta"):
                    with self.assertRaises(ValueError):
                        resolver_operacion_matrices(operacion, matriz, [[1]], 2)

    def test_ambos_operandos_se_validan(self):
        for operacion in (sumar_matrices, restar_matrices):
            for b in ([], [[1], []], [["3"]], [[False]], None):
                with self.subTest(operacion=operacion, b=b), self.assertRaises(ValueError):
                    operacion([[1]], b)

    def test_no_modifica_ni_comparte_entradas(self):
        a, b = [[1, F(-1, 2)], [3, 4]], [[5, 6], [7, 8]]
        copia_a, copia_b = deepcopy(a), deepcopy(b)
        for operacion in ("suma", "resta", "escalar", "traspuesta"):
            resultado = resolver_operacion_matrices(operacion, a, b, F(1, 3))
            resultado["resultado"][0][0] = 100
            self.assertEqual(a, copia_a)
            self.assertEqual(b, copia_b)

    def test_siempre_devuelve_fracciones(self):
        for operacion in ("suma", "resta", "escalar", "traspuesta"):
            resultado = resolver_operacion_matrices(operacion, [[2, F(1, 2)]], [[3, 2]], F(1, 3))
            self.assertTrue(all(isinstance(x, F) for fila in resultado["resultado"] for x in fila))

    def test_no_exige_matriz_cuadrada(self):
        a = [[1, 2, 3], [4, 5, 6]]
        self.assertNotEqual(*dimensiones(a))
        self.assertEqual(dimensiones(sumar_matrices(a, a)), (2, 3))
        self.assertEqual(dimensiones(restar_matrices(a, a)), (2, 3))
        self.assertEqual(dimensiones(multiplicar_escalar_matriz(2, a)), (2, 3))
        self.assertEqual(dimensiones(trasponer_matriz(a)), (3, 2))

    def test_no_hay_limites_de_interfaz_en_backend(self):
        for m, n in ((1, 14), (13, 1), (12, 15)):
            a = [[1] * n for _ in range(m)]
            for operacion in (sumar_matrices, restar_matrices):
                self.assertEqual(dimensiones(operacion(a, a)), (m, n))
            self.assertEqual(dimensiones(multiplicar_escalar_matriz(2, a)), (m, n))
            self.assertEqual(dimensiones(trasponer_matriz(a)), (n, m))

    def test_pasos_aritmeticos_son_datos_exactos(self):
        for op, operandos, esperado in (("suma", (F(1, 2), F(-1, 3)), F(1, 6)), ("resta", (F(1, 2), F(-1, 3)), F(5, 6)), ("escalar", (F(2), F(1, 2)), F(1))):
            r = resolver_operacion_matrices(op, [[F(1, 2)]], [[F(-1, 3)]], 2)
            self.assertEqual(r["pasos"], [[{"posicion": (1, 1), "origen": (1, 1), "operandos": operandos, "resultado": esperado}]])

    def test_pasos_traspuesta_identifican_origen_y_destino(self):
        r = resolver_operacion_matrices("traspuesta", [[1, 2, 3], [4, 5, 6]])
        self.assertEqual(r["dimensiones_entrada"], (2, 3))
        self.assertEqual(r["dimensiones_resultado"], (3, 2))
        self.assertEqual(r["pasos"][2][1], {"posicion": (3, 2), "origen": (2, 3), "operandos": (F(6),), "resultado": F(6)})

    def test_operaciones_desconocidas_se_rechazan(self):
        # producto y matriz_vector pasaron a ser válidas en P13B; las ecuaciones matriciales siguen fuera.
        for operacion in ("ecuacion", "inversa", "", None):
            with self.subTest(operacion=operacion), self.assertRaisesRegex(ValueError, "operación"):
                resolver_operacion_matrices(operacion, [[1]], [[1]])
