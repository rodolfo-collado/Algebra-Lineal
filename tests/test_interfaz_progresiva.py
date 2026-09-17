"""Divulgación progresiva: Inicio por temas, menú bajo demanda, teclado y opciones plegados,
resultado primero y conexiones «También puedes explorar». Contratos HTML, POST y de los
scripts locales, sin depender de clases decorativas."""

import os
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.http import QueryDict
from django.test import SimpleTestCase
from django.utils.html import strip_tags

from frontend.web.calculadora import catalogo
from frontend.web.calculadora.exploraciones import exploraciones_sistema
from frontend.web.calculadora.forms import SistemaForm
from frontend.web.calculadora.opciones_sistemas import BLOQUES, BLOQUES_PREDETERMINADOS, METODO_PREDETERMINADO, METODOS
from frontend.web.calculadora.servicios import resolver_entrada_web
from tests.test_navegacion import Documento, disponibles
from tests.test_resolver_sistema import UNICA, seccion_resultado
from tests.test_teclado import Botones
from tests.test_web import datos_matriz

RAIZ = Path(__file__).resolve().parents[1]
CALCULADORA = RAIZ / "frontend" / "web" / "calculadora"
STATIC = CALCULADORA / "static" / "calculadora"
TEMPLATES = CALCULADORA / "templates" / "calculadora"
TODOS = list(BLOQUES_PREDETERMINADOS)


class Desplegables(HTMLParser):
    """Localiza los details de la página: id, clases, estado y el texto de su summary."""

    def __init__(self, html):
        super().__init__()
        self.details = []
        self._abiertos = []
        self._en_summary = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag == "details":
            entrada = {
                "id": atributos.get("id"),
                "clases": atributos.get("class", "").split(),
                "open": "open" in atributos,
                "hidden": "hidden" in atributos,
                "summary": "",
                "controles": [],
            }
            self.details.append(entrada)
            self._abiertos.append(entrada)
        elif tag == "summary" and self._abiertos:
            self._en_summary = True
        elif tag == "input" and self._abiertos:
            self._abiertos[-1]["controles"].append(atributos)

    def handle_endtag(self, tag):
        if tag == "details" and self._abiertos:
            self._abiertos.pop()
        elif tag == "summary":
            self._en_summary = False

    def handle_data(self, data):
        if self._en_summary and self._abiertos:
            self._abiertos[-1]["summary"] += data

    def por_id(self, id_):
        return next(d for d in self.details if d["id"] == id_)

    def con_clase(self, clase):
        return [d for d in self.details if clase in d["clases"]]


class Formulario(HTMLParser):
    """Reconstruye el envío que haría un navegador con el formulario tal cual llega del servidor."""

    def __init__(self, html, id_formulario):
        super().__init__()
        self.id_formulario = id_formulario
        self.datos = []
        self._dentro = False
        self._textarea = None
        self._deshabilitado = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag == "form" and atributos.get("id") == self.id_formulario:
            self._dentro = True
            return
        if not self._dentro:
            return
        if tag == "fieldset" and "disabled" in atributos:
            self._deshabilitado += 1
        if self._deshabilitado:
            return
        nombre = atributos.get("name")
        if tag == "input" and nombre:
            tipo = atributos.get("type", "text")
            if tipo in ("checkbox", "radio") and "checked" not in atributos:
                return
            if tipo == "submit":
                return
            self.datos.append((nombre, atributos.get("value", "on" if tipo == "checkbox" else "")))
        if tag == "textarea" and nombre:
            self._textarea = [nombre, ""]

    def handle_data(self, data):
        if self._textarea:
            self._textarea[1] += data

    def handle_endtag(self, tag):
        if tag == "form" and self._dentro:
            self._dentro = False
        if tag == "fieldset" and self._deshabilitado:
            self._deshabilitado -= 1
        if tag == "textarea" and self._textarea:
            self.datos.append(tuple(self._textarea))
            self._textarea = None

    def como_datos(self, **cambios):
        """Los datos del envío como los codifica el cliente de pruebas: una lista por campo repetido."""
        datos = {}
        for nombre, valor in self.datos:
            datos.setdefault(nombre, []).append(valor)
        datos.update({nombre: list(valor) if isinstance(valor, (list, tuple)) else [valor] for nombre, valor in cambios.items()})
        return datos


def texto_plano(html):
    return " ".join(strip_tags(html).split())


class PruebasMenuBajoDemanda(SimpleTestCase):
    def test_el_menu_nace_cerrado_y_un_solo_boton_lo_controla(self):
        for ruta in ("/", "/sistemas/", "/bases/conversion/"):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                html = respuesta.content.decode("utf-8")
                documento = Documento(respuesta)
                boton = next(c for c in documento.controles if c.get("id") == "navigation-toggle")
                self.assertEqual(boton["type"], "button")
                self.assertEqual(boton["aria-expanded"], "false")
                self.assertEqual(boton["aria-controls"], "navegacion-principal")
                # Sin JavaScript la navegación se ve en flujo; el botón solo aparece con el script.
                self.assertIn("hidden", boton)
                self.assertIn("sidebar-backdrop", documento.ids)
                cerrar = next(c for c in documento.controles if c.get("id") == "sidebar-close")
                self.assertEqual(cerrar["type"], "button")
                # Ya no hay una columna permanente ni una preferencia guardada para ella.
                self.assertNotIn("data-menu", html)
                self.assertNotIn('"algebra-lineal-menu"', html)
                self.assertContains(respuesta, 'root.classList.add("js")')

    def test_navigation_js_abre_cierra_con_escape_y_fondo_y_devuelve_el_foco(self):
        script = (STATIC / "navigation.js").read_text(encoding="utf-8")
        for contrato in (
            'button.setAttribute("aria-expanded", String(abierto))',
            'root.toggleAttribute("data-drawer", abierto)',
            "sidebar.hidden = !abierto",
            "main.inert = abierto",
            'event.key === "Escape" && abierto',
            'backdrop.addEventListener("click", cerrar)',
            'closeButton.addEventListener("click", cerrar)',
            "button.focus()",
            "primero.focus()",
            'window.addEventListener("hashchange", revelarDestino)',
        ):
            self.assertIn(contrato, script)
        # El cajón se comporta igual en cualquier ancho: no hay modo columna ni preferencia guardada.
        self.assertNotIn("max-width: 880px", script)
        self.assertNotIn("algebra-lineal-menu\"", script)
        self.assertNotIn("data-menu", script)

    def test_el_css_esconde_el_cajon_cerrado_sin_dejar_hueco(self):
        shell = (STATIC / "styles" / "shell.css").read_text(encoding="utf-8")
        self.assertRegex(shell, r"\.js \.app-sidebar \{[^}]*position: fixed;[^}]*display: none;")
        self.assertRegex(shell, r"\.js\[data-drawer\] \.app-sidebar \{\s*display: block;")
        self.assertNotIn("data-menu", shell)
        self.assertNotIn("grid-template-columns: var(--nav-width)", shell)
        tokens = (STATIC / "styles" / "tokens.css").read_text(encoding="utf-8")
        self.assertIn("--nav-width", tokens)
        self.assertIn("--content-max", tokens)

    def test_el_cajon_conserva_rutas_estado_activo_y_buscador_tambien_tras_resolver(self):
        paginas = [(h.ruta, self.client.get(h.ruta), h.ruta) for h in disponibles()]
        paginas.append(("/", self.client.get("/"), "/"))
        paginas.append(("/sistemas/ (POST)", self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss"}), "/sistemas/"))
        for nombre, respuesta, activa in paginas:
            with self.subTest(pagina=nombre):
                documento = Documento(respuesta)
                enlaces = documento.enlaces_en("Herramientas")
                self.assertEqual({a["href"] for a in enlaces}, {"/", *(h.ruta for h in disponibles())})
                self.assertEqual([a["href"] for a in enlaces if a.get("aria-current") == "page"], [activa])
                formularios = [f for f in documento.formularios if f.get("role") == "search"]
                self.assertTrue(any(f.get("data-buscador") == "arbol-herramientas" for f in formularios))
                for area in catalogo.AREAS:
                    self.assertContains(respuesta, area.nombre)


class PruebasInicioPorTemas(SimpleTestCase):
    def test_el_inicio_presenta_temas_plegados_y_ver_mas_temas(self):
        respuesta = self.client.get("/")
        html = respuesta.content.decode("utf-8")
        desplegables = Desplegables(html)
        for categoria in catalogo.CATEGORIAS:
            with self.subTest(categoria=categoria.id):
                tema = desplegables.por_id(categoria.id)
                self.assertIn("topic", tema["clases"])
                self.assertFalse(tema["open"])
                self.assertIn(categoria.nombre, tema["summary"])
                self.assertIn(categoria.descripcion, tema["summary"])
                if not categoria.disponible:
                    self.assertIn("Próximamente", tema["summary"])
        # La primera área queda a la vista; las demás esperan bajo «Ver más temas».
        mas_temas = desplegables.por_id("mas-temas")
        self.assertFalse(mas_temas["open"])
        self.assertIn("Ver más temas", mas_temas["summary"])
        primera, *otras = catalogo.AREAS
        inicio_mas = html.index('id="mas-temas"')
        self.assertLess(html.index(f'id="{primera.id}"'), inicio_mas)
        for area in otras:
            self.assertGreater(html.index(f'id="{area.id}"'), inicio_mas)
            self.assertIn(area.nombre, mas_temas["summary"])
        # Cada herramienta se descubre dentro de su tema, una sola vez.
        for herramienta in disponibles():
            inicio_tema = html.index(f'id="{herramienta.categoria.id}"')
            fin_tema = html.index("</details>", inicio_tema)
            self.assertIn(f'href="{herramienta.ruta}"', html[inicio_tema:fin_tema])
        self.assertEqual(html.count('<a class="tool-link"'), len(disponibles()))

    def test_el_inicio_es_breve_sin_accesos_duplicados(self):
        respuesta = self.client.get("/")
        html = respuesta.content.decode("utf-8")
        self.assertContains(respuesta, '<h1 class="home-title">Álgebra Lineal</h1>', html=True)
        self.assertContains(respuesta, "Aprende resolviendo")
        self.assertContains(respuesta, "¿Qué quieres resolver?")
        for ausente in ("Calculadora educativa", "Explora los temas disponibles", "Acceso rápido", 'class="chip"'):
            self.assertNotIn(ausente, html)
        # Un solo buscador principal; el del cajón solo aparece al abrir el menú.
        self.assertEqual(html.count("search-large"), 1)
        self.assertLess(html.index('id="buscador-inicio"'), html.index('id="algebra-lineal"'))
        # Ningún área ni tema se lista fuera de su lugar: los ids de breadcrumbs siguen existiendo.
        ids = Documento(respuesta).ids
        for elemento in (*catalogo.AREAS, *catalogo.CATEGORIAS):
            self.assertIn(elemento.id, ids)

    def test_la_busqueda_del_inicio_sigue_filtrando_los_temas(self):
        html = self.client.get("/").content.decode("utf-8")
        # buscador.js abre los details con coincidencias y oculta los grupos vacíos: los temas y
        # «Ver más temas» deben declararse como grupos con sus índices dentro.
        for id_ in ("mas-temas", *(c.id for c in catalogo.CATEGORIAS)):
            self.assertRegex(html, rf'<details class="[^"]*" id="{id_}" data-grupo>')
        for herramienta in catalogo.HERRAMIENTAS:
            self.assertIn(f'data-indice="{herramienta.indice}"', html)
        self.assertContains(self.client.get("/", {"q": "binario"}), "Ver todos los temas")


class PruebasFormularioProgresivo(SimpleTestCase):
    def test_metodo_y_entrada_son_selectores_segmentados_con_una_sola_seleccion(self):
        html = self.client.get("/sistemas/").content.decode("utf-8")
        formulario = html[html.index('id="sistema-form"'):html.index('id="system-fields"')]
        segmentos = re.findall(r'<label class="segment"><input type="radio" name="(\w+)" value="([^"]+)"', formulario)
        self.assertEqual(
            segmentos,
            [("metodo", clave) for clave, _ in METODOS] + [("tipo_entrada", "sistema"), ("tipo_entrada", "matriz")],
        )
        self.assertEqual(formulario.count('<div class="segmented">'), 2)
        marcados = re.findall(r'name="metodo" value="([^"]+)"[^>]*checked', formulario)
        self.assertEqual(marcados, [METODO_PREDETERMINADO])
        # Una pista de una línea por método, visible solo la del elegido (sin JavaScript también).
        self.assertRegex(formulario, r'data-method-hint="gauss_jordan"\s*>')
        self.assertRegex(formulario, r'data-method-hint="gauss"\s+hidden>')
        self.assertRegex(formulario, r'data-method-hint="comparar"\s+hidden>')
        self.assertIn("[data-method-hint]", (STATIC / "matriz.js").read_text(encoding="utf-8"))
        # Antes del problema no hay secciones de configuración ni casillas a la vista.
        for ausente in ("Configuración de entrada", ">Datos<", "<h3"):
            self.assertNotIn(ausente, formulario)

    def test_el_teclado_nace_plegado_y_conserva_sus_teclas(self):
        html = self.client.get("/sistemas/").content.decode("utf-8")
        desplegables = Desplegables(html)
        teclados = desplegables.con_clase("disclosure-keyboard")
        self.assertEqual(len(teclados), 2)
        for teclado in teclados:
            self.assertFalse(teclado["open"])
            self.assertTrue(teclado["hidden"])
            self.assertEqual(teclado["summary"].strip(), "Teclado matemático")
        # Los botones siguen dentro del grupo del teclado, con su inserción y su nombre accesible.
        botones = [attrs for grupo, attrs in Botones(html).botones if grupo == "teclado"]
        self.assertTrue(botones)
        for boton in botones:
            self.assertEqual(boton["type"], "button")
            self.assertTrue(boton["data-insercion"])
        # teclado.js muestra el desplegable (cerrado) y mantiene la inserción en el cursor.
        script = (STATIC / "teclado.js").read_text(encoding="utf-8")
        self.assertIn('teclado.closest("details.disclosure")', script)
        self.assertIn("desplegable.hidden = false", script)
        self.assertIn("setRangeText", script)
        self.assertNotIn("open = true", script)

    def test_el_teclado_plegado_llega_a_todas_las_herramientas(self):
        for ruta in ("/sistemas/", "/vectores/operaciones/", "/matrices/operaciones/", "/matrices/ecuaciones/", "/bases/conversion/"):
            with self.subTest(ruta=ruta):
                html = self.client.get(ruta).content.decode("utf-8")
                teclados = Desplegables(html).con_clase("disclosure-keyboard")
                self.assertTrue(teclados)
                self.assertTrue(all(t["hidden"] and not t["open"] for t in teclados))
                self.assertNotIn("math-keyboard-title", html)

    def test_las_opciones_de_resultado_nacen_plegadas_con_sus_predeterminados(self):
        html = self.client.get("/sistemas/").content.decode("utf-8")
        opciones = Desplegables(html).por_id("opciones-resultado")
        self.assertFalse(opciones["open"])
        self.assertFalse(opciones["hidden"])
        self.assertEqual(opciones["summary"].strip(), "Opciones de resultado")
        casillas = [c for c in opciones["controles"] if c.get("name") == "mostrar"]
        self.assertEqual([c["value"] for c in casillas], [clave for clave, _ in BLOQUES])
        self.assertTrue(all("checked" in c for c in casillas))
        self.assertTrue(any(c.get("name") == "mostrar_definido" for c in opciones["controles"]))
        self.assertIn("La matriz final y la solución se muestran siempre.", html)
        # Las opciones van después del problema y antes de la acción principal.
        self.assertLess(html.index('id="system-fields"'), html.index('id="opciones-resultado"'))
        self.assertLess(html.index('id="opciones-resultado"'), html.index(">Resolver</button>"))

    def test_lo_que_envia_el_formulario_plegado_produce_el_mismo_resultado(self):
        pagina = self.client.get("/sistemas/").content.decode("utf-8")
        formulario = Formulario(pagina, "sistema-form")
        nombres = {nombre for nombre, _ in formulario.datos}
        self.assertEqual(nombres, {"csrfmiddlewaretoken", "metodo", "tipo_entrada", "sistema", "mostrar_definido", "mostrar"})
        # Las casillas plegadas viajan igual: el resultado es el de siempre, con todos los bloques.
        datos = formulario.como_datos(sistema=UNICA)
        self.assertEqual(datos["mostrar"], TODOS)
        self.assertEqual(datos["metodo"], [METODO_PREDETERMINADO])
        respuesta = self.client.post("/sistemas/", datos)
        explicito = self.client.post("/sistemas/", {"sistema": UNICA, "metodo": METODO_PREDETERMINADO, "mostrar_definido": "1", "mostrar": TODOS})
        texto = seccion_resultado(respuesta)
        self.assertEqual(texto, seccion_resultado(explicito))
        for presente in ("Procedimiento paso a paso", "Clasificación", "Columnas pivote: C1, C2", "x1 = 2", "x2 = 1"):
            self.assertIn(presente, texto)

    def test_elegir_cada_metodo_desde_el_selector_envia_su_clave(self):
        pagina = self.client.get("/sistemas/").content.decode("utf-8")
        formulario = Formulario(pagina, "sistema-form")
        for clave, _ in METODOS:
            with self.subTest(metodo=clave):
                datos = formulario.como_datos(sistema=UNICA, metodo=clave)
                with patch("frontend.web.calculadora.views.resolver_entrada_web", wraps=resolver_entrada_web) as resolver:
                    respuesta = self.client.post("/sistemas/", datos)
                esperados = ["gauss", "gauss_jordan"] if clave == "comparar" else [clave]
                self.assertEqual([llamada.args[1] for llamada in resolver.call_args_list], esperados)
                marcados = re.findall(r'name="metodo" value="([^"]+)"[^>]*checked', respuesta.content.decode("utf-8"))
                self.assertEqual(marcados, [clave])

    def test_cambiar_el_modo_de_entrada_no_pierde_su_comportamiento(self):
        pagina = self.client.get("/sistemas/").content.decode("utf-8")
        self.assertRegex(pagina, r'<fieldset id="system-fields" class="input-mode">')
        self.assertRegex(pagina, r'<fieldset id="matrix-fields" class="input-mode" hidden disabled>')
        # El modo matricial sigue enviando sus celdas y resolviendo igual que el texto.
        matriz = self.client.post("/sistemas/", datos_matriz([[1, 1, 3], [1, -1, 1]], "gauss_jordan"))
        texto = self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss_jordan"})
        # Mismo resultado y mismas conexiones; solo cambia lo que viaja en los enlaces y en la cuadrícula.
        self.assertEqual(seccion_resultado(matriz).split("Plantear")[0], seccion_resultado(texto).split("Plantear")[0])
        html = matriz.content.decode("utf-8")
        self.assertRegex(html, r'name="tipo_entrada" value="matriz"[^>]*checked')
        self.assertRegex(html, r'data-input-hint="matriz"\s*>')
        self.assertRegex(html, r'data-input-hint="sistema"\s+hidden>')

    def test_las_opciones_se_despliegan_solas_cuando_difieren_de_lo_predeterminado(self):
        casos = (
            (self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss", "mostrar_definido": "1", "mostrar": ["pivotes"]}), True),
            (self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss", "mostrar_definido": "1", "mostrar": TODOS}), False),
            (self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss"}), False),
            (self.client.post("/sistemas/", {"sistema": "x1+=1", "metodo": "gauss", "mostrar_definido": "1", "mostrar": ["clasificacion"]}), True),
            (self.client.get("/sistemas/", {"mostrar_definido": "1", "mostrar": ["pivotes"]}), True),
            (self.client.get("/sistemas/"), False),
        )
        for respuesta, abiertas in casos:
            with self.subTest(abiertas=abiertas):
                opciones = Desplegables(respuesta.content.decode("utf-8")).por_id("opciones-resultado")
                self.assertEqual(opciones["open"], abiertas)


class PruebasResultadoPrimero(SimpleTestCase):
    def test_el_resultado_precede_al_procedimiento_y_enlaza_con_el(self):
        respuesta = self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss_jordan", "mostrar_definido": "1", "mostrar": TODOS})
        html = respuesta.content.decode("utf-8")
        texto = seccion_resultado(respuesta)
        orden = ("Resultado final", "Clasificación", "Consistente de solución única", "Solución x1 = 2 x2 = 1",
                 "Ver procedimiento", "Matriz reducida", "Columnas pivote:", "Entender este resultado",
                 "Procedimiento paso a paso", "Matriz inicial", "Paso 1")
        posiciones = [texto.index(fragmento) for fragmento in orden]
        self.assertEqual(posiciones, sorted(posiciones), orden)
        self.assertIn('href="#procedimiento"', html)
        self.assertEqual(html.count('id="procedimiento"'), 1)
        self.assertLess(html.index('id="resultado"'), html.index('id="procedimiento"'))

    def test_sin_procedimiento_no_hay_enlace_ni_ancla(self):
        respuesta = self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss", "mostrar_definido": "1", "mostrar": ["clasificacion", "pivotes"]})
        html = respuesta.content.decode("utf-8")
        self.assertNotIn("#procedimiento", html)
        self.assertNotIn('id="procedimiento"', html)
        self.assertNotIn("Ver procedimiento", html)
        self.assertIn("Resultado final Clasificación Consistente de solución única Solución x1 = 2 x2 = 1", seccion_resultado(respuesta))

    def test_comparar_pone_el_resultado_comun_antes_de_cada_metodo(self):
        respuesta = self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "comparar", "mostrar_definido": "1", "mostrar": TODOS})
        html = respuesta.content.decode("utf-8")
        texto = seccion_resultado(respuesta)
        orden = ("Resultado final", "Clasificación", "Solución x1 = 2 x2 = 1", "Ver procedimiento", "Columnas pivote:",
                 "Matriz inicial", "Procedimiento paso a paso", "Matriz escalonada", "Matriz reducida")
        posiciones = [texto.index(fragmento) for fragmento in orden]
        self.assertEqual(posiciones, sorted(posiciones), orden)
        self.assertEqual(html.count('<section class="panel panel-method"'), 2)
        self.assertLess(html.index('id="procedimiento"'), html.index('class="panel panel-method"'))


class PruebasExplorar(SimpleTestCase):
    def enlaces_explorar(self, respuesta):
        html = respuesta.content.decode("utf-8")
        if 'id="explore-title"' not in html:
            return []
        seccion = html[html.index('id="explore-title"'):html.index("</section>", html.index('id="explore-title"'))]
        enlaces = re.findall(r'<a class="explore-link" href="([^"]+)">\s*<span[^>]*>→</span>\s*<span>([^<]+)</span>', seccion)
        return [(unescape(href), texto) for href, texto in enlaces]

    def test_sin_resultado_no_se_ofrecen_exploraciones(self):
        for respuesta in (
            self.client.get("/sistemas/"),
            self.client.post("/sistemas/", {"sistema": "x1+=1", "metodo": "gauss"}),
            self.client.get("/vectores/operaciones/"),
            self.client.get("/"),
        ):
            self.assertNotContains(respuesta, "También puedes explorar")
            self.assertNotContains(respuesta, 'class="explore"')

    def test_tras_resolver_se_ofrecen_conexiones_a_rutas_existentes(self):
        respuesta = self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss", "mostrar_definido": "1", "mostrar": TODOS})
        enlaces = self.enlaces_explorar(respuesta)
        self.assertEqual(
            [texto for _, texto in enlaces],
            ["Resolver el mismo sistema con Gauss-Jordan", "Comparar Gauss y Gauss-Jordan con este sistema",
             "Plantear un sistema como ecuación matricial Ax = b"],
        )
        html = respuesta.content.decode("utf-8")
        self.assertLess(html.index("Entender este resultado"), html.index('id="explore-title"'))
        self.assertLess(html.index('id="procedimiento"'), html.index('id="explore-title"'))
        for href, _ in enlaces:
            destino = urlsplit(href)
            self.assertFalse(destino.netloc)
            self.assertEqual(self.client.get(destino.path).status_code, 200)
        self.assertEqual(enlaces[-1][0], catalogo.ECUACIONES_MATRICIALES.ruta)
        consulta = parse_qs(urlsplit(enlaces[0][0]).query)
        self.assertEqual(consulta["metodo"], ["gauss_jordan"])
        self.assertEqual(consulta["sistema"], [UNICA])
        self.assertEqual(consulta["tipo_entrada"], ["sistema"])
        self.assertEqual(consulta["mostrar"], TODOS)
        self.assertEqual(parse_qs(urlsplit(enlaces[1][0]).query)["metodo"], ["comparar"])

    def test_el_enlace_prepara_el_mismo_sistema_sin_resolverlo(self):
        respuesta = self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss", "mostrar_definido": "1", "mostrar": TODOS})
        href = self.enlaces_explorar(respuesta)[0][0]
        pagina = self.client.get(href)
        self.assertEqual(pagina.status_code, 200)
        html = pagina.content.decode("utf-8")
        self.assertNotIn('id="resultado"', html)
        self.assertRegex(html, r'name="metodo" value="gauss_jordan"[^>]*checked')
        self.assertIn(">\n" + UNICA + "</textarea>", html)
        self.assertRegex(html, r'data-method-hint="gauss_jordan"\s*>')
        # Resolver desde ahí da exactamente lo mismo que con el otro método elegido a mano.
        formulario = Formulario(html, "sistema-form")
        directo = self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss_jordan", "mostrar_definido": "1", "mostrar": TODOS})
        self.assertEqual(seccion_resultado(self.client.post("/sistemas/", formulario.como_datos())), seccion_resultado(directo))

    def test_los_bloques_omitidos_se_ofrecen_y_la_matriz_viaja_completa(self):
        datos = datos_matriz([[1, 1, 3], [1, -1, 1]], "gauss")
        datos.update({"mostrar_definido": "1", "mostrar": ["procedimiento", "clasificacion"]})
        respuesta = self.client.post("/sistemas/", datos)
        enlaces = self.enlaces_explorar(respuesta)
        self.assertEqual(
            [texto for _, texto in enlaces],
            ["Resolver el mismo sistema con Gauss-Jordan", "Comparar Gauss y Gauss-Jordan con este sistema",
             "Ver las columnas pivote", "Ver el sistema resultante", "Plantear un sistema como ecuación matricial Ax = b"],
        )
        href = next(href for href, texto in enlaces if texto == "Ver las columnas pivote")
        consulta = parse_qs(urlsplit(href).query)
        self.assertEqual(consulta["tipo_entrada"], ["matriz"])
        self.assertEqual((consulta["ecuaciones"], consulta["variables"]), (["2"], ["2"]))
        self.assertEqual(consulta["matriz_1_1"], ["-1"])
        self.assertEqual(consulta["mostrar"], ["procedimiento", "clasificacion", "pivotes"])
        pagina = self.client.get(href)
        html = pagina.content.decode("utf-8")
        self.assertNotIn('id="resultado"', html)
        self.assertRegex(html, r'name="tipo_entrada" value="matriz"[^>]*checked')
        self.assertRegex(html, r'name="ecuaciones" value="2"')
        self.assertRegex(html, r'name="variables" value="2"')
        self.assertIn('[["1", "1", "3"], ["1", "-1", "1"]]', html)
        self.assertTrue(Desplegables(html).por_id("opciones-resultado")["open"])
        marcadas = re.findall(r'name="mostrar" value="([^"]+)"[^>]*checked', html)
        self.assertEqual(marcadas, ["procedimiento", "clasificacion", "pivotes"])

    def test_comparar_no_ofrece_otro_metodo_y_nada_se_inventa(self):
        respuesta = self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "comparar", "mostrar_definido": "1", "mostrar": TODOS})
        self.assertEqual(
            [texto for _, texto in self.enlaces_explorar(respuesta)],
            ["Plantear un sistema como ecuación matricial Ax = b"],
        )
        # La función solo enlaza al catálogo disponible: sin Ax = b no queda nada más que ofrecer.
        entrada = [("tipo_entrada", "sistema"), ("sistema", UNICA)]
        with patch.object(catalogo, "ECUACIONES_MATRICIALES", catalogo.HERRAMIENTAS[-1]):
            self.assertEqual(exploraciones_sistema(entrada, "comparar", frozenset(TODOS)), ())
        for exploracion in exploraciones_sistema(entrada, "gauss", frozenset()):
            self.assertTrue(exploracion.url.startswith("/"))

    def test_una_consulta_invalida_no_rompe_el_formulario(self):
        pagina = self.client.get("/sistemas/", {
            "tipo_entrada": "matriz", "ecuaciones": "abc", "variables": "-2", "metodo": "zzz",
            "mostrar_definido": "1", "mostrar": ["nada"], "sistema": "   ",
        })
        self.assertEqual(pagina.status_code, 200)
        html = pagina.content.decode("utf-8")
        self.assertRegex(html, rf'name="metodo" value="{METODO_PREDETERMINADO}"[^>]*checked')
        self.assertRegex(html, r'name="tipo_entrada" value="matriz"[^>]*checked')
        self.assertNotIn('name="ecuaciones" value="', html)
        self.assertEqual(re.findall(r'name="mostrar" value="([^"]+)"[^>]*checked', html), [])
        self.assertIn('id="matrix-initial-values"', html)
        self.assertEqual(SistemaForm.inicial_desde(QueryDict("ecuaciones=0&variables=3&metodo=gauss")), {"metodo": "gauss", "variables": 3})


class PruebasAccesibilidadProgresiva(SimpleTestCase):
    def test_los_controles_plegables_son_details_summary_y_botones_reales(self):
        for plantilla in TEMPLATES.rglob("*.html"):
            html = plantilla.read_text(encoding="utf-8")
            with self.subTest(plantilla=plantilla.relative_to(TEMPLATES).as_posix()):
                self.assertNotIn("onclick=", html)
                self.assertNotRegex(html, r'<(div|span)[^>]*role="button"')
                self.assertEqual(html.count("<details"), html.count("<summary"))
        for ruta in ("/", "/sistemas/"):
            html = self.client.get(ruta).content.decode("utf-8")
            with self.subTest(ruta=ruta):
                self.assertEqual(html.count("<details"), html.count("</details>"))
                self.assertEqual(html.count("<summary"), html.count("</summary>"))
                self.assertIn('aria-expanded="false" aria-controls="navegacion-principal"', html)

    def test_el_foco_visible_cubre_summary_y_el_texto_sigue_en_espanol(self):
        base = (STATIC / "styles" / "base.css").read_text(encoding="utf-8")
        self.assertIn("summary:focus-visible", base)
        for ruta in ("/", "/sistemas/"):
            html = self.client.get(ruta).content.decode("utf-8")
            for termino in ("Keyboard", "Options", "Explore", "More topics", "Menu<"):
                self.assertNotIn(f">{termino}", html)
