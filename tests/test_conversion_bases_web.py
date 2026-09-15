"""Integración web de Conversión de bases (P11)."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase
from django.urls import resolve, reverse

from frontend.web.calculadora import catalogo
from tests.test_navegacion import Documento


class PruebasConversionBasesWeb(SimpleTestCase):
    def setUp(self):
        self.ruta = reverse("calculadora:conversion-bases")
        self.herramienta = catalogo.herramienta_por_id("conversion-bases")

    def test_registro_central_disponible(self):
        self.assertIsNotNone(self.herramienta)
        self.assertTrue(self.herramienta.disponible)
        self.assertEqual(self.herramienta.nombre, "Conversión de bases")
        self.assertEqual(self.herramienta.categoria, catalogo.BASES_NUMERICAS)
        self.assertEqual(self.herramienta.ruta, self.ruta)
        self.assertEqual(resolve(self.ruta).view_name, "calculadora:conversion-bases")
        for clave in ("binario", "hexadecimal", "conversión", "sistemas numéricos", "bases"):
            self.assertIn(clave, self.herramienta.palabras_clave)

    def test_aparece_en_inicio_sidebar_y_busqueda(self):
        self.assertContains(self.client.get("/"), "Conversión de bases")
        self.assertContains(self.client.get("/"), self.ruta)

        documento = Documento(self.client.get("/"))
        hrefs = [attrs.get("href") for attrs in documento.enlaces_en("Herramientas")]
        self.assertIn(self.ruta, hrefs)

        for consulta in ("sistemas numéricos", "conversión", "binario", "hexadecimal"):
            with self.subTest(consulta=consulta):
                respuesta = self.client.get("/", {"q": consulta})
                self.assertContains(respuesta, "Conversión de bases")
                self.assertContains(respuesta, self.ruta)

    def test_get_breadcrumbs_y_sin_relacionadas(self):
        respuesta = self.client.get(self.ruta)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Sistemas numéricos")
        self.assertContains(respuesta, "Bases numéricas")
        self.assertContains(respuesta, "Conversión de bases")
        self.assertContains(respuesta, 'name="csrfmiddlewaretoken"', html=False)
        self.assertNotContains(respuesta, "Herramientas relacionadas")
        self.assertNotContains(respuesta, "Continúa con este mismo sistema")
        self.assertNotContains(respuesta, "related-list")

    def test_teclado_contextual_por_base(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        self.assertIn('data-teclado="base-2"', html)
        self.assertIn('data-teclado="base-8"', html)
        self.assertIn('data-teclado="base-10"', html)
        self.assertIn('data-teclado="base-16"', html)
        self.assertIn("calculadora/teclado.js", html)
        self.assertIn("calculadora/conversion.js", html)
        # Por defecto: desde decimal → teclado decimal visible en el contenedor activo.
        self.assertIn('data-teclado-base="10"', html)
        self.assertRegex(html, r'data-teclado-base="2"[^>]*hidden')
        self.assertIn('data-insercion="A"', html)
        self.assertIn('data-insercion="F"', html)
        self.assertIn('data-teclado="base-16"', html)
        # La etiqueta del número también sigue a la base de entrada.
        self.assertRegex(html, r'<span data-number-label-base="10"\s*>Número decimal</span>')
        self.assertRegex(html, r'data-number-label-base="2"[^>]*hidden[^>]*>Número binario<')
        self.assertRegex(html, r'data-number-label-base="16"[^>]*hidden[^>]*>Número hexadecimal<')

    def test_cambio_de_base_actualiza_teclado_y_etiqueta_sin_javascript(self):
        html = self.client.post(self.ruta, {
            "modo": "hacia_decimal",
            "base": "16",
            "numero": "",
        }).content.decode("utf-8")
        self.assertRegex(html, r'<div class="base-keyboard" data-teclado-base="16"\s*>')
        self.assertRegex(html, r'data-teclado-base="10"[^>]*hidden')
        self.assertRegex(html, r'<span data-number-label-base="16"\s*>Número hexadecimal</span>')
        self.assertRegex(html, r'data-number-label-base="10"[^>]*hidden')

    def test_el_campo_del_numero_es_de_una_linea(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        self.assertIn('class="field-input field-input-numeral"', html)
        self.assertNotIn("field-input-code", html)
        self.assertNotIn("<textarea", html)

    def test_post_decimal_a_binario(self):
        respuesta = self.client.post(self.ruta, {
            "modo": "desde_decimal",
            "base": "2",
            "numero": "13",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "1101₂")
        self.assertContains(respuesta, "13₁₀")
        self.assertContains(respuesta, "Decimal → binario")
        self.assertContains(respuesta, "Procedimiento")
        self.assertContains(respuesta, "13 ÷ 2")
        self.assertContains(respuesta, "residuos se leen")

    def test_post_decimal_a_hexadecimal(self):
        respuesta = self.client.post(self.ruta, {
            "modo": "desde_decimal",
            "base": "16",
            "numero": "26",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "1A₁₆")
        self.assertContains(respuesta, "10 → A")

    def test_post_binario_a_decimal(self):
        respuesta = self.client.post(self.ruta, {
            "modo": "hacia_decimal",
            "base": "2",
            "numero": "1011",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "1011₂")
        self.assertContains(respuesta, "11₁₀")
        self.assertContains(respuesta, "1·2")
        self.assertContains(respuesta, "<sup>3</sup>", html=False)
        self.assertContains(respuesta, "8 + 0 + 2 + 1")

    def test_post_hexadecimal_a_decimal(self):
        respuesta = self.client.post(self.ruta, {
            "modo": "hacia_decimal",
            "base": "16",
            "numero": "1a",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "1A₁₆")
        self.assertContains(respuesta, "Hexadecimal → decimal")
        self.assertContains(respuesta, "A = 10")
        self.assertContains(respuesta, "26₁₀")

    def test_error_digito_invalido_sin_traceback(self):
        respuesta = self.client.post(self.ruta, {
            "modo": "hacia_decimal",
            "base": "2",
            "numero": "102",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "El dígito 2 no es válido en un número binario.")
        self.assertNotContains(respuesta, "ValueError")
        self.assertNotContains(respuesta, "Traceback")
        self.assertNotContains(respuesta, "invalid literal")

    def test_rechaza_negativos_y_vacio(self):
        vacio = self.client.post(self.ruta, {
            "modo": "desde_decimal",
            "base": "2",
            "numero": "",
        })
        self.assertContains(vacio, "Ingresa un número.")

        negativo = self.client.post(self.ruta, {
            "modo": "desde_decimal",
            "base": "2",
            "numero": "-13",
        })
        self.assertContains(negativo, "no negativos")

    def test_tema_y_recursos_locales(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        self.assertIn("algebra-lineal-tema", html)
        self.assertNotIn("cdn.", html.lower())
        self.assertNotIn("fonts.googleapis", html.lower())
        self.assertIn("calculadora/styles.css", html)
        self.assertIn("calculadora/teclado.js", html)

    def test_sistemas_sigue_disponible(self):
        self.assertEqual(self.client.get("/sistemas/").status_code, 200)
        self.assertEqual(self.client.get("/sistemas/gauss/").status_code, 200)
