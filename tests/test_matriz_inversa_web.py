"""P26.4: «Matriz inversa» en la web: catálogo, entrada, métodos, procedimiento, resultado y confirmación."""

import os
import re
from html import unescape
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.http import QueryDict
from django.test import Client, SimpleTestCase
from django.urls import resolve, reverse
from django.utils.html import strip_tags

from backend.matriz_inversa import calcular_inversa
from backend.presupuesto_computacional import Categoria, estimar_gauss_jordan, perfil_numerico
from backend.seguridad_numerica import MENSAJE_CALCULO_GRANDE
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms_inversa import InversaForm
from frontend.web.calculadora.servicios_inversa import (
    confirmacion_pendiente, estimar_inversa_web, firmar_entrada, texto_intervalo,
)
from tests.ayudas import elemento_html
from tests.test_matrices_aumentadas_web import TablasAumentadas
from tests.test_matrices_web import Contenido
from tests.test_navegacion import Documento
from tests.test_presentacion_numerica import ValoresHTML
from tests.test_procedimiento_plegable import comprobar_estructura, partes

RUTA = "/matrices/inversa/"
RAIZ = Path(__file__).resolve().parents[1]
ESTATICOS = RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora"
SERVICIO = "frontend.web.calculadora.servicios_inversa"

PROFESOR_2X2 = [[3, 4], [5, 6]]
INVERSA_2X2 = [["-3", "2"], ["5/2", "-3/2"]]
PROFESOR_3X3 = [[0, 1, 2], [1, 0, 3], [4, -3, 8]]
INVERSA_3X3 = [["-9/2", "7", "-3/2"], ["-2", "4", "-1"], ["3/2", "-2", "1/2"]]
SINGULAR = [[1, 2], [2, 4]]
TABLA_INVERSA = "Matriz inversa de A"


def datos_inversa(a=None, metodo="gauss_jordan", **extra):
    """POST de la herramienta: el tamaño, el método y una celda por entrada de A."""
    a = PROFESOR_2X2 if a is None else a
    datos = {"orden": str(len(a))}
    if metodo is not None:
        datos["metodo"] = metodo
    for i, fila in enumerate(a):
        for j, valor in enumerate(fila):
            datos[f"celda_A_{i}_{j}"] = str(valor)
    return datos | extra


def texto(html, desde='id="resultado"'):
    if desde not in html:
        return ""
    return " ".join(unescape(strip_tags(re.sub(r">\s*<", "> <", html[html.index(desde):html.index("</main>")]))).split())


def radios(html):
    return {valor: atributos for valor, atributos in re.findall(r'<input type="radio" name="metodo" value="([^"]+)"([^>]*)>', html)}


def forzar(nivel=Categoria.PESADA, intervalo=(2.0, 18.0)):
    """Fuerza la categoría y el intervalo sin matrices enormes ni segundos reales."""
    return (patch(f"{SERVICIO}.categoria", return_value=nivel), patch(f"{SERVICIO}.intervalo_segundos", return_value=intervalo))


class PruebasCatalogo(SimpleTestCase):
    def test_cuarta_herramienta_de_matrices_con_ruta_propia(self):
        herramienta = catalogo.MATRIZ_INVERSA
        self.assertEqual(
            catalogo.herramientas_de(catalogo.MATRICES),
            (catalogo.OPERACIONES_MATRICES, catalogo.EXPRESIONES_MATRICIALES, catalogo.ECUACIONES_MATRICIALES, herramienta),
        )
        self.assertEqual((herramienta.id, herramienta.nombre), ("matriz-inversa", "Matriz inversa"))
        self.assertTrue(herramienta.disponible)
        self.assertEqual(reverse("calculadora:matriz-inversa"), RUTA)
        self.assertEqual(catalogo.herramienta_por_ruta(resolve(RUTA)), herramienta)
        # La última del registro sigue siendo una herramienta no disponible.
        self.assertFalse(catalogo.HERRAMIENTAS[-1].disponible)

    def test_descripcion_en_lenguaje_natural_sin_formulas(self):
        herramienta = catalogo.MATRIZ_INVERSA
        self.assertEqual(herramienta.descripcion, "Calcula la inversa de una matriz cuadrada y muestra el procedimiento paso a paso.")
        visibles = f"{herramienta.nombre} {herramienta.descripcion} {herramienta.invitacion}"
        for formula in ("ad − bc", "ad-bc", "1/(", "⁻¹", "[A | I]", "determinante"):
            self.assertNotIn(formula, visibles)
        self.assertIn("la matriz inversa", catalogo.MATRICES.descripcion)

    def test_inicio_sidebar_tema_y_breadcrumbs(self):
        inicio = Documento(self.client.get("/"))
        self.assertIn(RUTA, [a["href"] for a in inicio.enlaces_en("Herramientas")])
        self.assertIn(RUTA, [a["href"] for _, a in inicio.enlaces if a.get("class") == "tool-link"])
        respuesta = self.client.get(RUTA)
        doc = Documento(respuesta)
        self.assertEqual([a["href"] for a in doc.enlaces_en("Ruta de navegación")], ["/", "/#algebra-lineal", "/#matrices"])
        self.assertContains(respuesta, '<span aria-current="page">Matriz inversa</span>', html=True)
        self.assertEqual([a["href"] for a in doc.enlaces_en("Herramientas") if a.get("aria-current") == "page"], [RUTA])
        self.assertTrue(doc.categorias["matrices"])
        enlaces = [a["href"] for a in doc.enlaces_en("Herramientas") if a["href"].startswith("/matrices/")]
        self.assertEqual(enlaces, ["/matrices/operaciones/", "/matrices/expresiones/", "/matrices/ecuaciones/", RUTA])

    def test_buscador_encuentra_la_inversa_sin_quitar_prioridades(self):
        for consulta in ("inversa", "matriz inversa", "Inversa de una matriz", "invertible", "no invertible",
                         "matriz singular", "identidad", "A^-1", "A⁻¹", "2x2", "matriz cuadrada"):
            with self.subTest(consulta=consulta):
                self.assertIn(catalogo.MATRIZ_INVERSA, catalogo.buscar_herramientas(consulta))
                self.assertContains(self.client.get("/", {"q": consulta}), f'href="{RUTA}"')
        self.assertEqual(catalogo.buscar_herramientas("inversa"), (catalogo.MATRIZ_INVERSA,))
        # Gauss, pivotes y sistemas siguen llevando solo a Resolver un sistema.
        for consulta in ("gauss", "gauss jordan", "pivote", "escalonada", "binario", "resolver", "vector"):
            self.assertNotIn(catalogo.MATRIZ_INVERSA, catalogo.buscar_herramientas(consulta))


class PruebasEntrada(SimpleTestCase):
    def test_get_con_gauss_jordan_predeterminado(self):
        respuesta = self.client.get(RUTA)
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode()
        doc = Contenido(html)
        self.assertEqual(set(doc.tablas), {"Matriz A"})
        self.assertEqual(sorted(k for k in doc.campos if k.startswith("celda_")), ["celda_A_0_0", "celda_A_0_1", "celda_A_1_0", "celda_A_1_1"])
        metodos = radios(html)
        self.assertEqual(list(metodos), ["gauss_jordan", "directo_2x2"])
        self.assertIn("checked", metodos["gauss_jordan"])
        self.assertNotIn("disabled", metodos["directo_2x2"])
        self.assertContains(respuesta, "A es 2×2. De 1 a 10 filas y columnas.")
        self.assertContains(respuesta, 'name="ajustar"')
        for ausente in ('id="resultado"', "data-confirmacion", 'role="alert"', "data-numeric-controls"):
            self.assertNotContains(respuesta, ausente)

    def test_los_controles_no_muestran_formulas(self):
        html = self.client.get(RUTA).content.decode()
        formulario = elemento_html(html, html.index('id="inversa-form"'), "form")
        etiquetas = re.findall(r'<input type="radio"[^>]*>\s*<span>([^<]+)</span>', formulario)
        self.assertEqual(etiquetas, ["Gauss-Jordan", "Método para matrices 2×2"])
        for formula in ("ad − bc", "ad-bc", "1/(", "A⁻¹", "[A | I]", "determinante"):
            self.assertNotIn(formula, strip_tags(formulario))

    def test_el_metodo_2x2_solo_esta_disponible_en_2x2(self):
        for orden in (1, 3, 10):
            with self.subTest(orden=orden):
                # Aunque llegue el método 2×2, al cambiar de tamaño se vuelve a Gauss-Jordan.
                html = self.client.post(RUTA, {"orden": str(orden), "metodo": "directo_2x2", "ajustar": "1"}).content.decode()
                metodos = radios(html)
                self.assertIn("disabled", metodos["directo_2x2"])
                self.assertNotIn("checked", metodos["directo_2x2"])
                self.assertIn("checked", metodos["gauss_jordan"])
                self.assertEqual(len([k for k in Contenido(html).campos if k.startswith("celda_A_")]), orden * orden)
                self.assertIn(f"A es {orden}×{orden}.", html)
        html = self.client.post(RUTA, {"orden": "2", "metodo": "directo_2x2", "ajustar": "1"}).content.decode()
        self.assertIn("checked", radios(html)["directo_2x2"])
        self.assertNotIn("disabled", radios(html)["directo_2x2"])

    def test_aplicar_conserva_las_celdas_que_siguen(self):
        datos = datos_inversa(PROFESOR_2X2, celda_A_0_0="1/", orden="3", ajustar="1")
        respuesta = self.client.post(RUTA, datos)
        self.assertNotContains(respuesta, 'role="alert"')
        campos = Contenido(respuesta.content.decode()).campos
        self.assertEqual(campos["celda_A_0_0"]["value"], "1/")
        self.assertEqual(campos["celda_A_1_1"]["value"], "6")
        self.assertEqual(campos["celda_A_2_2"].get("value", ""), "")

    def test_tamanos_fuera_del_limite(self):
        for valor in ("", "0", "-1", "1.5", "abc", "11", "99999999999999999"):
            with self.subTest(valor=valor):
                respuesta = self.client.post(RUTA, datos_inversa(orden=valor))
                self.assertContains(respuesta, 'role="alert"')
                self.assertNotContains(respuesta, 'id="resultado"')
        self.assertContains(self.client.post(RUTA, datos_inversa(orden="11")), "La interfaz admite hasta 10 filas y columnas.")

    def test_formulario_entrega_a_exacta_y_el_metodo(self):
        form = InversaForm(datos_inversa([["1/2", "-3"], ["0.25", 7]], metodo="directo_2x2"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["entrada"]["metodo"], "directo_2x2")
        self.assertEqual([[str(v) for v in fila] for fila in form.cleaned_data["entrada"]["a"]], [["1/2", "-3"], ["1/4", "7"]])

    def test_labels_y_teclado_numerico(self):
        html = self.client.post(RUTA, {"orden": "3", "metodo": "gauss_jordan", "ajustar": "1"}).content.decode()
        doc = Contenido(html)
        for nombre, atributos in doc.campos.items():
            if nombre.startswith("celda_") or nombre == "orden":
                self.assertTrue(doc.labels.get(atributos["id"]), nombre)
        self.assertEqual(doc.labels[doc.campos["celda_A_2_1"]["id"]], "Matriz A, fila 3, columna 2")
        self.assertEqual(doc.labels[doc.campos["orden"]["id"]], "Filas y columnas")
        self.assertIn("<legend>Método</legend>", html)
        self.assertIn('id="inverse-fields" data-perfil="numerico"', html)
        self.assertIn('aria-label="Tamaño de A"', html)


class PruebasResultado(SimpleTestCase):
    def calcular(self, a, metodo="gauss_jordan"):
        respuesta = self.client.post(RUTA, datos_inversa(a, metodo))
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode()
        self.assertNotIn('role="alert"', html)
        self.assertNotIn("data-confirmacion", html)
        return html, Contenido(html), texto(html)

    def test_profesor_2x2_con_ambos_metodos(self):
        for metodo, titulo in (("gauss_jordan", "Gauss-Jordan"), ("directo_2x2", "Método para matrices 2×2")):
            with self.subTest(metodo=metodo):
                html, doc, contenido = self.calcular(PROFESOR_2X2, metodo)
                self.assertEqual(doc.tablas[TABLA_INVERSA], INVERSA_2X2)
                self.assertIn(f"Matriz inversa · {titulo} Inversa de A (2×2)", contenido)
                _, resultado = partes(html)
                self.assertEqual(resultado, "Resultado A⁻¹ = -3 2 5/2 -3/2")

    def test_profesor_3x3_por_gauss_jordan(self):
        html, doc, contenido = self.calcular(PROFESOR_3X3)
        self.assertEqual(doc.tablas[TABLA_INVERSA], INVERSA_3X3)
        self.assertIn("Paso 1 F1 <-> F2", contenido)
        self.assertEqual(doc.tablas["Matriz final"], [["1", "0", "0", *INVERSA_3X3[0]], ["0", "1", "0", *INVERSA_3X3[1]], ["0", "0", "1", *INVERSA_3X3[2]]])
        self.assertIn("El bloque derecho B es la inversa de A.", contenido)

    def test_uno_por_uno_sin_metodo_2x2(self):
        html, doc, _ = self.calcular([[4]])
        self.assertEqual(doc.tablas[TABLA_INVERSA], [["1/4"]])
        self.assertIn("disabled", radios(html)["directo_2x2"])

    def test_singular_con_ambos_metodos(self):
        casos = (
            ("gauss_jordan", "Con Gauss-Jordan, el lado izquierdo no pudo convertirse en la matriz identidad: A es una matriz no invertible."),
            ("directo_2x2", "Como ad − bc = 0, A es una matriz no invertible."),
        )
        for metodo, explicacion in casos:
            with self.subTest(metodo=metodo):
                html, doc, _ = self.calcular(SINGULAR, metodo)
                procedimiento, resultado = partes(html)
                self.assertEqual(resultado, f"Resultado La matriz no tiene inversa. {explicacion}")
                self.assertNotIn(TABLA_INVERSA, doc.tablas)
                self.assertNotIn("A⁻¹ =", resultado)
                self.assertNotIn("no tiene inversa", procedimiento)
                for tecnico in ("singular", "rango", "rank", "pivot", "determinant", "Exception"):
                    self.assertNotIn(tecnico, resultado)
        _, _, contenido = self.calcular(SINGULAR)
        self.assertIn("La fila 2 del lado izquierdo quedó con solo ceros", contenido)
        _, _, contenido = self.calcular(SINGULAR, "directo_2x2")
        self.assertIn("ad − bc = 1·4 − 2·2 = 4 − 4 = 0", contenido)
        self.assertNotIn("Intercambiar a y d", contenido)
        # Dos filas sin pivote se nombran juntas.
        _, _, contenido = self.calcular([[1, 1, 1], [2, 2, 2], [3, 3, 3]])
        self.assertIn("Las filas 2 y 3 del lado izquierdo quedaron con solo ceros", contenido)

    def test_procedimiento_2x2_ensena_la_regla_paso_a_paso(self):
        html, doc, contenido = self.calcular(PROFESOR_2X2, "directo_2x2")
        procedimiento, _ = partes(html)
        orden = (
            "1 · La regla para matrices 2×2", "a = 3, b = 4, c = 5 y d = 6", "A⁻¹ = 1/(ad − bc) ·",
            "2 · Calcular ad − bc", "ad − bc = 3·6 − 4·5 = 18 − 20 = -2", "Como -2 no es 0",
            "3 · Intercambiar a y d; cambiar el signo de b y c",
            "4 · Multiplicar por 1/(ad − bc)", "1/(ad − bc) = 1/(-2) = -1/2",
        )
        posiciones = [procedimiento.index(fragmento) for fragmento in orden]
        self.assertEqual(posiciones, sorted(posiciones))
        self.assertEqual(doc.tablas["A con letras"], [["a", "b"], ["c", "d"]])
        self.assertEqual(doc.tablas["d, −b, −c y a"], [["d", "−b"], ["−c", "a"]])
        self.assertEqual(doc.tablas["Matriz con a y d intercambiados"], [["6", "-4"], ["-5", "3"]])
        self.assertEqual(doc.tablas["Desarrollo por entradas"], [["(-1/2)·6", "(-1/2)·(-4)"], ["(-1/2)·(-5)", "(-1/2)·3"]])
        self.assertEqual(doc.tablas["Matriz obtenida"], INVERSA_2X2)
        # Negativos y fracciones van entre paréntesis en los productos.
        _, _, contenido = self.calcular([["1/2", -1], [3, "-2/3"]], "directo_2x2")
        self.assertIn("ad − bc = (1/2)·(-2/3) − (-1)·3 = -1/3 − (-3) = 8/3", contenido)

    def test_procedimiento_gauss_jordan_no_habla_de_sistemas(self):
        html, _, _ = self.calcular(PROFESOR_3X3)
        procedimiento, resultado = partes(html)
        for etapa in ("1 · Colocar la identidad junto a A", "2 · Operaciones por filas", "3 · Matriz final"):
            self.assertIn(etapa, procedimiento)
            self.assertNotIn(etapa, resultado)
        self.assertIn("[A | I]", procedimiento)
        for ajeno in ("sistema", "Sistema", "ecuaci", "clasificaci", "Clasificaci", "[A | b]", "Sustitución", "Columnas pivote"):
            self.assertNotIn(ajeno, texto(html))

    def test_el_separador_se_conserva_en_todas_las_matrices_del_procedimiento(self):
        for a in (PROFESOR_2X2, PROFESOR_3X3, SINGULAR, [[4]]):
            with self.subTest(a=a):
                html, _, _ = self.calcular(a)
                n = len(a)
                procedimiento = elemento_html(html, html.index('id="procedimiento"'), "details")
                tablas = TablasAumentadas(procedimiento).tablas
                pasos = len(re.findall(r'class="step"', procedimiento))
                # [A | I], antes y después de cada paso y la matriz final.
                self.assertEqual(len(tablas), 2 * pasos + 2)
                self.assertEqual(tablas[0]["etiqueta"], "Matriz A junto a la identidad")
                self.assertEqual(tablas[-1]["etiqueta"], "Matriz final")
                for tabla in tablas:
                    for fila in tabla["filas"]:
                        self.assertEqual(len(fila), 2 * n)
                        self.assertEqual([i for i, celda in enumerate(fila) if "constant" in celda["clases"]], [n])
                        self.assertEqual([i for i, celda in enumerate(fila) if "augmented" in celda["clases"]], list(range(n + 1, 2 * n)))
                # El resultado es una matriz sin separador.
                resultado = TablasAumentadas(elemento_html(html, html.index("panel-final"), "section")).tablas
                if resultado:
                    self.assertTrue(all(celda["clases"] == [] for fila in resultado[0]["filas"] for celda in fila))

    def test_procedimiento_plegado_y_resultado_al_final(self):
        for a, metodo in ((PROFESOR_2X2, "gauss_jordan"), (PROFESOR_2X2, "directo_2x2"), (PROFESOR_3X3, "gauss_jordan"),
                          (SINGULAR, "gauss_jordan"), (SINGULAR, "directo_2x2"), ([[4]], "gauss_jordan")):
            with self.subTest(a=a, metodo=metodo):
                html, _, contenido = self.calcular(a, metodo)
                comprobar_estructura(self, html)
                procedimiento, _ = partes(html)
                self.assertNotIn("Resultado", procedimiento)
                self.assertEqual(contenido.count("Resultado"), 1)
                self.assertLess(contenido.index("Ver procedimiento"), contenido.index("Resultado"))
                ids = re.findall(r'id="([^"]+)"', html)
                self.assertEqual(len(ids), len(set(ids)))

    def test_exacto_y_decimal_sin_recalcular(self):
        html, _, _ = self.calcular(PROFESOR_3X3)
        self.assertIn("data-numeric-controls hidden", html)
        self.assertIn("/static/calculadora/numeros.js", html)
        valores = {valor["exacto"]: valor for valor in ValoresHTML(html).valores}
        for exacto, decimal in (("-9/2", "-4.5"), ("-3/2", "-1.5"), ("3/2", "1.5"), ("1/2", "0.5")):
            self.assertEqual(valores[exacto]["decimales"]["4"], decimal)
            self.assertEqual(valores[exacto]["aproximados"], [])
        html, _, _ = self.calcular([[3]])
        valor = next(v for v in ValoresHTML(html).valores if v["exacto"] == "1/3")
        self.assertEqual(valor["decimales"], {"2": "0.33", "4": "0.3333", "6": "0.333333", "8": "0.33333333"})
        html, _, _ = self.calcular(PROFESOR_2X2, "directo_2x2")
        textos = {valor["exacto"]: valor["decimales"]["4"] for valor in ValoresHTML(html).valores}
        self.assertEqual(textos["1/(ad − bc) = 1/(-2) = -1/2"], "1/(ad − bc) = 1/(-2) = -0.5")

    def test_error_del_backend_llega_legible(self):
        with patch("frontend.web.calculadora.views.calcular_inversa_web", side_effect=ValueError("Mensaje legible.")):
            respuesta = self.client.post(RUTA, datos_inversa())
        self.assertContains(respuesta, "Mensaje legible.")
        self.assertNotContains(respuesta, 'id="resultado"')


class PruebasRechazo(SimpleTestCase):
    def rechazar(self, datos, mensaje=None):
        with patch("frontend.web.calculadora.views.calcular_inversa_web", side_effect=AssertionError("calculó")):
            respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'role="alert"')
        self.assertNotContains(respuesta, 'id="resultado"')
        if mensaje:
            self.assertContains(respuesta, mensaje)
        return respuesta

    def test_metodo_2x2_manipulado_en_otra_dimension(self):
        for a in ([[4]], PROFESOR_3X3):
            with self.subTest(n=len(a)):
                self.rechazar(datos_inversa(a, "directo_2x2"), "El método para matrices 2×2 solo se puede usar cuando A es 2×2.")

    def test_metodo_ausente_o_invalido(self):
        self.rechazar(datos_inversa(metodo=None), "Selecciona un método.")
        for metodo in ("", "gauss", "determinante", "comparar", "<script>alert(1)</script>"):
            respuesta = self.rechazar(datos_inversa(metodo=metodo), "Selecciona un método")
            self.assertNotContains(respuesta, "<script>alert(1)</script>")

    def test_celdas_de_mas_de_menos_o_ajenas(self):
        faltante = datos_inversa()
        del faltante["celda_A_1_1"]
        self.rechazar(faltante, "Las celdas recibidas no coinciden con el tamaño de A")
        for nombre in ("celda_A_2_0", "celda_A_0_2", "celda_B_0_0", "celda_b_0_0", "columnas", "filas", "operacion", "escalar"):
            with self.subTest(nombre=nombre):
                self.rechazar(datos_inversa(**{nombre: "1"}), "Las celdas recibidas no coinciden con el tamaño de A")
        self.rechazar(datos_inversa(PROFESOR_3X3, orden="2"), "Las celdas recibidas no coinciden")

    def test_campos_repetidos(self):
        for campo in ("orden", "metodo", "celda_A_0_0", "confirmacion"):
            datos = QueryDict(mutable=True)
            datos.update(datos_inversa(confirmacion="x"))
            datos.appendlist(campo, datos[campo])
            form = InversaForm(datos)
            self.assertFalse(form.is_valid())
            self.assertIn("campos repetidos", str(form.non_field_errors()))

    def test_celdas_vacias_o_invalidas(self):
        self.rechazar(datos_inversa(celda_A_0_0=""), "Completa matriz a, fila 1, columna 1.")
        for valor in ("abc", "1/0", "1/", "NaN", "--2", "1,5"):
            with self.subTest(valor=valor):
                self.rechazar(datos_inversa(celda_A_1_0=valor), "no es un número válido")

    def test_html_escapado_csrf_y_metodos_http(self):
        ataque = '<img src=x onerror="alert(1)">'
        for datos in (datos_inversa(celda_A_0_0=ataque), datos_inversa(celda_A_0_0=ataque, ajustar="1")):
            respuesta = self.client.post(RUTA, datos)
            self.assertNotContains(respuesta, ataque)
            self.assertContains(respuesta, "&lt;img")
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(RUTA, datos_inversa()).status_code, 403)
        cliente.get(RUTA)
        token = cliente.cookies["csrftoken"].value
        self.assertContains(cliente.post(RUTA, datos_inversa(csrfmiddlewaretoken=token)), 'id="resultado"')
        self.assertEqual(self.client.put(RUTA).status_code, 405)

    def test_crecimiento_de_fracciones_admitidas_da_error_controlado(self):
        from tests.test_seguridad_numerica import matriz_de_crecimiento

        respuesta = self.client.post(RUTA, datos_inversa([fila[:6] for fila in matriz_de_crecimiento()]))
        self.assertContains(respuesta, MENSAJE_CALCULO_GRANDE)
        for fragmento in ('id="resultado"', "Traceback", "Exceeds the limit", "bits"):
            self.assertNotContains(respuesta, fragmento)


class PruebasConfirmacion(SimpleTestCase):
    def post(self, datos, nivel=Categoria.PESADA, intervalo=(2.0, 18.0)):
        categoria, segundos = forzar(nivel, intervalo)
        with categoria, segundos:
            respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.content.decode()

    def firma_de(self, html):
        return re.search(r'name="confirmacion" value="([0-9a-f]+)"', html).group(1)

    def test_pesada_no_calcula_y_pregunta_sin_parecer_un_error(self):
        with patch(f"{SERVICIO}.calcular_inversa", side_effect=AssertionError("calculó antes de confirmar")):
            html = self.post(datos_inversa(PROFESOR_3X3))
        self.assertNotIn('id="resultado"', html)
        self.assertNotIn('role="alert"', html)
        self.assertNotIn("alert error", html)
        tarjeta = elemento_html(html, html.index("data-confirmacion"), "section")
        leido = " ".join(strip_tags(tarjeta).split())
        self.assertEqual(
            leido,
            "Antes de calcular La matriz es válida. Esta operación puede tardar varios segundos porque la matriz "
            "requiere un procedimiento largo. Tiempo estimado: entre 2 y 18 segundos. ¿Quieres continuar? Cancelar Continuar",
        )
        for tecnico in ("O(", "bits", "operaciones", "celdas", "presupuesto", "categoría", "PESADA"):
            self.assertNotIn(tecnico, leido)
        self.assertRegex(tarjeta, r'<button class="btn btn-secondary" type="submit" name="ajustar" value="1" formnovalidate>Cancelar</button>')
        self.assertRegex(tarjeta, r'<button class="btn btn-primary" type="submit" name="confirmacion" value="[0-9a-f]{64}">Continuar</button>')

    def test_la_confirmacion_conserva_matriz_y_metodo_dentro_del_formulario(self):
        html = self.post(datos_inversa(PROFESOR_3X3))
        formulario = elemento_html(html, html.index('id="inversa-form"'), "form")
        self.assertIn("data-confirmacion", formulario)
        self.assertLess(formulario.index("data-confirmacion"), formulario.index('data-inverse-entry'))
        campos = Contenido(html).campos
        self.assertEqual({k: campos[k]["value"] for k in campos if k.startswith("celda_A_")},
                         {f"celda_A_{i}_{j}": str(v) for i, fila in enumerate(PROFESOR_3X3) for j, v in enumerate(fila)})
        self.assertIn("checked", radios(html)["gauss_jordan"])

    def test_continuar_calcula_sin_volver_a_preguntar(self):
        firma = self.firma_de(self.post(datos_inversa(PROFESOR_3X3)))
        html = self.post(datos_inversa(PROFESOR_3X3, confirmacion=firma))
        self.assertNotIn("data-confirmacion", html)
        self.assertEqual(Contenido(html).tablas[TABLA_INVERSA], INVERSA_3X3)
        comprobar_estructura(self, html)

    def test_cancelar_redibuja_sin_calcular(self):
        with patch(f"{SERVICIO}.calcular_inversa", side_effect=AssertionError("calculó")):
            html = self.post(datos_inversa(PROFESOR_3X3, ajustar="1"))
        for ausente in ('id="resultado"', "data-confirmacion", 'role="alert"'):
            self.assertNotIn(ausente, html)
        self.assertEqual(Contenido(html).campos["celda_A_2_1"]["value"], "-3")

    def test_una_confirmacion_no_sirve_para_otra_matriz(self):
        firma = self.firma_de(self.post(datos_inversa(PROFESOR_3X3)))
        otra = [[0, 1, 2], [1, 0, 3], [4, -3, 9]]
        with patch(f"{SERVICIO}.calcular_inversa", side_effect=AssertionError("calculó con una firma ajena")):
            for datos in (datos_inversa(otra, confirmacion=firma), datos_inversa(PROFESOR_3X3, confirmacion="0" * 64),
                          datos_inversa(PROFESOR_3X3, confirmacion="basura"), datos_inversa(PROFESOR_3X3, confirmacion="")):
                html = self.post(datos)
                self.assertIn("data-confirmacion", html)
                self.assertNotIn('id="resultado"', html)
        self.assertNotEqual(self.firma_de(self.post(datos_inversa(otra))), firma)
        # La misma matriz escrita de otra forma sigue siendo la misma entrada.
        mismo = datos_inversa([["0", "2/2", "4/2"], ["1", "0", "3.0"], ["4", "-3", "8"]], confirmacion=firma)
        self.assertNotIn("data-confirmacion", self.post(mismo))

    def test_la_firma_liga_matriz_y_metodo(self):
        entrada = {"a": PROFESOR_2X2, "metodo": "gauss_jordan"}
        self.assertEqual(firmar_entrada(entrada), firmar_entrada(dict(entrada)))
        self.assertNotEqual(firmar_entrada(entrada), firmar_entrada({**entrada, "metodo": "directo_2x2"}))
        self.assertNotEqual(firmar_entrada(entrada), firmar_entrada({**entrada, "a": [[3, 4], [5, 7]]}))
        # Sin categoría pesada no hace falta firma.
        self.assertIsNone(confirmacion_pendiente(entrada))

    def test_muy_pesada_y_minutos(self):
        html = self.post(datos_inversa(PROFESOR_3X3), Categoria.MUY_PESADA, (12.8, 115.6))
        self.assertIn("Esta operación puede tardar bastante porque la matriz requiere un procedimiento muy largo.", html)
        self.assertIn("Tiempo estimado: entre 13 segundos y 2 minutos.", html)

    def test_normal_perceptible_y_regla_2x2_no_preguntan(self):
        for nivel in (Categoria.NORMAL, Categoria.PERCEPTIBLE):
            with self.subTest(nivel=nivel):
                html = self.post(datos_inversa(PROFESOR_3X3), nivel)
                self.assertNotIn("data-confirmacion", html)
                self.assertIn('id="resultado"', html)
        with patch(f"{SERVICIO}.estimar_gauss_jordan", side_effect=AssertionError("estimó la regla 2×2")):
            html = self.post(datos_inversa(PROFESOR_2X2, "directo_2x2"), Categoria.MUY_PESADA)
        self.assertNotIn("data-confirmacion", html)
        self.assertEqual(Contenido(html).tablas[TABLA_INVERSA], INVERSA_2X2)

    def test_estima_gauss_jordan_sobre_a_barra_i_antes_de_ejecutar(self):
        entrada = {"a": PROFESOR_3X3, "metodo": "gauss_jordan"}
        with patch(f"{SERVICIO}.estimar_gauss_jordan", wraps=estimar_gauss_jordan) as estimar:
            estimacion = estimar_inversa_web(entrada)
        estimar.assert_called_once_with(3, 6, columnas_pivote=3, perfil=perfil_numerico(PROFESOR_3X3))
        self.assertEqual(estimacion, estimar_gauss_jordan(3, 6, columnas_pivote=3, perfil=perfil_numerico(PROFESOR_3X3)))
        self.assertIsNone(estimar_inversa_web({"a": PROFESOR_2X2, "metodo": "directo_2x2"}))
        # El orden importa: se estima (y se pregunta, si hace falta) antes de cualquier cálculo.
        orden = Mock()
        with patch(f"{SERVICIO}.estimar_gauss_jordan", wraps=estimar_gauss_jordan) as estimar, \
                patch(f"{SERVICIO}.calcular_inversa", wraps=calcular_inversa) as calcular:
            orden.attach_mock(estimar, "estimar")
            orden.attach_mock(calcular, "calcular")
            self.client.post(RUTA, datos_inversa(PROFESOR_3X3))
        self.assertEqual([llamada[0] for llamada in orden.mock_calls], ["estimar", "calcular"])

    def test_texto_del_intervalo(self):
        for bajo, alto, esperado in ((1.2, 10.9, "entre 1 y 11 segundos"), (0.2, 1.8, "entre 1 y 2 segundos"),
                                     (12.8, 115.6, "entre 13 segundos y 2 minutos"), (100, 900, "entre 2 y 15 minutos"),
                                     (0.4, 60.5, "entre 1 y 60 segundos")):
            self.assertEqual(texto_intervalo(bajo, alto), esperado)


class PruebasRecursos(SimpleTestCase):
    def test_recursos_locales_teclado_y_scripts(self):
        respuesta = self.client.get(RUTA)
        for recurso in ("inversa.js", "teclado.js", "numeros.js", "tema.js", "styles.css"):
            self.assertContains(respuesta, f"/static/calculadora/{recurso}")
        for ajeno in ("matrices.js", "ecuaciones.js", "matriz.js", 'src="https://', 'href="https://'):
            self.assertNotContains(respuesta, ajeno)
        html = respuesta.content.decode()
        for plantilla in ("matrix-entry-template", "matrix-cell-template"):
            self.assertIn(f'<template id="{plantilla}">', html)
        for marca in ("data-inversa", "data-inverse-entry", "data-inverse-shape", "data-aplicar", 'data-dimension="orden"'):
            self.assertIn(marca, html)
        js = (ESTATICOS / "inversa.js").read_text(encoding="utf-8")
        for fragmento in ("data-inversa", "matrix-entry-template", 'value="directo_2x2"', "data-confirmacion", "#resultado", "ArrowDown", "disabled"):
            self.assertIn(fragmento, js)
        self.assertNotIn("innerHTML", js)
        from tests.test_teclado import Pagina
        self.assertEqual(set(Pagina(html).perfiles_publicados), {"numerico"})

    def test_pyinstaller_incluye_los_modulos_de_p26_4(self):
        spec = (RAIZ / "AlgebraLineal.spec").read_text(encoding="utf-8")
        for modulo in ("backend.matriz_inversa", "frontend.web.calculadora.forms_inversa", "frontend.web.calculadora.servicios_inversa"):
            self.assertIn(f'"{modulo}"', spec)

    def test_el_aviso_usa_tonos_neutros_y_no_los_de_error(self):
        css = (ESTATICOS / "styles" / "components.css").read_text(encoding="utf-8")
        bloque = css[css.index(".confirmation {"):css.index("}", css.index(".confirmation {"))]
        self.assertIn("var(--color-brand)", bloque)
        self.assertNotIn("danger", bloque)
