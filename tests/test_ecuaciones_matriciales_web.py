"""Contratos web de P14: Resolver Ax = b como segunda herramienta de Matrices, estructura, resultado y seguridad."""

import os
import re
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.http import QueryDict
from django.test import Client, SimpleTestCase
from django.urls import resolve, reverse
from django.utils.html import strip_tags

from backend.ecuaciones_matriciales import resolver_ecuacion_matricial
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms_ecuaciones import EcuacionMatricialForm
from frontend.web.calculadora.opciones_ecuaciones import METODO_PREDETERMINADO, METODOS, forma_texto
from frontend.web.calculadora.servicios import resolver_entrada_web
from frontend.web.calculadora.servicios_ecuaciones import ecuacion_vectorial, incognitas, resolver_ecuacion_web
from tests.test_matrices_web import RUTA as RUTA_OPERACIONES, Contenido
from tests.test_navegacion import Documento

RUTA = "/matrices/ecuaciones/"
RAIZ = Path(__file__).resolve().parents[1]
ESTATICOS = RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora"

UNICA = ([[1, 1], [1, -1]], [5, 1])
UNICA_RECTANGULAR = ([[1, 0], [0, 1], [1, 1]], [2, 3, 5])
INFINITAS = ([[1, 0, 1], [0, 1, 1]], [2, 3])
INCONSISTENTE = ([[1, 0], [0, 1], [1, 1]], [2, 3, 6])
FRACCIONES = ([[2, 0], [0, 3]], [1, 1])


def datos_ecuacion(a=None, b=None, metodo=METODO_PREDETERMINADO, **extra):
    """POST de Ax = b: solo las dimensiones de A; b lleva una componente por fila y x no viaja."""
    a = UNICA[0] if a is None else a
    b = UNICA[1] if b is None else b
    datos = {"filas": str(len(a)), "columnas": str(len(a[0]))}
    if metodo is not None:
        datos["metodo"] = metodo
    for i, fila in enumerate(a):
        for j, valor in enumerate(fila):
            datos[f"celda_A_{i}_{j}"] = str(valor)
    for i, valor in enumerate(b):
        datos[f"celda_b_{i}_0"] = str(valor)
    return datos | extra


def texto_resultado(html):
    """Texto plano del resultado, con un espacio entre elementos y espacios normalizados."""
    if 'id="resultado"' not in html:
        return ""
    return " ".join(strip_tags(re.sub(r">\s*<", "> <", html[html.index('id="resultado"'):])).split())


class PruebasCatalogoEcuaciones(SimpleTestCase):
    def test_segunda_herramienta_de_matrices_con_ruta_propia(self):
        self.assertEqual(
            catalogo.herramientas_de(catalogo.MATRICES),
            (catalogo.OPERACIONES_MATRICES, catalogo.ECUACIONES_MATRICIALES),
        )
        self.assertTrue(catalogo.ECUACIONES_MATRICIALES.disponible)
        self.assertEqual(catalogo.ECUACIONES_MATRICIALES.nombre, "Resolver Ax = b")
        self.assertEqual(reverse("calculadora:ecuaciones-matriciales"), RUTA)
        self.assertEqual(catalogo.herramienta_por_ruta(resolve(RUTA)), catalogo.ECUACIONES_MATRICIALES)
        self.assertEqual(catalogo.ECUACIONES_MATRICIALES.relacionadas, ())
        # Operaciones con matrices sigue igual: Ax con x conocido no cambia de significado.
        self.assertEqual(catalogo.OPERACIONES_MATRICES.ruta, RUTA_OPERACIONES)
        self.assertIn("ax", catalogo.OPERACIONES_MATRICES.palabras_clave)

    def test_inicio_sidebar_acceso_rapido_y_breadcrumbs(self):
        inicio = self.client.get("/")
        documento = Documento(inicio)
        for region in ("Herramientas", "Acceso rápido"):
            self.assertIn(RUTA, [a["href"] for a in documento.enlaces_en(region)])
        self.assertContains(inicio, "Resolver Ax = b")
        self.assertContains(inicio, "la ecuación matricial Ax = b")
        respuesta = self.client.get(RUTA)
        doc = Documento(respuesta)
        self.assertEqual([a["href"] for a in doc.enlaces_en("Ruta de navegación")], ["/", "/#algebra-lineal", "/#matrices"])
        self.assertContains(respuesta, '<span aria-current="page">Resolver Ax = b</span>', html=True)
        self.assertEqual([a["href"] for a in doc.enlaces_en("Herramientas") if a.get("aria-current") == "page"], [RUTA])
        self.assertTrue(doc.categorias["matrices"])
        enlaces = [a["href"] for a in doc.enlaces_en("Herramientas") if a["href"].startswith("/matrices/")]
        self.assertEqual(enlaces, [RUTA_OPERACIONES, RUTA])
        self.assertNotContains(respuesta, "Herramientas relacionadas")

    def test_busqueda_por_ecuacion_matricial_y_conceptos(self):
        consultas = ("ecuación matricial", "ecuaciones matriciales", "Ax=b", "ax = b", "resolver Ax=b", "matriz aumentada",
                     "sistema equivalente", "vector b", "incógnita x", "conjunto generado", "solución única",
                     "soluciones infinitas", "inconsistente", "combinación lineal")
        for consulta in consultas:
            with self.subTest(consulta=consulta):
                self.assertIn(catalogo.ECUACIONES_MATRICIALES, catalogo.buscar_herramientas(consulta))
                self.assertContains(self.client.get("/", {"q": consulta}), f'href="{RUTA}"')
        # Resolver un sistema conserva la prioridad en sus propias palabras y en «resolver».
        self.assertEqual(catalogo.buscar_herramientas("inconsistente")[0], catalogo.SISTEMAS)
        self.assertEqual(catalogo.buscar_herramientas("resolver")[0], catalogo.SISTEMAS)
        for consulta in ("gauss", "pivote", "binario", "traspuesta"):
            self.assertNotIn(catalogo.ECUACIONES_MATRICIALES, catalogo.buscar_herramientas(consulta))


class PruebasEstructuraEcuacion(SimpleTestCase):
    def test_get_con_metodo_predeterminado_a_x_y_b(self):
        respuesta = self.client.get(RUTA)
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode()
        doc = Contenido(html)
        self.assertEqual(set(doc.tablas), {"Matriz A", "Vector b", "Vector incógnita x, no editable"})
        self.assertEqual(sorted(k for k in doc.campos if k.startswith("celda_")), ["celda_A_0_0", "celda_A_0_1", "celda_A_1_0", "celda_A_1_1", "celda_b_0_0", "celda_b_1_0"])
        self.assertEqual(doc.tablas["Vector incógnita x, no editable"], [["x₁"], ["x₂"]])
        self.assertNotIn("celda_x_0_0", doc.campos)
        self.assertRegex(html, r'name="metodo" value="gauss_jordan"[^>]*checked')
        self.assertEqual(len(re.findall(r'<input type="radio" name="metodo"', html)), 3)
        self.assertContains(respuesta, "A (2×2) · x (2) = b (2).")
        self.assertContains(respuesta, 'name="ajustar"')
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertNotContains(respuesta, 'name="operacion"')
        self.assertNotContains(respuesta, 'name="columnas_b"')
        self.assertEqual(METODO_PREDETERMINADO, "gauss_jordan")
        self.assertEqual([m for m, _ in METODOS], ["gauss", "gauss_jordan", "comparar"])

    def test_b_deriva_de_las_filas_y_x_de_las_columnas(self):
        respuesta = self.client.post(RUTA, {"filas": "3", "columnas": "2", "metodo": "gauss", "ajustar": "1"})
        doc = Contenido(respuesta.content.decode())
        self.assertEqual(len([k for k in doc.campos if k.startswith("celda_A_")]), 6)
        self.assertEqual(sorted(k for k in doc.campos if k.startswith("celda_b_")), ["celda_b_0_0", "celda_b_1_0", "celda_b_2_0"])
        self.assertEqual(doc.tablas["Vector incógnita x, no editable"], [["x₁"], ["x₂"]])
        self.assertContains(respuesta, "A (3×2) · x (2) = b (3).")
        self.assertContains(respuesta, "x tiene 2 componentes desconocidas")
        respuesta = self.client.post(RUTA, {"filas": "2", "columnas": "3", "metodo": "gauss", "ajustar": "1"})
        doc = Contenido(respuesta.content.decode())
        self.assertEqual(doc.tablas["Vector incógnita x, no editable"], [["x₁"], ["x₂"], ["x₃"]])
        self.assertEqual(len([k for k in doc.campos if k.startswith("celda_b_")]), 2)
        self.assertContains(respuesta, "A (2×3) · x (3) = b (2).")
        self.assertRegex(respuesta.content.decode(), r'name="metodo" value="gauss"[^>]*checked')
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertEqual(forma_texto(1, 1), "A (1×1) · x (1) = b (1)")
        self.assertEqual(incognitas(10)[-1], "x₁₀")
        self.assertEqual(ecuacion_vectorial(3), "x₁a₁ + x₂a₂ + x₃a₃ = b")

    def test_aplicar_conserva_celdas_y_fracciones_a_medio_escribir(self):
        datos = datos_ecuacion(celda_A_0_0="1/", celda_b_1_0="7") | {"filas": "3", "columnas": "1", "ajustar": "1"}
        respuesta = self.client.post(RUTA, datos)
        self.assertNotContains(respuesta, 'role="alert"')
        campos = Contenido(respuesta.content.decode()).campos
        self.assertEqual(campos["celda_A_0_0"]["value"], "1/")
        self.assertEqual(campos["celda_A_1_0"]["value"], "1")
        self.assertEqual(campos["celda_b_1_0"]["value"], "7")
        self.assertEqual(campos["celda_A_2_0"].get("value", ""), "")
        self.assertEqual(campos["celda_b_2_0"].get("value", ""), "")
        self.assertNotIn("celda_A_0_1", campos)

    def test_aplicar_valida_dimensiones(self):
        for campo, valor in (("filas", "0"), ("columnas", "11"), ("filas", "abc")):
            respuesta = self.client.post(RUTA, datos_ecuacion(**{campo: valor, "ajustar": "1"}))
            self.assertContains(respuesta, 'role="alert"')
            self.assertNotContains(respuesta, 'id="resultado"')

    def test_labels_reales_y_x_comprensible_para_lector_de_pantalla(self):
        html = self.client.post(RUTA, {"filas": "2", "columnas": "3", "metodo": "comparar", "ajustar": "1"}).content.decode()
        doc = Contenido(html)
        for nombre, attrs in doc.campos.items():
            if nombre.startswith("celda_") or nombre in ("filas", "columnas"):
                self.assertTrue(doc.labels.get(attrs["id"]), nombre)
        self.assertEqual(doc.labels[doc.campos["celda_b_1_0"]["id"]], "Vector b, componente 2")
        self.assertIn('aria-label="Vector incógnita x, no editable"', html)
        self.assertIn("x tiene 3 componentes desconocidas; se determinan al resolver.", html)
        self.assertIn('aria-label="Dimensiones de A"', html)
        self.assertIn("<legend>Método</legend>", html)
        self.assertIn('data-teclado-para="equation-fields"', html)

    def test_formulario_entrega_a_y_b_exactos(self):
        form = EcuacionMatricialForm(datos_ecuacion(a=[["1/2", -1, 0]], b=["-2/3"], metodo="comparar"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["entrada"], {"a": [[Fraction(1, 2), -1, 0]], "b": [Fraction(-2, 3)], "metodo": "comparar"})
        self.assertEqual(form.forma_texto, "A (1×3) · x (3) = b (1)")
        self.assertEqual(form.incognitas, [["x₁"], ["x₂"], ["x₃"]])
        self.assertEqual([m["nombre"] for m in form.matrices], ["A", "b"])
        self.assertTrue(form.matrices[1]["vector"])

    def test_limite_de_interfaz_admite_rectangulares(self):
        for m, n in ((1, 10), (10, 1), (2, 3), (3, 2), (10, 10)):
            form = EcuacionMatricialForm(datos_ecuacion(a=[[1] * n for _ in range(m)], b=[1] * m))
            self.assertTrue(form.is_valid(), form.errors)


class PruebasResultadosEcuacion(SimpleTestCase):
    def resolver(self, datos):
        respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode()
        self.assertNotIn('role="alert"', html)
        self.assertIn('id="resultado"', html)
        return html, Contenido(html), texto_resultado(html)

    def test_solucion_unica_cuadrada_con_x_comprobacion_e_interpretacion(self):
        html, doc, texto = self.resolver(datos_ecuacion(*UNICA))
        self.assertIn("Ax = b tiene solución única.", texto)
        self.assertIn("El sistema equivalente es consistente de solución única.", texto)
        self.assertIn("x1 = 3 x2 = 2", texto)
        self.assertEqual(doc.tablas["Vector solución x"], [["3"], ["2"]])
        self.assertEqual(doc.tablas["Producto Ax"], [["5"], ["1"]])
        self.assertEqual(doc.tablas["Vector b de la comprobación"], [["5"], ["1"]])
        self.assertIn("el producto Ax reproduce b", texto)
        self.assertIn("b es combinación lineal de las columnas de A de una única manera.", texto)
        self.assertIn("b = 3a₁ + 2a₂", texto)
        self.assertIn('data-kind="unica"', html)
        self.assertIn("Ecuación matricial · Gauss-Jordan", texto)

    def test_solucion_unica_rectangular_tres_por_dos(self):
        html, doc, texto = self.resolver(datos_ecuacion(*UNICA_RECTANGULAR, metodo="gauss"))
        self.assertIn("Ax = b tiene solución única.", texto)
        self.assertEqual(doc.tablas["Vector solución x"], [["2"], ["3"]])
        self.assertIn("A (3×2) · x (2) = b (3)", texto)
        self.assertIn("Matriz escalonada", texto)
        self.assertIn("Sustitución regresiva", texto)
        self.assertIn("Columnas pivote: C1, C2", texto)
        self.assertEqual(doc.tablas["Producto Ax"], [["2"], ["3"], ["5"]])

    def test_infinitas_rectangular_con_solucion_general_de_sistemas(self):
        html, doc, texto = self.resolver(datos_ecuacion(*INFINITAS))
        self.assertIn("Ax = b tiene infinitas soluciones.", texto)
        self.assertIn("x1 = 2 - x3 x2 = 3 - x3 x3 es libre", texto)
        self.assertIn("La variable x3 no tiene pivote, por lo que es libre.", texto)
        self.assertIn("b es combinación lineal de las columnas de A de infinitas maneras", texto)
        self.assertIn("cada valor de x3", texto)
        self.assertIn('data-kind="infinitas"', html)
        self.assertNotIn("Vector solución x", doc.tablas)
        self.assertNotIn("Comprobación", texto)
        self.assertNotIn("Producto Ax", doc.tablas)
        self.assertIn("A (2×3) · x (3) = b (2)", texto)
        self.assertEqual(doc.tablas["Vector incógnita x"], [["x₁"], ["x₂"], ["x₃"]])

    def test_inconsistente_rectangular_con_la_contradiccion(self):
        html, doc, texto = self.resolver(datos_ecuacion(*INCONSISTENTE))
        self.assertIn("Ax = b no tiene solución.", texto)
        self.assertIn("En la fila 3 se obtiene [0 0 | 1], que equivale a 0 = 1.", texto)
        self.assertIn("b no pertenece al conjunto generado por las columnas de A", texto)
        self.assertIn("ninguna combinación x₁a₁ + x₂a₂ produce b", texto)
        self.assertIn('data-kind="inconsistente"', html)
        self.assertNotIn("Vector solución x", doc.tablas)
        self.assertNotIn("Producto Ax", doc.tablas)
        # Sin solución no se muestra ningún vector x ni líneas x1 = … en el resultado.
        self.assertNotIn("x1 =", texto[:texto.index("Procedimiento")])

    def test_fracciones_exactas(self):
        html, doc, texto = self.resolver(datos_ecuacion(*FRACCIONES))
        self.assertIn("x1 = 1/2 x2 = 1/3", texto)
        self.assertEqual(doc.tablas["Vector solución x"], [["1/2"], ["1/3"]])
        self.assertIn("b = (1/2)a₁ + (1/3)a₂", texto)
        self.assertNotIn("0.5", texto)
        html, doc, texto = self.resolver(datos_ecuacion(a=[["1/2", "1/3"], ["-3/4", 2]], b=["5/6", "5/4"], metodo="comparar"))
        self.assertEqual(doc.tablas["Vector solución x"], [["1"], ["1"]])

    def test_resultado_antes_del_procedimiento_y_cadena_de_equivalencias(self):
        html, doc, texto = self.resolver(datos_ecuacion(*UNICA))
        self.assertLess(html.index('id="results-title"'), html.index('id="equivalences-title"'))
        self.assertLess(html.index('id="equivalences-title"'), html.index('id="procedure-title"'))
        for etapa in ("1 · Ecuación matricial", "2 · Ecuación vectorial", "3 · Sistema equivalente", "4 · Matriz aumentada"):
            self.assertIn(etapa, texto)
        self.assertLess(texto.index("1 · Ecuación matricial"), texto.index("2 · Ecuación vectorial"))
        self.assertLess(texto.index("2 · Ecuación vectorial"), texto.index("3 · Sistema equivalente"))
        self.assertLess(texto.index("3 · Sistema equivalente"), texto.index("4 · Matriz aumentada"))
        self.assertLess(texto.index("4 · Matriz aumentada"), texto.index("Eliminación por Gauss-Jordan"))
        self.assertIn("Ecuación matricial → ecuación vectorial → sistema equivalente → matriz aumentada → Gauss-Jordan → conjunto solución", texto)
        self.assertIn("x₁a₁ + x₂a₂ = b", texto)
        self.assertEqual(doc.tablas["Columna 1 de A"], [["1"], ["1"]])
        self.assertEqual(doc.tablas["Columna 2 de A"], [["1"], ["-1"]])
        self.assertIn("x1 + x2 = 5 x1 - x2 = 1", texto)
        self.assertEqual(doc.tablas["Matriz aumentada A barra b"], [["1", "1", "5"], ["1", "-1", "1"]])
        self.assertEqual(doc.tablas["Matriz A"], [["1", "1"], ["1", "-1"]])
        self.assertEqual(doc.tablas["Vector b"], [["5"], ["1"]])
        # Dentro del resultado no se generan ids repetidos aunque se reutilicen las plantillas de sistemas.
        ids = re.findall(r'id="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))

    def test_gauss_muestra_escalonada_y_sustitucion_regresiva(self):
        html, doc, texto = self.resolver(datos_ecuacion(*UNICA, metodo="gauss"))
        self.assertIn("Eliminación por Gauss", texto)
        self.assertNotIn("Gauss-Jordan", texto[texto.index("Eliminación por Gauss"):])
        self.assertIn("Matriz escalonada", texto)
        self.assertIn("Sustitución regresiva", texto)
        self.assertIn("x2 = 2", texto)
        self.assertEqual(doc.tablas["Matriz escalonada"], [["1", "1", "5"], ["0", "1", "2"]])
        self.assertEqual(html.count('id="procedure-title"'), 1)
        self.assertNotIn('id="procedure-title-2"', html)

    def test_gauss_jordan_muestra_reducida(self):
        html, doc, texto = self.resolver(datos_ecuacion(*UNICA, metodo="gauss_jordan"))
        self.assertIn("Eliminación por Gauss-Jordan", texto)
        self.assertIn("Matriz reducida", texto)
        self.assertNotIn("Sustitución regresiva", texto)
        self.assertEqual(doc.tablas["Matriz reducida"], [["1", "0", "3"], ["0", "1", "2"]])
        self.assertIn("Paso 1", texto)

    def test_comparar_muestra_el_resultado_una_vez_y_los_dos_procedimientos(self):
        html, doc, texto = self.resolver(datos_ecuacion(*INFINITAS, metodo="comparar"))
        self.assertEqual(html.count('id="results-title"'), 1)
        self.assertEqual(texto.count("Ax = b tiene infinitas soluciones."), 1)
        self.assertEqual(texto.count("x3 es libre"), 1)
        self.assertEqual(html.count('id="procedure-title"'), 1)
        self.assertEqual(html.count('id="procedure-title-2"'), 1)
        self.assertIn("Eliminación por Gauss", texto)
        self.assertIn("Eliminación por Gauss-Jordan", texto)
        self.assertIn("Comparación de métodos", texto)
        self.assertIn("Gauss y Gauss-Jordan", texto)
        self.assertLess(html.index('id="procedure-title"'), html.index('id="procedure-title-2"'))
        self.assertIn("Matriz escalonada", doc.tablas)
        self.assertIn("Matriz reducida", doc.tablas)
        self.assertEqual(html.count('class="panel panel-method"'), 2)
        # Las equivalencias se muestran una sola vez: no dependen del método.
        self.assertEqual(texto.count("4 · Matriz aumentada"), 1)

    def test_una_por_una_y_una_por_n(self):
        html, doc, texto = self.resolver(datos_ecuacion(a=[[4]], b=[6]))
        self.assertIn("x1 = 3/2", texto)
        self.assertIn("b es combinación lineal de la columna de A de una única manera.", texto)
        self.assertIn("A (1×1) · x (1) = b (1)", texto)
        self.assertIn("una ecuación por cada una de las 1 fila de A, con 1 incógnita:", texto)
        html, doc, texto = self.resolver(datos_ecuacion(a=[[1, 2, 3]], b=[6], metodo="comparar"))
        self.assertIn("Ax = b tiene infinitas soluciones.", texto)
        self.assertIn("x2 es libre", texto)
        self.assertIn("x3 es libre", texto)
        self.assertIn("cada valor de x2 y x3", texto)

    def test_diez_columnas_con_subindices_legibles(self):
        html, doc, texto = self.resolver(datos_ecuacion(a=[[1] * 10], b=[1]))
        self.assertIn("x₁a₁ + x₂a₂ + x₃a₃ + x₄a₄ + x₅a₅ + x₆a₆ + x₇a₇ + x₈a₈ + x₉a₉ + x₁₀a₁₀ = b", texto)
        self.assertEqual(doc.tablas["Vector incógnita x"][-1], ["x₁₀"])
        self.assertEqual(doc.tablas["Columna 10 de A"], [["1"]])

    def test_servicio_delega_en_el_backend_una_vez_por_metodo(self):
        with patch("frontend.web.calculadora.servicios_ecuaciones.resolver_ecuacion_matricial", wraps=resolver_ecuacion_matricial) as resolver:
            unico = resolver_ecuacion_web({"a": [[2]], "b": [1], "metodo": "gauss"})
            comparado = resolver_ecuacion_web({"a": [[2]], "b": [1], "metodo": "comparar"})
        self.assertEqual([llamada.args for llamada in resolver.call_args_list], [([[2]], [1], "gauss"), ([[2]], [1], "gauss"), ([[2]], [1], "gauss_jordan")])
        self.assertEqual([m["metodo"] for m in unico["metodos"]], ["Gauss"])
        self.assertEqual([m["metodo"] for m in comparado["metodos"]], ["Gauss", "Gauss-Jordan"])
        self.assertTrue(comparado["comparando"])
        self.assertEqual(comparado["x"], [["1/2"]])
        self.assertEqual(comparado["comprobacion"]["producto"], [["1"]])
        self.assertTrue(comparado["comprobacion"]["coincide"])

    def test_coincide_con_resolver_un_sistema_sobre_la_matriz_aumentada(self):
        for a, b in (UNICA, UNICA_RECTANGULAR, INFINITAS, INCONSISTENTE, FRACCIONES):
            for metodo in ("gauss", "gauss_jordan"):
                with self.subTest(a=a, metodo=metodo):
                    ecuacion = resolver_ecuacion_web({"a": a, "b": b, "metodo": metodo})["metodos"][0]
                    sistema = resolver_entrada_web("matriz", metodo, matriz_aumentada=[list(fila) + [componente] for fila, componente in zip(a, b)])
                    self.assertEqual(ecuacion, sistema)

    def test_comparar_coincide_en_clasificacion_solucion_y_pivotes(self):
        for a, b in (UNICA, UNICA_RECTANGULAR, INFINITAS, INCONSISTENTE, FRACCIONES, ([[1, 2], [2, 4], [3, 6]], [3, 6, 9])):
            with self.subTest(a=a):
                resultado = resolver_ecuacion_web({"a": a, "b": b, "metodo": "comparar"})
                gauss, jordan = resultado["metodos"]
                for clave in ("clasificacion", "clasificacion_clave", "columnas_pivote", "solucion_general"):
                    self.assertEqual(gauss[clave], jordan[clave], clave)
                self.assertEqual(resultado["clasificacion"], gauss["clasificacion"])
                self.assertEqual(resultado["solucion_general"], jordan["solucion_general"])

    def test_error_del_backend_llega_legible(self):
        with patch("frontend.web.calculadora.views.resolver_ecuacion_web", side_effect=ValueError("No se puede plantear Ax = b: A tiene 2 filas y b tiene 3 componentes.")):
            respuesta = self.client.post(RUTA, datos_ecuacion())
        self.assertContains(respuesta, "No se puede plantear Ax = b: A tiene 2 filas y b tiene 3 componentes.")
        self.assertNotContains(respuesta, 'id="resultado"')


class PruebasRechazoEcuacion(SimpleTestCase):
    def rechazar(self, datos, mensaje=None):
        respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'role="alert"')
        self.assertNotContains(respuesta, 'id="resultado"')
        if mensaje:
            self.assertContains(respuesta, mensaje)
        return respuesta

    def test_post_vacio_y_metodos_http(self):
        self.rechazar({})
        self.assertEqual(self.client.put(RUTA).status_code, 405)

    def test_dimensiones_fuera_de_limite_o_invalidas(self):
        for campo in ("filas", "columnas"):
            for valor in ("", "0", "-1", "1.5", "abc", "11", "99999999999999999"):
                with self.subTest(campo=campo, valor=valor):
                    self.rechazar(datos_ecuacion(**{campo: valor}))
        self.rechazar(datos_ecuacion(columnas="11"), "La interfaz admite hasta 10 columnas de A.")

    def test_metodo_ausente_o_invalido(self):
        self.rechazar(datos_ecuacion(metodo=None), "Selecciona un método.")
        self.rechazar(datos_ecuacion(metodo=""), "Selecciona un método.")
        for metodo in ("cramer", "inversa", "fila_columna", "<script>alert(1)</script>"):
            respuesta = self.rechazar(datos_ecuacion(metodo=metodo), "Selecciona un método válido.")
            self.assertNotContains(respuesta, "<script>alert(1)</script>")

    def test_matriz_o_vector_incompletos(self):
        for borrada in ("celda_A_0_0", "celda_A_1_1", "celda_b_1_0", "celda_b_0_0"):
            datos = datos_ecuacion()
            del datos[borrada]
            self.rechazar(datos, "Las celdas recibidas no coinciden con las dimensiones de A y de b")

    def test_b_debe_tener_exactamente_una_componente_por_fila(self):
        self.rechazar(datos_ecuacion(b=[5]), "Las celdas recibidas no coinciden")
        self.rechazar(datos_ecuacion(b=[5, 1, 9]), "Las celdas recibidas no coinciden")
        self.rechazar(datos_ecuacion(celda_b_0_1="2"), "Las celdas recibidas no coinciden")

    def test_x_no_se_recibe_ni_celdas_extra_ni_campos_desconocidos(self):
        for nombre in ("celda_x_0_0", "celda_A_2_0", "celda_A_0_2", "celda_B_0_0", "celda_A_-1_0", "celda_A_00_0", "celda_A_a_0", "columnas_b", "operacion", "escalar", "incognita"):
            with self.subTest(nombre=nombre):
                self.rechazar(datos_ecuacion(**{nombre: "1"}), "Las celdas recibidas no coinciden")

    def test_dimensiones_estructurales_inconsistentes(self):
        # Las celdas de una A 2×3 con filas=2, columnas=2 no encajan, aunque b sí tenga 2 componentes.
        self.rechazar(datos_ecuacion(a=[[1, 2, 3], [4, 5, 6]], columnas="2"), "Las celdas recibidas no coinciden")
        self.rechazar(datos_ecuacion(a=[[1, 2], [3, 4], [5, 6]], b=[1, 2, 3], filas="2"), "Las celdas recibidas no coinciden")

    def test_campos_repetidos(self):
        for campo in ("filas", "metodo", "celda_A_0_0", "celda_b_0_0"):
            datos = QueryDict(mutable=True)
            datos.update(datos_ecuacion())
            datos.appendlist(campo, datos[campo])
            form = EcuacionMatricialForm(datos)
            self.assertFalse(form.is_valid())
            self.assertIn("campos repetidos", str(form.non_field_errors()))

    def test_celdas_vacias_y_numeros_invalidos_con_error_asociado(self):
        self.rechazar(datos_ecuacion(celda_A_0_0=""), "Completa matriz a, fila 1, columna 1.")
        self.rechazar(datos_ecuacion(celda_b_1_0="  "), "Completa vector b, componente 2.")
        for valor in ("abc", "1/0", "1/", "1/2/3", "NaN", "Infinity", "--2", "1,5"):
            with self.subTest(valor=valor):
                self.rechazar(datos_ecuacion(celda_b_0_0=valor), "no es un número válido")
        respuesta = self.rechazar(datos_ecuacion(celda_A_1_0="2/0"))
        doc = Contenido(respuesta.content.decode())
        attrs = doc.campos["celda_A_1_0"]
        self.assertEqual(attrs["aria-invalid"], "true")
        self.assertIn("id_celda_A_1_0_error", attrs["aria-describedby"])
        self.assertEqual(attrs["value"], "2/0")
        self.assertEqual(doc.campos["celda_b_1_0"]["value"], "1")

    def test_html_se_escapa_incluso_al_aplicar(self):
        ataque = '<img src=x onerror="alert(1)">'
        for datos in (datos_ecuacion(celda_A_0_0=ataque), datos_ecuacion(celda_b_0_0=ataque), datos_ecuacion(celda_b_0_0=ataque, ajustar="1")):
            respuesta = self.client.post(RUTA, datos)
            self.assertNotContains(respuesta, ataque)
            self.assertContains(respuesta, "&lt;img")

    def test_csrf_exigido_y_envio_valido(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(RUTA, datos_ecuacion()).status_code, 403)
        cliente.get(RUTA)
        token = cliente.cookies["csrftoken"].value
        self.assertContains(cliente.post(RUTA, datos_ecuacion(csrfmiddlewaretoken=token)), 'id="resultado"')


class PruebasRecursosEcuacion(SimpleTestCase):
    def test_recursos_locales_tema_y_teclado(self):
        respuesta = self.client.get(RUTA)
        for recurso in ("ecuaciones.js", "teclado.js", "tema.js", "styles.css"):
            self.assertContains(respuesta, f"/static/calculadora/{recurso}")
        self.assertNotContains(respuesta, "matrices.js")
        self.assertContains(respuesta, 'id="theme-toggle"')
        self.assertContains(respuesta, 'data-insercion="/"')
        self.assertContains(respuesta, 'data-insercion="-"')
        self.assertNotContains(respuesta, 'src="https://')
        self.assertNotContains(respuesta, 'href="https://')
        self.assertTrue((ESTATICOS / "ecuaciones.js").is_file())

    def test_javascript_regenera_las_tres_piezas_con_el_marcado_del_servidor(self):
        html = self.client.get(RUTA).content.decode()
        for plantilla in ("matrix-entry-template", "matrix-cell-template"):
            self.assertIn(f'<template id="{plantilla}">', html)
        for marca in ("data-ecuacion", "data-equation-entry", "data-unknown", "data-equation-shape", "data-aplicar", 'data-dimension="filas"', 'data-dimension="columnas"'):
            self.assertIn(marca, html)
        js = (ESTATICOS / "ecuaciones.js").read_text(encoding="utf-8")
        for fragmento in ("data-ecuacion", "matrix-entry-template", "data-matriz=\"A\"", "data-matriz=\"b\"", "actualizarIncognita", "data-equation-shape", "ArrowDown", "resultado"):
            self.assertIn(fragmento, js)
        self.assertNotIn("innerHTML", js)

    def test_pyinstaller_incluye_los_modulos_de_p14(self):
        spec = (RAIZ / "AlgebraLineal.spec").read_text(encoding="utf-8")
        for modulo in ("backend.ecuaciones_matriciales", "frontend.web.calculadora.forms_ecuaciones",
                       "frontend.web.calculadora.opciones_ecuaciones", "frontend.web.calculadora.servicios_ecuaciones"):
            self.assertIn(f'"{modulo}"', spec)

    def test_procedimiento_comprensible_sin_color(self):
        html = self.client.post(RUTA, datos_ecuacion(*INCONSISTENTE, metodo="comparar")).content.decode()
        self.assertIn('class="classification equation-verdict" data-kind="inconsistente"', html)
        self.assertIn("Ax = b no tiene solución.", html)
        self.assertIn("Columnas pivote: C1, C2", strip_tags(html))
        for etiqueta in ("Ecuación matricial A por x igual a b", "Ecuación vectorial con las columnas de A", "Matriz aumentada A barra b"):
            self.assertIn(f'aria-label="{etiqueta}"', html)
        self.assertIn('tabindex="0"', html)
