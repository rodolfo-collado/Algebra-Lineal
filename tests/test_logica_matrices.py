"""Pruebas de caracterizacion del backend matematico actual."""

import unittest
from fractions import Fraction

from logica_matrices import (
    aplicar_gauss_jordan,
    buscar_fila_pivote,
    convertir_matriz_a_fracciones,
    copiar_matriz,
    es_matriz_rectangular,
    generar_matriz,
    obtener_rango,
    obtener_tipo_gauss_jordan,
    resolver_gauss_jordan,
    texto_factor,
    validar_dimensiones_gauss_jordan,
)


class PruebasCreacionDeMatrices(unittest.TestCase):
    def test_generar_matriz_respeta_las_dimensiones(self):
        matriz = generar_matriz(3, 4)

        self.assertEqual(len(matriz), 3)
        self.assertEqual([len(fila) for fila in matriz], [4, 4, 4])

    def test_generar_matriz_usa_enteros_entre_0_y_20(self):
        matriz = generar_matriz(4, 4)

        for fila in matriz:
            for numero in fila:
                self.assertIsInstance(numero, int)
                self.assertGreaterEqual(numero, 0)
                self.assertLessEqual(numero, 20)

    def test_copiar_matriz_devuelve_el_mismo_contenido(self):
        original = [[1, 2], [3, 4]]

        self.assertEqual(copiar_matriz(original), original)

    def test_copiar_matriz_no_comparte_las_filas(self):
        original = [[1, 2], [3, 4]]
        copia = copiar_matriz(original)

        copia[0][0] = 99

        self.assertEqual(original, [[1, 2], [3, 4]])

    def test_convertir_matriz_a_fracciones(self):
        convertida = convertir_matriz_a_fracciones([[1, 2], [3, 4]])

        for fila in convertida:
            for numero in fila:
                self.assertIsInstance(numero, Fraction)
        self.assertEqual(convertida, [[1, 2], [3, 4]])


class PruebasValidaciones(unittest.TestCase):
    def test_matriz_rectangular(self):
        self.assertTrue(es_matriz_rectangular([[1, 2], [3, 4]]))
        self.assertFalse(es_matriz_rectangular([[1, 2], [3]]))

    def test_tipo_de_matriz_para_gauss_jordan(self):
        self.assertEqual(obtener_tipo_gauss_jordan([[1, 2], [3, 4]]), "cuadrada")
        self.assertEqual(obtener_tipo_gauss_jordan([[1, 2, 3], [4, 5, 6]]), "aumentada")
        self.assertIsNone(obtener_tipo_gauss_jordan([[1, 2, 3, 4], [5, 6, 7, 8]]))

    def test_validar_dimensiones_acepta_cuadrada_y_aumentada(self):
        self.assertEqual(
            validar_dimensiones_gauss_jordan([[1, 2], [3, 4]]), (True, "cuadrada")
        )
        self.assertEqual(
            validar_dimensiones_gauss_jordan([[1, 2, 3], [4, 5, 6]]), (True, "aumentada")
        )

    def test_validar_dimensiones_rechaza_matriz_dentada(self):
        es_valida, mensaje = validar_dimensiones_gauss_jordan([[1, 2], [3]])

        self.assertFalse(es_valida)
        self.assertEqual(mensaje, "Error: La matriz no es rectangular.")

    def test_validar_dimensiones_rechaza_forma_no_soportada(self):
        es_valida, mensaje = validar_dimensiones_gauss_jordan([[1, 2, 3, 4], [5, 6, 7, 8]])

        self.assertFalse(es_valida)
        self.assertEqual(
            mensaje,
            "Error: La matriz es de 2x4. Para Gauss-Jordan use matrices nxn o nx(n+1).",
        )

    def test_buscar_fila_pivote(self):
        matriz = [[0, 1], [0, 2], [3, 4]]

        self.assertEqual(buscar_fila_pivote(matriz, 0, 0), 2)
        self.assertEqual(buscar_fila_pivote(matriz, 0, 1), 0)
        self.assertIsNone(buscar_fila_pivote([[0, 1], [0, 2]], 0, 0))

    def test_obtener_rango_cuenta_filas_no_nulas(self):
        self.assertEqual(obtener_rango([[1, 2, 3], [0, 0, 0]], 2), 1)
        # Limitar las columnas deja fuera la de terminos independientes.
        self.assertEqual(obtener_rango([[1, 2, 3], [0, 0, 5]], 2), 1)

    def test_texto_factor(self):
        self.assertEqual(texto_factor(Fraction(3)), "- (3)")
        self.assertEqual(texto_factor(Fraction(-3)), "+ (3)")
        self.assertEqual(texto_factor(Fraction(1, 2)), "- (1/2)")


class PruebasGaussJordan(unittest.TestCase):
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

    def test_matriz_identidad_no_genera_pasos(self):
        _, pasos, _ = resolver_gauss_jordan([[1, 0], [0, 1]])

        self.assertEqual(pasos, [])

    def test_intercambio_de_filas_cuando_el_pivote_es_cero(self):
        matriz_reducida, pasos, _ = resolver_gauss_jordan([[0, 1, 1], [1, 0, 2]])

        self.assertEqual(pasos[0]["operacion"], "F1 <-> F2")
        self.assertEqual(matriz_reducida, [[1, 0, 2], [0, 1, 1]])

    def test_los_pasos_registran_la_matriz_antes_y_despues(self):
        _, pasos, _ = resolver_gauss_jordan([[1, 1, 2], [2, 2, 4]])

        self.assertEqual(len(pasos), 1)
        self.assertEqual(pasos[0]["antes"], [[1, 1, 2], [2, 2, 4]])
        self.assertEqual(pasos[0]["operacion"], "F2 = F2 - (2)F1")
        self.assertEqual(pasos[0]["despues"], [[1, 1, 2], [0, 0, 0]])

    def test_gauss_jordan_opera_con_fracciones_exactas(self):
        matriz_reducida, _, _ = resolver_gauss_jordan([[3, 0, 1], [0, 3, 1]])

        for fila in matriz_reducida:
            for numero in fila:
                self.assertIsInstance(numero, Fraction)
        self.assertEqual(matriz_reducida[0][2], Fraction(1, 3))

    def test_no_modifica_la_matriz_original(self):
        matriz = [[2, 1], [1, 1]]

        resolver_gauss_jordan(matriz)

        self.assertEqual(matriz, [[2, 1], [1, 1]])

    def test_dimension_no_soportada_lanza_valueerror(self):
        with self.assertRaises(ValueError):
            aplicar_gauss_jordan([[1, 2, 3, 4], [5, 6, 7, 8]])


if __name__ == "__main__":
    unittest.main()
