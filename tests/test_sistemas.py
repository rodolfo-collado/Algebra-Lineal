"""Pruebas de la resolucion de sistemas de ecuaciones."""

import unittest
from fractions import Fraction

from backend.sistemas import (
    INCONSISTENTE,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
    contar_variables,
    resolver_sistema_gauss,
    resolver_sistema_gauss_jordan,
    sustitucion_regresiva,
    validar_matriz_aumentada,
)

# Sistemas usados para comprobar que ambos metodos coinciden.
SISTEMAS = (
    [[1, 1, 3], [1, -1, 1]],
    [[2, 1, 5], [1, -1, 1]],
    [[0, 1, 1], [1, 0, 2]],
    [[1, 2, 3, 6], [2, -3, 2, 14], [3, 1, -1, -2]],
    [[2, 0, 0, 1], [0, 3, 0, 2], [0, 0, 4, -5]],
    [[1, 1, 3], [1, -1, 1], [2, 0, 4]],
    [[1, 2], [2, 4]],
    [[1, 1, 1, 6], [0, 1, 2, 5]],
    [[1, 1, 2], [2, 2, 4]],
    [[1, 1, 1, 3], [2, 2, 2, 6], [3, 3, 3, 9]],
    [[1, 1, 2], [1, 1, 5]],
    [[1, 1, 1, 3], [2, 2, 2, 7]],
    [[1, 1, 2], [1, -1, 0], [1, 1, 5]],
)


class PruebasSolucionUnica(unittest.TestCase):
    def test_dos_ecuaciones_y_dos_variables(self):
        resultado = resolver_sistema_gauss_jordan([[1, 1, 3], [1, -1, 1]])

        self.assertEqual(resultado["matriz_reducida"], [[1, 0, 2], [0, 1, 1]])
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [2, 1])

    def test_tres_ecuaciones_y_dos_variables(self):
        # Matriz 3x3 que NO es una matriz cuadrada ordinaria: la tercera
        # ecuación es combinación de las dos primeras.
        resultado = resolver_sistema_gauss_jordan([[1, 1, 3], [1, -1, 1], [2, 0, 4]])

        self.assertEqual(
            resultado["matriz_reducida"], [[1, 0, 2], [0, 1, 1], [0, 0, 0]]
        )
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [2, 1])

    def test_tres_ecuaciones_y_tres_variables(self):
        matriz = [[1, 2, 3, 6], [2, -3, 2, 14], [3, 1, -1, -2]]
        resultado = resolver_sistema_gauss_jordan(matriz)

        self.assertEqual(
            resultado["matriz_reducida"],
            [[1, 0, 0, 1], [0, 1, 0, -2], [0, 0, 1, 3]],
        )
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [1, -2, 3])

    def test_solucion_no_entera_se_conserva_como_fraccion(self):
        resultado = resolver_sistema_gauss_jordan([[2, 0, 1], [0, 1, 1]])

        self.assertEqual(resultado["soluciones"], [Fraction(1, 2), 1])
        self.assertIsInstance(resultado["soluciones"][0], Fraction)

    def test_soluciones_fraccionarias_exactas(self):
        matriz = [[2, 0, 0, 1], [0, 3, 0, 2], [0, 0, 4, -5]]
        resultado = resolver_sistema_gauss_jordan(matriz)

        self.assertEqual(
            resultado["soluciones"],
            [Fraction(1, 2), Fraction(2, 3), Fraction(-5, 4)],
        )

    def test_ecuacion_redundante_deja_solucion_unica(self):
        # 2 ecuaciones y 1 variable: la segunda es el doble de la primera.
        resultado = resolver_sistema_gauss_jordan([[1, 2], [2, 4]])

        self.assertEqual(resultado["matriz_reducida"], [[1, 2], [0, 0]])
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [2])


class PruebasSolucionesInfinitas(unittest.TestCase):
    def test_dos_ecuaciones_y_tres_variables(self):
        resultado = resolver_sistema_gauss_jordan([[1, 1, 1, 6], [0, 1, 2, 5]])

        self.assertEqual(
            resultado["matriz_reducida"], [[1, 0, -1, 1], [0, 1, 2, 5]]
        )
        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertEqual(resultado["soluciones"], [])

    def test_ecuaciones_proporcionales(self):
        resultado = resolver_sistema_gauss_jordan([[1, 1, 2], [2, 2, 4]])

        self.assertEqual(resultado["matriz_reducida"], [[1, 1, 2], [0, 0, 0]])
        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertEqual(resultado["soluciones"], [])

    def test_tres_ecuaciones_redundantes_con_tres_variables(self):
        matriz = [[1, 1, 1, 3], [2, 2, 2, 6], [3, 3, 3, 9]]
        resultado = resolver_sistema_gauss_jordan(matriz)

        self.assertEqual(
            resultado["matriz_reducida"],
            [[1, 1, 1, 3], [0, 0, 0, 0], [0, 0, 0, 0]],
        )
        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)


class PruebasInconsistencia(unittest.TestCase):
    def test_ecuaciones_contradictorias(self):
        resultado = resolver_sistema_gauss_jordan([[1, 1, 2], [1, 1, 5]])

        self.assertEqual(resultado["matriz_reducida"], [[1, 1, 2], [0, 0, 3]])
        self.assertEqual(resultado["clasificacion"], INCONSISTENTE)
        self.assertEqual(resultado["soluciones"], [])

    def test_mas_ecuaciones_que_variables_con_contradiccion(self):
        resultado = resolver_sistema_gauss_jordan([[1, 1, 2], [1, -1, 0], [1, 1, 5]])

        self.assertEqual(
            resultado["matriz_reducida"], [[1, 0, 1], [0, 1, 1], [0, 0, 3]]
        )
        self.assertEqual(resultado["clasificacion"], INCONSISTENTE)

    def test_mas_variables_que_ecuaciones_con_contradiccion(self):
        resultado = resolver_sistema_gauss_jordan([[1, 1, 1, 3], [2, 2, 2, 7]])

        self.assertEqual(
            resultado["matriz_reducida"], [[1, 1, 1, 3], [0, 0, 0, 1]]
        )
        self.assertEqual(resultado["clasificacion"], INCONSISTENTE)

    def test_matriz_cuadrada_se_interpreta_como_aumentada(self):
        # 2 ecuaciones y 1 variable: x = 1/2 y x = 1 se contradicen.
        resultado = resolver_sistema_gauss_jordan([[2, 1], [1, 1]])

        self.assertEqual(
            resultado["matriz_reducida"],
            [[1, Fraction(1, 2)], [0, Fraction(1, 2)]],
        )
        self.assertEqual(resultado["clasificacion"], INCONSISTENTE)


class PruebasValidacionDeSistemas(unittest.TestCase):
    def test_contar_variables_ignora_la_columna_final(self):
        self.assertEqual(contar_variables([[1, 2, 3]]), 2)

    def test_matriz_vacia(self):
        es_valida, mensaje = validar_matriz_aumentada([])

        self.assertFalse(es_valida)
        self.assertEqual(mensaje, "Error: La matriz está vacía.")

    def test_matriz_no_rectangular(self):
        es_valida, mensaje = validar_matriz_aumentada([[1, 2], [3, 4, 5]])

        self.assertFalse(es_valida)
        self.assertEqual(mensaje, "Error: La matriz no es rectangular.")

    def test_una_sola_columna_no_es_matriz_aumentada(self):
        es_valida, mensaje = validar_matriz_aumentada([[1], [2]])

        self.assertFalse(es_valida)
        self.assertIn("al menos una columna de coeficientes", mensaje)

    def test_matriz_vacia_lanza_valueerror(self):
        for resolver in (resolver_sistema_gauss, resolver_sistema_gauss_jordan):
            with self.subTest(metodo=resolver.__name__):
                with self.assertRaises(ValueError):
                    resolver([])

    def test_una_sola_columna_lanza_valueerror(self):
        for resolver in (resolver_sistema_gauss, resolver_sistema_gauss_jordan):
            with self.subTest(metodo=resolver.__name__):
                with self.assertRaises(ValueError):
                    resolver([[1], [2]])


class PruebasGaussSolucionUnica(unittest.TestCase):
    def test_dos_ecuaciones_y_dos_variables(self):
        resultado = resolver_sistema_gauss([[1, 1, 3], [1, -1, 1]])

        self.assertEqual(resultado["matriz_escalonada"], [[1, 1, 3], [0, 1, 1]])
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [2, 1])

    def test_tres_ecuaciones_y_tres_variables(self):
        matriz = [[1, 2, 3, 6], [2, -3, 2, 14], [3, 1, -1, -2]]
        resultado = resolver_sistema_gauss(matriz)

        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [1, -2, 3])

    def test_mas_ecuaciones_que_variables_con_solucion_unica(self):
        resultado = resolver_sistema_gauss([[1, 1, 3], [1, -1, 1], [2, 0, 4]])

        self.assertEqual(
            resultado["matriz_escalonada"], [[1, 1, 3], [0, 1, 1], [0, 0, 0]]
        )
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [2, 1])

    def test_soluciones_fraccionarias_exactas(self):
        matriz = [[2, 0, 0, 1], [0, 3, 0, 2], [0, 0, 4, -5]]
        resultado = resolver_sistema_gauss(matriz)

        self.assertEqual(
            resultado["soluciones"],
            [Fraction(1, 2), Fraction(2, 3), Fraction(-5, 4)],
        )

    def test_pivote_inicial_en_cero(self):
        resultado = resolver_sistema_gauss([[0, 1, 1], [1, 0, 2]])

        self.assertEqual(resultado["pasos"][0]["operacion"], "F1 <-> F2")
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["soluciones"], [2, 1])

    def test_la_matriz_escalonada_no_queda_reducida(self):
        resultado = resolver_sistema_gauss([[1, 1, 3], [1, -1, 1]])

        self.assertNotEqual(resultado["matriz_escalonada"], [[1, 0, 2], [0, 1, 1]])

    def test_los_pasos_de_sustitucion_van_de_la_ultima_variable_a_la_primera(self):
        resultado = resolver_sistema_gauss([[1, 1, 1, 6], [0, 1, 2, 5], [0, 0, 1, 2]])

        variables = [paso["variable"] for paso in resultado["pasos_sustitucion"]]
        valores = [paso["valor"] for paso in resultado["pasos_sustitucion"]]

        self.assertEqual(variables, [3, 2, 1])
        self.assertEqual(valores, [2, 1, 3])
        self.assertEqual(resultado["soluciones"], [3, 1, 2])

    def test_la_expresion_muestra_las_variables_ya_conocidas(self):
        resultado = resolver_sistema_gauss([[1, 1, 3], [1, -1, 1]])
        expresiones = [paso["expresion"] for paso in resultado["pasos_sustitucion"]]

        self.assertEqual(expresiones, ["1", "3 - (1)(1)"])


class PruebasGaussSinSolucionUnica(unittest.TestCase):
    def test_soluciones_infinitas_no_sustituyen(self):
        resultado = resolver_sistema_gauss([[1, 1, 1, 6], [0, 1, 2, 5]])

        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertEqual(resultado["soluciones"], [])
        self.assertEqual(resultado["pasos_sustitucion"], [])

    def test_ecuaciones_proporcionales(self):
        resultado = resolver_sistema_gauss([[1, 1, 2], [2, 2, 4]])

        self.assertEqual(resultado["matriz_escalonada"], [[1, 1, 2], [0, 0, 0]])
        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertEqual(resultado["pasos_sustitucion"], [])

    def test_sistema_inconsistente_no_sustituye(self):
        resultado = resolver_sistema_gauss([[1, 1, 2], [1, 1, 5]])

        self.assertEqual(resultado["matriz_escalonada"], [[1, 1, 2], [0, 0, 3]])
        self.assertEqual(resultado["clasificacion"], INCONSISTENTE)
        self.assertEqual(resultado["soluciones"], [])
        self.assertEqual(resultado["pasos_sustitucion"], [])

    def test_contradiccion_con_mas_variables_que_ecuaciones(self):
        resultado = resolver_sistema_gauss([[1, 1, 1, 3], [2, 2, 2, 7]])

        self.assertEqual(resultado["clasificacion"], INCONSISTENTE)
        self.assertEqual(resultado["pasos_sustitucion"], [])


class PruebasSustitucionRegresiva(unittest.TestCase):
    def test_sistema_de_dos_variables(self):
        soluciones, _ = sustitucion_regresiva([[1, 2, 5], [0, 1, 1]], [(0, 0), (1, 1)])

        self.assertEqual(soluciones, [3, 1])

    def test_sistema_de_tres_variables(self):
        matriz = [[1, 1, 1, 6], [0, 1, 2, 5], [0, 0, 1, 2]]
        soluciones, _ = sustitucion_regresiva(matriz, [(0, 0), (1, 1), (2, 2)])

        self.assertEqual(soluciones, [3, 1, 2])

    def test_valores_negativos(self):
        soluciones, _ = sustitucion_regresiva([[1, 2, -1], [0, 1, -3]], [(0, 0), (1, 1)])

        self.assertEqual(soluciones, [5, -3])

    def test_soluciones_fraccionarias(self):
        matriz = [[1, Fraction(1, 2), Fraction(5, 2)], [0, 1, 1]]
        soluciones, _ = sustitucion_regresiva(matriz, [(0, 0), (1, 1)])

        self.assertEqual(soluciones, [2, 1])

    def test_pivote_distinto_de_uno_se_divide(self):
        soluciones, pasos = sustitucion_regresiva([[2, 0, 1], [0, 1, 3]], [(0, 0), (1, 1)])

        self.assertEqual(soluciones, [Fraction(1, 2), 3])
        self.assertEqual(pasos[-1]["expresion"], "(1) / 2")

    def test_los_resultados_no_son_floats(self):
        matriz = [[3, 0, 1], [0, 3, 1]]
        soluciones, _ = sustitucion_regresiva(matriz, [(0, 0), (1, 1)])

        for solucion in soluciones:
            self.assertNotIsInstance(solucion, float)
            self.assertIsInstance(solucion, Fraction)

    def test_no_se_ejecuta_con_variables_libres(self):
        with self.assertRaises(ValueError):
            sustitucion_regresiva([[1, 1, 1, 6], [0, 1, 2, 5]], [(0, 0), (1, 1)])

    def test_no_se_ejecuta_con_un_sistema_inconsistente(self):
        with self.assertRaises(ValueError):
            sustitucion_regresiva([[1, 1, 2], [0, 0, 3]], [(0, 0)])

    def test_matriz_invalida_lanza_valueerror(self):
        with self.assertRaises(ValueError):
            sustitucion_regresiva([], [])

    def test_no_modifica_la_matriz_recibida(self):
        matriz = [[1, 2, 5], [0, 1, 1]]

        sustitucion_regresiva(matriz, [(0, 0), (1, 1)])

        self.assertEqual(matriz, [[1, 2, 5], [0, 1, 1]])


class PruebasEquivalenciaDeMetodos(unittest.TestCase):
    """Cambia el procedimiento mostrado, no el resultado matematico."""

    def test_ambos_metodos_clasifican_igual(self):
        for matriz in SISTEMAS:
            with self.subTest(matriz=matriz):
                por_gauss = resolver_sistema_gauss(matriz)
                por_gauss_jordan = resolver_sistema_gauss_jordan(matriz)

                self.assertEqual(
                    por_gauss["clasificacion"], por_gauss_jordan["clasificacion"]
                )

    def test_ambos_metodos_dan_las_mismas_soluciones(self):
        for matriz in SISTEMAS:
            with self.subTest(matriz=matriz):
                por_gauss = resolver_sistema_gauss(matriz)
                por_gauss_jordan = resolver_sistema_gauss_jordan(matriz)

                self.assertEqual(
                    por_gauss["soluciones"], por_gauss_jordan["soluciones"]
                )

    def test_las_tres_clasificaciones_aparecen_en_los_sistemas_de_prueba(self):
        clasificaciones = {
            resolver_sistema_gauss(matriz)["clasificacion"] for matriz in SISTEMAS
        }

        self.assertEqual(
            clasificaciones,
            {SOLUCION_UNICA, SOLUCIONES_INFINITAS, INCONSISTENTE},
        )

    def test_solo_hay_soluciones_cuando_son_unicas(self):
        for matriz in SISTEMAS:
            with self.subTest(matriz=matriz):
                resultado = resolver_sistema_gauss(matriz)
                hay_soluciones = bool(resultado["soluciones"])

                self.assertEqual(
                    hay_soluciones, resultado["clasificacion"] == SOLUCION_UNICA
                )

    def test_las_soluciones_satisfacen_el_sistema_original(self):
        for matriz in SISTEMAS:
            resultado = resolver_sistema_gauss(matriz)
            if resultado["clasificacion"] != SOLUCION_UNICA:
                continue

            with self.subTest(matriz=matriz):
                cantidad_variables = contar_variables(matriz)
                for fila in matriz:
                    total = sum(
                        fila[columna] * resultado["soluciones"][columna]
                        for columna in range(cantidad_variables)
                    )
                    self.assertEqual(total, fila[cantidad_variables])


if __name__ == "__main__":
    unittest.main()
