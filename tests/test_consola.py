"""Pruebas de las utilidades visuales de la terminal."""

import unittest
from unittest import mock

from frontend.terminal import consola
from tests.ayudas import capturar, sin_ansi

MENSAJES = (
    consola.titulo,
    consola.subtitulo,
    consola.exito,
    consola.error,
    consola.advertencia,
    consola.info,
)


class PruebasLimpiezaDePantalla(unittest.TestCase):
    def test_comando_en_windows(self):
        with mock.patch.object(consola.os, "name", "nt"):
            self.assertEqual(consola.comando_limpiar(), "cls")

    def test_comando_fuera_de_windows(self):
        with mock.patch.object(consola.os, "name", "posix"):
            self.assertEqual(consola.comando_limpiar(), "clear")

    def test_limpiar_pantalla_usa_el_comando_de_la_plataforma(self):
        with mock.patch.object(consola.os, "system") as sistema:
            consola.limpiar_pantalla()

        sistema.assert_called_once_with(consola.comando_limpiar())


class PruebasMensajes(unittest.TestCase):
    def test_cada_mensaje_conserva_su_texto(self):
        for funcion in MENSAJES:
            with self.subTest(mensaje=funcion.__name__):
                salida = capturar(funcion, "Mensaje de prueba")
                self.assertIn("Mensaje de prueba", sin_ansi(salida))

    def test_cada_mensaje_restablece_el_estilo(self):
        for funcion in MENSAJES:
            with self.subTest(mensaje=funcion.__name__):
                salida = capturar(funcion, "Mensaje de prueba")
                self.assertTrue(salida.rstrip("\n").endswith("\x1b[0m"))

    def test_titulo_subraya_con_el_mismo_ancho(self):
        lineas = sin_ansi(capturar(consola.titulo, "Matriz")).splitlines()

        self.assertEqual([linea for linea in lineas if linea], ["Matriz", "======"])


class PruebasOperacionDestacada(unittest.TestCase):
    def test_no_altera_el_texto_visible(self):
        operacion = "F2 = F2 - (3)F1"

        self.assertEqual(sin_ansi(consola.destacar_operacion(operacion)), operacion)

    def test_aplica_color_y_lo_cierra(self):
        resaltada = consola.destacar_operacion("F1 <-> F2")

        self.assertTrue(resaltada.startswith("\x1b["))
        self.assertTrue(resaltada.endswith("\x1b[0m"))


if __name__ == "__main__":
    unittest.main()
