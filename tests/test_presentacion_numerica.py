"""Exactitud de la representación y frontera común de los resultados web."""

import json
import os
from fractions import Fraction
from html.parser import HTMLParser
from unittest import TestCase
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.template import Context, Template
from django.test import SimpleTestCase
from django.utils.html import strip_tags

from backend.matrices import formatear_fraccion
from frontend.web.calculadora.presentacion_numerica import (
    PRECISIONES, formatear_exacto, representar, representar_texto,
)
from frontend.web.calculadora.servicios import resolver_sistema_web
from tests.test_ecuaciones_matriciales_web import datos_ecuacion
from tests.test_matrices_web import datos_matrices
from tests.test_multiplicacion_matrices_web import datos_matriz_vector, datos_producto
from tests.test_vectores_web import combinacion, datos_vectores


class PruebasRepresentacion(TestCase):
    def test_casos_exactos_y_periodicos(self):
        for valor, esperado, aproximado in (
            (Fraction(1, 2), "0.5", False), (Fraction(1, 4), "0.25", False),
            (Fraction(7, 2), "3.5", False), (Fraction(1, 3), "0.3333", True),
            (Fraction(-1, 3), "-0.3333", True), (Fraction(4), "4", False),
            (Fraction(0), "0", False), (Fraction(-7, 2), "-3.5", False),
            (Fraction(1, 10), "0.1", False), (Fraction(300, 1000), "0.3", False),
        ):
            with self.subTest(valor=valor):
                presentacion = representar(valor)
                self.assertEqual(presentacion.exacto, formatear_fraccion(valor))
                self.assertEqual(presentacion.decimal, esperado)
                self.assertEqual(presentacion.es_aproximado, aproximado)

    def test_precision_maxima_y_ceros_no_significativos(self):
        for p in PRECISIONES:
            self.assertEqual(representar(Fraction(1, 3), p).decimal, "0." + "3" * p)
            self.assertEqual(representar(Fraction(3, 2), p).decimal, "1.5")
        self.assertTrue(representar(Fraction(1, 8), 2).es_aproximado)
        self.assertFalse(representar(Fraction(1, 8), 4).es_aproximado)

    def test_redondeo_al_par_acarreo_y_cero_sin_signo(self):
        for n, esperado in ((125, "0.12"), (135, "0.14"), (-125, "-0.12"),
                            (-135, "-0.14"), (999, "1"), (-1, "0")):
            self.assertEqual(representar(Fraction(n, 1000), 2).decimal, esperado)
        self.assertTrue(representar(Fraction(-1, 1000), 2).es_aproximado)

    def test_enteros_grandes_no_pierden_digitos(self):
        valor = Fraction(10**80 * 2 + 1, 2)
        self.assertEqual(representar(valor).decimal, str(10**80) + ".5")
        self.assertFalse(representar(valor).es_aproximado)

    def test_error_de_redondeo_y_deteccion_en_muchos_racionales(self):
        for p in PRECISIONES:
            for n in range(-25, 26):
                for d in range(1, 18):
                    valor = Fraction(n, d)
                    vista = representar(valor, p)
                    decimal = Fraction(vista.decimal)
                    self.assertLessEqual(abs(valor - decimal), Fraction(1, 2 * 10**p))
                    self.assertEqual(vista.es_aproximado, valor != decimal)
                    self.assertEqual(formatear_exacto(valor), formatear_fraccion(valor))

    def test_rechaza_floats_y_precision_invalida(self):
        for valor in (0.1, True, "1/3"):
            with self.assertRaises(TypeError):
                representar(valor)
        for p in (0, 3, 10, "4", 4.0, True):
            with self.assertRaises(ValueError):
                representar(Fraction(1, 3), p)

    def test_expresiones_heredadas_no_evalua_ni_cambia_indices(self):
        for exacto, decimal in (
            ("x1 = 1/3 - 2/3x2", "x1 ≈ 0.3333 - 0.6667x2"),
            ("F12 = (1/3)F12", "F12 ≈ (0.3333)F12"),
            ("c₂₃ = (-1/2)·3 = -3/2", "c₂₃ = (-0.5)·3 = -1.5"),
            ("(1/3, 1/2, 4)", "(0.3333, 0.5, 4)"),
            ("x1 = 1/2+1/3", "x1 ≈ 0.5+0.3333"),
            ("(2 - 1) / 3", "(2 - 1) / 3"),
            ("x1/F2", "x1/F2"),
        ):
            with self.subTest(exacto=exacto):
                self.assertEqual(representar_texto(exacto).decimal, decimal)


class ValoresHTML(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.valores = []
        self.ocultos = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-numeric" in attrs:
            self.valores.append(json.loads(attrs["data-numeric"]))
            if "hidden" in attrs:
                self.ocultos.append(attrs)


class PruebasIntegracionNumerica(SimpleTestCase):
    def test_todas_las_familias_incluyen_ambas_representaciones(self):
        casos = [
            ("/sistemas/", {"sistema": "3x1 = 1; 2x2 = 1", "metodo": m})
            for m in ("gauss", "gauss_jordan", "comparar")
        ] + [
            ("/vectores/operaciones/", datos_vectores("suma", u=["1/3", "1/2"], v=[0, 0])),
            ("/vectores/operaciones/", datos_vectores("escalar", escalar="1/3", u=[1, 2])),
            ("/vectores/operaciones/", combinacion([[3, 0], [0, 2]], [1, 1])),
            ("/vectores/operaciones/", combinacion([[3, 0], [1, 0]], [1, 0])),
            ("/matrices/operaciones/", datos_matrices("suma", a=[["1/3"]], b=[[0]])),
            ("/matrices/operaciones/", datos_matrices("escalar", a=[[1]], escalar="1/3")),
            ("/matrices/operaciones/", datos_matrices("traspuesta", a=[["1/3", "1/2"]])),
            ("/matrices/operaciones/", datos_producto(a=[["1/3", 1]], b=[[1], [0]], metodo="comparar")),
            ("/matrices/operaciones/", datos_matriz_vector(a=[[1, 0]], x=["1/3", "1/2"], metodo="comparar")),
            ("/matrices/ecuaciones/", datos_ecuacion([[3, 0], [0, 2]], [1, 1], metodo="comparar")),
            ("/matrices/ecuaciones/", datos_ecuacion([[3, 1]], [1])),
            ("/matrices/expresiones/", {
                "expresion": "(1/3)*A", "cantidad": "1", "nombre_0": "A", "tipo_0": "matriz",
                "filas_0": "1", "columnas_0": "1", "celda_0_0_0": "1",
            }),
        ]
        for ruta, datos in casos:
            with self.subTest(ruta=ruta, datos=datos):
                respuesta = self.client.post(ruta, datos)
                self.assertEqual(respuesta.status_code, 200)
                html = respuesta.content.decode()
                valores = ValoresHTML(html)
                self.assertTrue(valores.valores)
                self.assertFalse(valores.ocultos)
                self.assertIn('data-numeric-controls hidden', html)
                self.assertEqual(html.count('id="numeric-mode"'), 1)
                self.assertIn("1/3", strip_tags(html))
                self.assertTrue(any("0.3333" in v["decimales"]["4"] for v in valores.valores))
                self.assertTrue(any("4" in v["aproximados"] for v in valores.valores))
                for valor in valores.valores:
                    self.assertEqual(set(valor["decimales"]), {"2", "4", "6", "8"})
                    self.assertIn(valor["exacto"], strip_tags(html))
                self.assertLess(html.index("panel-final"), html.index('id="procedimiento"'))

    def test_bases_entrada_y_errores_no_reciben_selector(self):
        for ruta in ("/", "/sistemas/", "/vectores/operaciones/", "/matrices/operaciones/", "/matrices/expresiones/", "/matrices/ecuaciones/", "/bases/conversion/"):
            self.assertNotContains(self.client.get(ruta), "data-numeric-controls")
        self.assertNotContains(self.client.post("/sistemas/", {"sistema": "x1+=1"}), "data-numeric-controls")
        conversion = self.client.post("/bases/conversion/", {
            "numero": "13", "base_origen": "10", "bases_destino": ["2", "16"],
        })
        self.assertContains(conversion, "1101")
        self.assertNotContains(conversion, "data-numeric-controls")

    def test_escapado_y_atributos_tecnicos_se_conservan(self):
        template = Template('{% load numeros %}{% numeric_results %}<p id="fraccion-1/3" title="Factor 1/3">{{ valor }}</p>{% endnumeric_results %}')
        html = template.render(Context({"valor": '<img src=x onerror=alert(1)> x1 = 1/3'}))
        self.assertNotIn("<img", html)
        self.assertIn('id="fraccion-1/3"', html)
        self.assertIn('title="Factor 1/3"', html)
        self.assertIn("data-numeric-attributes", html)
        self.assertIn("0.3333", html)

    def test_adaptar_resultado_existente_no_invoca_motores(self):
        resultado = resolver_sistema_web("3x1=1", "gauss_jordan")
        template = Template('{% load numeros %}{% numeric_results %}<code>{{ linea }}</code>{% endnumeric_results %}')
        with patch("backend.sistemas.resolver_sistema_gauss_jordan", side_effect=AssertionError("recalculó")):
            html = template.render(Context({"linea": resultado["solucion_general"][0]}))
        self.assertIn("x1 = 1/3", strip_tags(html))
        self.assertIn("x1 ≈ 0.3333", html)
