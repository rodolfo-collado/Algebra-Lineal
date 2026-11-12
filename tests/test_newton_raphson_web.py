"""Contrato HTTP, navegación, teclado y presentación sin JavaScript."""
import re
from tests.test_biseccion_web import resultado_html
from django.test import Client, SimpleTestCase
from django.urls import reverse
from backend.funciones_reales import FuncionReal
from backend.newton_raphson import newton_raphson
from frontend.web.calculadora import catalogo

RUTA = "/metodos-numericos/metodos-abiertos/newton-raphson/"
def datos(**cambios):
    return {"funcion":"x²-2", "x0":"1.5", **cambios}

class NewtonWebTests(SimpleTestCase):
    def test_entrada_y_catalogo(self):
        r=self.client.get(RUTA)
        for texto in ['id="id_x0"', 'data-perfil="funcion-real"',
                      "newton_raphson.js", "raices.js", "teclado.js", "plotly-basic"]:
            self.assertContains(r,texto)
        self.assertNotContains(r, 'id="id_derivada"')
        self.assertNotContains(r, 'id="id_a"')
        self.assertNotContains(r,'id="resultado"')
        self.assertEqual(reverse("calculadora:newton-raphson"), RUTA)
        self.assertTrue(catalogo.METODOS_ABIERTOS.disponible)
        self.assertEqual(catalogo.METODOS_ABIERTOS.ruta, RUTA)
        for ruta in ["/", "/?q=newton", "/areas/metodos-numericos/", catalogo.BISECCION.ruta, catalogo.REGLA_FALSA.ruta]:
            self.assertContains(self.client.get(ruta), f'href="{RUTA}"')

    def test_resultado_geometria_y_tabla(self):
        r=self.client.post(RUTA,datos())
        esperado=newton_raphson(FuncionReal("x²-2"), 1.5)
        self.assertEqual(resultado_html(r), esperado)
        self.assertContains(r, 'f′(x) = <span class="raices-expresion">2x</span>', count=1)
        # Diapositivas 12 y 14: función, derivada y fórmula fijas sobre la sustitución del paso.
        formula = r.content.decode().split('class="abierto-formula"')[1].split("</div>")[0]
        for texto in ["f(x) = x² − 2", "f′(x) = 2x", "xₙ₊₁ = xₙ − ", "<span>f(xₙ)</span><span>f′(xₙ)</span>"]:
            self.assertIn(texto, formula)
        # n = 0 es el punto inicial; después, una fila por cada xₙ calculada.
        self.assertContains(r,"data-iteracion=", count=len(esperado["iteraciones"]) + 1)
        for texto in ["tangente", "Verificación", "Residuo", "Cambio absoluto", "Anterior", "Siguiente", "error verdadero"]:
            self.assertContains(r,texto)

    def test_estados_sin_javascript(self):
        for cambios, estado in [({"x0":"0"},"derivada"),
                ({"funcion":"x^3-2x+2", "x0":"0"}, "oscilacion"),
                ({"funcion":"x^2", "x0":"0"}, "exacta"),
                ({"max_iteraciones":"1"}, "limite"),
                ({"funcion":"ln(x)","x0":"4"}, "dominio")]:
            with self.subTest(estado=estado):
                r=self.client.post(RUTA,datos(**cambios))
                self.assertEqual(resultado_html(r)["estado"],estado)
                if estado == "derivada":
                    self.assertContains(r, "Método no aplicable")
                elif estado != "exacta":
                    self.assertContains(r, "Aproximación sin convergencia")

    def test_validacion_limites_y_seguridad(self):
        for cambios in [{"derivada":"x.__class__"}, {"funcion":"x.__class__"},
                {"x0":"NaN"}, {"x0":"inf"}, {"x0":["1","2"]}, {"precision":"0"},
                {"precision":".001"}, {"precision":"NaN"}, {"max_iteraciones":"1001"}, {"a":"1"}]:
            with self.subTest(cambios=cambios):
                r=self.client.post(RUTA,datos(**cambios))
                self.assertContains(r,"data-respuesta-errores")
                self.assertNotContains(r,'id="resultado"')
        self.assertEqual(resultado_html(self.client.post(RUTA,datos(precision="",max_iteraciones="")))["tolerancia"],.0001)
        self.assertEqual(Client(enforce_csrf_checks=True).post(RUTA,datos()).status_code,403)
        self.assertEqual(self.client.put(RUTA).status_code,405)
        self.assertEqual(self.client.get(RUTA+"grafica/").status_code,405)

    def test_dominio_inicial_es_resultado_informativo(self):
        respuesta = self.client.post(RUTA, datos(funcion="ln(2x) + x² - sen(x)", x0="-1"))
        resultado = resultado_html(respuesta)
        self.assertEqual(resultado["clasificacion"], "no_aplicable")
        self.assertEqual(resultado["estado"], "dominio_inicial")
        self.assertIsNone(resultado["x"])
        self.assertContains(respuesta, "Método no aplicable")
        self.assertNotContains(respuesta, "data-respuesta-errores")

    def test_grafica_antes_del_calculo(self):
        r=self.client.post(RUTA+"grafica/", {"funcion":"ln(x)"})
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.json()["x"]),801)
        self.assertIn(None,r.json()["y"])

    def test_derivada_reactiva_llega_con_las_muestras(self):
        r = self.client.post(RUTA + "grafica/", {"funcion": "x^3-x-2"})
        self.assertEqual(r.json()["derivada"], "3x² − 1")
        self.assertEqual(len(r.json()["x"]), 801)
        # Una entrada incompleta no deriva ni calcula: error de validación de la función.
        incompleta = self.client.post(RUTA + "grafica/", {"funcion": "x^"})
        self.assertEqual(incompleta.status_code, 400)
        self.assertNotIn("derivada", incompleta.json())
        for ruta in (catalogo.BISECCION.ruta, catalogo.REGLA_FALSA.ruta):
            self.assertNotIn("derivada", self.client.post(ruta + "grafica/", {"funcion": "x^2"}).json())
        self.assertEqual(self.client.get(RUTA + "grafica/").status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(RUTA + "grafica/", {"funcion": "x"}).status_code, 403)

    def test_notacion_natural_solo_cambia_la_presentacion(self):
        from backend.derivacion_real import DerivadaReal, natural
        # Coeficientes pegados, superíndices, − tipográfico y nombres de clase; nunca 3 · x².
        for texto, funcion, derivada in [
                ("x^3-x-2", "x³ − x − 2", "3x² − 1"), ("x³-2x+2", "x³ − 2x + 2", "3x² − 2"),
                ("x^-2", "x⁻²", "−2x⁻³"), ("x^2.5", "x^2.5", "2.5x^1.5"), ("(x+1)^12", "(x + 1)¹²", "12(x + 1)¹¹"),
                ("cos(3x)", "cos(3x)", "−3sen(3x)"), ("x*sen(x)", "x · sen(x)", "sen(x) + x · cos(x)"),
                ("√(x)+abs(x)", "√x + |x|", "1/(2√x) + x/|x|"), ("log10(x)", "log₁₀(x)", "1/(x · ln(10))"),
                ("0.00001x^2 - -3", "0.00001x² + 3", "0.00002x"), ("2π*x + e^2*x", "2πx + e²x", "2π + e²")]:
            with self.subTest(texto=texto):
                f = FuncionReal(texto)
                self.assertEqual((natural(f.arbol), DerivadaReal(f).texto), (funcion, derivada))
        r = newton_raphson(FuncionReal("x^3-x-2"), 1.5)
        self.assertEqual(r["derivada"], "3x² − 1")
        self.assertEqual(r["iteraciones"][0]["dfxn"], 5.75)

    def test_tono_proporcional_de_cada_clasificacion(self):
        for cambios, tono in [({}, "exito"), ({"max_iteraciones": "1"}, "aviso"), ({"x0": "0"}, "info")]:
            with self.subTest(tono=tono):
                self.assertContains(self.client.post(RUTA, datos(**cambios)), f'data-tono="{tono}"', count=1)
        bis = "/metodos-numericos/biseccion/"
        for funcion, a, clasificacion in [("x²+1", "-1", "sin_raices_demostrado"), ("x²", "-1", "no_aplicable")]:
            r = self.client.post(bis, {"funcion": funcion, "a": a, "b": "1"})
            self.assertEqual(resultado_html(r)["clasificacion"], clasificacion)
            self.assertContains(r, 'data-tono="info"', count=1)
            self.assertNotContains(r, "data-respuesta-errores")

    def test_tabla_de_clase_n_xn_fxn_desde_cero(self):
        # Diapositiva 15: f(x) = x³ − x − 2, x₀ = 1.5 → filas n = 0…3 con xₙ y f(xₙ).
        r = self.client.post(RUTA, datos(funcion="x³-x-2"))
        html = r.content.decode()
        tabla = html[html.index('class="procedure-table raices-tabla raices-tabla-abierta"'):]
        tabla = tabla[:tabla.index("</table>")]
        self.assertEqual(re.findall(r'<th scope="col">([^<]+)</th>', tabla), ["n", "xₙ", "f(xₙ)"])
        filas = re.findall(r'data-iteracion="(\d+)"', tabla)
        self.assertEqual(filas, ["0", "1", "2", "3"])
        valores = re.findall(r'data-raices-numero="([^"]+)" data-raices-tipo="(x|f)"', tabla)
        self.assertEqual(valores[:2], [("1.5", "x"), ("-0.125", "f")])
        self.assertEqual(float(valores[2][0]), 1.5217391304347827)
        for ausente in ("f′(x actual)", "Cambio absoluto</th>", "Residuo siguiente"):
            self.assertNotIn(ausente, tabla)
        exacta = self.client.post(RUTA, datos(funcion="x^2", x0="0"))
        self.assertContains(exacta, "data-iteracion=", count=1)

    def test_lectura_sin_notacion_cientifica(self):
        from frontend.web.calculadora.templatetags.raices import numero_raices
        for valor, texto in [(5e-14, "0.00000000000005"), (1e-20, "0.00000000000000000001"),
                             (1.5e21, "1500000000000000000000"), (-0.125, "-0.125"), (1.0, "1.0")]:
            html = str(numero_raices(valor, "f"))
            self.assertIn(f">{texto}</span>", html)
            self.assertIn(f'data-raices-numero="{repr(valor)}"', html)
            self.assertIn('data-raices-tipo="f"', html)
            self.assertNotRegex(html.split(">", 1)[1], r"\de[-+]")
        self.assertNotIn("data-raices-tipo", str(numero_raices(0.5)))
