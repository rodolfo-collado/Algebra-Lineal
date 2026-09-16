"""Contratos de navegación, buscador y breadcrumbs mediante HTML y POST, sin depender de CSS."""

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
from django.utils.html import escape, strip_tags

from frontend.web.calculadora import catalogo
from frontend.web.calculadora.opciones_sistemas import (
    BLOQUES,
    BLOQUES_PREDETERMINADOS,
    METODO_PREDETERMINADO,
    METODOS,
    RUTAS_ANTIGUAS,
)
from frontend.web.calculadora.servicios import resolver_entrada_web
from tests.test_web import datos_matriz

PSEUDO_HERRAMIENTAS = ("Método de Gauss", "Gauss-Jordan", "Clasificación de sistemas", "Columnas pivote")


class Documento(HTMLParser):
    """Extrae contratos HTML públicos: enlaces, controles, formularios y el árbol de navegación."""

    def __init__(self, respuesta):
        super().__init__()
        self.enlaces = []
        self.controles = []
        self.formularios = []
        self.ids = []
        self.categorias = {}
        self.indices = []
        self._regiones = []
        self.feed(respuesta.content.decode("utf-8"))

    @property
    def region(self):
        return self._regiones[-1] if self._regiones else None

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if "id" in atributos:
            self.ids.append(atributos["id"])
        if tag in ("nav", "aside"):
            self._regiones.append(atributos.get("aria-label"))
        if tag == "a":
            self.enlaces.append((self.region, atributos))
        if tag in ("input", "button"):
            self.controles.append(atributos)
        if tag == "form":
            self.formularios.append(atributos)
        if tag == "details" and "data-categoria" in atributos:
            self.categorias[atributos["data-categoria"]] = "open" in atributos
        if "data-indice" in atributos:
            self.indices.append(atributos["data-indice"])

    def handle_endtag(self, tag):
        if tag in ("nav", "aside") and self._regiones:
            self._regiones.pop()

    def enlaces_en(self, region):
        return [attrs for nombre, attrs in self.enlaces if nombre == region]


def disponibles():
    return [h for h in catalogo.HERRAMIENTAS if h.disponible]


class PruebasCatalogo(SimpleTestCase):
    def test_ids_unicos_en_cada_nivel(self):
        for elementos in (catalogo.AREAS, catalogo.CATEGORIAS, catalogo.HERRAMIENTAS):
            ids = [elemento.id for elemento in elementos]
            self.assertEqual(len(ids), len(set(ids)))

    def test_jerarquia_y_estados_validos(self):
        for categoria in catalogo.CATEGORIAS:
            self.assertIn(categoria.area, catalogo.AREAS)
        for herramienta in catalogo.HERRAMIENTAS:
            with self.subTest(herramienta=herramienta.id):
                self.assertIn(herramienta.categoria, catalogo.CATEGORIAS)
                self.assertIn(herramienta.estado, ("disponible", "proximamente"))
                self.assertTrue(herramienta.descripcion)

    def test_disponibles_tienen_ruta_resoluble_y_proximas_no(self):
        for herramienta in catalogo.HERRAMIENTAS:
            with self.subTest(herramienta=herramienta.id):
                if herramienta.disponible:
                    ruta = herramienta.ruta
                    self.assertEqual(resolve(ruta).view_name, herramienta.route_name)
                    self.assertEqual(self.client.get(ruta).status_code, 200)
                    self.assertTrue(herramienta.palabras_clave)
                    self.assertTrue(herramienta.invitacion)
                else:
                    self.assertIsNone(herramienta.ruta)
                    self.assertIsNone(herramienta.route_name)

    def test_relaciones_referencian_ids_existentes(self):
        ids = {herramienta.id for herramienta in catalogo.HERRAMIENTAS}
        for herramienta in catalogo.HERRAMIENTAS:
            self.assertTrue(set(herramienta.relacionadas) <= ids)
            self.assertNotIn(herramienta.id, herramienta.relacionadas)

    def test_relaciones_filtran_herramientas_no_disponibles(self):
        herramienta = replace(catalogo.SISTEMAS, relacionadas=("conversion-bases", "operaciones-matrices"))
        self.assertEqual(catalogo.relacionadas_disponibles(herramienta), (catalogo.CONVERSION_BASES,))

    def test_sistemas_de_ecuaciones_tiene_una_sola_herramienta(self):
        """Gauss, Gauss-Jordan, clasificación y pivotes son opciones de Resolver un sistema, no herramientas."""
        self.assertEqual(catalogo.herramientas_de(catalogo.SISTEMAS_ECUACIONES), (catalogo.SISTEMAS,))
        self.assertEqual(catalogo.SISTEMAS.ruta, "/sistemas/")
        self.assertEqual(catalogo.SISTEMAS.relacionadas, ())
        self.assertEqual({h.id for h in catalogo.HERRAMIENTAS} & set(RUTAS_ANTIGUAS), set())
        for nombre in PSEUDO_HERRAMIENTAS:
            self.assertNotIn(nombre, [h.nombre for h in catalogo.HERRAMIENTAS])
        for palabra in ("gauss", "gauss-jordan", "clasificación", "columnas pivote", "inconsistente"):
            self.assertIn(palabra, catalogo.SISTEMAS.palabras_clave)

    def test_arbol_recorre_areas_categorias_y_herramientas_en_orden(self):
        arbol = catalogo.arbol()
        self.assertEqual(tuple(area for area, _ in arbol), catalogo.AREAS)
        categorias = tuple(categoria for _, grupos in arbol for categoria, _ in grupos)
        self.assertEqual(categorias, catalogo.CATEGORIAS)
        herramientas = tuple(h for _, grupos in arbol for _, hs in grupos for h in hs)
        self.assertEqual(herramientas, catalogo.HERRAMIENTAS)
        self.assertTrue(catalogo.SISTEMAS_ECUACIONES.disponible)
        self.assertFalse(catalogo.VECTORES.disponible)
        self.assertFalse(catalogo.CALCULO.disponible)

    def test_herramienta_por_ruta(self):
        self.assertEqual(catalogo.herramienta_por_ruta(resolve("/sistemas/")), catalogo.SISTEMAS)
        self.assertEqual(catalogo.herramienta_por_ruta(resolve("/bases/conversion/")), catalogo.CONVERSION_BASES)
        # Las rutas antiguas redirigen; no identifican una herramienta.
        self.assertIsNone(catalogo.herramienta_por_ruta(resolve("/sistemas/gauss/")))
        self.assertIsNone(catalogo.herramienta_por_ruta(resolve("/")))
        self.assertIsNone(catalogo.herramienta_por_ruta(resolve("/sistemas/inexistente/")))
        self.assertIsNone(catalogo.herramienta_por_ruta(None))

    def test_migas_derivan_de_area_categoria_y_herramienta(self):
        migas = catalogo.migas(catalogo.SISTEMAS)
        self.assertEqual(
            [(miga.nombre, miga.url, miga.actual) for miga in migas],
            [
                ("Inicio", "/", False),
                ("Álgebra Lineal", "/#algebra-lineal", False),
                ("Sistemas de ecuaciones", "/#sistemas-ecuaciones", False),
                ("Resolver un sistema", None, True),
            ],
        )
        self.assertEqual(catalogo.migas(None), ())


class PruebasBuscador(SimpleTestCase):
    def test_normalizar_ignora_acentos_mayusculas_y_espacios(self):
        self.assertEqual(catalogo.normalizar("  Clasificación   DE  Sistemas "), "clasificacion de sistemas")

    def test_busca_por_nombre_palabras_clave_categoria_y_area(self):
        # Lo que antes eran herramientas aparte sigue encontrándose: ahora lleva a Resolver un sistema.
        for consulta in ("Gauss", "pivote", "clasificacion", "inconsistente", "gauss jordan", "escalonada"):
            with self.subTest(consulta=consulta):
                self.assertEqual(catalogo.buscar_herramientas(consulta), (catalogo.SISTEMAS,))
        self.assertEqual(
            set(catalogo.buscar_herramientas("sistemas de ecuaciones")),
            set(catalogo.herramientas_de(catalogo.SISTEMAS_ECUACIONES)),
        )
        self.assertIn(catalogo.SISTEMAS, catalogo.buscar_herramientas("álgebra lineal"))

    def test_disponibles_primero_y_nombre_antes_que_descripcion(self):
        resultados = catalogo.buscar_herramientas("matriz")
        self.assertTrue(resultados)
        estados = [herramienta.disponible for herramienta in resultados]
        self.assertEqual(estados, sorted(estados, reverse=True))
        self.assertIn(catalogo.herramienta_por_id("operaciones-matrices"), resultados)
        self.assertEqual(catalogo.buscar_herramientas("resolver")[0], catalogo.SISTEMAS)
        self.assertEqual(catalogo.buscar_herramientas("conversion")[0], catalogo.CONVERSION_BASES)

    def test_todos_los_terminos_deben_coincidir(self):
        self.assertEqual(catalogo.buscar_herramientas("gauss binario"), ())
        self.assertEqual(catalogo.buscar_herramientas("zzz"), ())
        self.assertEqual(catalogo.buscar_herramientas("   "), ())
        self.assertEqual(catalogo.buscar_herramientas(""), ())

    def test_inicio_responde_a_la_consulta_sin_javascript(self):
        respuesta = self.client.get("/", {"q": "pivote"})
        self.assertContains(respuesta, "Resultados para «pivote»")
        self.assertContains(respuesta, f'href="{catalogo.SISTEMAS.ruta}"')
        self.assertContains(respuesta, "Resolver un sistema")
        self.assertNotContains(respuesta, "Columnas pivote")
        self.assertNotIn("algebra-lineal", Documento(respuesta).ids)
        self.assertContains(respuesta, 'value="pivote"')

        respuesta = self.client.get("/", {"q": "matriz"})
        self.assertContains(respuesta, "Operaciones con matrices")
        self.assertContains(respuesta, "Próximamente")
        destinos = {attrs["href"] for attrs in Documento(respuesta).enlaces_en(None)}
        self.assertNotIn("/matrices/", destinos)

        respuesta = self.client.get("/", {"q": "zzz"})
        self.assertContains(respuesta, "No se encontraron herramientas para «zzz»")

    def test_formulario_de_busqueda_e_indice_en_todas_las_paginas(self):
        for ruta in ("/", "/sistemas/", "/bases/conversion/"):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                documento = Documento(respuesta)
                formularios = [f for f in documento.formularios if f.get("role") == "search"]
                self.assertTrue(formularios)
                for formulario in formularios:
                    self.assertEqual(formulario["method"], "get")
                    self.assertEqual(formulario["action"], "/")
                    self.assertIn(formulario["data-buscador"], documento.ids)
                self.assertTrue(any(c.get("name") == "q" and c.get("type") == "search" for c in documento.controles))
                for herramienta in catalogo.HERRAMIENTAS:
                    self.assertIn(herramienta.indice, documento.indices)
                    self.assertEqual(herramienta.indice, catalogo.normalizar(herramienta.indice))


class PruebasNavegacion(SimpleTestCase):
    def test_inicio_es_general_sin_formulario_matematico(self):
        respuesta = self.client.get(reverse("calculadora:inicio"))
        self.assertContains(respuesta, "Inicio · Álgebra Lineal")
        self.assertContains(respuesta, "Explora los temas disponibles")
        self.assertContains(respuesta, "Aprende resolviendo")
        self.assertNotContains(respuesta, 'name="sistema"')
        self.assertNotContains(respuesta, "calculadora/matriz.js")
        self.assertNotContains(respuesta, 'aria-label="Ruta de navegación"')
        self.assertNotContains(respuesta, "math-keyboard")

    def test_inicio_descubre_todas_las_herramientas_del_catalogo(self):
        respuesta = self.client.get("/")
        documento = Documento(respuesta)
        for herramienta in catalogo.HERRAMIENTAS:
            with self.subTest(herramienta=herramienta.id):
                self.assertContains(respuesta, herramienta.nombre)
                self.assertContains(respuesta, herramienta.descripcion)
                if herramienta.disponible:
                    self.assertContains(respuesta, f'href="{herramienta.ruta}"')
        for elemento in (*catalogo.AREAS, *catalogo.CATEGORIAS):
            self.assertIn(elemento.id, documento.ids)
        self.assertContains(respuesta, 'aria-label="Acceso rápido"')

    def test_proximamente_sin_enlaces_falsos(self):
        respuesta = self.client.get("/")
        self.assertContains(respuesta, "Próximamente")
        destinos = {attrs["href"] for _, attrs in Documento(respuesta).enlaces}
        self.assertEqual(destinos, {"/", "#contenido", *(h.ruta for h in disponibles())})

    def test_sistemas_tiene_url_propia(self):
        self.assertEqual(reverse("calculadora:sistemas"), "/sistemas/")
        self.assertContains(self.client.get("/sistemas/"), 'id="sistema-form"')

    def test_inicio_no_resuelve_post(self):
        self.assertEqual(self.client.post("/", {"sistema": "x1=1"}).status_code, 405)

    def test_herramientas_no_registradas_devuelven_404(self):
        for ruta in ("/sistemas/inexistente/", "/sistemas/sistemas/", "/sistemas/vectores/"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 404)

    def test_sidebar_refleja_el_arbol_y_la_herramienta_activa(self):
        for herramienta in disponibles():
            with self.subTest(herramienta=herramienta.id):
                respuesta = self.client.get(herramienta.ruta)
                documento = Documento(respuesta)
                enlaces = documento.enlaces_en("Herramientas")
                activos = [a["href"] for a in enlaces if a.get("aria-current") == "page"]
                self.assertEqual(activos, [herramienta.ruta])
                self.assertEqual({a["href"] for a in enlaces}, {"/", *(h.ruta for h in disponibles())})
                self.assertEqual(set(documento.categorias), {c.id for c in catalogo.CATEGORIAS})
                abiertas = [id_ for id_, abierta in documento.categorias.items() if abierta]
                self.assertEqual(abiertas, [herramienta.categoria.id])
                for area in catalogo.AREAS:
                    self.assertContains(respuesta, area.nombre)

        inicio = Documento(self.client.get("/"))
        activos = [a["href"] for a in inicio.enlaces_en("Herramientas") if a.get("aria-current") == "page"]
        self.assertEqual(activos, ["/"])
        self.assertFalse(any(inicio.categorias.values()))

    def test_breadcrumbs_navegables_hasta_la_herramienta(self):
        respuesta = self.client.get("/sistemas/")
        documento = Documento(respuesta)
        enlaces = [a["href"] for a in documento.enlaces_en("Ruta de navegación")]
        self.assertEqual(enlaces, ["/", "/#algebra-lineal", "/#sistemas-ecuaciones"])
        self.assertContains(respuesta, '<span aria-current="page">Resolver un sistema</span>', html=True)
        ids_inicio = Documento(self.client.get("/")).ids
        self.assertIn("algebra-lineal", ids_inicio)
        self.assertIn("sistemas-ecuaciones", ids_inicio)

        respuesta = self.client.get("/bases/conversion/")
        enlaces = [a["href"] for a in Documento(respuesta).enlaces_en("Ruta de navegación")]
        self.assertEqual(enlaces, ["/", "/#sistemas-numericos", "/#bases-numericas"])
        self.assertContains(respuesta, '<span aria-current="page">Conversión de bases</span>', html=True)

    def test_enlaces_y_anclas_de_paginas_y_resultados_existen(self):
        paginas = [(h.ruta, self.client.get(h.ruta)) for h in disponibles()]
        paginas.append(("/", self.client.get("/")))
        paginas.append(("/sistemas/", self.client.post("/sistemas/", {"sistema": "x1=1", "metodo": "gauss"})))
        paginas.append(("/sistemas/ comparar", self.client.post(
            "/sistemas/", {"sistema": "x1+x2=3;x1-x2=1", "metodo": "comparar"},
        )))
        paginas.append(("/bases/conversion/", self.client.post(
            "/bases/conversion/", {"numero": "1010", "base_origen": "2", "base_destino": "16"},
        )))
        for ruta, respuesta in paginas:
            with self.subTest(ruta=ruta):
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
        self.assertContains(
            inicio,
            '<aside id="navegacion-principal" class="app-sidebar" aria-label="Navegación principal">',
        )
        pagina = self.client.get("/sistemas/")
        formulario = next(f for f in Documento(pagina).formularios if f.get("id") == "sistema-form")
        self.assertEqual(formulario["method"], "post")
        respuesta = self.client.post(formulario["action"].split("#")[0], {"metodo": "gauss", "sistema": "x1=7"})
        self.assertContains(respuesta, "x1 = 7")
        self.assertContains(respuesta, "Para editar la cuadrícula de una matriz, activa JavaScript.")
        # Lo que solo funciona con JavaScript nace oculto: no aparenta funcionar.
        self.assertContains(pagina, 'class="math-keyboard" data-teclado="sistema" data-teclado-para="system-fields"')
        self.assertContains(pagina, 'aria-label="Agregar una ecuación" hidden')

    def test_landmarks_skip_link_y_control_de_menu(self):
        for ruta in ("/", "/sistemas/"):
            respuesta = self.client.get(ruta)
            documento = Documento(respuesta)
            self.assertContains(respuesta, 'href="#contenido"')
            self.assertContains(respuesta, '<main id="contenido"')
            control = next(c for c in documento.controles if c.get("id") == "navigation-toggle")
            self.assertEqual(control["type"], "button")
            self.assertEqual(control["aria-expanded"], "false")
            self.assertIn(control["aria-controls"], documento.ids)
            self.assertIn("sidebar-backdrop", documento.ids)
