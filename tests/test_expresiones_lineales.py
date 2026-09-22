"""Igualdad simbólica y determinación de A dentro del evaluador de expresiones."""

from fractions import Fraction
from unittest import TestCase

from backend.expresiones_matriciales import Comparacion, Determinacion, aplanar, evaluar
from backend.expresiones_matriciales.evaluador import preparar_simbolo

A = [[2, 5], [3, 1]]
U = [4, -1]
V = [-3, 5]
EJEMPLO = {
    "A": {"tipo": "matriz", "valor": A},
    "u": {"tipo": "vector", "valor": U},
    "v": {"tipo": "vector", "valor": V},
}
MATRICES = {
    "A": {"tipo": "matriz", "valor": A},
    "B": {"tipo": "matriz", "valor": [[1, 0], [0, 1]]},
}


def simbolos(filas=3, columnas=2, componentes=("3x1 - 2x2", "x1 + 4x2", "x2"), dimension_x=2):
    return {
        "A": {"tipo": "matriz_desconocida", "filas": filas, "columnas": columnas},
        "x": {"tipo": "vector_simbolico", "filas": dimension_x},
        "b": {"tipo": "vector_lineal", "valor": list(componentes)},
    }


class PruebasIntegracion(TestCase):
    def test_el_caso_principal_sale_del_evaluador(self):
        resultado = evaluar("Ax = b", simbolos())
        self.assertIsInstance(resultado, Determinacion)
        self.assertEqual(resultado.resultado, (
            (Fraction(3), Fraction(-2)),
            (Fraction(1), Fraction(4)),
            (Fraction(0), Fraction(1)),
        ))
        self.assertTrue(resultado.verificada)
        self.assertEqual(resultado.texto, "Ax = b")
        self.assertEqual(
            [paso.id for paso in aplanar(evaluar("Ax = b", simbolos(), "izq:0").principal)],
            ["izq:0.0", "izq:0.1", "izq:0"],
        )

    def test_los_otros_tamanos_fracciones_y_normalizacion(self):
        cuadrada = evaluar("Ax = b", simbolos(2, 2, ("2x1 + x2", "-x1 + 3x2")))
        self.assertEqual(cuadrada.resultado, ((Fraction(2), Fraction(1)), (Fraction(-1), Fraction(3))))
        rectangular = evaluar("A*x = b", {
            "A": {"tipo": "matriz_desconocida", "filas": 2, "columnas": 3},
            "x": {"tipo": "vector_simbolico", "filas": 3},
            "b": {"tipo": "vector_lineal", "valor": ["x1 + 2x3", "-x2 + 4x3"]},
        })
        self.assertEqual(rectangular.resultado, (
            (Fraction(1), Fraction(0), Fraction(2)),
            (Fraction(0), Fraction(-1), Fraction(4)),
        ))
        fraccion = evaluar("Ax = b", simbolos(2, 2, ("(1/2)x1 - (3/4)x2", "x1 + (2/3)x2")))
        self.assertEqual(fraccion.resultado[0], (Fraction(1, 2), Fraction(-3, 4)))
        self.assertIsInstance(fraccion.resultado[0][0], Fraction)
        ausente = evaluar("Ax = b", simbolos(2, 2, ("x2", "x1")))
        self.assertEqual(ausente.resultado, ((Fraction(0), Fraction(1)), (Fraction(1), Fraction(0))))
        normal = evaluar("Ax = b", simbolos(2, 2, ("2(x1 + x2) - x1", "x1 - x1 + 3x2")))
        self.assertEqual(normal.resultado, ((Fraction(1), Fraction(2)), (Fraction(0), Fraction(3))))
        self.assertTrue(normal.verificada)

    def test_b_igual_ax_usa_el_mismo_procedimiento(self):
        resultado = evaluar("b = Ax", simbolos())
        self.assertEqual(resultado.resultado[0], (Fraction(3), Fraction(-2)))
        self.assertEqual(resultado.etiqueta, "b")

    def test_rechazos(self):
        with self.assertRaisesRegex(ValueError, r"contiene x3, pero x está formado únicamente por x1 y x2"):
            evaluar("Ax = b", simbolos(2, 2, ("x1 + x3", "x2")))
        with self.assertRaisesRegex(ValueError, "término constante independiente"):
            evaluar("Ax = b", simbolos(2, 2, ("x1 + 2", "x2")))
        with self.assertRaisesRegex(ValueError, "multiplica dos cantidades simbólicas"):
            evaluar("Ax = b", simbolos(1, 2, ("x1*x2",)))
        with self.assertRaisesRegex(ValueError, r"necesita un vector de 2 componentes, pero x tiene 3"):
            evaluar("Ax = b", simbolos(3, 2, ("x1", "x2", "x3"), 3))
        with self.assertRaisesRegex(ValueError, r"Ax tiene 3 componentes pero b tiene 4"):
            evaluar("Ax = b", simbolos(3, 2, ("x1", "x2", "x1", "x2")))
        with self.assertRaisesRegex(ValueError, "El símbolo Z no está definido"):
            evaluar("Z*x = b", simbolos())
        with self.assertRaisesRegex(ValueError, "vector de expresiones lineales"):
            evaluar("Ax = u", {**simbolos(), "u": {"tipo": "vector", "valor": [1, 2, 3]}})

    def test_una_matriz_numerica_no_se_adivina_como_incognita(self):
        numerica = {
            "A": {"tipo": "matriz", "valor": [[3, -2], [1, 4], [0, 1]]},
            "x": {"tipo": "vector_simbolico", "filas": 2},
            "b": {"tipo": "vector_lineal", "valor": ["3x1 - 2x2", "x1 + 4x2", "x2"]},
        }
        comparacion = evaluar("Ax = b", numerica)
        self.assertIsInstance(comparacion, Comparacion)
        self.assertNotIsInstance(comparacion, Determinacion)
        self.assertEqual(comparacion.alcance, "simbolica")
        self.assertTrue(comparacion.coincide)
        self.assertIn("para todos los valores de x1 y x2", comparacion.mensaje)
        self.assertNotIn("valores dados", comparacion.mensaje)
        distinta = evaluar("Ax = b", {**numerica, "b": {"tipo": "vector_lineal", "valor": ["x2", "x1", "0"]}})
        self.assertFalse(distinta.coincide)
        self.assertIn("no representan la misma expresión lineal", distinta.mensaje)

    def test_simbolo_sin_declarar_no_es_incognita_y_el_vector_no_se_evalua_a_numero(self):
        with self.assertRaisesRegex(ValueError, "no está definido"):
            evaluar("A + Z", {"A": MATRICES["A"]})
        equis = preparar_simbolo("x", {"tipo": "vector_simbolico", "filas": 2})
        self.assertEqual(equis.tipo, "vector_simbolico")
        self.assertEqual(equis.valor.variables, ("x1", "x2"))
        self.assertNotIsInstance(equis.valor, list)


class PruebasRegresionNumerica(TestCase):
    def test_p20_y_p21_siguen_comparando_valores_concretos(self):
        self.assertEqual(evaluar("A(u + v)", EJEMPLO).principal.resultado, [22, 7])
        self.assertEqual(evaluar("Au + Av", EJEMPLO).principal.resultado, [22, 7])
        self.assertEqual(evaluar("2A - 3B", {
            "A": MATRICES["A"], "B": {"tipo": "matriz", "valor": [[1, 0], [0, 1]]},
        }).principal.resultado, [[1, 10], [6, -1]])
        igualdad = evaluar("A(u + v) = Au + Av", EJEMPLO)
        self.assertIsInstance(igualdad, Comparacion)
        self.assertTrue(igualdad.coincide)
        self.assertEqual(igualdad.alcance, "valores")
        self.assertIn("para los valores dados", igualdad.mensaje)
        self.assertIn("[22, 7]", igualdad.mensaje)
        falsa = evaluar("Au = Av", EJEMPLO)
        self.assertFalse(falsa.coincide)
        self.assertIn("diferentes", falsa.mensaje)
        self.assertEqual(evaluar("A(u + v) = Au + Av", EJEMPLO, "izq:0.1").principal.resultado, [1, 4])
        self.assertEqual(evaluar("A(u + v) = Au + Av", EJEMPLO, "der:0").principal.resultado, [22, 7])
        fraccion = evaluar("(1/3) + (1/3) + (1/3) = 1", {})
        self.assertTrue(fraccion.coincide)
        self.assertIn("producen 1", fraccion.mensaje)
        self.assertTrue(evaluar("2(A + B) = 2A + 2B", MATRICES).coincide)
