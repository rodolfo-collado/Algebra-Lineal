"""Ecuaciones matriciales Ax = b (P14): [A | b], reutilización de sistemas y lectura del resultado."""

import random
import unittest
from copy import deepcopy
from fractions import Fraction as F
from unittest.mock import patch

from backend import ecuaciones_matriciales
from backend.ecuaciones_matriciales import (
    METODO_PREDETERMINADO,
    METODOS,
    columnas_de,
    matriz_aumentada_de_ax_b,
    resolver_ecuacion_matricial,
    validar_ecuacion_matricial,
)
from backend.matrices import multiplicar_matriz_vector
from backend.sistemas import (
    INCONSISTENTE,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
    ecuaciones_de_matriz,
    resolver_sistema_gauss,
    resolver_sistema_gauss_jordan,
)
from backend.vectores import combinar, evaluar_combinacion_lineal

# Casos del enunciado: (nombre, A, b, clasificación, x cuando es única, variables libres).
UNICA_CUADRADA = ("única 2×2", [[1, 1], [1, -1]], [5, 1], SOLUCION_UNICA, [3, 2], [])
UNICA_RECTANGULAR = ("única 3×2", [[1, 0], [0, 1], [1, 1]], [2, 3, 5], SOLUCION_UNICA, [2, 3], [])
INFINITAS_RECTANGULAR = ("infinitas 2×3", [[1, 0, 1], [0, 1, 1]], [2, 3], SOLUCIONES_INFINITAS, None, [3])
INCONSISTENTE_RECTANGULAR = ("inconsistente 3×2", [[1, 0], [0, 1], [1, 1]], [2, 3, 6], INCONSISTENTE, None, [])
CASOS = (
    UNICA_CUADRADA, UNICA_RECTANGULAR, INFINITAS_RECTANGULAR, INCONSISTENTE_RECTANGULAR,
    ("1×1", [[4]], [6], SOLUCION_UNICA, [F(3, 2)], []),
    ("1×1 sin solución", [[0]], [1], INCONSISTENTE, None, []),
    ("1×1 con x libre", [[0]], [0], SOLUCIONES_INFINITAS, None, [1]),
    ("1×n", [[1, 2, 3]], [6], SOLUCIONES_INFINITAS, None, [2, 3]),
    ("n×1 consistente", [[1], [2], [3]], [2, 4, 6], SOLUCION_UNICA, [2], []),
    ("n×1 inconsistente", [[1], [2], [3]], [2, 4, 7], INCONSISTENTE, None, []),
    ("ceros con b nulo", [[0, 0], [0, 0]], [0, 0], SOLUCIONES_INFINITAS, None, [1, 2]),
    ("ceros con b no nulo", [[0, 0], [0, 0]], [0, 1], INCONSISTENTE, None, []),
    ("negativos", [[-1, 2], [3, -4]], [1, -1], SOLUCION_UNICA, [1, 1], []),
    ("fracciones", [[2, 0], [0, 3]], [1, 1], SOLUCION_UNICA, [F(1, 2), F(1, 3)], []),
    ("fracciones en A y b", [[F(1, 2), F(1, 3)], [F(-3, 4), 2]], [F(5, 6), F(5, 4)], SOLUCION_UNICA, [1, 1], []),
    ("filas redundantes", [[1, 2], [2, 4], [3, 6]], [3, 6, 9], SOLUCIONES_INFINITAS, None, [2]),
    ("filas redundantes con única", [[1, 1], [2, 2], [1, -1]], [3, 6, 1], SOLUCION_UNICA, [2, 1], []),
    ("varias libres", [[1, 2, 0, 3], [0, 0, 1, 1]], [4, 5], SOLUCIONES_INFINITAS, None, [2, 4]),
    ("todas libres menos una", [[1, 1, 1, 1]], [1], SOLUCIONES_INFINITAS, None, [2, 3, 4]),
)


def matriz_de_prueba(generador, filas, columnas):
    return [
        [F(generador.randint(-5, 5), generador.choice((1, 1, 2, 3))) for _ in range(columnas)]
        for _ in range(filas)
    ]


class PruebasValidacion(unittest.TestCase):
    def test_a_rectangular_y_b_con_una_componente_por_fila(self):
        for a, b in (([[1, 2]], [3]), ([[1], [2]], [3, 4]), ([[1, 2, 3], [4, 5, 6]], [F(1, 2), -1])):
            with self.subTest(a=a, b=b):
                self.assertEqual(validar_ecuacion_matricial(a, b), (True, ""))

    def test_dimension_de_b_debe_ser_la_cantidad_de_filas_de_a(self):
        valida, mensaje = validar_ecuacion_matricial([[1, 2]], [1, 2])
        self.assertFalse(valida)
        self.assertIn("A tiene 1 fila y b tiene 2 componentes", mensaje)
        valida, mensaje = validar_ecuacion_matricial([[1, 2], [3, 4], [5, 6]], [1])
        self.assertFalse(valida)
        self.assertIn("A tiene 3 filas y b tiene 1 componente", mensaje)

    def test_entradas_invalidas_sin_errores_internos(self):
        casos = (([], [1]), ([[1, 2], [3]], [1, 2]), ([[1.5]], [1]), ([[1]], []), ([[1]], [None]), ([[1]], "1"), (None, [1]), ([[True]], [1]))
        for a, b in casos:
            with self.subTest(a=a, b=b):
                valida, mensaje = validar_ecuacion_matricial(a, b)
                self.assertFalse(valida)
                self.assertTrue(mensaje)
                with self.assertRaises(ValueError):
                    matriz_aumentada_de_ax_b(a, b)
                with self.assertRaises(ValueError):
                    resolver_ecuacion_matricial(a, b)

    def test_metodo_desconocido(self):
        for metodo in ("cramer", "inversa", "comparar", "", None, 3):
            with self.subTest(metodo=metodo), self.assertRaisesRegex(ValueError, "método de resolución válido"):
                resolver_ecuacion_matricial([[1]], [1], metodo)
        self.assertEqual(set(METODOS), {"gauss", "gauss_jordan"})
        self.assertEqual(METODO_PREDETERMINADO, "gauss_jordan")


class PruebasMatrizAumentada(unittest.TestCase):
    def test_a_seguida_de_b_fila_por_fila(self):
        a = [[1, 2, 3], [4, 5, 6]]
        self.assertEqual(matriz_aumentada_de_ax_b(a, [7, 8]), [[1, 2, 3, 7], [4, 5, 6, 8]])

    def test_entradas_exactas_sin_modificar_las_originales(self):
        a = [[1, F(1, 2)], [-3, 0]]
        b = [F(2, 3), 4]
        copia_a, copia_b = deepcopy(a), deepcopy(b)
        aumentada = matriz_aumentada_de_ax_b(a, b)
        self.assertEqual(aumentada, [[1, F(1, 2), F(2, 3)], [-3, 0, 4]])
        for fila in aumentada:
            for valor in fila:
                self.assertIsInstance(valor, F)
        self.assertEqual((a, b), (copia_a, copia_b))
        aumentada[0][0] = 99
        self.assertEqual(a[0][0], 1)

    def test_rectangulares_en_ambos_sentidos(self):
        self.assertEqual(matriz_aumentada_de_ax_b([[1, 2, 3]], [4]), [[1, 2, 3, 4]])
        self.assertEqual(matriz_aumentada_de_ax_b([[1], [2], [3]], [4, 5, 6]), [[1, 4], [2, 5], [3, 6]])

    def test_coincide_con_la_matriz_de_la_combinacion_lineal_de_vectores(self):
        # Ax = b y c1·a1 + … + cn·an = b son la misma ecuación: misma matriz aumentada.
        from backend.vectores import matriz_de_combinacion
        a, b = [[1, 0, 1], [0, 1, 1]], [2, 3]
        self.assertEqual(matriz_aumentada_de_ax_b(a, b), matriz_de_combinacion([list(c) for c in columnas_de(a)], b))

    def test_columnas_de_a(self):
        self.assertEqual(columnas_de([[1, 2, 3], [4, 5, 6]]), ((1, 4), (2, 5), (3, 6)))
        self.assertEqual(columnas_de([[F(1, 2)]]), ((F(1, 2),),))


class PruebasResolucion(unittest.TestCase):
    def test_casos_del_enunciado_con_ambos_metodos(self):
        for nombre, a, b, clasificacion, x, libres in CASOS:
            for metodo in METODOS:
                with self.subTest(caso=nombre, metodo=metodo):
                    r = resolver_ecuacion_matricial(a, b, metodo)
                    self.assertEqual(r["clasificacion"], clasificacion)
                    self.assertEqual(r["x"], x)
                    self.assertEqual(r["variables_libres"], libres)
                    self.assertEqual((r["filas"], r["columnas"]), (len(a), len(a[0])))
                    self.assertEqual(r["b_en_generado"], clasificacion != INCONSISTENTE)
                    self.assertEqual(r["metodo"], metodo)

    def test_solucion_unica_cuadrada(self):
        r = resolver_ecuacion_matricial([[1, 1], [1, -1]], [5, 1])
        self.assertEqual(r["x"], [3, 2])
        self.assertEqual(r["solucion_general"], ["x1 = 3", "x2 = 2"])
        self.assertEqual(r["ecuaciones"], ["x1 + x2 = 5", "x1 - x2 = 1"])
        self.assertEqual(r["columnas_pivote"], [1, 2])
        self.assertEqual(r["matriz_reducida"], [[1, 0, 3], [0, 1, 2]])

    def test_solucion_unica_rectangular_tres_por_dos(self):
        r = resolver_ecuacion_matricial([[1, 0], [0, 1], [1, 1]], [2, 3, 5], "gauss")
        self.assertEqual(r["x"], [2, 3])
        self.assertEqual(r["columnas_pivote"], [1, 2])
        # La tercera ecuación es redundante: queda una fila 0 = 0 sin cambiar la clasificación.
        self.assertEqual([fila["fila"] for fila in r["filas_nulas"]], [3])
        self.assertEqual(r["clasificacion"], SOLUCION_UNICA)

    def test_infinitas_rectangular_dos_por_tres(self):
        r = resolver_ecuacion_matricial([[1, 0, 1], [0, 1, 1]], [2, 3])
        self.assertEqual(r["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertEqual(r["variables_libres"], [3])
        self.assertEqual(r["solucion_general"], ["x1 = 2 - x3", "x2 = 3 - x3", "x3 es libre"])
        self.assertEqual(r["ecuaciones"], ["x1 + x3 = 2", "x2 + x3 = 3"])
        self.assertIsNone(r["x"])
        self.assertIsNone(r["verificacion"])
        self.assertTrue(r["b_en_generado"])

    def test_inconsistente_rectangular_con_la_contradiccion_de_sistemas(self):
        r = resolver_ecuacion_matricial([[1, 0], [0, 1], [1, 1]], [2, 3, 6])
        self.assertEqual(r["clasificacion"], INCONSISTENTE)
        self.assertEqual(r["fila_inconsistente"]["representacion"], [0, 0, 1])
        self.assertEqual(r["fila_inconsistente"]["fila"], 3)
        self.assertIn("que equivale a 0 = 1", r["justificacion"][0])
        self.assertEqual(r["solucion_general"], [])
        self.assertIsNone(r["x"])
        self.assertFalse(r["b_en_generado"])

    def test_fracciones_exactas(self):
        r = resolver_ecuacion_matricial([[2, 0], [0, 3]], [1, 1])
        self.assertEqual(r["x"], [F(1, 2), F(1, 3)])
        self.assertEqual(r["solucion_general"], ["x1 = 1/2", "x2 = 1/3"])
        for valor in r["x"] + r["verificacion"]:
            self.assertIsInstance(valor, F)
        self.assertNotIsInstance(r["x"][0], float)

    def test_la_cantidad_de_variables_es_la_de_columnas_de_a(self):
        r = resolver_ecuacion_matricial([[1, 1, 1, 1]], [1])
        self.assertEqual(r["ecuaciones"], ["x1 + x2 + x3 + x4 = 1"])
        self.assertEqual(len(r["solucion_general"]), 4)
        self.assertEqual(r["variables_libres"], [2, 3, 4])
        r = resolver_ecuacion_matricial([[1], [2], [3]], [2, 4, 6])
        self.assertEqual(r["ecuaciones"], ["x1 = 2", "2x1 = 4", "3x1 = 6"])
        self.assertEqual(len(r["solucion_general"]), 1)

    def test_las_entradas_no_se_modifican(self):
        a, b = [[1, F(1, 2)], [3, -4]], [F(2, 3), 5]
        copia_a, copia_b = deepcopy(a), deepcopy(b)
        resolver_ecuacion_matricial(a, b, "gauss")
        resolver_ecuacion_matricial(a, b, "gauss_jordan")
        self.assertEqual((a, b), (copia_a, copia_b))


class PruebasVerificacion(unittest.TestCase):
    def test_a_por_x_reproduce_b_con_solucion_unica(self):
        for nombre, a, b, clasificacion, x, _ in CASOS:
            if clasificacion != SOLUCION_UNICA:
                continue
            for metodo in METODOS:
                with self.subTest(caso=nombre, metodo=metodo):
                    r = resolver_ecuacion_matricial(a, b, metodo)
                    self.assertEqual(r["verificacion"], [F(componente) for componente in b])
                    self.assertEqual(r["verificacion"], multiplicar_matriz_vector(a, r["x"]))
                    # La misma igualdad leída como combinación lineal de las columnas de A.
                    self.assertEqual(combinar(r["x"], [list(c) for c in r["columnas_a"]]), r["verificacion"])

    def test_sin_solucion_unica_no_se_inventa_una_verificacion(self):
        for a, b in (([[1, 0, 1], [0, 1, 1]], [2, 3]), ([[1, 0], [0, 1], [1, 1]], [2, 3, 6])):
            r = resolver_ecuacion_matricial(a, b)
            self.assertIsNone(r["x"])
            self.assertIsNone(r["verificacion"])

    def test_la_verificacion_usa_el_producto_de_p13b(self):
        with patch.object(ecuaciones_matriciales, "multiplicar_matriz_vector", wraps=multiplicar_matriz_vector) as producto:
            resolver_ecuacion_matricial([[1, 1], [1, -1]], [5, 1])
            resolver_ecuacion_matricial([[1, 0, 1], [0, 1, 1]], [2, 3])
        producto.assert_called_once_with([[1, 1], [1, -1]], [3, 2])


class PruebasEquivalenciaConSistemas(unittest.TestCase):
    """P14 no tiene un segundo solucionador: coincide con Resolver un sistema sobre [A | b]."""

    def test_mismo_resultado_que_el_sistema_con_matriz_aumentada(self):
        motores = {"gauss": resolver_sistema_gauss, "gauss_jordan": resolver_sistema_gauss_jordan}
        for nombre, a, b, *_ in CASOS:
            for metodo, motor in motores.items():
                with self.subTest(caso=nombre, metodo=metodo):
                    ecuacion = resolver_ecuacion_matricial(a, b, metodo)
                    sistema = motor(matriz_aumentada_de_ax_b(a, b))
                    for clave in ("clasificacion", "columnas_pivote", "variables_libres", "solucion_general",
                                  "fila_inconsistente", "filas_nulas", "justificacion", "pasos", "soluciones",
                                  "ecuaciones_resultantes", "solucion_directa"):
                        self.assertEqual(ecuacion[clave], sistema[clave], clave)
                    matriz = "matriz_escalonada" if metodo == "gauss" else "matriz_reducida"
                    self.assertEqual(ecuacion[matriz], sistema[matriz])
                    self.assertEqual(ecuacion["ecuaciones"], ecuaciones_de_matriz(matriz_aumentada_de_ax_b(a, b)))

    def test_delega_en_el_motor_de_sistemas_sin_recalcular(self):
        with patch.object(ecuaciones_matriciales, "resolver_sistema_gauss", wraps=resolver_sistema_gauss) as gauss, \
                patch.object(ecuaciones_matriciales, "resolver_sistema_gauss_jordan", wraps=resolver_sistema_gauss_jordan) as jordan, \
                patch.dict(ecuaciones_matriciales.METODOS, {"gauss": gauss, "gauss_jordan": jordan}):
            resolver_ecuacion_matricial([[1, 1], [1, -1]], [5, 1], "gauss")
            gauss.assert_called_once_with([[1, 1, 5], [1, -1, 1]])
            jordan.assert_not_called()
            resolver_ecuacion_matricial([[1, 1], [1, -1]], [5, 1], "gauss_jordan")
            jordan.assert_called_once_with([[1, 1, 5], [1, -1, 1]])
            self.assertEqual(gauss.call_count, 1)

    def test_coincide_con_la_combinacion_lineal_de_vectores(self):
        # b es combinación lineal de las columnas de A exactamente cuando Ax = b es consistente.
        for nombre, a, b, clasificacion, x, libres in CASOS:
            with self.subTest(caso=nombre):
                r = resolver_ecuacion_matricial(a, b)
                combinacion = evaluar_combinacion_lineal([list(c) for c in columnas_de(a)], b)
                self.assertEqual(r["b_en_generado"], combinacion["es_combinacion"])
                self.assertEqual(r["clasificacion"], combinacion["clasificacion"])
                self.assertEqual(r["columnas_pivote"], combinacion["columnas_pivote"])
                self.assertEqual(r["variables_libres"], combinacion["variables_libres"])
                self.assertEqual(r["x"], combinacion["coeficientes"])

    def test_gauss_y_gauss_jordan_coinciden_en_lo_que_deben_coincidir(self):
        generador = random.Random(14)
        casos = [(a, b) for _, a, b, *_ in CASOS]
        for _ in range(60):
            m, n = generador.randint(1, 5), generador.randint(1, 5)
            a = matriz_de_prueba(generador, m, n)
            # Mezcla b arbitrarios con b construidos como Ax, para cubrir los tres tipos.
            if generador.random() < 0.5:
                b = multiplicar_matriz_vector(a, [F(generador.randint(-3, 3)) for _ in range(n)])
            else:
                b = [F(generador.randint(-5, 5)) for _ in range(m)]
            casos.append((a, b))
        for a, b in casos:
            with self.subTest(a=a, b=b):
                gauss = resolver_ecuacion_matricial(a, b, "gauss")
                jordan = resolver_ecuacion_matricial(a, b, "gauss_jordan")
                for clave in ("clasificacion", "columnas_pivote", "variables_libres", "solucion_general",
                              "x", "verificacion", "b_en_generado", "ecuaciones", "matriz_aumentada"):
                    self.assertEqual(gauss[clave], jordan[clave], clave)
                # La contradicción es la misma igualdad 0 = k aunque aparezca en otra fila.
                self.assertEqual(gauss["fila_inconsistente"] is None, jordan["fila_inconsistente"] is None)
                if gauss["fila_inconsistente"]:
                    self.assertNotEqual(gauss["fila_inconsistente"]["termino_independiente"], 0)
                    self.assertNotEqual(jordan["fila_inconsistente"]["termino_independiente"], 0)
                if gauss["x"] is not None:
                    self.assertEqual(gauss["verificacion"], [F(v) for v in b])


if __name__ == "__main__":
    unittest.main()
