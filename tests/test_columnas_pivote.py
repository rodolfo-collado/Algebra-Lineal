"""Contrato de pivotes compartido por ambos métodos y sus presentaciones."""

import unittest
from unittest.mock import patch

from backend.sistemas import (
    INCONSISTENTE,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
    interpretar_resultado,
    resolver_sistema_gauss,
    resolver_sistema_gauss_jordan,
)
from frontend.terminal.opciones import resolver_por_gauss, resolver_por_gauss_jordan
from frontend.web.calculadora.servicios import resolver_entrada_web
from tests.ayudas import capturar, sin_ansi


CASOS = (
    ("todas", [[2, 1, 5], [1, -1, 1]], [1, 2], SOLUCION_UNICA),
    ("intermedia", [[1, 2, 3, 4], [0, 0, 1, 2]], [1, 3], SOLUCIONES_INFINITAS),
    ("varias", [[0, 1, 3, 0, 2, 5], [0, 0, 0, 1, 4, 6]], [2, 4], SOLUCIONES_INFINITAS),
    ("fila_nula", [[1, 0, 2, 5], [0, 1, 3, 4], [0, 0, 0, 0]], [1, 2], SOLUCIONES_INFINITAS),
    ("unica_con_fila_nula", [[1, 0, 2], [0, 1, 3], [0, 0, 0]], [1, 2], SOLUCION_UNICA),
    ("inconsistente", [[1, 1, 2], [2, 2, 5]], [1], INCONSISTENTE),
    ("solo_aumentada", [[0, 0, 5]], [], INCONSISTENTE),
    ("sin_pivotes", [[0, 0, 0]], [], SOLUCIONES_INFINITAS),
)


class PruebasColumnasPivote(unittest.TestCase):
    def comprobar_metodo(self, resolver):
        for nombre, matriz, columnas, clasificacion in CASOS:
            with self.subTest(caso=nombre):
                resultado = resolver(matriz)
                self.assertEqual(resultado["columnas_pivote"], columnas)
                self.assertEqual(resultado["clasificacion"], clasificacion)
                self.assertTrue(all(type(c) is int for c in resultado["columnas_pivote"]))
                self.assertNotIn(0, resultado["columnas_pivote"])
                self.assertNotIn(len(matriz[0]), resultado["columnas_pivote"])

    def test_gauss(self):
        self.comprobar_metodo(resolver_sistema_gauss)

    def test_gauss_jordan(self):
        self.comprobar_metodo(resolver_sistema_gauss_jordan)

    def test_interpretacion_reutiliza_pivotes_sin_buscar_otra_vez(self):
        # La interpretación recibe una matriz ya reducida y no debe ejecutar
        # ningún algoritmo ni volver a llamar al buscador de pivotes.
        with patch("backend.operaciones_filas.buscar_fila_pivote", side_effect=AssertionError), \
                patch("backend.gauss.buscar_fila_pivote", side_effect=AssertionError):
            resultado = interpretar_resultado([[1, 2, 0, 4], [0, 0, 1, 3]], [(0, 0), (1, 2)], 3)
        self.assertEqual(resultado["columnas_pivote"], [1, 3])

    def test_adaptador_web_conserva_datos_de_ambos_metodos(self):
        for metodo in ("gauss", "gauss_jordan"):
            for nombre, matriz, columnas, _ in CASOS:
                with self.subTest(metodo=metodo, caso=nombre):
                    resultado = resolver_entrada_web("matriz", metodo, matriz_aumentada=matriz)
                    self.assertEqual(resultado["columnas_pivote"], columnas)

    def test_terminal_presenta_pivotes_una_vez_antes_de_interpretar(self):
        for resolver in (resolver_por_gauss, resolver_por_gauss_jordan):
            for nombre, matriz, columnas, _ in CASOS:
                with self.subTest(metodo=resolver.__name__, caso=nombre):
                    salida = sin_ansi(capturar(resolver, matriz))
                    esperado = ", ".join(f"C{c}" for c in columnas) or "Ninguna"
                    self.assertEqual(salida.count("Columnas pivote:"), 1)
                    self.assertIn(f"Columnas pivote: {esperado}\n", salida)
                    self.assertLess(salida.index("Columnas pivote:"), salida.index("Clasificación"))
                    if "Sistema resultante" in salida:
                        self.assertLess(salida.index("Columnas pivote:"), salida.index("Sistema resultante"))


if __name__ == "__main__":
    unittest.main()
