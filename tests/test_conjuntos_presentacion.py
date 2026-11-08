"""Presentación de Conjuntos: editor vacío con ejemplos, guía, Venn automático, recta con
operandos y procedimientos marcados. Todo sale de valores y hechos del motor."""

import json
import re
from fractions import Fraction

from django.test import SimpleTestCase, override_settings

from backend.conjuntos.cardinalidades import resolver_cardinalidades
from backend.conjuntos.literales import analizar_literal
from backend.conjuntos.modelo import presentar
from backend.conjuntos.parser import analizar_expresion
from backend.conjuntos.regiones import construir_venn, detectar_venn
from frontend.web.calculadora.forms_conjuntos import EJEMPLOS, rellenar
from tests.test_conjuntos_web import RUTA, datos

CARDINALIDAD = "/conjuntos/cardinalidad/"


def contrato(respuesta):
    texto = respuesta.content.decode()
    return json.loads(re.search(r'<script id="conjuntos-resultado-datos"[^>]*>(.*?)</script>', texto, re.S)[1])


def editor(filas, expresion, **extra):
    campos = {"cantidad": str(len(filas)), "expresion": expresion, "accion": "calcular", **extra}
    for i, (nombre, contenido) in enumerate(filas):
        campos.update({f"nombre_{i}": nombre, f"contenido_{i}": contenido, f"anterior_{i}": nombre})
    return campos


TRES = [("U", "{1,2,3,4,5,6,7,8,9,10}"), ("A", "{1,2,3,4,5}"), ("B", "{4,5,6,7}"), ("C", "{2,5,7,9}")]


class MotorPresentacionTests(SimpleTestCase):
    def test_orden_de_lectura_numerico_y_por_tamano(self):
        self.assertEqual(presentar(analizar_literal("{10, 6, 7, 8, 9}")), "{6, 7, 8, 9, 10}")
        self.assertEqual(presentar(analizar_literal('{{1, 2}, "a", 2, {3}, -1/2}')), '{-1/2, 2, "a", {3}, {1, 2}}')
        # El orden es solo de escritura: la igualdad no cambia.
        self.assertEqual(analizar_literal("{2, 1}"), analizar_literal("{1, 2}"))

    def test_detectar_venn_por_nombres_y_universo(self):
        entorno = {n: analizar_literal(c) for n, c in TRES}
        casos = {
            "(A ∪ B) ∖ C": (("A", "B", "C"), None), "∁(A, U)": (("A",), "U"),
            "∁(A ∪ B, U) ∩ C": (("A", "B", "C"), "U"), "A ∩ ∅": None, "A": None,
            "A ⊆ B": None, "A ∪ {1}": None, "potencia(A)": None, "|A ∩ B|": None,
            "A ∪ B ∪ C ∪ U": None,
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(detectar_venn(analizar_expresion(texto), entorno), esperado)

    def test_venn_de_un_conjunto_con_universo(self):
        entorno = {n: analizar_literal(c) for n, c in TRES}
        regiones = construir_venn(("A",), entorno, analizar_expresion("∁(A, U)"), universo="U")
        self.assertEqual([r["seleccionada"] for r in regiones], [True, False])
        self.assertEqual(len(regiones[0]["elementos"]), 5)
        with self.assertRaises(ValueError):
            construir_venn(("A",), entorno, analizar_expresion("A"))

    def test_inclusion_exclusion_cuenta_cada_region_una_vez(self):
        r = resolver_cardinalidades(("A", "B", "C"), {m: m for m in range(1, 8)})
        paso = next(p for p in r["pasos"] if p["regla"] == "inclusion_exclusion")
        self.assertEqual(set(paso["veces"].values()), {1})
        self.assertEqual(paso["terminos"][0]["cubre"], (1, 3, 5, 7))
        with self.assertRaisesRegex(ValueError, "A ∩ Bᶜ tendría −2"):
            resolver_cardinalidades(("A", "B"), {1: 1, 2: 8, 3: 3}, modo="intersecciones")

    def test_plantillas_de_la_guia(self):
        self.assertEqual(rellenar("∁({a}, {u})", ["U", "A", "B"]), "∁(A, U)")
        self.assertEqual(rellenar("{a} ∪ {b}", ["S"]), "S ∪ {1}")
        self.assertEqual(rellenar("∁({a}, {u})", ["A", "B"]), "∁(A, A ∪ B)")
        self.assertEqual(rellenar("{x} ∈ {a}", [], "7"), "7 ∈ A")


@override_settings(ROOT_URLCONF="tests.urls_conjuntos")
class EditorPresentacionTests(SimpleTestCase):
    def test_editor_vacio_y_ejemplos_opcionales(self):
        respuesta = self.client.get(RUTA)
        self.assertContains(respuesta, 'name="cantidad" value="0"')
        self.assertContains(respuesta, "Aún no hay conjuntos")
        for clave in EJEMPLOS:
            self.assertContains(respuesta, f'href="?ejemplo={clave}"')
        respuesta = self.client.get(RUTA + "?ejemplo=venn")
        self.assertContains(respuesta, 'name="nombre_3" value="C"')
        self.assertContains(respuesta, 'value="U"')
        self.assertContains(self.client.get(RUTA + "?ejemplo=relaciones"), "A ∈ B</textarea>")
        self.assertContains(self.client.get(RUTA + "?ejemplo=eval"), "Aún no hay conjuntos")

    def test_lectura_de_cada_conjunto_y_anidados(self):
        respuesta = self.client.get(RUTA + "?ejemplo=anidados")
        self.assertContains(respuesta, "3 elementos")
        self.assertContains(respuesta, '<span class="conjuntos-chip conjuntos-math">{{1}}</span>', html=False)

    def test_venn_automatico_con_universo_del_complemento(self):
        d = contrato(self.client.post(RUTA, editor(TRES, "∁(A ∪ B, U) ∩ C")))
        self.assertEqual(d["venn"]["nombres"], ["A", "B", "C"])
        self.assertEqual(d["venn"]["universo"], "U")
        seleccionadas = [r for r in d["venn"]["regiones"] if r["seleccionada"]]
        self.assertEqual([(r["mascara"], r["etiquetas"], r["descripcion"]) for r in seleccionadas], [(4, ["9"], "Solo en C")])
        self.assertNotIn("venn", contrato(self.client.post(RUTA, editor(TRES, "A ⊆ B"))))
        # Un universo que no contiene a los conjuntos no impide el resultado: solo el diagrama.
        respuesta = self.client.post(RUTA, editor([("U", "{1}"), ("A", "{1}"), ("B", "{2}")], "∁(A, U) ∪ B"))
        self.assertContains(respuesta, "No se dibuja el diagrama")
        self.assertContains(respuesta, 'data-respuesta-relacion>{2}</p>', html=False)

    def test_procedimiento_marca_elementos(self):
        respuesta = self.client.post(RUTA, editor(TRES, "(A ∪ B) ∖ C"))
        texto = respuesta.content.decode()
        self.assertIn("Paso 2", texto)
        self.assertRegex(texto, r'data-marca="sale">2<span class="sr-only">: se descarta')
        self.assertIn('data-marca="comun"', texto)
        self.assertContains(respuesta, 'data-respuesta-relacion>{1, 3, 4, 6}</p>', html=False)
        respuesta = self.client.post(RUTA, editor(TRES, "A ⊆ B"))
        self.assertContains(respuesta, "1 está en A pero no en B. Por eso, A ⊆ B es falso.")
        self.assertContains(self.client.post(RUTA, editor(TRES, "A × C")), "conjuntos-producto")
        self.assertContains(self.client.post(RUTA, editor(TRES, "potencia(C)")), "conjuntos-tamanos")

    def test_recta_con_operandos_y_punto(self):
        filas = [("I", "intervalo(0, 5, cerrado, abierto)"), ("J", "intervalo(2, 8, abierto, cerrado)")]
        respuesta = self.client.post(RUTA, editor(filas, "I ∖ J", punto="2"))
        self.assertContains(respuesta, 'data-respuesta-relacion>[0, 2]</p>', html=False)
        recta = contrato(respuesta)["recta"]
        self.assertEqual([f["etiqueta"] for f in recta["filas"]], ["I", "J"])
        self.assertEqual([f["notacion"] for f in recta["filas"]], ["[0, 5)", "(2, 8]"])
        self.assertIs(recta["pertenece"], True)
        # Un punto mal escrito conserva el resultado y explica el error junto al campo.
        respuesta = self.client.post(RUTA, editor(filas, "I ∖ J", punto='"x"'))
        self.assertContains(respuesta, 'id="resultado"')
        self.assertContains(respuesta, "número exacto")
        self.assertIn("relacion", contrato(self.client.post(RUTA, editor(filas, "3 ∈ I")))["recta"])


@override_settings(ROOT_URLCONF="tests.urls_conjuntos")
class CardinalidadPresentacionTests(SimpleTestCase):
    def test_campos_dibujan_su_region(self):
        respuesta = self.client.get(CARDINALIDAD)
        self.assertContains(respuesta, 'data-cubre="1"')
        self.assertContains(respuesta, "Solo en A")
        respuesta = self.client.post(CARDINALIDAD, {"numero": "3", "modo": "intersecciones", "accion": "ajustar", "expresion": "A"})
        self.assertContains(respuesta, 'data-cubre="1 3 5 7"')
        self.assertContains(respuesta, "|A ∩ B ∩ C|")

    def test_resultado_explica_regiones_y_veces(self):
        campos = {"numero": "2", "modo": "regiones", "region_1": "5", "region_2": "3", "region_3": "2",
                  "universo": "12", "expresion": "A ∪ B", "accion": "calcular"}
        respuesta = self.client.post(CARDINALIDAD, campos)
        self.assertContains(respuesta, "data-cardinalidad>10</span>", html=False)
        self.assertContains(respuesta, "|A| = 5 + 2 = 7")
        self.assertContains(respuesta, "¿Cuántas veces cuenta cada región?")
        self.assertContains(respuesta, 'data-mascaras="1"')
        d = contrato(respuesta)
        self.assertEqual(d["venn"]["regiones"][0]["cantidad"], "2")
        respuesta = self.client.post(CARDINALIDAD, {**campos, "modo": "intersecciones", "region_1": "1", "region_2": "8"})
        self.assertContains(respuesta, "Datos incoherentes")
        self.assertContains(respuesta, 'role="alert"')
