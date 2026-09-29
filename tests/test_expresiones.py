"""Pruebas de las expresiones lineales y de como se escriben."""

import unittest
from fractions import Fraction

from backend.expresiones import (
    crear_expresion,
    expresion_de_variable,
    expresion_desde_terminos,
    formatear_ecuacion,
    formatear_expresion,
    formatear_termino,
    multiplicar_expresion,
    normalizar_igualdad,
    restar_expresiones,
)


class PruebasConstruccion(unittest.TestCase):
    def test_una_expresion_vacia_vale_cero(self):
        expresion = crear_expresion()

        self.assertEqual(expresion["constante"], 0)
        self.assertEqual(expresion["coeficientes"], {})

    def test_los_coeficientes_en_cero_no_se_guardan(self):
        expresion = crear_expresion(1, {1: 0, 2: 5})

        self.assertEqual(expresion["coeficientes"], {2: Fraction(5)})

    def test_todo_se_guarda_como_fraccion(self):
        expresion = crear_expresion(2, {1: 3})

        self.assertIsInstance(expresion["constante"], Fraction)
        self.assertIsInstance(expresion["coeficientes"][1], Fraction)

    def test_una_variable_libre_se_representa_a_si_misma(self):
        self.assertEqual(
            expresion_de_variable(3), crear_expresion(0, {3: 1})
        )


class PruebasAritmetica(unittest.TestCase):
    def test_multiplicar_afecta_a_la_constante_y_a_los_coeficientes(self):
        expresion = multiplicar_expresion(crear_expresion(2, {1: 3}), -2)

        self.assertEqual(expresion, crear_expresion(-4, {1: -6}))

    def test_multiplicar_por_una_fraccion_mantiene_la_exactitud(self):
        expresion = multiplicar_expresion(
            crear_expresion(2, {1: 5}), Fraction(1, 3)
        )

        self.assertEqual(
            expresion, crear_expresion(Fraction(2, 3), {1: Fraction(5, 3)})
        )

    def test_multiplicar_por_cero_deja_la_expresion_vacia(self):
        expresion = multiplicar_expresion(crear_expresion(2, {1: 3}), 0)

        self.assertEqual(expresion, crear_expresion())

    def test_restar_combina_las_variables_comunes(self):
        expresion = restar_expresiones(
            crear_expresion(5, {1: 2, 2: 1}), crear_expresion(3, {1: 1})
        )

        self.assertEqual(expresion, crear_expresion(2, {1: 1, 2: 1}))

    def test_restar_puede_cancelar_una_variable(self):
        expresion = restar_expresiones(
            crear_expresion(5, {1: 2}), crear_expresion(0, {1: 2})
        )

        self.assertEqual(expresion["coeficientes"], {})

    def test_restar_introduce_variables_que_no_estaban(self):
        expresion = restar_expresiones(crear_expresion(5), crear_expresion(0, {2: 4}))

        self.assertEqual(expresion, crear_expresion(5, {2: -4}))

    def test_ninguna_operacion_produce_floats(self):
        expresion = multiplicar_expresion(
            restar_expresiones(crear_expresion(1, {1: 1}), crear_expresion(0, {1: 3})),
            Fraction(1, 7),
        )

        self.assertNotIsInstance(expresion["constante"], float)
        self.assertNotIsInstance(expresion["coeficientes"][1], float)


class PruebasRepresentarYNormalizar(unittest.TestCase):
    """La base que comparten los parsers de ecuaciones: términos → expresión → forma estándar."""

    def test_los_terminos_semejantes_se_agrupan(self):
        expresion = expresion_desde_terminos(
            [(1, Fraction(2)), (None, Fraction(3)), (1, Fraction(-1)), (None, Fraction(1, 2))]
        )

        self.assertEqual(expresion, crear_expresion(Fraction(7, 2), {1: 1}))
        self.assertEqual(expresion_desde_terminos([]), crear_expresion())
        self.assertEqual(expresion_desde_terminos([(2, Fraction(1)), (2, Fraction(-1))]), crear_expresion())

    def test_normalizar_pasa_las_variables_a_la_izquierda(self):
        # x1 - 6 = -x2  →  x1 + x2 = 6
        expresion, termino = normalizar_igualdad(crear_expresion(-6, {1: 1}), crear_expresion(0, {2: -1}))

        self.assertEqual(expresion, crear_expresion(0, {1: 1, 2: 1}))
        self.assertEqual(termino, 6)
        self.assertIsInstance(termino, Fraction)

    def test_si_solo_la_derecha_tiene_variables_se_intercambian_los_lados(self):
        # 6 = x1 + x2  →  x1 + x2 = 6, no -x1 - x2 = -6
        expresion, termino = normalizar_igualdad(crear_expresion(6), crear_expresion(0, {1: 1, 2: 1}))

        self.assertEqual(formatear_ecuacion(expresion, termino), "x1 + x2 = 6")

    def test_la_forma_estandar_ya_normalizada_no_cambia(self):
        izquierda = crear_expresion(0, {1: -1, 2: 4})

        self.assertEqual(normalizar_igualdad(izquierda, crear_expresion(7)), (izquierda, 7))

    def test_formas_equivalentes_dan_la_misma_forma_estandar(self):
        x1_mas_x2 = crear_expresion(0, {1: 1, 2: 1})
        formas = (
            (x1_mas_x2, crear_expresion(6)),                              # x1 + x2 = 6
            (crear_expresion(-6, {1: 1}), crear_expresion(0, {2: -1})),   # x1 - 6 = -x2
            (crear_expresion(6), x1_mas_x2),                              # 6 = x1 + x2
            (crear_expresion(0, {2: 1}), crear_expresion(6, {1: -1})),    # x2 = 6 - x1
        )
        for izquierda, derecha in formas:
            with self.subTest(izquierda=izquierda, derecha=derecha):
                self.assertEqual(normalizar_igualdad(izquierda, derecha), (x1_mas_x2, 6))

    def test_una_igualdad_que_se_cancela_queda_como_fila_nula_o_contradiccion(self):
        self.assertEqual(normalizar_igualdad(crear_expresion(0, {1: 1}), crear_expresion(0, {1: 1})), (crear_expresion(), 0))
        self.assertEqual(normalizar_igualdad(crear_expresion(0, {1: 1}), crear_expresion(1, {1: 1})), (crear_expresion(), 1))

    def test_no_depende_de_la_sintaxis_ni_de_la_letra(self):
        # La letra solo interviene al formatear: otro parser con otra notación reutiliza lo mismo.
        expresion, termino = normalizar_igualdad(
            expresion_desde_terminos([(1, Fraction(3)), (None, Fraction(1))]),
            expresion_desde_terminos([(2, Fraction(1, 2)), (None, Fraction(4))]),
        )

        self.assertEqual(formatear_ecuacion(expresion, termino, "c"), "3c1 - 1/2c2 = 3")


class PruebasFormatoDeTerminos(unittest.TestCase):
    def test_coeficiente_uno_no_se_escribe(self):
        self.assertEqual(formatear_termino(1, 1), "x1")

    def test_coeficiente_menos_uno_solo_deja_el_signo(self):
        self.assertEqual(formatear_termino(-1, 2), "-x2")

    def test_coeficiente_entero(self):
        self.assertEqual(formatear_termino(2, 1), "2x1")
        self.assertEqual(formatear_termino(-2, 1), "-2x1")

    def test_coeficiente_fraccionario(self):
        self.assertEqual(formatear_termino(Fraction(1, 2), 1), "1/2x1")
        self.assertEqual(formatear_termino(Fraction(-3, 4), 1), "-3/4x1")


class PruebasFormatoDeExpresiones(unittest.TestCase):
    def test_solo_constante(self):
        self.assertEqual(formatear_expresion(crear_expresion(3)), "3")

    def test_expresion_nula(self):
        self.assertEqual(formatear_expresion(crear_expresion(0)), "0")

    def test_constante_y_variable(self):
        self.assertEqual(formatear_expresion(crear_expresion(3, {1: 2})), "3 + 2x1")

    def test_una_resta_no_encadena_signos(self):
        texto = formatear_expresion(crear_expresion(3, {2: -1}))

        self.assertEqual(texto, "3 - x2")
        self.assertNotIn("+ -", texto)

    def test_constante_cero_se_omite_si_hay_variables(self):
        texto = formatear_expresion(crear_expresion(0, {2: -6, 4: -3}))

        self.assertEqual(texto, "-6x2 - 3x4")

    def test_las_variables_salen_en_orden_ascendente(self):
        texto = formatear_expresion(crear_expresion(0, {4: 1, 1: 2, 3: -1}))

        self.assertEqual(texto, "2x1 - x3 + x4")

    def test_fracciones_con_signo(self):
        expresion = crear_expresion(
            Fraction(-2, 3), {2: Fraction(4, 3), 3: Fraction(-5, 3)}
        )

        self.assertEqual(formatear_expresion(expresion), "-2/3 + 4/3x2 - 5/3x3")

    def test_nunca_aparece_un_coeficiente_uno_explicito(self):
        texto = formatear_expresion(crear_expresion(0, {1: 1, 2: -1}))

        self.assertNotIn("1x1", texto)
        self.assertNotIn("-1x2", texto)


class PruebasFormatoDeEcuaciones(unittest.TestCase):
    def test_ecuacion_normal(self):
        expresion = crear_expresion(0, {1: 1, 3: -5})

        self.assertEqual(formatear_ecuacion(expresion, 1), "x1 - 5x3 = 1")

    def test_una_fila_nula_se_escribe_igual(self):
        self.assertEqual(formatear_ecuacion(crear_expresion(), 0), "0 = 0")

    def test_una_contradiccion_se_escribe_igual(self):
        self.assertEqual(formatear_ecuacion(crear_expresion(), 3), "0 = 3")

    def test_termino_independiente_fraccionario(self):
        expresion = crear_expresion(0, {1: Fraction(1, 2)})

        self.assertEqual(
            formatear_ecuacion(expresion, Fraction(2, 3)), "1/2x1 = 2/3"
        )


if __name__ == "__main__":
    unittest.main()
