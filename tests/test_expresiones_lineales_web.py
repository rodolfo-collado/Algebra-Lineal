"""Expresiones lineales en la herramienta web: determinación de A, formato y POST."""

import os
from html.parser import HTMLParser

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django

django.setup()

from django.test import Client, SimpleTestCase

from frontend.web.calculadora.forms_expresiones import ExpresionMatricialForm
from frontend.web.calculadora.servicios_expresiones import evaluar_expresion_web

RUTA = "/matrices/expresiones/"


def datos(expresion, simbolos, **extra):
    datos_post = {"expresion": expresion, "cantidad": str(len(simbolos))}
    for indice, simbolo in enumerate(simbolos):
        datos_post[f"nombre_{indice}"] = simbolo["nombre"]
        datos_post[f"tipo_{indice}"] = simbolo["tipo"]
        tipo = simbolo["tipo"]
        if tipo == "matriz_desconocida":
            datos_post[f"filas_{indice}"] = str(simbolo["filas"])
            datos_post[f"columnas_{indice}"] = str(simbolo["columnas"])
        elif tipo == "vector_simbolico":
            datos_post[f"filas_{indice}"] = str(simbolo["filas"])
        elif tipo == "vector_lineal":
            datos_post[f"filas_{indice}"] = str(len(simbolo["valor"]))
            for fila, texto in enumerate(simbolo["valor"]):
                datos_post[f"celda_{indice}_{fila}_0"] = texto
        elif tipo == "escalar":
            datos_post[f"celda_{indice}_0_0"] = str(simbolo["valor"])
        elif tipo == "vector":
            datos_post[f"filas_{indice}"] = str(len(simbolo["valor"]))
            for fila, componente in enumerate(simbolo["valor"]):
                datos_post[f"celda_{indice}_{fila}_0"] = str(componente)
        else:
            datos_post[f"filas_{indice}"] = str(len(simbolo["valor"]))
            datos_post[f"columnas_{indice}"] = str(len(simbolo["valor"][0]))
            for fila, renglon in enumerate(simbolo["valor"]):
                for columna, entrada in enumerate(renglon):
                    datos_post[f"celda_{indice}_{fila}_{columna}"] = str(entrada)
    datos_post.update(extra)
    return datos_post


PRINCIPAL = (
    {"nombre": "A", "tipo": "matriz_desconocida", "filas": 3, "columnas": 2},
    {"nombre": "x", "tipo": "vector_simbolico", "filas": 2},
    {"nombre": "b", "tipo": "vector_lineal", "valor": ["3x1 - 2x2", "x1 + 4x2", "x2"]},
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


class PruebasPagina(SimpleTestCase):
    def test_los_tipos_simbolicos_no_abren_otra_herramienta(self):
        respuesta = self.client.get(RUTA)
        self.assertContains(respuesta, "Matriz desconocida")
        self.assertContains(respuesta, "Vector simbólico")
        self.assertContains(respuesta, "Vector lineal")
        self.assertContains(respuesta, "Matriz A, fila 1, columna 1")
        self.assertNotContains(respuesta, 'id="resultado"')
        inicio = self.client.get("/")
        self.assertNotContains(inicio, "Hallar A")

    def test_aplicar_muestra_solo_los_campos_del_tipo(self):
        desconocida = self.client.post(RUTA, datos("", (
            {"nombre": "A", "tipo": "matriz_desconocida", "filas": 3, "columnas": 2},
        ), ajustar="1"))
        self.assertContains(desconocida, "Matriz desconocida: indica filas y columnas")
        self.assertNotContains(desconocida, 'name="celda_0_0_0"')
        self.assertNotContains(desconocida, 'id="resultado"')
        simbolico = self.client.post(RUTA, datos("", (
            {"nombre": "x", "tipo": "vector_simbolico", "filas": 2},
        ), ajustar="1"))
        self.assertContains(simbolico, "Componentes independientes: x1, x2.")
        self.assertNotContains(simbolico, 'name="celda_0_0_0"')
        lineal = self.client.post(RUTA, datos("", (
            {"nombre": "b", "tipo": "vector_lineal", "valor": ["3x1 - 2x2", "x2"]},
        ), ajustar="1"))
        self.assertContains(lineal, 'placeholder="3x1 - 2x2"')
        self.assertContains(lineal, "3x1 - 2x2")
        self.assertNotContains(lineal, 'id="resultado"')


class PruebasDeterminacion(SimpleTestCase):
    def test_el_caso_principal_explica_las_columnas(self):
        html = self.client.post(RUTA, datos("Ax = b", PRINCIPAL)).content.decode()
        texto = str(Texto(html))
        for fragmento in (
            "Matriz determinada · 3×2",
            "para todos los valores de x1 y x2",
            "Cómo se obtuvo",
            "Escribir A por columnas",
            "A = [a1 a2]",
            "Ax = x1 a1 + x2 a2",
            "b = x1 [3, 1, 0]^T + x2 [-2, 4, 1]^T",
            "a1 = [3, 1, 0]^T",
            "a2 = [-2, 4, 1]^T",
            "componente 1: 3x1 - 2x2 coincide",
            "componente 3: x2 coincide",
            "No se sustituyen valores de prueba",
        ):
            self.assertIn(fragmento, texto, fragmento)
        self.assertNotIn("valores dados", texto)
        self.assertNotIn("x1 = 1", texto)
        self.assertLess(html.index("panel-final"), html.index('id="procedimiento"'))
        self.assertEqual(html.count('id="procedimiento"'), 1)
        self.assertEqual(html.count('id="numeric-mode"'), 1)

    def test_fraccion_exacta_y_decimal_preparado(self):
        simbolos = (
            {"nombre": "A", "tipo": "matriz_desconocida", "filas": 1, "columnas": 2},
            {"nombre": "x", "tipo": "vector_simbolico", "filas": 2},
            {"nombre": "b", "tipo": "vector_lineal", "valor": ["(1/2)x1 - (3/4)x2"]},
        )
        html = self.client.post(RUTA, datos("Ax = b", simbolos)).content.decode()
        self.assertIn("1/2", html)
        self.assertIn("-3/4", html)
        self.assertIn("0.5", html)
        self.assertIn("-0.75", html)
        self.assertEqual(html.count('id="numeric-mode"'), 1)

    def test_igualdad_simbolica_de_una_matriz_conocida(self):
        simbolos = (
            {"nombre": "A", "tipo": "matriz", "valor": [[3, -2], [1, 4], [0, 1]]},
            {"nombre": "x", "tipo": "vector_simbolico", "filas": 2},
            {"nombre": "b", "tipo": "vector_lineal", "valor": ["3x1 - 2x2", "x1 + 4x2", "x2"]},
        )
        texto = str(Texto(self.client.post(RUTA, datos("Ax = b", simbolos)).content.decode()))
        self.assertIn("Igualdad simbólica", texto)
        self.assertIn("Misma expresión lineal", texto)
        self.assertIn("para todos los valores de x1 y x2", texto)
        self.assertNotIn("valores dados", texto)
        self.assertNotIn("Matriz determinada", texto)

    def test_la_comparacion_numerica_de_p21_no_cambia(self):
        ejemplo = (
            {"nombre": "A", "tipo": "matriz", "valor": [[2, 5], [3, 1]]},
            {"nombre": "u", "tipo": "vector", "valor": [4, -1]},
            {"nombre": "v", "tipo": "vector", "valor": [-3, 5]},
        )
        texto = str(Texto(self.client.post(RUTA, datos("A(u + v) = Au + Av", ejemplo)).content.decode()))
        self.assertIn("Ambos lados coinciden", texto)
        self.assertIn("para los valores dados", texto)
        self.assertIn("[22, 7]", texto)
        self.assertNotIn("Igualdad simbólica", texto)
        self.assertNotIn("Matriz determinada", texto)


class PruebasSeguridad(SimpleTestCase):
    def rechazar(self, carga, mensaje):
        respuesta = self.client.post(RUTA, carga)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, mensaje)
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_estructura_manipulada(self):
        con_celdas = datos("Ax = b", PRINCIPAL)
        con_celdas["celda_0_0_0"] = "1"
        self.rechazar(con_celdas, "no coinciden")
        sin_componente = datos("Ax = b", PRINCIPAL)
        del sin_componente["celda_2_2_0"]
        self.rechazar(sin_componente, "no coinciden")
        self.rechazar(datos("Ax = b", PRINCIPAL, tipo_1="vector"), "no coinciden")
        self.rechazar(datos("A", ({"nombre": "A", "tipo": "matriz", "valor": [[1, 2], [3, 4]]},), tipo_0="inversa"), "matriz, vector o escalar")

    def test_componentes_no_lineales_ajenas_constantes_y_dimensiones(self):
        self.rechazar(datos("Ax = b", (
            {"nombre": "A", "tipo": "matriz_desconocida", "filas": 1, "columnas": 2},
            {"nombre": "x", "tipo": "vector_simbolico", "filas": 2},
            {"nombre": "b", "tipo": "vector_lineal", "valor": ["x1*x2"]},
        )), "multiplica dos cantidades simbólicas")
        self.rechazar(datos("Ax = b", (
            {"nombre": "A", "tipo": "matriz_desconocida", "filas": 2, "columnas": 2},
            {"nombre": "x", "tipo": "vector_simbolico", "filas": 2},
            {"nombre": "b", "tipo": "vector_lineal", "valor": ["x1 + x3", "x2"]},
        )), "contiene x3")
        self.rechazar(datos("Ax = b", (
            {"nombre": "A", "tipo": "matriz_desconocida", "filas": 2, "columnas": 2},
            {"nombre": "x", "tipo": "vector_simbolico", "filas": 2},
            {"nombre": "b", "tipo": "vector_lineal", "valor": ["x1 + 2", "x2"]},
        )), "término constante independiente")
        self.rechazar(datos("Ax = b", (
            {"nombre": "A", "tipo": "matriz_desconocida", "filas": 3, "columnas": 2},
            {"nombre": "x", "tipo": "vector_simbolico", "filas": 3},
            {"nombre": "b", "tipo": "vector_lineal", "valor": ["x1", "x2", "x3"]},
        )), "necesita un vector de 2 componentes")
        self.rechazar(datos("Ax = b", (
            {"nombre": "A", "tipo": "matriz_desconocida", "filas": 3, "columnas": 2},
            {"nombre": "x", "tipo": "vector_simbolico", "filas": 2},
            {"nombre": "b", "tipo": "vector_lineal", "valor": ["x1", "x2", "x1", "x2"]},
        )), "Ax tiene 3 componentes pero b tiene 4")

    def test_el_texto_de_la_componente_no_se_ejecuta_ni_se_inyecta(self):
        ataque = datos("Ax = b", (
            {"nombre": "A", "tipo": "matriz_desconocida", "filas": 1, "columnas": 1},
            {"nombre": "x", "tipo": "vector_simbolico", "filas": 1},
            {"nombre": "b", "tipo": "vector_lineal", "valor": ['__import__("os")']},
        ))
        respuesta = self.client.post(RUTA, ataque)
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertNotIn("os.system", respuesta.content.decode())
        html = self.client.post(RUTA, datos("b<img>", (
            {"nombre": "b", "tipo": "vector_lineal", "valor": ["x1"]},
        ))).content.decode()
        self.assertNotIn("b<img>", html)
        formulario = ExpresionMatricialForm(datos("Ax = b", PRINCIPAL))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        servicio = evaluar_expresion_web(formulario.cleaned_data["entrada"])
        self.assertEqual(servicio["matriz"], [["3", "-2"], ["1", "4"], ["0", "1"]])
        self.assertTrue(servicio["verificada"])

    def test_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(RUTA, datos("Ax = b", PRINCIPAL)).status_code, 403)
        cliente.get(RUTA)
        token = cliente.cookies["csrftoken"].value
        respuesta = cliente.post(RUTA, datos("Ax = b", PRINCIPAL, csrfmiddlewaretoken=token))
        self.assertContains(respuesta, "a1 = [3, 1, 0]^T")
