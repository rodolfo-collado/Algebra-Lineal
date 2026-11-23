"""Regresiones del logotipo compacto en celdas de terminal."""

import unittest

from frontend.terminal.marca import logotipo


class MarcaTerminalTests(unittest.TestCase):
    def test_logo_compacto_sin_margen_izquierdo_en_cada_disposicion(self):
        for ancho, alto in ((191, 55), (120, 35), (81, 35), (65, 38), (43, 22), (31, 38)):
            with self.subTest(ancho=ancho, alto=alto):
                filas = logotipo(ancho, alto).plain.splitlines()
                self.assertTrue(filas[0][0].strip())
                self.assertLessEqual(max(map(len, filas)), min(28, ancho - 6))
                self.assertLessEqual(len(filas), 3)

    def test_paleta_y_contornos_de_la_marca_compacta(self):
        marca = logotipo(191, 55)
        colores = {color for span in marca.spans for color in span.style.split(" on ")}
        self.assertTrue({"#c8a9f6", "#7f6d9f", "#af94d7", "#a1e2ae"} <= colores)
        claro = logotipo(191, 55, claro=True)
        self.assertEqual(claro.plain, marca.plain)
        self.assertNotEqual(claro.spans, marca.spans)
        self.assertEqual(len(marca.plain.splitlines()), 3)
        self.assertEqual(logotipo(70, 20).plain, "PYGEBRA")
