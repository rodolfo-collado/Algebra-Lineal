"""Contrato HTTP, navegación y datos offline de bisección."""

import json
import os
import re
from pathlib import Path
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


def datos_raices_html(respuesta):
    texto = respuesta.content.decode("utf-8")
    return json.loads(re.search(r'<script id="datos-raices" type="application/json">(.*?)</script>', texto, re.S)[1])


def resultado_html(respuesta):
    return datos_raices_html(respuesta)["resultado"]


class BiseccionWebTests(SimpleTestCase):
    def test_aliases_visuales_comparten_resolucion_y_muestras(self):
        for visual, alias, a, b in [("sen(x)", "sin(x)", "3", "4"), ("√(x)-2", "sqrt(x)-2", "1", "9")]:
            with self.subTest(visual=visual):
                r = self.client.post(RUTA, datos(funcion=visual, a=a, b=b))
                s = self.client.post(RUTA, datos(funcion=alias, a=a, b=b))
                self.assertEqual(resultado_html(r), resultado_html(s))
                self.assertEqual(self.client.post(RUTA+"grafica/", datos(funcion=visual, a=a, b=b)).json(),
                                 self.client.post(RUTA+"grafica/", datos(funcion=alias, a=a, b=b)).json())
    def test_inicio_vacio_con_ajustes_y_teclado_contextual(self):
        from tests.test_teclado import Pagina
        r = self.client.get(RUTA)
        pagina = Pagina(r.content.decode())
        self.assertEqual(set(pagina.json["math-keyboard-profiles"]), {"funcion-real"})
        self.assertEqual(len(pagina.teclados), 1)
        self.assertContains(r, "calculadora/teclado.js")
        from frontend.web.calculadora.forms_raices import BiseccionForm
        form = BiseccionForm()
        for campo in ("funcion", "a", "b"):
            self.assertIsNone(form[campo].value())
        self.assertEqual(form["precision"].value(), .0001)
        self.assertEqual(form["max_iteraciones"].value(), 200)
        self.assertContains(r, "Introduce una función para")
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
                self.assertContains(r, "b − a:")
                self.assertContains(r, "más de una raíz")

    def test_cero_de_maquina_no_se_presenta_como_error_matematico_cero(self):
        r = self.client.post(RUTA, datos(funcion="x+10000000000000000-10000000000000000", a="1", b="2"))
        self.assertEqual(resultado_html(r)["estado"], "exacta")
        self.assertContains(r, "no demuestra que el error matemático sea exactamente cero")
        self.assertNotContains(r, "no supera 0")
        r = self.client.post(RUTA, datos(funcion="x", a="0", b="1"))
        self.assertContains(r, 'title="Valor almacenado: 1.0"')

    def test_f_de_c_lleva_un_solo_signo_de_relacion(self):
        # Sin JavaScript se ve el valor completo con «=»; raices.js lo cambia por «≈» al
        # redondear, en vez de añadir otro símbolo (antes: «f(c) = ≈ -0.00067»).
        for funcion in ("x^2-2", "x-1.5"):
            with self.subTest(funcion=funcion):
                r = self.client.post(RUTA, datos(funcion=funcion, a="1", b="2"))
                self.assertContains(r, "f(c) <span data-raices-relacion>=</span> <span data-raices-numero=", count=1)
                self.assertNotRegex(r.content.decode(), r"f\(c\)\s*=\s*≈")
        js = (Path(__file__).resolve().parents[1] / "frontend/web/calculadora/static/calculadora/raices.js").read_text(encoding="utf-8")
        self.assertIn('relacion.textContent = aproximado ? "≈" : "="', js)

    def test_iteraciones_en_singular_y_plural(self):
        for cambios, texto in [({"funcion": "x-1.5", "a": "1", "b": "2"}, "1 iteración ·"),
                               ({}, "13 iteraciones ·"),
                               ({"funcion": "x", "a": "0", "b": "1"}, "0 iteraciones ·")]:
            with self.subTest(cambios=cambios):
                r = self.client.post(RUTA, datos(**cambios))
                self.assertContains(r, texto)
                self.assertNotContains(r, "1 iteraciones")

    def test_notaciones_comparten_resultado_muestras_y_clave_de_comparacion(self):
        implicita = "x⁴ - 5x³ + 0.5x² - 11x + 10"
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
        for texto in ["plotly-basic", "biseccion.js", "raices.js", 'name="funcion"', 'name="a"', 'name="b"',
                      'id="raices-grafica"', 'id="ajustes-raices"']:
            self.assertContains(r, texto)
        self.assertNotContains(r, 'id="resultado"')

    def test_resultado_trece_filas_y_datos_json(self):
        r = self.client.post(RUTA, datos())
        self.assertContains(r, "Convergencia por longitud")
        self.assertContains(r, 'data-iteracion=', count=13)
        self.assertContains(r, 'type="range"')
        # Sin JavaScript: tabla y resultado completos; reproductor e historial esperan al script.
        for marca in ('id="raices-reproductor"', 'id="raices-historial"', 'id="raices-tabla-marco"', 'id="paso-breve"'):
            self.assertContains(r, marca, count=1)
        self.assertContains(r, '<div class="raices-recorrido" hidden>', count=1)
        self.assertContains(r, 'class="raices-historial" aria-labelledby="historial-titulo" hidden', count=1)
        self.assertContains(r, 'data-tono="exito"', count=1)
        for velocidad in ("0.5×", "1×", "2×", "4×"):
            self.assertContains(r, velocidad)
        resultado = resultado_html(r)
        self.assertEqual(len(resultado["iteraciones"]), 13)
        self.assertAlmostEqual(resultado["c"], .763970947265625)
        self.assertNotContains(r, "data-respuesta-errores")

    def test_precision_opcional_y_validacion_estricta(self):
        for cambios in [{"precision": ".001"}, {"precision": "0"}, {"a": "NaN"},
                         {"a": "2", "b": "1"},
                         {"intruso": "1"}, {"a": ["0", "1"]}, {"max_iteraciones": "1001"}]:
            with self.subTest(cambios=cambios):
                r = self.client.post(RUTA, datos(**cambios))
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, "data-respuesta-errores")
                self.assertNotContains(r, 'id="resultado"')
                self.assertEqual(datos_raices_html(r)["clasificacion"], "entrada_invalida")
                self.assertIsNone(resultado_html(r))
        r = self.client.post(RUTA, datos(precision="", max_iteraciones=""))
        self.assertTrue(resultado_html(r)["convergio"])
        r = self.client.post(RUTA, datos(precision="1e-8"))
        self.assertLess(resultado_html(r)["longitud"], 1e-8)

    def test_limite_no_presenta_convergencia(self):
        r = self.client.post(RUTA, datos(max_iteraciones="1"))
        self.assertFalse(resultado_html(r)["convergio"])
        self.assertContains(r, "No converge")

    def test_explorar_no_ejecuta_biseccion_y_corta_discontinuidades(self):
        with patch("frontend.web.calculadora.views_raices.biseccion", side_effect=AssertionError("No calcular")):
            r = self.client.post(RUTA + "grafica/", {"funcion": "1/x", "a": "-1", "b": "1"})
        self.assertEqual(r.status_code, 200)
        puntos = r.json()
        self.assertEqual(len(puntos["x"]), len(puntos["y"]))
        self.assertIn(None, puntos["y"])
        self.assertEqual(puntos["clasificacion"], "exploracion_no_concluyente")
        self.assertLessEqual(len(puntos["x"]), 801)
        for cambio in [{"funcion": "x.__class__"}, {"a": "inf"}, {"a": "1", "b": "0"}]:
            self.assertEqual(self.client.post(RUTA + "grafica/", datos(**cambio)).status_code, 400)

    def test_explorar_solo_funcion_usa_ventana_independiente(self):
        with patch("frontend.web.calculadora.views_raices.biseccion", side_effect=AssertionError("No calcular")):
            r = self.client.post(RUTA + "grafica/", {"funcion": "x^2+1"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.json()["x"][0], r.json()["x"][-1]), (-10, 10))
        self.assertEqual(len(r.json()["x"]), 801)
        self.assertEqual(r.json()["clasificacion"], "exploracion_no_concluyente")
        r = self.client.post(RUTA, {"funcion": "x^2+1"})
        self.assertNotContains(r, 'id="resultado"')
        self.assertContains(r, "data-respuesta-errores")

    def test_intervalo_no_aplicable_muestra_resultado_informativo(self):
        for texto, a, b, clasificacion in [
            ("x^2+1", "-1", "1", "sin_raices_demostrado"),
            ("x^2", "-1", "1", "no_aplicable"),
            ("x^2-1", "-2", "2", "no_aplicable"),
            ("1/(x-.3)", "0", "1", "no_aplicable"),
        ]:
            with self.subTest(texto=texto):
                r = self.client.post(RUTA, datos(funcion=texto, a=a, b=b))
                self.assertEqual(r.status_code, 200)
                self.assertEqual(resultado_html(r)["clasificacion"], clasificacion)
                self.assertNotContains(r, "data-respuesta-errores")
                self.assertContains(r, 'id="resultado"')
                self.assertNotContains(r, 'data-iteracion=')
                self.assertNotContains(r, "Aproximación sin convergencia")

    def test_exploracion_puede_detectar_indicios_sin_aplicar_un_metodo(self):
        for texto in ("x^2", "x-.001"):
            with self.subTest(texto=texto):
                r = self.client.post(RUTA + "grafica/", {"funcion": texto, "a": "-1", "b": "1"})
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.json()["clasificacion"], "indicios_numericos")

    def test_exploracion_conserva_limites_y_validacion_de_entrada(self):
        for valores in [{"funcion": "x", "intruso": "1"}, {"funcion": ["x", "x+1"]},
                        {"funcion": "x", "a": "NaN", "b": "1"},
                        {"funcion": "x", "a": "-1e308", "b": "1.7e308"},
                        {"funcion": "x" * 513}]:
            with self.subTest(valores=valores):
                self.assertEqual(self.client.post(RUTA + "grafica/", valores).status_code, 400)

    def test_csrf_metodos_y_xss(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post(RUTA, datos()).status_code, 403)
        self.assertEqual(self.client.put(RUTA).status_code, 405)
        self.assertEqual(self.client.get(RUTA + "grafica/").status_code, 405)
        r = self.client.post(RUTA, datos(funcion="<script>alert(1)</script>"))
        self.assertNotContains(r, "<script>alert(1)</script>")
        self.assertNotContains(r, 'id="resultado"')


class ConjuntosPublicoTests(SimpleTestCase):
    def test_herramientas_publicadas_en_catalogo_y_rutas(self):
        for id_, ruta in (("relaciones-conjuntos", "/conjuntos/relaciones/"),
                          ("cardinalidad-conjuntos", "/conjuntos/cardinalidad/")):
            with self.subTest(id_=id_):
                h = catalogo.herramienta_por_id(id_)
                self.assertEqual((h.estado, h.ruta), ("disponible", ruta))
                self.assertContains(self.client.get(ruta), 'id="resultado"', count=0, status_code=200)
                self.assertContains(self.client.get("/areas/conjuntos/"), f'href="{ruta}"')
        self.assertContains(self.client.get("/?q=pertenencia"), 'href="/conjuntos/relaciones/"')
        for ruta in ("/conjuntos/", "/conjuntos/venn/", "/conjuntos/intervalos/"):
            self.assertEqual(self.client.get(ruta).status_code, 404)
