"""P26.5: catálogo canónico, marcadores históricos y equivalencia con P26.4."""

import hashlib
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()
from django.test import Client, SimpleTestCase
from django.urls import reverse
from django.test.utils import setup_test_environment, teardown_test_environment

from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms import SistemaForm
from frontend.web.calculadora.opciones_sistemas import METODOS, metodos_a_resolver
from tests.ayudas import antes_de_p2711, elemento_html
from tests.test_navegacion import Documento
from tests.test_resolver_sistema import seccion_resultado
from tests.test_web import datos_matriz

RUTA = "/matrices/reduccion/"
ANTIGUAS = (
    "/sistemas/", "/sistemas/gauss/", "/sistemas/gauss-jordan/",
    "/sistemas/clasificacion/", "/sistemas/columnas-pivote/",
)
CONSULTAS = (
    "gauss", "gauss jordan", "gauss-jordan", "reducción", "reducción por filas",
    "escalonar", "forma escalonada", "forma escalonada reducida", "matriz aumentada",
    "sistema de ecuaciones", "resolver sistema", "pivote", "variables libres", "clasificación",
)
CAPTURA = json.loads((Path(__file__).parent / "fixtures/reduccion_filas_p264.json").read_text(encoding="utf-8"))


class ContextoHTTP(SimpleTestCase):
    # unittest discover no activa la instrumentación de plantillas de Django.
    # Se acota a cada clase para no cambiar el entorno de otras pruebas.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_test_environment()
        cls.addClassCleanup(teardown_test_environment)


class PruebasCatalogoReduccion(ContextoHTTP):
    def test_unica_herramienta_canonica_y_categoria_sin_sistemas(self):
        self.assertEqual(reverse("calculadora:reduccion-filas"), RUTA)
        herramienta = catalogo.herramienta_por_id("reduccion-filas")
        self.assertEqual(herramienta.nombre, "Reducción por filas")
        self.assertEqual(herramienta.categoria, catalogo.MATRICES)
        self.assertIsNone(catalogo.herramienta_por_id("sistemas"))
        self.assertNotIn("Sistemas de ecuaciones", [c.nombre for c in catalogo.CATEGORIAS])
        self.assertNotIn("sistemas-ecuaciones", [c.id for c in catalogo.CATEGORIAS])
        self.assertNotIn("gauss", catalogo.MATRIZ_INVERSA.indice)
        self.assertEqual(SistemaForm.TIPOS_ENTRADA, (("sistema", "Sistema de ecuaciones"), ("matriz", "Matriz aumentada")))
        self.assertEqual(METODOS, (("gauss", "Gauss"), ("gauss_jordan", "Gauss-Jordan"), ("comparar", "Comparar ambos")))

    def test_inicio_menu_y_breadcrumb_en_matrices(self):
        inicio = self.client.get("/")
        html = inicio.content.decode()
        tema = elemento_html(html, html.index('id="matrices"'), "details")
        self.assertIn('href="/matrices/reduccion/"', tema)
        self.assertNotIn("sistemas-ecuaciones", Documento(inicio).ids)
        pagina = self.client.get(RUTA)
        documento = Documento(pagina)
        self.assertEqual([c for c, abierta in documento.categorias.items() if abierta], ["matrices"])
        self.assertNotIn("sistemas-ecuaciones", documento.categorias)
        self.assertEqual([a["href"] for a in documento.enlaces_en("Ruta de navegación")], ["/", "/#algebra-lineal", "/#matrices"])
        self.assertContains(pagina, '<span aria-current="page">Reducción por filas</span>', html=True)
        self.assertContains(pagina, 'action="/matrices/reduccion/#resultado"')
        for herramienta in catalogo.herramientas_disponibles():
            html = self.client.get(herramienta.ruta).content.decode()
            self.assertNotIn('href="/sistemas/', html)
            self.assertNotIn('data-categoria="sistemas-ecuaciones"', html)
            self.assertNotIn("Resolver un sistema", html)

    def test_busquedas_historicas_y_nuevas_con_y_sin_javascript(self):
        for consulta in CONSULTAS:
            with self.subTest(consulta=consulta):
                self.assertIn(catalogo.REDUCCION_FILAS, catalogo.buscar_herramientas(consulta))
                pagina = self.client.get("/", {"q": consulta})
                self.assertContains(pagina, "Reducción por filas")
                self.assertContains(pagina, 'href="/matrices/reduccion/"')
                self.assertNotContains(pagina, "Resolver un sistema")
                self.assertIn(catalogo.REDUCCION_FILAS.indice, Documento(pagina).indices)


class PruebasCompatibilidadReduccion(ContextoHTTP):
    def test_todas_las_rutas_llevan_al_destino_canonico(self):
        for antigua in ANTIGUAS:
            with self.subTest(ruta=antigua):
                pagina = self.client.get(antigua, follow=True)
                self.assertEqual(pagina.status_code, 200)
                self.assertEqual(len(pagina.redirect_chain), 1)
                self.assertEqual(urlsplit(pagina.redirect_chain[0][0]).path, RUTA)
                self.assertEqual(pagina.redirect_chain[0][1], 301)
                self.assertContains(pagina, "Reducción por filas · PyGebra")
                self.assertEqual(pagina.context["herramienta_actual"], catalogo.REDUCCION_FILAS)

    def test_conserva_todos_los_parametros_y_casillas_repetidas(self):
        for antigua in ANTIGUAS:
            for entrada in ("sistema", "matriz"):
                with self.subTest(ruta=antigua, entrada=entrada):
                    datos = datos_matriz([["1/2", 1, 3], [1, -1, 1]], "comparar")
                    datos.update(tipo_entrada=entrada, sistema="x1 - 6 = -x2; x1-x2=2", mostrar_definido="1", mostrar=["pivotes", "sistema-resultante"])
                    consulta = urlencode(datos, doseq=True)
                    respuesta = self.client.get(antigua + "?" + consulta)
                    self.assertEqual(parse_qs(urlsplit(respuesta["Location"]).query), parse_qs(consulta))
                    legado = self.client.get(antigua + "?" + consulta, follow=True)
                    directa = self.client.get(RUTA + "?" + consulta)
                    self.assertEqual(legado.context["form"].initial, directa.context["form"].initial)
                    self.assertEqual(legado.context["matrix_values"], directa.context["matrix_values"])
                    self.assertEqual(legado.context["opciones_abiertas"], directa.context["opciones_abiertas"])
                    self.assertFalse(legado.context["resultados"])

    def test_metodo_sugerido_por_ruta_solo_sin_parametro_explicito(self):
        for slug, sugerido in (("gauss", "gauss"), ("gauss-jordan", "gauss_jordan")):
            for metodo in (None, "comparar", "otro"):
                with self.subTest(slug=slug, metodo=metodo):
                    pagina = self.client.get(f"/sistemas/{slug}/", {} if metodo is None else {"metodo": metodo}, follow=True)
                    self.assertEqual(pagina.context["form"].initial["metodo"], sugerido if metodo is None else ("gauss_jordan" if metodo == "otro" else metodo))

    def test_post_conserva_cuerpo_metodo_bloques_y_errores(self):
        for antigua in ANTIGUAS:
            for datos in (
                {"tipo_entrada": "sistema", "sistema": "x1 - 6 = -x2; x1-x2=2", "metodo": "comparar", "mostrar_definido": "1", "mostrar": ["procedimiento", "pivotes"]},
                datos_matriz([["1/2", 1, 3], [1, -1, 1]], "gauss"),
                {"sistema": "x1+=1", "metodo": "gauss"},
                {"sistema": "x1=1"},
            ):
                with self.subTest(ruta=antigua, datos=datos):
                    destino = self.client.post(antigua, datos)
                    self.assertEqual(destino.status_code, 200 if antigua == "/sistemas/" else 308)
                    legado = self.client.post(antigua, datos, follow=True)
                    directa = self.client.post(RUTA, datos)
                    self.assertEqual(legado.wsgi_request.method, "POST")
                    self.assertContains(legado, 'action="/matrices/reduccion/#resultado"')
                    self.assertEqual(legado.context["herramienta_actual"], catalogo.REDUCCION_FILAS)
                    self.assertEqual(legado.wsgi_request.POST, directa.wsgi_request.POST)
                    self.assertEqual(legado.context["resultados"], directa.context["resultados"])
                    self.assertEqual(legado.context["form"].errors, directa.context["form"].errors)
                    self.assertEqual(legado.context["mostrar"], directa.context["mostrar"])
                    self.assertEqual(seccion_resultado(legado), seccion_resultado(directa))

    def test_csrf_y_rutas_desconocidas(self):
        cliente = Client(enforce_csrf_checks=True)
        for antigua in ANTIGUAS:
            self.assertEqual(cliente.post(antigua, {"sistema": "x1=1", "metodo": "gauss"}).status_code, 403)
        self.assertEqual(self.client.get("/sistemas/no-existe/").status_code, 404)


class PruebasEquivalenciaP264(ContextoHTTP):
    def test_60_salidas_http_coinciden_con_develop_previo(self):
        """Fixture capturado ANTES de editar: no se genera desde el código bajo prueba.

        Compara todos los campos: matrices, pasos, sustitución, clasificación,
        pivotes, contradicciones, libres, solución y normalización. El hash del
        texto completo de section#resultado comprueba también la presentación.
        """
        self.assertEqual(CAPTURA["base"], "1e69d3305f3c2ec519e9aac0a61407e6e780ef61")
        for caso in CAPTURA["casos"]:
            for metodo, _ in METODOS:
                for entrada in ("sistema", "matriz"):
                    with self.subTest(caso=caso["nombre"], metodo=metodo, entrada=entrada):
                        datos = {"sistema": caso["sistema"], "metodo": metodo} if entrada == "sistema" else datos_matriz(caso["matriz"], metodo)
                        respuesta = self.client.post(RUTA, datos)
                        self.assertEqual(respuesta.status_code, 200)
                        self.assertFalse(respuesta.context["form"].errors)
                        actual = json.loads(json.dumps(respuesta.context["resultados"], default=str))
                        esperados = []
                        for motor in metodos_a_resolver(metodo):
                            esperado = dict(caso["resultados"][motor])
                            if entrada == "sistema":
                                esperado["reescritas"] = caso["reescritas"]
                            esperados.append(esperado)
                        self.assertEqual(actual, esperados)
                        # Captura previa a P27.11: se deshacen solo el título del panel, la leyenda y x₁.
                        respuesta.content = antes_de_p2711(respuesta.content.decode("utf-8")).encode()
                        texto = seccion_resultado(respuesta)
                        self.assertEqual(hashlib.sha256(texto.encode()).hexdigest(), caso["texto_sha256"][metodo][entrada])
