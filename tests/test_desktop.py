"""Pruebas de la infraestructura local de la aplicación desktop."""

from __future__ import annotations

import json
import os
import re
import runpy
import sys
import tempfile
import unittest
from http.cookiejar import CookieJar
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

import desktop


RAIZ = Path(__file__).resolve().parents[1]


class PruebasLauncherDesktop(unittest.TestCase):
    def test_mensaje_webview2_identifica_pygebra(self):
        self.assertEqual(desktop.APP_TITLE, "PyGebra")
        with patch.object(desktop.sys, "platform", "win32"), patch.object(desktop, "webview2_available", return_value=False):
            with self.assertRaises(desktop.DesktopStartupError) as error:
                desktop.ensure_webview2_runtime()
        self.assertIn("Vuelve a ejecutar el instalador de PyGebra", str(error.exception))
        self.assertNotIn("Álgebra Lineal", str(error.exception))

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

        local = str(Path.home() / "AppData" / "Local")
        with patch.dict(os.environ, {"LOCALAPPDATA": local}, clear=True):
            desktop.configure_desktop_environment()
            self.assertEqual(
                os.environ[desktop.PREFERENCES_ENVIRONMENT],
                str(Path(local) / "PyGebra" / "preferencias.json"),
            )
        # Una ruta ya fijada (pruebas manuales aisladas) no se sobrescribe.
        with patch.dict(os.environ, {"LOCALAPPDATA": local, desktop.PREFERENCES_ENVIRONMENT: "otra.json"}, clear=True):
            desktop.configure_desktop_environment()
            self.assertEqual(os.environ[desktop.PREFERENCES_ENVIRONMENT], "otra.json")

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

        with patch.object(desktop, "restored_window_geometry", return_value=None):
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
        # UI-69: maximizada, no pantalla completa; restaurar vuelve a un tamaño normal.
        self.assertTrue(argumentos["kwargs"]["maximized"])
        self.assertNotIn("frameless", argumentos["kwargs"])
        self.assertEqual(argumentos["kwargs"]["min_size"], (760, 560))

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

    def test_el_spec_incluye_los_modulos_que_django_carga_por_nombre(self):
        """PyInstaller no ve los módulos referenciados solo como cadenas en settings."""
        ruta_settings = RAIZ / "frontend" / "web" / "algebra_web" / "settings.py"
        plantillas = runpy.run_path(str(ruta_settings))["TEMPLATES"]
        spec = (RAIZ / "AlgebraLineal.spec").read_text(encoding="utf-8")
        ocultos = re.findall(r'"(frontend\.[\w.]+)"', spec.split("hiddenimports")[1].split("]")[0])
        for opciones in (plantilla["OPTIONS"] for plantilla in plantillas):
            for procesador in opciones.get("context_processors", ()):
                modulo = procesador.rsplit(".", 1)[0]
                with self.subTest(modulo=modulo):
                    self.assertIn(modulo, ocultos)
        self.assertIn("frontend.web.calculadora.views", ocultos)
        # {% load %} importa cada librería de tags por nombre; sin ellas la app instalada responde 500.
        templatetags = RAIZ / "frontend" / "web" / "calculadora" / "templatetags"
        self.assertIn("frontend.web.calculadora.templatetags", ocultos)
        for libreria in templatetags.glob("*.py"):
            if libreria.stem != "__init__":
                with self.subTest(libreria=libreria.stem):
                    self.assertIn(f"frontend.web.calculadora.templatetags.{libreria.stem}", ocultos)

    def test_resuelve_el_icono_local(self):
        ruta = desktop.application_icon_path()

        self.assertIsNotNone(ruta)
        self.assertTrue(Path(ruta).is_file())
        self.assertTrue(ruta.endswith("pygebra.ico"))

    def test_el_spec_y_la_identidad_apuntan_al_icono_actual(self):
        spec = (RAIZ / "AlgebraLineal.spec").read_text(encoding="utf-8")
        self.assertGreaterEqual(spec.count("pygebra.ico"), 2)
        self.assertEqual(desktop.APP_USER_MODEL_ID, "PyGebra.Desktop")
        self.assertNotRegex(desktop.APP_USER_MODEL_ID, r"\d")
        fuente = Path(desktop.__file__).read_text(encoding="utf-8")
        self.assertLess(
            fuente.index("set_windows_app_user_model_id()"),
            fuente.index("create_desktop_window(webview, url)"),
        )

    def test_otra_plataforma_no_fija_la_identidad_de_windows(self):
        from unittest.mock import MagicMock

        windll = MagicMock()
        with patch.object(desktop.sys, "platform", "linux"), patch("ctypes.windll", windll, create=True):
            desktop.set_windows_app_user_model_id()
        windll.shell32.SetCurrentProcessExplicitAppUserModelID.assert_not_called()

    def test_win32_sin_windll_no_impide_el_arranque(self):
        with patch.object(desktop.sys, "platform", "win32"), patch("ctypes.windll", None, create=True):
            desktop.set_windows_app_user_model_id()


class EventoNet:
    """Doble de un evento .NET: pythonnet suscribe los manejadores con +=."""

    def __init__(self):
        self.manejadores = []

    def __iadd__(self, manejador):
        self.manejadores.append(manejador)
        return self

    def disparar(self, *args):
        for manejador in self.manejadores:
            manejador(*args)


class ListaNet(list):
    """Doble de IList<CoreWebView2ContextMenuItem>."""

    @property
    def Count(self):
        return len(self)

    def RemoveAt(self, indice):
        del self[indice]


def menu(*nombres):
    return SimpleNamespace(MenuItems=ListaNet(SimpleNamespace(Name=n) for n in nombres), Handled=False)


class PruebasEscritorioP27_7(unittest.TestCase):
    """Ventana, preferencias entre aperturas y menú contextual de la app de escritorio."""

    def area_util(self, rect, dpi):
        """user32 de mentira: área útil en píxeles físicos y DPI del sistema."""

        def spi(accion, parametro, puntero, flags):
            self.assertEqual(accion, desktop.SPI_GETWORKAREA)
            area = puntero._obj
            area.left, area.top, area.right, area.bottom = rect
            return 1

        return MagicMock(user32=SimpleNamespace(SystemParametersInfoW=spi, GetDpiForSystem=lambda: dpi))

    def test_al_restaurar_la_ventana_cabe_en_el_area_util(self):
        casos = (
            # Este equipo: 2912×1638 al 200 % con barra de tareas (área 1456×771 lógica).
            ((0, 0, 2912, 1542), 192, (178, 31, 1100, 709)),
            # Pantalla amplia sin escalado: tamaño completo y centrado.
            ((0, 0, 1920, 1032), 96, (410, 136, 1100, 760)),
            # Barra de tareas a la izquierda (el área no empieza en 0).
            ((62, 0, 1366, 768), 96, (164, 31, 1100, 706)),
            # Área menor que min_size: se respeta min_size y la barra de título queda visible.
            ((0, 0, 1000, 600), 120, (20, 0, 760, 560)),
        )
        for rect, dpi, esperado in casos:
            with self.subTest(rect=rect, dpi=dpi), patch.object(desktop.sys, "platform", "win32"), \
                    patch("ctypes.windll", self.area_util(rect, dpi), create=True):
                self.assertEqual(desktop.restored_window_geometry(), esperado)

    def test_sin_area_util_usa_el_tamano_por_defecto(self):
        with patch.object(desktop.sys, "platform", "linux"):
            self.assertIsNone(desktop.restored_window_geometry())
        sin_area = MagicMock(user32=SimpleNamespace(SystemParametersInfoW=lambda *args: 0, GetDpiForSystem=lambda: 96))
        with patch.object(desktop.sys, "platform", "win32"), patch("ctypes.windll", sin_area, create=True):
            self.assertIsNone(desktop.restored_window_geometry())
        webview = MagicMock()
        with patch.object(desktop, "restored_window_geometry", return_value=(178, 31, 1100, 709)):
            desktop.create_desktop_window(webview, "http://127.0.0.1:49173/")
        opciones = webview.create_window.call_args.kwargs
        self.assertEqual((opciones["x"], opciones["y"], opciones["width"], opciones["height"]), (178, 31, 1100, 709))
        self.assertTrue(opciones["maximized"])

    def test_preferencias_fuera_del_repositorio_la_instalacion_y_los_temporales(self):
        local = Path.home() / "AppData" / "Local"
        with patch.dict(os.environ, {"LOCALAPPDATA": str(local)}):
            ruta = desktop.preferences_path()
        self.assertEqual(ruta, local / "PyGebra" / "preferencias.json")
        self.assertTrue(ruta.is_absolute())
        for carpeta in (
            RAIZ,
            Path(tempfile.gettempdir()),
            Path(sys.executable).resolve().parent,
            # Carpeta de instalación por usuario de Inno Setup y _MEIPASS (_internal).
            local / "Programs" / "AlgebraLineal",
        ):
            with self.subTest(carpeta=carpeta):
                self.assertFalse(ruta.is_relative_to(carpeta.resolve()))
                self.assertFalse(ruta.is_relative_to(carpeta))

    def test_sin_carpeta_de_usuario_absoluta_no_se_guardan_preferencias(self):
        with patch.dict(os.environ, {"LOCALAPPDATA": "relativa"}, clear=True), \
                patch.object(desktop.Path, "home", side_effect=RuntimeError("sin carpeta")):
            self.assertIsNone(desktop.preferences_path())
            desktop.configure_desktop_environment()
            self.assertNotIn(desktop.PREFERENCES_ENVIRONMENT, os.environ)

    def test_settings_solo_usa_el_archivo_de_preferencias_en_escritorio(self):
        ruta_settings = RAIZ / "frontend" / "web" / "algebra_web" / "settings.py"
        with patch.dict(os.environ, {"ALGEBRA_DESKTOP": "1", "ALGEBRA_PREFERENCIAS": "pref.json"}):
            self.assertEqual(runpy.run_path(str(ruta_settings))["DESKTOP_PREFERENCES_FILE"], "pref.json")
        with patch.dict(os.environ, {"ALGEBRA_DESKTOP": "0", "ALGEBRA_PREFERENCIAS": "pref.json"}):
            self.assertIsNone(runpy.run_path(str(ruta_settings))["DESKTOP_PREFERENCES_FILE"])

    def iniciar(self, depuracion):
        webview = MagicMock()
        with patch.object(desktop.sys, "platform", "win32"), \
                patch.object(desktop, "webview2_available", return_value=True), \
                patch("ctypes.windll", MagicMock(), create=True), \
                patch.dict("sys.modules", webview=webview), \
                patch.dict(os.environ, {"ALGEBRA_DESKTOP_DEBUG": depuracion}), \
                patch.object(desktop, "load_wsgi_application"), \
                patch.object(desktop, "start_waitress", return_value=(object(), object(), "http://127.0.0.1:49173/", None)) as servidor, \
                patch.object(desktop, "wait_for_server"), \
                patch.object(desktop, "stop_waitress"), \
                patch.object(desktop, "install_edit_context_menu") as menu_edicion:
            desktop.run_desktop()
        return webview, servidor, menu_edicion

    def test_inicio_privado_en_puerto_efimero_y_desde_inicio(self):
        webview, servidor, menu_edicion = self.iniciar("0")
        opciones = webview.start.call_args.kwargs
        # WebView2 descarta su perfil al cerrar: no hay sesión anterior que restaurar.
        self.assertTrue(opciones["private_mode"])
        self.assertNotIn("storage_path", opciones)
        self.assertFalse(opciones["debug"])
        # Sin puerto preferido: el sistema elige uno libre en el mismo bind de Waitress.
        self.assertEqual(servidor.call_args.kwargs, {})
        self.assertEqual(webview.create_window.call_args.kwargs["url"], "http://127.0.0.1:49173/")
        menu_edicion.assert_called_once_with(webview.create_window.return_value)

    def test_diagnostico_conserva_el_menu_de_pywebview(self):
        webview, _, menu_edicion = self.iniciar("1")
        self.assertTrue(webview.start.call_args.kwargs["debug"])
        menu_edicion.assert_not_called()

    def test_menu_contextual_deja_solo_las_acciones_de_edicion(self):
        # Nombres reales del menú de WebView2 en un campo editable.
        args = menu("emoji", "other", "undo", "redo", "other", "cut", "copy", "paste", "pasteAndMatchStyle",
                    "selectAll", "other", "print", "other", "moreTools")
        desktop.filter_context_menu(None, args)
        self.assertEqual([item.Name for item in args.MenuItems], ["cut", "copy", "paste", "selectAll"])
        self.assertFalse(args.Handled)
        # Texto seleccionado sin editar: solo Copiar.
        args = menu("copy", "other", "print", "inspectElement")
        desktop.filter_context_menu(None, args)
        self.assertEqual([item.Name for item in args.MenuItems], ["copy"])
        # Fondo de la página o enlaces: nada útil, no se muestra menú.
        for nombres in (("back", "forward", "reload", "other", "saveAs", "print"), ("copyLinkToClipboard", "openLinkInNewWindow")):
            with self.subTest(nombres=nombres):
                args = menu(*nombres)
                desktop.filter_context_menu(None, args)
                self.assertEqual(list(args.MenuItems), [])
                self.assertTrue(args.Handled)
        # Un fallo inesperado nunca deja ver el menú completo.
        roto = SimpleNamespace(Handled=False)
        desktop.filter_context_menu(None, roto)
        self.assertTrue(roto.Handled)

    def test_menu_contextual_se_filtra_antes_de_activarse(self):
        orden = []

        class Evento(EventoNet):
            def __iadd__(self, manejador):
                orden.append("filtro")
                return super().__iadd__(manejador)

        class Ajustes:
            def __setattr__(self, nombre, valor):
                orden.append(f"{nombre}={valor}")
                super().__setattr__(nombre, valor)

        core = SimpleNamespace(ContextMenuRequested=Evento(), Settings=Ajustes())
        control = SimpleNamespace(CoreWebView2InitializationCompleted=EventoNet())
        ventana = SimpleNamespace(events=SimpleNamespace(before_show=EventoNet()), native=None)
        desktop.install_edit_context_menu(ventana)
        # pywebview crea el control nativo justo antes de before_show.
        ventana.native = SimpleNamespace(webview=control)
        ventana.events.before_show.disparar()
        control.CoreWebView2InitializationCompleted.disparar(SimpleNamespace(CoreWebView2=core), SimpleNamespace(IsSuccess=False))
        self.assertEqual(orden, [])
        control.CoreWebView2InitializationCompleted.disparar(SimpleNamespace(CoreWebView2=core), SimpleNamespace(IsSuccess=True))
        self.assertEqual(orden, ["filtro", "AreDefaultContextMenusEnabled=True"])
        self.assertEqual(core.ContextMenuRequested.manejadores, [desktop.filter_context_menu])
        # DevTools y los atajos del navegador no se tocan: siguen como los deja pywebview.
        self.assertNotIn("AreDevToolsEnabled", " ".join(orden))
        self.assertNotIn("AreBrowserAcceleratorKeysEnabled", " ".join(orden))

    def test_un_fallo_al_registrar_el_menu_no_sale_al_evento_net(self):
        class EventoRoto(EventoNet):
            def __iadd__(self, manejador):
                raise RuntimeError("API no disponible en este runtime")

        ajustes = SimpleNamespace(AreDefaultContextMenusEnabled=False)
        core = SimpleNamespace(ContextMenuRequested=EventoRoto(), Settings=ajustes)
        control = SimpleNamespace(CoreWebView2InitializationCompleted=EventoNet())
        ventana = SimpleNamespace(events=SimpleNamespace(before_show=EventoNet()), native=SimpleNamespace(webview=control))
        desktop.install_edit_context_menu(ventana)
        ventana.events.before_show.disparar()
        control.CoreWebView2InitializationCompleted.disparar(SimpleNamespace(CoreWebView2=core), SimpleNamespace(IsSuccess=True))
        self.assertFalse(ajustes.AreDefaultContextMenusEnabled)

    def test_sin_control_nativo_el_hook_no_impide_mostrar_la_ventana(self):
        ventana = SimpleNamespace(events=SimpleNamespace(before_show=EventoNet()), native=None)
        desktop.install_edit_context_menu(ventana)
        ventana.events.before_show.disparar()

    def test_dos_instancias_conviven_sin_single_instance(self):
        def aplicacion(environ, start_response):
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"ok"]

        primero, puerto_primero = desktop.create_local_server(aplicacion)
        try:
            segundo, puerto_segundo = desktop.create_local_server(aplicacion)
            try:
                self.assertNotEqual(puerto_primero, puerto_segundo)
                for servidor in (primero, segundo):
                    self.assertEqual(servidor.socket.getsockname()[0], desktop.LOOPBACK_HOST)
            finally:
                segundo.close()
        finally:
            primero.close()


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
                self.assertIn("Inicio · PyGebra", html)
                self.assertIn('href="/matrices/reduccion/"', html)

            # P27.7: con DEBUG=False (como en escritorio) un 404 es una página de PyGebra.
            from django.test import override_settings

            with override_settings(DEBUG=False), self.assertRaises(HTTPError) as error:
                cliente_http.open(f"{url}no-existe/", timeout=3.0)
            self.assertEqual(error.exception.code, 404)
            pagina_404 = error.exception.read().decode("utf-8")
            self.assertIn("No encontramos esta página.", pagina_404)
            self.assertNotIn("Not Found", pagina_404)

            # Las preferencias viajan por la misma pila y solo llegan al archivo propio.
            with tempfile.TemporaryDirectory() as carpeta:
                archivo = Path(carpeta) / "PyGebra" / "preferencias.json"
                with override_settings(DESKTOP_MODE=True, DESKTOP_PREFERENCES_FILE=str(archivo)):
                    with cliente_http.open(url, timeout=3.0) as respuesta:
                        inicio = respuesta.read().decode("utf-8")
                    token = re.search(r'<meta name="csrf-token" content="([^"]+)">', inicio).group(1)
                    solicitud = Request(
                        f"{url}preferencias/",
                        data=urlencode({"clave": "pygebra-tema", "valor": "dark"}).encode("ascii"),
                        headers={"X-CSRFToken": token},
                    )
                    with cliente_http.open(solicitud, timeout=3.0) as respuesta:
                        self.assertEqual(respuesta.status, 204)
                    with cliente_http.open(url, timeout=3.0) as respuesta:
                        self.assertIn('data-desktop data-pygebra-tema="dark"', respuesta.read().decode("utf-8"))
                self.assertEqual(json.loads(archivo.read_text(encoding="utf-8")), {"pygebra-tema": "dark"})

            url_sistemas = f"{url}sistemas/"
            with cliente_http.open(url_sistemas, timeout=3.0) as respuesta:
                html = respuesta.read().decode("utf-8")
                self.assertEqual(respuesta.status, 200)

            with cliente_http.open(
                f"{url}static/calculadora/styles.css",
                timeout=3.0,
            ) as respuesta:
                self.assertEqual(respuesta.status, 200)
                css = respuesta.read().decode("utf-8")
                self.assertIn("@import", css)
                self.assertIn("styles/tokens.css", css)
                self.assertIn("styles/base.css", css)

            with cliente_http.open(
                f"{url}static/calculadora/styles/tokens.css",
                timeout=3.0,
            ) as respuesta:
                self.assertEqual(respuesta.status, 200)
                tokens = respuesta.read().decode("utf-8")
                self.assertIn("--color-primary", tokens)
                self.assertIn("--color-brand", tokens)
                self.assertIn("--color-bg", tokens)

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

            for recurso, marca in (
                ("navigation.js", "navegacion-principal"),
                ("buscador.js", "data-buscador"),
                ("teclado.js", "data-insercion"),
                ("conversion.js", "data-conversion-bases"),
                ("vectores.js", "data-vectores"),
            ):
                with cliente_http.open(
                    f"{url}static/calculadora/{recurso}",
                    timeout=3.0,
                ) as respuesta:
                    self.assertEqual(respuesta.status, 200)
                    self.assertIn(marca, respuesta.read().decode("utf-8"))

            # La ruta antigua de Gauss sigue abriendo Reducción por filas con Gauss elegido.
            with cliente_http.open(f"{url}sistemas/gauss/", timeout=3.0) as respuesta:
                self.assertEqual(respuesta.status, 200)
                self.assertEqual(respuesta.url, f"{url}matrices/reduccion/?metodo=gauss")
                self.assertIn("Reducción por filas", respuesta.read().decode("utf-8"))

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
                url_sistemas,
                data=datos,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": url_sistemas,
                },
            )
            with cliente_http.open(solicitud, timeout=3.0) as respuesta:
                resultado = respuesta.read().decode("utf-8")
                self.assertEqual(respuesta.status, 200)

            self.assertIn("Consistente de solución única", resultado)
            self.assertIn("x₁ = 2", resultado)
            self.assertIn("x₂ = 1", resultado)

            # La conversión de bases viaja por la misma pila Waitress + Django.
            url_bases = f"{url}bases/conversion/"
            with cliente_http.open(url_bases, timeout=3.0) as respuesta:
                self.assertEqual(respuesta.status, 200)
                self.assertIn("Conversión de bases", respuesta.read().decode("utf-8"))
            # Varias casillas «Convertir a» viajan como campos repetidos, igual que en el navegador.
            solicitud = Request(
                url_bases,
                data=urlencode(
                    [
                        ("csrfmiddlewaretoken", csrf.group(1).decode("ascii")),
                        ("numero", "13"),
                        ("base_origen", "10"),
                        ("bases_destino", "2"),
                        ("bases_destino", "16"),
                    ]
                ).encode("ascii"),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": url_bases,
                },
            )
            with cliente_http.open(solicitud, timeout=3.0) as respuesta:
                self.assertEqual(respuesta.status, 200)
                conversion = respuesta.read().decode("utf-8")
            # Conversión multidestino real por la pila empaquetada: el origen una vez y las dos escrituras.
            self.assertIn("Decimal → binario y hexadecimal", conversion)
            self.assertIn("13₁₀", conversion)
            self.assertIn("1101₂", conversion)
            self.assertIn("D₁₆", conversion)
            self.assertNotIn("15₈", conversion)

            # Operaciones con vectores: la combinación lineal reutiliza Gauss-Jordan por la misma pila.
            url_vectores = f"{url}vectores/operaciones/"
            with cliente_http.open(url_vectores, timeout=3.0) as respuesta:
                self.assertEqual(respuesta.status, 200)
                self.assertIn("Operaciones con vectores", respuesta.read().decode("utf-8"))
            solicitud = Request(
                url_vectores,
                data=urlencode(
                    {
                        "csrfmiddlewaretoken": csrf.group(1).decode("ascii"),
                        "operacion": "combinacion",
                        "dimension": "2",
                        "vectores": "2",
                        "v1_0": "1", "v1_1": "0", "v2_0": "0", "v2_1": "1",
                        "b_0": "3", "b_1": "4",
                    }
                ).encode("ascii"),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": url_vectores,
                },
            )
            with cliente_http.open(solicitud, timeout=3.0) as respuesta:
                self.assertEqual(respuesta.status, 200)
                combinacion = respuesta.read().decode("utf-8")
            self.assertIn("b es combinación lineal de v1 y v2", combinacion)
            self.assertIn("x₁ = 3", combinacion)
            self.assertIn("(3, 4) = 3(1, 0) + 4(0, 1)", combinacion)

            # P13A viaja por la pila desktop real, con CSRF y recursos locales.
            from tests.test_matrices_web import Contenido, datos_matrices

            url_matrices = f"{url}matrices/operaciones/"
            with cliente_http.open(url_matrices, timeout=3.0) as respuesta:
                self.assertIn("Operaciones con matrices", respuesta.read().decode("utf-8"))
            for operacion, esperado in (
                ("suma", [["2", "4", "6"], ["8", "10", "12"]]),
                ("resta", [["0", "0", "0"], ["0", "0", "0"]]),
                ("escalar", [["1/2", "1", "3/2"], ["2", "5/2", "3"]]),
                ("traspuesta", [["1", "4"], ["2", "5"], ["3", "6"]]),
            ):
                a = [[1, 2, 3], [4, 5, 6]]
                datos = datos_matrices(
                    operacion, a=a, b=a if operacion in ("suma", "resta") else None,
                    escalar="1/2" if operacion == "escalar" else None,
                    csrfmiddlewaretoken=csrf.group(1).decode("ascii"),
                )
                solicitud = Request(url_matrices, data=urlencode(datos).encode("ascii"), headers={"Referer": url_matrices})
                with cliente_http.open(solicitud, timeout=3.0) as respuesta:
                    tablas = Contenido(respuesta.read().decode("utf-8")).tablas
                self.assertEqual(tablas["Resultado"], esperado)
            # P13B: AB y Ax con método comparado, por la misma pila.
            from tests.test_multiplicacion_matrices_web import datos_matriz_vector, datos_producto

            for datos, esperado, procedimientos in (
                (datos_producto(a=[[1, 2, 3], [4, 5, 6]], b=[[7, 8], [9, 10], [11, 12]], metodo="comparar"), [["58", "64"], ["139", "154"]], ("Fila por columna", "Por columnas")),
                (datos_matriz_vector(metodo="comparar"), [["3"], ["6"]], ("Regla fila-vector", "Combinación lineal de columnas")),
            ):
                datos["csrfmiddlewaretoken"] = csrf.group(1).decode("ascii")
                solicitud = Request(url_matrices, data=urlencode(datos).encode("ascii"), headers={"Referer": url_matrices})
                with cliente_http.open(solicitud, timeout=3.0) as respuesta:
                    html = respuesta.read().decode("utf-8")
                self.assertEqual(Contenido(html).tablas["Resultado"], esperado)
                for procedimiento in procedimientos:
                    self.assertIn(f">{procedimiento}</h5>", html)
            with cliente_http.open(f"{url}static/calculadora/expresiones.js", timeout=3.0) as respuesta:
                self.assertEqual(respuesta.status, 200)
                contenido = respuesta.read().decode("utf-8")
                self.assertIn("symbol-template", contenido)
                self.assertIn("camposMaximos", contenido)
            # P14: Ax = b con x desconocido, por la misma pila; una fracción y un caso rectangular.
            from tests.test_ecuaciones_matriciales_web import datos_ecuacion

            url_ecuaciones = f"{url}matrices/ecuaciones/"
            with cliente_http.open(url_ecuaciones, timeout=3.0) as respuesta:
                self.assertEqual(respuesta.status, 200)
                pagina = respuesta.read().decode("utf-8")
            self.assertIn("Resolver Ax = b", pagina)
            self.assertIn('aria-label="Vector incógnita x, no editable"', pagina)
            for datos, x, textos in (
                (datos_ecuacion(a=[[2, 0], [0, 3]], b=[1, 1], metodo="comparar"), [["1/2"], ["1/3"]],
                 ("Ax = b tiene solución única.", "b = (1/2)a₁ + (1/3)a₂", 'id="procedimiento"', 'class="disclosure disclosure-nested"')),
                (datos_ecuacion(a=[[1, 0], [0, 1], [1, 1]], b=[2, 3, 5]), [["2"], ["3"]],
                 ("A (3×2) · x (2) = b (3)", "x₁ = 2", "x₂ = 3")),
            ):
                datos["csrfmiddlewaretoken"] = csrf.group(1).decode("ascii")
                solicitud = Request(url_ecuaciones, data=urlencode(datos).encode("ascii"), headers={"Referer": url_ecuaciones})
                with cliente_http.open(solicitud, timeout=3.0) as respuesta:
                    html = respuesta.read().decode("utf-8")
                self.assertEqual(Contenido(html).tablas["Vector solución x"], x)
                for texto in textos:
                    self.assertIn(texto, html)
            with cliente_http.open(f"{url}static/calculadora/ecuaciones.js", timeout=3.0) as respuesta:
                self.assertEqual(respuesta.status, 200)
                self.assertIn("data-ecuacion", respuesta.read().decode("utf-8"))
        finally:
            desktop.stop_waitress(servidor, hilo)
            self.assertFalse(hilo.is_alive())


if __name__ == "__main__":
    unittest.main()
