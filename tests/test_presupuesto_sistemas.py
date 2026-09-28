"""Dimensiones no confiables: rechazar antes de range, celdas, parser o motor."""

import os
import random
from unittest.mock import Mock, patch
from urllib.parse import urlencode

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.conf import settings
from django.http import QueryDict
from django.test import Client, SimpleTestCase, override_settings

from backend.parser_sistemas import parsear_sistema
from backend.presupuesto_sistemas import (
    CELDAS_MAXIMAS,
    ECUACIONES_MAXIMAS,
    LONGITUD_SISTEMA_MAXIMA,
    VARIABLES_MAXIMAS,
    dimensiones_admitidas,
)
from frontend.web.calculadora.forms import SistemaForm
from frontend.web.calculadora.opciones_sistemas import BLOQUES_PREDETERMINADOS
from frontend.web.calculadora.servicios import resolver_entrada_web
from tests.test_interfaz_progresiva import Formulario
from tests.test_web import datos_matriz


FORMULARIOS = "frontend.web.calculadora.forms"
VISTAS = "frontend.web.calculadora.views"


def matriz_educativa(filas, variables):
    """Unas filas diagonales y otras redundantes: solución conocida y tamaño acotado."""
    return [
        [int(j == i % variables) for j in range(variables)] + [1]
        for i in range(filas)
    ]


class PruebasPresupuestoSistemas(SimpleTestCase):
    def assert_rechazo_temprano(self, ecuaciones, variables):
        datos = {"tipo_entrada": "matriz", "metodo": "comparar",
                 "ecuaciones": ecuaciones, "variables": variables}
        # Si reaparece el fallo, el test falla sin construir ni un rango peligroso.
        with (
            patch(f"{FORMULARIOS}.range", create=True, side_effect=AssertionError("range antes del límite")) as rangos,
            patch(f"{FORMULARIOS}.convertir_a_numero") as convertir,
            patch(f"{FORMULARIOS}.construir_matriz_aumentada") as construir,
            patch.object(SistemaForm, "valores_matriz_desde") as reconstruir,
            patch(f"{VISTAS}.resolver_entrada_web") as resolver,
        ):
            respuesta = self.client.post("/sistemas/", datos)
            self.assertEqual(respuesta.status_code, 200)
            self.assertRegex(respuesta.content.decode(), r'class="(?:field-error|alert error)"')
            for mock in (rangos, convertir, construir, reconstruir, resolver):
                mock.assert_not_called()
        return respuesta

    def test_demasiadas_ecuaciones_se_rechazan_antes_de_cualquier_range(self):
        self.assert_rechazo_temprano(ECUACIONES_MAXIMAS + 1, 2)

    def test_demasiadas_variables_se_rechazan_antes_de_cualquier_range(self):
        self.assert_rechazo_temprano(2, VARIABLES_MAXIMAS + 1)

    def test_una_celda_sobre_el_presupuesto_se_rechaza_antes_de_cualquier_range(self):
        self.assertEqual(11 * (10 + 1), CELDAS_MAXIMAS + 1)
        respuesta = self.assert_rechazo_temprano(11, 10)
        self.assertContains(respuesta, f"hasta {CELDAS_MAXIMAS} celdas")

    def test_post_dimensiones_absurdas_o_invalidas_no_construye_ni_resuelve(self):
        invalidos = ("100000", "999999999999999999999999999", "1e9", "-5", "0", "texto", "9" * 5000)
        for valor in invalidos:
            for filas, variables in ((valor, "2"), ("2", valor), (valor, valor)):
                with self.subTest(filas=filas[:30], variables=variables[:30]):
                    self.assert_rechazo_temprano(filas, variables)

    def test_helper_directo_no_lee_datos_ni_itera_dimensiones_invalidas(self):
        datos = Mock()
        for filas, variables in ((100000, 100000), (100000, 2), (2, 100000), (11, 10),
                                 (0, 2), (2, -5), ("2", 2), (None, 2)):
            with self.subTest(filas=filas, variables=variables):
                with patch(f"{FORMULARIOS}.range", create=True, side_effect=AssertionError("range")):
                    self.assertEqual(SistemaForm.valores_matriz_desde(datos, filas, variables), [])
        datos.get.assert_not_called()

    def test_reconstruccion_post_rechazado_por_presupuesto_devuelve_vacio(self):
        form = SistemaForm({"tipo_entrada": "matriz", "metodo": "gauss", "ecuaciones": 11, "variables": 10})
        self.assertFalse(form.is_valid())
        with patch.object(SistemaForm, "valores_matriz_desde") as reconstruir:
            self.assertEqual(form.valores_matriz_ingresados(), [])
            reconstruir.assert_not_called()

    def test_get_manipulado_no_invoca_reconstruccion_ni_motor(self):
        for valor in ("100000", "999999999999999999999999999", "1e9", "-5", "0", "texto", "²", "9" * 5000):
            for filas, variables in ((valor, "2"), ("2", valor), (valor, valor)):
                with (
                    self.subTest(filas=filas[:30], variables=variables[:30]),
                    patch.object(SistemaForm, "valores_matriz_desde") as reconstruir,
                    patch(f"{VISTAS}.resolver_entrada_web") as resolver,
                    patch(f"{FORMULARIOS}.range", create=True, side_effect=AssertionError("range")),
                ):
                    datos = {"tipo_entrada": "matriz", "ecuaciones": filas, "variables": variables}
                    respuesta = self.client.get("/sistemas/", datos)
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertContains(respuesta, 'id="matrix-initial-values" type="application/json">[]')
                    reconstruir.assert_not_called()
                    resolver.assert_not_called()

    def test_get_rechaza_presupuesto_con_dimensiones_individualmente_validas(self):
        consulta = QueryDict("tipo_entrada=matriz&ecuaciones=11&variables=10")
        inicial = SistemaForm.inicial_desde(consulta)
        self.assertNotIn("ecuaciones", inicial)
        self.assertNotIn("variables", inicial)
        with patch.object(SistemaForm, "valores_matriz_desde") as reconstruir:
            self.assertEqual(self.client.get("/sistemas/?" + consulta.urlencode()).status_code, 200)
            reconstruir.assert_not_called()

    def test_vista_verifica_dimensiones_incluso_si_iniciales_no_fueran_seguros(self):
        with (
            patch.object(SistemaForm, "inicial_desde", return_value={"ecuaciones": 100000, "variables": 100000}),
            patch.object(SistemaForm, "valores_matriz_desde") as reconstruir,
        ):
            self.assertEqual(self.client.get("/sistemas/").status_code, 200)
            reconstruir.assert_not_called()

    def test_get_adjunto_a_post_invalido_no_reconstruye_otra_matriz(self):
        with patch.object(SistemaForm, "valores_matriz_desde") as reconstruir:
            respuesta = self.client.post("/sistemas/?ecuaciones=2&variables=2", {
                "tipo_entrada": "matriz", "metodo": "gauss", "ecuaciones": 100000, "variables": 100000,
            })
            self.assertEqual(respuesta.status_code, 200)
            reconstruir.assert_not_called()

    def test_get_valido_reconstruye_valores_sin_resolver(self):
        datos = datos_matriz([[1, 1, 3], [1, -1, 1]])
        with (
            patch.object(SistemaForm, "valores_matriz_desde", wraps=SistemaForm.valores_matriz_desde) as reconstruir,
            patch(f"{VISTAS}.resolver_entrada_web") as resolver,
        ):
            respuesta = self.client.get("/sistemas/", datos)
            self.assertContains(respuesta, '[["1", "1", "3"], ["1", "-1", "1"]]')
            self.assertEqual(reconstruir.call_args.args[1:], (2, 2))
            resolver.assert_not_called()

    def test_maximos_individuales_y_total_admiten_rectangulares(self):
        for filas, variables in ((12, 9), (10, 11), (9, 12)):
            with self.subTest(filas=filas, variables=variables):
                datos = datos_matriz(matriz_educativa(filas, variables))
                form = SistemaForm(datos)
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(len(form.cleaned_data["matriz_aumentada"]), filas)
                self.assertEqual(len(form.valores_matriz_ingresados()[0]), variables + 1)
                respuesta = self.client.get("/sistemas/", datos)
                self.assertContains(respuesta, f'name="ecuaciones" value="{filas}"')

    def test_gauss_gauss_jordan_y_comparar_resuelven_el_maximo(self):
        matriz = matriz_educativa(12, 9)
        self.assertEqual(sum(map(len, matriz)), CELDAS_MAXIMAS)
        for metodo in ("gauss", "gauss_jordan", "comparar"):
            with self.subTest(metodo=metodo):
                respuesta = self.client.post("/sistemas/", datos_matriz(matriz, metodo))
                self.assertContains(respuesta, 'id="resultado"')
                self.assertContains(respuesta, "x9 = 1")
                self.assertContains(respuesta, "Consistente de solución única")

    def test_maximo_denso_se_resuelve_con_aritmetica_exacta(self):
        rng = random.Random(42)
        coeficientes = [[rng.randint(-5, 5) + (30 if i == j else 0) for j in range(9)] for i in range(12)]
        matriz = [fila + [sum(fila)] for fila in coeficientes]
        for metodo in ("gauss", "gauss_jordan"):
            with self.subTest(metodo=metodo):
                resultado = resolver_entrada_web("matriz", metodo, matriz_aumentada=matriz)
                self.assertEqual(resultado["solucion_general"], [f"x{i} = 1" for i in range(1, 10)])
                self.assertEqual(resultado["columnas_pivote"], list(range(1, 10)))
                self.assertGreater(len(resultado["pasos"]), 12)

    @override_settings(DATA_UPLOAD_MAX_NUMBER_FIELDS=1000)
    def test_peor_post_real_con_csrf_y_todas_las_opciones_cabe_en_django(self):
        cliente = Client(enforce_csrf_checks=True)
        html = cliente.get("/sistemas/?tipo_entrada=matriz&ecuaciones=12&variables=9&metodo=comparar").content.decode()
        # Reproduce el cambio de fieldsets realizado por setInputMode(): todos
        # los controles reales, incluidos los campos repetidos mostrar y CSRF.
        html = html.replace('id="system-fields"', 'id="system-fields" disabled')
        html = html.replace('class="input-mode" hidden disabled', 'class="input-mode"')
        controles = Formulario(html, "sistema-form").datos
        self.assertEqual(len(controles), 10)
        celdas = [(nombre, valor) for nombre, valor in datos_matriz(matriz_educativa(12, 9)).items()
                  if nombre.startswith("matriz_")]
        pares = controles + celdas
        self.assertEqual(len(pares), 130)
        self.assertLess(len(pares), settings.DATA_UPLOAD_MAX_NUMBER_FIELDS)
        # urlencoded cuenta las cuatro apariciones de mostrar, no solo claves.
        respuesta = cliente.post("/sistemas/", urlencode(pares), content_type="application/x-www-form-urlencoded")
        self.assertContains(respuesta, "x9 = 1")
        self.assertEqual(sum(len(v) for _, v in respuesta.wsgi_request.POST.lists()), 130)
        # También se procesa con el mismo parser multipart que usa Client.post.
        datos = Formulario(html, "sistema-form").como_datos()
        datos.update(dict(celdas))
        self.assertContains(cliente.post("/sistemas/", datos), "x9 = 1")

    def test_html_transmite_la_politica_al_navegador(self):
        html = self.client.get("/sistemas/").content.decode()
        self.assertIn(f'data-max-celdas="{CELDAS_MAXIMAS}"', html)
        self.assertRegex(html, rf'name="ecuaciones"[^>]*max="{ECUACIONES_MAXIMAS}"')
        self.assertRegex(html, rf'name="variables"[^>]*max="{VARIABLES_MAXIMAS}"')
        self.assertRegex(html, rf'name="sistema"[^>]*maxlength="{LONGITUD_SISTEMA_MAXIMA}"')

    def test_servicio_directo_rechaza_matriz_fuera_de_presupuesto_antes_del_motor(self):
        resolver = Mock(side_effect=AssertionError("motor"))
        with patch.dict("frontend.web.calculadora.servicios._RESOLVERS", {"gauss": ("Gauss", resolver, "", "")}):
            with self.assertRaisesRegex(ValueError, "celdas"):
                resolver_entrada_web("matriz", "gauss", matriz_aumentada=matriz_educativa(11, 10))
        resolver.assert_not_called()


class PruebasPresupuestoTexto(SimpleTestCase):
    def test_texto_educativo_sigue_funcionando_con_todos_los_metodos(self):
        for metodo in ("gauss", "gauss_jordan", "comparar"):
            with self.subTest(metodo=metodo):
                respuesta = self.client.post("/sistemas/", {"sistema": "x1+x2=3;x1-x2=1", "metodo": metodo})
                self.assertContains(respuesta, "x1 = 2")
                self.assertContains(respuesta, "x2 = 1")

    def test_texto_excesivo_y_espacios_no_llegan_al_servicio(self):
        for texto in ("x1=1" * (LONGITUD_SISTEMA_MAXIMA // 4 + 1), " " * LONGITUD_SISTEMA_MAXIMA + "x1=1"):
            with self.subTest(espacios=texto.startswith(" ")), patch(f"{VISTAS}.resolver_entrada_web") as resolver:
                respuesta = self.client.post("/sistemas/", {"metodo": "gauss", "sistema": texto})
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, str(LONGITUD_SISTEMA_MAXIMA))
                resolver.assert_not_called()

    def test_get_ignora_texto_excesivo(self):
        respuesta = self.client.get("/sistemas/", {"sistema": "x1=1" * LONGITUD_SISTEMA_MAXIMA})
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn("sistema", SistemaForm.inicial_desde(respuesta.wsgi_request.GET))

    def test_parser_limita_texto_y_ecuaciones_antes_de_analizarlas(self):
        with patch("backend.parser_sistemas.parsear_ecuacion") as analizar:
            for texto in ("x1=1" * LONGITUD_SISTEMA_MAXIMA, ";".join(["x1=1"] * (ECUACIONES_MAXIMAS + 1))):
                with self.subTest(longitud=len(texto)), self.assertRaises(ValueError):
                    parsear_sistema(texto, limitar_entrada=True)
            analizar.assert_not_called()

    def test_indice_textual_absurdo_no_reserva_una_fila_ni_invoca_motor(self):
        for texto in ("x100000=1", "x999999999999999999999999999=1", ";".join(["x10=1"] * 11)):
            with self.subTest(texto=texto):
                # El presupuesto debe abortar antes de simplificar coeficientes al
                # construir filas. Parsear RHS también simplifica: se aísla esa fase.
                with patch("backend.parser_sistemas.convertir_a_numero", return_value=1), \
                     patch("backend.parser_sistemas._simplificar", side_effect=AssertionError("construcción")) as construir:
                    with self.assertRaises(ValueError):
                        parsear_sistema(texto, limitar_entrada=True)
                    construir.assert_not_called()
                motor = Mock(side_effect=AssertionError("motor"))
                with patch.dict("frontend.web.calculadora.servicios._RESOLVERS", {"gauss": ("Gauss", motor, "", "")}):
                    respuesta = self.client.post("/sistemas/", {"metodo": "gauss", "sistema": texto})
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertNotContains(respuesta, 'id="resultado"')
                    motor.assert_not_called()

    def test_longitud_exacta_permitida_y_parser_de_consola_compatible(self):
        texto = "x1=1" + " " * (LONGITUD_SISTEMA_MAXIMA - 4)
        self.assertEqual(parsear_sistema(texto, limitar_entrada=True), [[1, 1]])
        self.assertTrue(SistemaForm({"sistema": texto, "metodo": "gauss"}).is_valid())
        self.assertEqual(len(parsear_sistema("x13=1")[0]), 14)

    def test_texto_y_matriz_comparten_presupuesto(self):
        texto = ";".join(["x9=1"] * 12)
        self.assertEqual(sum(map(len, parsear_sistema(texto, limitar_entrada=True))), CELDAS_MAXIMAS)
        self.assertTrue(dimensiones_admitidas(12, 9))
