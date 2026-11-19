"""Métodos cerrados: Bisección y Regla falsa en una sola herramienta, con resultados primero.

Cubre el selector, la conservación de función, intervalo y ajustes al cambiar de método
(sin arrastrar el resultado), las rutas antiguas y la presentación del error absoluto
aproximado de bisección |cᵢ − cᵢ₋₁|, distinto de la longitud, del residuo y del criterio.
"""

import json
import os
import re
from html import unescape
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase
from django.utils.html import strip_tags

from backend.biseccion import biseccion
from backend.funciones_reales import FuncionReal
from frontend.web.calculadora import catalogo

BISECCION = "/metodos-numericos/metodos-cerrados/biseccion/"
REGLA_FALSA = "/metodos-numericos/metodos-cerrados/regla-falsa/"
STATIC = Path(__file__).resolve().parents[1] / "frontend" / "web" / "calculadora" / "static" / "calculadora"


def datos(**cambios):
    return {"funcion": "x^3-x-2", "a": "1", "b": "2", **cambios}


def resultado(respuesta):
    texto = respuesta.content.decode("utf-8")
    return json.loads(re.search(r'<script id="datos-raices" type="application/json">(.*?)</script>', texto, re.S)[1])


def texto(respuesta):
    html = re.sub(r">\s*<", "> <", respuesta.content.decode("utf-8"))
    return " ".join(unescape(strip_tags(html[html.index("<main"):html.index("</main>")])).split())


class PruebasHerramientaUnica(SimpleTestCase):
    def test_una_entrada_de_navegacion_para_los_dos_metodos(self):
        raices = catalogo.herramientas_de(catalogo.RAICES)
        self.assertEqual([h.nombre for h in raices], ["Métodos cerrados", "Métodos abiertos"])
        self.assertIsNone(catalogo.herramienta_por_id("biseccion"))
        self.assertIsNone(catalogo.herramienta_por_id("regla-falsa"))
        for consulta in ("bisección", "regla falsa", "punto medio", "métodos cerrados"):
            with self.subTest(consulta=consulta):
                self.assertEqual(catalogo.buscar_herramientas(consulta)[0], catalogo.METODOS_CERRADOS)
        for ruta in (BISECCION, REGLA_FALSA):
            with self.subTest(ruta=ruta):
                html = self.client.get(ruta).content.decode("utf-8")
                sidebar = html[html.index('<aside id="navegacion-principal"'):html.index("</aside>")]
                self.assertEqual(sidebar.count(">Métodos cerrados</a>"), 1)
                self.assertNotIn("Método de bisección", sidebar)
                self.assertNotIn("Método de regla falsa", sidebar)

    def test_selector_marca_el_metodo_actual_y_conserva_los_datos(self):
        for ruta, actual in ((BISECCION, "Bisección"), (REGLA_FALSA, "Regla falsa")):
            with self.subTest(ruta=ruta):
                html = self.client.get(ruta).content.decode("utf-8")
                selector = html[html.index('aria-label="Método cerrado"'):html.index("</nav>", html.index('aria-label="Método cerrado"'))]
                self.assertEqual(selector.count('aria-current="page"'), 1)
                self.assertRegex(selector, rf'aria-current="page">{actual} <small>')
                self.assertEqual(selector.count('data-conservar="funcion a b precision max_iteraciones"'), 2)
        script = (STATIC / "raices.js").read_text(encoding="utf-8")
        self.assertIn('document.querySelectorAll("[data-conservar]")', script)

    def test_cambiar_de_metodo_conserva_entrada_y_no_el_resultado(self):
        consulta = {"funcion": "x^2-2", "a": "1", "b": "2", "precision": "0.00001", "max_iteraciones": "50"}
        for ruta in (BISECCION, REGLA_FALSA):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta, consulta)
                html = respuesta.content.decode("utf-8")
                for nombre, valor in consulta.items():
                    self.assertRegex(html, rf'name="{nombre}" value="{re.escape(valor)}"')
                # Llegar con datos no calcula ni muestra resultados de otro método.
                self.assertNotIn('id="resultado"', html)
                self.assertIsNone(resultado(respuesta)["resultado"])

    def test_cada_metodo_envia_a_su_ruta_y_calcula_lo_suyo(self):
        bis = self.client.post(BISECCION, datos())
        rf = self.client.post(REGLA_FALSA, datos())
        self.assertContains(bis, f'action="{BISECCION}#resultado"')
        self.assertContains(rf, f'action="{REGLA_FALSA}#resultado"')
        self.assertEqual(resultado(bis)["metodo"], "biseccion")
        self.assertEqual(resultado(rf)["metodo"], "regla_falsa")
        self.assertIn("c", resultado(bis)["resultado"])
        self.assertIn("xr", resultado(rf)["resultado"])
        # Historiales separados por método: nunca se mezclan ejecuciones de ambos.
        self.assertIn("pygebra-raices-historial-${datos.metodo}", (STATIC / "raices.js").read_text(encoding="utf-8"))

    def test_rutas_antiguas_redirigen_sin_perder_el_envio(self):
        for antigua, nueva in (("/metodos-numericos/biseccion/", BISECCION),
                               ("/metodos-numericos/regla-falsa/", REGLA_FALSA),
                               ("/metodos-numericos/biseccion/grafica/", BISECCION + "grafica/"),
                               ("/metodos-numericos/regla-falsa/grafica/", REGLA_FALSA + "grafica/")):
            with self.subTest(antigua=antigua):
                get = self.client.get(antigua, {"funcion": "x"})
                self.assertEqual((get.status_code, get["Location"]), (301, f"{nueva}?funcion=x"))
                post = self.client.post(antigua, datos())
                self.assertEqual((post.status_code, post["Location"]), (308, nueva))
                self.assertEqual(self.client.post(antigua, datos(), follow=True).status_code, 200)


class PruebasResultadoPrimero(SimpleTestCase):
    def test_biseccion_resume_las_cuatro_medidas_con_su_nombre(self):
        r = self.client.post(BISECCION, datos())
        esperado = biseccion(FuncionReal("x^3-x-2"), 1, 2)
        lectura = texto(r)
        self.assertIn("Raíz aproximada", lectura)
        self.assertIn("Iteraciones 14", lectura)
        self.assertIn("Error absoluto aproximado |cᵢ − cᵢ₋₁|", lectura)
        self.assertIn("Residuo |f(c)|", lectura)
        self.assertIn("Criterio de parada b − a < precisión", lectura)
        self.assertIn("· cumplido", lectura)
        self.assertIn("|c − raíz| ≤", lectura)
        self.assertNotIn("%", lectura[:lectura.index("Gráfica de la función")])
        # El resumen va antes de la gráfica; la explicación extensa, en un solo desplegable.
        html = r.content.decode("utf-8")
        self.assertLess(html.index('class="raices-ficha"'), html.index('id="raices-grafica"'))
        self.assertEqual(html.count("disclosure-procedure"), 1)
        self.assertIn("Ver desarrollo completo", html)
        self.assertNotIn('id="verificacion-raices" class="disclosure', html)
        self.assertEqual(resultado(r)["resultado"]["error_absoluto"], esperado["error_absoluto"])

    def test_tabla_de_biseccion_usa_error_absoluto_y_primera_fila_no_aplica(self):
        r = self.client.post(BISECCION, datos())
        html = r.content.decode("utf-8")
        tabla = html[html.index('class="procedure-table raices-tabla"'):html.index("</table>", html.index('class="procedure-table raices-tabla"'))]
        self.assertIn("|cᵢ − cᵢ₋₁| <small>error absoluto</small>", tabla)
        self.assertNotIn("Error relativo", tabla)
        self.assertNotIn(" %", strip_tags(tabla))
        filas = re.findall(r"<tr data-iteracion=\"(\d+)\".*?</tr>", tabla, re.S)
        self.assertEqual(len(filas), 14)
        primera = re.search(r'<tr data-iteracion="1".*?</tr>', tabla, re.S)[0]
        self.assertTrue(strip_tags(primera).strip().endswith("No aplica"))
        segunda = re.search(r'<tr data-iteracion="2".*?</tr>', tabla, re.S)[0]
        self.assertIn('data-raices-numero="0.25"', segunda)

    def test_valores_cercanos_a_la_tolerancia_no_se_redondean_a_cero(self):
        # El valor completo viaja con cada número; raices.js nunca muestra 0 para un valor distinto de cero.
        r = self.client.post(BISECCION, datos(precision="0.00001"))
        error = resultado(r)["resultado"]["error_absoluto"]
        self.assertLess(error, 0.00001)
        self.assertContains(r, f'data-raices-numero="{error!r}"')
        self.assertIn("Protección 1: un valor distinto de cero nunca se lee como 0", (STATIC / "raices.js").read_text(encoding="utf-8"))

    def test_sin_convergencia_y_sin_raices_no_se_confunden(self):
        limite = texto(self.client.post(BISECCION, datos(max_iteraciones="3")))
        self.assertIn("no cumplido: se agotaron las iteraciones", limite)
        self.assertIn("Sin garantía", limite)
        self.assertIn("No se demostró que falte una raíz", limite)
        demostrado = texto(self.client.post(BISECCION, datos(funcion="x^2+1", a="-1", b="1")))
        self.assertIn("Ausencia de raíces demostrada", demostrado)
        abierto = texto(self.client.post(BISECCION, datos(funcion="sen(x)", a="1", b="7")))
        self.assertIn("Método no aplicable", abierto)
        self.assertIn("deja abierta la existencia de raíces", abierto)

    def test_regla_falsa_conserva_su_criterio_y_su_cota(self):
        r = self.client.post(REGLA_FALSA, datos(funcion="x^2-2"))
        lectura = texto(r)
        self.assertIn("Ea ≤ tolerancia y cambio de signo", lectura)
        self.assertIn("cumplido, con la raíz confirmada por un cambio de signo", lectura)
        self.assertIn("|xr − raíz| ≤", lectura)
        self.assertEqual(resultado(r)["resultado"]["estado"], "tolerancia")

    def test_dominio_invalido_no_calcula(self):
        r = self.client.post(BISECCION, datos(funcion="ln(x)", a="-1", b="2"))
        self.assertIn("Método no aplicable", texto(r))
        self.assertNotIn("Ver desarrollo completo", r.content.decode("utf-8"))
