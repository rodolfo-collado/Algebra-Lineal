"""Contrato HTTP, navegación y datos offline de bisección."""

import json
import os
import re
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import Client, SimpleTestCase
from django.urls import reverse
from frontend.web.calculadora import catalogo
from tests.test_biseccion import POLINOMIO


RUTA = "/metodos-numericos/biseccion/"


def datos(**cambios):
    return {"funcion": POLINOMIO, "a": "0.55", "b": "1.1", **cambios}


def resultado_html(respuesta):
    texto = respuesta.content.decode("utf-8")
    return json.loads(re.search(r'<script id="datos-biseccion" type="application/json">(.*?)</script>', texto, re.S)[1])["resultado"]


class BiseccionWebTests(SimpleTestCase):
    def test_inicio_vacio_con_ajustes_y_teclado_contextual(self):
        from tests.test_teclado import Pagina
        r = self.client.get(RUTA)
        pagina = Pagina(r.content.decode())
        self.assertEqual(set(pagina.json["math-keyboard-profiles"]), {"funcion-real"})
        self.assertEqual(len(pagina.teclados), 1)
        self.assertContains(r, "calculadora/teclado.js")
        from frontend.web.calculadora.forms_biseccion import BiseccionForm
        form = BiseccionForm()
        for campo in ("funcion", "a", "b"):
            self.assertIsNone(form[campo].value())
        self.assertEqual(form["precision"].value(), .0001)
        self.assertEqual(form["max_iteraciones"].value(), 200)
        self.assertContains(r, "Introduce una función y un intervalo")
        self.assertNotContains(r, "data-respuesta-errores")

    def test_verificacion_adaptada_al_resultado(self):
        for cambios, mensaje in [({}, "Se alcanzó la precisión"),
                                 ({"funcion": "x", "a": "0", "b": "1"}, "Un extremo ya da cero"),
                                 ({"funcion": "x", "a": "-1", "b": "1"}, "El punto medio da cero"),
                                 ({"max_iteraciones": "1"}, "Se agotó el máximo"),
                                 ({"funcion": "x^2-2", "a": "1", "b": "2", "precision": "1e-30"}, "La máquina ya no puede")]:
            with self.subTest(cambios=cambios):
                r = self.client.post(RUTA, datos(**cambios))
                self.assertContains(r, mensaje)
                self.assertContains(r, "¿Cómo sabemos que hay una raíz?")
                self.assertContains(r, "¿Se alcanzó la precisión solicitada?")
                self.assertContains(r, "b − a =")
                self.assertContains(r, "más de una raíz")

    def test_cero_de_maquina_no_se_presenta_como_error_matematico_cero(self):
        r = self.client.post(RUTA, datos(funcion="x+10000000000000000-10000000000000000", a="1", b="2"))
        self.assertEqual(resultado_html(r)["estado"], "exacta")
        self.assertContains(r, "no demuestra que el error matemático sea exactamente cero")
        self.assertNotContains(r, "no supera 0")
        r = self.client.post(RUTA, datos(funcion="x", a="0", b="1"))
        self.assertContains(r, "f(b) = 1 (positivo)")

    def test_notaciones_comparten_resultado_muestras_y_clave_de_comparacion(self):
        implicita = POLINOMIO.replace("*", "")
        r = self.client.post(RUTA, datos(funcion=implicita))
        s = self.client.post(RUTA, datos())
        self.assertEqual(resultado_html(r), resultado_html(s))
        self.assertContains(r, implicita)
        a = self.client.post(RUTA + "grafica/", datos(funcion=implicita))
        b = self.client.post(RUTA + "grafica/", datos())
        self.assertEqual(a.status_code, 200)
        self.assertEqual(a.json(), b.json())

    def test_catalogo_navegacion_y_assets_locales(self):
        self.assertEqual(reverse("calculadora:biseccion"), RUTA)
        self.assertTrue(catalogo.herramienta_por_id("biseccion").disponible)
        for ruta in ["/", "/?q=biseccion", RUTA]:
            self.assertContains(self.client.get(ruta), RUTA)
        r = self.client.get(RUTA)
        for texto in ["plotly-basic", "biseccion.js", 'name="funcion"', 'name="a"', 'name="b"',
                      'id="biseccion-grafica"', 'id="ajustes-biseccion"']:
            self.assertContains(r, texto)
        self.assertNotContains(r, 'id="resultado"')

    def test_resultado_trece_filas_y_datos_json(self):
        r = self.client.post(RUTA, datos())
        self.assertContains(r, "Convergencia por longitud")
        self.assertContains(r, 'data-iteracion=', count=13)
        self.assertContains(r, 'type="range"')
        self.assertContains(r, 'id="comparacion-biseccion"')
        resultado = resultado_html(r)
        self.assertEqual(len(resultado["iteraciones"]), 13)
        self.assertAlmostEqual(resultado["c"], .763970947265625)
        self.assertNotContains(r, "data-respuesta-errores")

    def test_precision_opcional_y_validacion_estricta(self):
        for cambios in [{"precision": ".001"}, {"precision": "0"}, {"a": "NaN"},
                         {"a": "2", "b": "1"}, {"funcion": "1/(x-.3)", "a": "0", "b": "1"},
                         {"intruso": "1"}, {"a": ["0", "1"]}, {"max_iteraciones": "1001"}]:
            with self.subTest(cambios=cambios):
                r = self.client.post(RUTA, datos(**cambios))
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, "data-respuesta-errores")
                self.assertNotContains(r, 'id="resultado"')
        r = self.client.post(RUTA, datos(precision="", max_iteraciones=""))
        self.assertTrue(resultado_html(r)["convergio"])
        r = self.client.post(RUTA, datos(precision="1e-8"))
        self.assertLess(resultado_html(r)["longitud"], 1e-8)

    def test_limite_no_presenta_convergencia(self):
        r = self.client.post(RUTA, datos(max_iteraciones="1"))
        self.assertFalse(resultado_html(r)["convergio"])
        self.assertContains(r, "No converge")

    def test_explorar_no_ejecuta_biseccion_y_corta_discontinuidades(self):
        with patch("frontend.web.calculadora.views_biseccion.biseccion", side_effect=AssertionError("No calcular")):
            r = self.client.post(RUTA + "grafica/", {"funcion": "1/x", "a": "-1", "b": "1"})
        self.assertEqual(r.status_code, 200)
        puntos = r.json()
        self.assertEqual(len(puntos["x"]), len(puntos["y"]))
        self.assertIn(None, puntos["y"])
        self.assertLessEqual(len(puntos["x"]), 801)
        for cambio in [{"funcion": "x.__class__"}, {"a": "inf"}, {"a": "1", "b": "0"}]:
            self.assertEqual(self.client.post(RUTA + "grafica/", datos(**cambio)).status_code, 400)

    def test_csrf_metodos_y_xss(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post(RUTA, datos()).status_code, 403)
        self.assertEqual(self.client.put(RUTA).status_code, 405)
        self.assertEqual(self.client.get(RUTA + "grafica/").status_code, 405)
        r = self.client.post(RUTA, datos(funcion="<script>alert(1)</script>"))
        self.assertNotContains(r, "<script>alert(1)</script>")
        self.assertNotContains(r, 'id="resultado"')


class ConjuntosPublicoTests(SimpleTestCase):
    def test_bloqueado_en_get_post_y_catalogo(self):
        h = catalogo.herramienta_por_id("relaciones-conjuntos")
        self.assertEqual(h.estado, "proximamente")
        self.assertIsNone(h.ruta)
        for ruta in ["/conjuntos/relaciones/", "/conjuntos/", "/conjuntos/relaciones/?q=1"]:
            self.assertEqual(self.client.get(ruta).status_code, 404)
            self.assertEqual(self.client.post(ruta, {}).status_code, 404)
        for ruta in ["/", "/?q=pertenencia"]:
            r = self.client.get(ruta)
            self.assertNotContains(r, 'href="/conjuntos/relaciones/"')
            self.assertContains(r, "Próximamente")
