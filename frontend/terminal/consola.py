"""Utilidades visuales de la terminal: colores, limpieza y pausas."""

import os

from colorama import Fore, Style, init

# autoreset devuelve la consola a su estilo normal despues de cada print.
init(autoreset=True)

_TITULO = Style.BRIGHT + Fore.CYAN
_SUBTITULO = Fore.CYAN
_EXITO = Fore.GREEN
_ERROR = Fore.RED
_ADVERTENCIA = Fore.YELLOW
_INFO = Style.DIM
_OPERACION = Fore.YELLOW


def comando_limpiar():
    # os.name vale "nt" en Windows y "posix" en Linux y macOS.
    return "cls" if os.name == "nt" else "clear"


def limpiar_pantalla():
    os.system(comando_limpiar())


def _escribir(texto, estilo):
    print(f"{estilo}{texto}{Style.RESET_ALL}")


def titulo(texto):
    _escribir(f"\n{texto}", _TITULO)
    _escribir("=" * len(texto), _SUBTITULO)


def subtitulo(texto):
    _escribir(f"\n{texto}", _SUBTITULO)


def exito(texto):
    _escribir(f"\n{texto}", _EXITO)


def error(texto):
    _escribir(f"\n{texto}", _ERROR)


def advertencia(texto):
    _escribir(f"\n{texto}", _ADVERTENCIA)


def info(texto):
    _escribir(texto, _INFO)


def destacar_operacion(texto):
    # Se colorea al imprimir, nunca antes de calcular los anchos de columna.
    return f"{_OPERACION}{texto}{Style.RESET_ALL}"


def pedir(mensaje):
    # El prompt se imprime aparte para que pase por el envoltorio de colorama.
    print(f"{_SUBTITULO}{mensaje}{Style.RESET_ALL}", end="")
    return input()


def pausar():
    print(f"\n{_INFO}Presiona Enter para continuar...{Style.RESET_ALL}", end="")
    input()


def restablecer():
    print(Style.RESET_ALL, end="")
