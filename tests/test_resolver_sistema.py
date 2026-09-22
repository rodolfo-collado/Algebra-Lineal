"""Resolver un sistema como única herramienta: método, bloques a mostrar, comparación y rutas antiguas."""

import os
import re
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import Client, SimpleTestCase
from django.utils.html import strip_tags

from frontend.web.calculadora import catalogo
from frontend.web.calculadora.opciones_sistemas import (
    BLOQUES,
    BLOQUES_PREDETERMINADOS,
    METODO_PREDETERMINADO,
    METODOS,
    RUTAS_ANTIGUAS,
)
from frontend.web.calculadora.servicios import resolver_entrada_web
from tests.test_columnas_pivote import CASOS
from tests.test_navegacion import PSEUDO_HERRAMIENTAS, Documento
from tests.test_web import datos_matriz

UNICA = "x1+x2=3;x1-x2=1"
INFINITAS = "x1+x2=2;2x1+2x2=4"
INCONSISTENTE = "x1+x2=2;2x1+2x2=5"
TODOS = list(BLOQUES_PREDETERMINADOS)


def seccion_resultado(respuesta):
    """Texto plano solo del resultado: el formulario también nombra los bloques."""
    html = respuesta.content.decode("utf-8")
    if 'id="resultado"' not in html:
        return ""
    return " ".join(strip_tags(html[html.index('id="resultado"'):]).split())


class PruebasNavegacionUnificada(SimpleTestCase):
    def test_la_navegacion_no_lista_las_pseudo_herramientas(self):
        rutas = ("/sistemas/", "/vectores/operaciones/", "/matrices/operaciones/", "/matrices/ecuaciones/", "/bases/conversion/")
        for ruta in ("/", *rutas):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                documento = Documento(respuesta)
                enlaces = {a["href"] for a in documento.enlaces_en("Herramientas")}
                self.assertEqual(enlaces, {"/", *rutas})
                html = respuesta.content.decode("utf-8")
                for antigua in RUTAS_ANTIGUAS:
                    self.assertNotIn(f"/sistemas/{antigua}/", html)
                # Ni en la barra lateral ni en el catalogo de Inicio; en el formulario
                # de sistemas "Gauss-Jordan" y "Columnas pivote" siguen siendo opciones.
                sidebar = html[html.index('<aside id="navegacion-principal"'):html.index("</aside>")]
                for nombre in PSEUDO_HERRAMIENTAS:
                    self.assertNotIn(nombre, sidebar)
                    if ruta == "/":
                        self.assertNotIn(f">{nombre}<", html)

    def test_inicio_y_busqueda_llevan_a_resolver_un_sistema(self):
        inicio = self.client.get("/")
        self.assertContains(inicio, 'href="/sistemas/"')
        # Cada tema del Inicio despliega sus herramientas; ya no hay chips de acceso rápido.
        self.assertEqual(
            [a["href"] for _, a in Documento(inicio).enlaces if a.get("class") == "tool-link"],
            ["/sistemas/", "/vectores/operaciones/", "/matrices/operaciones/", "/matrices/ecuaciones/", "/bases/conversion/"],
        )
        self.assertNotContains(inicio, "Acceso rápido")
        for consulta in ("gauss", "clasificación", "columnas pivote"):
            with self.subTest(consulta=consulta):
                respuesta = self.client.get("/", {"q": consulta})
                self.assertContains(respuesta, "1 herramienta coincide")
                self.assertContains(respuesta, "Resolver un sistema")

    def test_rutas_antiguas_redirigen_a_resolver_un_sistema(self):
        destinos = {
            "/sistemas/gauss/": "/sistemas/?metodo=gauss",
            "/sistemas/gauss-jordan/": "/sistemas/?metodo=gauss_jordan",
            "/sistemas/clasificacion/": "/sistemas/",
            "/sistemas/columnas-pivote/": "/sistemas/",
        }
        for ruta, destino in destinos.items():
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertEqual(respuesta.status_code, 301)
                self.assertEqual(respuesta["Location"], destino)
                pagina = self.client.get(ruta, follow=True)
                self.assertEqual(pagina.status_code, 200)
                self.assertContains(pagina, 'id="sistema-form"')
        # Un envío a una ruta antigua tampoco produce un error: se redirige igual.
        self.assertEqual(self.client.post("/sistemas/gauss/", {"sistema": "x1=1"}).status_code, 301)
        for ruta in ("/sistemas/inexistente/", "/sistemas/sistemas/"):
            self.assertEqual(self.client.get(ruta).status_code, 404)

    def test_la_ruta_antigua_de_un_metodo_lo_deja_seleccionado(self):
        for metodo in ("gauss", "gauss_jordan"):
            with self.subTest(metodo=metodo):
                pagina = self.client.get("/sistemas/", {"metodo": metodo})
                marcados = [c["value"] for c in Documento(pagina).controles
                            if c.get("name") == "metodo" and "checked" in c]
                self.assertEqual(marcados, [metodo])
        # Un método desconocido en la URL no rompe nada: queda el predeterminado.
        pagina = self.client.get("/sistemas/", {"metodo": "otro"})
        marcados = [c["value"] for c in Documento(pagina).controles if c.get("name") == "metodo" and "checked" in c]
        self.assertEqual(marcados, [METODO_PREDETERMINADO])

    def test_sin_herramientas_relacionadas(self):
        for respuesta in (
            self.client.get("/sistemas/"),
            self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "gauss"}),
            self.client.post("/sistemas/", {"sistema": UNICA, "metodo": "comparar"}),
            self.client.post("/sistemas/", {"sistema": "x1+=1", "metodo": "gauss"}),
        ):
            for ausente in ("Herramientas relacionadas", "Continúa con este mismo sistema", 'class="related"', "formaction="):
                self.assertNotContains(respuesta, ausente)


class PruebasFormularioResolver(SimpleTestCase):
    def test_metodo_y_mostrar_son_controles_compactos(self):
        pagina = self.client.get("/sistemas/")
        documento = Documento(pagina)
        metodos = [c for c in documento.controles if c.get("name") == "metodo"]
        self.assertEqual([(c["type"], c["value"]) for c in metodos], [("radio", clave) for clave, _ in METODOS])
        self.assertEqual([c["value"] for c in metodos if "checked" in c], [METODO_PREDETERMINADO])
        casillas = [c for c in documento.controles if c.get("name") == "mostrar"]
        self.assertEqual([(c["type"], c["value"]) for c in casillas], [("checkbox", clave) for clave, _ in BLOQUES])
        self.assertTrue(all("checked" in c for c in casillas))
        marcador = next(c for c in documento.controles if c.get("name") == "mostrar_definido")
        self.assertEqual(marcador["type"], "hidden")
        html = pagina.content.decode("utf-8")
        for etiqueta in ("Gauss", "Gauss-Jordan", "Comparar ambos", "Procedimiento", "Clasificación", "Columnas pivote", "Sistema resultante"):
            self.assertIn(f"<span>{etiqueta}</span>", html)
        # El método es un selector segmentado y los bloques van en píldoras compactas, no en tarjetas.
        self.assertEqual(html.count('<label class="option">'), len(BLOQUES))
        self.assertEqual(html.count('<label class="segment">'), len(METODOS) + 2)
        self.assertNotIn('class="choice"', html)

    def test_tipo_de_entrada_es_un_selector_segmentado(self):
        pagina = self.client.get("/sistemas/")
        html = pagina.content.decode("utf-8")
        documento = Documento(pagina)
        tipos = [c for c in documento.controles if c.get("name") == "tipo_entrada"]
        self.assertEqual([(c["type"], c["value"]) for c in tipos], [("radio", "sistema"), ("radio", "matriz")])
        self.assertEqual([c["value"] for c in tipos if "checked" in c], ["sistema"])
        # Dos segmentos para la entrada más los del método, que comparte el mismo patrón compacto.
        self.assertEqual(html.count('<label class="segment">'), 2 + len(METODOS))
        self.assertIn("<span>Sistema de ecuaciones</span>", html)
        self.assertIn("<span>Matriz aumentada</span>", html)
        # Una explicación por opción; solo la de la opción elegida queda visible sin JavaScript.
        self.assertRegex(html, r'data-input-hint="sistema"\s*>\s*Escribe las ecuaciones directamente\.')
        self.assertRegex(html, r'data-input-hint="matriz"\s+hidden>\s*Ingresa los coeficientes en la matriz \[A \| b\]\.')
        self.assertIn('[data-input-hint]', (Path(__file__).resolve().parents[1]
                       / "frontend/web/calculadora/static/calculadora/matriz.js").read_text(encoding="utf-8"))

        matriz = self.client.post("/sistemas/", datos_matriz([[1, 1, 3], [1, -1, 1]], "gauss"))
        html = matriz.content.decode("utf-8")
        self.assertRegex(html, r'data-input-hint="matriz"\s*>\s*Ingresa los coeficientes')
        self.assertRegex(html, r'data-input-hint="sistema"\s+hidden>')
        self.assertContains(pagina, ">Resolver</button>")
        self.assertContains(pagina, "La matriz final y la solución se muestran siempre.")
        self.assertNotContains(pagina, "tool-note")

    def test_metodos_alternativos_no_son_casillas(self):
        documento = Documento(self.client.get("/sistemas/"))
        self.assertFalse(any(c.get("name") == "metodo" and c.get("type") == "checkbox" for c in documento.controles))

    def test_compartir_exige_csrf(self):
        respuesta = Client(enforce_csrf_checks=True).post("/sistemas/", {"sistema": UNICA, "metodo": "gauss"})
        self.assertEqual(respuesta.status_code, 403)


class PruebasMetodos(SimpleTestCase):
    def resolver(self, metodo, sistema=UNICA, mostrar=None):
        datos = {"sistema": sistema, "metodo": metodo, "mostrar_definido": "1", "mostrar": TODOS if mostrar is None else mostrar}
        with patch("frontend.web.calculadora.views.resolver_entrada_web", wraps=resolver_entrada_web) as resolver:
            respuesta = self.client.post("/sistemas/", datos)
        return respuesta, [llamada.args[1] for llamada in resolver.call_args_list]

    def test_seleccion_gauss(self):
        respuesta, metodos = self.resolver("gauss")
        self.assertEqual(metodos, ["gauss"])
        texto = seccion_resultado(respuesta)
        self.assertIn("Procedimiento y resultado Gauss ", texto)
        for presente in ("Matriz escalonada", "Sustitución regresiva", "Columnas pivote: C1, C2", "Consistente de solución única", "x1 = 2", "x2 = 1"):
            self.assertIn(presente, texto)
        self.assertNotIn("Matriz reducida", texto)
        self.assertNotIn("Gauss-Jordan", texto.split("Entender este resultado")[0])

    def test_seleccion_gauss_jordan(self):
        respuesta, metodos = self.resolver("gauss_jordan")
        self.assertEqual(metodos, ["gauss_jordan"])
        texto = seccion_resultado(respuesta)
        self.assertIn("Procedimiento y resultado Gauss-Jordan ", texto)
        for presente in ("Matriz reducida", "Columnas pivote: C1, C2", "x1 = 2", "x2 = 1"):
            self.assertIn(presente, texto)
        self.assertNotIn("Matriz escalonada", texto)
        self.assertNotIn("Sustitución regresiva", texto)

    def test_comparar_ambos_muestra_los_dos_procedimientos_y_un_solo_resultado(self):
        respuesta, metodos = self.resolver("comparar")
        self.assertEqual(metodos, ["gauss", "gauss_jordan"])
        html = respuesta.content.decode("utf-8")
        texto = seccion_resultado(respuesta)
        self.assertIn("Comparación de métodos Gauss y Gauss-Jordan", texto)
        self.assertEqual(texto.count("Operaciones por filas"), 2)
        self.assertEqual(texto.count("Matriz inicial"), 1)
        self.assertLess(texto.index("Matriz escalonada"), texto.index("Matriz reducida"))
        self.assertEqual(texto.count("Sustitución regresiva"), 1)
        # Pivotes, clasificación y solución son comunes: aparecen una sola vez, en el resultado
        # que precede al procedimiento plegado.
        self.assertEqual(texto.count("Columnas pivote:"), 1)
        self.assertLess(texto.index("Resultado final"), texto.index("Columnas pivote:"))
        self.assertEqual(html.count('class="classification"'), 1)
        self.assertEqual(texto.count("Solución x1 = 2 x2 = 1"), 1)
        self.assertLess(texto.index("Resultado final"), texto.index("Matriz escalonada"))
        # Cada matriz final sigue resaltando sus columnas pivote (2 filas x 2 pivotes por método).
        self.assertEqual(html.count(' pivot"'), 8)
        self.assertEqual(html.count('class="disclosure disclosure-nested"'), 2)
        # Las guías de los dos métodos quedan plegadas después del resultado.
        self.assertContains(respuesta, "Gauss se detiene en forma escalonada")
        self.assertContains(respuesta, "Gauss-Jordan reduce por completo")
        self.assertEqual(html.count('class="concept-guide"'), 4)
        ids = re.findall(r' id="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))

    def test_comparar_coincide_con_cada_metodo_por_separado(self):
        for nombre, matriz, columnas, clasificacion in CASOS:
            with self.subTest(caso=nombre):
                datos = datos_matriz(matriz, "comparar")
                datos.update({"mostrar_definido": "1", "mostrar": TODOS})
                texto = seccion_resultado(self.client.post("/sistemas/", datos))
                esperado = ", ".join(f"C{c}" for c in columnas) or "Ninguna"
                self.assertEqual(texto.count(f"Columnas pivote: {esperado}"), 1)
                self.assertEqual(texto.count(clasificacion), 1)
                for metodo in ("gauss", "gauss_jordan"):
                    resultado = resolver_entrada_web("matriz", metodo, matriz_aumentada=matriz)
                    for linea in resultado["solucion_general"]:
                        self.assertIn(linea, texto)

    def test_comparar_no_repite_las_columnas_pivote(self):
        """Regresión: el análisis de pivotes es común y no se muestra por método."""
        con, _ = self.resolver("comparar", mostrar=["pivotes"])
        html = con.content.decode("utf-8")
        texto = seccion_resultado(con)
        self.assertEqual(texto.count("Columnas pivote:"), 1)
        self.assertEqual(html.count('class="pivot-block"'), 1)
        self.assertLess(texto.index("Resultado final"), texto.index("Solución"))
        self.assertLess(texto.index("Solución"), texto.index("Columnas pivote:"))
        self.assertEqual(html.count(' pivot"'), 8)

        sin, _ = self.resolver("comparar", mostrar=["procedimiento", "clasificacion"])
        html = sin.content.decode("utf-8")
        texto = seccion_resultado(sin)
        self.assertNotIn("Columnas pivote", texto)
        self.assertNotIn('class="pivot-block"', html)
        self.assertNotIn(' pivot"', html)
        self.assertIn("Resultado final Clasificación Consistente de solución única Solución x1 = 2 x2 = 1", texto)

    def test_la_misma_entrada_da_los_mismos_resultados_que_antes(self):
        """Sin la sección Mostrar (clientes antiguos) se muestra todo, como hasta ahora."""
        for metodo in ("gauss", "gauss_jordan"):
            for nombre, matriz, columnas, clasificacion in CASOS:
                with self.subTest(metodo=metodo, caso=nombre):
                    respuesta = self.client.post("/sistemas/", datos_matriz(matriz, metodo))
                    texto = seccion_resultado(respuesta)
                    esperado = ", ".join(f"C{c}" for c in columnas) or "Ninguna"
                    self.assertIn(f"Columnas pivote: {esperado}", texto)
                    self.assertIn(clasificacion, texto)
                    self.assertIn("Operaciones por filas", texto)
                    resultado = resolver_entrada_web("matriz", metodo, matriz_aumentada=matriz)
                    for linea in resultado["solucion_general"]:
                        self.assertIn(linea, texto)
                    if resultado["mostrar_sistema_resultante"]:
                        self.assertIn("Sistema resultante", texto)


class PruebasBloquesDelResultado(SimpleTestCase):
    def resolver(self, mostrar, metodo="gauss", sistema=UNICA):
        return self.client.post("/sistemas/", {
            "sistema": sistema, "metodo": metodo, "mostrar_definido": "1", "mostrar": mostrar,
        })

    def test_la_solucion_final_siempre_se_muestra(self):
        respuesta = self.resolver([])
        texto = seccion_resultado(respuesta)
        # La solución encabeza el resultado; la matriz final la acompaña después.
        self.assertIn("Resultado final Solución x1 = 2 x2 = 1 Matriz escalonada", texto)
        for ausente in ("Matriz inicial", "Procedimiento paso a paso", "Columnas pivote", "Sistema resultante",
                        "Sustitución regresiva", "Clasificación", "Consistente"):
            self.assertNotIn(ausente, texto)
        html = respuesta.content.decode("utf-8")
        # Solo el panel de entrada y el del resultado final: sin procedimiento no hay más paneles.
        self.assertEqual(html.count('<section class="panel'), 2)
        self.assertNotIn('class="steps"', html)
        self.assertNotIn(' pivot"', html)

    def test_mostrar_u_ocultar_procedimiento(self):
        con = seccion_resultado(self.resolver(["procedimiento"]))
        sin = seccion_resultado(self.resolver(["clasificacion", "pivotes", "sistema-resultante"]))
        for bloque in ("Ver procedimiento", "Matriz inicial", "Operaciones por filas", "Paso 1", "Sustitución regresiva"):
            self.assertIn(bloque, con)
            self.assertNotIn(bloque, sin)
        self.assertIn("Procedimiento y resultado", con)
        self.assertNotIn("Procedimiento y resultado", sin)
        self.assertIn("Solución x1 = 2 x2 = 1", sin)

    def test_mostrar_u_ocultar_clasificacion(self):
        con = self.resolver(["clasificacion"], sistema=INCONSISTENTE)
        sin = self.resolver(["procedimiento"], sistema=INCONSISTENTE)
        self.assertContains(con, 'class="classification"')
        self.assertContains(con, 'data-kind="inconsistente"')
        self.assertIn("Clasificación Inconsistente", seccion_resultado(con))
        self.assertNotContains(sin, 'class="classification"')
        self.assertNotIn("Clasificación", seccion_resultado(sin).split("Entender este resultado")[0])
        # La justificación matemática pertenece a la solución y sigue visible.
        self.assertIn("representa una contradicción", seccion_resultado(sin).lower().replace("[0 0 | 5]", ""))

    def test_mostrar_u_ocultar_columnas_pivote(self):
        con = self.resolver(["pivotes"], metodo="gauss_jordan")
        sin = self.resolver(["procedimiento", "clasificacion"], metodo="gauss_jordan")
        self.assertIn("Columnas pivote: C1, C2", seccion_resultado(con))
        self.assertContains(con, 'class="pivot-chip"')
        self.assertContains(con, ' pivot"')
        self.assertContains(con, "Una columna pivote indica una variable determinada")
        self.assertNotIn("Columnas pivote", seccion_resultado(sin))
        self.assertNotContains(sin, 'class="pivot-chip"')
        self.assertNotContains(sin, ' pivot"')
        self.assertNotContains(sin, "Una columna pivote indica una variable determinada")

    def test_mostrar_u_ocultar_sistema_resultante(self):
        con = seccion_resultado(self.resolver(["sistema-resultante"], sistema=INFINITAS))
        sin = seccion_resultado(self.resolver(["procedimiento", "clasificacion", "pivotes"], sistema=INFINITAS))
        self.assertIn("Sistema resultante x1 + x2 = 2 0 = 0", con)
        self.assertNotIn("Sistema resultante", sin)
        for texto in (con, sin):
            self.assertIn("x2 es libre", texto)

    def test_sin_contenedores_vacios(self):
        combinaciones = ([], ["procedimiento"], ["pivotes"], ["clasificacion"], ["sistema-resultante"], TODOS)
        for metodo in ("gauss", "gauss_jordan", "comparar"):
            for mostrar in combinaciones:
                for sistema in (UNICA, INFINITAS, INCONSISTENTE):
                    with self.subTest(metodo=metodo, mostrar=mostrar, sistema=sistema):
                        html = self.resolver(mostrar, metodo=metodo, sistema=sistema).content.decode("utf-8")
                        resultado = html[html.index('id="resultado"'):]
                        self.assertNotRegex(resultado, r'<div class="final-block[^"]*">\s*(<h4[^>]*>[^<]*</h4>)?\s*</div>')
                        self.assertNotRegex(resultado, r'<section class="panel[^"]*"[^>]*>\s*(<h3[^>]*>[^<]*</h3>)?\s*</section>')
                        self.assertNotRegex(resultado, r'<ul class="[^"]*">\s*</ul>')
                        self.assertNotRegex(resultado, r'<ol class="steps">\s*</ol>')
                        self.assertIn("Solución", strip_tags(resultado))

    def test_guias_plegadas_despues_del_resultado(self):
        pagina = self.client.get("/sistemas/")
        self.assertNotContains(pagina, "Entender este resultado")
        respuesta = self.resolver(TODOS)
        html = respuesta.content.decode("utf-8")
        apertura = '<details class="insight" id="entender-resultado">'
        self.assertEqual(html.count(apertura), 1)
        inicio_insight = html.index(apertura)
        self.assertLess(html.index("x1 = 2"), inicio_insight)
        self.assertEqual(html.count('class="concept-guide"'), html.count('class="concept-guide"', inicio_insight))
        self.assertEqual(html.count('class="concept-guide"'), 3)

    def test_sin_guias_no_quedan_contenedores_vacios(self):
        with patch("frontend.web.calculadora.views.guias_para_resultado", return_value=()):
            respuesta = self.resolver(TODOS)
        for ausente in ("entender-resultado", "concept-guides", 'class="related"', "related-title"):
            self.assertNotContains(respuesta, ausente)
        for presente in ("Resultado final", "Ver procedimiento", "Operaciones por filas", "x1 = 2"):
            self.assertContains(respuesta, presente)

    def test_entrada_invalida_muestra_el_error_sin_resultado(self):
        respuesta = self.client.post("/sistemas/", {"sistema": "x1+=1", "metodo": "comparar", "mostrar_definido": "1"})
        self.assertContains(respuesta, "Formato de sistema inválido")
        self.assertNotContains(respuesta, "Traceback")
        self.assertNotContains(respuesta, 'id="resultado"')
