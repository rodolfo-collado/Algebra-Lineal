"""Jerarquía de resultados, compatibilidad del historial y desplazamiento."""

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
django.setup()

from frontend.terminal.adaptador import Linea, ProcedimientoHTML, Tabla
from frontend.terminal.componentes import Ficha
from frontend.terminal.graficas import Curva, MarcaGrafica
from frontend.terminal.historial import Ejercicio, Historial
from frontend.terminal.interfaz import PyGebra


class PresentacionTerminalTests(unittest.TestCase):
    def test_muestra_respuesta_antes_del_procedimiento_y_conserva_leyendas(self):
        parser = ProcedimientoHTML()
        parser.feed("""
        <section id="resultado">
          <header><h2>Romano → arábigo</h2></header>
          <details class="disclosure-procedure">
            <summary><h3>Ver procedimiento</h3></summary>
            <table>
              <caption class="sr-only">Valor de cada símbolo</caption>
              <thead><tr><th>Símbolo</th><th>Valor</th></tr></thead>
              <tbody><tr><th scope="row">XL</th><td>40</td></tr></tbody>
            </table>
          </details>
          <section class="panel-final">
            <h3>Resultado</h3>
            <p class="classification-value">XL = 40</p>
          </section>
        </section>""")
        parser.close()
        self.assertEqual([b.estilo for b in parser.bloques[:-1]],
                         ["titulo", "resultado", "valor", "seccion"])
        self.assertEqual(parser.bloques[-1], Tabla("Valor de cada símbolo", ("Símbolo", "Valor"), (("XL", "40"),)))

    def test_conserva_estilos_y_marcas_al_guardar_y_recupera_registros_previos(self):
        curva = Curva("f(x) = x", (-1., 1.), (-1., 1.), marcas=(MarcaGrafica("a", -1., -1.),))
        original = Ejercicio("biseccion", "Bisección", {}, (Linea("Método no aplicable", "aviso"),), grafica=curva)

        actual = Ejercicio.leer(original.serializar())
        self.assertEqual(actual.bloques[0].estilo, "aviso")
        self.assertEqual(actual.grafica.marcas, curva.marcas)

        legado = json.loads(original.serializar())
        legado["bloques"] = ["Método no aplicable", "Ver procedimiento"]
        legado["grafica"].pop("marcas")
        previo = Ejercicio.leer(json.dumps(legado))
        self.assertEqual([(str(b), b.estilo) for b in previo.bloques],
                         [("Método no aplicable", "aviso"), ("Procedimiento", "seccion")])
        self.assertEqual(previo.grafica.marcas, ())


class HistorialDesplazableTests(unittest.IsolatedAsyncioTestCase):
    async def test_avanza_por_un_resultado_largo_con_teclado(self):
        raiz = self.enterContext(TemporaryDirectory())
        historial = Historial(Path(raiz) / "historial.sqlite3")
        historial.abrir()
        bloques = (Linea("Procedimiento", "seccion"), *(Linea(f"Paso {n}") for n in range(1, 80)))
        historial.agregar(Ejercicio("conversion-romanos", "Conversión romana", {}, bloques))

        app = PyGebra(historial)
        async with app.run_test(size=(74, 32)) as teclas:
            ficha = app.query_one(Ficha)
            ficha.collapsed = False
            await teclas.pause()
            panel = app.query_one("#resultados")
            panel.focus()
            panel.scroll_home(animate=False, immediate=True)
            await teclas.pause()
            await teclas.press("pagedown")
            await teclas.pause()
            self.assertGreater(panel.scroll_y, 0)
