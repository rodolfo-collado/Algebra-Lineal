"""P27.6: contrato HTML compartido y representación completa sin JavaScript."""

from html.parser import HTMLParser

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from tests.resultado_browser import CASOS, caso
from tests.test_teclado import Pagina
from tests.ayudas import elemento_html


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
    def test_p28_5_botones_solo_en_matrices_finales(self):
        cantidades = {nombre: 1 for nombre in CASOS if nombre.startswith("p28-")}
        cantidades.update({"p28-igualdad": 2, "p28-comparar": 2, "p28-inversa-vector": 0,
                            "axb": 0, "vectores": 0, "bases": 0, "romanos": 0})
        for nombre, cantidad in cantidades.items():
            with self.subTest(caso=nombre):
                html = caso(nombre)[0].decode()
                botones = [e for e in Pagina(html).elementos if "data-copiar-resultado" in e]
                self.assertEqual(len(botones), cantidad)
                self.assertTrue(all(e["type"] == "button" and "hidden" in e
                                    and e["aria-label"].startswith("Copiar ") and not e["formulario"] for e in botones))
                if cantidad > 1:
                    self.assertEqual(len({e["aria-label"] for e in botones}), cantidad)
                if 'id="procedimiento"' in html:
                    procedimiento = elemento_html(html, html.index('id="procedimiento"'), "details")
                    self.assertNotIn("data-copiar-resultado", procedimiento)
                    self.assertNotIn("data-valor-exacto", procedimiento)

    def test_p28_5_valores_exactos_y_enteros_en_la_fuente_del_dom(self):
        html = caso("p28-suma")[0].decode()
        celdas = [e["data-valor-exacto"] for e in Pagina(html).elementos if "data-valor-exacto" in e]
        self.assertEqual(celdas, ["1/3", "-1", "2", "0", "4", "2"])
        self.assertIn('data-numeric="', html)
        self.assertNotIn('data-valor-exacto="0.3333"', html)

    def test_p28_5_fuente_y_etiqueta_escapadas_por_django(self):
        valor = '&<>"\''
        html = render_to_string("calculadora/components/matriz.html", {
            "matriz": [[valor]], "etiqueta": "A", "copiar": valor,
        })
        pagina = Pagina(html)
        self.assertEqual(next(e["data-valor-exacto"] for e in pagina.elementos if "data-valor-exacto" in e), valor)
        self.assertIn('&amp;&lt;&gt;&quot;&#x27;', html)

    def test_p28_5_limites_reales_y_resultado_completo(self):
        for nombre, cantidad in (("p28-operaciones-10", 100), ("inversa-10", 100),
                                 ("p28-reduccion-12", 120), ("p28-reduccion-13", 117)):
            with self.subTest(caso=nombre):
                html = caso(nombre)[0].decode()
                self.assertEqual(sum("data-valor-exacto" in e for e in Pagina(html).elementos), cantidad)

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
