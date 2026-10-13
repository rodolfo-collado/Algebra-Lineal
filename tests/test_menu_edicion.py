"""Menú de edición del clic derecho: dónde se carga, qué ofrece y con qué datos genera valores.

La interacción (abrir, rellenar, limpiar, seleccionar, foco y teclado matemático) se prueba en
DOM real con ``python -m tests.menu_edicion_browser``; aquí van los contratos del HTML y de los
datos que el navegador recibe del backend.
"""

import json
import os
import re
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import SimpleTestCase

from backend.parser_sistemas import convertir_a_numero
from backend.seguridad_numerica import validar_literal_numerico
from backend.sistemas_numericos import decimal_a_romano, romano_a_decimal
from backend.sistemas_numericos.romanos import LONGITUD_ROMANA_MAXIMA, MAXIMO, TABLA
from frontend.web.calculadora.servicios_romanos import numeracion_romana


STATIC = Path(__file__).resolve().parents[1] / "frontend" / "web" / "calculadora" / "static" / "calculadora"
CON_ENTRADAS = ("/matrices/operaciones/", "/matrices/inversa/", "/matrices/determinantes/", "/matrices/ecuaciones/",
                "/matrices/reduccion/", "/vectores/operaciones/", "/romanos/conversion/")
COMANDOS = ["toda", "fila", "columna", "principal", "secundaria", "superior", "inferior"]
# Mismo intervalo que menu_edicion.js: enteros pequeños para probar procedimientos.
ENTEROS = [str(valor) for valor in range(-9, 10)]


def plantilla_menu(html):
    return re.search(r'<template id="menu-edicion-template">(.*?)</template>', html, re.S).group(1)


def botones(plantilla):
    """(atributos, texto) de cada botón del menú, en orden."""
    return [(dict(re.findall(r'([\w-]+)(?:="([^"]*)")?', atributos)), texto.strip())
            for atributos, texto in re.findall(r"<button([^>]*)>([^<]*)</button>", plantilla)]


def escribir_romano(valor, tabla):
    """La escritura que hace el navegador con la tabla recibida: de mayor a menor, mientras quepa."""
    texto = ""
    for simbolos, cantidad in tabla:
        while valor >= cantidad:
            texto += simbolos
            valor -= cantidad
    return texto


class PruebasMenuEdicion(SimpleTestCase):
    def test_se_carga_una_vez_en_las_herramientas_con_entradas(self):
        for ruta in CON_ENTRADAS:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertContains(respuesta, 'id="menu-edicion-template"', count=1)
                self.assertContains(respuesta, "calculadora/menu_edicion.js", count=1)
                html = respuesta.content.decode()
                # Usa la aplicación atómica y el deshacer de la base compartida.
                self.assertLess(html.index("deshacer_pegado.js"), html.index("menu_edicion.js"))

    def test_no_se_carga_donde_no_hay_entradas_compatibles(self):
        for ruta in ("/", "/bases/conversion/"):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertNotContains(respuesta, "menu-edicion")
                self.assertNotContains(respuesta, "menu_edicion.js")

    def test_acciones_del_menu(self):
        plantilla = plantilla_menu(self.client.get("/matrices/inversa/").content.decode())
        self.assertRegex(plantilla, r'<div class="menu-edicion" role="menu" aria-labelledby="menu-edicion-titulo" data-edicion-menu hidden>')
        items = botones(plantilla)
        self.assertEqual([texto for _, texto in items], [
            "Rellenar aleatoriamente", "Limpiar", "Toda la matriz", "Fila actual", "Columna actual",
            "Diagonal principal", "Diagonal secundaria", "Triangular superior", "Triangular inferior", "Quitar selección",
        ])
        self.assertEqual([a.get("data-accion") or a.get("data-seleccionar") for a, _ in items],
                         ["rellenar", "limpiar", *COMANDOS, "deseleccionar"])
        for atributos, texto in items:
            with self.subTest(item=texto):
                # Acciones locales: nunca envían el formulario ni entran en el orden de Tab de la página.
                self.assertEqual((atributos["type"], atributos["role"], atributos["tabindex"]), ("button", "menuitem", "-1"))
                self.assertNotIn("name", atributos)
        # Restablecer todavía no existe: se añadiría como otro data-accion.
        self.assertNotIn("Restablecer", plantilla)

    def test_comandos_del_menu_y_del_modelo_coinciden(self):
        script = (STATIC / "seleccion_matricial.js").read_text(encoding="utf-8")
        modelo = re.search(r"const COMANDOS = \[([^\]]+)\]", script).group(1)
        self.assertEqual(re.findall(r'"(\w+)"', modelo), COMANDOS)

    def test_sin_chip_seleccionar(self):
        for ruta in CON_ENTRADAS:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertNotContains(respuesta, "matrix-selection")
                self.assertNotContains(respuesta, "data-limpiar-seleccion")

    def test_los_enteros_aleatorios_son_validos_en_las_cuadriculas(self):
        # Matrices, vectores y [A | b] leen cada celda con la misma conversión y la misma protección.
        for texto in ENTEROS:
            with self.subTest(texto=texto):
                validar_literal_numerico(texto)
                self.assertEqual(convertir_a_numero(texto, limitar_entrada=True), int(texto))

    def test_los_extremos_generables_se_calculan_en_cada_herramienta(self):
        envios = {
            "/matrices/inversa/": {"orden": "2", "metodo": "gauss_jordan", "celda_A_0_0": "-9", "celda_A_0_1": "9",
                                   "celda_A_1_0": "9", "celda_A_1_1": "-9"},
            "/matrices/determinantes/": {"orden": "2", "metodo": "reduccion", "celda_A_0_0": "-9", "celda_A_0_1": "0",
                                         "celda_A_1_0": "9", "celda_A_1_1": "-9"},
            "/matrices/ecuaciones/": {"filas": "2", "columnas": "2", "metodo": "gauss_jordan", "celda_A_0_0": "-9",
                                      "celda_A_0_1": "9", "celda_A_1_0": "0", "celda_A_1_1": "-9",
                                      "celda_b_0_0": "9", "celda_b_1_0": "-9"},
            "/vectores/operaciones/": {"operacion": "suma", "dimension": "2", "vectores": "2",
                                       "v1_0": "-9", "v1_1": "9", "v2_0": "0", "v2_1": "-9"},
        }
        for ruta, datos in envios.items():
            with self.subTest(ruta=ruta):
                if ruta == "/matrices/determinantes/":
                    respuesta = self.client.post(ruta, datos)
                    datos["eleccion"] = re.search(r'name="eleccion" value="([0-9a-f]+)"', respuesta.content.decode())[1]
                respuesta = self.client.post(ruta, datos)
                self.assertContains(respuesta, 'id="resultado"')
                for error in ("data-error-field", "data-error-general", 'id="errores-grupo"'):
                    self.assertNotContains(respuesta, error)

    def test_romanos_reciben_la_tabla_y_el_maximo_del_backend(self):
        html = self.client.get("/romanos/conversion/").content.decode()
        datos = json.loads(re.search(r'<script id="datos-numeracion-romana" type="application/json">(.*?)</script>', html, re.S).group(1))
        self.assertEqual(datos, numeracion_romana())
        self.assertEqual(datos, {"maximo": MAXIMO, "tabla": [[entrada.simbolos, entrada.valor] for entrada in TABLA]})
        self.assertRegex(html, r'<div class="field-group" data-numeracion-romana>\s*<label for="id_numero">')

    def test_cada_entero_generable_se_escribe_como_lo_lee_el_backend(self):
        tabla = numeracion_romana()["tabla"]
        for valor in range(1, numeracion_romana()["maximo"] + 1):
            texto = escribir_romano(valor, tabla)
            with self.subTest(valor=valor, texto=texto):
                self.assertEqual(texto, decimal_a_romano(valor).resultado)
                self.assertEqual(romano_a_decimal(texto).resultado, valor)
                self.assertLessEqual(len(texto), LONGITUD_ROMANA_MAXIMA)
                self.assertEqual(decimal_a_romano(str(valor)).valor, valor)


if __name__ == "__main__":
    import unittest
    unittest.main()
