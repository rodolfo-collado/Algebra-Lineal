"""Pruebas de la interfaz web de Django."""

import os
import unittest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase

from backend.sistemas import (
    INCONSISTENTE,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
)


class PruebasCalculadoraWeb(SimpleTestCase):
    def test_get_renderiza_la_pagina_principal(self):
        respuesta = self.client.get("/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Calculadora de sistemas")
        self.assertContains(respuesta, "Gauss-Jordan")

    def test_procesa_una_solucion_unica(self):
        respuesta = self.client.post(
            "/",
            {
                "metodo": "gauss_jordan",
                "sistema": "x1+x2=3;x1-x2=1",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, SOLUCION_UNICA)
        self.assertContains(respuesta, "x1 = 2")
        self.assertContains(respuesta, "x2 = 1")

    def test_procesa_soluciones_infinitas(self):
        respuesta = self.client.post(
            "/",
            {
                "metodo": "gauss_jordan",
                "sistema": "x1+x2=2;2x1+2x2=4",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, SOLUCIONES_INFINITAS)
        self.assertContains(respuesta, "x2 es libre")
        self.assertContains(respuesta, "no tiene pivote")

    def test_procesa_un_sistema_inconsistente(self):
        respuesta = self.client.post(
            "/",
            {
                "metodo": "gauss",
                "sistema": "x1+x2=2;2x1+2x2=5",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, INCONSISTENTE)
        self.assertContains(respuesta, "fila 2")
        self.assertContains(respuesta, "0 = 1")
        self.assertContains(respuesta, "no tiene solución")

    def test_muestra_un_error_de_entrada_sin_traceback(self):
        respuesta = self.client.post(
            "/",
            {
                "metodo": "gauss_jordan",
                "sistema": "x1 + = 3",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Formato de sistema inválido")
        self.assertNotContains(respuesta, "Traceback")

    def test_rechaza_un_sistema_vacio(self):
        respuesta = self.client.post(
            "/",
            {"metodo": "gauss", "sistema": "   "},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ingresa un sistema de ecuaciones.")


if __name__ == "__main__":
    unittest.main()
