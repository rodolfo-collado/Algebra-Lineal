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
from django.template.loader import render_to_string
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
        self.herramientas = []
        self.grupos = {}
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
        if "data-herramienta" in atributos:
            self.herramientas.append((self.region, atributos))
        if tag == "details" and atributos.get("id"):
            self.grupos[atributos["id"]] = atributos

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
        herramienta = replace(catalogo.REDUCCION_FILAS, relacionadas=("conversion-bases", "limites-funciones"))
        self.assertEqual(catalogo.relacionadas_disponibles(herramienta), (catalogo.CONVERSION_BASES,))

    def test_reduccion_por_filas_es_una_herramienta_de_matrices(self):
        """Gauss, Gauss-Jordan, clasificación y pivotes son opciones de Reducción por filas, no herramientas."""
        self.assertNotIn("sistemas-ecuaciones", [c.id for c in catalogo.CATEGORIAS])
        self.assertNotIn("Sistemas de ecuaciones", [c.nombre for c in catalogo.CATEGORIAS])
        self.assertEqual(catalogo.REDUCCION_FILAS.categoria, catalogo.MATRICES)
        self.assertEqual(catalogo.herramientas_de(catalogo.MATRICES), (
            catalogo.OPERACIONES_MATRICES,
            catalogo.REDUCCION_FILAS, catalogo.ECUACIONES_MATRICIALES, catalogo.MATRIZ_INVERSA,
        ))
        self.assertEqual(catalogo.REDUCCION_FILAS.ruta, "/matrices/reduccion/")
        self.assertEqual(catalogo.REDUCCION_FILAS.relacionadas, ("ecuaciones-matriciales",))
        self.assertEqual({h.id for h in catalogo.HERRAMIENTAS} & set(RUTAS_ANTIGUAS), set())
        for nombre in PSEUDO_HERRAMIENTAS:
            self.assertNotIn(nombre, [h.nombre for h in catalogo.HERRAMIENTAS])
        for palabra in ("gauss", "gauss-jordan", "clasificación", "columnas pivote", "inconsistente"):
            self.assertIn(palabra, catalogo.REDUCCION_FILAS.palabras_clave)

    def test_arbol_recorre_areas_categorias_y_herramientas_en_orden(self):
        arbol = catalogo.arbol()
        self.assertEqual(tuple(area for area, _ in arbol), catalogo.AREAS)
        categorias = tuple(categoria for _, grupos in arbol for categoria, _ in grupos)
        self.assertEqual(categorias, catalogo.CATEGORIAS)
        herramientas = tuple(h for _, grupos in arbol for _, hs in grupos for h in hs)
        self.assertEqual(herramientas, catalogo.HERRAMIENTAS)
        self.assertTrue(catalogo.VECTORES.disponible)
        self.assertTrue(catalogo.MATRICES.disponible)
        self.assertFalse(catalogo.CALCULO.disponible)

    def test_herramienta_por_ruta(self):
        self.assertEqual(catalogo.herramienta_por_ruta(resolve("/matrices/reduccion/")), catalogo.REDUCCION_FILAS)
        self.assertEqual(catalogo.herramienta_por_ruta(resolve("/bases/conversion/")), catalogo.CONVERSION_BASES)
        # Las rutas antiguas redirigen; no identifican una herramienta.
        self.assertIsNone(catalogo.herramienta_por_ruta(resolve("/sistemas/gauss/")))
        self.assertIsNone(catalogo.herramienta_por_ruta(resolve("/")))
        self.assertIsNone(catalogo.herramienta_por_ruta(resolve("/sistemas/inexistente/")))
        self.assertIsNone(catalogo.herramienta_por_ruta(None))

    def test_migas_derivan_de_area_categoria_y_herramienta(self):
        migas = catalogo.migas(catalogo.REDUCCION_FILAS)
        self.assertEqual(
            [(miga.nombre, miga.url, miga.actual) for miga in migas],
            [
                ("Inicio", "/", False),
                ("Álgebra Lineal", "/#algebra-lineal", False),
                ("Matrices", "/#matrices", False),
                ("Reducción por filas", None, True),
            ],
        )
        self.assertEqual(catalogo.migas(None), ())


class PruebasBuscador(SimpleTestCase):
    def test_normalizar_ignora_acentos_mayusculas_y_espacios(self):
        self.assertEqual(catalogo.normalizar("  Clasificación   DE  Sistemas "), "clasificacion de sistemas")

    def test_busca_por_nombre_palabras_clave_categoria_y_area(self):
        # Lo que antes eran herramientas aparte sigue encontrándose: ahora lleva a Reducción por filas.
        for consulta in ("Gauss", "pivote", "clasificacion", "gauss jordan", "escalonada"):
            with self.subTest(consulta=consulta):
                self.assertEqual(catalogo.buscar_herramientas(consulta), (catalogo.REDUCCION_FILAS,))
        # «inconsistente» también describe Ax = b (P14); Reducción por filas conserva el primer lugar.
        self.assertEqual(
            catalogo.buscar_herramientas("inconsistente"), (catalogo.REDUCCION_FILAS, catalogo.ECUACIONES_MATRICIALES),
        )
        self.assertEqual(
            catalogo.buscar_herramientas("sistemas de ecuaciones"),
            (catalogo.REDUCCION_FILAS, catalogo.ECUACIONES_MATRICIALES),
        )
        self.assertIn(catalogo.REDUCCION_FILAS, catalogo.buscar_herramientas("álgebra lineal"))

    def test_disponibles_primero_y_nombre_antes_que_descripcion(self):
        resultados = catalogo.buscar_herramientas("matriz")
        self.assertTrue(resultados)
        estados = [herramienta.disponible for herramienta in resultados]
        self.assertEqual(estados, sorted(estados, reverse=True))
        self.assertIn(catalogo.herramienta_por_id("operaciones-matrices"), resultados)
        self.assertEqual(catalogo.buscar_herramientas("resolver")[0], catalogo.ECUACIONES_MATRICIALES)
        self.assertEqual(catalogo.buscar_herramientas("conversion")[0], catalogo.CONVERSION_BASES)

    def test_todos_los_terminos_deben_coincidir(self):
        self.assertEqual(catalogo.buscar_herramientas("gauss binario"), ())
        self.assertEqual(catalogo.buscar_herramientas("zzz"), ())
        self.assertEqual(catalogo.buscar_herramientas("   "), ())
        self.assertEqual(catalogo.buscar_herramientas(""), ())

    def test_inicio_responde_a_la_consulta_sin_javascript(self):
        respuesta = self.client.get("/", {"q": "pivote"})
        self.assertContains(respuesta, "Resultados para «pivote»")
        self.assertContains(respuesta, f'href="{catalogo.REDUCCION_FILAS.ruta}"')
        self.assertContains(respuesta, "Reducción por filas")
        self.assertNotContains(respuesta, "Columnas pivote")
        self.assertNotIn("algebra-lineal", Documento(respuesta).ids)
        self.assertContains(respuesta, 'value="pivote"')

        respuesta = self.client.get("/", {"q": "matriz"})
        self.assertContains(respuesta, "Operaciones con matrices")
        # UI-15: las próximas también permanecen en el universo, ocultas si no coinciden.
        items = [a for region, a in Documento(respuesta).herramientas if region is None]
        self.assertEqual(len(items), len(catalogo.HERRAMIENTAS))
        self.assertIn("hidden", next(a for a in items if a["data-herramienta"] == "limites-funciones"))
        destinos = {attrs["href"] for attrs in Documento(respuesta).enlaces_en(None)}
        self.assertNotIn("/matrices/", destinos)
        self.assertIn("/matrices/operaciones/", destinos)

        respuesta = self.client.get("/", {"q": "zzz"})
        self.assertContains(respuesta, "No se encontraron herramientas para «zzz»")

    def test_terminos_vacios_no_devuelven_coincidencias(self):
        self.assertEqual(catalogo.terminos_de("  MÉTODO\tde\nGauss  "), ("gauss",))
        self.assertEqual(catalogo.terminos_de("CALCULAR\u0085la\u00a0INVERSA"), ("inversa",))
        for consulta in (*catalogo.PALABRAS_VACIAS, "calcular la", "Método de", "pasar a un"):
            with self.subTest(consulta=consulta):
                self.assertEqual(catalogo.buscar_herramientas(consulta), ())

    def test_consultas_naturales(self):
        consultas = {
            "calcular inversa": "matriz-inversa", "invertir matriz": "matriz-inversa",
            "multiplicar matrices": "operaciones-matrices", "sumar vectores": "operaciones-vectores",
            "convertir a binario": "conversion-bases", "método de gauss": "reduccion-filas",
            "transponer": "operaciones-matrices", "pasar decimal a binario": "conversion-bases",
            "restar vectores": "operaciones-vectores", "reducir matriz": "reduccion-filas",
        }
        for consulta, esperado in consultas.items():
            for variante in (consulta, consulta.upper(), f"  {consulta.replace(' ', '   ')}  "):
                with self.subTest(consulta=variante):
                    self.assertEqual(catalogo.buscar_herramientas(variante)[0].id, esperado)

    def test_sistemas_y_proximas(self):
        for consulta in ("sistema de ecuaciones", "sistema lineal", "sistemas lineales", "ecuaciones lineales"):
            self.assertEqual(catalogo.buscar_herramientas(consulta),
                             (catalogo.REDUCCION_FILAS, catalogo.ECUACIONES_MATRICIALES))
        limites, = catalogo.buscar_herramientas("LÍMITES")
        self.assertEqual(limites.id, "limites-funciones")
        self.assertEqual(limites.estado, "proximamente")

    def test_get_conserva_universo_completo_y_oculta_no_coincidentes(self):
        for consulta in ("gauss", "inversa", "límites", "zzz", "calcular la"):
            respuesta = self.client.get("/", {"q": consulta})
            items = [a for region, a in Documento(respuesta).herramientas if region is None]
            self.assertEqual({a["data-herramienta"] for a in items}, {h.id for h in catalogo.HERRAMIENTAS})
            visibles = [a["data-herramienta"] for a in items if "hidden" not in a]
            self.assertEqual(visibles, [h.id for h in catalogo.buscar_herramientas(consulta)])
            self.assertContains(respuesta, 'tabindex="-1" data-busqueda-get')
            self.assertContains(respuesta, 'id="buscador-inicio-estado" class="search-status" aria-live="polite"></p>')
            for termino in ("gauss", "matriz", "vectores"):
                self.assertContains(respuesta, f'href="{reverse("calculadora:inicio")}?q={termino}"')
        self.assertNotContains(self.client.get("/"), "data-busqueda-get")

    def test_datos_cliente_se_derivan_del_catalogo(self):
        respuesta = self.client.get("/")
        html = respuesta.content.decode()
        datos = json.loads(html.split('<script id="datos-buscador" type="application/json">')[1].split('</script>')[0])
        self.assertEqual(datos["palabras_vacias"], list(catalogo.PALABRAS_VACIAS))
        self.assertEqual(datos["separador"], catalogo.SEPARADOR_TERMINOS)
        self.assertEqual([h["id"] for h in datos["herramientas"]], [h.id for h in catalogo.HERRAMIENTAS])
        for h, publicado in zip(catalogo.HERRAMIENTAS, datos["herramientas"]):
            self.assertEqual(publicado["indice"], h.indice)
            self.assertEqual(publicado["nombre"], catalogo.normalizar(h.nombre))
            self.assertEqual(publicado["disponible"], h.disponible)

    def test_invitaciones_y_relaciones_se_renderizan(self):
        self.assertIn("ecuaciones-matriciales", catalogo.REDUCCION_FILAS.relacionadas)
        self.assertIn("reduccion-filas", catalogo.ECUACIONES_MATRICIALES.relacionadas)
        self.assertIn("matriz-inversa", catalogo.OPERACIONES_MATRICES.relacionadas)
        self.assertNotIn("matriz-inversa", catalogo.ECUACIONES_MATRICIALES.relacionadas)
        for herramienta in catalogo.herramientas_disponibles():
            relacionadas = catalogo.relacionadas_disponibles(herramienta)
            html = render_to_string("calculadora/components/related_tools.html",
                                    {"herramientas_relacionadas": relacionadas, "resultado": True})
            for relacionada in relacionadas:
                self.assertIn(escape(relacionada.nombre), html)
                self.assertIn(escape(relacionada.invitacion), html)
        # Comprueba además páginas reales: la orientación sale en el bloque de relacionadas.
        from tests.test_ecuaciones_matriciales_web import datos_ecuacion
        from tests.test_matrices_web import datos_simbolos
        ecuacion = self.client.post(catalogo.ECUACIONES_MATRICIALES.ruta, datos_ecuacion())
        self.assertContains(ecuacion, catalogo.REDUCCION_FILAS.invitacion)
        operaciones = self.client.post(catalogo.OPERACIONES_MATRICES.ruta, datos_simbolos(
            "A", [{"nombre": "A", "tipo": "matriz", "valor": [[1]]}],
        ))
        self.assertContains(operaciones, catalogo.MATRIZ_INVERSA.invitacion)
        self.assertContains(operaciones, catalogo.ECUACIONES_MATRICIALES.invitacion)

    def test_formulario_de_busqueda_e_indice_en_todas_las_paginas(self):
        for ruta in ("/", "/matrices/reduccion/", "/bases/conversion/"):
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
        self.assertContains(respuesta, "Inicio · PyGebra")
        self.assertContains(respuesta, "¿Qué quieres resolver?")
        self.assertContains(respuesta, "Aprende resolviendo")
        self.assertNotContains(respuesta, 'name="sistema"')
        self.assertNotContains(respuesta, "calculadora/matriz.js")
        self.assertNotContains(respuesta, 'aria-label="Ruta de navegación"')
        self.assertNotContains(respuesta, "math-keyboard")

    def test_inicio_descubre_todas_las_herramientas_del_catalogo(self):
        respuesta = self.client.get("/")
        documento = Documento(respuesta)
        for herramienta in catalogo.herramientas_disponibles():
            with self.subTest(herramienta=herramienta.id):
                self.assertContains(respuesta, herramienta.nombre)
                self.assertContains(respuesta, herramienta.descripcion)
                if herramienta.disponible:
                    self.assertContains(respuesta, f'href="{herramienta.ruta}"')
        for elemento in (*catalogo.AREAS, *catalogo.CATEGORIAS):
            if elemento.disponible:
                self.assertIn(elemento.id, documento.ids)
            else:
                # UI-15: el universo próximo existe, pero no aparece al explorar sin búsqueda.
                self.assertIn(elemento.id, documento.ids)
        self.assertIn("hidden", documento.grupos["calculo"])
        # Sin caminos duplicados: las herramientas se descubren dentro de su tema.
        self.assertNotContains(respuesta, "Acceso rápido")

    def test_proximamente_sin_enlaces_falsos(self):
        respuesta = self.client.get("/")
        self.assertContains(respuesta, "Próximamente")
        destinos = {attrs["href"] for _, attrs in Documento(respuesta).enlaces}
        self.assertEqual(destinos, {"/", "#contenido", *(h.ruta for h in disponibles()),
                                    "/?q=gauss", "/?q=matriz", "/?q=vectores"})

    def test_sistemas_tiene_url_propia(self):
        self.assertEqual(reverse("calculadora:reduccion-filas"), "/matrices/reduccion/")
        self.assertContains(self.client.get("/matrices/reduccion/"), 'id="sistema-form"')

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
        respuesta = self.client.get("/matrices/reduccion/")
        documento = Documento(respuesta)
        enlaces = [a["href"] for a in documento.enlaces_en("Ruta de navegación")]
        self.assertEqual(enlaces, ["/", "/#algebra-lineal", "/#matrices"])
        self.assertContains(respuesta, '<span aria-current="page">Reducción por filas</span>', html=True)
        ids_inicio = Documento(self.client.get("/")).ids
        self.assertIn("algebra-lineal", ids_inicio)
        self.assertIn("matrices", ids_inicio)
        self.assertNotIn("sistemas-ecuaciones", ids_inicio)

        respuesta = self.client.get("/bases/conversion/")
        enlaces = [a["href"] for a in Documento(respuesta).enlaces_en("Ruta de navegación")]
        self.assertEqual(enlaces, ["/", "/#sistemas-numericos", "/#bases-numericas"])
        self.assertContains(respuesta, '<span aria-current="page">Conversión de bases</span>', html=True)

    def test_enlaces_y_anclas_de_paginas_y_resultados_existen(self):
        paginas = [(h.ruta, self.client.get(h.ruta)) for h in disponibles()]
        paginas.append(("/", self.client.get("/")))
        paginas.append(("/matrices/reduccion/", self.client.post("/matrices/reduccion/", {"sistema": "x1=1", "metodo": "gauss"})))
        paginas.append(("/sistemas/ comparar", self.client.post(
            "/matrices/reduccion/", {"sistema": "x1+x2=3;x1-x2=1", "metodo": "comparar"},
        )))
        paginas.append(("/bases/conversion/", self.client.post(
            "/bases/conversion/", {"numero": "1010", "base_origen": "2", "bases_destino": ["10", "16"]},
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
        pagina = self.client.get("/matrices/reduccion/")
        formulario = next(f for f in Documento(pagina).formularios if f.get("id") == "sistema-form")
        self.assertEqual(formulario["method"], "post")
        respuesta = self.client.post(formulario["action"].split("#")[0], {"metodo": "gauss", "sistema": "x1=7"})
        self.assertContains(respuesta, "x1 = 7")
        self.assertContains(respuesta, "Para editar la cuadrícula de una matriz, activa JavaScript.")
        # Lo que solo funciona con JavaScript nace oculto: no aparenta funcionar.
        self.assertContains(pagina, 'class="math-keyboard" data-perfiles="math-keyboard-profiles"', count=1)
        self.assertContains(pagina, 'id="system-fields" data-perfil="sistema"')
        self.assertContains(pagina, 'aria-label="Agregar una ecuación" hidden')

    def test_landmarks_skip_link_y_control_de_menu(self):
        for ruta in ("/", "/matrices/reduccion/"):
            respuesta = self.client.get(ruta)
            documento = Documento(respuesta)
            self.assertContains(respuesta, 'href="#contenido"')
            self.assertContains(respuesta, '<main id="contenido"')
            control = next(c for c in documento.controles if c.get("id") == "navigation-toggle")
            self.assertEqual(control["type"], "button")
            self.assertEqual(control["aria-expanded"], "false")
            self.assertIn(control["aria-controls"], documento.ids)
            self.assertIn("sidebar-backdrop", documento.ids)
