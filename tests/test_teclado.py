"""Teclado matemático contextual y controles de estructura: infraestructura reutilizable."""

import os
import unittest
from html.parser import HTMLParser
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase

from backend.parser_sistemas import parsear_sistema
from frontend.web.calculadora import teclados
from frontend.web.calculadora.teclados import (
    TECLADO_MATRIZ,
    TECLADO_SISTEMA,
    TECLADOS,
    GrupoTeclas,
    Tecla,
    TecladoContextual,
    variables,
)


RAIZ = Path(__file__).resolve().parents[1]
STATIC = RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora"


class Botones(HTMLParser):
    """Localiza botones y en qué grupo (teclado o estructura) aparecen."""

    def __init__(self, html):
        super().__init__()
        self.botones = []
        self._grupos = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag == "div" and "class" in atributos and "math-keyboard" in atributos["class"].split():
            self._grupos.append(("teclado", atributos))
        elif tag == "div" and atributos.get("aria-label") == "Estructura de la matriz":
            self._grupos.append(("estructura", atributos))
        elif tag == "div":
            self._grupos.append((None, atributos))
        if tag == "button":
            grupos = [nombre for nombre, _ in self._grupos if nombre]
            self.botones.append((grupos[-1] if grupos else None, atributos))

    def handle_endtag(self, tag):
        if tag == "div" and self._grupos:
            self._grupos.pop()


class PruebasTeclas(unittest.TestCase):
    def test_una_tecla_necesita_etiqueta_insercion_y_nombre(self):
        for etiqueta, insercion, nombre in (("", "x", "n"), ("x", "", "n"), ("x", "x", " ")):
            with self.subTest(etiqueta=etiqueta, insercion=insercion, nombre=nombre):
                with self.assertRaises(ValueError):
                    Tecla(etiqueta, insercion, nombre)

    def test_el_retroceso_queda_dentro_de_lo_insertado(self):
        self.assertEqual(Tecla("( )", "()", "Paréntesis", retroceso=1).retroceso, 1)
        with self.assertRaises(ValueError):
            Tecla("( )", "()", "Paréntesis", retroceso=3)

    def test_las_variables_muestran_subindices_e_insertan_sintaxis_del_parser(self):
        teclas = variables(3)
        self.assertEqual([t.etiqueta for t in teclas], ["x₁", "x₂", "x₃"])
        self.assertEqual([t.insercion for t in teclas], ["x1", "x2", "x3"])
        self.assertEqual(teclas[0].nombre, "Variable x1")

    def test_notacion_visible_distinta_de_la_sintaxis_interna(self):
        por_etiqueta = {tecla.etiqueta: tecla.insercion for tecla in TECLADO_SISTEMA.teclas}
        self.assertEqual(por_etiqueta["−"], "-")
        self.assertEqual(por_etiqueta["a⁄b"], "/")
        self.assertEqual(por_etiqueta["x₁"], "x1")
        self.assertEqual(por_etiqueta["; nueva ecuación"], ";\n")

    def test_lo_que_inserta_el_teclado_lo_entiende_el_parser(self):
        tecla = {t.nombre: t.insercion for t in TECLADO_SISTEMA.teclas}
        texto = (
            "2" + tecla["Variable x1"] + tecla["Más"] + tecla["Variable x2"] + tecla["Igual"] + "3"
            + tecla["Separar la siguiente ecuación"]
            + tecla["Variable x1"] + tecla["Menos"] + "1" + tecla["Barra de fracción"] + "2"
            + tecla["Variable x2"] + tecla["Igual"] + "1"
        )
        matriz = parsear_sistema(texto)
        self.assertEqual(len(matriz), 2)
        self.assertEqual([str(valor) for valor in matriz[1]], ["1", "-1/2", "1"])

    def test_registro_de_teclados_sin_teclas_vacias_ni_duplicadas(self):
        self.assertEqual(set(TECLADOS), {"sistema", "matriz"})
        for teclado in TECLADOS.values():
            with self.subTest(teclado=teclado.id):
                self.assertIsInstance(teclado, TecladoContextual)
                self.assertTrue(teclado.grupos)
                etiquetas = [tecla.etiqueta for tecla in teclado.teclas]
                self.assertEqual(len(etiquetas), len(set(etiquetas)))
                for grupo in teclado.grupos:
                    self.assertIsInstance(grupo, GrupoTeclas)
                    self.assertTrue(grupo.teclas)
        # El teclado de la cuadrícula solo lleva lo que cabe en una celda numérica.
        self.assertEqual([t.insercion for t in TECLADO_MATRIZ.teclas], ["-", "/"])
        self.assertFalse(hasattr(teclados, "TECLADO_LIMITES"))


class PruebasTecladoEnPantalla(SimpleTestCase):
    def test_el_modulo_de_sistemas_incluye_teclados_ocultos_por_defecto(self):
        html = self.client.get("/sistemas/").content.decode("utf-8")
        self.assertIn(
            'class="math-keyboard" data-teclado="sistema" data-teclado-para="system-fields"',
            html,
        )
        self.assertIn(
            'class="math-keyboard" data-teclado="matriz" data-teclado-para="matrix-fields"',
            html,
        )
        self.assertIn('role="group" aria-label="Teclado matemático" hidden>', html)

        botones = [attrs for grupo, attrs in Botones(html).botones if grupo == "teclado"]
        self.assertEqual(len(botones), len(TECLADO_SISTEMA.teclas) + len(TECLADO_MATRIZ.teclas))
        for boton in botones:
            self.assertEqual(boton["type"], "button")
            self.assertTrue(boton["data-insercion"])
            self.assertTrue(boton["aria-label"])
        self.assertIn("system-fields", html)
        self.assertIn("matrix-fields", html)

    def test_los_controles_de_estructura_van_aparte_del_teclado(self):
        html = self.client.get("/sistemas/").content.decode("utf-8")
        estructura = [attrs for grupo, attrs in Botones(html).botones if grupo == "estructura"]
        self.assertEqual(
            sorted(boton["aria-label"] for boton in estructura),
            ["Agregar una ecuación", "Agregar una variable", "Quitar una ecuación", "Quitar una variable"],
        )
        for boton in estructura:
            self.assertEqual(boton["type"], "button")
            self.assertIn("hidden", boton)
            self.assertNotIn("data-insercion", boton)

    def test_el_inicio_no_muestra_teclado(self):
        self.assertNotContains(self.client.get("/"), "math-keyboard")

    def test_scripts_locales_del_teclado_y_la_estructura(self):
        teclado = (STATIC / "teclado.js").read_text(encoding="utf-8")
        self.assertIn("setRangeText", teclado)
        self.assertIn("data-insercion", teclado)
        self.assertIn("data-teclado-para", teclado)
        matriz = (STATIC / "matriz.js").read_text(encoding="utf-8")
        self.assertIn("data-estructura", matriz)
        self.assertIn("renderMatrix", matriz)
        html = self.client.get("/sistemas/").content.decode("utf-8")
        self.assertIn("calculadora/teclado.js", html)
        self.assertIn("calculadora/matriz.js", html)


if __name__ == "__main__":
    unittest.main()
