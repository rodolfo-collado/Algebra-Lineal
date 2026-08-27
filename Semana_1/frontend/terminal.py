import os

try:
    from colorama import Fore, Style, init
except ImportError:  # Permite ejecutar las pruebas antes de instalar dependencias.
    class _SinColor:
        BLACK = BLUE = CYAN = GREEN = MAGENTA = RED = WHITE = YELLOW = ""
        RESET_ALL = ""

    Fore = _SinColor()
    Style = _SinColor()

    def init(*_args, **_kwargs):
        pass


init(autoreset=True)


def _colorear(texto, color):
    return f"{color}{texto}{Style.RESET_ALL}"


def mostrar_titulo(texto):
    print(_colorear(texto, Fore.CYAN))


def mostrar_exito(texto):
    print(_colorear(texto, Fore.GREEN))


def mostrar_error(texto):
    print(_colorear(texto, Fore.RED))


def mostrar_advertencia(texto):
    print(_colorear(texto, Fore.YELLOW))


def mostrar_info(texto):
    print(_colorear(texto, Fore.BLUE))


def colorear_operacion(texto):
    return _colorear(texto, Fore.MAGENTA)


def limpiar_consola():
    comando = "cls" if os.name == "nt" else "clear"
    os.system(comando)


def pausar():
    input("\nPresione Enter para continuar...")
