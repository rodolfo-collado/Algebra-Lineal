"""Integración web de Conversión de bases (P11)."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase
from django.urls import resolve, reverse
from django.utils.html import strip_tags

from frontend.web.calculadora import catalogo
from tests.test_navegacion import Documento


def texto_plano(respuesta):
    return " ".join(strip_tags(respuesta.content.decode("utf-8")).split())


class PruebasConversionBasesWeb(SimpleTestCase):
    def setUp(self):
        self.ruta = reverse("calculadora:conversion-bases")
        self.herramienta = catalogo.herramienta_por_id("conversion-bases")

    def convertir(self, numero, origen, destino):
        return self.client.post(self.ruta, {
            "numero": numero,
            "base_origen": str(origen),
            "base_destino": str(destino),
        })

    def test_registro_central_disponible(self):
        self.assertIsNotNone(self.herramienta)
        self.assertTrue(self.herramienta.disponible)
        self.assertEqual(self.herramienta.nombre, "Conversión de bases")
        self.assertEqual(self.herramienta.categoria, catalogo.BASES_NUMERICAS)
        self.assertEqual(self.herramienta.ruta, self.ruta)
        self.assertEqual(resolve(self.ruta).view_name, "calculadora:conversion-bases")
        for clave in ("binario", "hexadecimal", "conversión", "sistemas numéricos", "bases"):
            self.assertIn(clave, self.herramienta.palabras_clave)
        self.assertEqual(
            [h.id for h in catalogo.herramientas_de(catalogo.BASES_NUMERICAS)], ["conversion-bases"],
        )

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

    def test_selectores_compactos_con_las_cuatro_bases_e_intercambio(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        documento = Documento(self.client.get(self.ruta))
        for nombre in ("base_origen", "base_destino"):
            with self.subTest(selector=nombre):
                self.assertIn(f'<select name="{nombre}" class="field-select"', html)
                for valor, etiqueta in ((2, "Binario"), (8, "Octal"), (10, "Decimal"), (16, "Hexadecimal")):
                    self.assertRegex(html, rf'<option value="{valor}"[^>]*>{etiqueta}</option>')
        # Valores iniciales: decimal → binario, como hasta ahora.
        self.assertRegex(html, r'name="base_origen"[\s\S]*?<option value="10" selected>Decimal</option>')
        self.assertRegex(html, r'name="base_destino"[\s\S]*?<option value="2" selected>Binario</option>')
        # Sin tarjetas grandes para elegir la base ni el modo.
        self.assertNotIn('name="modo"', html)
        self.assertNotIn('name="base"', html)
        self.assertNotIn('class="choice"', html)
        # El intercambio solo funciona con JavaScript, por eso nace oculto.
        intercambio = next(c for c in documento.controles if "data-intercambiar-bases" in c)
        self.assertEqual(intercambio["type"], "button")
        self.assertIn("hidden", intercambio)
        self.assertIn("Intercambiar", intercambio["aria-label"])

    def test_teclado_y_etiqueta_siguen_a_la_base_de_origen(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        for base in (2, 8, 10, 16):
            self.assertIn(f'data-teclado="base-{base}"', html)
        self.assertIn("calculadora/teclado.js", html)
        self.assertIn("calculadora/conversion.js", html)
        # Por defecto el origen es decimal: solo ese contenedor y esa etiqueta quedan visibles.
        self.assertRegex(html, r'<div class="base-keyboard" data-teclado-base="10" data-nombre-base="decimal"\s*>')
        self.assertRegex(html, r'data-teclado-base="2"[^>]*hidden')
        self.assertRegex(html, r'data-teclado-base="16"[^>]*hidden')
        self.assertRegex(html, r'<span data-number-label-base="10"\s*>Número decimal</span>')
        self.assertRegex(html, r'data-number-label-base="2"[^>]*hidden[^>]*>Número binario<')
        self.assertIn('data-insercion="A"', html)
        self.assertIn('data-insercion="F"', html)
        # Aviso de validación en vivo, vacío hasta que JavaScript lo use.
        self.assertIn('data-validacion-cliente role="alert" hidden', html)

    def test_cambio_de_origen_actualiza_teclado_y_etiqueta_sin_javascript(self):
        html = self.convertir("", 16, 2).content.decode("utf-8")
        self.assertRegex(html, r'<div class="base-keyboard" data-teclado-base="16" data-nombre-base="hexadecimal"\s*>')
        self.assertRegex(html, r'data-teclado-base="10"[^>]*hidden')
        self.assertRegex(html, r'<span data-number-label-base="16"\s*>Número hexadecimal</span>')
        self.assertRegex(html, r'data-number-label-base="10"[^>]*hidden')

    def test_el_campo_del_numero_es_de_una_linea(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        self.assertIn('class="field-input field-input-numeral"', html)
        self.assertNotIn("field-input-code", html)
        self.assertNotIn("<textarea", html)

    def test_todos_los_pares_de_bases_distintas(self):
        # 26₁₀ = 11010₂ = 32₈ = 1A₁₆
        escrituras = {2: "11010", 8: "32", 10: "26", 16: "1A"}
        subindices = {2: "₂", 8: "₈", 10: "₁₀", 16: "₁₆"}
        for origen, numero in escrituras.items():
            for destino, esperado in escrituras.items():
                if origen == destino:
                    continue
                with self.subTest(origen=origen, destino=destino):
                    respuesta = self.convertir(numero, origen, destino)
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertContains(respuesta, f"{numero}{subindices[origen]}")
                    self.assertContains(respuesta, f"{esperado}{subindices[destino]}")
                    self.assertContains(respuesta, "Procedimiento")

    def test_origen_igual_a_destino_no_se_permite(self):
        for base in (2, 8, 10, 16):
            with self.subTest(base=base):
                respuesta = self.convertir("1", base, base)
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, "La base de origen y la base de destino deben ser distintas.")
                self.assertNotContains(respuesta, 'id="resultado"')

    def test_decimal_a_binario_en_una_etapa(self):
        respuesta = self.convertir("13", 10, 2)
        self.assertContains(respuesta, "13₁₀")
        self.assertContains(respuesta, "1101₂")
        self.assertContains(respuesta, "Decimal → binario")
        self.assertContains(respuesta, "13 ÷ 2")
        self.assertContains(respuesta, "residuos se leen")
        self.assertNotContains(respuesta, "Etapa 1")
        self.assertNotContains(respuesta, "pasa por decimal")
        self.assertNotContains(respuesta, "Expansión posicional")

    def test_decimal_a_hexadecimal_sustituye_diez_por_a(self):
        respuesta = self.convertir("26", 10, 16)
        self.assertContains(respuesta, "1A₁₆")
        self.assertContains(respuesta, "10 → A")

    def test_binario_a_decimal_muestra_la_combinacion_lineal(self):
        respuesta = self.convertir("1011", 2, 10)
        self.assertContains(respuesta, "1011₂")
        self.assertContains(respuesta, "11₁₀")
        self.assertContains(respuesta, "Binario → decimal")
        self.assertContains(respuesta, "1·2")
        self.assertContains(respuesta, "<sup>3</sup>", html=False)
        self.assertContains(respuesta, "8 + 0 + 2 + 1")
        self.assertNotContains(respuesta, "Etapa 1")
        self.assertNotContains(respuesta, "Divisiones sucesivas")

    def test_hexadecimal_a_decimal_en_minusculas(self):
        respuesta = self.convertir("1a", 16, 10)
        self.assertContains(respuesta, "1A₁₆")
        self.assertContains(respuesta, "Hexadecimal → decimal")
        self.assertContains(respuesta, "A = 10")
        self.assertContains(respuesta, "26₁₀")

    def test_binario_a_hexadecimal_en_dos_etapas(self):
        respuesta = self.convertir("1010", 2, 16)
        texto = texto_plano(respuesta)
        self.assertIn("1010₂ = A₁₆", texto)
        self.assertIn("pasa por decimal", texto)
        self.assertIn("1010₂ = 10₁₀ = A₁₆", texto)
        self.assertIn("Etapa 1 · Binario → decimal", texto)
        self.assertIn("Etapa 2 · Decimal → hexadecimal", texto)
        self.assertLess(texto.index("Etapa 1"), texto.index("Etapa 2"))
        # Las dos matemáticas de siempre, en orden: expansión y después divisiones.
        self.assertLess(texto.index("Expansión posicional"), texto.index("Divisiones sucesivas"))
        self.assertIn("8 + 0 + 2 + 0", texto)
        self.assertIn("10 ÷ 16", texto)
        self.assertIn("10 → A", texto)

    def test_octal_a_binario_en_dos_etapas(self):
        texto = texto_plano(self.convertir("17", 8, 2))
        self.assertIn("17₈ = 1111₂", texto)
        self.assertIn("17₈ = 15₁₀ = 1111₂", texto)
        self.assertIn("Etapa 1 · Octal → decimal", texto)
        self.assertIn("Etapa 2 · Decimal → binario", texto)

    def test_error_digito_invalido_sin_traceback(self):
        respuesta = self.convertir("102", 2, 10)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "El dígito 2 no es válido en un número binario.")
        self.assertNotContains(respuesta, "ValueError")
        self.assertNotContains(respuesta, "Traceback")
        self.assertNotContains(respuesta, "invalid literal")
        self.assertNotContains(respuesta, 'id="resultado"')
        # El error también aplica cuando el destino no es decimal.
        self.assertContains(self.convertir("1G", 16, 8), "G no es un dígito hexadecimal válido.")

    def test_rechaza_negativos_y_vacio(self):
        self.assertContains(self.convertir("", 10, 2), "Ingresa un número.")
        self.assertContains(self.convertir("-13", 10, 2), "no negativos")
        self.assertContains(self.convertir("-11", 2, 8), "no negativos")

    def test_base_invalida_en_el_formulario(self):
        respuesta = self.client.post(self.ruta, {"numero": "1", "base_origen": "3", "base_destino": "2"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertNotContains(respuesta, "Traceback")

    def test_tema_y_recursos_locales(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        self.assertIn("algebra-lineal-tema", html)
        self.assertNotIn("cdn.", html.lower())
        self.assertNotIn("fonts.googleapis", html.lower())
        self.assertIn("calculadora/styles.css", html)
        self.assertIn("calculadora/teclado.js", html)

    def test_sistemas_sigue_disponible(self):
        self.assertEqual(self.client.get("/sistemas/").status_code, 200)
