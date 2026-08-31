"""Pruebas de la resolucion de sistemas de ecuaciones."""

import unittest
from fractions import Fraction

from backend.sistemas import (
    INCONSISTENTE,
    SIN_SOLUCION,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
    contar_variables,
    ecuaciones_de_matriz,
    interpretar_resultado,
    resolver_sistema_gauss,
    resolver_sistema_gauss_jordan,
    solucion_general,
    sustitucion_regresiva,
    validar_matriz_aumentada,
    variables_libres,
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
    # Una variable libre, con x1 dependiendo todavia de otra variable pivote.
    [[1, 1, 1, 5], [0, 1, 1, 2]],
    [[1, 0, -5, 1], [0, 1, 1, 4], [0, 0, 0, 0]],
    # Dos variables libres, una de ellas por ecuaciones redundantes.
    [[1, 6, 0, 3, 0, 0], [0, 0, 1, -4, 0, 5], [0, 0, 0, 0, 1, 7]],
    [[2, 4, 6, 8], [1, 2, 3, 4]],
    # Fracciones con una variable libre.
    [[Fraction(1, 2), Fraction(-3, 4), 0, Fraction(2, 3)], [0, 1, Fraction(1, 3), 2]],
)


def evaluar(expresion, valores):
    """Sustituye valores concretos en una expresion lineal."""
    total = expresion["constante"]
    for variable, coeficiente in expresion["coeficientes"].items():
        total += coeficiente * valores[variable]

    return total


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


class PruebasEcuacionesDeMatriz(unittest.TestCase):
    """Traduccion de una matriz aumentada al sistema que representa."""

    def test_matriz_identidad(self):
        self.assertEqual(
            ecuaciones_de_matriz([[1, 0, 3], [0, 1, 2]]), ["x1 = 3", "x2 = 2"]
        )

    def test_una_variable_ausente_no_aparece(self):
        self.assertEqual(
            ecuaciones_de_matriz([[1, 0, -5, 1], [0, 1, 1, 4]]),
            ["x1 - 5x3 = 1", "x2 + x3 = 4"],
        )

    def test_una_fila_nula_se_muestra_como_cero_igual_a_cero(self):
        self.assertEqual(ecuaciones_de_matriz([[1, 1, 2], [0, 0, 0]])[1], "0 = 0")

    def test_una_contradiccion_se_muestra_como_cero_igual_a_k(self):
        self.assertEqual(ecuaciones_de_matriz([[1, 1, 2], [0, 0, 5]])[1], "0 = 5")

    def test_coeficientes_fraccionarios(self):
        matriz = [[Fraction(1, 2), Fraction(-3, 4), Fraction(2, 3)]]

        self.assertEqual(ecuaciones_de_matriz(matriz), ["1/2x1 - 3/4x2 = 2/3"])

    def test_coeficientes_de_uno_y_menos_uno(self):
        self.assertEqual(ecuaciones_de_matriz([[1, -1, 0]]), ["x1 - x2 = 0"])

    def test_varias_variables(self):
        matriz = [[1, 6, 0, 3, 0, 0], [0, 0, 1, -4, 0, 5], [0, 0, 0, 0, 1, 7]]

        self.assertEqual(
            ecuaciones_de_matriz(matriz),
            ["x1 + 6x2 + 3x4 = 0", "x3 - 4x4 = 5", "x5 = 7"],
        )

    def test_una_matriz_invalida_lanza_valueerror(self):
        with self.assertRaises(ValueError):
            ecuaciones_de_matriz([[1], [2]])


class PruebasVariablesLibres(unittest.TestCase):
    def test_una_columna_sin_pivote_deja_libre_a_su_variable(self):
        self.assertEqual(variables_libres([(0, 0), (1, 1)], 3), [3])

    def test_varias_columnas_sin_pivote(self):
        self.assertEqual(variables_libres([(0, 0), (1, 2), (2, 4)], 5), [2, 4])

    def test_un_pivote_por_variable_no_deja_libres(self):
        self.assertEqual(variables_libres([(0, 0), (1, 1)], 2), [])


class PruebasSolucionGeneral(unittest.TestCase):
    def test_una_variable_libre(self):
        matriz = [[1, 0, -5, 1], [0, 1, 1, 4], [0, 0, 0, 0]]
        resultado = interpretar_resultado(matriz, [(0, 0), (1, 1)], 3)

        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertEqual(
            resultado["solucion_general"],
            ["x1 = 1 + 5x3", "x2 = 4 - x3", "x3 es libre"],
        )

    def test_varias_variables_libres_en_orden_de_variable(self):
        matriz = [[1, 6, 0, 3, 0, 0], [0, 0, 1, -4, 0, 5], [0, 0, 0, 0, 1, 7]]
        resultado = interpretar_resultado(matriz, [(0, 0), (1, 2), (2, 4)], 5)

        self.assertEqual(
            resultado["solucion_general"],
            [
                "x1 = -6x2 - 3x4",
                "x2 es libre",
                "x3 = 5 + 4x4",
                "x4 es libre",
                "x5 = 7",
            ],
        )

    def test_una_variable_pivote_se_despeja_hasta_depender_solo_de_las_libres(self):
        # x1 depende de x2, que a su vez todavia depende de la variable libre.
        matriz = [[1, 1, 1, 5], [0, 1, 1, 2]]
        resultado = interpretar_resultado(matriz, [(0, 0), (1, 1)], 3)

        self.assertEqual(
            resultado["solucion_general"], ["x1 = 3", "x2 = 2 - x3", "x3 es libre"]
        )

    def test_el_despeje_mantiene_fracciones_exactas(self):
        resultado = interpretar_resultado([[-3, 4, -5, 2]], [(0, 0)], 3)

        self.assertEqual(
            resultado["solucion_general"],
            ["x1 = -2/3 + 4/3x2 - 5/3x3", "x2 es libre", "x3 es libre"],
        )

    def test_la_solucion_unica_usa_el_mismo_modelo(self):
        matriz = [[1, 0, 0, 1], [0, 1, 0, -2], [0, 0, 1, 3]]
        resultado = interpretar_resultado(matriz, [(0, 0), (1, 1), (2, 2)], 3)

        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(
            resultado["solucion_general"], ["x1 = 1", "x2 = -2", "x3 = 3"]
        )
        self.assertEqual(resultado["soluciones"], [1, -2, 3])

    def test_ninguna_expresion_depende_de_una_variable_pivote(self):
        pivotes = [(0, 0), (1, 1)]
        expresiones = solucion_general([[1, 1, 1, 5], [0, 1, 1, 2]], pivotes, 3)
        libres = set(variables_libres(pivotes, 3))

        for expresion in expresiones:
            self.assertLessEqual(set(expresion["coeficientes"]), libres)

    def test_los_valores_se_mantienen_como_fracciones(self):
        expresiones = solucion_general([[2, 1, 3]], [(0, 0)], 2)

        self.assertEqual(expresiones[0]["constante"], Fraction(3, 2))
        self.assertEqual(expresiones[0]["coeficientes"], {2: Fraction(-1, 2)})


class PruebasSolucionGeneralSatisfaceElSistema(unittest.TestCase):
    """Cualquier valor de las variables libres debe cumplir las ecuaciones."""

    CASOS = (
        ([[1, 0, -5, 1], [0, 1, 1, 4], [0, 0, 0, 0]], [(0, 0), (1, 1)], 3),
        ([[1, 1, 1, 5], [0, 1, 1, 2]], [(0, 0), (1, 1)], 3),
        (
            [[1, 6, 0, 3, 0, 0], [0, 0, 1, -4, 0, 5], [0, 0, 0, 0, 1, 7]],
            [(0, 0), (1, 2), (2, 4)],
            5,
        ),
        ([[-3, 4, -5, 2]], [(0, 0)], 3),
    )

    def test_las_ecuaciones_se_cumplen_con_valores_arbitrarios(self):
        for matriz, pivotes, cantidad_variables in self.CASOS:
            with self.subTest(matriz=matriz):
                expresiones = solucion_general(matriz, pivotes, cantidad_variables)
                libres = variables_libres(pivotes, cantidad_variables)

                # Valores arbitrarios y fraccionarios para las variables libres.
                valores = {
                    variable: Fraction(indice + 2, 3)
                    for indice, variable in enumerate(libres)
                }
                for variable in range(1, cantidad_variables + 1):
                    if variable not in valores:
                        valores[variable] = evaluar(
                            expresiones[variable - 1], valores
                        )

                for fila in matriz:
                    total = sum(
                        fila[columna] * valores[columna + 1]
                        for columna in range(cantidad_variables)
                    )
                    self.assertEqual(total, fila[cantidad_variables])


class PruebasSolucionDeSistemasInconsistentes(unittest.TestCase):
    MATRIZ = [[1, 0, -2, 4], [0, 0, 0, 3]]

    def test_la_contradiccion_queda_visible_en_el_sistema_resultante(self):
        resultado = interpretar_resultado(self.MATRIZ, [(0, 0)], 3)

        self.assertEqual(resultado["clasificacion"], INCONSISTENTE)
        self.assertEqual(
            resultado["ecuaciones_resultantes"], ["x1 - 2x3 = 4", "0 = 3"]
        )

    def test_no_existe_solucion(self):
        resultado = interpretar_resultado(self.MATRIZ, [(0, 0)], 3)

        self.assertEqual(resultado["solucion_general"], [SIN_SOLUCION])
        self.assertEqual(resultado["soluciones"], [])

    def test_una_columna_sin_pivote_no_declara_variables_libres(self):
        for resolver in (resolver_sistema_gauss, resolver_sistema_gauss_jordan):
            with self.subTest(metodo=resolver.__name__):
                resultado = resolver(self.MATRIZ)

                for linea in resultado["solucion_general"]:
                    self.assertNotIn("es libre", linea)

    def test_una_variable_libre_no_vuelve_inconsistente_el_sistema(self):
        resultado = resolver_sistema_gauss([[1, 1, 1, 6], [0, 1, 2, 5]])

        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertIn("x3 es libre", resultado["solucion_general"])

    def test_una_fila_nula_tampoco_vuelve_inconsistente_el_sistema(self):
        resultado = resolver_sistema_gauss([[1, 1, 2], [1, 1, 2]])

        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertEqual(resultado["ecuaciones_resultantes"][1], "0 = 0")
        self.assertNotIn(SIN_SOLUCION, resultado["solucion_general"])


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

    def test_ambos_metodos_dan_la_misma_solucion_general(self):
        for matriz in SISTEMAS:
            with self.subTest(matriz=matriz):
                por_gauss = resolver_sistema_gauss(matriz)
                por_gauss_jordan = resolver_sistema_gauss_jordan(matriz)

                self.assertEqual(
                    por_gauss["solucion_general"],
                    por_gauss_jordan["solucion_general"],
                )

    def test_los_sistemas_de_prueba_cubren_una_y_dos_variables_libres(self):
        cantidades = set()
        for matriz in SISTEMAS:
            solucion = resolver_sistema_gauss(matriz)["solucion_general"]
            cantidades.add(
                sum(1 for linea in solucion if linea.endswith("es libre"))
            )

        self.assertLessEqual({0, 1, 2}, cantidades)

    def test_el_sistema_resultante_describe_la_matriz_de_cada_metodo(self):
        for matriz in SISTEMAS:
            with self.subTest(matriz=matriz):
                por_gauss = resolver_sistema_gauss(matriz)
                por_gauss_jordan = resolver_sistema_gauss_jordan(matriz)

                self.assertEqual(
                    por_gauss["ecuaciones_resultantes"],
                    ecuaciones_de_matriz(por_gauss["matriz_escalonada"]),
                )
                self.assertEqual(
                    por_gauss_jordan["ecuaciones_resultantes"],
                    ecuaciones_de_matriz(por_gauss_jordan["matriz_reducida"]),
                )

    def test_el_sistema_resultante_puede_diferir_aunque_la_solucion_coincida(self):
        matriz = [[1, 1, 1, 5], [0, 1, 1, 2]]
        por_gauss = resolver_sistema_gauss(matriz)
        por_gauss_jordan = resolver_sistema_gauss_jordan(matriz)

        self.assertNotEqual(
            por_gauss["ecuaciones_resultantes"],
            por_gauss_jordan["ecuaciones_resultantes"],
        )
        self.assertEqual(
            por_gauss["solucion_general"], por_gauss_jordan["solucion_general"]
        )


if __name__ == "__main__":
    unittest.main()
