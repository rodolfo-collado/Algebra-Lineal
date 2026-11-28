"""Independencia de vectores, desde el modelo exacto hasta el formulario web."""

import os
from fractions import Fraction
from unittest import TestCase

import django
from django.test import Client, SimpleTestCase

from backend.independencia_lineal import analizar_independencia_lineal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
django.setup()

RUTA = "/vectores/independencia/"
VECTORES_ACEPTACION = [(1, 2, 0), (0, 1, 3), (2, 5, 3)]


def datos(vectores):
    return {
        "dimension": len(vectores[0]),
        "cantidad": len(vectores),
        **{
            f"celda_v{indice}_{fila}_0": str(valor)
            for indice, vector in enumerate(vectores, 1)
            for fila, valor in enumerate(vector)
        },
    }


class IndependenciaLinealTests(TestCase):
    def comprobar_relacion(self, vectores, testigo):
        coeficientes = testigo["coeficientes"]
        self.assertEqual(len(coeficientes), len(vectores))
        self.assertTrue(any(coeficientes))
        self.assertTrue(testigo["verificada"])
        for componentes in zip(*vectores):
            self.assertEqual(sum(a * b for a, b in zip(coeficientes, componentes)), 0)
        indice = testigo["vector_despejado"]
        self.assertEqual(coeficientes[indice - 1], 1)
        for fila, valor in enumerate(vectores[indice - 1]):
            self.assertEqual(sum(
                coef * vectores[otro - 1][fila] for otro, coef in testigo["combinacion"].items()
            ), valor)

    def test_caso_de_aceptacion(self):
        resultado = analizar_independencia_lineal(VECTORES_ACEPTACION)
        self.assertEqual(resultado["matriz"], [[1, 0, 2], [2, 1, 5], [0, 3, 3]])
        self.assertEqual(resultado["matriz_aumentada"], [[1, 0, 2, 0], [2, 1, 5, 0], [0, 3, 3, 0]])
        self.assertEqual(resultado["sistema"]["matriz_reducida"], [[1, 0, 2, 0], [0, 1, 1, 0], [0, 0, 0, 0]])
        self.assertTrue(resultado["sistema"]["pasos"])
        self.assertFalse(resultado["es_independiente"])
        self.assertEqual(resultado["rango"], 2)
        self.assertEqual(resultado["sistema"]["columnas_pivote"], [1, 2])
        self.assertEqual(resultado["sistema"]["variables_libres"], [3])
        testigo = resultado["relacion"]
        self.assertEqual(testigo["coeficientes"], [-2, -1, 1])
        self.assertEqual(testigo["combinacion"], {1: 2, 2: 1})
        self.assertEqual(testigo["verificacion"], [0, 0, 0])
        self.comprobar_relacion(VECTORES_ACEPTACION, testigo)

    def test_independientes_y_un_vector_no_nulo(self):
        for vectores in ([(0, 1, 2), (1, 0, 1)], [(Fraction(1, 3),)]):
            with self.subTest(vectores=vectores):
                resultado = analizar_independencia_lineal(vectores)
                self.assertTrue(resultado["es_independiente"])
                self.assertEqual(resultado["rango"], len(vectores))
                self.assertEqual(resultado["sistema"]["soluciones"], [0] * len(vectores))
                self.assertEqual(resultado["sistema"]["variables_libres"], [])
                self.assertIsNone(resultado["relacion"])

    def test_nulos_repetidos_y_pivote_despues_de_variable_libre(self):
        for vectores, rango, pivotes in (
            ([(0, 0)], 0, []),
            ([(0, 0), (0, 0)], 0, []),
            ([(0, 0), (1, 2)], 1, [2]),
            ([(1, 2), (1, 2)], 1, [1]),
        ):
            with self.subTest(vectores=vectores):
                resultado = analizar_independencia_lineal(vectores)
                self.assertFalse(resultado["es_independiente"])
                self.assertEqual(resultado["rango"], rango)
                self.assertEqual(resultado["sistema"]["columnas_pivote"], pivotes)
                self.comprobar_relacion(vectores, resultado["relacion"])

    def test_mas_vectores_que_dimension_y_varias_libres(self):
        vectores = [(1, 0), (0, 1), (1, 1), (7, 9)]
        resultado = analizar_independencia_lineal(vectores)
        testigo = resultado["relacion"]
        self.assertEqual(resultado["sistema"]["variables_libres"], [3, 4])
        self.assertEqual(testigo["asignacion_libres"], {3: 1, 4: 0})
        self.assertEqual(testigo["coeficientes"], [-1, -1, 1, 0])
        self.comprobar_relacion(vectores, testigo)

    def test_conserva_fracciones(self):
        vectores = [(Fraction(3, 2), 1), (Fraction(1, 2), Fraction(1, 3))]
        resultado = analizar_independencia_lineal(vectores)
        self.assertEqual(resultado["relacion"]["coeficientes"], [Fraction(-1, 3), 1])
        self.comprobar_relacion(vectores, resultado["relacion"])

    def test_limites_e_incompatibilidad(self):
        for vectores in ([(1,)] * 12, [(1,) * 12] * 9):
            with self.subTest(vectores=vectores):
                resultado = analizar_independencia_lineal(vectores)
                self.comprobar_relacion(vectores, resultado["relacion"])

        for vectores, mensaje in (
            ([], "al menos un vector"),
            ([(1,), (1, 2)], "distinta dimensión"),
            ([(1,) * 12] * 10, "120 celdas"),
            ([(1,)] * 13, "1 y 12 variables"),
        ):
            with self.subTest(vectores=vectores), self.assertRaisesRegex(ValueError, mensaje):
                analizar_independencia_lineal(vectores)


class IndependenciaWebTests(SimpleTestCase):
    def test_catalogo_y_ejemplos(self):
        self.assertContains(Client().get("/"), RUTA)
        for clave, numero_celdas in (("independiente", 6), ("dependiente", 9), ("varias-libres", 8)):
            with self.subTest(clave=clave):
                respuesta = Client().get(RUTA, {"ejemplo": clave})
                self.assertContains(respuesta, "Vectores del conjunto")
                self.assertNotContains(respuesta, 'id="resultado"')
                self.assertEqual(len(respuesta.context_data["form"].nombres_celdas), numero_celdas)

    def test_conclusion_y_procedimiento_estructurado(self):
        respuesta = Client().post(RUTA, datos(VECTORES_ACEPTACION))
        for texto in (
            "Conjunto linealmente dependiente", 'data-kind="dependiente"',
            "rango(A) = 2 &lt; 3", "-2v₁ - v₂ + v₃ = 𝟎", "v₃ = 2v₁ + v₂",
            "α₁v₁ + α₂v₂ + α₃v₃ = 𝟎", "A𝛂 = 𝟎", "𝛂 = (-2, -1, 1)",
            "α₁ + 2α₃ = 0", "α₃ es libre", "F₂ = F₂ - (2)F₁",
            "-2(1, 2, 0) - (0, 1, 3) + (2, 5, 3) = (0, 0, 0)</span> = 𝟎",
        ):
            self.assertContains(respuesta, texto)
        self.assertContains(respuesta, "<dt>Rango de A</dt><dd data-rango>2</dd>", html=True)
        self.assertContains(respuesta, "<dt>Vectores</dt><dd data-cantidad-vectores>3</dd>", html=True)
        self.assertContains(respuesta, "<dt>Variables libres</dt><dd data-cantidad-libres>1</dd>", html=True)
        self.assertLess(respuesta.content.index(b"results-title"), respuesta.content.index(b"Ver procedimiento"))
        resolucion = respuesta.context_data["resolucion"]
        self.assertEqual(resolucion["rango"], 2)
        self.assertTrue(resolucion["sistema"]["pasos"])
        self.assertTrue(resolucion["relacion"]["verificada"])

    def test_el_rango_justifica_la_independencia(self):
        respuesta = Client().post(RUTA, datos([(1, 0), (0, 1)]))
        self.assertContains(respuesta, "Conjunto linealmente independiente")
        self.assertContains(respuesta, "rango(A) = 2 = 2")
        self.assertContains(respuesta, "<dt>Variables libres</dt><dd data-cantidad-libres>0</dd>", html=True)
        self.assertNotContains(respuesta, "Relación de dependencia")

    def test_metodos_y_celdas_invalidas(self):
        self.assertEqual(Client().put(RUTA).status_code, 405)
        casos = (
            ({"celda_v2_0_0": "1/0"}, "no es un número válido"),
            ({"dimension": 3}, "Las celdas no coinciden"),
            ({"cantidad": 12, "dimension": 12}, "120 celdas"),
            ({"celda_v3_0_0": "1"}, "Las celdas no coinciden"),
        )
        for cambio, mensaje in casos:
            with self.subTest(cambio=cambio):
                respuesta = Client().post(RUTA, {**datos([(1, 0), (0, 1)]), **cambio})
                self.assertContains(respuesta, mensaje)
                self.assertNotContains(respuesta, 'id="resultado"')

    def test_aplicar_sin_javascript_conserva_entradas(self):
        respuesta = Client().post(RUTA, {**datos([(1, 0), (0, 1)]), "cantidad": 3, "ajustar": 1})
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertContains(respuesta, 'name="celda_v3_1_0"')
        self.assertEqual(respuesta.context_data["form"]["celda_v1_0_0"].value(), "1")
