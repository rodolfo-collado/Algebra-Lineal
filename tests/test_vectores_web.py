"""Vectores dentro de Operaciones: la antigua herramienta de vectores, sus rutas y sus resultados.

Operaciones con vectores dejó de ser una herramienta aparte. /vectores/operaciones/ redirige por
GET a un ejemplo de vectores y su POST (v1_0, v2_0, b_0, escalar…) se traduce a operandos y a la
expresión equivalente, que calcula la herramienta unificada. Los helpers `datos_vectores` y
`combinacion` siguen armando ese POST antiguo para las pruebas transversales.
"""

import os
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import Client, SimpleTestCase
from django.test.utils import setup_test_environment, teardown_test_environment
from django.utils.html import strip_tags

from frontend.web.calculadora import catalogo
from frontend.web.calculadora.opciones_matrices import PLANTILLAS, datos_operacion_vectorial, estado_plantilla
from tests.test_matrices_web import datos_simbolos

RUTA = "/vectores/operaciones/"
OPERACIONES = "/matrices/operaciones/"
# c1, C2, c₃ o el 3c2 de «x1 + 3c2»: la notación que las incógnitas de la combinación ya no usan.
INCOGNITA_C = r"(?<![A-Za-z_])[cC][0-9₀-₉]"


_PROPIO = False


def setUpModule():
    """Respuestas con `context` (vista y plantilla) aunque se ejecute con unittest a secas."""
    global _PROPIO
    try:
        setup_test_environment()
        _PROPIO = True
    except RuntimeError:
        pass


def tearDownModule():
    if _PROPIO:
        teardown_test_environment()


def datos_vectores(operacion, dimension=None, escalar=None, vectores=None, **componentes):
    """El POST de la antigua Operaciones con vectores: operacion, dimension y celdas nombre_i."""
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


def vector(nombre, valor):
    return {"nombre": nombre, "tipo": "vector", "valor": valor}


def seccion_resultado(respuesta):
    html = respuesta.content.decode("utf-8")
    if 'id="resultado"' not in html:
        return ""
    return " ".join(strip_tags(html[html.index('id="resultado"'):html.index("</main>")]).split())


def errores(respuesta):
    html = respuesta.content.decode("utf-8")
    return " ".join(strip_tags(html[html.index('id="expresiones-form"'):html.index("workspace-actions")]).split())


class PruebasNavegacionUnica(SimpleTestCase):
    def test_no_hay_una_herramienta_de_vectores_aparte(self):
        self.assertIsNone(catalogo.herramienta_por_id("operaciones-vectores"))
        nombres = [h.nombre for h in catalogo.HERRAMIENTAS]
        self.assertEqual(nombres.count("Operaciones"), 1)
        self.assertNotIn("Operaciones con vectores", nombres)
        self.assertNotIn("Operaciones con matrices", nombres)

    def test_buscar_vectores_lleva_a_operaciones(self):
        for consulta in ("vectores", "suma de vectores", "producto por escalar"):
            with self.subTest(consulta=consulta):
                self.assertEqual(catalogo.buscar_herramientas(consulta)[0].id, "operaciones-matrices")
        # «lineal» también nombra a Sistemas lineales (Ax = b), que resuelve lo mismo con A = [u v].
        self.assertIn("operaciones-matrices", [h.id for h in catalogo.buscar_herramientas("combinación lineal")])

    def test_la_ruta_antigua_identifica_la_herramienta_unificada(self):
        respuesta = Client().post(RUTA, datos_vectores("suma", v1=[1, 2], v2=[3, 4]))
        self.assertEqual(respuesta.context["herramienta_actual"].id, "operaciones-matrices")
        # El formulario envía ya a la ruta canónica.
        self.assertContains(respuesta, f'action="{OPERACIONES}#resultado"')


class PruebasRutaAntigua(SimpleTestCase):
    def test_get_redirige_permanentemente_a_un_ejemplo_de_vectores(self):
        respuesta = Client().get(RUTA)
        self.assertEqual(respuesta.status_code, 301)
        self.assertEqual(respuesta["Location"], f"{OPERACIONES}?plantilla=suma-vectores")

    def test_la_operacion_pedida_elige_el_ejemplo(self):
        for operacion, plantilla in (("escalar", "escalar-vector"), ("combinacion", "combinacion-lineal"),
                                     ("resta", "suma-vectores"), ("inventada", "suma-vectores")):
            with self.subTest(operacion=operacion):
                respuesta = Client().get(RUTA, {"operacion": operacion})
                self.assertEqual(respuesta["Location"], f"{OPERACIONES}?plantilla={plantilla}")

    def test_el_ejemplo_de_vectores_abre_con_vectores_y_su_expresion(self):
        respuesta = Client().get(f"{OPERACIONES}?plantilla=suma-vectores")
        self.assertEqual(respuesta.status_code, 200)
        form = respuesta.context["form"]
        self.assertEqual([bloque["tipo"] for bloque in form.bloques], ["vector", "vector"])
        self.assertEqual(form["expresion"].value(), "u + v")

    def test_post_antiguo_de_suma_resta_y_escalar_calcula_lo_mismo(self):
        casos = (
            (datos_vectores("suma", v1=[1, 2, 3], v2=[4, 5, 6]), "v1 + v2 = [5, 7, 9]"),
            (datos_vectores("suma", vectores=3, v1=[1, 0], v2=[0, 1], v3=[2, 2]), "v1 + v2 + v3 = [3, 3]"),
            (datos_vectores("resta", v1=[1, 2, 3], v2=[4, 5, 6]), "v1 - v2 = [-3, -3, -3]"),
            (datos_vectores("escalar", escalar="1/2", v1=[2, -4]), "k v1 = [1, -2]"),
        )
        for datos, igualdad in casos:
            with self.subTest(igualdad=igualdad):
                respuesta = Client().post(RUTA, datos)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.context["resultado"]["igualdad"], igualdad)

    def test_post_antiguo_de_combinacion_lineal(self):
        unica = Client().post(RUTA, combinacion([[1, 0], [0, 1]], [3, 4])).context["resultado"]
        self.assertEqual(unica["modo"], "combinacion")
        self.assertEqual(unica["coeficientes"], [("x1", "3"), ("x2", "4")])
        self.assertEqual(unica["conclusion"], "Sí: b es combinación lineal de v1 y v2.")
        infinitas = Client().post(RUTA, combinacion([[1, 1], [2, 2]], [3, 3])).context["resultado"]
        self.assertEqual(infinitas["clasificacion_clave"], "infinitas")
        ninguna = Client().post(RUTA, combinacion([[1, 1], [2, 2]], [1, 0])).context["resultado"]
        self.assertEqual(ninguna["conclusion"], "No: b no es combinación lineal de v1 y v2.")

    def test_post_antiguo_incompleto_explica_el_error_sin_calcular(self):
        datos = datos_vectores("suma", v1=[1, 2], v2=[3, 4])
        datos["v2_1"] = ""
        respuesta = Client().post(RUTA, datos)
        self.assertIsNone(respuesta.context["resultado"])
        self.assertTrue(respuesta.context["form"].errors)

    def test_traduccion_conserva_nombres_y_expresion(self):
        datos = datos_operacion_vectorial(combinacion([[1, 0], [0, 1], [1, 1]], [3, 4]))
        self.assertEqual(datos["expresion"], "x1 v1 + x2 v2 + x3 v3 = b")
        self.assertEqual([datos[f"nombre_{i}"] for i in range(4)], ["v1", "v2", "v3", "b"])
        self.assertEqual(datos["celda_3_1_0"], "4")


class PruebasVectoresEnOperaciones(SimpleTestCase):
    def evaluar(self, expresion, *simbolos):
        return Client().post(OPERACIONES, datos_simbolos(expresion, list(simbolos)))

    def test_solo_se_operan_los_operandos_escritos(self):
        u, v, w = vector("u", [1, 2]), vector("v", [3, 4]), vector("w", [100, 100])
        resultado = self.evaluar("2u - v", u, v, w).context["resultado"]
        self.assertEqual(resultado["igualdad"], "2u - v = [-1, 0]")
        self.assertEqual(resultado["tipo_texto"], "Vector de 2 componentes")

    def test_expresion_mixta_matriz_vector_y_escalar(self):
        a = {"nombre": "A", "tipo": "matriz", "valor": [[1, 2], [3, 4]]}
        k = {"nombre": "k", "tipo": "escalar", "valor": "2"}
        resultado = self.evaluar("k(Au) + v", a, k, vector("u", [1, 1]), vector("v", [0, -1])).context["resultado"]
        self.assertEqual(resultado["igualdad"], "k(Au) + v = [6, 13]")
        escalar = self.evaluar("3k - 1", k).context["resultado"]
        self.assertEqual((escalar["igualdad"], escalar["tipo_texto"]), ("3k - 1 = 5", "Escalar"))

    def test_no_hay_broadcasting_entre_matriz_y_vector(self):
        a = {"nombre": "A", "tipo": "matriz", "valor": [[1, 2], [3, 4]]}
        respuesta = self.evaluar("A + u", a, vector("u", [1, 1]))
        self.assertIsNone(respuesta.context["resultado"])
        self.assertIn("Solo se pueden sumar o restar matrices con matrices, vectores con vectores", errores(respuesta))

    def test_dimensiones_incompatibles_de_vectores(self):
        respuesta = self.evaluar("u + v", vector("u", [1, 2]), vector("v", [1, 2, 3]))
        self.assertIsNone(respuesta.context["resultado"])
        self.assertIn("u + v", errores(respuesta))

    def test_combinacion_lineal_como_igualdad_con_incognitas(self):
        respuesta = self.evaluar("x1 u + x2 v = b", vector("u", [1, 2]), vector("v", [3, 1]), vector("b", [5, 5]))
        resultado = respuesta.context["resultado"]
        self.assertEqual(resultado["coeficientes"], [("x1", "2"), ("x2", "1")])
        self.assertEqual(resultado["igualdad"], "(5, 5) = 2(1, 2) + (3, 1)")
        texto = seccion_resultado(respuesta)
        # Resultado antes del procedimiento.
        self.assertLess(texto.index("Sí: b es combinación lineal de u y v."), texto.index("Ver procedimiento"))
        self.assertNotRegex(texto, INCOGNITA_C)

    def test_combinacion_mal_planteada_explica_la_forma(self):
        u, v, b = vector("u", [1, 2]), vector("v", [3, 1]), vector("b", [5, 5])
        a = {"nombre": "A", "tipo": "matriz", "valor": [[1, 2], [3, 4]]}
        for expresion, mensaje, simbolos in (
            ("x1 u + x2 v", "no son operandos definidos", (u, v, b)),
            ("x2 u + x1 v = b", "Numera los coeficientes en orden", (u, v, b)),
            ("x1 A + x2 v = b", "A debe ser un vector", (a, v, b)),
            ("x1 u + x2 w = b", "x1 u + x2 v = b", (u, v, b, vector("w", [1, 2, 3]))),
        ):
            with self.subTest(expresion=expresion):
                respuesta = self.evaluar(expresion, *simbolos)
                self.assertIsNone(respuesta.context["resultado"])
                self.assertIn(mensaje, errores(respuesta))

    def test_combinacion_con_vectores_de_distinta_dimension(self):
        respuesta = self.evaluar("x1 u + x2 v = b", vector("u", [1, 2]), vector("v", [3, 1, 0]), vector("b", [5, 5]))
        self.assertIn("No se pueden combinar vectores de distinta dimensión", errores(respuesta))


class PruebasPlantillas(SimpleTestCase):
    def test_cada_ejemplo_carga_y_se_calcula_sin_errores(self):
        for identificador, rotulo, expresion, _ in PLANTILLAS:
            with self.subTest(plantilla=identificador):
                pagina = Client().get(OPERACIONES, {"plantilla": identificador})
                self.assertContains(pagina, f'data-plantilla="{identificador}"')
                self.assertEqual(pagina.context["form"]["expresion"].value(), expresion)
                respuesta = Client().post(OPERACIONES, estado_plantilla(identificador))
                self.assertIsNotNone(respuesta.context["resultado"], respuesta.context["form"].errors)

    def test_plantilla_desconocida_abre_el_formulario_vacio(self):
        respuesta = Client().get(OPERACIONES, {"plantilla": "<script>"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["form"]["expresion"].value() or "", "")
        self.assertNotContains(respuesta, "<script>\"")

    def test_resultado_principal_antes_del_procedimiento(self):
        respuesta = Client().post(OPERACIONES, estado_plantilla("producto"))
        html = respuesta.content.decode("utf-8")
        self.assertLess(html.index('id="final-title"'), html.index('id="procedimiento"'))
        self.assertIn("Matriz 2×2", seccion_resultado(respuesta))
        self.assertTrue(re.search(r"Expresión · Matriz 2×2", seccion_resultado(respuesta)))
