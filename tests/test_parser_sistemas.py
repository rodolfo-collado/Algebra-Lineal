"""Pruebas del parser de sistemas de ecuaciones escritos como texto."""

import unittest
from fractions import Fraction

from backend.parser_sistemas import (
    analizar_sistema,
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

    def test_ecuacion_sin_variables(self):
        for texto in ("3 = 5", "0 = 0", "x1 = 2; 4 = 4"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "al menos una variable xN"):
                    parsear_sistema(texto)

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

    def test_devuelve_la_forma_estandar_de_una_ecuacion_libre(self):
        self.assertEqual(parsear_ecuacion("x1 - 6 = -x2"), ({1: 1, 2: 1}, 6))
        # Una variable escrita que se cancela conserva su columna, con coeficiente 0.
        self.assertEqual(parsear_ecuacion("x1 + x3 = x1 + 2"), ({1: 0, 3: 1}, 2))


class PruebasEcuacionesEnFormaLibre(unittest.TestCase):
    """P25.2: términos y constantes en ambos lados; PyGebra normaliza a a1x1 + … + anxn = b."""

    FORMAS_DE_X1_MAS_X2_IGUAL_6 = ("x1 + x2 = 6", "x1 - 6 = -x2", "6 = x1 + x2", "x2 = 6 - x1", "x2 + x1 = 6")

    def test_formas_equivalentes_producen_la_misma_representacion(self):
        for texto in self.FORMAS_DE_X1_MAS_X2_IGUAL_6:
            with self.subTest(texto=texto):
                self.assertEqual(parsear_ecuacion(texto), ({1: 1, 2: 1}, 6))
                self.assertEqual(parsear_sistema(texto), [[1, 1, 6]])
                self.assertEqual(parsear_sistema(texto, limitar_entrada=True), [[1, 1, 6]])

    def test_casos_aceptados(self):
        casos = (
            ("2x1 + 3 = x2 - 5", [[2, -1, -8]]),
            ("-x1 + 4x2 = 7", [[-1, 4, 7]]),
            ("3 = -2x1 + x2", [[-2, 1, 3]]),
            ("x1 + x1 + x2 = 6", [[2, 1, 6]]),
            ("0.5x1 + x2 = 3", [[Fraction(1, 2), 1, 3]]),
            ("1/2x1 - x2 = 4", [[Fraction(1, 2), -1, 4]]),
        )
        for texto, matriz in casos:
            with self.subTest(texto=texto):
                self.assertEqual(parsear_sistema(texto, limitar_entrada=True), matriz)

    def test_terminos_desordenados_conservan_su_signo(self):
        # -x2 + x1 = 6 es x1 - x2 = 6: reordenar no cambia signos.
        self.assertEqual(parsear_sistema("-x2 + x1 = 6"), [[1, -1, 6]])
        self.assertEqual(parsear_sistema("-x2 + x1 = 6"), parsear_sistema("x1 - x2 = 6"))

    def test_constantes_en_ambos_lados(self):
        for texto in ("x1 + 3 = 5", "x1 + 2 = 5 - 1", "3 + x1 - 1 = 4", "x1 = 6 - 2 - 2"):
            with self.subTest(texto=texto):
                self.assertEqual(parsear_sistema(texto), [[1, 2]])

    def test_variables_en_ambos_lados(self):
        self.assertEqual(parsear_sistema("x1 + x2 = x3 + 4"), [[1, 1, -1, 4]])
        self.assertEqual(parsear_sistema("2x1 = x1 + 3"), [[1, 3]])
        self.assertEqual(parsear_sistema("x1 - 6 = -x2 + 2x1"), [[-1, 1, 6]])

    def test_variables_repetidas_en_ambos_lados(self):
        self.assertEqual(parsear_sistema("x1 + x2 = x1 + 3"), [[0, 1, 3]])
        self.assertEqual(parsear_sistema("3x1 + x1 = 2x1 - 4"), [[2, -4]])

    def test_signos_negativos(self):
        # Solo variables a la izquierda: los signos escritos se conservan (compatibilidad).
        self.assertEqual(parsear_sistema("-x1 - x2 = -6"), [[-1, -1, -6]])
        # Solo variables a la derecha: se intercambian los lados, sin cambiar signos.
        self.assertEqual(parsear_sistema("-6 = -x1 - x2"), [[-1, -1, -6]])
        self.assertEqual(parsear_sistema("-x1 = x2 - 6"), [[-1, -1, -6]])

    def test_coeficientes_implicitos(self):
        self.assertEqual(parsear_sistema("x1 = -x2"), [[1, 1, 0]])
        self.assertEqual(parsear_sistema("-x1 = -x2 + 1"), [[-1, 1, 1]])

    def test_fracciones_y_decimales(self):
        self.assertEqual(
            parsear_sistema("1/2x1 + 1/3 = 1/6x2"), [[Fraction(1, 2), Fraction(-1, 6), Fraction(-1, 3)]]
        )
        self.assertEqual(
            parsear_sistema("0.25x1 - 1.5 = .5x2"), [[Fraction(1, 4), Fraction(-1, 2), Fraction(3, 2)]]
        )
        self.assertEqual(parsear_sistema("x1 + 1/2 = 1/2"), [[1, 0]])
        for numero in parsear_sistema("2x1 + 4/2 = 6")[0]:
            self.assertIsInstance(numero, int)

    def test_espacios(self):
        for texto in ("  x1-6   =  - x2 ", "x1-6=-x2", "x 1 - 6 = - x 2"):
            with self.subTest(texto=texto):
                self.assertEqual(parsear_sistema(texto), [[1, 1, 6]])

    def test_ecuaciones_con_cero(self):
        casos = (
            ("x1 + x2 = 0", [[1, 1, 0]]),
            ("0 = x1 - x2", [[1, -1, 0]]),
            ("x1 + 0 = 5", [[1, 5]]),
            ("0x1 + x2 = 3 + 0", [[0, 1, 3]]),
            # Todo se cancela: una fila 0 = 0 (redundante) o 0 = 1 (contradicción).
            ("x1 = x1", [[0, 0]]),
            ("x1 = x1 + 1", [[0, 1]]),
        )
        for texto, matriz in casos:
            with self.subTest(texto=texto):
                self.assertEqual(parsear_sistema(texto), matriz)

    def test_variables_ausentes_en_alguna_ecuacion(self):
        self.assertEqual(
            parsear_sistema("x1 - 6 = -x3; x2 = 2 + x1"),
            [[1, 0, 1, 6], [-1, 1, 0, 2]],
        )

    def test_se_resuelve_igual_que_la_forma_normalizada(self):
        from backend.sistemas import resolver_sistema_gauss_jordan

        libre = resolver_sistema_gauss_jordan(parsear_sistema("x1 - 6 = -x2; x2 = x1 - 2"))
        normal = resolver_sistema_gauss_jordan(parsear_sistema("x1 + x2 = 6; -x1 + x2 = -2"))
        self.assertEqual(libre["solucion_general"], ["x1 = 4", "x2 = 2"])
        self.assertEqual(libre["solucion_general"], normal["solucion_general"])


class PruebasAnalizarSistema(unittest.TestCase):
    def test_solo_se_reescriben_las_ecuaciones_que_no_estaban_en_forma_estandar(self):
        matriz, reescritas = analizar_sistema("x1 + x2 = 6; x1 -  6 = -x2; 6=x1+x2")

        self.assertEqual(matriz, [[1, 1, 6]] * 3)
        self.assertEqual(reescritas, [
            {"numero": 2, "original": "x1 - 6 = -x2", "estandar": "x1 + x2 = 6"},
            {"numero": 3, "original": "6=x1+x2", "estandar": "x1 + x2 = 6"},
        ])

    def test_formas_que_ya_funcionaban_no_generan_pasos(self):
        for texto in ("x1 + x2 = 3; x1 - x2 = 1", "x2 + x1 = 3", "x1 + 2x1 - x2 = 4", "-x1 = 5", "x1 = 1_000"):
            with self.subTest(texto=texto):
                matriz, reescritas = analizar_sistema(texto, limitar_entrada=True)
                self.assertEqual(reescritas, [])
                self.assertEqual(matriz, parsear_sistema(texto))

    def test_la_forma_estandar_agrupa_y_cambia_de_lado(self):
        casos = (
            ("2x1 + 3 = x2 - 5", "2x1 - x2 = -8"),
            ("3 = -2x1 + x2", "-2x1 + x2 = 3"),
            ("x1 = 6 - 2", "x1 = 4"),
            ("1/2x1 + 1 = x2", "1/2x1 - x2 = -1"),
            ("x1 = x1 + 1", "0 = 1"),
        )
        for texto, estandar in casos:
            with self.subTest(texto=texto):
                _, reescritas = analizar_sistema(texto)
                self.assertEqual([ecuacion["estandar"] for ecuacion in reescritas], [estandar])


class PruebasRechazoNoLineal(unittest.TestCase):
    """Un parser de álgebra lineal, no un CAS: lo no lineal se rechaza con su motivo."""

    def test_expresiones_no_lineales(self):
        casos = (
            ("x1*x2 = 5", "multiplica dos variables"),
            ("x1x2 = 5", "multiplica dos variables"),
            ("x1 = x2*x1", "multiplica dos variables"),
            ("x1^2 = 4", "eleva una variable a una potencia"),
            ("x1 = x2^3", "eleva una variable a una potencia"),
            ("1/x1 = 2", "divide por una variable"),
            ("sqrt(x1) = 3", "sqrt(…) no forma parte de una ecuación lineal"),
            ("sin(x1) = 0", "sin(…) no forma parte de una ecuación lineal"),
        )
        for texto, motivo in casos:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError) as contexto:
                    parsear_sistema(texto, limitar_entrada=True)
                mensaje = str(contexto.exception)
                self.assertTrue(mensaje.startswith("Formato de sistema inválido:"), mensaje)
                self.assertIn(motivo, mensaje)
                if "variable" in motivo:
                    self.assertIn("deja de ser lineal", mensaje)

    def test_sintaxis_invalida_con_mensaje_comprensible(self):
        casos = (
            ("2*x1 = 3", "sin *, como 2x1"),
            ("x1/2 = 1", "la fracción antes de la variable"),
            ("2(x1 + x2) = 6", "sin paréntesis"),
            ("2^2x1 = 3", "las potencias no forman parte"),
            ("X1 = 3", "«X1» no es un número ni una variable xN"),
            ("x1 + y = 3", "«y» no es un número ni una variable xN"),
            ("x1 = test", "«test» no es un número ni una variable xN"),
            ("x1 ++ x2 = 3", "cada + o - debe ir seguido"),
            ("x1 = 2 -", "cada + o - debe ir seguido"),
            ("x1 = 1/0", "un número no puede tener denominador cero"),
            ("x1 + 1/0 = x2", "un número no puede tener denominador cero"),
            ("x1 = 1/0x2", "un coeficiente no puede tener denominador cero"),
        )
        for texto, fragmento in casos:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError) as contexto:
                    parsear_sistema(texto, limitar_entrada=True)
                self.assertIn(fragmento, str(contexto.exception))
                self.assertNotIn("Traceback", str(contexto.exception))


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
