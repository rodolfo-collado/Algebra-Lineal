"""Pruebas de la infraestructura local de la aplicación desktop."""

from __future__ import annotations

import os
import re
import runpy
import unittest
from http.cookiejar import CookieJar
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

import desktop


RAIZ = Path(__file__).resolve().parents[1]


class PruebasLauncherDesktop(unittest.TestCase):
    def test_construye_url_de_loopback(self):
        self.assertEqual(
            desktop.build_local_url(desktop.LOOPBACK_HOST, 49173),
            "http://127.0.0.1:49173/",
        )

    def test_rechaza_host_externo(self):
        with self.assertRaises(ValueError):
            desktop.build_local_url("0.0.0.0", 49173)

    def test_rechaza_url_de_readiness_externa(self):
        with self.assertRaises(ValueError):
            desktop.wait_for_server("http://example.com:80/", timeout=0.1)

    def test_configura_entorno_desktop(self):
        with patch.dict(os.environ, {}, clear=True):
            desktop.configure_desktop_environment()

            self.assertEqual(
                os.environ["DJANGO_SETTINGS_MODULE"],
                desktop.DJANGO_SETTINGS_MODULE,
            )
            self.assertEqual(os.environ[desktop.DESKTOP_ENVIRONMENT], "1")
            self.assertEqual(os.environ["DJANGO_DEBUG"], "0")

    def test_carga_la_aplicacion_wsgi_configurada(self):
        aplicacion = object()
        aplicacion_con_estaticos = object()
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "django.contrib.staticfiles.handlers.StaticFilesHandler",
                return_value=aplicacion_con_estaticos,
            ) as envolver_estaticos:
                with patch.object(
                    desktop.importlib,
                    "import_module",
                    return_value=SimpleNamespace(application=aplicacion),
                ) as importar:
                    resultado = desktop.load_wsgi_application()

        self.assertIs(resultado, aplicacion_con_estaticos)
        importar.assert_called_once_with("frontend.web.algebra_web.wsgi")
        envolver_estaticos.assert_called_once_with(aplicacion)

    def test_settings_distingue_desarrollo_de_desktop(self):
        ruta_settings = RAIZ / "frontend" / "web" / "algebra_web" / "settings.py"

        with patch.dict(
            os.environ,
            {"ALGEBRA_DESKTOP": "1", "DJANGO_DEBUG": "1"},
            clear=False,
        ):
            desktop_settings = runpy.run_path(str(ruta_settings))

        with patch.dict(
            os.environ,
            {"ALGEBRA_DESKTOP": "0", "DJANGO_DEBUG": "1"},
            clear=False,
        ):
            development_settings = runpy.run_path(str(ruta_settings))

        self.assertTrue(desktop_settings["DESKTOP_MODE"])
        self.assertFalse(desktop_settings["DEBUG"])
        self.assertFalse(development_settings["DESKTOP_MODE"])
        self.assertTrue(development_settings["DEBUG"])

    def test_crea_ventana_con_configuracion_de_escritorio(self):
        ventana = object()
        argumentos = {}

        def crear_ventana(*args, **kwargs):
            argumentos["args"] = args
            argumentos["kwargs"] = kwargs
            return ventana

        webview = SimpleNamespace(create_window=crear_ventana)

        resultado = desktop.create_desktop_window(webview, "http://127.0.0.1:49173/")

        self.assertIs(resultado, ventana)
        self.assertEqual(argumentos["args"], (desktop.APP_TITLE,))
        self.assertEqual(argumentos["kwargs"]["url"], "http://127.0.0.1:49173/")
        self.assertEqual(argumentos["kwargs"]["width"], desktop.WINDOW_WIDTH)
        self.assertEqual(argumentos["kwargs"]["height"], desktop.WINDOW_HEIGHT)
        self.assertEqual(argumentos["kwargs"]["min_size"], desktop.WINDOW_MIN_SIZE)
        self.assertEqual(
            argumentos["kwargs"]["background_color"],
            desktop.WINDOW_BACKGROUND,
        )
        self.assertNotIn("icon", argumentos["kwargs"])
        self.assertTrue(argumentos["kwargs"]["resizable"])
        self.assertFalse(argumentos["kwargs"]["fullscreen"])

    def test_main_reporta_un_error_de_inicio_controlado(self):
        error = desktop.DesktopStartupError("fallo controlado")

        with patch.object(desktop, "run_desktop", side_effect=error):
            with patch.object(desktop, "report_startup_error") as reportar:
                self.assertEqual(desktop.main(), 1)

        reportar.assert_called_once_with(error)

    def test_waitress_usa_loopback_y_puerto_efectivo(self):
        def aplicacion(environ, start_response):
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"ok"]

        servidor, puerto = desktop.create_local_server(aplicacion)
        try:
            self.assertEqual(servidor.effective_host, desktop.LOOPBACK_HOST)
            self.assertEqual(servidor.socket.getsockname()[0], desktop.LOOPBACK_HOST)
            self.assertGreater(puerto, 0)
            self.assertEqual(servidor.socket.getsockname()[1], puerto)
        finally:
            servidor.close()

    def test_el_callback_de_cierre_es_idempotente(self):
        class ThreadFalso:
            def __init__(self):
                self.uniones = 0

            def join(self, timeout):
                self.uniones += 1

            def is_alive(self):
                return False

        servidor = SimpleNamespace(cierres=0)

        def cerrar_servidor():
            servidor.cierres += 1

        servidor.close = cerrar_servidor
        hilo = ThreadFalso()
        shutdown = desktop.make_shutdown_callback(servidor, hilo)

        shutdown()
        shutdown()

        self.assertEqual(servidor.cierres, 1)
        self.assertEqual(hilo.uniones, 1)

    def test_resuelve_el_icono_local(self):
        ruta = desktop.application_icon_path()

        self.assertIsNotNone(ruta)
        self.assertTrue(Path(ruta).is_file())
        self.assertTrue(ruta.endswith("algebra-lineal.ico"))


class PruebaSmokeWaitressDjango(unittest.TestCase):
    def test_waitress_django_y_backend_responden_por_http(self):
        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE",
            "frontend.web.algebra_web.settings",
        )
        import django

        django.setup()

        application = desktop.load_wsgi_application()
        servidor, hilo, url, errores = desktop.start_waitress(application)
        cliente_http = build_opener(HTTPCookieProcessor(CookieJar()))
        try:
            desktop.wait_for_server(
                url,
                timeout=3.0,
                server_thread=hilo,
                errors=errores,
                opener=cliente_http.open,
            )

            with cliente_http.open(url, timeout=3.0) as respuesta:
                html = respuesta.read().decode("utf-8")
                self.assertEqual(respuesta.status, 200)

            with cliente_http.open(
                f"{url}static/calculadora/styles.css",
                timeout=3.0,
            ) as respuesta:
                self.assertEqual(respuesta.status, 200)
                css = respuesta.read().decode("utf-8")
                self.assertIn("--color-primary", css)
                self.assertIn("--color-bg", css)

            with cliente_http.open(
                f"{url}static/calculadora/matriz.js",
                timeout=3.0,
            ) as respuesta:
                self.assertEqual(respuesta.status, 200)
                self.assertIn("renderMatrix", respuesta.read().decode("utf-8"))

            with cliente_http.open(
                f"{url}static/calculadora/tema.js",
                timeout=3.0,
            ) as respuesta:
                self.assertEqual(respuesta.status, 200)
                self.assertIn("algebra-lineal-tema", respuesta.read().decode("utf-8"))

            csrf = re.search(
                rb'name="csrfmiddlewaretoken" value="([^"]+)"',
                html.encode("utf-8"),
            )
            self.assertIsNotNone(csrf)

            datos = urlencode(
                {
                    "csrfmiddlewaretoken": csrf.group(1).decode("ascii"),
                    "metodo": "gauss_jordan",
                    "sistema": "x1+x2=3;x1-x2=1",
                }
            ).encode("ascii")
            solicitud = Request(
                url,
                data=datos,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": url,
                },
            )
            with cliente_http.open(solicitud, timeout=3.0) as respuesta:
                resultado = respuesta.read().decode("utf-8")
                self.assertEqual(respuesta.status, 200)

            self.assertIn("Consistente de solución única", resultado)
            self.assertIn("x1 = 2", resultado)
            self.assertIn("x2 = 1", resultado)
        finally:
            desktop.stop_waitress(servidor, hilo)
            self.assertFalse(hilo.is_alive())


if __name__ == "__main__":
    unittest.main()
