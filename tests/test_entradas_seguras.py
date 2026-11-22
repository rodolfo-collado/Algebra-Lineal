"""P27.1: estructura inválida en el fallback sin JavaScript."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import SimpleTestCase


class PruebasDimensionesSinJS(SimpleTestCase):
    def test_aplicar_vectores_fuera_de_rango_no_calcula_ni_rompe(self):
        # La ruta antigua de vectores se traduce a Operaciones: una estructura imposible no se
        # dibuja ni se calcula (Operaciones aplica sus propios topes de dimensión y operandos).
        for campo, valor in (("dimension", "11"), ("dimension", "0"), ("dimension", ""),
                             ("vectores", "51"), ("vectores", "x")):
            with self.subTest(campo=campo, valor=valor):
                respuesta = self.client.post("/vectores/operaciones/", {
                    "operacion": "suma", "dimension": "3", "vectores": "2",
                    "ajustar": "1", "v1_0": "1/", campo: valor,
                })
                self.assertEqual(respuesta.status_code, 200)
                self.assertNotContains(respuesta, 'id="resultado"')

    def test_aplicar_vectores_conserva_entradas_incompletas_sin_calcular(self):
        respuesta = self.client.post("/vectores/operaciones/", {
            "operacion": "suma", "dimension": "4", "vectores": "3",
            "ajustar": "1", "v1_0": "1/", "v2_2": "-",
        })
        # v3 es el tercer operando de Operaciones; su cuarta componente es la celda 2_3_0.
        self.assertContains(respuesta, 'name="celda_2_3_0"')
        self.assertContains(respuesta, 'value="1/"')
        self.assertContains(respuesta, 'value="-"')
        self.assertNotContains(respuesta, 'aria-invalid="true"')
        self.assertNotContains(respuesta, 'id="resultado"')
