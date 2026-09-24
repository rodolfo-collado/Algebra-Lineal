"""Contratos web de P13B: AB y Ax dentro de Operaciones con matrices, métodos y seguridad."""

import json
import os
import re
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import Client, SimpleTestCase

from backend.matrices import resolver_coleccion_matrices, resolver_operacion_matrices
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms_matrices import MatricesForm
from frontend.web.calculadora.opciones_matrices import CONFIGURACION, ENTRADAS_DESPLEGADAS
from frontend.web.calculadora.servicios_matrices import operar_matrices, subindice
from tests.test_matrices_web import RUTA, Contenido, datos_matrices
from tests.test_navegacion import Documento

RAIZ = Path(__file__).resolve().parents[1]
ESTATICOS = RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora"


def datos_producto(a=None, b=None, metodo="fila_columna", **extra):
    """POST de AB: las filas de B salen de las columnas de A; columnas_b es la tercera dimensión."""
    a = [[1, 2], [3, 4]] if a is None else a
    b = [[5, 6], [7, 8]] if b is None else b
    datos = datos_matrices("producto", a=a, b=b, columnas_b=str(len(b[0])))
    if metodo is not None:
        datos["metodo"] = metodo
    return datos | extra


def datos_matriz_vector(a=None, x=None, metodo="fila_columna", **extra):
    a = [[1, 2, -1], [0, -5, 3]] if a is None else a
    x = [4, 3, 7] if x is None else x
    datos = datos_matrices("matriz_vector", a=a)
    for i, valor in enumerate(x):
        datos[f"celda_x_{i}_0"] = str(valor)
    if metodo is not None:
        datos["metodo"] = metodo
    return datos | extra


def lineas(html):
    """Las igualdades del procedimiento entrada por entrada, en orden."""
    return [re.sub(r"<[^>]+>", "", linea).strip() for linea in re.findall(r'<li>(.*?)</li>', html, re.S) if " = " in linea]


class PruebasCatalogoP13B(SimpleTestCase):
    def test_los_productos_no_son_herramientas_aparte(self):
        # AB y Ax son operaciones dentro de Operaciones con matrices; la segunda herramienta
        # de la categoría (P14) resuelve Ax = b con x desconocido, no un producto.
        documento = Documento(self.client.get(RUTA))
        enlaces = [a["href"] for a in documento.enlaces_en("Herramientas") if a["href"].startswith("/matrices/")]
        self.assertEqual(enlaces, [RUTA, "/matrices/expresiones/", "/matrices/ecuaciones/"])
        self.assertNotIn("Multiplicación de matrices", [a.get("title") for a in documento.enlaces_en("Herramientas")])

    def test_busqueda_encuentra_los_productos(self):
        consultas = ("multiplicación de matrices", "producto de matrices", "matriz por matriz", "Ax", "matriz vector",
                     "fila columna", "fila vector", "producto punto", "combinación lineal", "columnas")
        for consulta in consultas:
            with self.subTest(consulta=consulta):
                self.assertIn(catalogo.OPERACIONES_MATRICES, catalogo.buscar_herramientas(consulta))
                self.assertContains(self.client.get("/", {"q": consulta}), f'href="{RUTA}"')
        # Las palabras propias de sistemas siguen sin arrastrar a matrices.
        for consulta in ("gauss", "pivote", "binario"):
            self.assertNotIn(catalogo.OPERACIONES_MATRICES, catalogo.buscar_herramientas(consulta))

    def test_descripcion_y_ayuda_mencionan_ab_y_ax(self):
        respuesta = self.client.get(RUTA)
        self.assertContains(respuesta, "calcula AB o Ax")
        self.assertContains(respuesta, "Matriz por vector (Ax)")
        self.assertContains(respuesta, "Multiplicación de matrices")


class PruebasEstructuraProducto(SimpleTestCase):
    def test_metodo_y_columnas_b_deshabilitados_fuera_de_los_productos(self):
        for op in ("suma", "resta", "escalar", "traspuesta"):
            with self.subTest(op=op):
                form = MatricesForm(initial={"operacion": op})
                self.assertTrue(form.fields["metodo"].disabled)
                self.assertTrue(form.fields["columnas_b"].disabled)
                html = self.client.post(RUTA, {"operacion": op, "filas": "2", "columnas": "2", "ajustar": "1"}).content.decode()
                self.assertIn('data-metodos hidden', html)
                self.assertIn('data-dimension="columnas_b" hidden', html)
                self.assertIn('name="columnas_b"', html)
                self.assertRegex(html, r'name="columnas_b"[^>]*disabled')

    def test_producto_pide_tres_dimensiones_con_etiquetas_claras(self):
        form = MatricesForm(initial={"operacion": "producto"})
        self.assertFalse(form.fields["columnas_b"].disabled)
        self.assertFalse(form.fields["metodo"].disabled)
        self.assertEqual(form.fields["filas"].label, "Filas de A")
        self.assertEqual(form.fields["columnas"].label, "Columnas de A = filas de B")
        self.assertEqual(form.fields["columnas_b"].label, "Columnas de B")
        self.assertEqual(form.forma_texto, "A: 2×2 · B: 2×2 → AB: 2×2.")
        self.assertEqual([m["nombre"] for m in form.matrices], ["A", "B"])

    def test_b_toma_sus_filas_de_las_columnas_de_a(self):
        respuesta = self.client.post(RUTA, {"operacion": "producto", "filas": "2", "columnas": "3", "columnas_b": "4", "ajustar": "1"})
        doc = Contenido(respuesta.content.decode())
        celdas_b = sorted(k for k in doc.campos if k.startswith("celda_B_"))
        self.assertEqual(len(celdas_b), 12)
        self.assertEqual(celdas_b[0], "celda_B_0_0")
        self.assertEqual(celdas_b[-1], "celda_B_2_3")
        self.assertEqual(len([k for k in doc.campos if k.startswith("celda_A_")]), 6)
        self.assertEqual(doc.tablas["Matriz B"], [["Matriz B, fila 1, columna 1", "Matriz B, fila 1, columna 2", "Matriz B, fila 1, columna 3", "Matriz B, fila 1, columna 4"]] + doc.tablas["Matriz B"][1:])
        self.assertContains(respuesta, "A: 2×3 · B: 3×4 → AB: 2×4.")
        # No hay cuarta dimensión: la interfaz no puede construir un producto imposible.
        self.assertNotIn("filas_b", doc.campos)

    def test_ax_deriva_x_de_las_columnas_de_a(self):
        respuesta = self.client.post(RUTA, {"operacion": "matriz_vector", "filas": "2", "columnas": "3", "ajustar": "1"})
        doc = Contenido(respuesta.content.decode())
        self.assertEqual(doc.tablas["Vector x"], [["Vector x, componente 1"], ["Vector x, componente 2"], ["Vector x, componente 3"]])
        self.assertEqual(sorted(k for k in doc.campos if k.startswith("celda_x_")), ["celda_x_0_0", "celda_x_1_0", "celda_x_2_0"])
        self.assertContains(respuesta, "A (2×3) · x (3) → Ax (2).")
        self.assertContains(respuesta, 'data-dimension="columnas_b" hidden')
        self.assertContains(respuesta, "Columnas de A = componentes de x")
        for nombre in ("celda_x_0_0", "celda_x_2_0"):
            self.assertEqual(doc.labels[doc.campos[nombre]["id"]], f"Vector x, componente {int(nombre.split('_')[2]) + 1}")

    def test_etiquetas_del_metodo_segun_la_operacion(self):
        producto = self.client.post(RUTA, {"operacion": "producto", "filas": "1", "columnas": "1", "ajustar": "1"}).content.decode()
        etiquetas = re.compile(r'<span data-etiqueta-metodo="(\w+)">([^<]+)</span>')
        self.assertEqual(etiquetas.findall(producto), [("fila_columna", "Fila por columna"), ("columnas", "Por columnas"), ("comparar", "Comparar ambos")])
        self.assertRegex(producto, r'name="metodo" value="fila_columna"[^>]*checked')
        matriz_vector = self.client.post(RUTA, {"operacion": "matriz_vector", "filas": "1", "columnas": "1", "ajustar": "1"}).content.decode()
        self.assertEqual(etiquetas.findall(matriz_vector), [("fila_columna", "Regla fila-vector"), ("columnas", "Combinación lineal de columnas"), ("comparar", "Comparar ambos")])
        self.assertNotIn('data-metodos hidden', matriz_vector)

    def test_aplicar_sin_javascript_crea_los_controles_nuevos_con_su_valor_inicial(self):
        # Desde suma (sin columnas_b ni método en el POST) hacia AB: Aplicar redibuja sin error.
        datos = datos_matrices() | {"operacion": "producto", "ajustar": "1"}
        respuesta = self.client.post(RUTA, datos)
        self.assertNotContains(respuesta, 'role="alert"')
        doc = Contenido(respuesta.content.decode())
        self.assertEqual(doc.campos["columnas_b"]["value"], "2")
        self.assertNotIn("disabled", doc.campos["columnas_b"])
        self.assertEqual(doc.campos["celda_A_1_1"]["value"], "4")
        self.assertEqual(doc.campos["celda_B_0_1"]["value"], "6")

    def test_aplicar_conserva_celdas_al_cambiar_p(self):
        datos = datos_producto(b=[[5, 6, 7], [8, 9, 10]]) | {"columnas_b": "2", "ajustar": "1"}
        doc = Contenido(self.client.post(RUTA, datos).content.decode())
        self.assertEqual(doc.campos["celda_B_1_1"]["value"], "9")
        self.assertNotIn("celda_B_0_2", doc.campos)
        self.assertRegex(str(doc.campos), r"'name': 'columnas_b', 'value': '2'")

    def test_opciones_para_javascript_incluyen_formas_dimensiones_y_metodos(self):
        html = self.client.get(RUTA).content.decode()
        opciones = json.loads(re.search(r'<script id="matrix-options" type="application/json">(.*?)</script>', html, re.S).group(1))
        self.assertEqual(opciones["producto"]["formas"], {"A": ["filas", "columnas"], "B": ["columnas", "columnas_b"]})
        self.assertEqual(opciones["matriz_vector"]["formas"]["x"], ["columnas", None])
        self.assertEqual([m[0] for m in opciones["producto"]["metodos"]], ["fila_columna", "columnas", "comparar"])
        self.assertEqual(opciones["suma"]["metodos"], [])
        self.assertEqual(opciones["producto"]["forma_texto"], "A: {m}×{n} · B: {n}×{p} → AB: {m}×{p}.")
        js = (ESTATICOS / "matrices.js").read_text(encoding="utf-8")
        for fragmento in ("data-dimension", "opcion.formas", "opcion.metodos", "forma_texto", "Vector ${nombre}, componente", "ArrowDown"):
            self.assertIn(fragmento, js)


class PruebasResultadosProducto(SimpleTestCase):
    def calcular(self, datos):
        respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode()
        self.assertNotIn('role="alert"', html)
        self.assertIn('id="resultado"', html)
        return html, Contenido(html)

    def test_dos_por_dos_fila_por_columna(self):
        html, doc = self.calcular(datos_producto())
        self.assertEqual(doc.tablas["Matriz resultado"], [["19", "22"], ["43", "50"]])
        self.assertEqual(doc.tablas["Desarrollo por entradas"], [["1·5 + 2·7", "1·6 + 2·8"], ["3·5 + 4·7", "3·6 + 4·8"]])
        self.assertEqual(lineas(html)[:2], [
            "c₁₁ = fila₁(A) · columna₁(B) = a₁₁b₁₁ + a₁₂b₂₁ = 1·5 + 2·7 = 5 + 14 = 19",
            "c₁₂ = fila₁(A) · columna₂(B) = a₁₁b₁₂ + a₁₂b₂₂ = 1·6 + 2·8 = 6 + 16 = 22",
        ])
        self.assertIn("Fila 1 de AB", html)
        self.assertIn("c₁₁ = 19, c₁₂ = 22", html)
        # Un solo método: su desarrollo va directo dentro de «Ver procedimiento», sin sub-bloques.
        self.assertEqual(html.count('id="procedimiento"'), 1)
        self.assertNotIn("disclosure-nested", html)
        self.assertNotIn("Columna por columna", html)

    def test_dos_por_tres_por_tres_por_dos_y_tres_por_dos_por_dos_por_cuatro(self):
        html, doc = self.calcular(datos_producto(a=[[1, 2, 3], [4, 5, 6]], b=[[7, 8], [9, 10], [11, 12]]))
        self.assertEqual(doc.tablas["Matriz resultado"], [["58", "64"], ["139", "154"]])
        self.assertIn("Multiplicación de matrices · 2×2", html)
        html, doc = self.calcular(datos_producto(a=[[1, 0], [0, 1], [2, 3]], b=[[1, 2, 3, 4], [5, 6, 7, 8]], metodo="columnas"))
        self.assertEqual(doc.tablas["Matriz resultado"], [["1", "2", "3", "4"], ["5", "6", "7", "8"], ["17", "22", "27", "32"]])
        self.assertIn("A: 3×2 · B: 2×4 → AB: 3×4.", html)

    def test_fracciones_exactas_con_la_igualdad_del_enunciado(self):
        html, doc = self.calcular(datos_producto(a=[[3, -1, 5]], b=[[2], [4], ["1/2"]]))
        self.assertEqual(doc.tablas["Matriz resultado"], [["9/2"]])
        self.assertEqual(lineas(html), ["c₁₁ = fila₁(A) · columna₁(B) = a₁₁b₁₁ + a₁₂b₂₁ + a₁₃b₃₁ = 3·2 + (-1)·4 + 5·(1/2) = 6 + (-4) + 5/2 = 9/2"])

    def test_por_columnas_muestra_la_combinacion_lineal_y_el_ensamble(self):
        html, doc = self.calcular(datos_producto(a=[[2, 3, 4], [-1, 5, -3], [6, -2, 8]], b=[[2, 1], [-1, 0], [3, "1/2"]], metodo="columnas"))
        self.assertEqual(doc.tablas["Matriz resultado"], [["13", "4"], ["-16", "-5/2"], ["38", "10"]])
        self.assertIn("Ab₁ = b₁₁a₁ + b₂₁a₂ + b₃₁a₃ = 2a₁ − a₂ + 3a₃", html)
        self.assertIn("Ab₂ = b₁₂a₁ + b₂₂a₂ + b₃₂a₃ = a₁ + 0a₂ + (1/2)a₃", html)
        self.assertEqual(doc.tablas["Columna 1 de A"], [["2"], ["-1"], ["6"]])
        self.assertEqual(doc.tablas["Columna 3 de A multiplicada por 3"], [["12"], ["-9"], ["24"]])
        self.assertEqual(doc.tablas["Columna 1 de AB"], [["13"], ["-16"], ["38"]])
        self.assertEqual(doc.tablas["Columna 2 de AB"], [["4"], ["-5/2"], ["10"]])
        self.assertIn("AB = [Ab₁ Ab₂] =", html)
        self.assertEqual(doc.tablas["Resultado ensamblado"], doc.tablas["Matriz resultado"])
        self.assertNotIn("Entrada por entrada", html)

    def test_comparar_muestra_el_resultado_una_vez_y_los_dos_procedimientos(self):
        html, doc = self.calcular(datos_producto(metodo="comparar"))
        self.assertEqual(html.count('id="results-title"'), 1)
        self.assertEqual(html.count('<table class="matrix-table" aria-label="Matriz resultado"'), 1)
        # Un único resultado y, después, «Ver procedimiento» plegado con un sub-bloque por método.
        self.assertEqual(html.count('id="procedimiento"'), 1)
        self.assertEqual(html.count('class="disclosure disclosure-nested"'), 2)
        self.assertIn(">Fila por columna</h4>", html)
        self.assertIn(">Por columnas</h4>", html)
        self.assertIn("Comparación de métodos", html)
        self.assertLess(html.index('id="final-title"'), html.index('id="procedimiento"'))
        self.assertLess(html.index(">Fila por columna</h4>"), html.index(">Por columnas</h4>"))
        # Ambas lecturas terminan en la misma matriz.
        self.assertEqual(doc.tablas["Resultado del desarrollo"], doc.tablas["Matriz resultado"])
        self.assertEqual(doc.tablas["Resultado ensamblado"], doc.tablas["Matriz resultado"])

    def test_ax_regla_fila_vector(self):
        html, doc = self.calcular(datos_matriz_vector())
        self.assertEqual(doc.tablas["Matriz resultado"], [["3"], ["6"]])
        self.assertEqual(doc.tablas["x"], [["4"], ["3"], ["7"]])
        self.assertIn("Matriz por vector (Ax) · 2 componentes", html)
        self.assertIn("A (2×3) · x (3) → Ax (2).", html)
        self.assertEqual(lineas(html), [
            "(Ax)₁ = fila₁(A) · x = a₁₁x₁ + a₁₂x₂ + a₁₃x₃ = 1·4 + 2·3 + (-1)·7 = 4 + 6 + (-7) = 3",
            "(Ax)₂ = fila₂(A) · x = a₂₁x₁ + a₂₂x₂ + a₂₃x₃ = 0·4 + (-5)·3 + 3·7 = 0 + (-15) + 21 = 6",
        ])
        self.assertIn("Entradas de Ax", html)
        self.assertIn("Regla fila-vector", html)

    def test_ax_combinacion_lineal_de_columnas(self):
        html, doc = self.calcular(datos_matriz_vector(a=[[2, 3, 4], [-1, 5, -3], [6, -2, 8]], x=[2, -1, 3], metodo="columnas"))
        self.assertEqual(doc.tablas["Matriz resultado"], [["13"], ["-16"], ["38"]])
        self.assertIn("Ax = x₁a₁ + x₂a₂ + x₃a₃ = 2a₁ − a₂ + 3a₃", html)
        self.assertEqual(doc.tablas["Columna 2 de A multiplicada por -1"], [["-3"], ["-5"], ["2"]])
        self.assertEqual(doc.tablas["Vector Ax"], [["13"], ["-16"], ["38"]])
        self.assertIn("Combinación lineal de columnas", html)
        self.assertIn("combinación lineal de las columnas de A", html)
        self.assertNotIn("forman el resultado", html)

    def test_ax_comparar_y_fracciones(self):
        html, doc = self.calcular(datos_matriz_vector(a=[["1/2", -1], [3, "2/3"]], x=[4, "-3/2"], metodo="comparar"))
        self.assertEqual(doc.tablas["Matriz resultado"], [["7/2"], ["11"]])
        self.assertEqual(html.count('<table class="matrix-table" aria-label="Matriz resultado"'), 1)
        self.assertIn(">Regla fila-vector</h4>", html)
        self.assertIn(">Combinación lineal de columnas</h4>", html)
        self.assertIn("(Ax)₁ = fila₁(A) · x = a₁₁x₁ + a₁₂x₂ = (1/2)·4 + (-1)·(-3/2) = 2 + 3/2 = 7/2", lineas(html))
        self.assertIn("Ax = x₁a₁ + x₂a₂ = 4a₁ − (3/2)a₂", html)

    def test_ax_una_fila_y_una_columna(self):
        html, doc = self.calcular(datos_matriz_vector(a=[[1, 2, 3]], x=[4, 5, 6]))
        self.assertEqual(doc.tablas["Matriz resultado"], [["32"]])
        self.assertIn("Matriz por vector (Ax) · 1 componente<", html)
        html, doc = self.calcular(datos_matriz_vector(a=[[1], [2], [3]], x=["1/2"], metodo="comparar"))
        self.assertEqual(doc.tablas["Matriz resultado"], [["1/2"], ["1"], ["3/2"]])
        self.assertIn("(Ax)₁ = fila₁(A) · x = a₁₁x₁ = 1·(1/2) = 1/2", lineas(html))

    def test_grupos_abiertos_solo_con_resultados_pequenos(self):
        html, _ = self.calcular(datos_producto())
        self.assertEqual(html.count('<details class="procedure-group" open>'), 2)
        grande = [[1] * 4 for _ in range(4)]
        html, _ = self.calcular(datos_producto(a=grande, b=grande, metodo="comparar"))
        self.assertNotIn('<details class="procedure-group" open>', html)
        self.assertEqual(html.count('<details class="procedure-group">'), 8)
        self.assertEqual(ENTRADAS_DESPLEGADAS, 12)

    def test_resultado_antes_del_procedimiento_plegado_y_recursos_locales(self):
        html, _ = self.calcular(datos_producto(metodo="comparar"))
        self.assertLess(html.index('id="results-title"'), html.index('id="procedimiento"'))
        self.assertLess(html.index('id="final-title"'), html.index('id="procedimiento"'))
        for recurso in ("matrices.js", "teclado.js", "tema.js", "styles.css"):
            self.assertIn(f"/static/calculadora/{recurso}", html)
        self.assertNotIn('src="https://', html)
        self.assertNotIn('href="https://', html)
        self.assertIn('id="matrix-fields" data-perfil="numerico"', html)

    def test_servicio_delega_en_el_backend(self):
        with patch("frontend.web.calculadora.servicios_matrices.resolver_operacion_matrices", wraps=resolver_operacion_matrices) as resolver, \
             patch("frontend.web.calculadora.servicios_matrices.resolver_coleccion_matrices", wraps=resolver_coleccion_matrices) as coleccion:
            producto = operar_matrices({"operacion": "producto", "matrices": {"A": [[1, 2]], "B": [[3], [4]]}, "metodo": "comparar"})
            matriz_vector = operar_matrices({"operacion": "matriz_vector", "matrices": {"A": [[1, 2]]}, "vector": [3, 4], "metodo": "columnas"})
        coleccion.assert_called_once_with("producto", [[[1, 2]], [[3], [4]]])
        resolver.assert_called_once_with("matriz_vector", [[1, 2]], vector=[3, 4])
        self.assertEqual([m["clave"] for m in producto["metodos"]], ["fila_columna", "columnas"])
        self.assertTrue(producto["comparando"])
        self.assertEqual([m["clave"] for m in matriz_vector["metodos"]], ["columnas"])
        self.assertEqual(matriz_vector["matriz"], [["11"]])
        self.assertEqual(matriz_vector["dimensiones_resultado"], "1 componente")

    def test_subindices_legibles_hasta_diez(self):
        self.assertEqual(subindice(2, 3), "₂₃")
        self.assertEqual(subindice(10, 2), "₁₀,₂")
        self.assertEqual(subindice(7), "₇")
        html, _ = self.calcular(datos_producto(a=[[1] * 10], b=[[1] for _ in range(10)]))
        self.assertIn("a₁,₁₀b₁₀,₁", html)

    def test_error_del_backend_llega_legible(self):
        with patch("frontend.web.calculadora.views.operar_matrices", side_effect=ValueError("No se puede calcular AB: A tiene 3 columnas y B tiene 2 filas.")):
            respuesta = self.client.post(RUTA, datos_producto())
        self.assertContains(respuesta, "No se puede calcular AB: A tiene 3 columnas y B tiene 2 filas.")
        self.assertNotContains(respuesta, 'id="resultado"')


class PruebasRechazoProducto(SimpleTestCase):
    def rechazar(self, datos, mensaje=None):
        respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'role="alert"')
        self.assertNotContains(respuesta, 'id="resultado"')
        if mensaje:
            self.assertContains(respuesta, mensaje)
        return respuesta

    def test_metodo_ausente_o_invalido(self):
        self.rechazar(datos_producto(metodo=None), "Selecciona un método.")
        self.rechazar(datos_producto(metodo=""), "Selecciona un método.")
        for metodo in ("gauss", "ambos", "<script>alert(1)</script>"):
            respuesta = self.rechazar(datos_producto(metodo=metodo), "Selecciona un método válido.")
            self.assertNotContains(respuesta, "<script>alert(1)</script>")
        self.rechazar(datos_matriz_vector(metodo=None), "Selecciona un método.")

    def test_columnas_b_ausente_o_invalida(self):
        datos = datos_producto()
        del datos["columnas_b"]
        self.rechazar(datos, "Indica el número de columnas de B.")
        for valor in ("0", "11", "abc", "1.5", "-2"):
            with self.subTest(valor=valor):
                self.rechazar(datos_producto(columnas_b=valor))

    def test_estructura_de_b_manipulada(self):
        # B debe ser n×p: con columnas=2 y columnas_b=2, una B de 3 filas o de 3 columnas no coincide.
        self.rechazar(datos_producto(b=[[5, 6], [7, 8], [9, 10]], columnas_b="2"), "Las celdas recibidas no coinciden")
        self.rechazar(datos_producto(b=[[5, 6, 1], [7, 8, 1]], columnas_b="2"), "Las celdas recibidas no coinciden")
        datos = datos_producto()
        del datos["celda_B_1_1"]
        self.rechazar(datos, "Las celdas recibidas no coinciden")
        self.rechazar(datos_producto(celda_B_2_0="1"), "Las celdas recibidas no coinciden")

    def test_vector_x_manipulado(self):
        self.rechazar(datos_matriz_vector(x=[1, 2]), "Las celdas recibidas no coinciden")
        self.rechazar(datos_matriz_vector(x=[1, 2, 3, 4]), "Las celdas recibidas no coinciden")
        self.rechazar(datos_matriz_vector(celda_x_0_1="1"), "Las celdas recibidas no coinciden")
        self.rechazar(datos_matriz_vector(celda_B_0_0="1"), "Las celdas recibidas no coinciden")
        for valor in ("", "abc", "1/0", "2/", "1,5"):
            with self.subTest(valor=valor):
                self.rechazar(datos_matriz_vector(celda_x_1_0=valor))
        self.rechazar(datos_matriz_vector(celda_x_1_0=""), "Completa vector x, componente 2.")

    def test_celdas_de_b_vacias_o_invalidas(self):
        self.rechazar(datos_producto(celda_B_0_0=""), "Completa matriz b, fila 1, columna 1.")
        self.rechazar(datos_producto(celda_B_1_1="1/0"), "no es un número válido")

    def test_controles_deshabilitados_en_el_calculo_se_rechazan(self):
        # columnas_b y metodo existen siempre, pero deshabilitados no viajan desde el navegador:
        # si llegan en el envío de cálculo de otra operación, el POST fue manipulado.
        mensaje = "Se recibieron campos que no corresponden a la operación seleccionada"
        self.rechazar(datos_matrices(columnas_b="9"), f"{mensaje}: columnas de B.")
        self.rechazar(datos_matrices("resta", metodo="comparar"), f"{mensaje}: método.")
        self.rechazar(datos_matrices("escalar", escalar="2", columnas_b="3", metodo="columnas"), f"{mensaje}: columnas de B, método.")
        self.rechazar(datos_matrices("traspuesta", columnas_b="3", metodo="fila_columna"), f"{mensaje}: columnas de B, método.")
        for datos in (datos_matrices(columnas_b=""), datos_matrices("resta", metodo="")):
            self.rechazar(datos, mensaje)

    def test_aplicar_tolera_los_controles_de_la_estructura_anterior(self):
        # Sin JavaScript, al cambiar de operación el navegador aún envía los controles previos:
        # de AB a suma llegan columnas_b y metodo; de Ax a traspuesta llega metodo. Aplicar redibuja.
        respuesta = self.client.post(RUTA, datos_producto(metodo="comparar") | {"operacion": "suma", "ajustar": "1"})
        self.assertNotContains(respuesta, 'role="alert"')
        doc = Contenido(respuesta.content.decode())
        self.assertEqual(set(doc.tablas), {"Matriz A", "Matriz B"})
        self.assertEqual(doc.campos["celda_B_1_1"]["value"], "8")
        self.assertIn("disabled", doc.campos["columnas_b"])
        self.assertContains(respuesta, 'data-metodos hidden')
        respuesta = self.client.post(RUTA, datos_matriz_vector(metodo="comparar") | {"operacion": "traspuesta", "ajustar": "1"})
        self.assertNotContains(respuesta, 'role="alert"')
        doc = Contenido(respuesta.content.decode())
        self.assertEqual(set(doc.tablas), {"Matriz A"})
        self.assertEqual(doc.campos["celda_A_1_2"]["value"], "3")
        self.assertContains(respuesta, 'data-metodos hidden')
        # El envío de cálculo que sigue, ya sin esos controles, funciona.
        respuesta = self.client.post(RUTA, datos_matrices("traspuesta", a=[[1, 2, -1], [0, -5, 3]]))
        self.assertEqual(Contenido(respuesta.content.decode()).tablas["Matriz resultado"], [["1", "0"], ["2", "-5"], ["-1", "3"]])

    def test_html_se_escapa_en_x_y_en_b(self):
        ataque = '<img src=x onerror="alert(1)">'
        for datos in (datos_matriz_vector(celda_x_0_0=ataque), datos_producto(celda_B_0_0=ataque), datos_matriz_vector(celda_x_0_0=ataque, ajustar="1")):
            respuesta = self.client.post(RUTA, datos)
            self.assertNotContains(respuesta, ataque)
            self.assertContains(respuesta, "&lt;img")

    def test_csrf_exigido_en_los_productos(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(RUTA, datos_producto()).status_code, 403)
        self.assertEqual(cliente.post(RUTA, datos_matriz_vector()).status_code, 403)
        cliente.get(RUTA)
        token = cliente.cookies["csrftoken"].value
        self.assertContains(cliente.post(RUTA, datos_matriz_vector(csrfmiddlewaretoken=token)), 'id="resultado"')

    def test_formulario_entrega_x_como_vector_exacto(self):
        form = MatricesForm(datos_matriz_vector(a=[["1/2", 1, 0]], x=["-2", "1/3", 5], metodo="comparar"))
        self.assertTrue(form.is_valid(), form.errors)
        entrada = form.cleaned_data["entrada"]
        self.assertEqual(entrada["vector"], [-2, Fraction(1, 3), 5])
        self.assertEqual(entrada["matrices"], {"A": [[Fraction(1, 2), 1, 0]]})
        self.assertEqual(entrada["metodo"], "comparar")
        suma = MatricesForm(datos_matrices())
        self.assertTrue(suma.is_valid(), suma.errors)
        self.assertIsNone(suma.cleaned_data["entrada"]["metodo"])
        self.assertNotIn("vector", suma.cleaned_data["entrada"])


class PruebasAccesibilidadProducto(SimpleTestCase):
    def test_labels_reales_y_controles_de_metodo_como_radios(self):
        html = self.client.post(RUTA, datos_matriz_vector(ajustar="1")).content.decode()
        doc = Contenido(html)
        for nombre, attrs in doc.campos.items():
            if nombre.startswith("celda_") or nombre in ("filas", "columnas"):
                self.assertTrue(doc.labels.get(attrs["id"]), nombre)
        self.assertEqual(len(re.findall(r'<input type="radio" name="metodo"', html)), 3)
        self.assertIn("<legend>Método del procedimiento</legend>", html)
        self.assertIn('aria-label="Estructura de las matrices"', html)

    def test_procedimiento_comprensible_sin_color(self):
        html = self.client.post(RUTA, datos_producto(metodo="comparar")).content.decode()
        # Cada igualdad nombra la fila y la columna; los grupos son details/summary reales con texto.
        self.assertIn("c₂₁ = fila₂(A) · columna₁(B)", html)
        self.assertIn('<summary class="procedure-summary">', html)
        self.assertIn('role="region" aria-label="Desarrollo de Ab₁"', html)
        self.assertIn('aria-label="Columnas de A"', html)
        self.assertIn('tabindex="0"', html)
        for etiqueta in ("Columna 1 de A", "Columna 1 de AB", "Resultado ensamblado"):
            self.assertIn(f'aria-label="{etiqueta}"', html)

    def test_configuracion_declara_lo_que_usa_la_interfaz(self):
        for clave, opcion in CONFIGURACION.items():
            with self.subTest(clave=clave):
                for campo in ("formas", "dimensiones", "forma_texto", "metodos", "ayuda_metodos", "expresion", "ayuda"):
                    self.assertIn(campo, opcion)
                for nombre in opcion["matrices"]:
                    self.assertIn(nombre, opcion["formas"])
        self.assertEqual(CONFIGURACION["producto"]["matrices"], ("A", "B"))
        self.assertEqual(CONFIGURACION["matriz_vector"]["matrices"], ("A", "x"))
