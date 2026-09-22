"""Formas lineales: aritmética exacta, normalización y columnas de A."""

import ast
from fractions import Fraction
from pathlib import Path
from unittest import TestCase

from backend.expresiones_matriciales.lineal import (
    FormaLineal,
    MatrizDesconocida,
    VectorLineal,
    VectorSimbolico,
    analizar_lineal,
    coef_vector,
    determinar,
    escalar,
    forma,
    negar,
    restar,
    sumar,
    texto_forma,
)

A32 = MatrizDesconocida("A", 3, 2)
X2 = VectorSimbolico("x", ("x1", "x2"))


def vector(textos, variables=()):
    return VectorLineal(tuple(analizar_lineal(texto) for texto in textos), variables)


class PruebasFormaLineal(TestCase):
    def test_constante_y_coeficientes_son_fraction(self):
        obtenida = forma(5, {"x1": 3, "x2": -2, "x3": 0})
        self.assertEqual(obtenida.constante, Fraction(5))
        self.assertEqual(obtenida.coeficiente("x1"), Fraction(3))
        self.assertEqual(obtenida.coeficiente("x2"), Fraction(-2))
        self.assertEqual(obtenida.coeficiente("x3"), Fraction(0))
        self.assertNotIn("x3", dict(obtenida.coeficientes))
        self.assertIsInstance(obtenida.coeficiente("x1"), Fraction)

    def test_suma_resta_negacion_y_escalar(self):
        izquierda = forma(1, {"x1": 3, "x2": -2})
        derecha = forma(4, {"x2": 5, "x3": 1})
        self.assertEqual(sumar(izquierda, derecha), forma(5, {"x1": 3, "x2": 3, "x3": 1}))
        self.assertEqual(restar(izquierda, derecha), forma(-3, {"x1": 3, "x2": -7, "x3": -1}))
        self.assertEqual(negar(izquierda), forma(-1, {"x1": -3, "x2": 2}))
        self.assertEqual(escalar(Fraction(1, 2), izquierda), forma(Fraction(1, 2), {"x1": Fraction(3, 2), "x2": -1}))
        self.assertEqual(escalar(0, izquierda), forma(0))

    def test_la_igualdad_no_depende_del_orden_de_los_terminos(self):
        self.assertEqual(forma(0, {"x1": 1, "x2": 2}), forma(0, {"x2": 2, "x1": 1}))
        self.assertNotEqual(forma(0, {"x1": 1}), forma(1, {"x1": 1}))


class PruebasParserLineal(TestCase):
    def test_ejemplos_validos_y_fracciones(self):
        self.assertEqual(analizar_lineal("3x1"), forma(0, {"x1": 3}))
        self.assertEqual(analizar_lineal("-2x2"), forma(0, {"x2": -2}))
        self.assertEqual(analizar_lineal("x1 + x2"), forma(0, {"x1": 1, "x2": 1}))
        self.assertEqual(analizar_lineal("2(x1 - 3x2)"), forma(0, {"x1": 2, "x2": -6}))
        mitad = analizar_lineal("(1/2)x1 + (3/4)x2")
        self.assertEqual(mitad.coeficiente("x1"), Fraction(1, 2))
        self.assertEqual(mitad.coeficiente("x2"), Fraction(3, 4))
        self.assertEqual(analizar_lineal("3x1 - 2x2 + 5").constante, Fraction(5))
        self.assertEqual(analizar_lineal("1/2x1").coeficiente("x1"), Fraction(1, 2))

    def test_normalizacion_por_coeficientes(self):
        self.assertEqual(analizar_lineal("x1 + x1"), analizar_lineal("2x1"))
        self.assertEqual(analizar_lineal("2(x1 + x2) - x1"), analizar_lineal("x1 + 2x2"))
        self.assertEqual(analizar_lineal("x1 - x1"), forma(0))
        self.assertEqual(texto_forma(analizar_lineal("x1 + x1")), "2x1")
        self.assertEqual(texto_forma(analizar_lineal("x2"), ("x1", "x2")), "x2")
        self.assertEqual(texto_forma(analizar_lineal("3x1 - 2x2 + 5"), ("x1", "x2")), "3x1 - 2x2 + 5")
        self.assertEqual(texto_forma(forma(0)), "0")

    def test_rechaza_lo_que_deja_de_ser_lineal(self):
        for texto in ("x1*x2", "x1*x1", "(x1)(x2)", "sin(x1)", "x1(x2)"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "multiplica dos cantidades simbólicas"):
                    analizar_lineal(texto)
        for texto in ("x1^2", "x1^3"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "potencia"):
                    analizar_lineal(texto)
        for texto in ("1/x1", "x1/x2", "x1/(x2)"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "divide por una cantidad simbólica"):
                    analizar_lineal(texto)

    def test_el_modulo_no_evalua_texto_ni_importa_algebra_externa(self):
        arbol = ast.parse(Path(__file__).resolve().parents[1].joinpath(
            "backend", "expresiones_matriciales", "lineal.py"
        ).read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                self.assertNotIn(nodo.func.id, {"eval", "exec"})
            if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                modulos = [alias.name for alias in nodo.names] if isinstance(nodo, ast.Import) else [nodo.module or ""]
                for modulo in modulos:
                    self.assertFalse(modulo.startswith(("numpy", "sympy", "scipy", "backend.ecuaciones", "backend.gauss")))


class PruebasCoeficientes(TestCase):
    def test_extraccion_y_variable_ausente(self):
        lado = vector(("3x1 - 2x2", "x1 + 4x2", "x2"))
        self.assertEqual(coef_vector(lado, "x1"), (Fraction(3), Fraction(1), Fraction(0)))
        self.assertEqual(coef_vector(lado, "x2"), (Fraction(-2), Fraction(4), Fraction(1)))
        self.assertIsInstance(coef_vector(lado, "x1")[0], Fraction)

    def test_el_orden_de_columnas_es_el_del_vector_no_el_alfabetico(self):
        matriz = MatrizDesconocida("A", 1, 2)
        vector_simbolico = VectorSimbolico("z", ("b", "a"))
        obtenida = determinar(matriz, vector_simbolico, vector(("a + 2b",)))
        self.assertEqual(obtenida.resultado, ((Fraction(2), Fraction(1)),))
        self.assertEqual(obtenida.nombres_columnas, ("a1", "a2"))


class PruebasDeterminacion(TestCase):
    def test_caso_principal_3x2(self):
        obtenida = determinar(A32, X2, vector(("3x1 - 2x2", "x1 + 4x2", "x2")), "b")
        self.assertEqual(obtenida.resultado, (
            (Fraction(3), Fraction(-2)),
            (Fraction(1), Fraction(4)),
            (Fraction(0), Fraction(1)),
        ))
        self.assertTrue(obtenida.verificada)
        self.assertEqual(obtenida.verificacion, obtenida.componentes)

    def test_matriz_2x2(self):
        obtenida = determinar(
            MatrizDesconocida("A", 2, 2), X2,
            vector(("2x1 + x2", "-x1 + 3x2")),
        )
        self.assertEqual(obtenida.resultado, ((Fraction(2), Fraction(1)), (Fraction(-1), Fraction(3))))

    def test_rectangular_2x3_respeta_el_orden_de_x(self):
        equis = VectorSimbolico("x", ("x1", "x2", "x3"))
        obtenida = determinar(
            MatrizDesconocida("A", 2, 3), equis,
            vector(("x1 + 2x3", "-x2 + 4x3")),
        )
        self.assertEqual(obtenida.resultado, (
            (Fraction(1), Fraction(0), Fraction(2)),
            (Fraction(0), Fraction(-1), Fraction(4)),
        ))
        self.assertEqual(obtenida.columnas[1], (Fraction(0), Fraction(-1)))

    def test_fracciones_variable_ausente_y_expresion_normalizable(self):
        fracciones = determinar(
            MatrizDesconocida("A", 2, 2), X2,
            vector(("(1/2)x1 - (3/4)x2", "x1 + (2/3)x2")),
        )
        self.assertEqual(fracciones.resultado[0][0], Fraction(1, 2))
        self.assertEqual(fracciones.resultado[0][1], Fraction(-3, 4))
        self.assertEqual(fracciones.resultado[1][1], Fraction(2, 3))
        ausente = determinar(MatrizDesconocida("A", 2, 2), X2, vector(("x2", "x1")))
        self.assertEqual(ausente.resultado, ((Fraction(0), Fraction(1)), (Fraction(1), Fraction(0))))
        normal = determinar(
            MatrizDesconocida("A", 2, 2), X2,
            vector(("2(x1 + x2) - x1", "x1 - x1 + 3x2")),
        )
        self.assertEqual(normal.resultado, ((Fraction(1), Fraction(2)), (Fraction(0), Fraction(3))))
        self.assertTrue(normal.verificada)

    def test_variable_ajena_constante_y_dimensiones(self):
        with self.assertRaisesRegex(ValueError, r"El lado derecho contiene x3, pero x está formado únicamente por x1 y x2"):
            determinar(MatrizDesconocida("A", 2, 2), X2, vector(("x1 + x3", "x2")), "b")
        with self.assertRaisesRegex(ValueError, "término constante independiente"):
            determinar(MatrizDesconocida("A", 2, 2), X2, vector(("x1 + 2", "x2")))
        with self.assertRaisesRegex(ValueError, r"necesita un vector de 2 componentes, pero x tiene 3"):
            determinar(MatrizDesconocida("A", 3, 2), VectorSimbolico("x", ("x1", "x2", "x3")), vector(("x1", "x2", "x3")))
        with self.assertRaisesRegex(ValueError, r"Ax tiene 3 componentes pero b tiene 4"):
            determinar(A32, X2, vector(("x1", "x2", "x1", "x2")), "b")
        self.assertIsInstance(analizar_lineal("x1"), FormaLineal)
