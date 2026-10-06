"""Punto de entrada de la aplicación de escritorio para Windows.

El launcher mantiene Django como interfaz: Waitress atiende únicamente en
loopback y pywebview presenta esa URL en una ventana nativa. WebView2 corre en
modo privado; solo las preferencias de presentación sobreviven al cierre, en un
archivo propio que escribe Django.
"""

from __future__ import annotations

import importlib
import os
import queue
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


LOOPBACK_HOST = "127.0.0.1"
DJANGO_SETTINGS_MODULE = "frontend.web.algebra_web.settings"
DESKTOP_ENVIRONMENT = "ALGEBRA_DESKTOP"
PREFERENCES_ENVIRONMENT = "ALGEBRA_PREFERENCIAS"
APP_TITLE = "PyGebra"
# Tamaño máximo al restaurar: la ventana abre maximizada.
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 760
SPI_GETWORKAREA = 0x0030
WINDOW_MIN_SIZE = (760, 560)
WINDOW_BACKGROUND = "#EEF3F0"
ICON_RELATIVE_PATH = Path("assets") / "brand" / "app" / "pygebra.ico"
# Estable entre versiones: Windows agrupa las actualizaciones como la misma aplicación.
APP_USER_MODEL_ID = "PyGebra.Desktop"
STARTUP_TIMEOUT_SECONDS = 10.0
SHUTDOWN_TIMEOUT_SECONDS = 5.0
WAITRESS_THREADS = 4
WEBVIEW2_REGISTRY_KEY = (
    r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
)
WEBVIEW2_DOWNLOAD_URL = "https://developer.microsoft.com/microsoft-edge/webview2/"
# El menú nativo de WebView2 trae también Imprimir, Emoji y «Más herramientas».
CONTEXT_MENU_ITEMS = frozenset({"cut", "copy", "paste", "selectAll"})


class DesktopStartupError(RuntimeError):
    """Indica que la aplicación no pudo preparar su entorno local."""


def webview2_available() -> bool:
    """Consulta el runtime Evergreen por usuario y por equipo, sin importar GUI."""
    import winreg

    # Microsoft registra la instalación por equipo en la vista de 32 bits.
    for hive, view in (
        (winreg.HKEY_CURRENT_USER, winreg.KEY_WOW64_64KEY),
        (winreg.HKEY_CURRENT_USER, winreg.KEY_WOW64_32KEY),
        (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY),
    ):
        try:
            with winreg.OpenKey(
                hive, WEBVIEW2_REGISTRY_KEY, 0, winreg.KEY_READ | view
            ) as key:
                value, _ = winreg.QueryValueEx(key, "pv")
            version = tuple(int(part) for part in value.split("."))
            if len(version) == 4 and version >= (86, 0, 622, 0):
                return True
        except (OSError, ValueError, AttributeError):
            continue
    return False


def ensure_webview2_runtime() -> None:
    """Evita iniciar el servidor o caer en MSHTML cuando falta WebView2."""
    if sys.platform == "win32" and not webview2_available():
        raise DesktopStartupError(
            "Falta Microsoft Edge WebView2 Runtime o necesita actualizarse.\n"
            "Vuelve a ejecutar el instalador de PyGebra con conexión a Internet "
            "para instalarlo. También puedes descargar el runtime Evergreen desde:\n"
            f"{WEBVIEW2_DOWNLOAD_URL}\n"
            "Después, vuelve a abrir PyGebra."
        )


def set_windows_app_user_model_id() -> None:
    """Fija la identidad de Windows antes de crear cualquier ventana.

    pywebview carga ``pygebra.ico`` en la barra de título. La barra de tareas
    no usa ese icono: agrupa el proceso con el acceso directo que lo lanzó.
    Sin un AppUserModelID explícito, ese acceso queda ligado a
    ``AlgebraLineal.exe`` y Windows reutiliza el icono cacheado de esa ruta
    (el símbolo anterior) aunque el ejecutable ya traiga el icono nuevo.
    El instalador declara el mismo identificador y el ``pygebra.ico`` empaquetado.
    """
    if sys.platform != "win32":
        return
    import ctypes

    # En Linux `ctypes` no tiene `windll`. Las pruebas de arranque parchean
    # la plataforma a win32 sin esa API; no debe impedir crear la ventana.
    shell32 = getattr(getattr(ctypes, "windll", None), "shell32", None)
    if shell32 is None:
        return
    shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)


def application_icon_path() -> str | None:
    """Devuelve el icono local si existe junto al código o en la distribución."""
    candidatos: list[Path] = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidatos.append(Path(meipass) / ICON_RELATIVE_PATH)
        candidatos.append(
            Path(sys.executable).resolve().parent / ICON_RELATIVE_PATH
        )
    candidatos.append(Path(__file__).resolve().parent / ICON_RELATIVE_PATH)

    for ruta in candidatos:
        if ruta.is_file():
            return str(ruta)
    return None


def preferences_path() -> Path | None:
    """Archivo de preferencias del usuario, fuera de la instalación y del repositorio.

    En Windows queda en %LOCALAPPDATA%\\PyGebra: las actualizaciones lo conservan y
    la desinstalación no lo borra. No es temporal ni depende del puerto local. Sin
    una carpeta de usuario absoluta devuelve None: nunca se escribe junto al programa.
    """
    base = os.environ.get("LOCALAPPDATA")
    if base and Path(base).is_absolute():
        raiz = Path(base)
    else:
        try:
            raiz = Path.home() / ".local" / "share"
        except RuntimeError:
            return None
    return raiz / APP_TITLE / "preferencias.json"


def configure_desktop_environment() -> None:
    """Fuerza la configuración segura de Django para la distribución desktop."""
    os.environ["DJANGO_SETTINGS_MODULE"] = DJANGO_SETTINGS_MODULE
    os.environ[DESKTOP_ENVIRONMENT] = "1"
    os.environ["DJANGO_DEBUG"] = "0"
    ruta = preferences_path()
    if ruta is not None:
        # Una ruta ya fijada permite aislar pruebas manuales sin tocar las preferencias reales.
        os.environ.setdefault(PREFERENCES_ENVIRONMENT, str(ruta))


def load_wsgi_application() -> Callable[..., Any]:
    """Carga la aplicación WSGI de Django después de fijar el entorno desktop."""
    configure_desktop_environment()

    try:
        modulo = importlib.import_module(
            "frontend.web.algebra_web.wsgi"
        )
        from django.contrib.staticfiles.handlers import StaticFilesHandler

        return StaticFilesHandler(modulo.application)
    except Exception as error:
        raise DesktopStartupError(
            "Django no pudo cargar la aplicación web local."
        ) from error


def build_local_url(host: str, port: int) -> str:
    """Construye una URL HTTP local y rechaza hosts fuera de loopback."""
    if host != LOOPBACK_HOST:
        raise ValueError("La aplicación desktop solo puede usar 127.0.0.1.")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("El puerto local debe estar entre 1 y 65535.")

    return f"http://{host}:{port}/"


def _validate_port(port: int) -> None:
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("El puerto debe ser 0 o estar entre 1 y 65535.")


def create_local_server(
    application: Callable[..., Any],
    *,
    host: str = LOOPBACK_HOST,
    port: int = 0,
) -> tuple[Any, int]:
    """Enlaza Waitress en loopback y devuelve el servidor y su puerto efectivo.

    El puerto 0 delega la elección al sistema operativo dentro de la misma
    operación de bind de Waitress, por lo que no existe una carrera entre
    comprobar un puerto y tratar de ocuparlo después.
    """
    if host != LOOPBACK_HOST:
        raise ValueError("Waitress debe escuchar exclusivamente en 127.0.0.1.")
    _validate_port(port)

    try:
        from waitress import create_server

        server = create_server(
            application,
            host=host,
            port=port,
            threads=WAITRESS_THREADS,
        )
        bound_host, bound_port = server.socket.getsockname()[:2]
    except Exception as error:
        raise DesktopStartupError(
            "Waitress no pudo abrir el servidor local."
        ) from error

    if bound_host != LOOPBACK_HOST or not 1 <= bound_port <= 65535:
        server.close()
        raise DesktopStartupError(
            "Waitress no quedó enlazado correctamente al loopback."
        )

    return server, bound_port


def start_waitress(
    application: Callable[..., Any],
    *,
    host: str = LOOPBACK_HOST,
    port: int = 0,
) -> tuple[Any, threading.Thread, str, queue.SimpleQueue[BaseException]]:
    """Inicia Waitress en un thread y devuelve su URL y canal de errores."""
    server, bound_port = create_local_server(
        application,
        host=host,
        port=port,
    )
    errors: queue.SimpleQueue[BaseException] = queue.SimpleQueue()

    def serve() -> None:
        try:
            server.run()
        except BaseException as error:
            errors.put(error)

    thread = threading.Thread(
        target=serve,
        name="AlgebraLineal-Waitress",
        daemon=False,
    )
    try:
        thread.start()
    except Exception:
        server.close()
        raise

    return server, thread, build_local_url(host, bound_port), errors


def _take_server_error(
    errors: queue.SimpleQueue[BaseException] | None,
) -> BaseException | None:
    if errors is None:
        return None

    try:
        return errors.get_nowait()
    except queue.Empty:
        return None


def _validate_local_url(url: str) -> None:
    partes = urlsplit(url)
    if partes.scheme != "http" or partes.hostname != LOOPBACK_HOST:
        raise ValueError("La readiness solo puede comprobar una URL de loopback.")
    if partes.port is None or not 1 <= partes.port <= 65535:
        raise ValueError("La URL local debe incluir un puerto válido.")


def wait_for_server(
    url: str,
    *,
    timeout: float = STARTUP_TIMEOUT_SECONDS,
    server_thread: threading.Thread | None = None,
    errors: queue.SimpleQueue[BaseException] | None = None,
    opener: Callable[..., Any] = urlopen,
) -> None:
    """Espera una respuesta HTTP real de Django con un timeout finito."""
    _validate_local_url(url)
    if timeout <= 0:
        raise ValueError("El timeout de readiness debe ser positivo.")

    deadline = time.monotonic() + timeout
    ultimo_error: Exception | None = None

    while True:
        server_error = _take_server_error(errors)
        if server_error is not None:
            raise DesktopStartupError(
                "El servidor local terminó durante el arranque."
            ) from server_error

        if server_thread is not None and not server_thread.is_alive():
            raise DesktopStartupError(
                "El servidor local terminó antes de responder."
            )

        restante = deadline - time.monotonic()
        if restante <= 0:
            break

        try:
            request = Request(
                url,
                headers={"Cache-Control": "no-cache"},
            )
            with opener(request, timeout=min(0.5, restante)) as response:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()
                if 200 <= status < 400:
                    return
                ultimo_error = RuntimeError(
                    f"Django respondió con HTTP {status}."
                )
        except HTTPError as error:
            ultimo_error = error
        except (URLError, OSError, TimeoutError) as error:
            ultimo_error = error

        time.sleep(min(0.05, max(0.0, restante)))

    detalle = ""
    if ultimo_error is not None:
        detalle = f" Último error: {ultimo_error}."
    raise DesktopStartupError(
        f"Django no respondió en {timeout:.1f} segundos.{detalle}"
    )


def stop_waitress(
    server: Any,
    thread: threading.Thread,
    *,
    timeout: float = SHUTDOWN_TIMEOUT_SECONDS,
) -> None:
    """Cierra el socket de Waitress y espera que su thread termine."""
    if timeout <= 0:
        raise ValueError("El timeout de shutdown debe ser positivo.")

    deadline = time.monotonic() + timeout
    server.close()
    # `server.close()` deja abiertos los canales HTTP keep-alive. WebView2 puede
    # conservarlos después de cargar la página, así que se cierran antes de
    # esperar al loop de Waitress.
    for channel in list(getattr(server, "active_channels", {}).values()):
        channel.close()

    dispatcher = getattr(server, "task_dispatcher", None)
    if dispatcher is not None:
        dispatcher.shutdown(timeout=max(0.0, deadline - time.monotonic()))

    thread.join(timeout=max(0.0, deadline - time.monotonic()))
    if thread.is_alive():
        raise DesktopStartupError(
            "Waitress no terminó dentro del tiempo de cierre esperado."
        )


def restored_window_geometry() -> tuple[int, int, int, int] | None:
    """Posición y tamaño al restaurar, dentro del área útil del monitor principal.

    Con el escalado de Windows 1100×760 lógicos pueden no caber sobre la barra de
    tareas. Devuelve (x, y, ancho, alto) en unidades lógicas, como pywebview, o None
    fuera de Windows. No recuerda tamaño, posición ni monitor de aperturas previas.
    """
    if sys.platform != "win32":
        return None
    import ctypes

    # RECT propio: ctypes.wintypes no siempre se importa fuera de Windows (pruebas en CI).
    class Rect(ctypes.Structure):
        _fields_ = [(lado, ctypes.c_long) for lado in ("left", "top", "right", "bottom")]

    user32 = getattr(getattr(ctypes, "windll", None), "user32", None)
    area = Rect()
    try:
        if user32 is None or not user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(area), 0):
            return None
        # Sin conciencia de DPI, Windows ya entrega unidades lógicas y GetDpiForSystem da 96.
        escala = (int(user32.GetDpiForSystem()) or 96) / 96
        ancho_util = (area.right - area.left) / escala
        alto_util = (area.bottom - area.top) / escala
        ancho = max(WINDOW_MIN_SIZE[0], min(WINDOW_WIDTH, int(ancho_util * 0.92)))
        alto = max(WINDOW_MIN_SIZE[1], min(WINDOW_HEIGHT, int(alto_util * 0.92)))
        # Si ni min_size cabe, la barra de título sigue visible arriba a la izquierda.
        x = int(area.left / escala + max(0, (ancho_util - ancho) / 2))
        y = int(area.top / escala + max(0, (alto_util - alto) / 2))
    except Exception:
        # Solo es el tamaño al restaurar: nunca debe impedir abrir la ventana.
        return None
    return x, y, ancho, alto


def create_desktop_window(webview_module: Any, url: str) -> Any:
    """Crea la única ventana nativa que presenta la aplicación local.

    Abre maximizada (no en pantalla completa) para no quedar fuera del área útil
    con el escalado de Windows; al restaurarla conserva barra de título y bordes,
    y vuelve a un tamaño que cabe en el monitor principal.
    """
    x, y, ancho, alto = restored_window_geometry() or (None, None, WINDOW_WIDTH, WINDOW_HEIGHT)
    window = webview_module.create_window(
        APP_TITLE,
        url=url,
        x=x,
        y=y,
        width=ancho,
        height=alto,
        min_size=WINDOW_MIN_SIZE,
        resizable=True,
        fullscreen=False,
        maximized=True,
        confirm_close=False,
        text_select=True,
        background_color=WINDOW_BACKGROUND,
    )
    if window is None:
        raise DesktopStartupError("pywebview no pudo crear la ventana.")
    return window


def filter_context_menu(sender: Any, args: Any) -> None:
    """Deja en el menú contextual nativo solo Cortar, Copiar, Pegar y Seleccionar todo.

    Sin acciones de edición (texto sin seleccionar, enlaces, fondo) no se muestra
    ningún menú. Un fallo inesperado también lo oculta: nunca aparece el menú completo.
    """
    try:
        items = args.MenuItems
        for indice in range(items.Count - 1, -1, -1):
            if items[indice].Name not in CONTEXT_MENU_ITEMS:
                items.RemoveAt(indice)
        if items.Count == 0:
            args.Handled = True
    except Exception:
        args.Handled = True


def install_edit_context_menu(window: Any) -> None:
    """Activa el menú contextual de WebView2 filtrado a las acciones de edición.

    pywebview desactiva todos los menús por defecto fuera de debug y no ofrece un
    filtro. ``window.native.webview`` (el control WinForms de WebView2) no es API
    pública de pywebview: si cambia, la ventana sigue sin menú, como antes.
    """

    def configurar(sender: Any, args: Any) -> None:
        if not args.IsSuccess:
            return
        core = sender.CoreWebView2
        core.ContextMenuRequested += filter_context_menu
        core.Settings.AreDefaultContextMenusEnabled = True

    def antes_de_mostrar() -> None:
        # before_show corre en el hilo de la GUI, antes de que WebView2 termine de iniciar.
        window.native.webview.CoreWebView2InitializationCompleted += configurar

    window.events.before_show += antes_de_mostrar


def make_shutdown_callback(
    server: Any,
    thread: threading.Thread,
) -> Callable[[], None]:
    """Crea un cierre idempotente para usarlo desde pywebview y `finally`."""
    lock = threading.Lock()
    cerrado = False

    def shutdown() -> None:
        nonlocal cerrado
        with lock:
            if cerrado:
                return
            stop_waitress(server, thread)
            cerrado = True

    return shutdown


def desktop_debug_enabled() -> bool:
    """Permite diagnósticos detallados durante desarrollo sin mostrarlos en release."""
    return os.environ.get("ALGEBRA_DESKTOP_DEBUG") == "1"


def run_desktop() -> None:
    """Ejecuta el ciclo completo de Django, Waitress y pywebview."""
    set_windows_app_user_model_id()
    server = None
    thread = None
    shutdown = None

    try:
        ensure_webview2_runtime()
        application = load_wsgi_application()
        server, thread, url, errors = start_waitress(application)
        wait_for_server(
            url,
            server_thread=thread,
            errors=errors,
        )

        import webview

        window = create_desktop_window(webview, url)
        # En diagnóstico se conserva el menú completo de pywebview (con Inspeccionar).
        if sys.platform == "win32" and not desktop_debug_enabled():
            install_edit_context_menu(window)
        shutdown = make_shutdown_callback(server, thread)
        window.events.closing += shutdown
        # start() bloquea en el thread principal hasta que el usuario cierra la ventana.
        webview.start(
            gui="edgechromium" if sys.platform == "win32" else None,
            debug=desktop_debug_enabled(),
            http_server=False,
            # El perfil de WebView2 se descarta al cerrar: historial, caché y formularios
            # no llegan a disco. Las preferencias viven en preferences_path().
            private_mode=True,
            # WinForms lee este icono aunque la documentación mencione GTK/QT.
            icon=application_icon_path(),
        )
    except DesktopStartupError:
        raise
    except Exception as error:
        raise DesktopStartupError(
            "La aplicación de escritorio no pudo iniciar correctamente."
        ) from error
    finally:
        if shutdown is not None:
            shutdown()
        elif server is not None and thread is not None:
            stop_waitress(server, thread)


def report_startup_error(error: Exception) -> None:
    """Informa un fallo sin ocultarlo ni mostrar un traceback al usuario final."""
    causa = error.__cause__
    detalle = str(error)
    if causa is not None and str(causa):
        detalle = f"{detalle}\nDetalle técnico: {causa}"
    mensaje = f"{APP_TITLE} no pudo iniciar.\n\n{detalle}"

    if getattr(sys, "frozen", False) and sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, mensaje, APP_TITLE, 0x10)
            return
        except Exception:
            pass

    print(mensaje, file=sys.stderr)
    if desktop_debug_enabled():
        traceback.print_exception(error, file=sys.stderr)


def main() -> int:
    try:
        run_desktop()
    except Exception as error:
        report_startup_error(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
