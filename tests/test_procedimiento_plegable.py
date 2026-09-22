"""P18: procedimiento plegable y resultado único.

Tras resolver, cada herramienta principal lee Entrada → Resultado (panel
visible, una sola vez) → «Ver procedimiento» (details cerrado). Se prueba la
estructura semántica (details/summary nativos, orden en el DOM, un solo panel
final) y que el contenido educativo sigue presente, sin depender de clases
decorativas ni de cadenas exactas del HTML más allá de los textos matemáticos.
"""

import os
import re
from html.parser import HTMLParser
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.template import Context, Template
from django.test import SimpleTestCase
from django.utils.html import strip_tags

from frontend.web.calculadora.opciones_sistemas import BLOQUES_PREDETERMINADOS
from tests.test_ecuaciones_matriciales_web import INCONSISTENTE as AXB_INCONSISTENTE
from tests.test_ecuaciones_matriciales_web import INFINITAS as AXB_INFINITAS
from tests.test_ecuaciones_matriciales_web import RUTA as RUTA_ECUACIONES
from tests.test_ecuaciones_matriciales_web import UNICA as AXB_UNICA
from tests.test_ecuaciones_matriciales_web import datos_ecuacion
from tests.test_matrices_web import RUTA as RUTA_MATRICES
from tests.test_matrices_web import Contenido, datos_matrices
from tests.test_multiplicacion_matrices_web import datos_matriz_vector, datos_producto
from tests.test_resolver_sistema import INCONSISTENTE, INFINITAS, UNICA
from tests.test_teclado import Pagina
from tests.test_vectores_web import RUTA as RUTA_VECTORES
from tests.test_vectores_web import combinacion, datos_vectores
from tests.test_web import datos_matriz

RAIZ = Path(__file__).resolve().parents[1]
TEMPLATES = RAIZ / "frontend" / "web" / "calculadora" / "templates" / "calculadora"
TODOS = list(BLOQUES_PREDETERMINADOS)
HERRAMIENTAS = ("/sistemas/", RUTA_VECTORES, RUTA_MATRICES, RUTA_ECUACIONES)
# Los mismos tres sistemas de test_resolver_sistema escritos como matriz aumentada.
MATRICES = {UNICA: [[1, 1, 3], [1, -1, 1]], INFINITAS: [[1, 1, 2], [2, 2, 4]], INCONSISTENTE: [[1, 1, 2], [2, 2, 5]]}


class Estructura(HTMLParser):
    """Lee la sección de resultados en orden: cada details (con profundidad, estado y
    título de su summary) y el panel del resultado final, para razonar sobre el DOM
    sin depender de clases decorativas."""

    def __init__(self, html):
        super().__init__()
        self.eventos = []
        self._pila = []
        self._summary = None
        self._en_resultado = False
        self._profundidad_resultado = 0
        self._profundidad = 0
        self.feed(html)

    def handle_starttag(self, tag, atributos):
        atributos = dict(atributos)
        clases = atributos.get("class", "").split()
        if atributos.get("id") == "resultado":
            self._en_resultado = True
            self._profundidad_resultado = self._profundidad
        self._profundidad += 1
        if not self._en_resultado:
            return
        if tag == "details":
            detalle = {
                "id": atributos.get("id"), "clases": clases, "open": "open" in atributos,
                "nivel": len(self._pila), "summary": "", "encabezado": None,
            }
            self.eventos.append(("details", detalle))
            self._pila.append(detalle)
        elif tag == "summary" and self._pila:
            self._summary = self._pila[-1]
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if self._summary is not None:
                self._summary["encabezado"] = tag
            self.eventos.append(("encabezado", {"nivel": int(tag[1]), "dentro": len(self._pila)}))
        elif "panel-final" in clases:
            self.eventos.append(("panel-final", {"dentro": len(self._pila)}))

    def handle_endtag(self, tag):
        self._profundidad -= 1
        if self._en_resultado and self._profundidad == self._profundidad_resultado:
            self._en_resultado = False
        if not self._en_resultado:
            return
        if tag == "details" and self._pila:
            self._pila.pop()
        elif tag == "summary":
            self._summary = None

    def handle_data(self, data):
        if self._summary is not None:
            self._summary["summary"] += data

    @property
    def details(self):
        return [datos for tipo, datos in self.eventos if tipo == "details"]

    @property
    def paneles_finales(self):
        return [datos for tipo, datos in self.eventos if tipo == "panel-final"]

    def indice(self, tipo, **filtro):
        for posicion, (clase, datos) in enumerate(self.eventos):
            if clase == tipo and all(datos.get(k) == v for k, v in filtro.items()):
                return posicion
        raise AssertionError(f"No hay {tipo} con {filtro}")

    def principal(self):
        """El único «Ver procedimiento» de nivel superior."""
        principales = [d for d in self.details if d["nivel"] == 0 and " ".join(d["summary"].split()) == "Ver procedimiento"]
        assert len(principales) == 1, principales
        return principales[0]


def texto_resultado(html):
    if 'id="resultado"' not in html:
        return ""
    return " ".join(strip_tags(html[html.index('id="resultado"'):html.index("</main>")]).split())


class PruebasComponenteDisclosure(SimpleTestCase):
    def render(self, plantilla, **contexto):
        return Template("{% load componentes %}" + plantilla).render(Context(contexto))

    def test_details_summary_nativos_cerrados_con_titulo_como_encabezado(self):
        html = self.render('{% disclosure titulo="Ver procedimiento" id="procedimiento" %}<p>cuerpo</p>{% enddisclosure %}')
        self.assertRegex(html, r'<details class="disclosure[^"]*" id="procedimiento">')
        self.assertNotIn(" open", html)
        self.assertRegex(html, r"(?s)<summary[^>]*>.*<h3[^>]*>Ver procedimiento</h3>.*</summary>")
        self.assertIn("<p>cuerpo</p>", html)
        self.assertEqual(html.count("<details"), 1)
        self.assertEqual(html.count("<summary"), 1)
        self.assertLess(html.index("</summary>"), html.index("<p>cuerpo</p>"))

    def test_nivel_clase_y_apertura_opcionales(self):
        html = self.render('{% disclosure titulo="Gauss" nivel=4 clase="disclosure-nested" abierto=True %}x{% enddisclosure %}')
        self.assertRegex(html, r'<details class="disclosure disclosure-nested" open>')
        self.assertIn("<h4", html)
        self.assertNotIn("<h3", html)
        self.assertNotIn(' id="', html)

    def test_el_titulo_se_escapa_y_el_contenido_renderizado_no_se_vuelve_a_escapar(self):
        html = self.render('{% disclosure titulo=titulo %}<code>{{ valor }}</code>{% enddisclosure %}', titulo="a < b", valor="x&y")
        self.assertIn("a &lt; b", html)
        self.assertIn("<code>x&amp;y</code>", html)
        self.assertNotIn("&lt;code&gt;", html)

    def test_no_hay_botones_dentro_del_summary_ni_detalles_abiertos_por_defecto_en_las_plantillas(self):
        for plantilla in TEMPLATES.rglob("*.html"):
            html = plantilla.read_text(encoding="utf-8")
            with self.subTest(plantilla=plantilla.relative_to(TEMPLATES).as_posix()):
                self.assertNotRegex(html, r"(?s)<summary[^>]*>(?:(?!</summary>).)*<(button|a|input)[\s>]", msg="summary con controles")
                self.assertNotRegex(html, r"<details[^>]*\sopen\s*>")


def partes(html):
    """Texto educativo y resultado separados por sus contenedores, sin mezclar extras."""
    inicio = html.index('id="procedimiento"')
    panel = html.index("panel-final")
    # El procedimiento principal puede contener otros details: contar su cierre real.
    profundidad = 1
    fin = inicio
    for marca in re.finditer(r"</?details\b[^>]*>", html[inicio:]):
        profundidad += -1 if marca.group().startswith("</") else 1
        if profundidad == 0:
            fin = inicio + marca.end()
            break
    limpiar = lambda trozo: " ".join(strip_tags(trozo).split())
    return limpiar(html[inicio:fin]), limpiar(html[panel:inicio])


def comprobar_estructura(caso, html):
    """Contrato común: un solo «Ver procedimiento» cerrado, después del único panel final, que queda fuera de él."""
    estructura = Estructura(html)
    principal = estructura.principal()
    caso.assertEqual(principal["id"], "procedimiento")
    caso.assertFalse(principal["open"], "el procedimiento debe nacer cerrado")
    caso.assertEqual(principal["encabezado"], "h3")
    caso.assertEqual(len(estructura.paneles_finales), 1, "un solo resultado canónico")
    caso.assertEqual(estructura.paneles_finales[0]["dentro"], 0, "el resultado no vive dentro del details")
    caso.assertLess(estructura.indice("panel-final"), estructura.indice("details", id="procedimiento"))
    caso.assertEqual(html.count('id="procedimiento"'), 1)
    for anidado in estructura.details:
        if "procedure-group" not in anidado["clases"]:
            caso.assertFalse(anidado["open"], anidado["summary"])
    return estructura


class PruebasSistemas(SimpleTestCase):
    def resolver(self, sistema=UNICA, metodo="gauss_jordan", mostrar=TODOS, **datos):
        datos = datos or {"sistema": sistema}
        return self.client.post("/sistemas/", {**datos, "metodo": metodo, "mostrar_definido": "1", "mostrar": mostrar}).content.decode("utf-8")

    def test_resultado_antes_del_procedimiento_cerrado_en_todos_los_casos(self):
        for metodo in ("gauss", "gauss_jordan", "comparar"):
            for sistema in (UNICA, INFINITAS, INCONSISTENTE):
                for tipo in ("texto", "matriz"):
                    with self.subTest(metodo=metodo, sistema=sistema, tipo=tipo):
                        if tipo == "texto":
                            html = self.resolver(sistema, metodo)
                        else:
                            html = self.resolver(metodo=metodo, **{k: v for k, v in datos_matriz(MATRICES[sistema]).items() if k != "metodo"})
                        comprobar_estructura(self, html)

    def test_conserva_todos_los_pasos_y_el_resultado_una_sola_vez(self):
        from frontend.web.calculadora.servicios import resolver_entrada_web

        for metodo in ("gauss", "gauss_jordan"):
            for sistema in (UNICA, INFINITAS, INCONSISTENTE):
                with self.subTest(metodo=metodo, sistema=sistema):
                    html = self.resolver(sistema, metodo)
                    esperado = resolver_entrada_web("sistema", metodo, texto=sistema)
                    procedimiento, resultado = partes(html)
                    self.assertIn("Matriz inicial", procedimiento)
                    self.assertIn(esperado["etiqueta_matriz"], procedimiento)
                    for paso in esperado["pasos"]:
                        self.assertIn(f"Paso {paso['numero']}", procedimiento)
                        self.assertIn(paso["operacion"], procedimiento)
                    for linea in esperado["sustitucion"]:
                        self.assertIn(linea, procedimiento)
                    if esperado["mostrar_sistema_resultante"]:
                        self.assertIn("Sistema resultante", procedimiento)
                        for ecuacion in esperado["ecuaciones_resultantes"]:
                            self.assertIn(ecuacion, procedimiento)
                    # El procedimiento explica cómo; la clasificación y la solución viven solo en el resultado.
                    self.assertNotIn("Clasificación", procedimiento)
                    self.assertNotIn(esperado["clasificacion"], procedimiento)
                    self.assertNotIn("Solución", procedimiento)
                    self.assertIn(f"Clasificación {esperado['clasificacion']}", resultado)
                    for linea in esperado["solucion_general"]:
                        self.assertIn(linea, resultado)
                    self.assertNotIn("Paso 1", resultado)
                    self.assertNotIn("Matriz inicial", resultado)
                    self.assertNotIn(esperado["etiqueta_matriz"], resultado)
                    todo = texto_resultado(html)
                    self.assertEqual(todo.count(esperado["clasificacion"]), 1)
                    self.assertEqual(todo.count("Columnas pivote:"), 1)
                    self.assertEqual(todo.count("Solución "), 1)

    def test_comparar_conserva_ambos_procedimientos_con_un_resultado_comun(self):
        html = self.resolver(UNICA, "comparar")
        estructura = comprobar_estructura(self, html)
        metodos = [d for d in estructura.details if d["nivel"] == 1]
        self.assertEqual([" ".join(d["summary"].split()) for d in metodos], ["Gauss", "Gauss-Jordan"])
        self.assertEqual({d["encabezado"] for d in metodos}, {"h4"})
        procedimiento, resultado = partes(html)
        self.assertEqual(procedimiento.count("Matriz inicial"), 1)
        for bloque in ("Matriz escalonada", "Sustitución regresiva", "Matriz reducida"):
            self.assertIn(bloque, procedimiento)
            self.assertNotIn(bloque, resultado)
        self.assertEqual(procedimiento.count("Operaciones por filas"), 2)
        self.assertNotIn("Consistente", procedimiento)
        self.assertEqual(resultado.count("Consistente de solución única"), 1)
        self.assertEqual(resultado.count("Solución x1 = 2 x2 = 1"), 1)
        self.assertEqual(texto_resultado(html).count("Columnas pivote:"), 1)

    def test_sin_el_bloque_procedimiento_la_matriz_final_sigue_visible_una_vez(self):
        for metodo in ("gauss", "comparar"):
            with self.subTest(metodo=metodo):
                html = self.resolver(UNICA, metodo, ["clasificacion", "pivotes", "sistema-resultante"])
                estructura = Estructura(html)
                self.assertEqual([d for d in estructura.details if "Ver procedimiento" in d["summary"]], [])
                self.assertNotIn('id="procedimiento"', html)
                self.assertEqual(len(estructura.paneles_finales), 1)
                todo = texto_resultado(html)
                self.assertEqual(todo.count("Matriz escalonada"), 1)
                self.assertNotIn("Paso 1", todo)
                self.assertNotIn("Sustitución regresiva", todo)
                self.assertLess(todo.index("Solución x1 = 2 x2 = 1"), todo.index("Matriz escalonada"))


class PruebasVectores(SimpleTestCase):
    def test_operaciones_desarrollo_plegado_y_vector_resultante_una_vez(self):
        casos = (
            (datos_vectores("suma", u=[1, 2, 3], v=[4, 5, 6]), "u + v", "(1, 2, 3) + (4, 5, 6) = (1 + 4, 2 + 5, 3 + 6) = (5, 7, 9)"),
            (datos_vectores("resta", u=[4, 6], v=[1, 2]), "u − v", "(4, 6) − (1, 2) = (4 - 1, 6 - 2) = (3, 4)"),
            (datos_vectores("escalar", escalar="3", u=[1, -2, 4]), "k·u", "3·(1, -2, 4) = (3·1, 3·(-2), 3·4) = (3, -6, 12)"),
            (datos_vectores("escalar", escalar="-1/2", u=["1/3", -4]), "k·u", "(-1/2)·(1/3, -4) = ((-1/2)·(1/3), (-1/2)·(-4)) = (-1/6, 2)"),
        )
        for datos, expresion, cadena in casos:
            with self.subTest(operacion=datos["operacion"]):
                html = self.client.post(RUTA_VECTORES, datos).content.decode("utf-8")
                comprobar_estructura(self, html)
                procedimiento, resultado = partes(html)
                # La cadena arranca en la expresión, sustituye los vectores y termina en el resultado.
                self.assertIn(f"{expresion} = {cadena}", procedimiento)
                self.assertNotIn("Vectores de entrada", procedimiento)
                vector = cadena.rsplit("= ", 1)[1]
                self.assertIn(f"Resultado {expresion} = {vector}", resultado)
                self.assertEqual(texto_resultado(html).count("Resultado"), 1)

    def test_combinacion_lineal_conserva_las_etapas_sin_duplicar_la_conclusion(self):
        casos = (
            (combinacion([[1, 2], [3, 4]], [-1, 0]), "Sí: b es combinación lineal de v1 y v2.", "c1 = 2"),
            (combinacion([[1, 2], [2, 4]], [3, 6]), "Sí: b es combinación lineal de v1 y v2.", "c1 = 3 - 2c2"),
            (combinacion([[1, 2], [2, 4]], [3, 7]), "No: b no es combinación lineal de v1 y v2.", "0 = 1"),
        )
        for datos, conclusion, linea in casos:
            with self.subTest(conclusion=conclusion):
                html = self.client.post(RUTA_VECTORES, datos).content.decode("utf-8")
                comprobar_estructura(self, html)
                procedimiento, resultado = partes(html)
                for etapa in ("1 · Planteamiento", "2 · Sistema equivalente", "columna aumentada", "3 · Gauss-Jordan", "Matriz reducida", "4 · Lectura de la matriz"):
                    self.assertIn(etapa, procedimiento)
                    self.assertNotIn(etapa, resultado)
                # La lectura explica la matriz (clasificación y justificación) pero no repite la respuesta.
                self.assertIn("El sistema es", procedimiento)
                for ausente in ("Coeficientes", "Solución general", "Sí:", "No:", "como combinación lineal"):
                    self.assertNotIn(ausente, procedimiento)
                self.assertEqual(resultado.count(conclusion), 1)
                todo = texto_resultado(html)
                self.assertEqual(todo.count(conclusion), 1)
                if linea != "0 = 1":
                    self.assertEqual(todo.count(linea), 1)
                    self.assertIn(linea, resultado)
                else:
                    self.assertIn(linea, procedimiento)


class PruebasMatrices(SimpleTestCase):
    def test_entrada_por_entrada_es_una_sola_cadena_y_el_resultado_una_matriz(self):
        casos = (
            (datos_matrices(), "A + B", "Entrada por entrada", [["6", "8"], ["10", "12"]]),
            (datos_matrices("resta"), "A − B", "Entrada por entrada", [["-4", "-4"], ["-4", "-4"]]),
            (datos_matrices("escalar", escalar="1/2"), "k·A", "Entrada por entrada", [["1/2", "1"], ["3/2", "2"]]),
            (datos_matrices("traspuesta", a=[[1, 2, 3], [4, 5, 6]]), "Aᵀ", "De filas a columnas", [["1", "4"], ["2", "5"], ["3", "6"]]),
        )
        for datos, expresion, etapa, matriz in casos:
            with self.subTest(operacion=datos["operacion"]):
                html = self.client.post(RUTA_MATRICES, datos).content.decode("utf-8")
                comprobar_estructura(self, html)
                doc = Contenido(html)
                procedimiento, resultado = partes(html)
                self.assertIn(etapa, procedimiento)
                self.assertIn("Desarrollo por entradas", doc.tablas)
                # La cadena termina en la matriz obtenida; el único bloque «Resultado» es el panel final.
                self.assertEqual(doc.tablas["Resultado del desarrollo"], matriz)
                self.assertEqual(doc.tablas["Matriz resultado"], matriz)
                self.assertEqual(html.count('<table class="matrix-table" aria-label="Matriz resultado"'), 1)
                self.assertEqual(html.count('<table class="matrix-table" aria-label="Resultado del desarrollo"'), 1)
                self.assertNotIn("Resultado", procedimiento)
                self.assertNotIn("Expresión matricial", procedimiento)
                self.assertIn(f"Resultado {expresion} =", resultado)
                self.assertEqual(texto_resultado(html).count("Resultado"), 1)

    def test_traspuesta_conserva_los_traslados_fila_a_columna(self):
        html = self.client.post(RUTA_MATRICES, datos_matrices("traspuesta", a=[[1, 2, 3], [4, 5, 6]])).content.decode("utf-8")
        procedimiento, _ = partes(html)
        self.assertIn("2×3 → 3×2", procedimiento)
        self.assertIn("Fila 2 de A → columna 2 de Aᵀ: 4, 5, 6", procedimiento)

    def test_productos_conservan_sus_metodos_sin_repetir_c_por_metodo(self):
        casos = (
            (datos_producto(), [], "Fila por columna"),
            (datos_producto(metodo="columnas"), [], "Por columnas"),
            (datos_producto(metodo="comparar"), ["Fila por columna", "Por columnas"], None),
            (datos_matriz_vector(), [], "Regla fila-vector"),
            (datos_matriz_vector(metodo="columnas"), [], "Combinación lineal de columnas"),
            (datos_matriz_vector(metodo="comparar"), ["Regla fila-vector", "Combinación lineal de columnas"], None),
        )
        for datos, anidados, titulo in casos:
            with self.subTest(operacion=datos["operacion"], metodo=datos["metodo"]):
                html = self.client.post(RUTA_MATRICES, datos).content.decode("utf-8")
                estructura = comprobar_estructura(self, html)
                metodos = [d for d in estructura.details if "disclosure-nested" in d["clases"]]
                self.assertEqual([" ".join(d["summary"].split()) for d in metodos], anidados)
                self.assertTrue(any("procedure-group" in d["clases"] for d in estructura.details), "grupos por fila o columna")
                procedimiento, resultado = partes(html)
                if titulo:
                    self.assertEqual(procedimiento.count(titulo), 1)
                self.assertNotIn("Expresión matricial", procedimiento)
                self.assertNotIn("Resultado", procedimiento)
                self.assertEqual(html.count('<table class="matrix-table" aria-label="Matriz resultado"'), 1)
                self.assertEqual(texto_resultado(html).count("Resultado"), 1)
                doc = Contenido(html)
                for tabla in ("Resultado del desarrollo", "Resultado ensamblado"):
                    if tabla in doc.tablas:
                        self.assertEqual(doc.tablas[tabla], doc.tablas["Matriz resultado"])


class PruebasEcuacionMatricial(SimpleTestCase):
    def resolver(self, a, b, metodo=None):
        datos = datos_ecuacion(a, b) if metodo is None else datos_ecuacion(a, b, metodo=metodo)
        return self.client.post(RUTA_ECUACIONES, datos).content.decode("utf-8")

    def test_procedimiento_plegado_con_equivalencias_y_eliminacion_y_un_solo_resultado(self):
        from frontend.web.calculadora.servicios_ecuaciones import resolver_ecuacion_web

        for (a, b) in (AXB_UNICA, AXB_INFINITAS, AXB_INCONSISTENTE):
            for metodo in ("gauss", "gauss_jordan", "comparar"):
                with self.subTest(b=b, metodo=metodo):
                    html = self.resolver(a, b, metodo)
                    estructura = comprobar_estructura(self, html)
                    esperado = resolver_ecuacion_web({"a": a, "b": b, "metodo": metodo})
                    procedimiento, resultado = partes(html)
                    for etapa in ("1 · Ecuación matricial", "2 · Ecuación vectorial", "3 · Sistema equivalente", "4 · Matriz aumentada"):
                        self.assertIn(etapa, procedimiento)
                        self.assertNotIn(etapa, resultado)
                    for metodo_web in esperado["metodos"]:
                        self.assertIn(metodo_web["etiqueta_matriz"], procedimiento)
                        for paso in metodo_web["pasos"]:
                            self.assertIn(paso["operacion"], procedimiento)
                    # La clasificación y la solución/contradicción viven solo en el panel final.
                    self.assertNotIn(esperado["enunciado"], procedimiento)
                    for ausente in ("Solución", "Conjunto solución", "Contradicción", "Comprobación", "Interpretación"):
                        self.assertNotIn(ausente, procedimiento)
                    self.assertEqual(resultado.count(esperado["enunciado"]), 1)
                    for linea in esperado["solucion_general"]:
                        self.assertEqual(resultado.count(linea), 1)
                    todo = texto_resultado(html)
                    self.assertEqual(todo.count(esperado["enunciado"]), 1)
                    self.assertEqual(todo.count(f"El sistema equivalente es {esperado['clasificacion'].lower()}"), 1)
                    anidados = [" ".join(d["summary"].split()) for d in estructura.details if "disclosure-nested" in d["clases"]]
                    self.assertEqual(anidados, ["Gauss", "Gauss-Jordan"] if metodo == "comparar" else [])

    def test_comprobacion_e_interpretacion_plegadas_despues_del_resultado(self):
        for (a, b), comprobable in ((AXB_UNICA, True), (AXB_INFINITAS, False), (AXB_INCONSISTENTE, False)):
            with self.subTest(b=b):
                html = self.resolver(a, b)
                estructura = comprobar_estructura(self, html)
                extras = [d for d in estructura.details if d["nivel"] == 0 and " ".join(d["summary"].split()) != "Ver procedimiento"]
                titulos = [" ".join(d["summary"].split()) for d in extras]
                self.assertEqual(titulos, ["Comprobar solución", "Interpretar Ax = b"] if comprobable else ["Interpretar Ax = b"])
                self.assertFalse(any(d["open"] for d in extras))
                panel = estructura.indice("panel-final")
                for titulo in titulos:
                    posicion = next(i for i, (tipo, d) in enumerate(estructura.eventos) if tipo == "details" and " ".join(d["summary"].split()) == titulo)
                    self.assertGreater(posicion, panel)
                texto = texto_resultado(html)
                self.assertIn("b es combinación lineal" if comprobable or b == AXB_INFINITAS[1] else "b no pertenece", texto)
                if comprobable:
                    self.assertIn("Producto Ax", Contenido(html).tablas)


class PruebasTransversales(SimpleTestCase):
    """Contratos comunes a las cuatro herramientas y lo que P18 no toca."""

    def respuestas(self):
        return (
            ("/sistemas/", {"sistema": UNICA, "metodo": "comparar", "mostrar_definido": "1", "mostrar": TODOS}),
            ("/sistemas/", {"sistema": INFINITAS, "metodo": "gauss", "mostrar_definido": "1", "mostrar": ["clasificacion", "sistema-resultante"]}),
            (RUTA_VECTORES, datos_vectores("escalar", escalar="2", u=[1, 2])),
            (RUTA_VECTORES, combinacion([[1, 2], [3, 4]], [-1, 0])),
            (RUTA_MATRICES, datos_matrices("traspuesta")),
            (RUTA_MATRICES, datos_producto(metodo="comparar")),
            (RUTA_ECUACIONES, datos_ecuacion(*AXB_UNICA)),
            (RUTA_ECUACIONES, datos_ecuacion(*AXB_INFINITAS, metodo="comparar")),
        )

    def test_ancla_y_foco_del_resultado_se_conservan(self):
        for ruta, datos in self.respuestas():
            with self.subTest(ruta=ruta):
                html = self.client.post(ruta, datos).content.decode("utf-8")
                self.assertIn(f'action="{ruta}#resultado"', html)
                self.assertRegex(html, r'<section id="resultado" class="results" aria-labelledby="results-title" tabindex="-1">')
                self.assertEqual(html.count('id="resultado"'), 1)

    def test_los_encabezados_del_resultado_no_saltan_niveles(self):
        for ruta, datos in self.respuestas():
            with self.subTest(ruta=ruta):
                html = self.client.post(ruta, datos).content.decode("utf-8")
                niveles = [d["nivel"] for tipo, d in Estructura(html).eventos if tipo == "encabezado"]
                self.assertEqual(niveles[0], 2)
                for anterior, siguiente in zip(niveles, niveles[1:]):
                    self.assertLessEqual(siguiente, anterior + 1, niveles)

    def test_sin_javascript_todo_el_contenido_esta_en_el_html(self):
        for ruta, datos in self.respuestas():
            with self.subTest(ruta=ruta):
                html = self.client.post(ruta, datos).content.decode("utf-8")
                seccion = html[html.index('id="resultado"'):html.index("</main>")]
                # Solo los controles de formato son una mejora progresiva; la matemática sigue visible.
                sin_controles = re.sub(r'<div class="numeric-format"[\s\S]*?</div>', '', seccion)
                self.assertNotIn(" hidden", sin_controles)
                self.assertIn('data-numeric-controls hidden', seccion)
                self.assertNotIn("<script", seccion)
                self.assertNotIn("<template", seccion)
                self.assertEqual(seccion.count("<details"), seccion.count("</details>"))
                self.assertEqual(seccion.count("<details"), seccion.count("<summary"))

    def test_inicio_y_conversion_de_bases_no_cambian(self):
        inicio = self.client.get("/").content.decode("utf-8")
        self.assertNotIn("disclosure-procedure", inicio)
        self.assertNotIn('id="procedimiento"', inicio)
        bases = self.client.post("/bases/conversion/", {"numero": "13", "base_origen": "10", "bases_destino": ["2", "16"]}).content.decode("utf-8")
        self.assertNotIn("disclosure-procedure", bases)
        self.assertNotIn('id="procedimiento"', bases)
        texto = texto_resultado(bases)
        # Conversión de bases conserva su presentación de P16: resultado y después el procedimiento compartido.
        self.assertLess(texto.index("Resultado Número de origen"), texto.index("Procedimiento"))
        self.assertIn("1101", texto)
        self.assertIn("D", texto)


class PruebasComparacionSinProcedimiento(SimpleTestCase):
    """Comparar ambos sin «Procedimiento»: cada matriz final nombra su método y sigue habiendo un solo resultado."""

    def resolver(self, sistema, mostrar):
        return self.client.post("/sistemas/", {"sistema": sistema, "metodo": "comparar", "mostrar_definido": "1", "mostrar": mostrar}).content.decode("utf-8")

    def test_cada_matriz_final_y_sistema_resultante_nombran_su_metodo(self):
        html = self.resolver(INFINITAS, ["clasificacion", "pivotes", "sistema-resultante"])
        texto = texto_resultado(html)
        self.assertNotIn("Ver procedimiento", texto)
        for bloque in ("Matriz escalonada · Gauss", "Sistema resultante · Gauss ", "Matriz reducida · Gauss-Jordan", "Sistema resultante · Gauss-Jordan"):
            self.assertEqual(texto.count(bloque), 1, bloque)
        self.assertLess(texto.index("Matriz escalonada · Gauss"), texto.index("Matriz reducida · Gauss-Jordan"))
        # Un único resultado canónico: clasificación y solución una sola vez, antes de las matrices.
        self.assertEqual(texto.count("Consistente de soluciones infinitas"), 1)
        self.assertEqual(texto.count("Solución "), 1)
        self.assertEqual(texto.count("x2 es libre"), 1)
        self.assertLess(texto.index("Solución "), texto.index("Matriz escalonada · Gauss"))
        self.assertEqual(len(Estructura(html).paneles_finales), 1)

    def test_con_un_solo_metodo_o_con_procedimiento_no_se_repite_el_nombre(self):
        solo = texto_resultado(self.client.post("/sistemas/", {"sistema": INFINITAS, "metodo": "gauss", "mostrar_definido": "1", "mostrar": ["sistema-resultante"]}).content.decode("utf-8"))
        self.assertIn("Matriz escalonada 1 1 2 0 0 0 Sistema resultante x1 + x2 = 2 0 = 0", solo)
        self.assertNotIn("· Gauss", solo)
        con_procedimiento = texto_resultado(self.resolver(INFINITAS, TODOS))
        # Con procedimiento, el sub-bloque «Gauss»/«Gauss-Jordan» ya nombra el método: los encabezados no lo repiten.
        self.assertNotIn("Matriz escalonada · Gauss", con_procedimiento)
        self.assertNotIn("Sistema resultante · Gauss", con_procedimiento)
