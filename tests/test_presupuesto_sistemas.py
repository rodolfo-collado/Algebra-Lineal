"""Dimensiones no confiables: rechazar antes de range, celdas, parser o motor."""

import os
import random
from fractions import Fraction
from unittest.mock import Mock, patch
from urllib.parse import urlencode

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.conf import settings
from django.http import QueryDict
from django.test import Client, SimpleTestCase, override_settings

from backend.parser_sistemas import convertir_a_numero, parsear_sistema
from backend.presupuesto_sistemas import (
    CELDAS_MAXIMAS,
    DIGITOS_MAXIMOS,
    ECUACIONES_MAXIMAS,
    LONGITUD_SISTEMA_MAXIMA,
    MENSAJE_NOTACION_CIENTIFICA,
    MENSAJE_NUMERO_GRANDE,
    MENSAJE_VALOR_AGRUPADO_GRANDE,
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
        with patch("backend.parser_sistemas._leer_ecuacion") as analizar:
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


def _literal_caro(texto):
    compacto = "".join(str(texto).split())
    return any(caracter in "eE" for caracter in compacto) or (
        sum(caracter.isdigit() for caracter in compacto) > DIGITOS_MAXIMOS
    )


def _fraction_vigilada(valor=0, denominador=None):
    if isinstance(valor, str) and _literal_caro(valor):
        raise AssertionError(f"Fraction({valor[:48]!r})")
    if denominador is None:
        return Fraction(valor)
    return Fraction(valor, denominador)


class PruebasLiteralesSistemas(SimpleTestCase):
    def assert_rechazo_textual(self, texto, fragmento):
        with patch("backend.parser_sistemas.Fraction", _fraction_vigilada):
            with self.assertRaises(ValueError) as contexto:
                parsear_sistema(texto, limitar_entrada=True)
        mensaje = str(contexto.exception)
        self.assertIn(fragmento, mensaje)
        self.assertNotIn("..", mensaje)
        return mensaje

    def test_literales_educativos_siguen_admitidos(self):
        casos = (
            ("3x1=1", [[3, 1]]),
            ("-5x1=1", [[-5, 1]]),
            ("1/2x1=1", [[Fraction(1, 2), 1]]),
            ("-7/3x1=1", [[Fraction(-7, 3), 1]]),
            ("0.25x1=1", [[Fraction(1, 4), 1]]),
            ("x1=-5", [[1, -5]]),
            ("x1=1/2", [[1, Fraction(1, 2)]]),
            ("x1=-7/3", [[1, Fraction(-7, 3)]]),
            ("x1=0.25", [[1, Fraction(1, 4)]]),
            ("x1=.5", [[1, Fraction(1, 2)]]),
            ("x1=5.", [[1, 5]]),
            ("x1=1 / 2", [[1, Fraction(1, 2)]]),
            (".5x1=0.25", [[Fraction(1, 2), Fraction(1, 4)]]),
            ("+x1=2", [[1, 2]]),
            ("-x1=3", [[-1, 3]]),
            ("-1/2x1=1", [[Fraction(-1, 2), 1]]),
        )
        for texto, matriz in casos:
            with self.subTest(texto=texto):
                self.assertEqual(parsear_sistema(texto, limitar_entrada=True), matriz)

    def test_valor_en_el_limite_de_digitos(self):
        tope = "9" * DIGITOS_MAXIMOS
        decimal = "1" * DIGITOS_MAXIMOS
        self.assertEqual(parsear_sistema(f"x1={tope}", limitar_entrada=True), [[1, int(tope)]])
        self.assertEqual(parsear_sistema(f"x1=-{tope}", limitar_entrada=True), [[1, -int(tope)]])
        self.assertEqual(parsear_sistema(f"{tope}x1=1", limitar_entrada=True), [[int(tope), 1]])
        self.assertEqual(
            parsear_sistema(f"x1={tope}/{tope}", limitar_entrada=True),
            [[1, 1]],
        )
        self.assertEqual(
            parsear_sistema(f"x1=1/{tope}", limitar_entrada=True),
            [[1, Fraction(1, int(tope))]],
        )
        self.assertEqual(
            parsear_sistema(f"x1=1 / {tope}", limitar_entrada=True),
            [[1, Fraction(1, int(tope))]],
        )
        self.assertEqual(
            parsear_sistema(f"x1=0.{decimal}", limitar_entrada=True),
            [[1, Fraction(int(decimal), 10 ** DIGITOS_MAXIMOS)]],
        )
        datos = datos_matriz([[1, 1]])
        datos["matriz_0_0"] = tope
        form = SistemaForm(datos)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["matriz_aumentada"][0][0], int(tope))

    def test_componente_demasiado_largo_no_llega_a_fraction(self):
        largo = "9" * (DIGITOS_MAXIMOS + 1)
        casos = {
            "entero": f"x1={largo}",
            "numerador": f"x1={largo}/2",
            "denominador": f"x1=1/{largo}",
            "decimal": f"x1=0.{largo}",
            "coeficiente": f"{largo}x1=1",
            "numerador coeficiente": f"{largo}/2x1=1",
            "denominador coeficiente": f"1/{largo}x1=1",
            "decimal coeficiente": f"{largo}.5x1=1",
            "termino independiente": f"x1={largo}",
            "guion bajo": "x1=1_" + "0" * DIGITOS_MAXIMOS,
        }
        for nombre, texto in casos.items():
            with self.subTest(nombre=nombre):
                self.assert_rechazo_textual(texto, MENSAJE_NUMERO_GRANDE)

    def test_denominador_cero_tiene_mensaje_propio(self):
        with self.assertRaises(ValueError) as coeficiente:
            parsear_sistema("1/0x1=2", limitar_entrada=True)
        self.assertEqual(
            str(coeficiente.exception),
            "Formato de sistema inválido: un coeficiente no puede tener denominador cero.",
        )
        # P25.2: el lado derecho ya no es solo un término independiente, así que
        # el mensaje nombra el problema en cualquier lado.
        for texto in ("x1=1/0", "1/0 = x1", "x1 + 1/0 = x2"):
            with self.subTest(texto=texto), self.assertRaises(ValueError) as independiente:
                parsear_sistema(texto, limitar_entrada=True)
            self.assertEqual(
                str(independiente.exception),
                "Formato de sistema inválido: un número no puede tener denominador cero.",
            )
        datos = datos_matriz([["1/0", 1]])
        respuesta = self.client.post("/sistemas/", datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "no es un número válido")
        self.assertNotContains(respuesta, "Traceback")

    def test_notacion_cientifica_no_llega_a_fraction(self):
        casos = (
            "x1=1e1000000000",
            "x1=1E1000000000",
            "x1=1e-1000000000",
            "x1=1E-1000000000",
            "x1=1 e 1000000000",
            "x1=1e2",
            "x1=1E-2",
            "1e1000000000x1=1",
            "1E-1000000000x1=1",
        )
        for texto in casos:
            with self.subTest(texto=texto):
                self.assert_rechazo_textual(texto, MENSAJE_NOTACION_CIENTIFICA)
        for texto in ("x1=test", "x1=hello", "x1=e10", "e10 = x1", "x1 = x2 + e10"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError) as contexto:
                    parsear_sistema(texto, limitar_entrada=True)
                self.assertIn("no es un número ni una variable xN", str(contexto.exception))
                self.assertNotIn("científica", str(contexto.exception))

    def test_texto_extremo_responde_200_sin_motor(self):
        motor = Mock(side_effect=AssertionError("motor"))
        resolvers = {
            "gauss": ("Gauss", motor, "matriz_escalonada", "Matriz escalonada"),
            "gauss_jordan": ("Gauss-Jordan", motor, "matriz_reducida", "Matriz reducida"),
        }
        textos = (
            "x1=1e1000000000",
            "x1=1e-1000000000",
            "1e1000000000x1=1",
            "x1=" + "9" * (DIGITOS_MAXIMOS + 1),
        )
        for texto in textos:
            with self.subTest(texto=texto[:32]), patch(
                "backend.parser_sistemas.Fraction", _fraction_vigilada
            ), patch.dict("frontend.web.calculadora.servicios._RESOLVERS", resolvers):
                respuesta = self.client.post("/sistemas/", {"metodo": "gauss", "sistema": texto})
                self.assertEqual(respuesta.status_code, 200)
                self.assertNotContains(respuesta, "Traceback")
                self.assertNotContains(respuesta, 'id="resultado"')
                motor.assert_not_called()

    def test_celda_extrema_no_convierte_ni_resuelve(self):
        real = convertir_a_numero

        def vigil(texto):
            if _literal_caro(texto):
                raise AssertionError(f"convertir({texto[:48]!r})")
            return real(texto)

        casos = {
            "coeficiente cientifico": ("1e1000000000", "1"),
            "independiente cientifico": ("1", "1e-1000000000"),
            "coeficiente largo": ("9" * (DIGITOS_MAXIMOS + 1), "1"),
            "independiente largo": ("1", "9" * (DIGITOS_MAXIMOS + 1)),
            "decimal largo": ("0." + "1" * (DIGITOS_MAXIMOS + 1), "1"),
            "denominador largo": ("1/" + "9" * (DIGITOS_MAXIMOS + 1), "1"),
        }
        for nombre, celdas in casos.items():
            datos = datos_matriz([[1, 1]])
            datos["matriz_0_0"], datos["matriz_0_1"] = celdas
            with self.subTest(nombre=nombre), patch(
                f"{FORMULARIOS}.convertir_a_numero", vigil
            ), patch(f"{VISTAS}.resolver_entrada_web", side_effect=AssertionError("servicio")):
                respuesta = self.client.post("/sistemas/", datos)
                fragmento = (
                    MENSAJE_NOTACION_CIENTIFICA if "cientifico" in nombre else MENSAJE_NUMERO_GRANDE
                )
                self.assertEqual(respuesta.status_code, 200)
                self.assertNotContains(respuesta, "Traceback")
                self.assertContains(respuesta, fragmento)
                self.assertNotContains(respuesta, 'id="resultado"')

    def test_servicio_rechaza_el_literal_antes_del_motor(self):
        motor = Mock(side_effect=AssertionError("motor"))
        with patch("backend.parser_sistemas.Fraction", _fraction_vigilada), patch.dict(
            "frontend.web.calculadora.servicios._RESOLVERS",
            {"gauss": ("Gauss", motor, "matriz_escalonada", "Matriz escalonada")},
        ):
            for texto in ("x1=1e1000000000", "x1=" + "9" * (DIGITOS_MAXIMOS + 1)):
                with self.subTest(texto=texto[:24]):
                    with self.assertRaises(ValueError):
                        resolver_entrada_web("sistema", "gauss", texto=texto)
                    motor.assert_not_called()

    def test_consola_y_convertir_a_numero_conservan_su_contrato(self):
        self.assertEqual(parsear_sistema("x1=1e2"), [[1, 100]])
        self.assertEqual(parsear_sistema("x1=1E-2"), [[1, Fraction(1, 100)]])
        self.assertEqual(parsear_sistema("x1=" + "9" * (DIGITOS_MAXIMOS + 1))[0][1], int("9" * (DIGITOS_MAXIMOS + 1)))
        with self.assertRaises(ValueError) as contexto:
            parsear_sistema("1e2x1=1")
        self.assertIn("coeficientes numéricos", str(contexto.exception))
        self.assertEqual(convertir_a_numero("1e2"), 100)
        self.assertEqual(convertir_a_numero("1_000"), 1000)
        self.assertEqual(parsear_sistema("x1=1_000", limitar_entrada=True), [[1, 1000]])


# Dos denominadores de 100 cifras sin factores comunes: cada literal cabe, su suma no.
P, Q = 10**99 + 1, 10**99 + 3


class PruebasPresupuestoFormaLibre(SimpleTestCase):
    """P25.2: normalizar no reabre entradas caras; cada literal se revisa en ambos lados."""

    def assert_rechazo(self, texto, fragmento, vigilar_fraction=True):
        """Se rechaza antes de construir filas y, si se vigila, antes de convertir un literal caro."""
        fraction = _fraction_vigilada if vigilar_fraction else Fraction
        with patch("backend.parser_sistemas.Fraction", fraction), \
             patch("backend.parser_sistemas._simplificar", side_effect=AssertionError("construcción")):
            with self.assertRaises(ValueError) as contexto:
                parsear_sistema(texto, limitar_entrada=True)
        self.assertIn(fragmento, str(contexto.exception))

    def test_literales_extremos_en_cualquier_lado_no_llegan_a_fraction(self):
        largo = "9" * (DIGITOS_MAXIMOS + 1)
        casos = {
            "constante a la izquierda": f"x1 + {largo} = x2",
            "lado izquierdo sin variables": f"{largo} = x1",
            "fracción a la derecha": f"x1 = x2 - {largo}/2",
            "decimal a la derecha": f"x1 = x2 + 0.{largo}",
            "coeficiente a la derecha": f"x1 = {largo}x2",
            "guion bajo con variables": "x1 = x2 + 1_" + "0" * DIGITOS_MAXIMOS,
            "índice de variable": f"x1 = x{largo}",
        }
        for nombre, texto in casos.items():
            with self.subTest(nombre=nombre):
                self.assert_rechazo(texto, MENSAJE_NUMERO_GRANDE)

    def test_notacion_cientifica_en_cualquier_lado(self):
        for texto in ("x1 = x2 + 1e5", "x1 + 1e1000000000 = x2", "1E-1000000000 = x1", "x1 = 2e3x2", "x1 - 1 e 9 = x2"):
            with self.subTest(texto=texto):
                self.assert_rechazo(texto, MENSAJE_NOTACION_CIENTIFICA)

    def test_agrupar_terminos_no_supera_lo_que_admite_un_literal(self):
        for texto in (
            f"1/{P}x1 + 1/{Q}x1 = 1",   # variables repetidas: ya era posible antes de P25.2
            f"x1 = 1/{P} + 1/{Q}",
            f"x1 + 1/{P} = 1/{Q}",
            f"1/{P}x1 = 1/{Q}x2 - 1/{Q}x1",
        ):
            with self.subTest(texto=texto[:40]):
                # Cada literal cabe (Fraction sí se llama); lo que no cabe es su suma.
                self.assert_rechazo(texto, MENSAJE_VALOR_AGRUPADO_GRANDE, vigilar_fraction=False)

    def test_valores_en_el_limite_de_un_literal_se_admiten(self):
        tope = "9" * DIGITOS_MAXIMOS
        self.assertEqual(
            parsear_sistema(f"{tope}.{tope}x1 = 1", limitar_entrada=True),
            [[Fraction(int(tope + tope), 10**DIGITOS_MAXIMOS), 1]],
        )
        self.assertEqual(parsear_sistema(f"x1 + 1/{P} = 2/{P}", limitar_entrada=True), [[1, Fraction(1, P)]])
        self.assertEqual(parsear_sistema("1/3x1 + 1/7x1 = 1/2", limitar_entrada=True), [[Fraction(10, 21), Fraction(1, 2)]])

    def test_dimensiones_de_la_forma_libre_antes_de_construir_filas(self):
        self.assert_rechazo(f"x1 = x{VARIABLES_MAXIMAS + 1}", f"Indica entre 1 y {VARIABLES_MAXIMAS} variables")
        self.assert_rechazo("x10 = x1; " * 10 + "x10 = x1", f"hasta {CELDAS_MAXIMAS} celdas")
        with patch("backend.parser_sistemas._leer_ecuacion") as analizar, self.assertRaises(ValueError):
            parsear_sistema(";".join(["x1 - 1 = x2"] * (ECUACIONES_MAXIMAS + 1)), limitar_entrada=True)
        analizar.assert_not_called()

    def test_web_responde_200_con_mensaje_propio_y_sin_motor(self):
        motor = Mock(side_effect=AssertionError("motor"))
        casos = {
            f"x1 = 1/{P} + 1/{Q}": MENSAJE_VALOR_AGRUPADO_GRANDE,
            "x1 + 1e1000000000 = x2": MENSAJE_NOTACION_CIENTIFICA,
            "x1*x2 = 5": "deja de ser lineal",
        }
        for texto, fragmento in casos.items():
            with self.subTest(texto=texto[:32]), patch.dict(
                "frontend.web.calculadora.servicios._RESOLVERS", {"gauss": ("Gauss", motor, "", "")}
            ):
                respuesta = self.client.post("/sistemas/", {"metodo": "gauss", "sistema": texto})
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, fragmento)
                self.assertNotContains(respuesta, 'id="resultado"')
                self.assertNotContains(respuesta, "Exceeds the limit")
                motor.assert_not_called()

    def test_consola_conserva_su_contrato_sin_presupuesto(self):
        self.assertEqual(parsear_sistema(f"1/{P}x1 + 1/{Q}x1 = 1"), [[Fraction(P + Q, P * Q), 1]])
        # Un lado que es un solo número conserva el contrato de siempre, también a la izquierda.
        self.assertEqual(parsear_sistema("1e2 = x1 - x2"), [[1, -1, 100]])
        # Dentro de una suma no se añade notación científica, ni siquiera en consola.
        with self.assertRaisesRegex(ValueError, "«1e2» no es un número ni una variable xN"):
            parsear_sistema("x1 - 1e2 = x2")
