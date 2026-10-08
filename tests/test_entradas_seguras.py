"""P27.1: estructura inválida en el fallback sin JavaScript."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import SimpleTestCase


class PruebasDimensionesSinJS(SimpleTestCase):
    def test_aplicar_vectores_rechaza_dimensiones_y_cantidades_fuera_de_rango(self):
        for campo, valor, mensaje in (
            ("dimension", "11", "La dimensión máxima admitida es 10"),
            ("dimension", "0", "al menos una componente"),
            ("dimension", "", "Indica la dimensión"),
            ("vectores", "51", "hasta 50 vectores"),
            ("vectores", "1", "al menos"),
        ):
            with self.subTest(campo=campo, valor=valor):
                respuesta = self.client.post("/vectores/operaciones/", {
                    "operacion": "suma", "dimension": "3", "vectores": "2",
                    "ajustar": "1", "v1_0": "1/", campo: valor,
                })
                self.assertContains(respuesta, mensaje)
                self.assertContains(respuesta, 'aria-invalid="true"')
                self.assertContains(respuesta, 'value="1/"')
                self.assertNotContains(respuesta, 'id="resultado"')

    def test_aplicar_vectores_conserva_entradas_incompletas_sin_calcular(self):
        respuesta = self.client.post("/vectores/operaciones/", {
            "operacion": "suma", "dimension": "4", "vectores": "3",
            "ajustar": "1", "v1_0": "1/", "v2_2": "-",
        })
        self.assertContains(respuesta, 'name="v3_3"')
        self.assertContains(respuesta, 'value="1/"')
        self.assertContains(respuesta, 'value="-"')
        self.assertNotContains(respuesta, 'aria-invalid="true"')
        self.assertNotContains(respuesta, 'id="resultado"')
