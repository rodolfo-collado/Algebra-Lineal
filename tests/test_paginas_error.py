"""P27.7 (UI-61): páginas de error propias de PyGebra con DEBUG=False.

404 con la interfaz normal; 400, 403, CSRF y 500 con una base mínima sin
catálogo, reverse() ni JavaScript. Nunca muestran traceback ni datos internos.
"""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.core.exceptions import PermissionDenied
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.views.defaults import permission_denied

from frontend.web.calculadora import catalogo


TEMPLATES = Path(__file__).resolve().parents[1] / "frontend" / "web" / "calculadora" / "templates"


@override_settings(DEBUG=False)
class PruebasPaginasDeError(SimpleTestCase):
    def assertPaginaPyGebra(self, respuesta, estado, mensaje):
        self.assertEqual(respuesta.status_code, estado)
        html = respuesta.content.decode()
        self.assertIn(mensaje, html)
        self.assertIn('class="app-name">PyGebra</span>', html)
        self.assertRegex(html, r'<a class="btn btn-primary" href="/">Ir al inicio</a>')
        self.assertIn('<html lang="es"', html)
        for ausente in ("Traceback", "Django", "CSRF verification", "Forbidden", "Bad Request",
                        "Server Error", "Not Found", "DEBUG", "reason"):
            with self.subTest(ausente=ausente):
                self.assertNotIn(ausente, html)
        return html

    def test_404_con_la_interfaz_normal(self):
        for ruta in ("/no-existe/", "/sistemas/inexistente/"):
            with self.subTest(ruta=ruta):
                html = self.assertPaginaPyGebra(self.client.get(ruta), 404, "No encontramos esta página.")
                self.assertIn('id="navigation-toggle"', html)
                self.assertIn("<title>Página no encontrada · PyGebra</title>", html)

    def test_400_por_solicitud_sospechosa(self):
        with self.assertLogs("django.security", "ERROR"):
            respuesta = self.client.get("/", headers={"host": "ejemplo.invalido"})
        html = self.assertPaginaPyGebra(respuesta, 400, "No pudimos procesar esta solicitud.")
        self.assertNotIn("ejemplo.invalido", html)

    def test_403_propio(self):
        respuesta = permission_denied(RequestFactory().get("/"), PermissionDenied("detalle interno"))
        html = self.assertPaginaPyGebra(respuesta, 403, "No se pudo completar esta acción.")
        self.assertNotIn("detalle interno", html)

    def test_403_csrf_propio(self):
        cliente = Client(enforce_csrf_checks=True)
        with self.assertLogs("django.security.csrf", "WARNING"):
            respuesta = cliente.post("/matrices/reduccion/", {"metodo": "gauss", "sistema": "x1=1"})
        html = self.assertPaginaPyGebra(respuesta, 403, "No se pudo completar esta acción.")
        self.assertIn("Vuelve a abrir la herramienta", html)

    def test_500_aunque_falle_la_navegacion(self):
        cliente = Client(raise_request_exception=False)
        with patch.object(catalogo, "arbol", side_effect=RuntimeError("fallo interno")), \
                self.assertLogs("django.request", "ERROR"):
            respuesta = cliente.get("/")
        html = self.assertPaginaPyGebra(respuesta, 500, "PyGebra encontró un problema al procesar esta página.")
        self.assertNotIn("fallo interno", html)

    def test_las_paginas_minimas_no_dependen_de_javascript_ni_del_catalogo(self):
        base = (TEMPLATES / "calculadora" / "errores" / "base.html").read_text(encoding="utf-8")
        self.assertNotIn("{% url", base)
        self.assertNotIn("<script src", base)
        for nombre in ("400.html", "403.html", "403_csrf.html", "500.html"):
            with self.subTest(plantilla=nombre):
                self.assertIn('{% extends "calculadora/errores/base.html" %}', (TEMPLATES / nombre).read_text(encoding="utf-8"))
        self.assertIn('{% extends "calculadora/base.html" %}', (TEMPLATES / "404.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
