"""Expresiones dentro de Operaciones con matrices (P26.6): catálogo, POST, procedimiento y formato."""

import os
import re
from fractions import Fraction
from html.parser import HTMLParser
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django

django.setup()

from django.http import QueryDict
from django.test import Client, SimpleTestCase

from backend.expresiones_matriciales import evaluar as evaluar_backend
from backend.matrices import multiplicar_matriz_vector, sumar_matrices
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms_expresiones import ExpresionMatricialForm
from frontend.web.calculadora.servicios_expresiones import evaluar_expresion_web
from tests.test_matrices_web import Contenido, datos_simbolos

RUTA = "/matrices/operaciones/"
ANTIGUA = "/matrices/expresiones/"


def datos_expresion(expresion, simbolos, **extra):
    return datos_simbolos(expresion, simbolos, **extra)


EJEMPLO = (
    {"nombre": "A", "tipo": "matriz", "valor": [[2, 5], [3, 1]]},
    {"nombre": "u", "tipo": "vector", "valor": [4, -1]},
    {"nombre": "v", "tipo": "vector", "valor": [-3, 5]},
)


class Texto(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.partes = []
        self.feed(html)

    def handle_data(self, data):
        self.partes.append(data)

    def __str__(self):
        return " ".join(self.partes)


class PruebasCatalogo(SimpleTestCase):
    def test_las_expresiones_son_operaciones_con_matrices(self):
        # P26.6: una sola herramienta; la ruta anterior redirige y no hay segunda tarjeta.
        herramienta = catalogo.OPERACIONES_MATRICES
        self.assertEqual(herramienta.ruta, RUTA)
        self.assertEqual(herramienta.categoria, catalogo.MATRICES)
        self.assertFalse(hasattr(catalogo, "EXPRESIONES_MATRICIALES"))
        self.assertIsNone(catalogo.herramienta_por_id("expresiones-matriciales"))
        self.assertEqual(
            catalogo.herramientas_de(catalogo.MATRICES),
            (herramienta, catalogo.ECUACIONES_MATRICIALES, catalogo.REDUCCION_FILAS, catalogo.MATRIZ_INVERSA,
             catalogo.DETERMINANTES),
        )
        # UI-17 añade inversa desde operaciones, sin sugerir resolver Ax=b por inversión.
        self.assertEqual(set(herramienta.relacionadas), {"ecuaciones-matriciales", "matriz-inversa"})
        respuesta = self.client.get("/")
        self.assertContains(respuesta, f'href="{RUTA}"')
        self.assertNotContains(respuesta, f'href="{ANTIGUA}"')
        self.assertNotContains(respuesta, "Expresiones matriciales")
        self.assertNotContains(respuesta, "Acceso rápido")
        self.assertEqual(self.client.get(ANTIGUA)["Location"], RUTA)


class PruebasPagina(SimpleTestCase):
    def test_vocabulario_visible_y_fuente_de_operandos_del_teclado(self):
        respuesta = self.client.get(RUTA)
        self.assertContains(respuesta, '>Operandos</h3>')
        self.assertContains(respuesta, '>Agregar operando</button>')
        self.assertContains(respuesta, 'Define las matrices, vectores y escalares; la expresión usa solo los que escribas.')
        self.assertContains(respuesta, 'data-operandos="#symbol-list"')
        for texto in ('Símbolos', 'Agregar símbolo', 'Eliminar símbolo'):
            self.assertNotContains(respuesta, texto)
        vacio = self.client.post(RUTA, datos_expresion('', EJEMPLO[:1], eliminar='0'))
        self.assertContains(vacio, 'Sin operandos:')

    def test_get_empieza_con_dos_matrices_y_sin_resultado(self):
        respuesta = self.client.get(RUTA)
        self.assertContains(respuesta, 'id="expresiones-form"')
        self.assertContains(respuesta, 'name="nombre_0"')
        self.assertContains(respuesta, 'name="nombre_1"')
        self.assertContains(respuesta, "Matriz A, fila 1, columna 1")
        self.assertContains(respuesta, "Matriz B, fila 2, columna 2")
        self.assertNotContains(respuesta, 'name="nombre_2"')
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertNotContains(respuesta, "data-numeric-controls")
        self.assertContains(respuesta, "calculadora/expresiones.js")

    def test_agregar_eliminar_y_aplicar_no_calculan(self):
        agregado = self.client.post(RUTA, datos_expresion("", EJEMPLO[:1], agregar="1"))
        self.assertContains(agregado, 'name="nombre_1"')
        self.assertNotContains(agregado, 'id="resultado"')
        vacio = self.client.post(RUTA, datos_expresion("", EJEMPLO[:1], eliminar="0"))
        self.assertNotContains(vacio, 'name="nombre_0"')
        self.assertNotContains(vacio, 'id="resultado"')
        vector = self.client.post(RUTA, {
            "cantidad": "1", "nombre_0": "u", "tipo_0": "vector", "filas_0": "3", "columnas_0": "2",
            "celda_0_0_0": "1", "celda_0_0_1": "9", "expresion": "u", "ajustar": "1",
        })
        self.assertContains(vector, "componente 3")
        self.assertNotContains(vector, 'id="resultado"')

    def test_cada_simbolo_es_un_grupo_y_sus_controles_dicen_a_que_simbolo_pertenecen(self):
        # P27.8 (UI-34): también sin JavaScript; expresiones.js mantiene los mismos textos al renombrar
        # (y rotula las copias de la plantilla inerte, que se excluye aquí).
        html = re.sub(r"<template\b.*?</template>", "", self.client.get(RUTA).content.decode(), flags=re.S)
        for nombre in ("A", "B"):
            with self.subTest(nombre=nombre):
                self.assertIn(f'<fieldset class="symbol-card" data-simbolo aria-label="Operando {nombre}">', html)
                self.assertIn(f'aria-label="Eliminar operando {nombre}">Eliminar</button>', html)
                for etiqueta in (f"Quitar una fila de {nombre}", f"Agregar una fila a {nombre}",
                                 f"Quitar una columna de {nombre}", f"Agregar una columna a {nombre}"):
                    self.assertIn(f'aria-label="{etiqueta}"', html)
        self.assertNotIn('aria-label="Quitar una fila"', html)
        self.assertNotIn('aria-label="Eliminar"', html)
        # Renombrado y de otro tipo: el servidor ya rotula con el nombre enviado.
        renombrado = self.client.post(RUTA, {
            "cantidad": "1", "nombre_0": "u", "tipo_0": "vector", "filas_0": "2",
            "celda_0_0_0": "1", "celda_0_1_0": "2", "expresion": "u", "ajustar": "1",
        }).content.decode()
        self.assertIn('aria-label="Operando u"', renombrado)
        self.assertIn('aria-label="Quitar una componente de u"', renombrado)
        self.assertIn('aria-label="Agregar una componente a u"', renombrado)
        self.assertIn('aria-label="Eliminar operando u"', renombrado)

    def test_nombre_tipo_y_dimensiones_tienen_label_asociado_sin_dos_puntos(self):
        # P27.8 (UI-62): etiquetas reales encima de cada control y sin «:» automático.
        html = self.client.get(RUTA).content.decode()
        for campo, texto in (("nombre_0", "Nombre"), ("tipo_0", "Tipo"), ("filas_0", "Filas"), ("columnas_0", "Columnas")):
            with self.subTest(campo=campo):
                self.assertIn(f'<label for="id_{campo}">{texto}</label>', html)
                self.assertIn(f'id="id_{campo}"', html)
        self.assertNotIn(":</label>", html)


class PruebasCalculo(SimpleTestCase):
    def test_traspuesta_visual_y_manual_de_nombre_largo_son_equivalentes(self):
        matriz = ({'nombre': 'Manzana', 'tipo': 'matriz', 'valor': [[1, 2, 3], [4, 5, 6]]},)
        resultados = []
        for sufijo in ('^T', 'ᵀ'):
            with self.subTest(sufijo=sufijo):
                respuesta = self.client.post(RUTA, datos_expresion('Manzana' + sufijo, matriz))
                self.assertNotContains(respuesta, 'data-respuesta-errores')
                self.assertContains(respuesta, 'Manzanaᵀ')
                resultados.append(Contenido(respuesta.content.decode()).tablas['Resultado'])
        self.assertEqual(resultados[0], [['1', '4'], ['2', '5'], ['3', '6']])
        self.assertEqual(resultados[0], resultados[1])

    def test_ejemplo_obligatorio_y_la_suma_equivalente(self):
        for expresion, fragmentos in (
            ("A(u + v)", ("u + v = [1, 4]", "A(u + v) = [22, 7]")),
            ("Au + Av", ("Au = [3, 11]", "Av = [19, -4]", "Au + Av = [22, 7]")),
            ("A * (u + v)", ("A * (u + v) = [22, 7]",)),
        ):
            with self.subTest(expresion=expresion):
                html = self.client.post(RUTA, datos_expresion(expresion, EJEMPLO)).content.decode()
                texto = str(Texto(html))
                for fragmento in fragmentos:
                    self.assertIn(fragmento, texto)
                self.assertLess(html.index("panel-final"), html.index('id="procedimiento"'))
                self.assertIn('name="nodo" value="0.1"', html)

    def test_subexpresion_por_el_identificador_del_nodo(self):
        html = self.client.post(RUTA, datos_expresion("A(u + v)", EJEMPLO, nodo="0.1")).content.decode()
        texto = str(Texto(html))
        self.assertIn("u + v = [1, 4]", texto)
        self.assertNotIn("A(u + v) = [22, 7]", texto)
        self.assertIn("Subexpresión", texto)

    def test_fraccion_exacta_en_el_resultado(self):
        respuesta = self.client.post(RUTA, datos_expresion("k*A", (
            {"nombre": "A", "tipo": "matriz", "valor": [["1/2"]]},
            {"nombre": "k", "tipo": "escalar", "valor": "-3/4"},
        )))
        self.assertContains(respuesta, "-3/8")
        self.assertContains(respuesta, "data-numeric")
        self.assertIn('data-numeric-controls hidden', respuesta.content.decode())

    def test_el_servicio_delega_en_el_evaluador(self):
        simbolos = (
            {"nombre": "A", "tipo": "matriz", "valor": [[1, 2], [3, 4]]},
            {"nombre": "B", "tipo": "matriz", "valor": [[1, 0], [0, 1]]},
        )
        formulario = ExpresionMatricialForm(datos_expresion("A + B", simbolos))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        with patch("frontend.web.calculadora.servicios_expresiones.evaluar", wraps=evaluar_backend) as motor:
            resultado = evaluar_expresion_web(formulario.cleaned_data["entrada"])
        motor.assert_called_once()
        self.assertEqual(resultado["texto"], "A + B")
        self.assertEqual(resultado["matriz"], [["2", "2"], ["3", "5"]])


class PruebasSeguridad(SimpleTestCase):
    def rechazar(self, datos, mensaje):
        respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, mensaje)
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_celdas_de_mas_de_menos_y_tipo_invalido(self):
        datos = datos_expresion("A", EJEMPLO[:1])
        datos["celda_0_2_0"] = "1"
        self.rechazar(datos, "no coinciden")
        incompleto = datos_expresion("A", EJEMPLO[:1])
        del incompleto["celda_0_1_1"]
        self.rechazar(incompleto, "no coinciden")
        self.rechazar(datos_expresion("A", ({"nombre": "A", "tipo": "matriz", "valor": [[1, 2], [3, 4]]},), tipo_0="inversa"), "matriz, vector o escalar")

    def test_nombre_repetido_simbolo_ajeno_y_sintaxis(self):
        repetido = datos_expresion("A + B", (
            {"nombre": "A", "tipo": "escalar", "valor": "1"},
            {"nombre": "A", "tipo": "escalar", "valor": "2"},
        ))
        self.rechazar(repetido, "está repetido")
        self.rechazar(datos_expresion("A + Z", EJEMPLO[:1]), "El operando Z no está definido")
        self.rechazar(datos_expresion("A + * B", EJEMPLO[:1] + ({"nombre": "B", "tipo": "matriz", "valor": [[1, 0], [0, 1]]},)), "operando")

    def test_dimensiones_incompatibles_en_la_subexpresion(self):
        self.rechazar(datos_expresion("A(B + C)", (
            {"nombre": "A", "tipo": "matriz", "valor": [[1, 0], [0, 1]]},
            {"nombre": "B", "tipo": "matriz", "valor": [[1, 2], [3, 4]]},
            {"nombre": "C", "tipo": "matriz", "valor": [[1, 2, 3]]},
        )), "No se puede calcular B + C")

    def test_campos_duplicados_y_html_escapado(self):
        datos = QueryDict(mutable=True)
        datos.update(datos_expresion("A", EJEMPLO[:1]))
        datos.appendlist("nombre_0", "A")
        formulario = ExpresionMatricialForm(datos)
        self.assertFalse(formulario.is_valid())
        self.assertIn("campos repetidos", str(formulario.non_field_errors()))
        ataque = datos_expresion("A", EJEMPLO[:1])
        ataque["nombre_0"] = "A<img>"
        respuesta = self.client.post(RUTA, ataque)
        self.assertNotContains(respuesta, "A<img>")
        self.assertContains(respuesta, "A&lt;img&gt;")

    def test_csrf_exigido_y_envio_valido(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(RUTA, datos_expresion("A(u + v)", EJEMPLO)).status_code, 403)
        cliente.get(RUTA)
        token = cliente.cookies["csrftoken"].value
        respuesta = cliente.post(RUTA, datos_expresion("A(u + v)", EJEMPLO, csrfmiddlewaretoken=token))
        self.assertContains(respuesta, "[22, 7]")

    def test_el_resultado_usa_las_mismas_primitivas_que_la_operacion_directa(self):
        a = [[2, 5], [3, 1]]
        u = [4, -1]
        formulario = ExpresionMatricialForm(datos_expresion("Au", EJEMPLO[:2]))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        resultado = evaluar_expresion_web(formulario.cleaned_data["entrada"])
        self.assertEqual(resultado["igualdad"], "Au = [3, 11]")
        self.assertEqual([3, 11], multiplicar_matriz_vector(a, u))
        suma = ExpresionMatricialForm(datos_expresion("A + A", EJEMPLO[:1]))
        self.assertTrue(suma.is_valid(), suma.errors)
        self.assertEqual(
            evaluar_expresion_web(suma.cleaned_data["entrada"])["matriz"],
            [["4", "10"], ["6", "2"]],
        )
        self.assertEqual(sumar_matrices(a, a), [[4, 10], [6, 2]])


class PruebasIgualdadWeb(SimpleTestCase):
    def test_ejemplo_obligatorio(self):
        html = self.client.post(RUTA, datos_expresion("A(u + v) = Au + Av", EJEMPLO)).content.decode()
        texto = str(Texto(html))
        for fragmento in (
            "Lado izquierdo", "u + v = [1, 4]", "A(u + v) = [22, 7]",
            "Lado derecho", "Au = [3, 11]", "Av = [19, -4]", "Au + Av = [22, 7]",
            "Ambos lados coinciden", "producen [22, 7]",
        ):
            self.assertIn(fragmento, texto)
        self.assertNotIn("Verdadero", texto)
        self.assertNotIn("demostr", texto)
        # El procedimiento de cada lado va plegado antes; los dos valores y el veredicto forman el resultado.
        self.assertLess(html.index('id="lado-izquierdo-title"'), html.index('id="procedimiento"'))
        # El veredicto primero; después, el valor de cada lado.
        self.assertLess(html.index("panel-final"), html.index('id="lado-izquierdo-title"'))
        self.assertEqual(html.count('id="procedimiento"'), 1)
        self.assertEqual(html.count('id="numeric-mode"'), 1)
        self.assertIn('name="nodo" value="izq:0.1"', html)
        self.assertIn('name="nodo" value="der:0.0"', html)
        self.assertNotIn('name="nodo" value="0.1"', html)

    def test_falsa_e_incompatible_no_son_un_error(self):
        falsa = self.client.post(RUTA, datos_expresion("Au = Av", EJEMPLO))
        texto = str(Texto(falsa.content.decode()))
        self.assertContains(falsa, 'id="resultado"')
        self.assertIn("Los resultados son diferentes", texto)
        self.assertIn("[3, 11]", texto)
        self.assertIn("[19, -4]", texto)
        incompatible = self.client.post(RUTA, datos_expresion("A = u", EJEMPLO[:2]))
        aviso = str(Texto(incompatible.content.decode()))
        self.assertContains(incompatible, 'id="resultado"')
        self.assertIn("No se pueden comparar ambos lados", aviso)
        self.assertIn("matriz 2×2", aviso)
        self.assertIn("vector de 2 componentes", aviso)
        self.assertNotIn("Falso", aviso)

    def test_fraccion_exacta_aunque_el_decimal_no_sume_uno(self):
        respuesta = self.client.post(RUTA, {"expresion": "(1/3) + (1/3) + (1/3) = 1", "cantidad": "0"})
        html = respuesta.content.decode()
        self.assertIn("Ambos lados coinciden", str(Texto(html)))
        self.assertIn("producen 1", str(Texto(html)))
        self.assertIn("1/3", str(Texto(html)))
        self.assertIn("0.3333", html)
        self.assertEqual(html.count('id="numeric-mode"'), 1)

    def test_subexpresion_de_cada_lado(self):
        izquierda = self.client.post(RUTA, datos_expresion("A(u + v) = Au + Av", EJEMPLO, nodo="izq:0.1"))
        texto = str(Texto(izquierda.content.decode()))
        self.assertIn("u + v = [1, 4]", texto)
        self.assertIn("Subexpresión", texto)
        self.assertNotIn("Ambos lados coinciden", texto)
        derecha = str(Texto(self.client.post(RUTA, datos_expresion("A(u + v) = Au + Av", EJEMPLO, nodo="der:0.1")).content.decode()))
        self.assertIn("Av = [19, -4]", derecha)
        self.assertNotIn("Au + Av = [22, 7]", derecha)

    def rechazar(self, datos, mensaje):
        respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, mensaje)
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_rutas_manipuladas_sintaxis_y_simbolo_desconocido(self):
        for nodo in ("0.1", "izq:9", "der:0.1.9", "izq:0;id", "<script>", "medio:0"):
            with self.subTest(nodo=nodo):
                self.rechazar(datos_expresion("A(u + v) = Au + Av", EJEMPLO, nodo=nodo), "No existe la subexpresión")
        ataque = self.client.post(RUTA, datos_expresion("A = A", EJEMPLO[:1], nodo="<script>")).content.decode()
        self.assertIn("&lt;script&gt;", ataque)
        self.assertNotIn("«<script>»", ataque)
        datos = datos_expresion("A = A", EJEMPLO[:1], nodo="izq:0")
        datos["eval"] = "1"
        self.rechazar(datos, "no coinciden")
        self.rechazar(datos_expresion("A =", EJEMPLO[:1]), "lado derecho")
        self.rechazar(datos_expresion("= A", EJEMPLO[:1]), "lado izquierdo")
        self.rechazar(datos_expresion("A = A = A", EJEMPLO[:1]), "una igualdad")
        self.rechazar(datos_expresion("A == A", EJEMPLO[:1]), "==")
        self.rechazar(datos_expresion("A + = A", EJEMPLO[:1]), "lado izquierdo")
        self.rechazar(datos_expresion("A = Z", EJEMPLO[:1]), "El operando Z no está definido")
        self.rechazar(datos_expresion("(A = A", EJEMPLO[:1]), "paréntesis")
        self.rechazar(datos_expresion("A(B + C) = D", (
            {"nombre": "A", "tipo": "matriz", "valor": [[1, 0], [0, 1]]},
            {"nombre": "B", "tipo": "matriz", "valor": [[1, 2], [3, 4]]},
            {"nombre": "C", "tipo": "matriz", "valor": [[1, 2, 3]]},
            {"nombre": "D", "tipo": "matriz", "valor": [[1, 0], [0, 1]]},
        )), "En el lado izquierdo")


class PruebasCaracterizacionFormulario(SimpleTestCase):
    """Lo que ExpresionMatricialForm entrega a la vista: `estado` para redibujar o `entrada` para calcular.

    Fija el orden de las validaciones (cada fase con errores detiene las siguientes),
    el campo de cada mensaje y el armado de los operandos de cada tipo.
    """

    OPERANDOS = (
        {"nombre": "A", "tipo": "matriz", "valor": [[1, "1/2"], [3, "-4"]]},
        {"nombre": "u", "tipo": "vector", "valor": [4, "0.5"]},
        {"nombre": "k", "tipo": "escalar", "valor": "2/3"},
        {"nombre": "w", "tipo": "vector_lineal", "valor": ["3x1 - 2x2", "x2"]},
        {"nombre": "X", "tipo": "matriz_desconocida", "filas": 2, "columnas": 1},
        {"nombre": "y", "tipo": "vector_simbolico", "filas": 2},
    )
    GRANDES = tuple({"nombre": f"M{i}", "tipo": "matriz", "valor": [[1] * 10 for _ in range(10)]} for i in range(10))

    def formulario(self, datos, accion=None):
        form = ExpresionMatricialForm(datos, accion=accion)
        form.is_valid()
        return form

    def errores(self, datos, accion=None):
        return [(campo, list(mensajes)) for campo, mensajes in self.formulario(datos, accion).errors.items()]

    def test_calcular_arma_un_operando_de_cada_tipo(self):
        form = self.formulario(datos_expresion(" k*A*u + w ", self.OPERANDOS, nodo=" 2 ", metodo="columnas"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertNotIn("estado", form.cleaned_data)
        self.assertEqual(form.cleaned_data["entrada"], {
            "expresion": "k*A*u + w",
            "simbolos": {
                "A": {"tipo": "matriz", "valor": [[1, Fraction(1, 2)], [3, -4]]},
                "u": {"tipo": "vector", "valor": [4, Fraction(1, 2)]},
                "k": {"tipo": "escalar", "valor": Fraction(2, 3)},
                "w": {"tipo": "vector_lineal", "valor": ["3x1 - 2x2", "x2"]},
                "X": {"tipo": "matriz_desconocida", "filas": 2, "columnas": 1},
                "y": {"tipo": "vector_simbolico", "filas": 2},
            },
            "nodo": "2", "metodo": "columnas",
        })
        sin_nodo = self.formulario(datos_expresion("A", self.OPERANDOS[:1])).cleaned_data["entrada"]
        self.assertEqual((sin_nodo["nodo"], sin_nodo["metodo"]), (None, "fila_columna"))

    def test_las_acciones_redibujan_sin_calcular_ni_exigir_celdas(self):
        datos = datos_expresion("", self.OPERANDOS[:3], metodo="comparar")
        datos["celda_0_0_1"] = ""  # una celda vacía no impide editar la estructura
        esperado = {
            "expresion": "", "cantidad": 3, "metodo": "comparar",
            "nombre_0": "A", "tipo_0": "matriz", "filas_0": 2, "columnas_0": 2,
            "celda_0_0_0": "1", "celda_0_0_1": "", "celda_0_1_0": "3", "celda_0_1_1": "-4",
            "nombre_1": "u", "tipo_1": "vector", "filas_1": 2, "celda_1_0_0": "4", "celda_1_1_0": "0.5",
            "nombre_2": "k", "tipo_2": "escalar", "celda_2_0_0": "2/3",
        }
        ajustado = self.formulario(dict(datos, ajustar="1"), "ajustar")
        self.assertNotIn("entrada", ajustado.cleaned_data)
        self.assertEqual(ajustado.cleaned_data["estado"], esperado)
        agregado = self.formulario(dict(datos, agregar="1"), "agregar").cleaned_data["estado"]
        self.assertEqual(agregado, esperado | {
            "cantidad": 4, "nombre_3": "B", "tipo_3": "matriz", "filas_3": 2, "columnas_3": 2,
            "celda_3_0_0": "", "celda_3_0_1": "", "celda_3_1_0": "", "celda_3_1_1": "",
        })
        eliminado = self.formulario(dict(datos, eliminar="0"), "eliminar").cleaned_data["estado"]
        self.assertEqual(eliminado, {
            "expresion": "", "cantidad": 2, "metodo": "comparar",
            "nombre_0": "u", "tipo_0": "vector", "filas_0": 2, "celda_0_0_0": "4", "celda_0_1_0": "0.5",
            "nombre_1": "k", "tipo_1": "escalar", "celda_1_0_0": "2/3",
        })
        # Sin JS, Aplicar con otra dimensión conserva lo escrito y dibuja vacías las celdas nuevas.
        html = self.client.post(RUTA, dict(datos, filas_0="3", ajustar="1")).content.decode()
        self.assertIn('name="celda_0_2_1"', html)
        self.assertRegex(html, r'name="celda_0_1_1" value="-4"')
        self.assertNotIn('id="resultado"', html)

    def test_cada_fase_con_errores_detiene_las_siguientes(self):
        base = datos_expresion("A*u", self.OPERANDOS[:2])
        nombre_y_celda = dict(base, nombre_0="1A")
        del nombre_y_celda["celda_1_1_0"]
        lineal_y_presupuesto = datos_expresion("+".join(["w"] * 60), self.OPERANDOS[3:4])
        lineal_y_presupuesto["celda_0_0_0"] = "3x1 +"
        casos = (
            # Nombres y dimensiones, antes que el contrato de celdas.
            (nombre_y_celda, None, [("nombre_0", ["Usa una letra seguida de letras o dígitos, como A, u o k."])]),
            (dict(base, nombre_1="A"), None, [("nombre_1", ["El operando A está repetido."])]),
            (dict(base, filas_0="", ajustar="1"), "ajustar", [("filas_0", ["Indica el número de filas."])]),
            # La expresión vacía se informa antes de leer las celdas.
            (dict(base, expresion=" ", celda_0_0_0="abc"), None, [("expresion", ["Escribe una expresión."])]),
            # Celdas y componentes lineales se informan juntos, antes del presupuesto de la expresión.
            (dict(base, celda_0_0_0="abc", celda_1_0_0=""), None, [
                ("celda_0_0_0", ["'abc' no es un número válido."]),
                ("celda_1_0_0", ["Completa vector u, componente 1."]),
            ]),
            (lineal_y_presupuesto, None, [("celda_0_0_0", ["La expresión está incompleta."])]),
            (datos_expresion("+".join(["A"] * 60), self.OPERANDOS[:1]), None, [("expresion", [
                "La expresión tiene 60 operandos y la interfaz admite hasta 50: "
                "cada aparición de un operando o de un número cuenta."])]),
            (datos_expresion("+".join(["A"] * 10), (dict(self.GRANDES[0], nombre="A"),)), None, [("expresion", [
                "Los operandos de la expresión suman 1000 entradas y la interfaz admite hasta 900: "
                "cada aparición de un operando cuenta todas sus entradas."])]),
            # La sintaxis la explica el servicio al evaluar.
            (dict(base, expresion="A + * ("), None, []),
            (dict(base, eliminar="5"), "eliminar", [("__all__", ["No se puede eliminar ese operando."])]),
        )
        for datos, accion, esperado in casos:
            with self.subTest(esperado=esperado, accion=accion):
                self.assertEqual(self.errores(datos, accion), esperado)

    def test_contrato_y_presupuestos_de_la_estructura(self):
        incompleto = datos_expresion("A", self.OPERANDOS[:1])
        del incompleto["celda_0_1_1"]
        form = self.formulario(incompleto)
        self.assertEqual(form.errors["__all__"], [
            "Las celdas recibidas no coinciden con los operandos indicados. Pulsa Aplicar para ajustar la estructura."])
        self.assertEqual(form.grupo_error, "symbol-list")
        # Con una acción solo se rechazan los campos ajenos: las celdas pueden faltar.
        self.assertTrue(self.formulario(dict(incompleto, ajustar="1"), "ajustar").is_valid())
        self.assertFalse(self.formulario(dict(incompleto, intruso="1", ajustar="1"), "ajustar").is_valid())
        for accion in (None, "ajustar"):
            with self.subTest(accion=accion):
                datos = datos_expresion("M0", self.GRANDES, **({accion: "1"} if accion else {}))
                form = self.formulario(datos, accion)
                self.assertEqual(form.errors["__all__"], [
                    "Los 10 operandos suman 1000 celdas y la interfaz admite hasta 900: "
                    "quita operandos o reduce sus dimensiones."])
                self.assertEqual(form.grupo_error, "symbol-list")
        escalares = [{"nombre": f"k{i}", "tipo": "escalar", "valor": 1} for i in range(50)]
        for operandos, mensaje in (
            (self.GRANDES[:9], "No se puede agregar otro operando: una matriz 2×2 más no cabe. Los 10 operandos "
                               "suman 904 celdas y la interfaz admite hasta 900: quita operandos o reduce sus dimensiones."),
            (escalares, "No se puede agregar otro operando: la interfaz admite hasta 50."),
        ):
            with self.subTest(mensaje=mensaje):
                form = self.formulario(datos_expresion("", operandos, agregar="1"), "agregar")
                self.assertEqual(form.errors["__all__"], [mensaje])
