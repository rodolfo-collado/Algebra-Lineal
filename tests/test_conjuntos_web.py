"""Editor, catálogo y relaciones comparten el contrato del backend."""

import json
import os
import re
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from frontend.web.calculadora import catalogo
from backend.conjuntos.evaluador import evaluar_expresion

RUTA = "/conjuntos/relaciones/"


def datos(**extra):
    return {"cantidad": "2", "nombre_0": "A", "contenido_0": "{1,2}", "anterior_0": "A",
            "nombre_1": "B", "contenido_1": "{2,{1,2}}", "anterior_1": "B",
            "expresion": "A ∈ B", "accion": "calcular", **extra}


@override_settings(ROOT_URLCONF="tests.urls_conjuntos")
class ConjuntosWebTests(SimpleTestCase):
    def test_catalogo_y_pantalla(self):
        self.assertEqual(reverse("calculadora:relaciones-conjuntos"), RUTA)
        self.assertEqual(catalogo.herramienta_por_id("relaciones-conjuntos").area.nombre, "Conjuntos")
        self.assertContains(self.client.get("/?q=pertenencia"), "Relaciones entre conjuntos")
        respuesta = self.client.get(RUTA)
        for texto in ('name="nombre_0"', 'name="contenido_0"', 'name="expresion"',
                      'data-perfil="relacion-conjuntos"', 'calculadora/conjuntos.js', 'math-keyboard-profiles'):
            self.assertContains(respuesta, texto)

    def test_resultado_unico_y_procedimiento(self):
        respuesta = self.client.post(RUTA, datos())
        self.assertContains(respuesta, "Verdadero", count=1)
        self.assertContains(respuesta, 'id="procedimiento"')
        self.assertNotContains(respuesta, 'id="procedimiento" open')
        self.assertContains(respuesta, "elemento completo")
        self.assertContains(respuesta, 'data-resultado="vigente"')
        self.assertContains(self.client.post(RUTA, datos(expresion="A ⊆ B")), "Falso", count=1)

    def test_crud_y_renombrado(self):
        respuesta = self.client.post(RUTA, datos(nombre_0="S", accion="guardar"))
        self.assertContains(respuesta, "S ∈ B")
        self.assertContains(respuesta, 'name="anterior_0" value="S"')
        self.assertNotContains(respuesta, 'id="resultado"')
        respuesta = self.client.post(RUTA, datos(accion="agregar", definicion="Conjunto1 = {1,1,{2}}"))
        self.assertContains(respuesta, 'name="nombre_2" value="Conjunto1"')
        respuesta = self.client.post(RUTA, datos(accion="guardar", eliminar="0"))
        self.assertNotContains(respuesta, 'name="nombre_1"')
        self.assertContains(respuesta, 'name="nombre_0" value="B"')
        self.assertContains(self.client.post(RUTA, datos(contenido_0="{3}", expresion="3 ∈ A")), "Verdadero")

    def test_guiado_genera_expresion_sin_calcular(self):
        respuesta = self.client.post(RUTA, datos(accion="construir", izquierdo="{2}", operador="⊆", derecho="B"))
        self.assertContains(respuesta, "{2} ⊆ B")
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_post_invalido_conserva_editor(self):
        for cambios, mensaje in (
            ({"nombre_1": "A"}, "nombre"), ({"expresion": "Z ∈ B"}, "No existe"),
            ({"contenido_0": "{1,}"}, "Se esperaba"), ({"expresion": "1 ⊆ A"}, "inclusión"),
            ({"cantidad": "999999999"}, "50"), ({"cantidad": "-1"}, "0"),
            ({"intruso": "1"}, "campos"), ({"nombre_0": "__import__"}, "nombre"),
            ({"accion": "construir", "operador": "∪"}, "relación"),
            ({"contenido_0": "{" * 60 + "}" * 60}, "niveles"),
        ):
            with self.subTest(cambios=cambios):
                respuesta = self.client.post(RUTA, datos(**cambios))
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, mensaje)
                self.assertNotContains(respuesta, 'id="resultado"')

    def test_xss_y_campos_repetidos(self):
        respuesta = self.client.post(RUTA, datos(expresion='"<script>alert(1)</script>" ∈ {"<script>alert(1)</script>"}'))
        self.assertContains(respuesta, "Verdadero")
        self.assertNotContains(respuesta, "<script>alert(1)</script>")
        self.assertContains(self.client.post(RUTA, datos(nombre_0=["A", "S"])), "repetidos")

    def test_presupuesto_acumulado_y_agregado_duplicado(self):
        contenido = "{" + ",".join(map(str, range(450))) + "}"
        respuesta = self.client.post(RUTA, datos(contenido_0=contenido, contenido_1=contenido))
        self.assertContains(respuesta, "900 elementos")
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertContains(self.client.post(RUTA, datos(accion="agregar", definicion="A = {}")), "ya está definido")
        self.assertContains(self.client.post(RUTA, datos(eliminar="50")), "No existe")

    def test_cero_definiciones_y_fallback_guiado(self):
        respuesta = self.client.post(RUTA, {"cantidad": "0", "expresion": "{} = ∅", "accion": "calcular"})
        self.assertContains(respuesta, "Verdadero", count=1)
        respuesta = self.client.post(RUTA, datos(accion="construir", izquierdo="2", operador="∈", derecho="A"))
        self.assertContains(respuesta, "2 ∈ A")

    def test_metodos_csrf_y_borrador_conservado(self):
        self.assertEqual(self.client.put(RUTA).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(RUTA, datos()).status_code, 403)
        respuesta = self.client.post(RUTA, datos(definicion="S = {3}"))
        self.assertContains(respuesta, 'value="S = {3}"')

    def test_operaciones_y_cardinalidad_sin_javascript(self):
        for expresion, esperado in (('A ∪ B', '{1, 2, {1, 2}}'),
                                    ('A ∩ B', '{2}'), ('A ∖ B', '{1}'),
                                    ('∁(A, A ∪ B)', '{{1, 2}}'), ('|A|', '2'),
                                    ('|A ∩ B| = 1', 'Verdadero'), ('|∅|', '0'),
                                    ('A ∩ ∅', '∅')):
            with self.subTest(expresion=expresion):
                respuesta = self.client.post(RUTA, datos(expresion=expresion))
                self.assertContains(respuesta, f'data-respuesta-relacion>{esperado}</p>', html=False)
                self.assertContains(respuesta, 'id="procedimiento"')
                self.assertNotContains(respuesta, 'id="procedimiento" open')

    def test_contrato_json_exacto_y_evaluacion_unica(self):
        with patch('frontend.web.calculadora.servicios_conjuntos.evaluar_expresion', wraps=evaluar_expresion) as evaluar:
            respuesta = self.client.post(RUTA, datos(expresion='|A ∪ B|'))
        self.assertEqual(evaluar.call_count, 1)
        contenido = re.search(r'<script id="conjuntos-resultado-datos"[^>]*>(.*?)</script>', respuesta.content.decode(), re.S)[1]
        contrato = json.loads(contenido)
        self.assertEqual(contrato['valor'], {'tipo': 'numero', 'numerador': '3', 'denominador': '1'})
        self.assertEqual([p['regla'] for p in contrato['procedimiento']], ['union', 'cardinalidad'])
        union = contrato['procedimiento'][0]
        self.assertEqual(union['operandos'][0]['tipo'], 'conjunto')
        self.assertEqual(union['resultado']['tipo'], 'conjunto')
        self.assertEqual(len(union['resultado']['elementos']), 3)

    def test_errores_p2_conservan_editor_y_no_presentan_resultado(self):
        for expresion, mensaje in (('∁(A,B)', 'universo'), ('A ∪ 1', 'conjuntos finitos'),
                                    ('|1|', 'conjuntos finitos'), ('A ∪', 'Se esperaba')):
            with self.subTest(expresion=expresion):
                respuesta = self.client.post(RUTA, datos(expresion=expresion))
                self.assertContains(respuesta, mensaje)
                self.assertNotContains(respuesta, 'id="resultado"')
                self.assertContains(respuesta, 'name="nombre_0" value="A"')
        conjunto = '{' + ','.join(map(str, range(250))) + '}'
        respuesta = self.client.post(RUTA, datos(contenido_0=conjunto, expresion=' ∪ '.join(['A'] * 49)))
        self.assertContains(respuesta, 'presupuesto')
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_json_escapa_texto_y_conserva_tipo(self):
        respuesta = self.client.post(RUTA, datos(expresion='{"</script><script>alert(1)</script>", 1/2} ∪ ∅'))
        self.assertNotContains(respuesta, '</script><script>alert(1)</script>')
        self.assertContains(respuesta, '\\u003C/script\\u003E')

    @override_settings(ROOT_URLCONF='frontend.web.algebra_web.urls')
    def test_p2_no_habilita_urls_publicas(self):
        for ruta in ('/conjuntos/', RUTA, '/conjuntos/operaciones/'):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 404)
                self.assertEqual(self.client.post(ruta, datos(expresion='A ∪ B')).status_code, 404)
