"""Contratos de P13A: catálogo, estructura HTTP, cálculo, presentación y seguridad."""

import os
from fractions import Fraction
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.http import QueryDict
from django.template.loader import render_to_string
from django.test import Client, SimpleTestCase
from django.urls import resolve, reverse

from backend.matrices import resolver_operacion_matrices
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms_matrices import MatricesForm
from frontend.web.calculadora.opciones_matrices import CONFIGURACION, DIMENSION_MAXIMA, es_vector
from frontend.web.calculadora.servicios_matrices import operar_matrices
from tests.test_navegacion import Documento

RUTA = "/matrices/operaciones/"
RAIZ = Path(__file__).resolve().parents[1]


def datos_matrices(operacion="suma", a=None, b=None, escalar=None, **extra):
    a = [[1, 2], [3, 4]] if a is None else a
    datos = {"operacion": operacion, "filas": str(len(a)), "columnas": str(len(a[0]))}
    matrices = {"A": a}
    if b is not None:
        matrices["B"] = b
    elif operacion in ("suma", "resta"):
        matrices["B"] = [[5, 6], [7, 8]]
    for nombre, matriz in matrices.items():
        for i, fila in enumerate(matriz):
            for j, valor in enumerate(fila):
                datos[f"celda_{nombre}_{i}_{j}"] = str(valor)
    if escalar is not None:
        datos["escalar"] = str(escalar)
    return datos | extra


class Contenido(HTMLParser):
    """Lee tablas y campos activos; ignora plantillas inertes para JavaScript."""
    def __init__(self, html):
        super().__init__()
        self.tablas, self.campos, self.labels = {}, {}, {}
        self.plantilla = False
        self.tabla = self.fila = self.celda = self.label = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "template":
            self.plantilla = True
        if self.plantilla:
            return
        if tag == "table":
            self.tabla = attrs.get("aria-label")
            self.tablas[self.tabla] = []
        if tag == "tr" and self.tabla is not None:
            self.fila = []
        if tag == "td" and self.fila is not None:
            self.celda = ""
        if tag == "input" and attrs.get("name"):
            self.campos[attrs["name"]] = attrs
        if tag == "label" and attrs.get("for"):
            self.label = attrs["for"]
            self.labels[self.label] = ""

    def handle_data(self, data):
        if self.plantilla:
            return
        if self.celda is not None:
            self.celda += data
        if self.label:
            self.labels[self.label] += data

    def handle_endtag(self, tag):
        if tag == "template":
            self.plantilla = False
        if self.plantilla:
            return
        if tag == "label":
            self.label = None
        if tag == "td" and self.celda is not None:
            self.fila.append(self.celda.strip())
            self.celda = None
        if tag == "tr" and self.fila is not None:
            self.tablas[self.tabla].append(self.fila)
            self.fila = None
        if tag == "table":
            self.tabla = None


class PruebasCatalogoMatrices(SimpleTestCase):
    def test_operaciones_es_la_primera_herramienta_de_matrices(self):
        # Desde P14 la categoría tiene dos herramientas; Operaciones con matrices sigue igual.
        self.assertTrue(catalogo.MATRICES.disponible)
        self.assertEqual(catalogo.herramientas_de(catalogo.MATRICES)[0], catalogo.OPERACIONES_MATRICES)
        self.assertEqual(len(catalogo.herramientas_de(catalogo.MATRICES)), 2)
        self.assertEqual(reverse("calculadora:operaciones-matrices"), RUTA)
        self.assertEqual(catalogo.herramienta_por_ruta(resolve(RUTA)), catalogo.OPERACIONES_MATRICES)

    def test_inicio_sidebar_y_tema(self):
        respuesta = self.client.get("/")
        documento = Documento(respuesta)
        self.assertIn(RUTA, [a["href"] for a in documento.enlaces_en("Herramientas")])
        self.assertContains(respuesta, '<details class="topic" id="matrices"')
        self.assertIn(RUTA, [a["href"] for _, a in documento.enlaces if a.get("class") == "tool-link"])

    def test_busqueda_por_sinonimos_y_operaciones(self):
        for palabra in ("matriz", "matrices", "suma", "resta", "escalar", "traspuesta", "transpuesta", "filas", "columnas"):
            with self.subTest(palabra=palabra):
                self.assertIn(catalogo.OPERACIONES_MATRICES, catalogo.buscar_herramientas(palabra))
                self.assertContains(self.client.get("/", {"q": palabra}), f'href="{RUTA}"')

    def test_breadcrumbs_estado_activo_categoria_abierta(self):
        respuesta = self.client.get(RUTA)
        doc = Documento(respuesta)
        self.assertEqual([a["href"] for a in doc.enlaces_en("Ruta de navegación")], ["/", "/#algebra-lineal", "/#matrices"])
        self.assertEqual([a["href"] for a in doc.enlaces_en("Herramientas") if a.get("aria-current") == "page"], [RUTA])
        self.assertTrue(doc.categorias["matrices"])

    def test_seis_operaciones_en_una_sola_herramienta(self):
        # P13B añadió AB y Ax a la misma herramienta, sin otra entrada en la sidebar.
        form = MatricesForm()
        self.assertEqual(set(dict(form.fields["operacion"].choices)), {"suma", "resta", "escalar", "traspuesta", "producto", "matriz_vector"})


class PruebasFormularioMatrices(SimpleTestCase):
    def test_get_dos_matrices_y_sin_escalar(self):
        respuesta = self.client.get(RUTA)
        doc = Contenido(respuesta.content.decode())
        self.assertEqual(len([k for k in doc.campos if k.startswith("celda_")]), 8)
        self.assertNotIn("escalar", doc.campos)
        self.assertEqual({"Matriz A", "Matriz B"}, set(doc.tablas))

    def test_campos_de_cada_operacion_sin_javascript(self):
        # Cada entrada toma su forma de la estructura: A es 2×3; B comparte forma en suma/resta,
        # es 3×2 en AB (columnas_b nace en 2 al cambiar de operación) y x es un vector de 3.
        for op, opcion in CONFIGURACION.items():
            respuesta = self.client.post(RUTA, {"operacion": op, "filas": "2", "columnas": "3", "ajustar": "1"})
            doc = Contenido(respuesta.content.decode())
            esperadas = {("Vector " if es_vector(opcion, n) else "Matriz ") + n for n in opcion["matrices"]}
            self.assertEqual(set(doc.tablas), esperadas)
            self.assertEqual("escalar" in doc.campos, opcion["escalar"])
            medidas = {"filas": 2, "columnas": 3, "columnas_b": 2, None: 1}
            celdas = sum(medidas[alto] * medidas[ancho] for alto, ancho in (opcion["formas"][n] for n in opcion["matrices"]))
            self.assertEqual(len([k for k in doc.campos if k.startswith("celda_")]), celdas)
            self.assertNotContains(respuesta, 'id="resultado"')

    def test_aplicar_conserva_celdas_al_cambiar_dimensiones(self):
        respuesta = self.client.post(RUTA, datos_matrices(filas="3", columnas="1", ajustar="1"))
        campos = Contenido(respuesta.content.decode()).campos
        self.assertEqual(campos["celda_A_1_0"]["value"], "3")
        self.assertEqual(campos["celda_A_2_0"].get("value", ""), "")
        self.assertNotIn("celda_A_0_1", campos)

    def test_aplicar_conserva_fraccion_a_medio_escribir(self):
        respuesta = self.client.post(RUTA, datos_matrices(celda_A_0_0="1/", ajustar="1"))
        self.assertEqual(Contenido(respuesta.content.decode()).campos["celda_A_0_0"]["value"], "1/")
        self.assertNotContains(respuesta, 'role="alert"')

    def test_aplicar_valida_dimensiones_y_operacion(self):
        for campo, valor in (("filas", "0"), ("columnas", "11"), ("operacion", "inversa")):
            r = self.client.post(RUTA, datos_matrices(**{campo: valor, "ajustar": "1"}))
            self.assertContains(r, 'role="alert"')
            self.assertNotContains(r, 'id="resultado"')

    def test_formulario_exactitud_del_parser_compartido(self):
        form = MatricesForm(datos_matrices("escalar", a=[["0.5", "-7/3", "0"]], escalar="1/2"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["entrada"]["matrices"]["A"], [[Fraction(1, 2), Fraction(-7, 3), 0]])
        self.assertEqual(form.cleaned_data["entrada"]["escalar"], Fraction(1, 2))

    def test_labels_reales_para_todas_las_celdas(self):
        r = self.client.post(RUTA, datos_matrices("escalar", escalar="2", ajustar="1"))
        doc = Contenido(r.content.decode())
        for nombre, attrs in doc.campos.items():
            if nombre.startswith("celda_") or nombre in ("escalar", "filas", "columnas"):
                self.assertTrue(doc.labels.get(attrs["id"]))

    def test_error_asociado_con_celda_y_valores_conservados(self):
        r = self.client.post(RUTA, datos_matrices(celda_A_0_0="1/0"))
        doc = Contenido(r.content.decode())
        attrs = doc.campos["celda_A_0_0"]
        self.assertEqual(attrs["aria-invalid"], "true")
        self.assertIn("id_celda_A_0_0_error", attrs["aria-describedby"])
        self.assertContains(r, 'id="id_celda_A_0_0_error"')
        self.assertEqual(attrs["value"], "1/0")
        self.assertEqual(doc.campos["celda_B_1_1"]["value"], "8")

    def test_limite_de_interfaz_admite_rectangulares(self):
        for m, n in ((1, 10), (10, 1), (2, 3), (3, 2), (10, 10)):
            form = MatricesForm(datos_matrices("traspuesta", a=[[0] * n for _ in range(m)]))
            self.assertTrue(form.is_valid(), form.errors)


class PruebasResultadosMatrices(SimpleTestCase):
    def comprobar(self, datos, esperado):
        r = self.client.post(RUTA, datos)
        self.assertEqual(r.status_code, 200)
        doc = Contenido(r.content.decode())
        self.assertEqual(doc.tablas.get("Matriz resultado"), esperado)
        self.assertEqual(doc.tablas.get("Resultado del desarrollo"), esperado)
        return r, doc

    def test_suma_con_desarrollo(self):
        r, doc = self.comprobar(datos_matrices(), [["6", "8"], ["10", "12"]])
        self.assertEqual(doc.tablas["Desarrollo por entradas"], [["1 + 5", "2 + 6"], ["3 + 7", "4 + 8"]])
        self.assertContains(r, "cᵢⱼ = aᵢⱼ + bᵢⱼ")

    def test_resta_con_signos_claros(self):
        r, doc = self.comprobar(datos_matrices("resta", a=[[5, 6]], b=[[1, -2]]), [["4", "8"]])
        self.assertEqual(doc.tablas["Desarrollo por entradas"], [["5 − 1", "6 − (-2)"]])
        self.assertContains(r, "cᵢⱼ = aᵢⱼ − bᵢⱼ")

    def test_escalar_con_fraccion(self):
        r, doc = self.comprobar(datos_matrices("escalar", a=[[2, 4], [6, 8]], escalar="1/2"), [["1", "2"], ["3", "4"]])
        self.assertEqual(doc.tablas["Desarrollo por entradas"][0], ["(1/2) · 2", "(1/2) · 4"])
        self.assertContains(r, "(kA)ᵢⱼ = k · aᵢⱼ")

    def test_escalar_cero_visible(self):
        r, _ = self.comprobar(datos_matrices("escalar", a=[[2, -4, 7]], escalar="0"), [["0", "0", "0"]])
        self.assertContains(r, 'class="matrix-expression">0 ·')

    def test_traspuesta_rectangular_con_indices_y_dimensiones(self):
        r, doc = self.comprobar(datos_matrices("traspuesta", a=[[1, 2, 3], [4, 5, 6]]), [["1", "4"], ["2", "5"], ["3", "6"]])
        self.assertContains(r, "2×3 → 3×2")
        self.assertContains(r, "Fila 2 de A → columna 2 de Aᵀ")
        self.assertEqual(doc.tablas["Desarrollo por entradas"][2], ["a[1, 3]", "a[2, 3]"])

    def test_suma_fraccionaria_rectangular(self):
        self.comprobar(datos_matrices(a=[["1/2", -2, 0]], b=[["1/3", 3, "-7/3"]]), [["5/6", "1", "-7/3"]])

    def test_resta_fraccionaria_rectangular(self):
        self.comprobar(datos_matrices("resta", a=[["1/2"], [-2], [0]], b=[["1/3"], [3], ["-7/3"]]), [["1/6"], ["-5"], ["7/3"]])

    def test_procedimiento_plegado_antes_del_resultado(self):
        r = self.client.post(RUTA, datos_matrices())
        html = r.content.decode()
        self.assertLess(html.index('id="results-title"'), html.index('id="procedimiento"'))
        self.assertLess(html.index('id="procedimiento"'), html.index('id="final-title"'))

    def test_servicio_delega_la_matematica(self):
        with patch("frontend.web.calculadora.servicios_matrices.resolver_operacion_matrices", wraps=resolver_operacion_matrices) as resolver:
            operar_matrices({"operacion": "traspuesta", "matrices": {"A": [[1, 2]]}})
        resolver.assert_called_once_with("traspuesta", [[1, 2]], None, None)

    def test_dominio_del_backend_llega_como_error_legible(self):
        with patch("frontend.web.calculadora.views.operar_matrices", side_effect=ValueError("Ambas matrices deben tener las mismas dimensiones.")):
            r = self.client.post(RUTA, datos_matrices())
        self.assertContains(r, "Ambas matrices deben tener las mismas dimensiones.")
        self.assertNotContains(r, 'id="resultado"')


class PruebasRechazoMatrices(SimpleTestCase):
    def rechazar(self, datos, mensaje=None):
        r = self.client.post(RUTA, datos)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'role="alert"')
        self.assertNotContains(r, 'id="resultado"')
        if mensaje:
            self.assertContains(r, mensaje)
        return r

    def test_post_vacio(self):
        self.rechazar({})

    def test_dimensiones_invalidas(self):
        for campo in ("filas", "columnas"):
            for valor in ("", "0", "-1", "1.5", "abc", "11", "99999999999999999"):
                with self.subTest(campo=campo, valor=valor):
                    self.rechazar(datos_matrices(**{campo: valor}))

    def test_operacion_invalida(self):
        for op in ("", "inversa", "determinante", "<script>"):
            self.rechazar(datos_matrices(operacion=op))

    def test_filas_y_columnas_incompletas(self):
        for borrada in ("celda_A_0_0", "celda_A_1_1", "celda_B_1_0"):
            datos = datos_matrices()
            del datos[borrada]
            self.rechazar(datos, "Las celdas recibidas no coinciden")

    def test_dimensiones_incompatibles_en_post(self):
        self.rechazar(datos_matrices(a=[[1, 2, 3]], b=[[1], [2], [3]]), "Las celdas recibidas no coinciden")

    def test_campos_sobrantes_o_indices_manipulados(self):
        for nombre in ("celda_A_2_0", "celda_B_-1_0", "celda_A_00_0", "celda_C_0_0", "filas_B", "escalar", "celda_A_x_0"):
            self.rechazar(datos_matrices(**{nombre: "1"}), "Las celdas recibidas no coinciden")

    def test_campos_ajenos_a_traspuesta_o_escalar(self):
        for op in ("traspuesta", "escalar"):
            self.rechazar(datos_matrices(op, escalar="2" if op == "escalar" else None, celda_B_0_0="3"))

    def test_campos_duplicados(self):
        for campo in ("filas", "operacion", "celda_A_0_0"):
            datos = QueryDict(mutable=True)
            datos.update(datos_matrices())
            datos.appendlist(campo, datos[campo])
            form = MatricesForm(datos)
            self.assertFalse(form.is_valid())
            self.assertIn("campos repetidos", str(form.non_field_errors()))

    def test_celdas_vacias(self):
        for valor in ("", "   "):
            self.rechazar(datos_matrices(celda_A_0_0=valor), "Completa matriz a, fila 1, columna 1.")

    def test_numeros_y_fracciones_invalidos(self):
        for valor in ("abc", "1/0", "1/", "1/2/3", "NaN", "Infinity", "--2"):
            self.rechazar(datos_matrices(celda_A_0_0=valor), "no es un número válido")

    def test_escalar_invalido_o_ausente(self):
        for valor in (None, "", "1/0", "texto"):
            self.rechazar(datos_matrices("escalar", escalar=valor))

    def test_html_se_escapa_incluso_al_aplicar(self):
        ataque = '<script>alert("x")</script>'
        for ajustar in (False, True):
            datos = datos_matrices(celda_A_0_0=ataque)
            if ajustar:
                datos["ajustar"] = "1"
            r = self.client.post(RUTA, datos)
            self.assertNotContains(r, ataque)
            self.assertContains(r, "&lt;script&gt;")

    def test_csrf_exigido_y_envio_valido(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(RUTA, datos_matrices()).status_code, 403)
        cliente.get(RUTA)
        token = cliente.cookies["csrftoken"].value
        r = cliente.post(RUTA, datos_matrices(csrfmiddlewaretoken=token))
        self.assertContains(r, 'id="resultado"')

    def test_metodos_http_restringidos(self):
        self.assertEqual(self.client.put(RUTA).status_code, 405)


class PruebasComponentesYRecursosMatrices(SimpleTestCase):
    def test_matriz_generica_sin_columna_aumentada(self):
        html = render_to_string("calculadora/components/matriz.html", {"matriz": [[1, 2, 3]], "etiqueta": "A"})
        self.assertNotIn('class="constant', html)
        self.assertIn("matrix-fence-start", html)
        self.assertIn('tabindex="0"', html)

    def test_matriz_aumentada_conserva_separador_y_pivotes(self):
        html = render_to_string("calculadora/components/matrix.html", {"matriz": [[1, 2, 3]], "columnas_pivote": [1]})
        self.assertEqual(html.count('class="constant'), 1)
        self.assertEqual(html.count('class=" pivot'), 1)

    def test_componentes_escapan_expresiones(self):
        html = render_to_string("calculadora/components/matriz.html", {"matriz": [["<b>1</b>"]]})
        self.assertIn("&lt;b&gt;1&lt;/b&gt;", html)
        self.assertNotIn("<b>1</b>", html)

    def test_tema_teclado_y_recursos_locales(self):
        r = self.client.get(RUTA)
        for recurso in ("matrices.js", "teclado.js", "tema.js", "styles.css"):
            self.assertContains(r, f"/static/calculadora/{recurso}")
        self.assertContains(r, 'id="matrix-fields" data-perfil="numerico"')
        from tests.test_teclado import Pagina
        teclas = Pagina(r.content.decode()).perfiles_publicados["numerico"]["grupos"][0]["teclas"]
        self.assertEqual([t["insercion"] for t in teclas], ["-", "/"])
        self.assertNotContains(r, 'src="https://')
        self.assertNotContains(r, 'href="https://')

    def test_pyinstaller_incluye_modulos_y_recursos(self):
        spec = (RAIZ / "AlgebraLineal.spec").read_text(encoding="utf-8")
        for modulo in ("backend.matrices", "frontend.web.calculadora.forms_matrices", "frontend.web.calculadora.opciones_matrices", "frontend.web.calculadora.servicios_matrices"):
            self.assertIn(f'"{modulo}"', spec)
        self.assertIn('"frontend/web/calculadora/templates"', spec)
        self.assertIn('"frontend/web/calculadora/static"', spec)
