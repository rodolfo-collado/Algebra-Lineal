"""Pruebas de la lectura y validacion de datos del usuario."""

import unittest
from fractions import Fraction
from unittest import mock

from backend.parser_sistemas import parsear_sistema
from frontend.terminal import consola, entradas
from tests.ayudas import capturar_con_resultado, sin_ansi


def responder(respuestas):
    """Sustituye la lectura por consola por una lista de respuestas."""
    return mock.patch.object(consola, "pedir", side_effect=respuestas)


class PruebasEnteroPositivo(unittest.TestCase):
    def test_acepta_un_entero_mayor_que_cero(self):
        with responder(["3"]):
            valor, _ = capturar_con_resultado(
                entradas.pedir_entero_positivo, "", "filas"
            )

        self.assertEqual(valor, 3)

    def test_insiste_hasta_recibir_un_entero_valido(self):
        with responder(["hola", "2.5", "4"]):
            valor, salida = capturar_con_resultado(
                entradas.pedir_entero_positivo, "", "filas"
            )

        self.assertEqual(valor, 4)
        self.assertEqual(sin_ansi(salida).count("Ingrese un número válido"), 2)

    def test_rechaza_el_cero_y_los_negativos(self):
        with responder(["0", "-2", "1"]):
            valor, salida = capturar_con_resultado(
                entradas.pedir_entero_positivo, "", "variables"
            )

        self.assertEqual(valor, 1)
        self.assertEqual(
            sin_ansi(salida).count("cantidad de variables debe ser mayor que 0"), 2
        )


class PruebasNumero(unittest.TestCase):
    def test_entero(self):
        with responder(["-7"]):
            numero, _ = capturar_con_resultado(entradas.pedir_numero, "")

        self.assertEqual(numero, -7)

    def test_fraccion(self):
        with responder(["3/4"]):
            numero, _ = capturar_con_resultado(entradas.pedir_numero, "")

        self.assertEqual(numero, Fraction(3, 4))

    def test_decimal(self):
        with responder(["0.5"]):
            numero, _ = capturar_con_resultado(entradas.pedir_numero, "")

        self.assertEqual(numero, Fraction(1, 2))

    def test_insiste_hasta_recibir_un_numero_valido(self):
        with responder(["hola", "1/0", "2"]):
            numero, salida = capturar_con_resultado(entradas.pedir_numero, "")

        self.assertEqual(numero, 2)
        self.assertEqual(sin_ansi(salida).count("Ingrese un número válido"), 2)


class PruebasDimensiones(unittest.TestCase):
    def test_pide_filas_y_columnas(self):
        with responder(["2", "3"]):
            dimensiones, _ = capturar_con_resultado(entradas.pedir_dimensiones)

        self.assertEqual(dimensiones, (2, 3))


class PruebasSistemaManual(unittest.TestCase):
    def test_construye_la_matriz_aumentada(self):
        respuestas = ["3", "2", "1", "-3", "-5", "0", "0", "1", "1", "3"]

        with responder(respuestas):
            matriz, salida = capturar_con_resultado(entradas.pedir_sistema_manual)

        self.assertEqual(matriz, [[1, -3, -5, 0], [0, 1, 1, 3]])
        self.assertIn("Ecuación 1", sin_ansi(salida))
        self.assertIn("Ecuación 2", sin_ansi(salida))

    def test_admite_fracciones_y_decimales(self):
        with responder(["2", "1", "1/2", "0.5", "3/4"]):
            matriz, _ = capturar_con_resultado(entradas.pedir_sistema_manual)

        self.assertEqual(matriz, [[Fraction(1, 2), Fraction(1, 2), Fraction(3, 4)]])

    def test_pregunta_por_cada_variable_y_termino(self):
        with responder(["2", "2", "1", "2", "3", "4", "5", "6"]) as pedir:
            matriz, _ = capturar_con_resultado(entradas.pedir_sistema_manual)

        preguntas = [llamada.args[0] for llamada in pedir.call_args_list]

        self.assertEqual(matriz, [[1, 2, 3], [4, 5, 6]])
        self.assertEqual(preguntas.count("x1: "), 2)
        self.assertEqual(preguntas.count("x2: "), 2)
        self.assertEqual(preguntas.count("Término independiente: "), 2)

    def test_el_ingreso_manual_equivale_al_textual(self):
        with responder(["3", "2", "1", "-3", "-5", "0", "0", "1", "1", "3"]):
            matriz, _ = capturar_con_resultado(entradas.pedir_sistema_manual)

        self.assertEqual(matriz, parsear_sistema("x1 - 3x2 - 5x3 = 0; x2 + x3 = 3"))


class PruebasElementosDeMatriz(unittest.TestCase):
    def test_elemento_con_fraccion(self):
        with responder(["1/3"]):
            numero, _ = capturar_con_resultado(entradas.pedir_elemento_matriz, 1, 1)

        self.assertEqual(numero, Fraction(1, 3))

    def test_nuevo_numero_con_decimal(self):
        with responder(["2.5"]):
            numero, _ = capturar_con_resultado(entradas.pedir_nuevo_numero)

        self.assertEqual(numero, Fraction(5, 2))


class PruebasIndices(unittest.TestCase):
    def test_acepta_indices_dentro_de_rango(self):
        with responder(["1", "2"]):
            indices, _ = capturar_con_resultado(
                entradas.pedir_indices, [[1, 2], [3, 4]]
            )

        self.assertEqual(indices, (1, 2))

    def test_rechaza_una_fila_fuera_de_rango(self):
        with responder(["9", "1", "1"]):
            indices, salida = capturar_con_resultado(entradas.pedir_indices, [[1, 2]])

        self.assertEqual(indices, (1, 1))
        self.assertIn("Fila fuera de rango", sin_ansi(salida))

    def test_rechaza_una_columna_fuera_de_rango(self):
        with responder(["1", "9", "1", "2"]):
            indices, salida = capturar_con_resultado(entradas.pedir_indices, [[1, 2]])

        self.assertEqual(indices, (1, 2))
        self.assertIn("Columna fuera de rango", sin_ansi(salida))


if __name__ == "__main__":
    unittest.main()
