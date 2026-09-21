"""Integración web de Operaciones con vectores (P12): registro, navegación, formulario y resultados."""

import os
import re
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import Client, SimpleTestCase
from django.urls import resolve, reverse
from django.utils.html import strip_tags

from backend.sistemas import resolver_sistema_gauss_jordan
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms import VectoresForm
from frontend.web.calculadora.opciones_vectores import (
    DIMENSION_MAXIMA,
    OPERACIONES,
    VECTORES_MAXIMOS,
    nombres_vectores,
)
from frontend.web.calculadora.servicios_vectores import operar_vectores
from frontend.web.calculadora.teclados import perfiles_para
from tests.test_navegacion import Documento
from tests.test_teclado import Pagina

RAIZ = Path(__file__).resolve().parents[1]
STATIC = RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora"
RUTA = "/vectores/operaciones/"


def datos_vectores(operacion, dimension=None, escalar=None, vectores=None, **componentes):
    """Arma el POST que produce la interfaz: operacion, dimension y celdas nombre_i."""
    datos = {"operacion": operacion}
    if dimension is None:
        dimension = len(next(iter(componentes.values())))
    datos["dimension"] = str(dimension)
    if escalar is not None:
        datos["escalar"] = escalar
    if vectores is not None:
        datos["vectores"] = str(vectores)
    for nombre, valores in componentes.items():
        for indice, valor in enumerate(valores):
            datos[f"{nombre}_{indice}"] = str(valor)
    return datos


def combinacion(generadores, objetivo, **extra):
    celdas = {f"v{indice}": vector for indice, vector in enumerate(generadores, start=1)}
    celdas["b"] = objetivo
    return datos_vectores("combinacion", len(objetivo), vectores=len(generadores), **celdas) | extra


def seccion_resultado(respuesta):
    html = respuesta.content.decode("utf-8")
    if 'id="resultado"' not in html:
        return ""
    return " ".join(strip_tags(html[html.index('id="resultado"'):html.index("</main>")]).split())


def errores_formulario(respuesta):
    html = respuesta.content.decode("utf-8")
    formulario = html[html.index('id="vectores-form"'):html.index("workspace-actions")]
    return re.findall(r'<(?:li|p class="field-error"[^>]*)>([^<]+)</', formulario)


class PruebasRegistroYNavegacion(SimpleTestCase):
    def setUp(self):
        self.herramienta = catalogo.herramienta_por_id("operaciones-vectores")

    def test_vectores_es_una_categoria_disponible_con_una_sola_herramienta(self):
        self.assertTrue(catalogo.VECTORES.disponible)
        self.assertEqual(catalogo.herramientas_de(catalogo.VECTORES), (catalogo.OPERACIONES_VECTORES,))
        self.assertIsNone(catalogo.herramienta_por_id("combinacion-lineal"))
        self.assertTrue(self.herramienta.disponible)
        self.assertEqual(self.herramienta.nombre, "Operaciones con vectores")
        self.assertEqual(self.herramienta.ruta, RUTA)
        self.assertEqual(reverse("calculadora:operaciones-vectores"), RUTA)
        self.assertEqual(resolve(RUTA).view_name, "calculadora:operaciones-vectores")
        self.assertEqual(catalogo.herramienta_por_ruta(resolve(RUTA)), catalogo.OPERACIONES_VECTORES)
        self.assertEqual(self.herramienta.relacionadas, ())
        for palabra in ("vector", "vectores", "suma de vectores", "resta de vectores", "escalar",
                        "combinación lineal", "span", "generado", "dimensión"):
            self.assertIn(palabra, self.herramienta.palabras_clave)

    def test_aparece_en_inicio_sidebar_y_buscador(self):
        inicio = self.client.get("/")
        self.assertContains(inicio, "Operaciones con vectores")
        self.assertContains(inicio, f'href="{RUTA}"')
        documento = Documento(inicio)
        self.assertIn(RUTA, [a.get("href") for a in documento.enlaces_en("Herramientas")])
        self.assertIn(RUTA, [a.get("href") for _, a in documento.enlaces if a.get("class") == "tool-link"])
        # La categoría ya no se anuncia como próxima.
        html = inicio.content.decode("utf-8")
        seccion = html[html.index('id="vectores"'):html.index("</details>", html.index('id="vectores"'))]
        self.assertNotIn("Próximamente", seccion)
        self.assertNotIn("topic-upcoming", seccion)
        self.assertRegex(html, r'<details class="topic" id="vectores"')

        # Desde P13B, Operaciones con matrices también responde a «vector» (Ax) y a
        # «combinación lineal» (Ax como combinación de columnas), y desde P14 Resolver
        # Ax = b responde a «vector» (vector b) y a «combinación lineal»; vectores sigue primero.
        compartidas = {
            "escalar": (catalogo.OPERACIONES_VECTORES, catalogo.OPERACIONES_MATRICES),
            "vector": (catalogo.OPERACIONES_VECTORES, catalogo.OPERACIONES_MATRICES, catalogo.ECUACIONES_MATRICIALES),
            "combinación lineal": (catalogo.OPERACIONES_VECTORES, catalogo.OPERACIONES_MATRICES, catalogo.ECUACIONES_MATRICIALES),
        }
        for consulta in ("vector", "vectores", "suma de vectores", "escalar", "combinación lineal", "span", "dimension"):
            with self.subTest(consulta=consulta):
                esperadas = compartidas.get(consulta, (catalogo.OPERACIONES_VECTORES,))
                self.assertEqual(catalogo.buscar_herramientas(consulta), esperadas)
                respuesta = self.client.get("/", {"q": consulta})
                self.assertContains(respuesta, f"{len(esperadas)} herramientas coinciden" if len(esperadas) > 1 else "1 herramienta coincide")
                self.assertContains(respuesta, f'href="{RUTA}"')
        # «matriz» sigue sin mezclar vectores con las herramientas de matrices y sistemas.
        self.assertNotIn(catalogo.OPERACIONES_VECTORES, catalogo.buscar_herramientas("matriz"))
        for consulta in ("gauss", "pivote", "binario"):
            self.assertNotIn(catalogo.OPERACIONES_VECTORES, catalogo.buscar_herramientas(consulta))

    def test_get_breadcrumbs_sidebar_activa_y_sin_relacionadas(self):
        respuesta = self.client.get(RUTA)
        self.assertEqual(respuesta.status_code, 200)
        documento = Documento(respuesta)
        self.assertEqual(
            [a["href"] for a in documento.enlaces_en("Ruta de navegación")],
            ["/", "/#algebra-lineal", "/#vectores"],
        )
        self.assertContains(respuesta, '<span aria-current="page">Operaciones con vectores</span>', html=True)
        activos = [a["href"] for a in documento.enlaces_en("Herramientas") if a.get("aria-current") == "page"]
        self.assertEqual(activos, [RUTA])
        self.assertEqual([c for c, abierta in documento.categorias.items() if abierta], ["vectores"])
        self.assertContains(respuesta, "Álgebra Lineal · Vectores")
        self.assertContains(respuesta, 'name="csrfmiddlewaretoken"', html=False)
        self.assertNotContains(respuesta, "Herramientas relacionadas")
        self.assertNotContains(respuesta, "related-list")
        self.assertEqual(
            [(m.nombre, m.url) for m in catalogo.migas(catalogo.OPERACIONES_VECTORES)][:3],
            [("Inicio", "/"), ("Álgebra Lineal", "/#algebra-lineal"), ("Vectores", "/#vectores")],
        )

    def test_las_rutas_antiguas_de_sistemas_no_alcanzan_a_vectores(self):
        self.assertEqual(self.client.get("/sistemas/vectores/").status_code, 404)
        self.assertEqual(self.client.get("/vectores/").status_code, 404)
        self.assertEqual(self.client.get("/vectores/combinacion/").status_code, 404)

    def test_tema_recursos_locales_y_scripts(self):
        html = self.client.get(RUTA).content.decode("utf-8")
        self.assertIn("algebra-lineal-tema", html)
        self.assertIn('id="theme-toggle"', html)
        self.assertNotIn("cdn.", html.lower())
        self.assertNotIn("fonts.googleapis", html.lower())
        self.assertIn("calculadora/styles.css", html)
        self.assertIn("calculadora/teclado.js", html)
        self.assertIn("calculadora/vectores.js", html)
        self.assertNotIn("calculadora/matriz.js", html)
        self.assertIn('id="vector-initial-values"', html)
        script = (STATIC / "vectores.js").read_text(encoding="utf-8")
        for marca in ("data-vectores", "data-estructura", "data-cell", "data-solo-operacion", "data-operacion-hint", "render"):
            self.assertIn(marca, script)
        self.assertNotIn("://", script)


class PruebasFormulario(SimpleTestCase):
    def test_la_operacion_se_elige_dentro_de_la_herramienta(self):
        pagina = self.client.get(RUTA)
        documento = Documento(pagina)
        radios = [c for c in documento.controles if c.get("name") == "operacion"]
        self.assertEqual([(c["type"], c["value"]) for c in radios], [("radio", clave) for clave, _ in OPERACIONES])
        self.assertEqual([c["value"] for c in radios if "checked" in c], ["suma"])
        html = pagina.content.decode("utf-8")
        for etiqueta in ("Suma", "Resta", "Multiplicación por escalar", "Combinación lineal"):
            self.assertIn(f"<span>{etiqueta}</span>", html)
        self.assertEqual(html.count('<label class="option">'), len(OPERACIONES))
        # Una ayuda por operación; solo la de la elegida queda visible sin JavaScript.
        self.assertRegex(html, r'data-operacion-hint="suma"\s*>')
        self.assertRegex(html, r'data-operacion-hint="combinacion"\s+hidden>')
        self.assertContains(pagina, ">Calcular</button>")

    def test_dimension_dinamica_con_celdas_por_componente(self):
        pagina = self.client.get(RUTA)
        documento = Documento(pagina)
        celdas = [c["name"] for c in documento.controles if c.get("data-cell")]
        self.assertEqual(celdas, ["u_0", "u_1", "u_2", "v_0", "v_1", "v_2"])
        dimension = next(c for c in documento.controles if c.get("name") == "dimension")
        self.assertEqual((dimension["type"], dimension["value"], dimension["min"], dimension["max"]),
                         ("number", "3", "1", str(DIMENSION_MAXIMA)))
        html = pagina.content.decode("utf-8")
        for ausente in ('name="x"', 'name="y"', 'name="z"', "<textarea", "[1, 2, 3]"):
            self.assertNotIn(ausente, html)
        self.assertIn('aria-label="Componente 1 de u"', html)
        self.assertIn('aria-label="Componente 3 de v"', html)
        self.assertRegex(html, r'data-vector="u"[^>]*aria-label="Vector u"')
        # El campo de vectores generadores existe pero nace oculto: solo aplica a la combinación.
        self.assertRegex(html, r'data-solo-operacion="combinacion"\s+hidden>')

    def test_el_servidor_redibuja_la_estructura_pedida(self):
        # Sin JavaScript, «Aplicar» reajusta dimensión y operación conservando lo escrito, sin calcular.
        respuesta = self.client.post(RUTA, {"operacion": "escalar", "dimension": "2", "ajustar": "1", "u_0": "7", "u_1": "8", "escalar": "2"})
        self.assertEqual(respuesta.status_code, 200)
        documento = Documento(respuesta)
        celdas = [(c["name"], c["value"]) for c in documento.controles if c.get("data-cell")]
        self.assertEqual(celdas, [("u_0", "7"), ("u_1", "8")])
        escalar = next(c for c in documento.controles if c.get("name") == "escalar")
        self.assertEqual(escalar["value"], "2")
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertNotContains(respuesta, "field-error")
        self.assertNotContains(respuesta, 'class="alert error"')
        self.assertContains(respuesta, 'aria-label="Escalar k"')

        respuesta = self.client.post(RUTA, {"operacion": "combinacion", "dimension": "4", "vectores": "3", "ajustar": "1"})
        celdas = [c["name"] for c in Documento(respuesta).controles if c.get("data-cell")]
        self.assertEqual(celdas, [f"{n}_{i}" for n in ("v1", "v2", "v3", "b") for i in range(4)])
        self.assertContains(respuesta, ">Comprobar</button>")
        self.assertRegex(respuesta.content.decode("utf-8"), r'data-solo-operacion="combinacion"\s*>')
        self.assertContains(respuesta, 'class="vector-row vector-row-target"')

    def test_tras_un_error_se_conservan_valores_y_estructura(self):
        respuesta = self.client.post(RUTA, datos_vectores("suma", u=[1, "x", 3], v=[4, 5, 6]))
        celdas = [(c["name"], c["value"]) for c in Documento(respuesta).controles if c.get("data-cell")]
        self.assertEqual(celdas, [("u_0", "1"), ("u_1", "x"), ("u_2", "3"), ("v_0", "4"), ("v_1", "5"), ("v_2", "6")])
        self.assertIn("En la componente 2 de u: &#x27;x&#x27; no es un número válido.", errores_formulario(respuesta))
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_estructura_del_formulario_por_operacion(self):
        self.assertEqual(nombres_vectores("suma", 0), ("u", "v"))
        self.assertEqual(nombres_vectores("resta", 5), ("u", "v"))
        self.assertEqual(nombres_vectores("escalar", 0), ("u",))
        self.assertEqual(nombres_vectores("combinacion", 3), ("v1", "v2", "v3", "b"))
        form = VectoresForm()
        estructura = form.estructura()
        self.assertEqual((estructura["operacion"], estructura["dimension"], estructura["vectores"]), ("suma", 3, 2))
        self.assertEqual([fila["nombre"] for fila in estructura["filas"]], ["u", "v"])
        form = VectoresForm({"operacion": "combinacion", "dimension": "99", "vectores": "-3"})
        estructura = form.estructura()
        self.assertEqual((estructura["dimension"], estructura["vectores"]), (DIMENSION_MAXIMA, 1))
        self.assertEqual([fila["nombre"] for fila in estructura["filas"]], ["v1", "b"])
        self.assertTrue(estructura["filas"][-1]["objetivo"])

    def test_teclado_contextual_reutilizado_y_controles_de_estructura_aparte(self):
        html = self.client.get(RUTA).content.decode("utf-8")
        pagina = Pagina(html)
        self.assertEqual(len(pagina.teclados), 1)
        self.assertEqual(pagina.contenedores["vector-fields"], "numerico")
        self.assertEqual(pagina.perfiles_publicados, perfiles_para("numerico"))
        self.assertIn('role="group" aria-label="Teclado matemático" hidden>', html)
        teclado = pagina.perfiles_publicados["numerico"]["grupos"][0]["teclas"]
        self.assertEqual([t["insercion"] for t in teclado], ["-", "/"])
        estructura = re.findall(r'aria-label="(Quitar una componente|Agregar una componente|Quitar un vector|Agregar un vector)" hidden', html)
        self.assertEqual(sorted(estructura), ["Agregar un vector", "Agregar una componente", "Quitar un vector", "Quitar una componente"])
        self.assertIn('aria-label="Estructura de los vectores"', html)
        for boton in teclado:
            self.assertNotIn("Quitar", boton["nombre"])
            self.assertNotIn("Agregar", boton["nombre"])
        self.assertIn("<noscript>", html)
        self.assertIn('name="ajustar"', html)

    def test_csrf_obligatorio(self):
        respuesta = Client(enforce_csrf_checks=True).post(RUTA, datos_vectores("suma", u=[1, 2], v=[3, 4]))
        self.assertEqual(respuesta.status_code, 403)

    def test_inicio_no_muestra_el_formulario_de_vectores(self):
        inicio = self.client.get("/")
        self.assertNotContains(inicio, 'name="operacion"')
        self.assertNotContains(inicio, "calculadora/vectores.js")


class PruebasOperacionesWeb(SimpleTestCase):
    def test_suma(self):
        respuesta = self.client.post(RUTA, datos_vectores("suma", u=[1, 2, 3], v=[4, 5, 6]))
        texto = seccion_resultado(respuesta)
        self.assertIn("Resultado u + v = (5, 7, 9)", texto)
        # P18: el desarrollo va plegado antes del resultado y sustituye los vectores en la propia cadena.
        self.assertIn("Ver procedimiento Componente a componente u + v = (1, 2, 3) + (4, 5, 6) = (1 + 4, 2 + 5, 3 + 6) = (5, 7, 9)", texto)
        self.assertNotIn("Vectores de entrada", texto)
        self.assertLess(texto.index("Ver procedimiento"), texto.index("Resultado u + v"))
        self.assertContains(respuesta, 'class="vector vector-result"')
        self.assertContains(respuesta, 'class="panel panel-final"')

        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("suma", u=[1, 2], v=[3, 4])))
        self.assertIn("u + v = (4, 6)", texto)

    def test_suma_con_fracciones_exactas(self):
        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("suma", u=["1/2", "2/3"], v=["1/2", "1/3"])))
        self.assertIn("u + v = (1, 1)", texto)
        self.assertIn("(1/2 + 1/2, 2/3 + 1/3)", texto)
        self.assertNotIn("0.", texto)
        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("suma", u=["1/3"], v=["1/3"])))
        self.assertIn("u + v = (2/3)", texto)
        self.assertNotIn("0.6", texto)

    def test_resta(self):
        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("resta", u=[4, 6], v=[1, 2])))
        self.assertIn("Resultado u − v = (3, 4)", texto)
        self.assertIn("u − v = (4, 6) − (1, 2) = (4 - 1, 6 - 2) = (3, 4)", texto)
        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("resta", u=[5, 7, 9], v=[1, 2, 3])))
        self.assertIn("= (4, 5, 6)", texto)
        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("resta", u=[5], v=[-1])))
        self.assertIn("(5 - (-1)) = (6)", texto)

    def test_escalar(self):
        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("escalar", escalar="3", u=[1, -2, 4])))
        self.assertIn("Resultado k·u = (3, -6, 12)", texto)
        self.assertIn("k·u = 3·(1, -2, 4) = (3·1, 3·(-2), 3·4) = (3, -6, 12)", texto)
        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("escalar", escalar="0", u=[1, 2, 3])))
        self.assertIn("k·u = (0, 0, 0)", texto)
        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("escalar", escalar="1/2", u=["1/3", -4])))
        self.assertIn("k·u = (1/6, -2)", texto)
        self.assertIn("k·u = (1/2)·(1/3, -4) = ((1/2)·(1/3), (1/2)·(-4))", texto)

    def test_dimension_grande_y_dimension_uno(self):
        u = list(range(1, 9))
        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("suma", u=u, v=u)))
        self.assertIn("u + v = (2, 4, 6, 8, 10, 12, 14, 16)", texto)
        texto = seccion_resultado(self.client.post(RUTA, datos_vectores("escalar", escalar="-2", u=[5])))
        self.assertIn("k·u = (-10)", texto)

    def test_sin_excepciones_internas(self):
        for datos in (
            datos_vectores("suma", u=[1, 2], v=[3, 4]),
            datos_vectores("suma", u=[1, "abc"], v=[3, 4]),
            {"operacion": "suma", "dimension": "abc"},
            {},
        ):
            with self.subTest(datos=datos):
                respuesta = self.client.post(RUTA, datos)
                self.assertEqual(respuesta.status_code, 200)
                for ausente in ("Traceback", "ValueError", "Fraction("):
                    self.assertNotContains(respuesta, ausente)


class PruebasCombinacionLinealWeb(SimpleTestCase):
    def test_solucion_unica_con_procedimiento_en_lenguaje_de_coeficientes(self):
        respuesta = self.client.post(RUTA, combinacion([[1, 0], [0, 1]], [3, 4]))
        texto = seccion_resultado(respuesta)
        self.assertIn("Resultado Sí: b es combinación lineal de v1 y v2. Existe una única combinación.", texto)
        self.assertIn("Coeficientes c1 = 3 c2 = 4", texto)
        self.assertIn("b como combinación lineal (3, 4) = 3(1, 0) + 4(0, 1)", texto)
        self.assertIn("1 · Planteamiento Buscamos c1 y c2 tales que: c1(1, 0) + c2(0, 1) = (3, 4)", texto)
        self.assertIn("2 · Sistema equivalente", texto)
        self.assertIn("c1 = 3 c2 = 4 Cada vector generador es una columna y b es la columna aumentada", texto)
        self.assertIn("3 · Gauss-Jordan No fue necesario realizar operaciones por filas.", texto)
        self.assertIn("4 · Lectura de la matriz El sistema es consistente de solución única.", texto)
        # P18: procedimiento plegado antes; la conclusión y los coeficientes solo en el resultado.
        self.assertLess(texto.index("Ver procedimiento"), texto.index("Resultado Sí:"))
        self.assertEqual(texto.count("c1 = 3 c2 = 4"), 2)  # sistema equivalente y coeficientes
        self.assertContains(respuesta, 'data-kind="unica"')
        # Habla de coeficientes c, no de variables x.
        self.assertNotRegex(texto, r"\bx[1-9]")
        self.assertNotIn("Entender este resultado", texto)

    def test_solucion_unica_con_eliminacion_y_coeficiente_negativo(self):
        texto = seccion_resultado(self.client.post(RUTA, combinacion([[1, 2], [3, 4]], [-1, 0])))
        self.assertIn("Coeficientes c1 = 2 c2 = -1", texto)
        self.assertIn("(-1, 0) = 2(1, 2) - (3, 4)", texto)
        self.assertIn("Paso 1", texto)
        self.assertIn("c1 + 3c2 = -1 2c1 + 4c2 = 0", texto)
        self.assertIn("Matriz reducida", texto)

    def test_no_es_combinacion_lineal(self):
        respuesta = self.client.post(RUTA, combinacion([[1, 2], [2, 4]], [3, 7]))
        texto = seccion_resultado(respuesta)
        self.assertIn("No: b no es combinación lineal de v1 y v2. El sistema asociado no tiene solución.", texto)
        self.assertIn("El sistema es inconsistente.", texto)
        self.assertIn("que equivale a 0 = 1", texto)
        self.assertNotIn("Coeficientes", texto)
        self.assertNotIn("b como combinación lineal", texto)
        self.assertContains(respuesta, 'data-kind="inconsistente"')

    def test_infinitas_combinaciones_cuentan_como_combinacion_lineal(self):
        respuesta = self.client.post(RUTA, combinacion([[1, 2], [2, 4]], [3, 6]))
        texto = seccion_resultado(respuesta)
        self.assertIn("Sí: b es combinación lineal de v1 y v2. Existen infinitas combinaciones posibles.", texto)
        self.assertIn("Solución general c1 = 3 - 2c2 c2 es libre", texto)
        self.assertIn("Por ejemplo, con c2 = 0: (3, 6) = 3(1, 2) + 0(2, 4)", texto)
        self.assertIn("La variable c2 no tiene pivote, por lo que es libre.", texto)
        self.assertContains(respuesta, 'data-kind="infinitas"')
        self.assertNotIn("No:", texto)

    def test_mas_de_dos_generadores_y_dimension_mayor(self):
        texto = seccion_resultado(self.client.post(RUTA, combinacion([[1, 0, 2], [0, 1, 3], [1, 1, 0]], [4, 5, 6])))
        self.assertIn("Buscamos c1, c2 y c3 tales que: c1(1, 0, 2) + c2(0, 1, 3) + c3(1, 1, 0) = (4, 5, 6)", texto)
        self.assertIn("c1 + c3 = 4 c2 + c3 = 5 2c1 + 3c2 = 6", texto)
        self.assertIn("Sí: b es combinación lineal de v1, v2 y v3.", texto)

        generadores = [[1, 0, 0, 0, 1], [0, 1, 0, 0, 1], [0, 0, 1, 0, 1], [0, 0, 0, 1, 1]]
        texto = seccion_resultado(self.client.post(RUTA, combinacion(generadores, [1, 2, 3, 4, 10])))
        self.assertIn("Coeficientes c1 = 1 c2 = 2 c3 = 3 c4 = 4", texto)
        self.assertIn("(1, 2, 3, 4, 10) = (1, 0, 0, 0, 1) + 2(0, 1, 0, 0, 1) + 3(0, 0, 1, 0, 1) + 4(0, 0, 0, 1, 1)", texto)
        self.assertIn("cada una de las 5 componentes", texto)

    def test_fracciones_en_componentes_y_coeficientes(self):
        texto = seccion_resultado(self.client.post(RUTA, combinacion([[2, 0], [0, 3]], [1, 1])))
        self.assertIn("Coeficientes c1 = 1/2 c2 = 1/3", texto)
        self.assertIn("(1, 1) = 1/2(2, 0) + 1/3(0, 3)", texto)
        texto = seccion_resultado(self.client.post(RUTA, combinacion([["1/2", 0], [0, "1/3"]], [1, 1])))
        self.assertIn("Coeficientes c1 = 2 c2 = 3", texto)
        self.assertNotIn("0.5", texto)

    def test_reutiliza_el_motor_de_sistemas_sin_pasar_por_su_interfaz(self):
        with patch("backend.vectores.resolver_sistema_gauss_jordan", wraps=resolver_sistema_gauss_jordan) as motor, \
                patch("frontend.web.calculadora.views.resolver_entrada_web") as sistemas_web:
            respuesta = self.client.post(RUTA, combinacion([[1, 2], [3, 4]], [5, 6]))
        motor.assert_called_once()
        self.assertEqual(motor.call_args.args[0], [[1, 3, 5], [2, 4, 6]])
        sistemas_web.assert_not_called()
        texto = seccion_resultado(respuesta)
        self.assertIn("Coeficientes c1 = -1 c2 = 2", texto)
        self.assertIn("(5, 6) = -(1, 2) + 2(3, 4)", texto)
        # La matriz reducida resalta las columnas pivote igual que en Resolver un sistema.
        self.assertContains(respuesta, ' pivot"')

    def test_un_solo_generador(self):
        texto = seccion_resultado(self.client.post(RUTA, combinacion([[2, 4]], [1, 2])))
        self.assertIn("Sí: b es combinación lineal de v1.", texto)
        self.assertIn("Coeficientes c1 = 1/2", texto)
        self.assertIn("Buscamos c1 tales que", texto)

    def test_dimensiones_incompatibles_se_rechazan_antes_de_resolver(self):
        datos = combinacion([[1, 2], [1, 2]], [4, 5])
        datos["v2_2"] = "3"
        with patch("backend.vectores.resolver_sistema_gauss_jordan") as motor:
            respuesta = self.client.post(RUTA, datos)
        motor.assert_not_called()
        self.assertIn("La cantidad de componentes no coincide con la dimensión y los vectores indicados.", errores_formulario(respuesta))
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_servicio_devuelve_datos_no_html(self):
        entrada = {"operacion": "combinacion", "dimension": 2, "nombres": ("v1", "v2", "b"),
                   "vectores": {"v1": [1, 0], "v2": [0, 1], "b": [3, 4]}, "escalar": None}
        resultado = operar_vectores(entrada)
        self.assertEqual(resultado["coeficientes"], [("c1", "3"), ("c2", "4")])
        self.assertEqual(resultado["planteamiento"], "c1(1, 0) + c2(0, 1) = (3, 4)")
        self.assertEqual(resultado["igualdad"], "(3, 4) = 3(1, 0) + 4(0, 1)")
        self.assertEqual(resultado["matriz_aumentada"], [["1", "0", "3"], ["0", "1", "4"]])
        self.assertEqual(resultado["clasificacion_clave"], "unica")
        for valor in (resultado["conclusion"], resultado["igualdad"], *resultado["ecuaciones"]):
            self.assertNotIn("<", valor)


class PruebasValidacionWeb(SimpleTestCase):
    def post(self, datos):
        respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertNotContains(respuesta, "Traceback")
        return errores_formulario(respuesta)

    def test_entrada_vacia_y_componentes_invalidas(self):
        self.assertIn("Indica la dimensión de los vectores.", self.post({"operacion": "suma"}))
        errores = self.post(datos_vectores("suma", u=[1, ""], v=["x", "1/0"]))
        self.assertIn("Falta la componente 2 de u.", errores)
        self.assertIn("En la componente 1 de v: &#x27;x&#x27; no es un número válido.", errores)
        self.assertIn("En la componente 2 de v: &#x27;1/0&#x27; no es un número válido.", errores)

    def test_dimensiones_incompatibles_y_estructuras_manipuladas(self):
        # Menos celdas que la dimensión, celdas de más y nombres ajenos: siempre se rechazan.
        mensaje = "La cantidad de componentes no coincide con la dimensión y los vectores indicados."
        self.assertIn(mensaje, self.post(datos_vectores("suma", dimension=3, u=[1, 2, 3], v=[4, 5])))
        self.assertIn(mensaje, self.post(datos_vectores("suma", u=[1, 2], v=[3, 4]) | {"v_7": "1"}))
        self.assertIn(mensaje, self.post(datos_vectores("suma", u=[1, 2], v=[3, 4]) | {"b_0": "1"}))
        self.assertIn(mensaje, self.post(datos_vectores("escalar", escalar="2", u=[1, 2], v=[3, 4])))
        self.assertIn(mensaje, self.post(combinacion([[1, 2], [3, 4]], [5, 6]) | {"v3_0": "1", "v3_1": "2"}))

    def test_limites_de_dimension_y_vectores(self):
        self.assertIn("Un vector necesita al menos una componente.", self.post({"operacion": "suma", "dimension": "0"}))
        self.assertIn(f"La dimensión máxima admitida es {DIMENSION_MAXIMA}.", self.post({"operacion": "suma", "dimension": str(DIMENSION_MAXIMA + 1)}))
        self.assertIn("La dimensión debe ser un número entero.", self.post({"operacion": "suma", "dimension": "2.5"}))
        self.assertIn("Hace falta al menos un vector generador.", self.post({"operacion": "combinacion", "dimension": "2", "vectores": "0"}))
        self.assertIn(f"Se admiten como máximo {VECTORES_MAXIMOS} vectores generadores.",
                      self.post({"operacion": "combinacion", "dimension": "2", "vectores": str(VECTORES_MAXIMOS + 1)}))
        self.assertIn("Indica cuántos vectores generadores hay.", self.post({"operacion": "combinacion", "dimension": "2", "b_0": "1", "b_1": "2"}))

    def test_vector_objetivo_incompleto_y_escalar_invalido(self):
        errores = self.post(combinacion([[1, 0], [0, 1]], ["3", ""]))
        self.assertIn("Falta la componente 2 de b.", errores)
        self.assertIn("Ingresa el escalar k.", self.post(datos_vectores("escalar", u=[1, 2])))
        self.assertIn("El escalar: &#x27;abc&#x27; no es un número válido.", self.post(datos_vectores("escalar", escalar="abc", u=[1, 2])))
        self.assertIn("Selecciona una operación válida.", self.post(datos_vectores("otra", u=[1, 2], v=[3, 4])))
        self.assertIn("Selecciona una operación.", self.post({"dimension": "2", "u_0": "1", "u_1": "2", "v_0": "1", "v_1": "2"}))

    def test_valores_manipulados_desde_cliente_no_rompen_la_pagina(self):
        for datos in (
            {"operacion": "suma", "dimension": "2", "vectores": "abc", "u_0": "1", "u_1": "2", "v_0": "1", "v_1": "2"},
            {"operacion": "combinacion", "dimension": "2", "vectores": "2", "v1_0": "1", "v1_1": "2", "v2_0": "3", "v2_1": "4", "b_0": "5", "b_1": "6", "ajustar": ""},
            {"operacion": "escalar", "dimension": "1", "escalar": "1e400", "u_0": "1"},
            {"operacion": "escalar", "dimension": "1", "escalar": "<script>", "u_0": "1"},
        ):
            with self.subTest(datos=datos):
                respuesta = self.client.post(RUTA, datos)
                self.assertEqual(respuesta.status_code, 200)
                self.assertNotContains(respuesta, "Traceback")
        # Lo que escribe el usuario vuelve escapado, nunca como HTML.
        self.assertContains(respuesta, "&#x27;&lt;script&gt;&#x27; no es un número válido.")
        self.assertNotContains(respuesta, "'<script>'")


if __name__ == "__main__":
    import unittest

    unittest.main()
