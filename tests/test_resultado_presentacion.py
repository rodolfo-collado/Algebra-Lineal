"""P27.6: contrato HTML compartido y representación completa sin JavaScript."""

from html.parser import HTMLParser

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from tests.resultado_browser import CASOS


class MatrizHTML(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.pila = []
        self.corchetes = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if "matrix-fence" in atributos.get("class", "").split():
            self.corchetes.append(any("matrix-scroll" in clases for clases in self.pila))
        if tag == "div":
            self.pila.append(atributos.get("class", "").split())

    def handle_endtag(self, tag):
        if tag == "div":
            self.pila.pop()


class PruebasResultadoPresentacion(SimpleTestCase):
    def test_siete_herramientas_publican_el_mismo_contrato_vigente(self):
        for nombre in ("reduccion", "axb", "inversa", "operaciones", "vectores", "bases", "romanos"):
            ruta, datos = CASOS[nombre]
            with self.subTest(herramienta=nombre):
                respuesta = self.client.post(ruta, datos)
                self.assertContains(respuesta, 'data-entrada-calculo')
                self.assertContains(respuesta, 'data-resultado="vigente"', count=1)
                self.assertContains(respuesta, 'calculadora/resultado.js')
                self.assertContains(respuesta, 'calculadora/presentacion.js')
                self.assertNotContains(respuesta, 'tabindex="0"')
                self.assertNotContains(respuesta, 'result-notice')

    def test_corchetes_y_ultima_columna_dentro_del_area_desplazable(self):
        for filas, columnas in ((1, 1), (8, 8), (8, 9), (2, 20)):
            with self.subTest(forma=(filas, columnas)):
                matriz = [[f"{i + j}/123456789" for j in range(columnas)] for i in range(filas)]
                html = render_to_string("calculadora/components/matriz.html", {"matriz": matriz, "etiqueta": "A"})
                self.assertEqual(MatrizHTML(html).corchetes, [True, True])
                self.assertEqual(html.count("<td "), filas * columnas)
                self.assertIn('aria-label="A, desplazamiento horizontal"', html)
                self.assertNotIn("tabindex", html)

    def test_verificacion_resumida_usa_la_comprobacion_y_no_la_casilla(self):
        ruta, datos = CASOS["inversa"]
        sin = self.client.post(ruta, {k: v for k, v in datos.items() if k != "verificar"})
        self.assertNotContains(sin, 'data-verificacion')
        for metodo in ("gauss_jordan", "directo_2x2"):
            with self.subTest(metodo=metodo):
                respuesta = self.client.post(ruta, datos | {"metodo": metodo, "funcion_adicional": "traspuesta"})
                self.assertContains(respuesta, 'data-verificacion', count=1)
                self.assertContains(respuesta, 'Verificación: A·A⁻¹ = A⁻¹·A = I ✓', count=1)
                self.assertContains(respuesta, 'Producto A por su inversa')
                self.assertContains(respuesta, 'Producto de la inversa por A')
