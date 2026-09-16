"""Productos AB y Ax de P13B: producto punto, aritmética exacta y equivalencia de métodos."""

import random
import unittest
from copy import deepcopy
from fractions import Fraction as F

from backend.matrices import (
    dimensiones, multiplicar_matrices, multiplicar_matriz_vector, producto_punto,
    resolver_operacion_matrices, trasponer_matriz, validar_vector, vector_columna,
)
from backend.vectores import combinar

IDENTIDAD_3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
IDENTIDAD_2 = [[1, 0], [0, 1]]


def matriz_de_prueba(generador, filas, columnas):
    """Enteros, negativos y fracciones mezclados, reproducibles por semilla."""
    return [
        [F(generador.randint(-6, 6), generador.choice((1, 1, 2, 3))) for _ in range(columnas)]
        for _ in range(filas)
    ]


def columna(matriz, j):
    return [fila[j] for fila in matriz]


class PruebasProductoPunto(unittest.TestCase):
    def test_suma_de_productos(self):
        self.assertEqual(producto_punto([1, 2, 3], [4, 5, 6]), 32)

    def test_una_componente(self):
        self.assertEqual(producto_punto([7], [-3]), -21)

    def test_fracciones_negativos_y_ceros(self):
        self.assertEqual(producto_punto([F(1, 2), -3, 0], [4, F(1, 3), 99]), F(1))
        self.assertEqual(producto_punto([0, 0], [5, F(7, 2)]), 0)

    def test_devuelve_fraccion_exacta_incluso_con_enteros(self):
        resultado = producto_punto([1, 1], [1, 1])
        self.assertIsInstance(resultado, F)
        self.assertEqual(producto_punto([F(1, 3)], [F(1, 3)]), F(1, 9))

    def test_es_conmutativo(self):
        u, v = [1, F(-2, 5), 3], [F(1, 2), 4, -1]
        self.assertEqual(producto_punto(u, v), producto_punto(v, u))

    def test_dimensiones_distintas(self):
        with self.assertRaisesRegex(ValueError, "u tiene 2 componentes y v tiene 3 componentes"):
            producto_punto([1, 2], [1, 2, 3])
        with self.assertRaisesRegex(ValueError, "u tiene 1 componente y v tiene 2 componentes"):
            producto_punto([1], [1, 2])

    def test_vectores_invalidos_sin_errores_internos(self):
        for u, v in (([], [1]), ([1], []), (None, [1]), ([1], "1"), ([1.5], [1]), ([1], [True]), ([1], [None])):
            with self.subTest(u=u, v=v), self.assertRaises(ValueError):
                producto_punto(u, v)

    def test_validar_vector_sigue_disponible_desde_vectores(self):
        from backend import vectores
        self.assertIs(vectores.validar_vector, validar_vector)
        self.assertEqual(validar_vector([1, F(1, 2)]), (True, ""))
        self.assertEqual(validar_vector([], "x"), (False, "El vector x no tiene componentes."))


class PruebasMultiplicacionMatrices(unittest.TestCase):
    def test_uno_por_uno(self):
        self.assertEqual(multiplicar_matrices([[3]], [[F(1, 3)]]), [[1]])

    def test_dos_por_dos(self):
        self.assertEqual(multiplicar_matrices([[1, 2], [3, 4]], [[5, 6], [7, 8]]), [[19, 22], [43, 50]])

    def test_dos_por_tres_por_tres_por_dos(self):
        a, b = [[1, 2, 3], [4, 5, 6]], [[7, 8], [9, 10], [11, 12]]
        self.assertEqual(multiplicar_matrices(a, b), [[58, 64], [139, 154]])
        self.assertEqual(dimensiones(multiplicar_matrices(a, b)), (2, 2))

    def test_tres_por_dos_por_dos_por_cuatro(self):
        a, b = [[1, 0], [0, 1], [2, 3]], [[1, 2, 3, 4], [5, 6, 7, 8]]
        self.assertEqual(multiplicar_matrices(a, b), [[1, 2, 3, 4], [5, 6, 7, 8], [17, 22, 27, 32]])
        self.assertEqual(dimensiones(multiplicar_matrices(a, b)), (3, 4))

    def test_fila_por_columna_da_uno_por_uno(self):
        self.assertEqual(multiplicar_matrices([[1, 2, 3]], [[4], [5], [6]]), [[32]])

    def test_columna_por_fila_da_n_por_p(self):
        self.assertEqual(multiplicar_matrices([[1], [2], [3]], [[4, 5]]), [[4, 5], [8, 10], [12, 15]])

    def test_resultado_rectangular_sin_exigir_cuadradas(self):
        a = [[1, 2, 3], [4, 5, 6]]
        b = [[1, 0, 2, 1], [0, 1, 3, -1], [2, 2, 0, F(1, 2)]]
        producto = multiplicar_matrices(a, b)
        self.assertEqual(dimensiones(producto), (2, 4))
        self.assertEqual(producto, [[7, 8, 8, F(1, 2)], [16, 17, 23, 2]])

    def test_ceros(self):
        self.assertEqual(multiplicar_matrices([[0, 0], [0, 0]], [[1, 2], [3, 4]]), [[0, 0], [0, 0]])
        self.assertEqual(multiplicar_matrices([[1, 2], [3, 4]], [[0], [0]]), [[0], [0]])

    def test_negativos(self):
        self.assertEqual(multiplicar_matrices([[-1, 2], [3, -4]], [[-5, 6], [7, -8]]), [[19, -22], [-43, 50]])

    def test_fracciones_exactas(self):
        a = [[F(1, 2), F(1, 3)], [F(-3, 4), 2]]
        b = [[F(2, 3), 1], [F(1, 2), F(-1, 5)]]
        self.assertEqual(multiplicar_matrices(a, b), [[F(1, 2), F(13, 30)], [F(1, 2), F(-23, 20)]])

    def test_identidad_a_ambos_lados_de_una_rectangular(self):
        a = [[1, F(1, 2), -3], [0, 4, F(2, 7)]]
        self.assertEqual(multiplicar_matrices(IDENTIDAD_2, a), a)
        self.assertEqual(multiplicar_matrices(a, IDENTIDAD_3), a)

    def test_no_es_conmutativo_en_general(self):
        a, b = [[1, 2], [3, 4]], [[0, 1], [1, 0]]
        self.assertNotEqual(multiplicar_matrices(a, b), multiplicar_matrices(b, a))

    def test_dimensiones_incompatibles_con_mensaje_claro(self):
        casos = (
            ([[1, 2, 3]], [[1], [2]], "A tiene 3 columnas y B tiene 2 filas"),
            ([[1, 2], [3, 4]], [[1, 2, 3]], "A tiene 2 columnas y B tiene 1 fila"),
            ([[1], [2]], [[1, 2], [3, 4]], "A tiene 1 columna y B tiene 2 filas"),
        )
        for a, b, detalle in casos:
            with self.subTest(a=a, b=b), self.assertRaisesRegex(ValueError, f"No se puede calcular AB: {detalle}"):
                multiplicar_matrices(a, b)

    def test_ambas_matrices_se_validan(self):
        for a, b in (([], [[1]]), ([[1]], []), (None, [[1]]), ([[1]], [[1], [2, 3]]), ([[1.5]], [[1]]), ([[1]], [["1"]])):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                multiplicar_matrices(a, b)

    def test_no_modifica_las_entradas_y_devuelve_fracciones(self):
        a, b = [[1, 2], [3, 4]], [[F(1, 2), 0], [1, -1]]
        copia_a, copia_b = deepcopy(a), deepcopy(b)
        producto = multiplicar_matrices(a, b)
        producto[0][0] = 100
        self.assertEqual((a, b), (copia_a, copia_b))
        self.assertTrue(all(isinstance(x, F) for fila in multiplicar_matrices(a, b) for x in fila))

    def test_sin_limites_de_interfaz(self):
        a = [[1] * 15 for _ in range(12)]
        b = [[2] * 3 for _ in range(15)]
        producto = multiplicar_matrices(a, b)
        self.assertEqual(dimensiones(producto), (12, 3))
        self.assertTrue(all(x == 30 for fila in producto for x in fila))


class PruebasMatrizVector(unittest.TestCase):
    def test_ejemplo_fila_vector(self):
        self.assertEqual(multiplicar_matriz_vector([[1, 2, -1], [0, -5, 3]], [4, 3, 7]), [3, 6])

    def test_ejemplo_combinacion_de_columnas(self):
        a = [[2, 3, 4], [-1, 5, -3], [6, -2, 8]]
        self.assertEqual(multiplicar_matriz_vector(a, [2, -1, 3]), [13, -16, 38])

    def test_cuadrada_y_rectangular(self):
        self.assertEqual(multiplicar_matriz_vector([[1, 2], [3, 4]], [1, 1]), [3, 7])
        self.assertEqual(multiplicar_matriz_vector([[1, 2, 3], [4, 5, 6]], [1, 0, -1]), [-2, -2])
        self.assertEqual(multiplicar_matriz_vector([[1, 2], [3, 4], [5, 6]], [1, 1]), [3, 7, 11])

    def test_una_fila_y_una_columna(self):
        self.assertEqual(multiplicar_matriz_vector([[1, 2, 3]], [4, 5, 6]), [32])
        self.assertEqual(multiplicar_matriz_vector([[1], [2], [3]], [F(1, 2)]), [F(1, 2), 1, F(3, 2)])

    def test_enteros_negativos_y_fracciones(self):
        a = [[F(1, 2), -1], [3, F(2, 3)]]
        self.assertEqual(multiplicar_matriz_vector(a, [4, F(-3, 2)]), [F(7, 2), 11])

    def test_es_el_mismo_producto_que_a_por_columna(self):
        a, x = [[1, 2, 3], [4, 5, 6]], [F(1, 2), -1, 2]
        self.assertEqual(vector_columna(multiplicar_matriz_vector(a, x)), multiplicar_matrices(a, vector_columna(x)))

    def test_dimension_incompatible(self):
        with self.assertRaisesRegex(ValueError, "No se puede calcular Ax: A tiene 3 columnas y x tiene 2 componentes"):
            multiplicar_matriz_vector([[1, 2, 3]], [1, 2])
        with self.assertRaisesRegex(ValueError, "A tiene 1 columna y x tiene 2 componentes"):
            multiplicar_matriz_vector([[1], [2]], [1, 2])

    def test_vector_y_matriz_invalidos(self):
        for a, x in (([[1, 2]], []), ([[1, 2]], None), ([[1, 2]], [1, "2"]), ([[1, 2]], [1.5, 2]), ([], [1]), ([[1], [2, 3]], [1])):
            with self.subTest(a=a, x=x), self.assertRaises(ValueError):
                multiplicar_matriz_vector(a, x)

    def test_devuelve_lista_de_fracciones_sin_tocar_entradas(self):
        a, x = [[1, 2], [3, 4]], [5, 6]
        resultado = multiplicar_matriz_vector(a, x)
        self.assertTrue(all(isinstance(c, F) for c in resultado))
        self.assertEqual((a, x), ([[1, 2], [3, 4]], [5, 6]))


class PruebasEquivalenciaMetodos(unittest.TestCase):
    """Fila por columna y por columnas son dos lecturas del mismo producto: coinciden siempre."""

    def casos(self):
        generador = random.Random(1305)
        for m, n, p in ((1, 1, 1), (2, 2, 2), (2, 3, 2), (3, 2, 4), (1, 5, 1), (4, 1, 3), (2, 3, 4), (5, 4, 3), (3, 3, 3), (10, 10, 10)):
            yield m, n, p, matriz_de_prueba(generador, m, n), matriz_de_prueba(generador, n, p)

    def test_fila_por_columna_y_por_columnas_dan_la_misma_matriz(self):
        for m, n, p, a, b in self.casos():
            with self.subTest(forma=(m, n, p)):
                calculo = resolver_operacion_matrices("producto", a, b)
                resultado = calculo["resultado"]
                self.assertEqual(dimensiones(resultado), (m, p))
                # Fila por columna: cada entrada es la suma de sus productos.
                por_entrada = [[sum(paso["productos"], F(0)) for paso in fila] for fila in calculo["pasos"]]
                # Por columnas: cada columna del resultado es la suma de las columnas escaladas.
                por_columnas = trasponer_matriz([
                    [sum(escalada[i] for escalada in col["escaladas"]) for i in range(m)] for col in calculo["columnas"]
                ])
                self.assertEqual(por_entrada, resultado)
                self.assertEqual(por_columnas, resultado)
                self.assertEqual([list(col["resultado"]) for col in calculo["columnas"]], trasponer_matriz(resultado))

    def test_cada_columna_es_la_combinacion_lineal_de_las_columnas_de_a(self):
        # El módulo de vectores calcula c1·v1 + … + cn·vn por su cuenta; debe coincidir.
        for m, n, p, a, b in self.casos():
            calculo = resolver_operacion_matrices("producto", a, b)
            for col in calculo["columnas"]:
                with self.subTest(forma=(m, n, p), columna=col["posicion"]):
                    combinacion = combinar(list(col["coeficientes"]), [list(c) for c in calculo["columnas_a"]])
                    self.assertEqual(combinacion, list(col["resultado"]))

    def test_ax_por_fila_vector_y_por_combinacion_coinciden(self):
        generador = random.Random(2026)
        for m, n in ((1, 1), (2, 3), (3, 2), (1, 4), (4, 1), (3, 3), (5, 2), (10, 10)):
            a = matriz_de_prueba(generador, m, n)
            x = [F(generador.randint(-5, 5), generador.choice((1, 2, 4))) for _ in range(n)]
            with self.subTest(forma=(m, n)):
                ax = multiplicar_matriz_vector(a, x)
                self.assertEqual(ax, [producto_punto(fila, x) for fila in a])
                self.assertEqual(ax, combinar(x, trasponer_matriz(a)))
                calculo = resolver_operacion_matrices("matriz_vector", a, vector=x)
                self.assertEqual(calculo["resultado"], vector_columna(ax))
                self.assertEqual(list(calculo["columnas"][0]["resultado"]), ax)

    def test_traspuesta_del_producto(self):
        for m, n, p, a, b in self.casos():
            with self.subTest(forma=(m, n, p)):
                self.assertEqual(
                    trasponer_matriz(multiplicar_matrices(a, b)),
                    multiplicar_matrices(trasponer_matriz(b), trasponer_matriz(a)),
                )


class PruebasPasosProducto(unittest.TestCase):
    def test_pasos_por_entrada_con_fila_columna_y_productos(self):
        calculo = resolver_operacion_matrices("producto", [[1, 2], [3, 4]], [[5, 6], [7, 8]])
        self.assertEqual(calculo["operacion"], "producto")
        self.assertEqual(calculo["dimensiones_entrada"], (2, 2))
        self.assertEqual(calculo["dimensiones_b"], (2, 2))
        self.assertEqual(calculo["dimensiones_resultado"], (2, 2))
        self.assertEqual(calculo["pasos"][1][0], {
            "posicion": (2, 1), "fila": (F(3), F(4)), "columna": (F(5), F(7)),
            "productos": (F(15), F(28)), "resultado": F(43),
        })

    def test_pasos_por_columna_con_coeficientes_y_escaladas(self):
        a = [[2, 3, 4], [-1, 5, -3], [6, -2, 8]]
        calculo = resolver_operacion_matrices("matriz_vector", a, vector=[2, -1, 3])
        self.assertEqual(calculo["dimensiones_b"], (3, 1))
        self.assertEqual(calculo["dimensiones_resultado"], (3, 1))
        self.assertEqual(calculo["columnas_a"], ((F(2), F(-1), F(6)), (F(3), F(5), F(-2)), (F(4), F(-3), F(8))))
        self.assertEqual(calculo["columnas"], [{
            "posicion": 1, "coeficientes": (F(2), F(-1), F(3)),
            "escaladas": ((F(4), F(-2), F(12)), (F(-3), F(-5), F(2)), (F(12), F(-9), F(24))),
            "resultado": (F(13), F(-16), F(38)),
        }])
        self.assertEqual(calculo["pasos"][0][0]["productos"], (F(4), F(-3), F(12)))

    def test_pasos_conservan_fracciones_exactas(self):
        calculo = resolver_operacion_matrices("producto", [[3, -1, 5]], [[2], [4], [F(1, 2)]])
        paso = calculo["pasos"][0][0]
        self.assertEqual(paso["productos"], (F(6), F(-4), F(5, 2)))
        self.assertEqual(paso["resultado"], F(9, 2))
        self.assertEqual(calculo["resultado"], [[F(9, 2)]])

    def test_entradas_invalidas_sin_errores_internos(self):
        for a, b in (([[1]], None), ([], [[1]]), ([[1]], [[]]), ([[1, 2]], [[1]]), (None, None), ([[1]], [[True]])):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                resolver_operacion_matrices("producto", a, b)
        for a, x in (([[1]], None), ([[1]], []), ([[1, 2]], [1]), ([], [1]), ([[1]], [[1]]), ([[1]], ["1"])):
            with self.subTest(a=a, x=x), self.assertRaises(ValueError):
                resolver_operacion_matrices("matriz_vector", a, vector=x)

    def test_no_modifica_ni_comparte_entradas(self):
        a, b, x = [[1, F(1, 2)], [3, 4]], [[5, 6], [7, 8]], [1, -1]
        copias = deepcopy((a, b, x))
        producto = resolver_operacion_matrices("producto", a, b)
        matriz_vector = resolver_operacion_matrices("matriz_vector", a, vector=x)
        producto["resultado"][0][0] = 100
        matriz_vector["resultado"][0][0] = 100
        self.assertEqual((a, b, x), copias)

    def test_matriz_vector_una_columna_una_fila(self):
        calculo = resolver_operacion_matrices("matriz_vector", [[1, 2, 3]], vector=[4, 5, 6])
        self.assertEqual(calculo["resultado"], [[32]])
        self.assertEqual(len(calculo["pasos"]), 1)
        self.assertEqual(len(calculo["columnas"]), 1)
        self.assertEqual(len(calculo["columnas_a"]), 3)


if __name__ == "__main__":
    unittest.main()
