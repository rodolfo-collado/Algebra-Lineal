"""Contratos de navegación y comparación mediante HTML y POST, sin depender de CSS."""

import json
import os
from dataclasses import replace
from html.parser import HTMLParser
from unittest.mock import patch
from urllib.parse import urlsplit

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase
from django.urls import resolve, reverse
from django.utils.html import escape

from frontend.web.calculadora import catalogo
from frontend.web.calculadora.conexiones import COMPARACIONES
from frontend.web.calculadora.forms import SistemaForm
from frontend.web.calculadora.servicios import resolver_entrada_web
from tests.test_web import datos_matriz


class Documento(HTMLParser):
    """Extrae contratos HTML públicos: enlaces, controles y formularios."""

    def __init__(self, respuesta):
        super().__init__()
        self.enlaces = []
        self.controles = []
        self.formularios = []
        self.ids = []
        self.navegacion = None
        self.feed(respuesta.content.decode("utf-8"))

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if "id" in atributos:
            self.ids.append(atributos["id"])
        if tag == "nav":
            self.navegacion = atributos.get("aria-label")
        if tag == "a":
            self.enlaces.append((self.navegacion, atributos))
        if tag in ("input", "button"):
            self.controles.append(atributos)
        if tag == "form":
            self.formularios.append(atributos)

    def handle_endtag(self, tag):
        if tag == "nav":
            self.navegacion = None


class PruebasCatalogo(SimpleTestCase):
    def test_ids_unicos_de_modulos_y_categorias(self):
        for elementos in (catalogo.MODULOS, catalogo.CATEGORIAS):
            ids = [elemento.id for elemento in elementos]
            self.assertEqual(len(ids), len(set(ids)))

    def test_modulos_con_categoria_y_estado_validos(self):
        for modulo in catalogo.MODULOS:
            with self.subTest(modulo=modulo.id):
                self.assertIn(modulo.categoria, catalogo.CATEGORIAS)
                self.assertIn(modulo.estado, ("disponible", "proximamente"))

    def test_disponibles_tienen_ruta_resoluble(self):
        for modulo in catalogo.MODULOS:
            if modulo.estado == "disponible":
                ruta = reverse(modulo.route_name)
                self.assertEqual(resolve(ruta).view_name, modulo.route_name)
                self.assertEqual(self.client.get(ruta).status_code, 200)

    def test_relaciones_referencian_ids_existentes(self):
        ids = {modulo.id for modulo in catalogo.MODULOS}
        for modulo in catalogo.MODULOS:
            self.assertTrue(set(modulo.relacionados) <= ids)
            self.assertNotIn(modulo.id, modulo.relacionados)

    def test_relaciones_filtran_modulos_no_disponibles(self):
        modulo = replace(catalogo.MODULOS[1], relacionados=("sistemas", "matrices"))
        self.assertEqual(catalogo.relacionados_disponibles(modulo), (catalogo.SISTEMAS,))

    def test_grupos_omiten_categorias_sin_modulos_disponibles(self):
        grupos = catalogo.grupos_disponibles()
        self.assertEqual(grupos, ((catalogo.SISTEMAS_LINEALES, (catalogo.SISTEMAS,)),))

    def test_comparaciones_usan_metodos_validos(self):
        metodos = dict(SistemaForm.METODOS)
        self.assertEqual(set(COMPARACIONES), set(metodos))
        for origen, conexion in COMPARACIONES.items():
            self.assertIn(conexion.metodo, metodos)
            self.assertNotEqual(origen, conexion.metodo)


class PruebasNavegacion(SimpleTestCase):
    def test_inicio_es_general_sin_formulario_matematico(self):
        respuesta = self.client.get(reverse("calculadora:inicio"))
        self.assertContains(respuesta, "Inicio · Álgebra Lineal")
        self.assertContains(respuesta, "Explora los temas disponibles")
        self.assertContains(respuesta, "Aprende resolviendo")
        self.assertNotContains(respuesta, 'name="sistema"')
        self.assertNotContains(respuesta, "calculadora/matriz.js")
        self.assertNotContains(respuesta, 'aria-label="Ruta de navegación"')

    def test_inicio_muestra_modulos_disponibles_del_catalogo(self):
        respuesta = self.client.get("/")
        for modulo in catalogo.MODULOS:
            if modulo.estado == "disponible":
                self.assertContains(respuesta, modulo.nombre)
                self.assertContains(respuesta, f'href="{reverse(modulo.route_name)}"')
                for contenido in modulo.contenidos:
                    self.assertContains(respuesta, contenido)

    def test_proximamente_sin_enlaces_falsos(self):
        respuesta = self.client.get("/")
        for modulo in catalogo.MODULOS:
            if modulo.estado == "proximamente":
                self.assertContains(respuesta, modulo.nombre)
        self.assertContains(respuesta, "Próximamente · No disponible", count=3)
        destinos = {attrs["href"] for _, attrs in Documento(respuesta).enlaces}
        self.assertEqual(
            destinos,
            {
                "/",
                "/sistemas/",
                "#contenido",
                "#fundamentos",
                "#vectores",
                "#matrices",
                "#sistemas-lineales",
                "#proximamente",
            },
        )

    def test_sistemas_tiene_url_propia(self):
        self.assertEqual(reverse("calculadora:sistemas"), "/sistemas/")
        self.assertContains(self.client.get("/sistemas/"), 'id="sistema-form"')

    def test_inicio_no_resuelve_post(self):
        self.assertEqual(self.client.post("/", {"sistema": "x1=1"}).status_code, 405)

    def test_navegacion_activa_segun_pagina(self):
        for ruta in ("/", "/sistemas/"):
            with self.subTest(ruta=ruta):
                enlaces = Documento(self.client.get(ruta)).enlaces
                activos = [a["href"] for nav, a in enlaces
                           if nav == "Navegación principal" and a.get("aria-current") == "page"]
                self.assertEqual(activos, [ruta])
                destinos = {a["href"] for nav, a in enlaces if nav == "Navegación principal"}
                self.assertEqual(destinos, {"/", "/sistemas/"})

    def test_breadcrumb_deriva_de_categoria_y_modulo(self):
        respuesta = self.client.get("/sistemas/")
        documento = Documento(respuesta)
        enlaces = [a["href"] for nav, a in documento.enlaces if nav == "Ruta de navegación"]
        self.assertEqual(enlaces, ["/", f"/#{catalogo.SISTEMAS.categoria.id}"])
        self.assertContains(respuesta, f'<span aria-current="page">{catalogo.SISTEMAS.nombre}</span>', html=True)
        self.assertIn(catalogo.SISTEMAS.categoria.id, Documento(self.client.get("/")).ids)

    def test_enlaces_y_anclas_de_paginas_y_resultados_existen(self):
        for ruta, respuesta in (
            ("/", self.client.get("/")),
            ("/sistemas/", self.client.get("/sistemas/")),
            ("/sistemas/", self.client.post("/sistemas/", {"sistema": "x1=1", "metodo": "gauss"})),
        ):
            documento = Documento(respuesta)
            self.assertEqual(len(documento.ids), len(set(documento.ids)))
            for _, enlace in documento.enlaces:
                destino = urlsplit(enlace["href"])
                self.assertFalse(destino.netloc)
                if destino.path:
                    pagina = self.client.get(destino.path)
                    self.assertEqual(pagina.status_code, 200)
                    ids = Documento(pagina).ids
                else:
                    ids = documento.ids
                if destino.fragment:
                    self.assertIn(destino.fragment, ids)

    def test_html_inicial_permite_navegar_y_resolver_sin_javascript(self):
        inicio = self.client.get("/")
        self.assertContains(inicio, '<nav id="navegacion-principal" class="app-navigation" aria-label="Navegación principal">')
        pagina = self.client.get("/sistemas/")
        formulario = Documento(pagina).formularios[0]
        self.assertEqual(formulario["method"], "post")
        respuesta = self.client.post(formulario["action"], {"metodo": "gauss", "sistema": "x1=7"})
        self.assertContains(respuesta, "x1 = 7")
        self.assertContains(respuesta, "Para editar la cuadrícula de una matriz, activa JavaScript.")

    def test_landmarks_skip_link_y_control_movil(self):
        for ruta in ("/", "/sistemas/"):
            respuesta = self.client.get(ruta)
            documento = Documento(respuesta)
            self.assertContains(respuesta, 'href="#contenido"')
            self.assertContains(respuesta, '<main id="contenido"')
            control = next(c for c in documento.controles if c.get("id") == "navigation-toggle")
            self.assertEqual(control["type"], "button")
            self.assertEqual(control["aria-expanded"], "false")
            self.assertIn(control["aria-controls"], documento.ids)


class PruebasComparacion(SimpleTestCase):
    TEXTO = "  x1 + x2 = 3;\nx1 - x2 = 1  "

    def comparar(self, datos, destino):
        inicial = self.client.post("/sistemas/", datos)
        documento = Documento(inicial)
        boton = next(c for c in documento.controles if c.get("name") == "metodo_alternativo")
        self.assertEqual(boton["value"], destino)
        self.assertEqual(boton["form"], documento.formularios[0]["id"])
        datos = {**datos, boton["name"]: boton["value"]}
        with patch("frontend.web.calculadora.views.resolver_entrada_web", wraps=resolver_entrada_web) as resolver:
            respuesta = self.client.post("/sistemas/", datos)
        resolver.assert_called_once()
        self.assertEqual(resolver.call_args.args[1], destino)
        self.assertEqual(respuesta.status_code, 200)
        seleccionados = [c["value"] for c in Documento(respuesta).controles
                         if c.get("name") == "metodo" and "checked" in c]
        self.assertEqual(seleccionados, [destino])
        self.assertContains(respuesta, dict(SistemaForm.METODOS)[destino])
        return respuesta

    def test_gauss_a_gauss_jordan_conserva_texto(self):
        respuesta = self.comparar({"sistema": self.TEXTO, "metodo": "gauss"}, "gauss_jordan")
        self.assertContains(respuesta, escape(self.TEXTO))
        self.assertContains(respuesta, "x1 = 2")
        self.assertContains(respuesta, "x2 = 1")

    def test_gauss_jordan_a_gauss_conserva_texto(self):
        respuesta = self.comparar({"sistema": self.TEXTO, "metodo": "gauss_jordan"}, "gauss")
        self.assertContains(respuesta, escape(self.TEXTO))
        self.assertContains(respuesta, "Sustitución regresiva")
        self.assertContains(respuesta, "x1 = 2")

    def test_comparar_matriz_rectangular_conserva_dimensiones_valores_y_fracciones(self):
        matriz = [["1/2", "1/2", "3/2"], ["1", "-1", "1"], ["2", "0", "4"]]
        for origen, destino in (("gauss", "gauss_jordan"), ("gauss_jordan", "gauss")):
            with self.subTest(origen=origen):
                respuesta = self.comparar(datos_matriz(matriz, origen), destino)
                self.assertContains(respuesta, json.dumps(matriz))
                controles = Documento(respuesta).controles
                for nombre, valor in (("ecuaciones", "3"), ("variables", "2")):
                    self.assertEqual(next(c["value"] for c in controles if c.get("name") == nombre), valor)
                self.assertContains(respuesta, "x1 = 2")
                self.assertContains(respuesta, "x2 = 1")

    def test_pivotes_y_conexion_apuntan_al_mismo_bloque(self):
        respuesta = self.client.post("/sistemas/", {"sistema": "x1+x3=4;x3=2", "metodo": "gauss"})
        self.assertContains(respuesta, 'id="columnas-pivote"', count=1)
        self.assertContains(respuesta, '<a href="#columnas-pivote">Revisar columnas pivote</a>', html=True)
        self.assertContains(respuesta, "C1")
        self.assertContains(respuesta, "C3")
        self.assertContains(respuesta, 'class="pivot-chip"')
        self.assertContains(respuesta, "Guía de concepto")
        self.assertContains(respuesta, "Gauss se detiene en forma escalonada")

    def test_metodo_alternativo_invalido_no_ejecuta_resolucion(self):
        for metodo in ("", "inexistente"):
            with self.subTest(metodo=metodo), patch("frontend.web.calculadora.views.resolver_entrada_web") as resolver:
                respuesta = self.client.post("/sistemas/", {"sistema": self.TEXTO, "metodo": "gauss", "metodo_alternativo": metodo})
                resolver.assert_not_called()
                self.assertContains(respuesta, escape(self.TEXTO))
                self.assertNotContains(respuesta, "Continúa explorando")

    def test_comparacion_valida_revalida_la_entrada(self):
        respuesta = self.client.post("/sistemas/", {"sistema": "x1+=1", "metodo": "gauss", "metodo_alternativo": "gauss_jordan"})
        self.assertContains(respuesta, "Formato de sistema inválido")
        self.assertNotContains(respuesta, "Continúa explorando")

    def test_no_hay_recomendaciones_antes_de_resolver(self):
        self.assertNotContains(self.client.get("/sistemas/"), "Continúa explorando")

    def test_comparacion_exige_csrf(self):
        from django.test import Client

        respuesta = Client(enforce_csrf_checks=True).post("/sistemas/", {
            "sistema": self.TEXTO, "metodo": "gauss", "metodo_alternativo": "gauss_jordan",
        })
        self.assertEqual(respuesta.status_code, 403)
