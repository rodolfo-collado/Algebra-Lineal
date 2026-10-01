"""P26.7: confirmación del cálculo exacto, contrato estricto y errores antes del aviso."""

import os
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.http import QueryDict
from django.test import SimpleTestCase
from django.test.utils import setup_test_environment, teardown_test_environment

from backend.presupuesto_computacional import Categoria, categoria
from frontend.web.calculadora.forms_expresiones import ExpresionMatricialForm
from frontend.web.calculadora.presupuesto_expresiones import estimar_expresion_web, firmar_entrada
from tests.test_matrices_web import Contenido, datos_simbolos, matriz

RUTA = "/matrices/operaciones/"
EVALUADOR = "frontend.web.calculadora.views.evaluar_expresion_web"
PESADA = "(uv)" * 12
SIMBOLOS = [matriz("u", [[i + 1] for i in range(10)]), matriz("v", [[j + 1 for j in range(10)]])]
RESULTADO = {"texto": "confirmado", "tipo": "escalar", "dimensiones": "escalar", "igualdad": "resultado = 1", "pasos": []}


class PruebasConfirmacionExpresiones(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_test_environment()
        cls.addClassCleanup(teardown_test_environment)

    def datos(self, expresion=PESADA, **extra):
        return datos_simbolos(expresion, SIMBOLOS, metodo="comparar", **extra)

    def aviso(self, datos=None):
        with patch(EVALUADOR, side_effect=AssertionError("Calculó antes de confirmar")):
            respuesta = self.client.post(RUTA, datos or self.datos())
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.context["form"].errors, respuesta.context["form"].errors)
        self.assertIsNone(respuesta.context["resultado"])
        self.assertIsNotNone(respuesta.context["confirmacion"])
        return respuesta

    def test_primer_post_no_calcula_y_el_aviso_es_neutral(self):
        for texto, nivel in ((PESADA, Categoria.PESADA), ("(uv)" * 25, Categoria.MUY_PESADA)):
            with self.subTest(nivel=nivel):
                respuesta = self.aviso(self.datos(texto))
                html = respuesta.content.decode()
                self.assertEqual(categoria(estimar_expresion_web(respuesta.context["form"].cleaned_data["entrada"])), nivel)
                self.assertContains(respuesta, "La expresión es válida, pero este cálculo puede tardar")
                self.assertContains(respuesta, "Tiempo estimado: entre")
                self.assertContains(respuesta, "¿Quieres continuar?")
                self.assertContains(respuesta, "Cancelar")
                self.assertContains(respuesta, "Continuar")
                for ausente in ('id="resultado"', "alert error", 'role="alert"', "La matriz es válida", "MUY_PESADA"):
                    self.assertNotIn(ausente, html)
                campos = Contenido(html).campos
                self.assertEqual({k: v["value"] for k, v in campos.items() if k.startswith("celda_")},
                                 {k: v for k, v in self.datos(texto).items() if k.startswith("celda_")})

    def test_continuar_calcula_exactamente_una_vez_sin_repetir_aviso(self):
        aviso = self.aviso()
        entrada = aviso.context["form"].cleaned_data["entrada"]
        with patch(EVALUADOR, return_value=RESULTADO) as evaluar:
            respuesta = self.client.post(RUTA, self.datos(confirmacion=aviso.context["confirmacion"]["firma"]))
        evaluar.assert_called_once_with(entrada)
        self.assertIsNone(respuesta.context["confirmacion"])
        self.assertContains(respuesta, 'id="resultado"')

    def test_cancelar_agregar_eliminar_y_aplicar_no_calculan_y_borran_firma(self):
        firma = self.aviso().context["confirmacion"]["firma"]
        for accion, valor in (("ajustar", "1"), ("agregar", "1"), ("eliminar", "1")):
            with self.subTest(accion=accion), patch(EVALUADOR, side_effect=AssertionError("Calculó")):
                respuesta = self.client.post(RUTA, self.datos(confirmacion=firma, **{accion: valor}))
                self.assertIsNone(respuesta.context["resultado"])
                self.assertIsNone(respuesta.context["confirmacion"])
                self.assertEqual(respuesta.context["form"]["confirmacion"].value(), None)
                self.assertEqual(respuesta.context["form"]["expresion"].value(), PESADA)
                self.assertEqual(respuesta.context["form"]["celda_0_0_0"].value(), "1")

    def test_firma_manipulada_y_cambios_no_autorizan_el_calculo(self):
        firma = self.aviso().context["confirmacion"]["firma"]
        for cambio in ({"confirmacion": "1"}, {"confirmacion": "f" * 64}, {"confirmacion": "basura"},
                       {"celda_0_0_0": "2"}, {"expresion": "(uv)" * 13}, {"metodo": "columnas"},
                       {"nombre_0": "U", "expresion": "(Uv)" * 12}):
            with self.subTest(cambio=cambio):
                datos = self.datos(confirmacion=firma)
                datos.update(cambio)
                self.aviso(datos)

    def test_firma_liga_tipos_dimensiones_valores_metodo_y_nodo(self):
        entrada = self.aviso().context["form"].cleaned_data["entrada"]
        firma = firmar_entrada(entrada)
        for clave, valor in (("nodo", "0.0"), ("metodo", "fila_columna"), ("expresion", PESADA + " ")):
            self.assertNotEqual(firma, firmar_entrada({**entrada, clave: valor}))
        otra = {**entrada, "simbolos": {**entrada["simbolos"], "u": {"tipo": "vector", "valor": list(range(10))}}}
        self.assertNotEqual(firma, firmar_entrada(otra))
        otra["simbolos"]["u"] = {"tipo": "matriz", "valor": [list(range(10))]}
        self.assertNotEqual(firma, firmar_entrada(otra))
        datos = self.datos(confirmacion=firma)
        datos["celda_0_0_0"] = "2/2"
        with patch(EVALUADOR, return_value=RESULTADO) as evaluar:
            self.client.post(RUTA, datos)
        evaluar.assert_called_once()  # mismo valor exacto, otra escritura

    def test_error_dimensional_parser_seguridad_y_contrato_antes_de_confirmar(self):
        for cambio in ({"expresion": PESADA + "+v"}, {"expresion": PESADA + "+"}, {"nodo": "0.9"},
                       {"celda_0_0_0": "1e999999"}, {"celda_0_0_0": "9" * 101}, {"ajeno": "1"},
                       {"columnas_1": "9"}):
            with self.subTest(cambio=cambio), patch(EVALUADOR, side_effect=AssertionError("Calculó entrada inválida")):
                datos = self.datos()
                datos.update(cambio)
                respuesta = self.client.post(RUTA, datos)
                self.assertTrue(respuesta.context["form"].errors)
                self.assertIsNone(respuesta.context["confirmacion"])

    def test_confirmacion_repetida_es_rechazada_por_el_contrato(self):
        datos = QueryDict(mutable=True)
        datos.update(self.datos())
        datos.setlist("confirmacion", ["a", "b"])
        with patch(EVALUADOR, side_effect=AssertionError("Calculó")):
            respuesta = self.client.post(RUTA, datos.urlencode(), content_type="application/x-www-form-urlencoded")
        self.assertIn("campos repetidos", str(respuesta.context["form"].errors))
        self.assertIsNone(respuesta.context["confirmacion"])

    def test_igualdad_pide_una_confirmacion_para_ambos_lados(self):
        respuesta = self.aviso(self.datos("(uv)" * 5 + "=" + "(uv)" * 5))
        total = estimar_expresion_web(respuesta.context["form"].cleaned_data["entrada"])
        self.assertEqual(len(total.partes), 18)
        self.assertEqual(respuesta.content.decode().count("data-confirmacion"), 1)
        with patch(EVALUADOR, return_value=RESULTADO) as evaluar:
            datos = self.datos("(uv)" * 5 + "=" + "(uv)" * 5, confirmacion=respuesta.context["confirmacion"]["firma"])
            self.assertIsNone(self.client.post(RUTA, datos).context["confirmacion"])
        evaluar.assert_called_once()

    def test_parte_pequena_no_estima_el_producto_costoso(self):
        simbolos = [*SIMBOLOS, matriz("B", [[1] * 10 for _ in range(10)])]
        for expresion, nodo in ((PESADA + "+B", "0.1"), (PESADA + "=B", "der:0")):
            with self.subTest(nodo=nodo):
                respuesta = self.client.post(RUTA, datos_simbolos(expresion, simbolos, nodo=nodo))
                self.assertFalse(respuesta.context["form"].errors)
                self.assertIsNone(respuesta.context["confirmacion"])
                self.assertEqual(respuesta.context["resultado"]["texto"], "B")

    def test_parte_pesada_conserva_nodo_en_continuar_y_su_firma(self):
        for expresion, nodo in ((PESADA + "+uv", "0.0"), (PESADA + "=uv", "izq:0")):
            with self.subTest(nodo=nodo):
                datos = self.datos(expresion, nodo=nodo)
                aviso = self.aviso(datos)
                self.assertContains(aviso, f'name="nodo" value="{nodo}"')
                datos["confirmacion"] = aviso.context["confirmacion"]["firma"]
                with patch(EVALUADOR, return_value=RESULTADO) as evaluar:
                    self.assertIsNone(self.client.post(RUTA, datos).context["confirmacion"])
                self.assertEqual(evaluar.call_args.args[0]["nodo"], nodo)
                datos.pop("nodo")
                self.aviso(datos)  # la firma parcial no sirve para toda la expresión

    def test_normales_del_curso_calculan_sin_confirmar(self):
        for filas, comunes, columnas in ((2, 2, 2), (3, 3, 3), (2, 3, 4)):
            a, b = [[1] * comunes for _ in range(filas)], [[2] * columnas for _ in range(comunes)]
            for expresion, simbolos in (("AB", [matriz("A", a), matriz("B", b)]),
                                      ("Ax", [matriz("A", a), {"nombre": "x", "tipo": "vector", "valor": [1] * comunes}]),
                                      ("A+B", [matriz("A", a), matriz("B", a)]),
                                      ("2A-B", [matriz("A", a), matriz("B", a)]),
                                      ("(A+B)ᵀ", [matriz("A", a), matriz("B", a)])):
                with self.subTest(expresion=expresion, dimensiones=(filas, comunes, columnas)):
                    respuesta = self.client.post(RUTA, datos_simbolos(expresion, simbolos))
                    self.assertFalse(respuesta.context["form"].errors)
                    self.assertIsNone(respuesta.context["confirmacion"])
                    self.assertIsNotNone(respuesta.context["resultado"])

    def test_formulario_declara_confirmacion_oculta_y_simbolicos_conservan_flujo(self):
        self.assertTrue(ExpresionMatricialForm().fields["confirmacion"].widget.is_hidden)
        simbolos = [matriz("A", [[1, 2], [3, 4]]), {"nombre": "x", "tipo": "vector_simbolico", "filas": 2}]
        respuesta = self.client.post(RUTA, datos_simbolos("Ax", simbolos))
        self.assertFalse(respuesta.context["form"].errors)
        self.assertIsNone(respuesta.context["confirmacion"])
        self.assertEqual(respuesta.context["resultado"]["tipo"], "vector_lineal")
