"""HTTP y presentación de regla falsa, también sin JavaScript."""

from unittest.mock import patch

from django.test import Client, SimpleTestCase
from django.urls import reverse

from backend.funciones_reales import FuncionReal
from backend.regla_falsa import regla_falsa
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms_raices import ReglaFalsaForm
from tests.test_biseccion_web import resultado_html
from tests.test_teclado import Pagina


RUTA = "/metodos-numericos/regla-falsa/"


def datos(**cambios):
    return {"funcion": "x^2-2", "a": "1", "b": "2", **cambios}


class ReglaFalsaWebTests(SimpleTestCase):
    def test_formulario_vacio_teclado_y_recursos_locales(self):
        r = self.client.get(RUTA)
        form = ReglaFalsaForm()
        for campo in ("funcion", "a", "b"):
            self.assertIsNone(form[campo].value())
        self.assertEqual(form["precision"].value(), .0001)
        self.assertEqual(form["max_iteraciones"].value(), 200)
        self.assertEqual(form["precision"].label, "Tolerancia del error absoluto")
        pagina = Pagina(r.content.decode())
        self.assertEqual(set(pagina.json["math-keyboard-profiles"]), {"funcion-real"})
        self.assertEqual(len(pagina.teclados), 1)
        for recurso in ("raices.js", "regla_falsa.js", "raices.css", "plotly-basic", "teclado.js"):
            self.assertContains(r, recurso)
        self.assertNotContains(r, "calculadora/biseccion.js")
        self.assertNotContains(r, 'id="resultado"')
        self.assertContains(r, "no con un porcentaje")

    def test_catalogo_busqueda_area_y_herramientas_hermanas(self):
        self.assertEqual(reverse("calculadora:regla-falsa"), RUTA)
        self.assertEqual(reverse("calculadora:regla-falsa-grafica"), RUTA+"grafica/")
        h = catalogo.herramienta_por_id("regla-falsa")
        self.assertTrue(h.disponible)
        for ruta in ("/", "/?q=falsa", "/areas/metodos-numericos/", catalogo.BISECCION.ruta):
            self.assertContains(self.client.get(ruta), f'href="{RUTA}"')
        self.assertContains(self.client.get(RUTA), f'href="{catalogo.BISECCION.ruta}"')
        self.assertContains(self.client.get("/areas/metodos-numericos/"), "x² − 4 en [1, 3] ⟶ xr ≈ 2")

    def test_resultado_y_tabla_coinciden_con_backend_sin_javascript(self):
        r = self.client.post(RUTA, datos())
        esperado = regla_falsa(FuncionReal("x^2-2"), 1, 2)
        self.assertEqual(resultado_html(r), esperado)
        self.assertContains(r, "data-iteracion=", count=len(esperado["iteraciones"]))
        for texto in ("xr", "recta secante", "Error absoluto Ea", "No disponible",
                      "Residuo", "Error absoluto verdadero", "punto de prueba",
                      "Su longitud acota", "no demuestra unicidad"):
            self.assertContains(r, texto)
        self.assertContains(r, 'id="resultado"', count=1)
        self.assertContains(r, "f(xr) <span data-raices-relacion>=</span>", count=1)
        self.assertNotContains(r, "data-respuesta-errores")

    def test_explicaciones_de_cada_estado_no_prometen_una_raiz_no_verificada(self):
        for cambios, estado, texto in [
            ({}, "tolerancia", "Se cumplen las dos condiciones"),
            ({"funcion": "x", "a": "0", "b": "1"}, "exacta", "El extremo da cero"),
            ({"funcion": "x", "a": "-1", "b": "1"}, "exacta", "xr da cero"),
            ({"max_iteraciones": "1"}, "limite", "Se agotó el máximo"),
            ({"precision": "1e-30"}, "maquina", "ya no produce un punto nuevo"),
            ({"funcion": "1e-200*(x^20-1)", "a": "0"}, "estancamiento", "Esto no descarta raíces"),
        ]:
            with self.subTest(estado=estado, cambios=cambios):
                r = self.client.post(RUTA, datos(**cambios))
                resultado = resultado_html(r)
                self.assertEqual(resultado["estado"], estado)
                self.assertContains(r, texto)
                self.assertContains(r, "no demuestra que el error matemático sea exactamente cero"
                                    if estado == "exacta" else "¿Qué tan cerca")
                if not resultado["convergio"]:
                    self.assertContains(r, "Aproximación sin convergencia")
                if not resultado["iteraciones"]:
                    self.assertNotContains(r, 'id="iteracion-raices"')
                self.assertNotContains(r, "la raíz está más lejos")

    def test_secante_grande_y_pequena_se_serializan_sin_inf_ni_nan(self):
        for f, a, b in [("x/2-1e200", "0", "4e200"), ("1e-300*(x-1e-10)", "0", "2e-10")]:
            r = self.client.post(RUTA, datos(funcion=f, a=a, b=b))
            self.assertEqual(resultado_html(r)["estado"], "exacta")
            self.assertNotContains(r, "Infinity")
            self.assertNotContains(r, "NaN")

    def test_errores_de_entrada_no_producen_resultado(self):
        for cambios in [{"funcion": "1/x", "a": "-1", "b": "1"}, {"funcion": "x^2+1"},
                         {"funcion": "x.__class__"}, {"precision": "0"}, {"precision": ".001"},
                         {"precision": "NaN"}, {"a": "inf"}, {"a": ["0", "1"]}, {"b": "0"},
                         {"intruso": "1"}, {"max_iteraciones": "1001"}]:
            with self.subTest(cambios=cambios):
                r = self.client.post(RUTA, datos(**cambios))
                self.assertContains(r, "data-respuesta-errores")
                self.assertNotContains(r, 'id="resultado"')
        r = self.client.post(RUTA, datos(precision="", max_iteraciones=""))
        self.assertEqual(resultado_html(r)["tolerancia"], .0001)

    def test_previsualizacion_compartida_no_ejecuta_metodos(self):
        with patch("frontend.web.calculadora.views_raices.regla_falsa", side_effect=AssertionError("No calcular")), \
             patch("frontend.web.calculadora.views_raices.biseccion", side_effect=AssertionError("No calcular")):
            for valores in [{"funcion": "x²+1"}, {"funcion": "1/x", "a": "-1", "b": "1"}]:
                r = self.client.post(RUTA+"grafica/", valores)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.json(), self.client.post(catalogo.BISECCION.ruta+"grafica/", valores).json())
                self.assertEqual(len(r.json()["x"]), 801)
                if valores["funcion"] == "1/x":
                    self.assertIn(None, r.json()["y"])
                else:
                    self.assertEqual((r.json()["x"][0], r.json()["x"][-1]), (-10, 10))
        for cambios in [{"funcion": "x.__class__"}, {"a": "inf"}, {"b": "0"}, {"intruso": "1"}]:
            self.assertEqual(self.client.post(RUTA+"grafica/", datos(**cambios)).status_code, 400)

    def test_aliases_conservan_resultado_y_clave(self):
        for visual, normal, a, b in [("sen(x)", "sin(x)", "3", "4"), ("√(x)-2", "sqrt(x)-2", "1", "9"),
                                    ("x²-2", "x^2-2", "1", "2")]:
            self.assertEqual(resultado_html(self.client.post(RUTA, datos(funcion=visual, a=a, b=b))),
                             resultado_html(self.client.post(RUTA, datos(funcion=normal, a=a, b=b))))

    def test_csrf_metodos_y_escape_del_texto(self):
        for ruta in (RUTA, RUTA+"grafica/"):
            self.assertEqual(Client(enforce_csrf_checks=True).post(ruta, datos()).status_code, 403)
            self.assertEqual(self.client.put(ruta).status_code, 405)
        self.assertEqual(self.client.get(RUTA+"grafica/").status_code, 405)
        r = self.client.post(RUTA, datos(funcion="<script>alert(1)</script>"))
        self.assertNotContains(r, "<script>alert(1)</script>")
        self.assertNotContains(r, 'id="resultado"')
