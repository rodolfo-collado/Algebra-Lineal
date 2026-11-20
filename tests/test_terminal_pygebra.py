"""Cobertura de los contratos propios de la consola interactiva."""

import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
django.setup()

from textual.widgets import TextArea

from frontend.terminal.adaptador import Tabla, ejecutar, procedimiento
from frontend.terminal.algebra import preparar_algebra
from frontend.terminal.componentes import ArchivosBackend, Paleta, TablaInteractiva
from frontend.terminal.conjuntos import preparar_conjuntos, representacion, resolver_conjuntos
from frontend.terminal.graficas import Grafica
from frontend.terminal.historial import Historial
from frontend.terminal.interfaz import PyGebra
from frontend.terminal.navegacion import HERRAMIENTAS
from frontend.terminal.raices import curva


class HerramientasTerminalTests(unittest.TestCase):
    def test_algebra_usa_el_procedimiento_web(self):
        casos = (
            ("operaciones-vectores", {"operacion": "escalar", "dimension": "2", "@v1": "1 2", "escalar": "2"}),
            ("operaciones-matrices", {
                "expresion": "AB", "cantidad": "2", "metodo": "comparar",
                "nombre_0": "A", "tipo_0": "matriz", "@operando_0": "1 2; 3 4",
                "nombre_1": "B", "tipo_1": "matriz", "@operando_1": "2 0; 0 2",
            }),
            ("reduccion-filas", {"tipo_entrada": "matriz", "@matriz": "1\t2\t4\n2\t5\t9",
                                 "metodo": "comparar", "mostrar": ("procedimiento",)}),
            ("ecuaciones-matriciales", {"@A": "1 2;2 5", "@b": "4 9", "metodo": "cramer",
                                       "metodo_determinante": "directo_2x2"}),
            ("matriz-inversa", {"@A": "1 2;2 5", "metodo": "directo_2x2", "verificar": "si",
                               "funcion_adicional": "vector", "@b": "4 9"}),
            ("determinantes", {"@A": "1 2;3 4", "metodo": "cofactores", "expansion": "fila_2"}),
        )
        for herramienta, datos in casos:
            with self.subTest(herramienta=herramienta):
                respuesta, _ = ejecutar(herramienta, preparar_algebra(herramienta, datos, "."))
                self.assertFalse(respuesta.context_data["form"].errors)
                bloques = procedimiento(respuesta)
                self.assertTrue(bloques)
                if herramienta != "operaciones-vectores":
                    self.assertTrue(any(isinstance(b, Tabla) for b in bloques))

    def test_ambos_modos_de_conjuntos_ofrecen_datos_para_graficar(self):
        casos = (
            ("relaciones-conjuntos", {
                "@modo": "regiones", "venn_nombres": "A, B", "venn_region_1": "1",
                "venn_region_2": "2", "venn_region_3": "3", "expresion": "A ∪ B",
            }, "venn"),
            ("relaciones-conjuntos", {
                "@definiciones": "I = intervalo(0, 3, cerrado, abierto)", "expresion": "I", "punto": "1/2",
            }, "recta"),
            ("cardinalidad-conjuntos", {
                "numero": "2", "modo": "intersecciones", "region_1": "4", "region_2": "3",
                "region_3": "1", "expresion": "A ∪ B",
            }, "venn"),
        )
        for herramienta, datos, tipo in casos:
            with self.subTest(herramienta=herramienta, tipo=tipo):
                respuesta, _ = resolver_conjuntos(herramienta, preparar_conjuntos(herramienta, datos, "."), False)
                self.assertFalse(respuesta.context_data["form"].errors)
                self.assertTrue(getattr(representacion(respuesta.context_data), tipo))
                self.assertTrue(procedimiento(respuesta))

    def test_cada_metodo_de_raices_conserva_sus_iteraciones(self):
        casos = (
            ("biseccion", {"a": "1", "b": "2"}),
            ("regla-falsa", {"a": "1", "b": "2"}),
            ("newton-raphson", {"x0": "2"}),
            ("secante", {"x0": "1", "x1": "2"}),
        )
        for metodo, puntos in casos:
            with self.subTest(metodo=metodo):
                datos = {"funcion": "x^2-2", **puntos}
                respuesta, _ = ejecutar(metodo, datos)
                resultado = respuesta.context_data["resultado"]
                self.assertTrue(resultado["convergio"])
                self.assertTrue(any(isinstance(b, Tabla) for b in procedimiento(respuesta)))
                self.assertEqual(len(curva(metodo, datos, resultado).pasos), len(resultado["iteraciones"]))


class ConsolaInteractivaTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporal = self.enterContext(TemporaryDirectory())
        self.historial = Historial(Path(temporal) / "consola.sqlite3")

    async def test_navega_redimensiona_copia_y_recupera_el_historial(self):
        app = PyGebra(self.historial)
        async with app.run_test(size=(124, 35)) as teclas:
            self.assertTrue(app.screen.has_class("ancha"))
            await teclas.press("slash", "enter", "down", "enter", "left")
            self.assertEqual(app.navegacion.ruta[-1].id, "resolver")
            await teclas.press("right")
            self.assertEqual(app.navegacion.ruta[-1].id, "sistemas-numericos")
            await teclas.resize_terminal(65, 40)
            await teclas.pause()
            self.assertFalse(app.screen.has_class("ancha"))

            await teclas.press("escape", "slash", "up", "enter")
            self.assertTrue(app.debugging)
            await teclas.press("slash", "enter", "down", "enter", "enter", "enter", "4", "2", "enter")
            await teclas.press("down", "space", "enter")
            await app.workers.wait_for_complete()
            await teclas.pause()
            resultado = app.ultimo_resultado
            self.assertEqual(len(resultado.query(TablaInteractiva)), 2)
            resultado.query_one(TablaInteractiva).focus()
            await teclas.press("ctrl+c")
            self.assertEqual(app.clipboard, "42 ÷ 2")

        nueva = PyGebra(self.historial)
        async with nueva.run_test(size=(65, 40)) as teclas:
            await teclas.press("slash", "down", "enter", "enter")
            await teclas.pause()
            ficha = nueva.ultimo_resultado
            self.assertFalse(ficha.collapsed)
            self.assertTrue(ficha.query(TablaInteractiva))
            traza = ficha.query_one(ArchivosBackend)
            self.assertTrue(all(Path(a).is_absolute() for a in traza.archivos))
            self.assertTrue(any(Path(a).name == "conversion.py" for a in traza.archivos))
            self.assertNotIn("biseccion.py", [Path(a).name for a in traza.archivos])

    async def test_previsualizacion_conserva_la_curva_y_admite_simbolos(self):
        app = PyGebra(self.historial)
        async with app.run_test(size=(123, 35)) as teclas:
            app.abrir_herramienta(HERRAMIENTAS["biseccion"])
            await teclas.press("f6")
            self.assertIsInstance(app.screen, Paleta)
            await teclas.press("down", "enter")
            self.assertEqual(app.entrada.value, "x²")
            app.entrada.value = "x^2 - 2"
            grafica = app.query_one("#grafica-viva", Grafica)
            async with asyncio.timeout(5):
                while grafica.curva is None:
                    await teclas.pause(.05)
            anterior = grafica.curva
            app.entrada.value = "x^2 -"
            async with asyncio.timeout(5):
                while not app.query_one("#aviso").display:
                    await teclas.pause(.05)
            self.assertIs(grafica.curva, anterior)
            self.assertIn("Falta un término", str(app.query_one("#aviso").content))

    async def test_entrada_multilinea_resuelve_con_el_teclado(self):
        app = PyGebra(self.historial)
        async with app.run_test(size=(70, 38)) as teclas:
            app.abrir_herramienta(HERRAMIENTAS["determinantes"])
            app.query_one("#editor", TextArea).load_text("1\t2\n3\t4")
            await teclas.press("f2", "enter")
            await app.workers.wait_for_complete()
            await teclas.pause()
            self.assertIn("det(A) = -2", " ".join(
                b for b in app.ultimo_ejercicio.bloques if isinstance(b, str)
            ))
