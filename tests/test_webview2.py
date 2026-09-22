"""El launcher informa la ausencia del runtime antes de iniciar servicios."""

import unittest
from unittest.mock import MagicMock, patch

import desktop


class PruebasWebView2(unittest.TestCase):
    def registro(self, valores):
        registry = MagicMock()
        registry.HKEY_CURRENT_USER = 1
        registry.HKEY_LOCAL_MACHINE = 2
        registry.KEY_READ = 4
        registry.KEY_WOW64_32KEY = 8
        registry.KEY_WOW64_64KEY = 16

        def abrir(hive, path, reserved, access):
            self.assertEqual(path, desktop.WEBVIEW2_REGISTRY_KEY)
            if (hive, access) not in valores:
                raise FileNotFoundError
            key = MagicMock()
            key.__enter__.return_value = valores[hive, access]
            return key

        registry.OpenKey.side_effect = abrir
        registry.QueryValueEx.side_effect = lambda key, name: (key, 1)
        return registry

    def test_detecta_runtime_por_usuario_y_equipo(self):
        for hive, access in ((1, 20), (1, 12), (2, 12)):
            with self.subTest(hive=hive, access=access):
                registry = self.registro({(hive, access): "140.0.3485.54"})
                with patch.dict("sys.modules", winreg=registry):
                    self.assertTrue(desktop.webview2_available())

    def test_rechaza_registro_ausente_vacio_cero_antiguo_o_invalido(self):
        for version in (None, "", "0.0.0.0", "85.0.1000.0", "texto", "140", "1.2.3.4.5"):
            with self.subTest(version=version):
                registry = self.registro({(1, 20): version})
                with patch.dict("sys.modules", winreg=registry):
                    self.assertFalse(desktop.webview2_available())

    def test_registro_invalido_de_usuario_no_oculta_runtime_por_equipo(self):
        registry = self.registro({(1, 20): "0.0.0.0", (2, 12): "140.0.3485.54"})
        with patch.dict("sys.modules", winreg=registry):
            self.assertTrue(desktop.webview2_available())

    def test_sin_runtime_no_inicia_django_y_da_instrucciones(self):
        with patch.object(desktop.sys, "platform", "win32"), \
                patch.object(desktop, "webview2_available", return_value=False), \
                patch.object(desktop, "load_wsgi_application") as cargar:
            with self.assertRaises(desktop.DesktopStartupError) as contexto:
                desktop.run_desktop()
        cargar.assert_not_called()
        self.assertIn("Microsoft Edge WebView2 Runtime", str(contexto.exception))
        self.assertIn("instalador", str(contexto.exception))
        self.assertIn(desktop.WEBVIEW2_DOWNLOAD_URL, str(contexto.exception))

    def test_otras_plataformas_no_consultan_registro_windows(self):
        with patch.object(desktop.sys, "platform", "linux"), \
                patch.object(desktop, "webview2_available") as detectar:
            desktop.ensure_webview2_runtime()
        detectar.assert_not_called()

    def test_error_empaquetado_se_muestra_sin_consola(self):
        messagebox = MagicMock()
        with patch.object(desktop.sys, "frozen", True, create=True), \
                patch.object(desktop.sys, "platform", "win32"), \
                patch("ctypes.windll", messagebox, create=True):
            desktop.report_startup_error(desktop.DesktopStartupError("Falta WebView2"))
        args = messagebox.user32.MessageBoxW.call_args.args
        self.assertIn("Falta WebView2", args[1])
        self.assertEqual(args[2], "PyGebra")

    def test_inicio_windows_selecciona_edgechromium_y_cierra_waitress(self):
        webview = MagicMock()
        server, thread = object(), object()
        with patch.object(desktop.sys, "platform", "win32"), \
                patch.object(desktop, "webview2_available", return_value=True), \
                patch.dict("sys.modules", webview=webview), \
                patch.object(desktop, "load_wsgi_application"), \
                patch.object(desktop, "start_waitress", return_value=(server, thread, "http://127.0.0.1:49173/", None)), \
                patch.object(desktop, "wait_for_server"), \
                patch.object(desktop, "stop_waitress") as cerrar:
            desktop.run_desktop()
        self.assertEqual(webview.start.call_args.kwargs["gui"], "edgechromium")
        self.assertFalse(webview.start.call_args.kwargs["http_server"])
        cerrar.assert_called_once_with(server, thread)

    def test_fallo_de_webview_no_deja_el_servidor_abierto(self):
        webview = MagicMock()
        webview.start.side_effect = RuntimeError("fallo de ventana")
        server, thread = object(), object()
        with patch.object(desktop, "ensure_webview2_runtime"), \
                patch.dict("sys.modules", webview=webview), \
                patch.object(desktop, "load_wsgi_application"), \
                patch.object(desktop, "start_waitress", return_value=(server, thread, "http://127.0.0.1:49173/", None)), \
                patch.object(desktop, "wait_for_server"), \
                patch.object(desktop, "stop_waitress") as cerrar:
            with self.assertRaises(desktop.DesktopStartupError):
                desktop.run_desktop()
        cerrar.assert_called_once_with(server, thread)


if __name__ == "__main__":
    unittest.main()
