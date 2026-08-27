import unittest
from unittest.mock import patch

from Semana_1.frontend.entradas import pedir_sistema_manual
from Semana_1.frontend.menu import menu_sistemas


class PruebasFrontend(unittest.TestCase):
    def test_ingreso_manual_genera_matriz_aumentada(self):
        respuestas = iter([
            "3", "2", "1", "-3", "-5", "0", "0", "1", "1", "3"
        ])

        with patch("builtins.input", side_effect=respuestas):
            matriz = pedir_sistema_manual()

        self.assertEqual(
            matriz,
            [[1, -3, -5, 0], [0, 1, 1, 3]]
        )

    def test_cancelar_submenu_no_crea_una_matriz_nueva(self):
        with patch("Semana_1.frontend.menu.limpiar_consola"):
            with patch("builtins.input", return_value="3"):
                self.assertIsNone(menu_sistemas())

    def test_entrada_directa_invalida_devuelve_none(self):
        respuestas = iter(["1", "x1 + = 3", ""])

        with patch("Semana_1.frontend.menu.limpiar_consola"):
            with patch("Semana_1.frontend.menu.pausar"):
                with patch("builtins.input", side_effect=respuestas):
                    resultado = menu_sistemas()

        self.assertIsNone(resultado)


if __name__ == "__main__":
    unittest.main()
