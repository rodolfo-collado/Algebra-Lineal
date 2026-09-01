"""Pruebas del parser de sistemas de ecuaciones escritos como texto."""

import unittest
from fractions import Fraction

from backend.parser_sistemas import (
    construir_matriz_aumentada,
    convertir_a_numero,
    parsear_ecuacion,
    parsear_sistema,
)


class PruebasSistemasBasicos(unittest.TestCase):
    def test_dos_ecuaciones_y_dos_variables(self):
        matriz = parsear_sistema("x1 + x2 = 3; x1 - x2 = 1")

        self.assertEqual(matriz, [[1, 1, 3], [1, -1, 1]])

    def test_una_sola_ecuacion(self):
        self.assertEqual(parsear_sistema("2x1 = 6"), [[2, 6]])

    def test_coeficientes_de_varias_cifras(self):
        matriz = parsear_sistema("12x1 - 100x2 = 25")

        self.assertEqual(matriz, [[12, -100, 25]])

    def test_variables_con_indice_de_dos_cifras(self):
        matriz = parsear_sistema("x10 = 4")

        self.assertEqual(len(matriz[0]), 11)
        self.assertEqual(matriz, [[0] * 9 + [1, 4]])


class PruebasEspaciosLibres(unittest.TestCase):
    def test_espacios_alrededor_de_operadores_y_variables(self):
        matriz = parsear_sistema("   x1   -   3 x2   =   0   ")

        self.assertEqual(matriz, [[1, -3, 0]])

    def test_espacios_alrededor_del_separador(self):
        matriz = parsear_sistema("x1 + x2 = 4   ;   x1 - x2 = 2")

        self.assertEqual(matriz, [[1, 1, 4], [1, -1, 2]])

    def test_sistema_sin_espacios(self):
        self.assertEqual(parsear_sistema("x1+x2=4;x1-x2=2"), [[1, 1, 4], [1, -1, 2]])


class PruebasVariablesAusentes(unittest.TestCase):
    def test_la_variable_ausente_vale_cero(self):
        matriz = parsear_sistema("x1 - 3x2 - 5x3 = 0; x2 + x3 = 3")

        self.assertEqual(matriz, [[1, -3, -5, 0], [0, 1, 1, 3]])

    def test_cada_ecuacion_omite_una_variable_distinta(self):
        matriz = parsear_sistema("x1 + x3 = 5; x2 - x3 = 2")

        self.assertEqual(matriz, [[1, 0, 1, 5], [0, 1, -1, 2]])

    def test_la_cantidad_de_variables_la_marca_el_mayor_indice(self):
        matriz = parsear_sistema("x4 = 1; x1 = 2")

        self.assertEqual(matriz, [[0, 0, 0, 1, 1], [1, 0, 0, 0, 2]])

    def test_los_terminos_pueden_ir_desordenados(self):
        matriz = parsear_sistema("x2 + x1 = 3")

        self.assertEqual(matriz, [[1, 1, 3]])


class PruebasCoeficientesImplicitos(unittest.TestCase):
    def test_variable_sin_coeficiente_vale_uno(self):
        self.assertEqual(parsear_sistema("x1 - x2 = 4"), [[1, -1, 4]])

    def test_signo_positivo_explicito(self):
        self.assertEqual(parsear_sistema("+x1 + x2 = 2"), [[1, 1, 2]])

    def test_primer_termino_negativo(self):
        self.assertEqual(parsear_sistema("-x1 + x2 = 3; x1 + x2 = 5"), [[-1, 1, 3], [1, 1, 5]])


class PruebasTiposNumericos(unittest.TestCase):
    def test_enteros_negativos(self):
        self.assertEqual(parsear_sistema("-x1 - 2x2 = -5"), [[-1, -2, -5]])

    def test_fracciones(self):
        matriz = parsear_sistema("1/2x1 + 3/4x2 = 2")

        self.assertEqual(matriz, [[Fraction(1, 2), Fraction(3, 4), 2]])

    def test_fracciones_negativas(self):
        matriz = parsear_sistema("-3/4x1 = 1/2")

        self.assertEqual(matriz, [[Fraction(-3, 4), Fraction(1, 2)]])

    def test_decimales(self):
        matriz = parsear_sistema("0.5x1 + 1.25x2 = 3")

        self.assertEqual(matriz, [[Fraction(1, 2), Fraction(5, 4), 3]])

    def test_termino_independiente_decimal(self):
        self.assertEqual(parsear_sistema("x1 = 2.5"), [[1, Fraction(5, 2)]])

    def test_los_decimales_no_se_guardan_como_float(self):
        matriz = parsear_sistema("0.5x1 = 0.25")

        for numero in matriz[0]:
            self.assertNotIsInstance(numero, float)
            self.assertIsInstance(numero, Fraction)

    def test_un_entero_no_se_guarda_como_fraccion(self):
        matriz = parsear_sistema("2x1 = 6")

        for numero in matriz[0]:
            self.assertIsInstance(numero, int)


class PruebasVariablesRepetidas(unittest.TestCase):
    def test_los_coeficientes_repetidos_se_suman(self):
        self.assertEqual(parsear_sistema("x1 + 2x1 - x2 = 4"), [[3, -1, 4]])

    def test_los_coeficientes_repetidos_pueden_cancelarse(self):
        self.assertEqual(parsear_sistema("x1 - x1 + x2 = 2"), [[0, 1, 2]])


class PruebasErroresDelParser(unittest.TestCase):
    def test_sistema_vacio(self):
        for texto in ("", "   ", "\n"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    parsear_sistema(texto)

    def test_texto_que_no_es_cadena(self):
        with self.assertRaises(ValueError):
            parsear_sistema(None)

    def test_falta_el_signo_igual(self):
        with self.assertRaises(ValueError):
            parsear_sistema("x1 + x2")

    def test_mas_de_un_signo_igual(self):
        with self.assertRaises(ValueError):
            parsear_sistema("x1 = 2 = 3")

    def test_indice_cero(self):
        with self.assertRaises(ValueError):
            parsear_sistema("x0 + x1 = 2")

    def test_variable_invalida(self):
        for texto in ("2y1 + x2 = 3", "x1 + abc = 2", "x = 3"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    parsear_sistema(texto)

    def test_sintaxis_invalida(self):
        with self.assertRaises(ValueError):
            parsear_sistema("x1 ++ x2 = 3")

    def test_termino_independiente_no_numerico(self):
        with self.assertRaises(ValueError):
            parsear_sistema("x1 = hola")

    def test_termino_incompleto(self):
        with self.assertRaises(ValueError):
            parsear_sistema("x1 + = 3")

    def test_separacion_invalida(self):
        for texto in ("x1 = 2;; x2 = 3", "x1 = 2;", "; x1 = 2"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    parsear_sistema(texto)

    def test_lado_vacio(self):
        for texto in ("x1 =", "= 3"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    parsear_sistema(texto)

    def test_variables_en_el_lado_derecho(self):
        with self.assertRaises(ValueError):
            parsear_sistema("x1 + x2 = x3 + 4")

    def test_termino_constante_a_la_izquierda(self):
        with self.assertRaises(ValueError):
            parsear_sistema("x1 + 3 = 5")

    def test_denominador_cero(self):
        with self.assertRaises(ValueError):
            parsear_sistema("1/0x1 = 2")

    def test_el_mensaje_identifica_el_problema(self):
        with self.assertRaises(ValueError) as contexto:
            parsear_sistema("x1 = 2 = 3")

        self.assertEqual(
            str(contexto.exception),
            "Formato de sistema inválido: cada ecuación debe contener un "
            "único signo '='."
        )

    def test_el_mensaje_empieza_igual_para_cualquier_error(self):
        for texto in ("x1 + x2", "x0 = 1", "x1 = hola"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError) as contexto:
                    parsear_sistema(texto)

                self.assertTrue(
                    str(contexto.exception).startswith("Formato de sistema inválido:")
                )


class PruebasParsearEcuacion(unittest.TestCase):
    def test_devuelve_coeficientes_por_indice(self):
        coeficientes, termino_independiente = parsear_ecuacion("2x1 - x3 = 7")

        self.assertEqual(coeficientes, {1: 2, 3: -1})
        self.assertEqual(termino_independiente, 7)


class PruebasConvertirANumero(unittest.TestCase):
    def test_entero(self):
        self.assertEqual(convertir_a_numero("7"), 7)
        self.assertIsInstance(convertir_a_numero("7"), int)

    def test_entero_negativo(self):
        self.assertEqual(convertir_a_numero("-7"), -7)

    def test_fraccion(self):
        self.assertEqual(convertir_a_numero("3/4"), Fraction(3, 4))

    def test_fraccion_que_equivale_a_un_entero(self):
        self.assertEqual(convertir_a_numero("4/2"), 2)
        self.assertIsInstance(convertir_a_numero("4/2"), int)

    def test_decimal(self):
        self.assertEqual(convertir_a_numero("1.25"), Fraction(5, 4))
        self.assertNotIsInstance(convertir_a_numero("1.25"), float)

    def test_espacios_alrededor(self):
        self.assertEqual(convertir_a_numero("  -3/4  "), Fraction(-3, 4))

    def test_espacios_dentro_de_la_fraccion(self):
        self.assertEqual(convertir_a_numero("1 / 2"), Fraction(1, 2))

    def test_texto_invalido(self):
        for texto in ("", "hola", "1/0", "x1", "1,5"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    convertir_a_numero(texto)


class PruebasConstruirMatrizAumentada(unittest.TestCase):
    def test_une_coeficientes_y_terminos_independientes(self):
        matriz = construir_matriz_aumentada([[1, -3, -5], [0, 1, 1]], [0, 3])

        self.assertEqual(matriz, [[1, -3, -5, 0], [0, 1, 1, 3]])

    def test_conserva_fracciones(self):
        matriz = construir_matriz_aumentada([[Fraction(1, 2)]], [Fraction(3, 4)])

        self.assertEqual(matriz, [[Fraction(1, 2), Fraction(3, 4)]])

    def test_no_comparte_las_filas_recibidas(self):
        coeficientes = [[1, 2]]
        matriz = construir_matriz_aumentada(coeficientes, [3])

        matriz[0][0] = 99

        self.assertEqual(coeficientes, [[1, 2]])

    def test_sin_ecuaciones(self):
        with self.assertRaises(ValueError):
            construir_matriz_aumentada([], [])

    def test_faltan_terminos_independientes(self):
        with self.assertRaises(ValueError):
            construir_matriz_aumentada([[1, 2], [3, 4]], [1])

    def test_ecuacion_sin_variables(self):
        with self.assertRaises(ValueError):
            construir_matriz_aumentada([[]], [1])


class PruebasEquivalenciaDeIngresos(unittest.TestCase):
    """El ingreso textual y el manual deben producir la misma matriz."""

    def test_sistema_de_tres_variables(self):
        directo = parsear_sistema("x1 - 3x2 - 5x3 = 0; x2 + x3 = 3")
        manual = construir_matriz_aumentada([[1, -3, -5], [0, 1, 1]], [0, 3])

        self.assertEqual(directo, manual)

    def test_sistema_con_fracciones(self):
        directo = parsear_sistema("1/2x1 + 3/4x2 = 2")
        manual = construir_matriz_aumentada([[Fraction(1, 2), Fraction(3, 4)]], [2])

        self.assertEqual(directo, manual)

    def test_sistema_con_decimales(self):
        directo = parsear_sistema("0.5x1 + 1.25x2 = 3")
        manual = construir_matriz_aumentada(
            [[Fraction(1, 2), Fraction(5, 4)]], [3]
        )

        self.assertEqual(directo, manual)


if __name__ == "__main__":
    unittest.main()
