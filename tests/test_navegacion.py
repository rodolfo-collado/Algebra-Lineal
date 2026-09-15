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
from frontend.web.calculadora.forms import SistemaForm
from frontend.web.calculadora.herramientas_sistemas import HERRAMIENTAS as HERRAMIENTAS_SISTEMAS
from frontend.web.calculadora.servicios import resolver_entrada_web
from tests.test_web import datos_matriz


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
        herramienta = replace(catalogo.GAUSS, relacionadas=("gauss-jordan", "operaciones-matrices"))
        self.assertEqual(catalogo.relacionadas_disponibles(herramienta), (catalogo.GAUSS_JORDAN,))

    def test_herramientas_de_sistemas_coinciden_con_el_modulo(self):
        ids_catalogo = {h.id for h in catalogo.herramientas_de(catalogo.SISTEMAS_ECUACIONES)}
        self.assertEqual(ids_catalogo, set(HERRAMIENTAS_SISTEMAS))
        self.assertEqual(catalogo.SISTEMAS.ruta, "/sistemas/")
        self.assertEqual(catalogo.GAUSS.ruta, "/sistemas/gauss/")

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
        self.assertEqual(catalogo.herramienta_por_ruta(resolve("/sistemas/gauss/")), catalogo.GAUSS)
        self.assertEqual(catalogo.herramienta_por_ruta(resolve("/sistemas/")), catalogo.SISTEMAS)
        self.assertIsNone(catalogo.herramienta_por_ruta(resolve("/")))
        self.assertIsNone(catalogo.herramienta_por_ruta(resolve("/sistemas/inexistente/")))
        self.assertIsNone(catalogo.herramienta_por_ruta(None))

    def test_migas_derivan_de_area_categoria_y_herramienta(self):
        migas = catalogo.migas(catalogo.GAUSS)
        self.assertEqual(
            [(miga.nombre, miga.url, miga.actual) for miga in migas],
            [
                ("Inicio", "/", False),
                ("Álgebra Lineal", "/#algebra-lineal", False),
                ("Sistemas de ecuaciones", "/#sistemas-ecuaciones", False),
                ("Método de Gauss", None, True),
            ],
        )
        self.assertEqual(catalogo.migas(None), ())


class PruebasBuscador(SimpleTestCase):
    def test_normalizar_ignora_acentos_mayusculas_y_espacios(self):
        self.assertEqual(catalogo.normalizar("  Clasificación   DE  Sistemas "), "clasificacion de sistemas")

    def test_busca_por_nombre_palabras_clave_categoria_y_area(self):
        self.assertIn(catalogo.GAUSS, catalogo.buscar_herramientas("Gauss"))
        self.assertIn(catalogo.COLUMNAS_PIVOTE, catalogo.buscar_herramientas("pivote"))
        self.assertIn(catalogo.CLASIFICACION, catalogo.buscar_herramientas("clasificacion"))
        self.assertIn(catalogo.CLASIFICACION, catalogo.buscar_herramientas("inconsistente"))
        self.assertEqual(
            set(catalogo.buscar_herramientas("sistemas de ecuaciones")),
            set(catalogo.herramientas_de(catalogo.SISTEMAS_ECUACIONES)),
        )
        self.assertIn(catalogo.GAUSS, catalogo.buscar_herramientas("álgebra lineal"))

    def test_disponibles_primero_y_nombre_antes_que_descripcion(self):
        resultados = catalogo.buscar_herramientas("matriz")
        self.assertTrue(resultados)
        estados = [herramienta.disponible for herramienta in resultados]
        self.assertEqual(estados, sorted(estados, reverse=True))
        self.assertIn(catalogo.herramienta_por_id("operaciones-matrices"), resultados)
        self.assertEqual(catalogo.buscar_herramientas("pivote")[0], catalogo.COLUMNAS_PIVOTE)
        self.assertEqual(catalogo.buscar_herramientas("gauss jordan")[0], catalogo.GAUSS_JORDAN)

    def test_todos_los_terminos_deben_coincidir(self):
        self.assertEqual(catalogo.buscar_herramientas("gauss binario"), ())
        self.assertEqual(catalogo.buscar_herramientas("zzz"), ())
        self.assertEqual(catalogo.buscar_herramientas("   "), ())
        self.assertEqual(catalogo.buscar_herramientas(""), ())

    def test_inicio_responde_a_la_consulta_sin_javascript(self):
        respuesta = self.client.get("/", {"q": "pivote"})
        self.assertContains(respuesta, "Resultados para «pivote»")
        self.assertContains(respuesta, f'href="{catalogo.COLUMNAS_PIVOTE.ruta}"')
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
        for ruta in ("/", "/sistemas/", "/sistemas/gauss/"):
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
        respuesta = self.client.get("/sistemas/gauss/")
        documento = Documento(respuesta)
        enlaces = [a["href"] for a in documento.enlaces_en("Ruta de navegación")]
        self.assertEqual(enlaces, ["/", "/#algebra-lineal", "/#sistemas-ecuaciones"])
        self.assertContains(respuesta, '<span aria-current="page">Método de Gauss</span>', html=True)
        ids_inicio = Documento(self.client.get("/")).ids
        self.assertIn("algebra-lineal", ids_inicio)
        self.assertIn("sistemas-ecuaciones", ids_inicio)

        respuesta = self.client.get("/sistemas/")
        self.assertContains(respuesta, '<span aria-current="page">Resolver un sistema</span>', html=True)

    def test_enlaces_y_anclas_de_paginas_y_resultados_existen(self):
        paginas = [(h.ruta, self.client.get(h.ruta)) for h in disponibles()]
        paginas.append(("/", self.client.get("/")))
        paginas.append(("/sistemas/", self.client.post("/sistemas/", {"sistema": "x1=1", "metodo": "gauss"})))
        paginas.append(("/sistemas/clasificacion/", self.client.post(
            "/sistemas/clasificacion/", {"sistema": "x1=1", "metodo": "gauss"},
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


class PruebasHerramientasSistemas(SimpleTestCase):
    TEXTO = "  x1 + x2 = 3;\nx1 - x2 = 1  "

    def test_cada_herramienta_declara_su_accion_principal(self):
        for herramienta in catalogo.herramientas_de(catalogo.SISTEMAS_ECUACIONES):
            configuracion = HERRAMIENTAS_SISTEMAS[herramienta.id]
            with self.subTest(herramienta=herramienta.id):
                respuesta = self.client.get(herramienta.ruta)
                self.assertContains(respuesta, f">{configuracion.accion}</button>")
                self.assertContains(respuesta, f"{herramienta.nombre} · Álgebra Lineal")
                self.assertContains(respuesta, 'id="sistema-form"')

    def test_gauss_y_gauss_jordan_fijan_el_metodo(self):
        for ruta, fijo, etiqueta, ajena in (
            ("/sistemas/gauss/", "gauss", "Matriz escalonada", "Matriz reducida"),
            ("/sistemas/gauss-jordan/", "gauss_jordan", "Matriz reducida", "Sustitución regresiva"),
        ):
            with self.subTest(ruta=ruta):
                pagina = self.client.get(ruta)
                controles = Documento(pagina).controles
                metodos = [c for c in controles if c.get("name") == "metodo"]
                self.assertEqual([(c["type"], c["value"]) for c in metodos], [("hidden", fijo)])
                otro = "gauss_jordan" if fijo == "gauss" else "gauss"
                with patch("frontend.web.calculadora.views.resolver_entrada_web", wraps=resolver_entrada_web) as resolver:
                    respuesta = self.client.post(ruta, {"sistema": self.TEXTO, "metodo": otro})
                self.assertEqual(resolver.call_args.args[1], fijo)
                self.assertContains(respuesta, etiqueta)
                self.assertNotContains(respuesta, ajena)
                self.assertContains(respuesta, "x1 = 2")
                self.assertContains(respuesta, "x2 = 1")

    def test_clasificacion_y_pivotes_dejan_elegir_el_metodo(self):
        for ruta in ("/sistemas/clasificacion/", "/sistemas/columnas-pivote/", "/sistemas/"):
            with self.subTest(ruta=ruta):
                controles = Documento(self.client.get(ruta)).controles
                metodos = [c for c in controles if c.get("name") == "metodo"]
                self.assertEqual({c["type"] for c in metodos}, {"radio"})
                with patch("frontend.web.calculadora.views.resolver_entrada_web", wraps=resolver_entrada_web) as resolver:
                    respuesta = self.client.post(ruta, {"sistema": self.TEXTO, "metodo": "gauss"})
                self.assertEqual(resolver.call_args.args[1], "gauss")
                self.assertContains(respuesta, "Matriz escalonada")
                self.assertNotContains(respuesta, "Matriz reducida")

    def test_clasificacion_destaca_el_tipo_de_solucion(self):
        respuesta = self.client.post("/sistemas/clasificacion/", {"sistema": "x1+x2=2;2x1+2x2=5", "metodo": "gauss"})
        texto = strip_tags(respuesta.content.decode("utf-8"))
        self.assertIn("Clasificación del sistema", texto)
        inicio_resultado = texto.index("Resultado final")
        self.assertLess(texto.index("Inconsistente", inicio_resultado), texto.index("Matriz escalonada", inicio_resultado))
        self.assertLess(texto.index("Resultado final"), texto.index("Procedimiento paso a paso"))
        self.assertEqual(texto.count("Clasificación\n", inicio_resultado), 1)

    def test_columnas_pivote_destaca_y_resalta_los_pivotes(self):
        respuesta = self.client.post("/sistemas/columnas-pivote/", datos_matriz([[1, 2, 1, 4], [0, 0, 1, 2]], "gauss_jordan"))
        html = respuesta.content.decode("utf-8")
        texto = strip_tags(html)
        self.assertIn("Columnas pivote: C1, C3", texto)
        self.assertLess(texto.index("Resultado final"), texto.index("Procedimiento paso a paso"))
        self.assertEqual(html.count('class="constant pivot"') + html.count('class=" pivot"'), 4)
        self.assertContains(respuesta, "Las columnas resaltadas en la matriz contienen un pivote.")

        sin_pivotes = self.client.post("/sistemas/columnas-pivote/", datos_matriz([[0, 0, 0]], "gauss"))
        self.assertNotContains(sin_pivotes, ' pivot"')
        self.assertNotContains(sin_pivotes, "Las columnas resaltadas")

    def test_relacionadas_antes_y_despues_de_resolver(self):
        pagina = self.client.get("/sistemas/gauss/")
        self.assertContains(pagina, "Herramientas relacionadas")
        self.assertNotContains(pagina, "Continúa con este mismo sistema")
        self.assertNotContains(pagina, "formaction=")
        for relacionada in catalogo.relacionadas_disponibles(catalogo.GAUSS):
            self.assertContains(pagina, f'href="{relacionada.ruta}"')

        respuesta = self.client.post("/sistemas/gauss/", {"sistema": self.TEXTO, "metodo": "gauss"})
        self.assertContains(respuesta, "Continúa con este mismo sistema")
        self.assertContains(respuesta, 'id="resultado"')
        botones = [c for c in Documento(respuesta).controles if "formaction" in c]
        self.assertEqual(
            [b["formaction"] for b in botones],
            [f"{r.ruta}#resultado" for r in catalogo.relacionadas_disponibles(catalogo.GAUSS)],
        )
        for boton in botones:
            self.assertEqual(boton["type"], "submit")
            self.assertEqual(boton["form"], "sistema-form")
        self.assertContains(respuesta, "Ver el procedimiento con Gauss-Jordan")

    def compartir(self, origen, datos, destino):
        inicial = self.client.post(origen, datos)
        documento = Documento(inicial)
        boton = next(c for c in documento.controles if c.get("formaction", "").startswith(destino))
        self.assertEqual(boton["form"], "sistema-form")
        with patch("frontend.web.calculadora.views.resolver_entrada_web", wraps=resolver_entrada_web) as resolver:
            respuesta = self.client.post(destino, datos)
        resolver.assert_called_once()
        self.assertEqual(respuesta.status_code, 200)
        return respuesta, resolver.call_args.args[1]

    def test_gauss_a_gauss_jordan_conserva_texto(self):
        respuesta, metodo = self.compartir(
            "/sistemas/gauss/", {"sistema": self.TEXTO, "metodo": "gauss"}, "/sistemas/gauss-jordan/",
        )
        self.assertEqual(metodo, "gauss_jordan")
        self.assertContains(respuesta, escape(self.TEXTO))
        self.assertContains(respuesta, "Matriz reducida")
        self.assertContains(respuesta, "x1 = 2")
        self.assertContains(respuesta, "x2 = 1")

    def test_gauss_jordan_a_gauss_conserva_texto(self):
        respuesta, metodo = self.compartir(
            "/sistemas/gauss-jordan/", {"sistema": self.TEXTO, "metodo": "gauss_jordan"}, "/sistemas/gauss/",
        )
        self.assertEqual(metodo, "gauss")
        self.assertContains(respuesta, escape(self.TEXTO))
        self.assertContains(respuesta, "Sustitución regresiva")
        self.assertContains(respuesta, "x1 = 2")

    def test_clasificacion_conserva_el_metodo_al_resolver_el_sistema_completo(self):
        respuesta, metodo = self.compartir(
            "/sistemas/clasificacion/", {"sistema": self.TEXTO, "metodo": "gauss"}, "/sistemas/",
        )
        self.assertEqual(metodo, "gauss")
        self.assertContains(respuesta, "Sustitución regresiva")
        self.assertContains(respuesta, "x1 = 2")
        seleccionados = [c["value"] for c in Documento(respuesta).controles
                         if c.get("name") == "metodo" and "checked" in c]
        self.assertEqual(seleccionados, ["gauss"])
        self.assertContains(respuesta, dict(SistemaForm.METODOS)["gauss"])

    def test_compartir_matriz_rectangular_conserva_dimensiones_valores_y_fracciones(self):
        matriz = [["1/2", "1/2", "3/2"], ["1", "-1", "1"], ["2", "0", "4"]]
        for origen, destino in (
            ("/sistemas/gauss/", "/sistemas/gauss-jordan/"),
            ("/sistemas/columnas-pivote/", "/sistemas/"),
        ):
            with self.subTest(origen=origen):
                respuesta, _ = self.compartir(origen, datos_matriz(matriz, "gauss"), destino)
                self.assertContains(respuesta, json.dumps(matriz))
                controles = Documento(respuesta).controles
                for nombre, valor in (("ecuaciones", "3"), ("variables", "2")):
                    self.assertEqual(next(c["value"] for c in controles if c.get("name") == nombre), valor)
                self.assertContains(respuesta, "x1 = 2")
                self.assertContains(respuesta, "x2 = 1")

    def test_pivotes_y_guia_en_el_mismo_bloque(self):
        respuesta = self.client.post("/sistemas/", {"sistema": "x1+x3=4;x3=2", "metodo": "gauss"})
        self.assertContains(respuesta, 'id="columnas-pivote"', count=1)
        self.assertContains(respuesta, "C1")
        self.assertContains(respuesta, "C3")
        self.assertContains(respuesta, 'class="pivot-chip"')
        self.assertContains(respuesta, "Guía de concepto")
        self.assertContains(respuesta, "Gauss se detiene en forma escalonada")

    def test_entrada_invalida_al_compartir_muestra_el_error_sin_resultado(self):
        respuesta = self.client.post("/sistemas/gauss-jordan/", {"sistema": "x1+=1", "metodo": "gauss"})
        self.assertContains(respuesta, "Formato de sistema inválido")
        self.assertNotContains(respuesta, "Traceback")
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertNotContains(respuesta, "Continúa con este mismo sistema")
        self.assertContains(respuesta, "Herramientas relacionadas")

    def test_no_hay_recomendaciones_con_entrada_antes_de_resolver(self):
        self.assertNotContains(self.client.get("/sistemas/gauss/"), "Continúa con este mismo sistema")

    def test_el_espacio_general_no_recomienda_lo_que_ya_muestra(self):
        """Resolver un sistema ya calcula método, clasificación y pivotes: no hay relacionadas."""
        self.assertEqual(catalogo.SISTEMAS.relacionadas, ())
        for respuesta in (
            self.client.get("/sistemas/"),
            self.client.post("/sistemas/", {"sistema": self.TEXTO, "metodo": "gauss"}),
            self.client.post("/sistemas/", {"sistema": self.TEXTO, "metodo": "gauss_jordan"}),
            self.client.post("/sistemas/", {"sistema": "x1+=1", "metodo": "gauss"}),
        ):
            self.assertNotContains(respuesta, "Herramientas relacionadas")
            self.assertNotContains(respuesta, "Continúa con este mismo sistema")
            self.assertNotContains(respuesta, 'class="related"')
            self.assertNotContains(respuesta, "formaction=")

    def test_cada_relacionada_aporta_algo_que_la_vista_actual_no_da(self):
        """Una recomendación cambia el procedimiento o añade bloques; no se rellena por afinidad."""
        for herramienta in catalogo.herramientas_de(catalogo.SISTEMAS_ECUACIONES):
            actual = HERRAMIENTAS_SISTEMAS[herramienta.id]
            for relacionada in catalogo.relacionadas_disponibles(herramienta):
                destino = HERRAMIENTAS_SISTEMAS[relacionada.id]
                with self.subTest(origen=herramienta.id, destino=relacionada.id):
                    cambia_procedimiento = destino.metodo_fijo != actual.metodo_fijo
                    aporta_bloques = bool(destino.bloques - actual.bloques)
                    self.assertTrue(cambia_procedimiento or aporta_bloques)
        self.assertEqual(catalogo.CLASIFICACION.relacionadas, ("sistemas",))
        self.assertEqual(catalogo.COLUMNAS_PIVOTE.relacionadas, ("sistemas",))

    def test_vistas_especializadas_muestran_solo_su_bloque(self):
        clasificacion = self.client.post(
            "/sistemas/clasificacion/", {"sistema": "x1+x2=2;2x1+2x2=4", "metodo": "gauss_jordan"},
        )
        self.assertContains(clasificacion, "Consistente de soluciones infinitas")
        self.assertContains(clasificacion, "no tiene pivote, por lo que es libre")
        self.assertContains(clasificacion, "Sistema resultante")
        self.assertNotContains(clasificacion, "solution-list")
        self.assertNotContains(clasificacion, "Sustitución regresiva")
        self.assertContains(clasificacion, "Resolver el sistema completo")

        pivotes = self.client.post("/sistemas/columnas-pivote/", {"sistema": self.TEXTO, "metodo": "gauss"})
        self.assertContains(pivotes, "Columnas pivote: C1, C2")
        self.assertContains(pivotes, "Procedimiento paso a paso")
        for ausente in ('class="classification"', "Sistema resultante", "Sustitución regresiva", "solution-list"):
            self.assertNotContains(pivotes, ausente)
        self.assertContains(pivotes, "Resolver el sistema completo")

        completo = self.client.post("/sistemas/", {"sistema": self.TEXTO, "metodo": "gauss"})
        for presente in ('class="classification"', "Sustitución regresiva", "solution-list", "x1 = 2"):
            self.assertContains(completo, presente)

    def test_guias_plegadas_bajo_entender_este_resultado(self):
        pagina = self.client.get("/sistemas/gauss/")
        self.assertNotContains(pagina, "Entender este resultado")
        self.assertNotContains(pagina, "concept-guide")

        respuesta = self.client.post("/sistemas/gauss/", {"sistema": self.TEXTO, "metodo": "gauss"})
        html = respuesta.content.decode("utf-8")
        self.assertIn('<details class="insight" id="entender-resultado">', html)
        self.assertContains(respuesta, "Entender este resultado")
        self.assertContains(respuesta, "Gauss se detiene en forma escalonada")
        self.assertContains(respuesta, "Hay tantas columnas pivote como variables")
        # Todas las guías viven dentro del bloque plegado, después del resultado matemático.
        inicio_insight = html.index('id="entender-resultado"')
        self.assertLess(html.index("x1 = 2"), inicio_insight)
        self.assertEqual(html.count('class="concept-guide"'), html.count('class="concept-guide"', inicio_insight))
        self.assertEqual(html.count('class="concept-guide"'), 3)

    def test_guias_se_conservan_plegadas_en_todas_las_vistas_y_clasificaciones(self):
        casos = (
            (self.TEXTO, "Hay tantas columnas pivote como variables"),
            ("x1+x2=2;2x1+2x2=4", "Las variables libres parametrizan"),
            ("x1+x2=2;2x1+2x2=5", "representa una contradicción"),
        )
        for herramienta in catalogo.herramientas_de(catalogo.SISTEMAS_ECUACIONES):
            for sistema, explicacion in casos:
                with self.subTest(herramienta=herramienta.id, sistema=sistema):
                    respuesta = self.client.post(herramienta.ruta, {
                        "sistema": sistema, "metodo": "gauss_jordan",
                    })
                    html = respuesta.content.decode("utf-8")
                    apertura = '<details class="insight" id="entender-resultado">'
                    self.assertContains(respuesta, apertura, count=1)
                    contenido = html.split(apertura, 1)[1].split("</details>", 1)[0]
                    self.assertIn(explicacion, contenido)
                    self.assertEqual(contenido.count('class="concept-guide"'),
                                     html.count('class="concept-guide"'))
                    self.assertContains(respuesta, "Procedimiento paso a paso")

    def test_sin_guias_ni_relacionadas_no_quedan_contenedores_vacios(self):
        with patch("frontend.web.calculadora.views.guias_para_resultado", return_value=()):
            respuesta = self.client.post("/sistemas/", {
                "sistema": self.TEXTO, "metodo": "gauss",
            })
        for ausente in ("entender-resultado", "concept-guides", 'class="related"', "related-title"):
            self.assertNotContains(respuesta, ausente)
        for presente in ("Resultado final", "Procedimiento paso a paso", "x1 = 2"):
            self.assertContains(respuesta, presente)

    def test_compartir_exige_csrf(self):
        from django.test import Client

        respuesta = Client(enforce_csrf_checks=True).post("/sistemas/gauss-jordan/", {
            "sistema": self.TEXTO, "metodo": "gauss",
        })
        self.assertEqual(respuesta.status_code, 403)
