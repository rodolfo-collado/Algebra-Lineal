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
from backend.operandos import OPERANDOS_MAXIMOS


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

    async def test_menu_adapta_las_descripciones_y_la_ayuda_al_espacio(self):
        app = PyGebra(self.historial)
        async with app.run_test(size=(145, 39)) as teclas:
            await teclas.press("slash", "down")
            menu = app.query_one("#menu")
            detalle = app.query_one("#detalle-menu")
            pregunta = app.query_one("#pregunta")
            self.assertRegex(str(menu.content), r"▌\s+/historial\s+Ir a los ejercicios")
            self.assertFalse(detalle.display)
            self.assertFalse(pregunta.display)

            await teclas.resize_terminal(35, 22)
            await teclas.pause()
            self.assertNotIn("Ir a los ejercicios", str(menu.content))
            self.assertTrue(detalle.display)
            self.assertEqual(str(detalle.content), "Ir a los ejercicios")
            await teclas.press("escape")
            self.assertTrue(pregunta.display)

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
            editor = app.query_one("#editor", TextArea)
            aviso = app.query_one("#aviso")
            editor.load_text("1\t2\n3")
            await teclas.pause()
            self.assertIn("fila 2 tiene 1 celda", str(aviso.content))
            await teclas.press("f2")
            self.assertEqual(app.campo_actual().id, "@A")

            editor.load_text("1\t2\n3\tX")
            await teclas.pause()
            self.assertIn("Fila 2, columna 2", str(aviso.content))
            editor.load_text("1\t2\n3\t4")
            await teclas.pause()
            self.assertFalse(aviso.display)
            await teclas.press("f2", "enter")
            await app.workers.wait_for_complete()
            await teclas.pause()
            self.assertIn("det(A) = -2", " ".join(
                b for b in app.ultimo_ejercicio.bloques if isinstance(b, str)
            ))

    async def test_cada_vector_se_valida_antes_de_confirmar_con_f2(self):
        app = PyGebra(self.historial)
        async with app.run_test(size=(70, 38)) as teclas:
            app.decimal = ","
            app.abrir_herramienta(HERRAMIENTAS["operaciones-vectores"])
            await teclas.press("enter", "enter")  # Suma en dimensión 3.
            aviso = app.query_one("#aviso")
            app.entrada.value = "1"
            await teclas.pause()
            self.assertIn("al menos 2 operandos", str(aviso.content))
            await teclas.press("enter")
            self.assertEqual(app.campo_actual().id, "vectores")
            app.entrada.value = "5"
            await teclas.press("enter")

            editor = app.query_one("#editor", TextArea)
            await teclas.press("f2")
            self.assertIn("Hay 0", str(aviso.content))
            incorrectos = (
                ("1 x 3", "Componente 2 de v1"),
                ("1 2", "Escribe 3 componentes para v2. Hay 2"),
                ("1 2 1/0", "Componente 3 de v3"),
            )
            for indice in range(1, 6):
                campo = f"@v{indice}"
                self.assertEqual(app.campo_actual().id, campo)
                if indice <= len(incorrectos):
                    texto, mensaje = incorrectos[indice - 1]
                    editor.load_text(texto)
                    await teclas.pause()
                    self.assertTrue(aviso.display)
                    self.assertIn(mensaje, str(aviso.content))
                    await teclas.press("f2")
                    self.assertEqual(app.campo_actual().id, campo)
                    self.assertIs(app.focused, editor)
                    self.assertEqual(editor.text, texto)
                    self.assertNotIn(campo, app.datos)
                editor.load_text("1,5\t-1/2\n3")
                await teclas.pause()
                self.assertFalse(aviso.display)
                await teclas.press("f2")
            await app.workers.wait_for_complete()
            await teclas.pause()
            self.assertEqual(app.ultimo_ejercicio.datos["@v5"], "1,5\t-1/2\n3")

    async def test_metodo_no_aplicable_muestra_un_aviso_bajo_la_entrada(self):
        app = PyGebra(self.historial)
        async with app.run_test(size=(122, 35)) as teclas:
            app.abrir_herramienta(HERRAMIENTAS["biseccion"])
            app.entrada.value = "1/x"
            await teclas.press("enter", "-", "1", "enter", "1", "enter", "enter", "enter")
            await app.workers.wait_for_complete()
            await teclas.pause()
            self.assertIsNotNone(app.ultimo_ejercicio)
            self.assertIn("Elige extremos", str(app.query_one("#aviso").content))

    async def test_comparar_jacobi_y_gauss_seidel_muestra_sus_tablas(self):
        app = PyGebra(self.historial)
        async with app.run_test(size=(124, 35)) as teclas:
            app.abrir_herramienta(HERRAMIENTAS["metodos-iterativos"])
            editor = app.query_one("#editor", TextArea)
            editor.load_text("4 1\n2 3")
            await teclas.press("f2")
            editor.load_text("1 2")
            await teclas.press("f2", "down", "down", "enter", "enter", "enter", "enter")
            await app.workers.wait_for_complete()
            await teclas.pause()
            ejercicio = app.ultimo_ejercicio
            self.assertEqual(ejercicio.datos["metodo"], "comparar_iterativos")
            tablas = [bloque.titulo for bloque in ejercicio.bloques if isinstance(bloque, Tabla)]
            self.assertIn("Iteraciones de Jacobi", tablas)
            self.assertIn("Iteraciones de Gauss-Seidel", tablas)

    async def test_combinacion_admite_el_maximo_de_generadores_mas_el_objetivo(self):
        app = PyGebra(self.historial)
        datos = {f"@v{i}": "1 0" if i % 2 else "0 1" for i in range(1, OPERANDOS_MAXIMOS + 1)}
        datos.update(operacion="combinacion", dimension="2", vectores=str(OPERANDOS_MAXIMOS))
        datos["@b"] = "3 4"
        async with app.run_test(size=(124, 35)) as teclas:
            app.debugging = True
            app.abrir_herramienta(HERRAMIENTAS["operaciones-vectores"], datos)
            app.paso = len(app.campos()) - 1
            app.mostrar_paso()
            self.assertEqual(app.campo_actual().id, "@b")
            await teclas.press("f2")
            await app.workers.wait_for_complete()
            await teclas.pause()
            ejercicio = app.ultimo_ejercicio
            self.assertTrue(any(isinstance(b, str) and "b es combinación lineal" in b for b in ejercicio.bloques))
            self.assertTrue(any(Path(a).name == "vectores.py" for a in ejercicio.archivos))

    async def test_chat_esta_abajo_del_panel_ancho_y_f7_conserva_el_borrador(self):
        app = PyGebra(self.historial)
        async with app.run_test(size=(145, 39)) as teclas:
            app.abrir_herramienta(HERRAMIENTAS["conversion-romanos"])
            await teclas.press("enter")
            app.entrada.value = "XL"
            await teclas.pause()
            chat = app.query_one("#chat")
            self.assertGreater(app.entrada.region.y, chat.region.y + chat.region.height // 2)
            await teclas.press("f7")
            self.assertEqual(app.focused.id, "resultados")
            await teclas.press("f7")
            self.assertIs(app.focused, app.entrada)
            self.assertEqual(app.entrada.value, "XL")
            await teclas.resize_terminal(65, 38)
            await teclas.pause()
            self.assertGreaterEqual(chat.region.y, app.query_one("#resultados").region.bottom)
            self.assertLessEqual(app.entrada.region.bottom, chat.region.bottom)

            app.abrir_herramienta(HERRAMIENTAS["determinantes"])
            editor = app.query_one("#editor", TextArea)
            editor.load_text("1 2\n3 4")
            await teclas.press("f7")
            self.assertEqual(app.focused.id, "resultados")
            self.assertTrue(app.screen.has_class("lectura"))
            await teclas.press("f7")
            self.assertIs(app.focused, editor)
            self.assertEqual(editor.text, "1 2\n3 4")
