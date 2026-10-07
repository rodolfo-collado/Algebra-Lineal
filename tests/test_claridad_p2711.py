"""P27.11: claridad de entrada y consistencia final de resultados y notación."""

import os
import re
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django

django.setup()

from django.test import SimpleTestCase
from django.utils.html import strip_tags

from backend.parser_sistemas import convertir_a_numero
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.servicios_romanos import convertir_romanos
from frontend.web.calculadora.templatetags.numeros import incognitas
from tests.test_ecuaciones_matriciales_web import INFINITAS, datos_ecuacion
from tests.test_resolver_sistema import seccion_resultado
from tests.test_vectores_web import combinacion, datos_vectores

RAIZ = Path(__file__).resolve().parents[1]
ESTATICOS = RAIZ / "frontend/web/calculadora/static/calculadora"
HERRAMIENTAS = ("/matrices/reduccion/", "/vectores/operaciones/", "/matrices/operaciones/",
                "/matrices/ecuaciones/", "/matrices/inversa/", "/bases/conversion/", "/romanos/conversion/")


class PruebasNavegacion(SimpleTestCase):
    def test_ui07_el_area_se_escribe_desde_el_catalogo(self):
        self.assertEqual(catalogo.ALGEBRA_LINEAL.nombre, "Álgebra lineal")
        for ruta in ("/", "/matrices/reduccion/", "/?q=gauss"):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertContains(respuesta, "Álgebra lineal")
                self.assertNotContains(respuesta, "Álgebra Lineal")
        self.assertContains(self.client.get("/?q=gauss"), "Álgebra lineal · Matrices")

    def test_ui21_solo_los_temas_de_una_herramienta_nacen_abiertos(self):
        unicos = {c.id: c.herramienta_unica for c in catalogo.CATEGORIAS}
        self.assertEqual(unicos, {"vectores": True, "matrices": False, "bases-numericas": True,
                                  "numeracion-romana": True, "limites": False})
        html = self.client.get("/").content.decode("utf-8")
        for categoria in catalogo.CATEGORIAS:
            with self.subTest(categoria=categoria.id):
                etiqueta = re.search(rf'<details class="topic[^"]*" id="{categoria.id}"[^>]*>', html).group()
                self.assertEqual(" open" in etiqueta, categoria.herramienta_unica)
        # Las áreas siguen plegadas: abrir el tema evita un clic, no reordena Inicio.
        self.assertNotRegex(html, r'<details class="home-area"[^>]* open')

    def test_ui72_herramientas_sin_kicker_con_migas_y_titulo(self):
        for ruta in HERRAMIENTAS:
            with self.subTest(ruta=ruta):
                html = self.client.get(ruta).content.decode("utf-8")
                self.assertNotIn("tool-kicker", html)
                cabecera = re.search(r'<header class="tool-header">(.*?)</header>', html, re.S).group(1)
                self.assertEqual(re.findall(r'class="(tool-[a-z]+)"', cabecera), ["tool-title", "tool-lead"])
                self.assertLess(html.index('class="breadcrumbs"'), html.index('class="tool-title"'))
        self.assertNotIn(".tool-kicker", (ESTATICOS / "styles/components.css").read_text(encoding="utf-8"))

    def test_ui63_relacionadas_y_exploraciones_comparten_titulo(self):
        romanos = self.client.post("/romanos/conversion/", {"direccion": "decimal_a_romano", "numero": "12"})
        self.assertContains(romanos, '<h2 id="related-title" class="explore-title">También puedes explorar</h2>', html=True)
        self.assertNotContains(romanos, "explorar…")
        reduccion = self.client.post("/matrices/reduccion/", {"sistema": "x1 + x2 = 3; x1 - x2 = 1", "metodo": "gauss"})
        self.assertContains(reduccion, '<h2 id="explore-title" class="explore-title">También puedes explorar</h2>', html=True)


class PruebasEntrada(SimpleTestCase):
    def test_ui40_etiqueta_y_ayuda_por_direccion_tambien_sin_js(self):
        html = self.client.get("/romanos/conversion/").content.decode("utf-8")
        etiqueta = re.search(r'<label for="id_numero">(.*?)</label>', html, re.S).group(1)
        self.assertEqual(re.findall(r'data-direccion="(\w+)">([^<]+)<', etiqueta),
                         [("decimal_a_romano", "Número arábigo"), ("romano_a_decimal", "Número romano")])
        self.assertIn("Un entero del 1 al 3999, escrito con cifras.", html)
        css = (ESTATICOS / "styles/modules.css").read_text(encoding="utf-8")
        self.assertIn('#romanos-form:has([name="direccion"][value="romano_a_decimal"]:checked) [data-direccion="decimal_a_romano"]', css)

    def test_ui40_sugiere_la_otra_direccion_solo_si_convierte(self):
        for direccion, numero, mensaje in (
            ("decimal_a_romano", "XIV", "XIV parece un número romano. Cambia a Romano → arábigo."),
            ("decimal_a_romano", " xiv ", "XIV parece un número romano. Cambia a Romano → arábigo."),
            ("romano_a_decimal", "14", "14 está escrito con cifras arábigas. Cambia a Arábigo → romano."),
            ("romano_a_decimal", "014", "14 está escrito con cifras arábigas. Cambia a Arábigo → romano."),
        ):
            with self.subTest(direccion=direccion, numero=numero), self.assertRaisesMessage(ValueError, mensaje):
                convertir_romanos(direccion=direccion, numero=numero)
        # Inválido en ambas direcciones: el error original, sin adivinar.
        for direccion, numero in (("decimal_a_romano", "IIII"), ("decimal_a_romano", "abc"), ("decimal_a_romano", "0"),
                                  ("romano_a_decimal", "4000"), ("romano_a_decimal", "-5"), ("romano_a_decimal", "")):
            with self.subTest(direccion=direccion, numero=numero), self.assertRaises(ValueError) as error:
                convertir_romanos(direccion=direccion, numero=numero)
            self.assertNotIn("Cambia a", str(error.exception))

    def test_ui41_base_de_origen_antes_del_numero(self):
        html = self.client.get("/bases/conversion/").content.decode("utf-8")
        self.assertLess(html.index('name="base_origen"'), html.index('name="numero"'))
        self.assertLess(html.index('name="numero"'), html.index('name="bases_destino"'))
        # Sin JS la etiqueta sigue a la base enviada y 1A se convierte desde hexadecimal.
        respuesta = self.client.post("/bases/conversion/", {"numero": "1A", "base_origen": "16", "bases_destino": ["2"]})
        self.assertContains(respuesta, '<span data-number-label-base="16" >Número hexadecimal</span>', html=False)
        self.assertIn("11010₂", seccion_resultado(respuesta))

    def test_ui42_ayudas_numericas_nombran_decimales_con_punto(self):
        for ruta in ("/vectores/operaciones/", "/matrices/ecuaciones/", "/matrices/inversa/"):
            with self.subTest(ruta=ruta):
                self.assertContains(self.client.get(ruta), "Escribe enteros, fracciones como <code>1/2</code> o decimales con punto")
        texto = "Completa todas las celdas con enteros, fracciones o decimales con punto."
        self.assertContains(self.client.get("/matrices/reduccion/"), texto)
        self.assertIn(texto, (ESTATICOS / "matriz.js").read_text(encoding="utf-8"))

    def test_ui42_coma_decimal_sugiere_el_punto_sin_convertir(self):
        for texto, ejemplo in (("0,5", "0.5"), ("-3,14", "-3.14"), (",5", ".5"), ("+2,25", "+2.25"), ("0,500", "0.500")):
            with self.subTest(texto=texto), self.assertRaisesMessage(
                    ValueError, f"'{texto}' no es un número válido. Usa punto para los decimales, por ejemplo {ejemplo}."):
                convertir_a_numero(texto, limitar_entrada=True)
        # Separador de miles, listas o texto: el mensaje de siempre.
        for texto in ("1,000", "12,345", "1,2,3", "1, 2", "1,", "abc"):
            with self.subTest(texto=texto), self.assertRaises(ValueError) as error:
                convertir_a_numero(texto, limitar_entrada=True)
            self.assertEqual(str(error.exception), f"'{texto}' no es un número válido.")

    def test_ui42_vectores_v1_v2_y_resultado_sin_kicker_repetido(self):
        html = self.client.get("/vectores/operaciones/").content.decode("utf-8")
        self.assertEqual(re.findall(r'data-vector="(\w+)"', html), ["v1", "v2"])
        respuesta = self.client.post("/vectores/operaciones/", datos_vectores("suma", vectores=3, v1=[1], v2=[2], v3=["0.5"]))
        self.assertIn("Resultado v1 + v2 + v3 = (7/2)", seccion_resultado(respuesta))
        for respuesta in (respuesta, self.client.post("/vectores/operaciones/", combinacion([[1, 0], [0, 1]], [3, 4]))):
            resultado = respuesta.content.decode("utf-8")
            encabezado = re.search(r'<header class="results-heading">(.*?)</header>', resultado, re.S).group(1)
            self.assertNotIn("section-kicker", encabezado)

    def test_ui43_el_campo_dice_ecuaciones_y_el_selector_sistema_de_ecuaciones(self):
        html = self.client.get("/matrices/reduccion/").content.decode("utf-8")
        self.assertIn('<label for="id_sistema">Ecuaciones</label>', html)
        self.assertIn("<span>Sistema de ecuaciones</span>", html)
        css = (ESTATICOS / "styles/modules.css").read_text(encoding="utf-8")
        regla = re.search(r"\.choice-row \{(.*?)\}", css, re.S).group(1)
        self.assertIn("margin-bottom: 1rem;", regla)


class PruebasResultado(SimpleTestCase):
    def test_ui52_filtro_de_incognitas_solo_cambia_la_presentacion(self):
        for texto, esperado in (("2x1 - x2 = 3", "2x₁ - x₂ = 3"), ("x10 = 1/2x3", "x₁₀ = 1/2x₃"),
                                ("La variable x2 es libre.", "La variable x₂ es libre."),
                                ("F2 = F2 - (1)F1", "F2 = F2 - (1)F1"), ("C1, C3", "C1, C3"), ("max1", "max1")):
            with self.subTest(texto=texto):
                self.assertEqual(incognitas(texto), esperado)

    def test_ui52_axb_no_mezcla_x1_y_x_subindice(self):
        respuesta = self.client.post("/matrices/ecuaciones/", datos_ecuacion(*INFINITAS, metodo="comparar"))
        texto = seccion_resultado(respuesta)
        self.assertRegex(texto, r"x[₀-₉]")
        self.assertNotRegex(texto, r"(?<![A-Za-z])x[0-9]")
        # La entrada y sus ayudas conservan la sintaxis que se escribe.
        reduccion = self.client.post("/matrices/reduccion/", {"sistema": "x1 - 6 = -x2", "metodo": "gauss"})
        self.assertContains(reduccion, "x1 - 6 = -x2</textarea>")
        self.assertContains(reduccion, "Usa <code>x1</code>, <code>x2</code>")
        self.assertNotRegex(seccion_resultado(reduccion), r"(?<![A-Za-z])x[0-9]")

    def test_ui52_reduccion_dice_resultado_y_no_repite_el_kicker(self):
        respuesta = self.client.post("/matrices/reduccion/", {"sistema": "x1 + x2 = 3; x1 - x2 = 1", "metodo": "gauss",
                                                              "mostrar_definido": "1", "mostrar": ["clasificacion"]})
        self.assertContains(respuesta, '<h3 id="final-title" class="panel-title">Resultado</h3>', html=True)
        self.assertNotContains(respuesta, "Resultado final")
        self.assertTrue(seccion_resultado(respuesta).startswith("Gauss "))

    def test_ui53_la_leyenda_nombra_la_matriz_y_donde_esta(self):
        sistema = {"sistema": "x1 + x2 = 3; x1 - x2 = 1", "mostrar_definido": "1"}
        for metodo, mostrar, leyenda in (
            ("gauss", ["pivotes", "procedimiento"], "Los pivotes se resaltan en la matriz escalonada del procedimiento."),
            ("gauss_jordan", ["pivotes", "procedimiento"], "Los pivotes se resaltan en la matriz reducida del procedimiento."),
            ("comparar", ["pivotes", "procedimiento"],
             "Los pivotes se resaltan en la matriz escalonada y en la matriz reducida del procedimiento."),
            ("gauss_jordan", ["pivotes"], "Los pivotes se resaltan en la matriz reducida."),
        ):
            with self.subTest(metodo=metodo, mostrar=mostrar):
                texto = seccion_resultado(self.client.post("/matrices/reduccion/", {**sistema, "metodo": metodo, "mostrar": mostrar}))
                self.assertIn(leyenda, texto)
                self.assertNotIn("matriz final contienen", texto)
        axb = strip_tags(self.client.post("/matrices/ecuaciones/", datos_ecuacion(*INFINITAS, metodo="gauss")).content.decode("utf-8"))
        self.assertIn("Los pivotes se resaltan en la matriz escalonada del procedimiento.", axb)


if __name__ == "__main__":
    import unittest

    unittest.main()
