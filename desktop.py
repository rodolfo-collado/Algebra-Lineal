"""Punto de entrada de la aplicación de escritorio para Windows.

El launcher mantiene Django como interfaz: Waitress atiende únicamente en
loopback y pywebview presenta esa URL en una ventana nativa.
"""

from __future__ import annotations

import importlib
import os
import queue
import sys
import threading
import time
import traceback
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


LOOPBACK_HOST = "127.0.0.1"
DJANGO_SETTINGS_MODULE = "frontend.web.algebra_web.settings"
DESKTOP_ENVIRONMENT = "ALGEBRA_DESKTOP"
APP_TITLE = "Calculadora de Álgebra Lineal"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 760
WINDOW_MIN_SIZE = (760, 560)
STARTUP_TIMEOUT_SECONDS = 10.0
SHUTDOWN_TIMEOUT_SECONDS = 5.0
WAITRESS_THREADS = 4


class DesktopStartupError(RuntimeError):
    """Indica que la aplicación no pudo preparar su entorno local."""


def configure_desktop_environment() -> None:
    """Fuerza la configuración segura de Django para la distribución desktop."""
    os.environ["DJANGO_SETTINGS_MODULE"] = DJANGO_SETTINGS_MODULE
    os.environ[DESKTOP_ENVIRONMENT] = "1"
    os.environ["DJANGO_DEBUG"] = "0"


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


def create_desktop_window(webview_module: Any, url: str) -> Any:
    """Crea la única ventana nativa que presenta la aplicación local."""
    window = webview_module.create_window(
        APP_TITLE,
        url=url,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=WINDOW_MIN_SIZE,
        resizable=True,
        fullscreen=False,
        confirm_close=False,
        text_select=True,
        background_color="#F3F6FA",
    )
    if window is None:
        raise DesktopStartupError("pywebview no pudo crear la ventana.")
    return window


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
    server = None
    thread = None
    shutdown = None

    try:
        application = load_wsgi_application()
        server, thread, url, errors = start_waitress(application)
        wait_for_server(
            url,
            server_thread=thread,
            errors=errors,
        )

        import webview

        window = create_desktop_window(webview, url)
        shutdown = make_shutdown_callback(server, thread)
        window.events.closing += shutdown
        # start() bloquea en el thread principal hasta que el usuario cierra la ventana.
        webview.start(
            debug=desktop_debug_enabled(),
            http_server=False,
            private_mode=True,
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
