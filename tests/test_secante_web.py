"""Métodos abiertos: contrato HTTP de Secante, selector de método, rutas antiguas y catálogo."""

import re

from django.test import Client, SimpleTestCase
from django.urls import reverse

from backend.funciones_reales import FuncionReal
from backend.secante import secante
from frontend.web.calculadora import catalogo
from tests.test_biseccion_web import datos_raices_html, resultado_html

RUTA = "/metodos-numericos/metodos-abiertos/secante/"
NEWTON = "/metodos-numericos/metodos-abiertos/newton-raphson/"


def datos(**cambios):
    return {"funcion": "x³-x-2", "x0": "1", "x1": "2", **cambios}


def selector(respuesta):
    html = respuesta.content.decode()
    return html[html.index('<nav class="metodos-abiertos"'):html.index("</nav>", html.index('<nav class="metodos-abiertos"'))]


class SecanteWebTests(SimpleTestCase):
    def test_entrada_selector_y_recursos(self):
        r = self.client.get(RUTA)
        for texto in ['id="id_x0"', 'id="id_x1"', 'data-perfil="funcion-real"', "metodos_abiertos.js", "secante.js",
                      "raices.js", "teclado.js", "plotly-basic", 'data-elegir-extremo="x0"', 'data-elegir-extremo="x1"',
                      "<title>Secante · Métodos abiertos · PyGebra</title>", ">Métodos abiertos</h1>"]:
            self.assertContains(r, texto)
        for ausente in ['id="id_a"', 'id="id_derivada"', 'id="resultado"', "newton_raphson.js", 'id="raices-derivada"']:
            self.assertNotContains(r, ausente)
        self.assertEqual(reverse("calculadora:secante"), RUTA)
        # Cada método envía su formulario a su propia ruta (Métodos abiertos tiene la de Newton).
        self.assertContains(r, f'action="{RUTA}#resultado"')
        self.assertContains(self.client.get(NEWTON), f'action="{NEWTON}#resultado"')
        # Un solo selector con los dos métodos; el activo lo marca aria-current.
        nav = selector(r)
        self.assertEqual(re.findall(r'href="([^"]+)"', nav), [NEWTON, RUTA])
        self.assertIn(f'href="{RUTA}" data-metodo-abierto aria-current="page"', nav)
        self.assertNotIn(f'href="{NEWTON}" data-metodo-abierto aria-current', nav)
        nav_newton = selector(self.client.get(NEWTON))
        self.assertIn(f'href="{NEWTON}" data-metodo-abierto aria-current="page"', nav_newton)
        self.assertContains(self.client.get(NEWTON), "<title>Newton-Raphson · Métodos abiertos · PyGebra</title>")

    def test_la_funcion_se_conserva_al_cambiar_de_metodo(self):
        for ruta in (RUTA, NEWTON):
            with self.subTest(ruta=ruta):
                r = self.client.get(ruta, {"funcion": "x^3-2x-5"})
                self.assertContains(r, 'value="x^3-2x-5"')
                self.assertNotContains(r, 'id="resultado"')
                self.assertNotContains(r, "data-respuesta-errores")
        # Una consulta enorme se recorta al máximo del campo; nunca calcula ni muestra errores.
        r = self.client.get(RUTA, {"funcion": "x" * 2000})
        self.assertNotContains(r, "x" * 513)

    def test_resultado_formula_y_tabla_de_la_diapositiva_23(self):
        r = self.client.post(RUTA, datos())
        esperado = secante(FuncionReal("x³-x-2"), 1, 2)
        self.assertEqual(resultado_html(r), esperado)
        self.assertEqual(datos_raices_html(r)["metodo"], "secante")
        html = r.content.decode()
        formula = html.split('class="abierto-formula"')[1].split("</div>")[0]
        for texto in ["f(x) = x³ − x − 2", "xₙ₊₁ = xₙ −</span> ", "<span>f(xₙ) · (xₙ − xₙ₋₁)</span><span>f(xₙ) − f(xₙ₋₁)</span>"]:
            self.assertIn(texto, formula)
        self.assertNotIn("f′", formula)
        tabla = html[html.index('class="procedure-table raices-tabla raices-tabla-abierta raices-tabla-secante"'):]
        tabla = tabla[:tabla.index("</table>")]
        self.assertEqual(re.findall(r'<th scope="col">(.*?)</th>', tabla),
                         ["n", "xₙ₋₁ <small>anterior</small>", "xₙ <small>actual</small>", "xₙ₊₁ <small>nueva</small>", "|xₙ₊₁ − xₙ| <small>cambio</small>", "|f(xₙ₊₁)| <small>residuo</small>"])
        self.assertEqual(re.findall(r'data-iteracion="(\d+)"', tabla), ["1", "2", "3", "4", "5", "6"])
        primera = re.findall(r'data-raices-numero="([^"]+)" data-raices-tipo="x"', tabla)[:3]
        self.assertEqual(primera, ["1.0", "2.0", repr(4 / 3)])
        for texto in ["Raíz aproximada", "Verificación", "secante", "Anterior", "Siguiente", "error verdadero",
                      "no exige cambio de signo"]:
            self.assertContains(r, texto)
        self.assertContains(r, 'data-tono="exito"', count=1)

    def test_practica_integradora_con_tolerancia_menor(self):
        r = resultado_html(self.client.post(RUTA, datos(funcion="x³-2x-5", x0="2", x1="3", precision="0.000001")))
        self.assertTrue(r["convergio"])
        self.assertEqual(r["tolerancia"], 1e-6)
        self.assertAlmostEqual(r["x"], 2.0945514815, places=9)
        self.assertContains(self.client.get(RUTA), '"precision": "0.000001"')

    def test_estados_sin_javascript(self):
        for cambios, estado, titulo, tono in [
                ({"funcion": "x^2-4", "x0": "-1", "x1": "1"}, "denominador", "Método no aplicable", "info"),
                ({"funcion": "x^2+1", "x0": "0", "x1": "1"}, "denominador", "Aproximación sin convergencia", "aviso"),
                ({"funcion": "ln(x)", "x0": "-1", "x1": "2"}, "dominio_inicial", "Método no aplicable", "info"),
                ({"funcion": "x^2-4", "x0": "3", "x1": "2"}, "exacta", "Raíz aproximada", "exito"),
                ({"max_iteraciones": "2"}, "limite", "Aproximación sin convergencia", "aviso"),
                ({"funcion": "√(x) - 0.1", "x0": "4", "x1": "9"}, "dominio", "Aproximación sin convergencia", "aviso")]:
            with self.subTest(estado=estado, cambios=cambios):
                r = self.client.post(RUTA, datos(**cambios))
                self.assertEqual(resultado_html(r)["estado"], estado)
                self.assertContains(r, titulo)
                self.assertContains(r, f'data-tono="{tono}"', count=1)
                self.assertNotContains(r, "data-respuesta-errores")
        exacta = self.client.post(RUTA, datos(funcion="x^2-4", x0="3", x1="2"))
        self.assertContains(exacta, "Sin iteraciones")
        self.assertNotContains(exacta, "data-iteracion=")

    def test_validacion_limites_y_seguridad(self):
        for cambios in [{"x1": "1"}, {"x1": "1.0"}, {"funcion": "x.__class__"}, {"x0": "NaN"}, {"x1": "inf"},
                        {"x1": ""}, {"x0": ["1", "2"]}, {"precision": "0"}, {"precision": ".001"},
                        {"max_iteraciones": "1001"}, {"a": "1"}, {"derivada": "3x^2"}]:
            with self.subTest(cambios=cambios):
                r = self.client.post(RUTA, datos(**cambios))
                self.assertContains(r, "data-respuesta-errores")
                self.assertNotContains(r, 'id="resultado"')
        self.assertContains(self.client.post(RUTA, datos(x1="1")), "x₁ debe ser distinto de x₀")
        self.assertEqual(resultado_html(self.client.post(RUTA, datos(precision="", max_iteraciones="")))["tolerancia"], .0001)
        self.assertEqual(Client(enforce_csrf_checks=True).post(RUTA, datos()).status_code, 403)
        self.assertEqual(self.client.put(RUTA).status_code, 405)
        self.assertEqual(self.client.get(RUTA + "grafica/").status_code, 405)

    def test_grafica_antes_del_calculo_sin_derivada(self):
        r = self.client.post(RUTA + "grafica/", {"funcion": "x^3-x-2"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["x"]), 801)
        self.assertNotIn("derivada", r.json())
        self.assertEqual(self.client.post(RUTA + "grafica/", {"funcion": "x^"}).status_code, 400)

    def test_los_metodos_no_mezclan_estados(self):
        newton = self.client.post(NEWTON, {"funcion": "x³-x-2", "x0": "1.5"})
        sec = self.client.post(RUTA, datos())
        self.assertEqual(datos_raices_html(newton)["metodo"], "newton_raphson")
        self.assertEqual(datos_raices_html(sec)["metodo"], "secante")
        self.assertNotIn("x1", resultado_html(newton))
        self.assertNotIn("derivada", resultado_html(sec))
        # El formulario de Newton rechaza x₁ y el de Secante exige x₁: nunca se cruzan los envíos.
        self.assertContains(self.client.post(NEWTON, {"funcion": "x³-x-2", "x0": "1.5", "x1": "2"}), "data-respuesta-errores")
        self.assertContains(self.client.post(RUTA, {"funcion": "x³-x-2", "x0": "1.5"}), "data-respuesta-errores")


class MetodosAbiertosNavegacionTests(SimpleTestCase):
    def test_rutas_antiguas_de_newton_redirigen(self):
        r = self.client.get("/metodos-numericos/newton-raphson/", {"funcion": "x^2-2"})
        self.assertEqual((r.status_code, r["Location"]), (301, NEWTON + "?funcion=x%5E2-2"))
        self.assertEqual(self.client.get("/metodos-numericos/newton-raphson/")["Location"], NEWTON)
        post = self.client.post("/metodos-numericos/newton-raphson/", {"funcion": "x^2-2", "x0": "1.5"})
        self.assertEqual((post.status_code, post["Location"]), (308, NEWTON))
        grafica = self.client.post("/metodos-numericos/newton-raphson/grafica/", {"funcion": "x"})
        self.assertEqual((grafica.status_code, grafica["Location"]), (308, NEWTON + "grafica/"))
        # Siguiendo la redirección, el POST histórico se resuelve igual que en la ruta nueva.
        seguido = self.client.post("/metodos-numericos/newton-raphson/", {"funcion": "x^2-2", "x0": "1.5"}, follow=True)
        self.assertEqual(resultado_html(seguido)["estado"], "tolerancia")

    def test_una_sola_herramienta_en_el_catalogo_y_la_navegacion(self):
        ids = [h.id for h in catalogo.herramientas_de(catalogo.RAICES)]
        self.assertEqual(ids, ["biseccion", "regla-falsa", "metodos-abiertos"])
        self.assertIsNone(catalogo.herramienta_por_id("newton-raphson"))
        for ruta in ("/", "/areas/metodos-numericos/", RUTA, NEWTON, catalogo.BISECCION.ruta):
            with self.subTest(ruta=ruta):
                html = self.client.get(ruta).content.decode()
                self.assertNotIn("Método de Newton-Raphson<", html)
                self.assertIn(f'href="{NEWTON}"', html)
        # La barra lateral marca Métodos abiertos tanto en Newton como en Secante.
        for ruta in (RUTA, NEWTON):
            self.assertContains(self.client.get(ruta), f'href="{NEWTON}" aria-current="page">Métodos abiertos<')
        relacionadas = catalogo.relacionadas_disponibles(catalogo.REGLA_FALSA)
        self.assertIn(catalogo.METODOS_ABIERTOS, relacionadas)

    def test_buscador_encuentra_los_dos_metodos(self):
        for consulta in ("secante", "método de la secante", "newton", "raphson", "tangente", "métodos abiertos"):
            with self.subTest(consulta=consulta):
                self.assertIn(catalogo.METODOS_ABIERTOS, catalogo.buscar_herramientas(consulta))
        self.assertEqual(catalogo.buscar_herramientas("método de la secante")[0], catalogo.METODOS_ABIERTOS)
