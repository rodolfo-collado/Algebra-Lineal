"""P26.3: separación presentacional de [A | B], sin una herramienta de inversa."""

import os
from html.parser import HTMLParser

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import aumentar_matrices, matriz_identidad
from frontend.web.calculadora.forms import SistemaForm
from frontend.web.calculadora.servicios import adaptar_pasos, formatear_matriz


class TablasAumentadas(HTMLParser):
    """Lee las celdas reales, sus valores y la separación de cada fila."""

    def __init__(self, html):
        super().__init__()
        self.tablas = []
        self.tabla = self.fila = self.celda = None
        self.feed(html)

    def handle_starttag(self, tag, atributos):
        atributos = dict(atributos)
        if tag == "table" and "matrix-table" in atributos.get("class", "").split():
            self.tabla = {"etiqueta": atributos.get("aria-label"), "filas": []}
            self.tablas.append(self.tabla)
        elif self.tabla is not None and tag == "tr":
            self.fila = []
            self.tabla["filas"].append(self.fila)
        elif self.tabla is not None and tag == "td":
            self.celda = {"clases": atributos.get("class", "").split(), "valor": ""}
            self.fila.append(self.celda)

    def handle_data(self, texto):
        if self.celda is not None:
            self.celda["valor"] += texto

    def handle_endtag(self, tag):
        if tag == "td":
            self.celda = None
        elif tag == "table":
            self.tabla = self.fila = None


def resultado_bloques():
    """Fixture de infraestructura que reutiliza el motor y los pasos existentes."""
    aumentada = aumentar_matrices([[3, 4], [5, 6]], matriz_identidad(2))
    reducida, pasos, pivotes = aplicar_gauss_jordan(aumentada, columnas_pivote=2)
    return {
        "metodo": "Gauss-Jordan",
        "columnas_izquierda": 2,
        "matriz_inicial": formatear_matriz(aumentada),
        "pasos": adaptar_pasos(pasos),
        "matriz_final": formatear_matriz(reducida),
        "columnas_pivote": [columna + 1 for _, columna in pivotes],
        "etiqueta_matriz": "Matriz reducida",
        "mostrar_sistema_resultante": False,
        "sustitucion": [],
    }


class PruebasPresentacionBloques(SimpleTestCase):
    def comprobar_corte(self, tabla, izquierda, derecha):
        for fila in tabla["filas"]:
            self.assertEqual(len(fila), izquierda + derecha)
            self.assertEqual(
                [i for i, celda in enumerate(fila) if "constant" in celda["clases"]],
                [izquierda],
            )
            self.assertEqual(
                [i for i, celda in enumerate(fila) if "augmented" in celda["clases"]],
                list(range(izquierda + 1, izquierda + derecha)),
            )

    def test_a_barra_b_conserva_html_predeterminado_con_corte_explicito(self):
        contexto = {"matriz": [[1, 2, 3], [4, 5, 6]], "columnas_pivote": [1, 2]}
        predeterminado = render_to_string("calculadora/components/matrix.html", contexto)
        explicito = render_to_string(
            "calculadora/components/matrix.html", contexto | {"columnas_izquierda": 2}
        )
        self.assertEqual(predeterminado, explicito)
        tablas = TablasAumentadas(predeterminado).tablas
        self.assertEqual(len(tablas), 1)
        self.comprobar_corte(tablas[0], 2, 1)

    def test_a_barra_i_usa_una_tabla_y_separa_antes_del_bloque_derecho(self):
        matriz = aumentar_matrices([[3, 4], [5, 6]], matriz_identidad(2))
        html = render_to_string(
            "calculadora/components/matrix.html",
            {"matriz": formatear_matriz(matriz), "columnas_izquierda": 2},
        )
        tablas = TablasAumentadas(html).tablas
        self.assertEqual(len(tablas), 1)
        self.comprobar_corte(tablas[0], 2, 2)
        self.assertEqual(
            [[celda["valor"] for celda in fila] for fila in tablas[0]["filas"]],
            [["3", "4", "1", "0"], ["5", "6", "0", "1"]],
        )

    def test_varias_columnas_derechas_no_generan_separadores_adicionales(self):
        for izquierda, derecha in ((1, 3), (2, 3), (3, 2)):
            with self.subTest(izquierda=izquierda, derecha=derecha):
                matriz = [list(range(izquierda + derecha)) for _ in range(2)]
                html = render_to_string(
                    "calculadora/components/matrix.html",
                    {"matriz": matriz, "columnas_izquierda": izquierda},
                )
                self.comprobar_corte(TablasAumentadas(html).tablas[0], izquierda, derecha)

    def test_matriz_generica_sin_metadata_no_tiene_separacion(self):
        html = render_to_string("calculadora/components/matriz.html", {"matriz": [[1, 2, 3]]})
        self.assertEqual(
            [celda["clases"] for celda in TablasAumentadas(html).tablas[0]["filas"][0]],
            [[], [], []],
        )

    def test_matriz_generica_admite_corte_sin_contexto_de_sistemas(self):
        html = render_to_string(
            "calculadora/components/matriz.html",
            {"matriz": [[1, 0, "1/2", "-3/2"]], "columnas_izquierda": 2},
        )
        tabla = TablasAumentadas(html).tablas[0]
        self.comprobar_corte(tabla, 2, 2)
        self.assertEqual([celda["valor"] for celda in tabla["filas"][0]], ["1", "0", "1/2", "-3/2"])

    def test_pivotes_y_corte_son_metadata_independiente(self):
        html = render_to_string(
            "calculadora/components/matrix.html",
            {"matriz": [[0, 1, 4, 5]], "columnas_izquierda": 2, "columnas_pivote": [2]},
        )
        tabla = TablasAumentadas(html).tablas[0]
        self.comprobar_corte(tabla, 2, 2)
        self.assertEqual(
            [i for i, celda in enumerate(tabla["filas"][0]) if "pivot" in celda["clases"]],
            [1],
        )

    def test_corte_no_interfiere_con_escape_html(self):
        html = render_to_string(
            "calculadora/components/matrix.html",
            {"matriz": [[1, "<script>alert(1)</script>", 2]], "columnas_izquierda": 1},
        )
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>", html)
        self.comprobar_corte(TablasAumentadas(html).tablas[0], 1, 2)

    def test_procedimiento_mantiene_corte_y_valores_en_todos_los_pasos(self):
        resultado = resultado_bloques()
        html = render_to_string(
            "calculadora/modules/sistemas/_procedimiento_metodo.html",
            {"resultado": resultado, "mostrar": ["procedimiento", "pivotes"]},
        )
        tablas = TablasAumentadas(html).tablas
        self.assertEqual(len(tablas), 2 * len(resultado["pasos"]) + 1)
        for indice, paso in enumerate(resultado["pasos"]):
            for desplazamiento, clave in ((0, "antes"), (1, "despues")):
                tabla = tablas[2 * indice + desplazamiento]
                self.comprobar_corte(tabla, 2, 2)
                self.assertEqual(
                    [[celda["valor"] for celda in fila] for fila in tabla["filas"]],
                    paso[clave],
                )
            self.assertInHTML(f'<code>{paso["operacion"]}</code>', html)
        self.comprobar_corte(tablas[-1], 2, 2)
        self.assertEqual(
            [[celda["valor"] for celda in fila] for fila in tablas[-1]["filas"]],
            [["1", "0", "-3", "2"], ["0", "1", "5/2", "-3/2"]],
        )

    def test_corte_comun_se_conserva_si_resultado_no_incluye_metadata(self):
        resultado = resultado_bloques()
        del resultado["columnas_izquierda"]
        html = render_to_string(
            "calculadora/modules/sistemas/_procedimiento_metodo.html",
            {"resultado": resultado, "columnas_izquierda": 2, "mostrar": ["procedimiento"]},
        )
        for tabla in TablasAumentadas(html).tablas:
            self.comprobar_corte(tabla, 2, 2)

    def test_corte_del_resultado_prevalece_sobre_contexto_comun(self):
        html = render_to_string(
            "calculadora/modules/sistemas/_bloques_metodo.html",
            {"resultado": resultado_bloques(), "columnas_izquierda": 3, "mostrar": []},
        )
        self.comprobar_corte(TablasAumentadas(html).tablas[0], 2, 2)

    def test_pagina_completa_conserva_corte_en_inicial_pasos_y_final(self):
        for metadata_comun in (False, True):
            with self.subTest(metadata_comun=metadata_comun):
                resultado = resultado_bloques()
                contexto = {
                    "form": SistemaForm(),
                    "resultado": resultado,
                    "resultados": [resultado],
                    "mostrar": ["procedimiento", "pivotes"],
                    "matrix_values": {},
                    "csrf_token": "a" * 64,
                }
                if metadata_comun:
                    contexto["columnas_izquierda"] = resultado.pop("columnas_izquierda")
                html = render_to_string("calculadora/modules/sistemas/index.html", contexto)
                tablas = TablasAumentadas(html).tablas
                self.assertEqual(len(tablas), 2 * len(resultado["pasos"]) + 2)
                self.assertEqual(tablas[0]["etiqueta"], "Matriz inicial")
                self.assertEqual(tablas[-1]["etiqueta"], "Matriz reducida")
                for tabla in tablas:
                    self.comprobar_corte(tabla, 2, 2)
