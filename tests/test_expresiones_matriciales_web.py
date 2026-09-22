"""Herramienta web de expresiones matriciales: catálogo, POST, procedimiento y formato."""

import os
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

RUTA = "/matrices/expresiones/"


def datos_expresion(expresion, simbolos, **extra):
    datos = {"expresion": expresion, "cantidad": str(len(simbolos))}
    for indice, simbolo in enumerate(simbolos):
        datos[f"nombre_{indice}"] = simbolo["nombre"]
        datos[f"tipo_{indice}"] = simbolo["tipo"]
        valor = simbolo["valor"]
        if simbolo["tipo"] == "escalar":
            datos[f"celda_{indice}_0_0"] = str(valor)
        elif simbolo["tipo"] == "vector":
            datos[f"filas_{indice}"] = str(len(valor))
            for fila, componente in enumerate(valor):
                datos[f"celda_{indice}_{fila}_0"] = str(componente)
        else:
            datos[f"filas_{indice}"] = str(len(valor))
            datos[f"columnas_{indice}"] = str(len(valor[0]))
            for fila, renglon in enumerate(valor):
                for columna, entrada in enumerate(renglon):
                    datos[f"celda_{indice}_{fila}_{columna}"] = str(entrada)
    datos.update(extra)
    return datos


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
    def test_entra_en_matrices_y_queda_relacionada(self):
        herramienta = catalogo.EXPRESIONES_MATRICIALES
        self.assertEqual(herramienta.ruta, RUTA)
        self.assertEqual(herramienta.categoria, catalogo.MATRICES)
        self.assertEqual(
            catalogo.herramientas_de(catalogo.MATRICES),
            (catalogo.OPERACIONES_MATRICES, herramienta, catalogo.ECUACIONES_MATRICIALES),
        )
        self.assertEqual(
            set(herramienta.relacionadas),
            {"operaciones-matrices", "ecuaciones-matriciales", "operaciones-vectores"},
        )
        respuesta = self.client.get("/")
        self.assertContains(respuesta, 'href="/matrices/expresiones/"')
        self.assertContains(respuesta, "Expresiones matriciales")
        self.assertNotContains(respuesta, "Acceso rápido")


class PruebasPagina(SimpleTestCase):
    def test_get_empieza_con_un_simbolo_y_sin_resultado(self):
        respuesta = self.client.get(RUTA)
        self.assertContains(respuesta, 'id="expresiones-form"')
        self.assertContains(respuesta, 'name="nombre_0"')
        self.assertContains(respuesta, "Matriz A, fila 1, columna 1")
        self.assertNotContains(respuesta, 'name="nombre_1"')
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


class PruebasCalculo(SimpleTestCase):
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
        self.rechazar(datos_expresion("A + Z", EJEMPLO[:1]), "El símbolo Z no está definido")
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
