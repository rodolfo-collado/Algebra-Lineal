"""Pruebas de la interfaz web de Django."""

import os
import unittest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase

from backend.sistemas import (
    INCONSISTENTE,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
)
from tests.test_columnas_pivote import CASOS


def datos_matriz(matriz, metodo="gauss"):
    """Convierte filas de prueba en el POST que produce la cuadrícula web."""
    cantidad_ecuaciones = len(matriz)
    cantidad_variables = len(matriz[0]) - 1
    datos = {
        "tipo_entrada": "matriz",
        "metodo": metodo,
        "ecuaciones": str(cantidad_ecuaciones),
        "variables": str(cantidad_variables),
    }
    for fila, valores in enumerate(matriz):
        for columna, valor in enumerate(valores):
            datos[f"matriz_{fila}_{columna}"] = str(valor)

    return datos


class PruebasCalculadoraWeb(SimpleTestCase):
    def test_columnas_pivote_en_resultado_y_html(self):
        from django.utils.html import strip_tags
        from frontend.web.calculadora.servicios import resolver_sistema_web

        for metodo in ("gauss", "gauss_jordan"):
            for nombre, matriz, columnas, _ in CASOS:
                with self.subTest(metodo=metodo, caso=nombre):
                    respuesta = self.client.post("/sistemas/", datos_matriz(matriz, metodo))
                    self.assertEqual(respuesta.status_code, 200)
                    texto = strip_tags(respuesta.content.decode("utf-8"))
                    esperado = ", ".join(f"C{c}" for c in columnas) or "Ninguna"
                    self.assertIn(f"Columnas pivote: {esperado}", texto)
                    self.assertEqual(texto.count("Columnas pivote:"), 1)
                    # La sidebar ya nombra «Clasificación de sistemas»; el orden se mide dentro del resultado.
                    inicio_resultado = texto.index("Resultado final")
                    self.assertLess(inicio_resultado, texto.index("Columnas pivote:"))
                    self.assertLess(texto.index("Columnas pivote:"), texto.index("Clasificación", inicio_resultado))

            resultado = resolver_sistema_web("x1 + 2x2 + x3 = 4; x3 = 2", metodo)
            self.assertEqual(resultado["columnas_pivote"], [1, 3])
            respuesta = self.client.post("/sistemas/", {"metodo": metodo, "sistema": "x1 + 2x2 + x3 = 4; x3 = 2"})
            self.assertIn("Columnas pivote: C1, C3", strip_tags(respuesta.content.decode("utf-8")))

    def test_get_renderiza_el_modulo_de_sistemas(self):
        respuesta = self.client.get("/sistemas/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Álgebra Lineal")
        self.assertContains(respuesta, "Sistemas de ecuaciones")
        self.assertContains(respuesta, "Gauss-Jordan")
        self.assertContains(respuesta, 'id="theme-toggle"')
        self.assertContains(respuesta, "static/calculadora/styles.css")
        self.assertContains(respuesta, "static/calculadora/tema.js")
        self.assertContains(respuesta, "static/calculadora/matriz.js")

    def test_muestra_los_dos_tipos_de_entrada(self):
        respuesta = self.client.get("/sistemas/")

        self.assertContains(respuesta, "Sistema de ecuaciones")
        self.assertContains(respuesta, "Matriz aumentada")
        self.assertContains(respuesta, 'name="tipo_entrada"')
        self.assertContains(respuesta, 'name="metodo"')
        self.assertContains(respuesta, 'type="radio"')

    def test_el_modulo_no_carga_recursos_remotos(self):
        html = self.client.get("/sistemas/").content.decode("utf-8").lower()

        for host in (
            "fonts.googleapis.com",
            "cdn.jsdelivr.net",
            "unpkg.com",
        ):
            self.assertNotIn(host, html)

    def test_procesa_una_solucion_unica(self):
        respuesta = self.client.post(
            "/sistemas/",
            {
                "metodo": "gauss_jordan",
                "sistema": "x1+x2=3;x1-x2=1",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, SOLUCION_UNICA)
        self.assertContains(respuesta, 'data-kind="unica"')
        self.assertContains(respuesta, "x1 = 2")
        self.assertContains(respuesta, "x2 = 1")

    def test_procesa_una_matriz_con_gauss(self):
        respuesta = self.client.post(
            "/sistemas/",
            datos_matriz([[1, 1, 3], [1, -1, 1]], metodo="gauss"),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Gauss")
        self.assertContains(respuesta, SOLUCION_UNICA)
        self.assertContains(respuesta, "x1 = 2")
        self.assertContains(respuesta, "x2 = 1")

    def test_procesa_una_matriz_rectangular_con_gauss_jordan(self):
        respuesta = self.client.post(
            "/sistemas/",
            datos_matriz(
                [[1, 1, 3], [1, -1, 1], [2, 0, 4]],
                metodo="gauss_jordan",
            ),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Gauss-Jordan")
        self.assertContains(respuesta, SOLUCION_UNICA)
        self.assertContains(respuesta, "x1 = 2")
        self.assertContains(respuesta, "x2 = 1")

    def test_procesa_soluciones_infinitas(self):
        respuesta = self.client.post(
            "/sistemas/",
            {
                "metodo": "gauss_jordan",
                "sistema": "x1+x2=2;2x1+2x2=4",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, SOLUCIONES_INFINITAS)
        self.assertContains(respuesta, 'data-kind="infinitas"')
        self.assertContains(respuesta, "x2 es libre")
        self.assertContains(respuesta, "no tiene pivote")

    def test_procesa_una_matriz_rectangular_con_soluciones_infinitas(self):
        respuesta = self.client.post(
            "/sistemas/",
            datos_matriz(
                [[1, 1, 1, 6], [0, 1, 2, 5]],
                metodo="gauss_jordan",
            ),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, SOLUCIONES_INFINITAS)
        self.assertContains(respuesta, "x3 es libre")
        self.assertContains(respuesta, "x1 = 1 + x3")

    def test_procesa_un_sistema_inconsistente(self):
        respuesta = self.client.post(
            "/sistemas/",
            {
                "metodo": "gauss",
                "sistema": "x1+x2=2;2x1+2x2=5",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, INCONSISTENTE)
        self.assertContains(respuesta, 'data-kind="inconsistente"')
        self.assertContains(respuesta, "fila 2")
        self.assertContains(respuesta, "0 = 1")
        self.assertContains(respuesta, "no tiene solución")

    def test_procesa_una_matriz_inconsistente_con_contradiccion_no_final(self):
        respuesta = self.client.post(
            "/sistemas/",
            datos_matriz([[0, 0, 4], [1, 1, 2]], metodo="gauss"),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, INCONSISTENTE)
        self.assertContains(respuesta, "fila 2")
        self.assertContains(respuesta, "0 = 4")
        self.assertContains(respuesta, "no tiene solución")

    def test_matriz_con_fracciones_conserva_la_exactitud(self):
        respuesta = self.client.post(
            "/sistemas/",
            datos_matriz(
                [["1/2", 0, "1/2"], [0, "-2/3", "4/3"]],
                metodo="gauss_jordan",
            ),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "1/2")
        self.assertContains(respuesta, "x1 = 1")
        self.assertContains(respuesta, "x2 = -2")

    def test_muestra_un_error_de_entrada_sin_traceback(self):
        respuesta = self.client.post(
            "/sistemas/",
            {
                "metodo": "gauss_jordan",
                "sistema": "x1 + = 3",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Formato de sistema inválido")
        self.assertNotContains(respuesta, "Traceback")

    def test_rechaza_un_sistema_vacio(self):
        respuesta = self.client.post(
            "/sistemas/",
            {"metodo": "gauss", "sistema": "   "},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ingresa un sistema de ecuaciones.")

    def test_muestra_error_para_una_celda_vacia(self):
        datos = datos_matriz([[1, "", 3]], metodo="gauss")
        respuesta = self.client.post("/sistemas/", datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "La celda fila 1, x2 no puede estar vacía.")
        self.assertNotContains(respuesta, "Traceback")

    def test_muestra_error_para_una_celda_no_numerica(self):
        datos = datos_matriz([["hola", 1, 3]], metodo="gauss")
        respuesta = self.client.post("/sistemas/", datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "La celda fila 1, x1")
        self.assertContains(respuesta, "no es un número válido")
        self.assertNotContains(respuesta, "Traceback")

    def test_muestra_error_para_un_denominador_cero(self):
        datos = datos_matriz([["1/0", 1, 3]], metodo="gauss")
        respuesta = self.client.post("/sistemas/", datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "La celda fila 1, x1")
        self.assertContains(respuesta, "no es un número válido")
        self.assertNotContains(respuesta, "Traceback")

    def test_rechaza_dimensiones_cero(self):
        respuesta = self.client.post(
            "/sistemas/",
            {
                "tipo_entrada": "matriz",
                "metodo": "gauss",
                "ecuaciones": "0",
                "variables": "2",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Debe haber al menos una ecuación.")
        self.assertNotContains(respuesta, "Traceback")

    def test_rechaza_dimensiones_negativas(self):
        datos = datos_matriz([[1, 2, 3]], metodo="gauss")
        datos["variables"] = "-1"
        respuesta = self.client.post("/sistemas/", datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Debe haber al menos una variable.")
        self.assertNotContains(respuesta, "Traceback")

    def test_rechaza_dimensiones_no_enteras(self):
        respuesta = self.client.post(
            "/sistemas/",
            {
                "tipo_entrada": "matriz",
                "metodo": "gauss",
                "ecuaciones": "2.5",
                "variables": "2",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "debe ser un número entero")
        self.assertNotContains(respuesta, "Traceback")

    def test_rechaza_una_cantidad_de_celdas_inconsistente(self):
        respuesta = self.client.post(
            "/sistemas/",
            {
                "tipo_entrada": "matriz",
                "metodo": "gauss",
                "ecuaciones": "2",
                "variables": "2",
                "matriz_0_0": "1",
                "matriz_0_1": "1",
                "matriz_0_2": "3",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(
            respuesta,
            "La cantidad de celdas no coincide con las dimensiones indicadas.",
        )
        self.assertNotContains(respuesta, "Traceback")


if __name__ == "__main__":
    unittest.main()
