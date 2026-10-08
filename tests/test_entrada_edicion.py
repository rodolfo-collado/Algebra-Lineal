"""P27.9: contrato real del parser, ayudas, dimensiones y fallback HTTP."""

import os
from fractions import Fraction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import SimpleTestCase

from backend.parser_sistemas import parsear_sistema
from frontend.web.calculadora.forms import SistemaForm
from tests.test_teclado import Pagina


EJEMPLO = "2x1 - x2 = 3; x1 + 4x2 = 7"


class PruebasEntradaEdicion(SimpleTestCase):
    def test_sintaxis_real_aceptada(self):
        for texto, esperado in (
            ("x1 = 2", [[1, 2]]), ("x2 = 2", [[0, 1, 2]]),
            ("1/2x1 = -11/13", [[Fraction(1, 2), Fraction(-11, 13)]]),
            ("3.14x1 = -2", [[Fraction(157, 50), -2]]),
            (EJEMPLO, [[2, -1, 3], [1, 4, 7]]),
            (EJEMPLO.replace("; ", "\n"), [[2, -1, 3], [1, 4, 7]]),
            (EJEMPLO.replace("; ", "\r\n"), [[2, -1, 3], [1, 4, 7]]),
            (f"  {EJEMPLO}  ", [[2, -1, 3], [1, 4, 7]]),
            ("1 / 2x1 = 3", [[Fraction(1, 2), 3]]),
        ):
            with self.subTest(texto=texto):
                self.assertEqual(parsear_sistema(texto, limitar_entrada=True), esperado)

    def test_sintaxis_real_rechazada(self):
        for texto in ("X1 = 2", "x = 2", "y = 2", "z = 2", "3,14x1 = 2", EJEMPLO + ";", "1 2x1 = 3"):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                parsear_sistema(texto, limitar_entrada=True)

    def test_ayuda_y_placeholder_aceptados_y_asociados(self):
        respuesta = self.client.get("/matrices/reduccion/")
        for texto in (EJEMPLO, "minúscula", "decimales con punto", "saltos de línea", "coma decimal", "vacío al final"):
            self.assertContains(respuesta, texto)
        campo = next(e for e in Pagina(respuesta.content.decode()).elementos if e.get("name") == "sistema")
        self.assertIn("sistema-ayuda", campo["aria-describedby"].split())
        self.assertEqual(len(parsear_sistema(campo["placeholder"], limitar_entrada=True)), 3)
        respuesta = self.client.post("/matrices/reduccion/", {"sistema": "X1=2", "metodo": "gauss"})
        campo = next(e for e in Pagina(respuesta.content.decode()).elementos if e.get("name") == "sistema")
        self.assertEqual(campo["aria-describedby"].split(), ["sistema-ayuda", "id_sistema_error"])

    def test_defaults_y_dimensiones_explicitas(self):
        form = SistemaForm()
        self.assertEqual([form[c].value() for c in ("ecuaciones", "variables")], [3, 3])
        form = SistemaForm(initial={"ecuaciones": 5, "variables": 4})
        self.assertEqual([form[c].value() for c in ("ecuaciones", "variables")], [5, 4])

    def test_post_error_conserva_dimensiones_y_valores(self):
        datos = {"tipo_entrada": "matriz", "metodo": "gauss", "ecuaciones": "5", "variables": "4"}
        datos.update({f"matriz_{i}_{j}": "-11/13" for i in range(5) for j in range(5)})
        datos["matriz_4_4"] = "1/"
        respuesta = self.client.post("/matrices/reduccion/", datos)
        form = SistemaForm(datos)
        self.assertFalse(form.is_valid())
        self.assertEqual([form[c].value() for c in ("ecuaciones", "variables")], ["5", "4"])
        self.assertEqual(form.valores_matriz_ingresados()[4], ["-11/13"] * 4 + ["1/"])
        self.assertNotContains(respuesta, 'id="resultado"')
        datos["variables"] = ""
        respuesta = self.client.post("/matrices/reduccion/", datos)
        self.assertContains(respuesta, 'name="variables"')
        self.assertEqual(SistemaForm(datos)["variables"].value(), "")

    def test_sin_js_texto_sigue_funcional(self):
        respuesta = self.client.post("/matrices/reduccion/", {"sistema": EJEMPLO, "metodo": "gauss"})
        self.assertContains(respuesta, 'id="resultado"')


if __name__ == "__main__":
    import unittest
    unittest.main()
