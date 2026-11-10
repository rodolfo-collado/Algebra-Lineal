"""Contrato HTTP, navegación, teclado y presentación sin JavaScript."""
from tests.test_biseccion_web import resultado_html
from django.test import Client, SimpleTestCase
from django.urls import reverse
from backend.funciones_reales import FuncionReal
from backend.newton_raphson import newton_raphson
from frontend.web.calculadora import catalogo

RUTA = "/metodos-numericos/newton-raphson/"
def datos(**cambios):
    return {"funcion":"x²-2", "derivada":"2x", "x0":"1.5", **cambios}

class NewtonWebTests(SimpleTestCase):
    def test_entrada_y_catalogo(self):
        r=self.client.get(RUTA)
        for texto in ['id="id_derivada"', 'id="id_x0"', 'data-perfil="funcion-real"',
                      "newton_raphson.js", "raices.js", "teclado.js", "plotly-basic"]:
            self.assertContains(r,texto)
        self.assertNotContains(r,'id="id_a"')
        self.assertNotContains(r,'id="resultado"')
        self.assertEqual(reverse("calculadora:newton-raphson"), RUTA)
        self.assertTrue(catalogo.NEWTON_RAPHSON.disponible)
        for ruta in ["/", "/?q=newton", "/areas/metodos-numericos/", catalogo.BISECCION.ruta, catalogo.REGLA_FALSA.ruta]:
            self.assertContains(self.client.get(ruta), f'href="{RUTA}"')

    def test_resultado_geometria_y_tabla(self):
        r=self.client.post(RUTA,datos())
        esperado=newton_raphson(FuncionReal("x²-2"),FuncionReal("2x"),1.5)
        self.assertEqual(resultado_html(r), esperado)
        self.assertContains(r,"data-iteracion=", count=len(esperado["iteraciones"]))
        for texto in ["tangente", "Verificación", "Residuo", "Cambio absoluto", "Anterior", "Siguiente", "error verdadero"]:
            self.assertContains(r,texto)

    def test_estados_sin_javascript(self):
        for cambios, estado in [({"x0":"0"},"derivada"),
                ({"funcion":"x^3-2x+2", "derivada":"3x^2-2", "x0":"0"}, "oscilacion"),
                ({"funcion":"x^2", "x0":"0"}, "exacta"),
                ({"max_iteraciones":"1"}, "limite"),
                ({"funcion":"ln(x)","derivada":"1/x","x0":"4"}, "dominio")]:
            with self.subTest(estado=estado):
                r=self.client.post(RUTA,datos(**cambios))
                self.assertEqual(resultado_html(r)["estado"],estado)
                if estado != "exacta": self.assertContains(r,"Aproximación sin convergencia")

    def test_validacion_limites_y_seguridad(self):
        for cambios in [{"derivada":""}, {"derivada":"x.__class__"}, {"funcion":"ln(x)", "x0":"-1"},
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

    def test_grafica_antes_de_derivada_o_calculo(self):
        r=self.client.post(RUTA+"grafica/", {"funcion":"ln(x)"})
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.json()["x"]),801)
        self.assertIn(None,r.json()["y"])
