"""Regresiones de tamaño y centrado del logotipo en celdas de terminal."""

import unittest

from frontend.terminal.marca import logotipo


class MarcaTerminalTests(unittest.TestCase):
    def test_logo_centrado_y_acotado_en_cada_disposicion(self):
        for ancho, alto in ((191, 55), (120, 35), (81, 35), (65, 38), (43, 22)):
            with self.subTest(ancho=ancho, alto=alto):
                filas = logotipo(ancho, alto).plain.splitlines()
                self.assertTrue(all(len(fila) == ancho for fila in filas))
                izquierda = min(len(fila) - len(fila.lstrip()) for fila in filas)
                derecha = min(len(fila) - len(fila.rstrip()) for fila in filas)
                self.assertLessEqual(abs(izquierda - derecha), 1)
                self.assertLessEqual(len(filas), alto // 3)

    def test_paleta_y_contornos_de_la_marca_amplia(self):
        marca = logotipo(191, 55)
        estilos = {span.style for span in marca.spans}
        frente_lila = "#c8a9f6"
        sombras_lilas = {"#7f6d9f", "#af94d7"}
        self.assertIn(frente_lila, estilos)
        self.assertTrue(sombras_lilas <= estilos)
        self.assertIn("#a1e2ae", estilos)
        self.assertGreater(len(marca.plain.splitlines()), 10)
        self.assertEqual(logotipo(70, 20).plain.strip(), "PYGEBRA")
