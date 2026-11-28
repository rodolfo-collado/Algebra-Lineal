"""Resolución por lotes de Operaciones con matrices."""

from unittest.mock import patch

from django.conf import settings

from backend.operandos import nombre_matriz
from frontend.web.calculadora.servicios_expresiones import evaluar_expresion_web
from tests.test_matrices_web import Contenido, datos_simbolos, matriz
from tests.test_operaciones_matrices_unificadas import ContextoHTTP

RUTA = "/matrices/operaciones/"
EVALUADOR = "frontend.web.calculadora.views.evaluar_expresion_web"
EJERCICIO_56 = (
    matriz("A", [[2, 0], [-1, 3], [4, 2]]),
    matriz("B", [[-3, 5], [2, 1], [0, -4]]),
    matriz("C", [[1, 2], [0, -2], [3, 1]]),
)


def datos(expresiones, operandos=EJERCICIO_56, **extra):
    return datos_simbolos(expresiones[0], operandos, **{
        f"expresion_{indice}": texto for indice, texto in enumerate(expresiones[1:], 1)
    }, **extra)


class PruebasExpresionesMultiples(ContextoHTTP):
    def test_ejercicio_56_con_un_procedimiento_por_expresion(self):
        expresiones = ("A + B", "A - C", "A + B + C")
        with patch(EVALUADOR, wraps=evaluar_expresion_web) as evaluar:
            respuesta = self.client.post(RUTA, datos(expresiones))
        filas = respuesta.context["resultados"]
        self.assertEqual([fila["expresion"] for fila in filas], list(expresiones))
        self.assertEqual([fila["resultado"]["matriz"] for fila in filas], [
            [["-1", "5"], ["1", "4"], ["4", "-2"]],
            [["1", "-2"], ["-1", "5"], ["1", "1"]],
            [["0", "7"], ["1", "2"], ["7", "-1"]],
        ])
        self.assertEqual([[paso["texto"] for paso in fila["resultado"]["pasos"]] for fila in filas],
                         [["A + B"], ["A - C"], ["A + B", "A + B + C"]])
        self.assertEqual(evaluar.call_count, 3)
        self.assertTrue(all(llamada.args[0]["simbolos"] is evaluar.call_args.args[0]["simbolos"]
                            for llamada in evaluar.call_args_list))

    def test_rectangular_vector_escalar_fracciones_e_igualdad(self):
        operandos = (
            matriz("A", [["1/2", 0, 2], [0, "1/3", 0]]),
            {"nombre": "u", "tipo": "vector", "valor": [1, "3/2", 2]},
            {"nombre": "k", "tipo": "escalar", "valor": "1/3"},
        )
        respuesta = self.client.post(RUTA, datos(("Au", "kA", "kA = Ak"), operandos))
        vector, rectangular, igualdad = [fila["resultado"] for fila in respuesta.context["resultados"]]
        self.assertEqual(vector["igualdad"], "Au = [9/2, 1/2]")
        self.assertEqual(rectangular["matriz"], [["1/6", "0", "2/3"], ["0", "1/9", "0"]])
        self.assertTrue(igualdad["coincide"])

    def test_errores_locales_conservan_resultado_y_textos(self):
        expresiones = ("A +", "A - C", "A" * 401, "")
        respuesta = self.client.post(RUTA, datos(expresiones))
        error, valida, larga, vacia = respuesta.context["resultados"]
        self.assertTrue(error["error"])
        self.assertEqual(valida["resultado"]["matriz"][0], ["1", "-2"])
        self.assertIn("400 caracteres", larga["error"])
        self.assertIn("Escribe una expresión", vacia["error"])
        self.assertEqual([campo.value() for campo in respuesta.context["form"].expresiones], list(expresiones))
        self.assertContains(respuesta, 'id="resultado"')
        self.assertContains(respuesta, 'aria-invalid="true"')

    def test_acciones_sin_javascript_conservan_entradas_y_no_calculan(self):
        with patch(EVALUADOR, side_effect=AssertionError("Calculó durante la edición")):
            agregar = self.client.post(RUTA, datos(("A + B",), agregar_expresion="1"))
            quitar = self.client.post(RUTA, datos(("A + B", "A - C"), eliminar_expresion="0"))
        for respuesta, valores in ((agregar, ["A + B", ""]), (quitar, ["A - C"])):
            form = respuesta.context["form"]
            self.assertEqual([campo.value() or "" for campo in form.expresiones], valores)
            self.assertEqual(form["celda_0_0_0"].value(), "2")
            self.assertNotContains(respuesta, 'id="resultado"')

    def test_expresion_larga_invalida_no_se_convierte_al_mostrar_resultados(self):
        invalida = "9" * 5000 + "/3"
        respuesta = self.client.post(RUTA, datos(("1/3", invalida, "1/0"), []))
        self.assertEqual(respuesta.status_code, 200)
        valida, larga, division = respuesta.context["resultados"]
        self.assertEqual(valida["resultado"]["escalar"], "1/3")
        self.assertIn("400 caracteres", larga["error"])
        self.assertTrue(division["error"])
        self.assertEqual(respuesta.context["form"]["expresion_1"].value(), invalida)

    def test_compatibilidad_con_post_anterior(self):
        respuesta = self.client.post(RUTA, datos_simbolos("A - C", EJERCICIO_56))
        self.assertEqual(respuesta.context["resultados"][0]["resultado"], respuesta.context["resultado"])
        self.assertEqual(Contenido(respuesta.content.decode()).tablas["Resultado"][0], ["1", "-2"])
        self.assertContains(respuesta, 'id="procedimiento"')

    def test_subexpresion_se_dirige_al_arbol_de_su_fila(self):
        respuesta = self.client.post(RUTA, datos(("A+B", "A+B+C"), nodo="1|0.0"))
        primera, segunda = [fila["resultado"] for fila in respuesta.context["resultados"]]
        self.assertFalse(primera["parcial"])
        self.assertTrue(segunda["parcial"])
        self.assertEqual(segunda["matriz"], primera["matriz"])

    def test_costos_se_suman_y_la_firma_reconoce_el_orden(self):
        a = matriz("A", [[1] * 10 for _ in range(10)])
        expresiones = ("AAAAAA", "AAAAAAᵀ", "A+")
        for expresion in expresiones[:2]:
            with self.subTest(expresion=expresion), patch(EVALUADOR, return_value={"texto": expresion}):
                self.assertIsNone(self.client.post(RUTA, datos((expresion,), [a])).context["confirmacion"])
        with patch(EVALUADOR, side_effect=AssertionError("Calculó antes de confirmar")):
            aviso = self.client.post(RUTA, datos(expresiones, [a]))
            firma = aviso.context["confirmacion"]["firma"]
            otra = self.client.post(RUTA, datos(expresiones[::-1], [a], confirmacion=firma))
            self.assertNotEqual(otra.context["confirmacion"]["firma"], firma)
        with patch(EVALUADOR, return_value={"texto": "resultado"}) as evaluar:
            respuesta = self.client.post(RUTA, datos(expresiones, [a], confirmacion=firma))
        self.assertIsNone(respuesta.context["confirmacion"])
        self.assertEqual(evaluar.call_count, 2)

    def test_limites_acumulados_preservan_filas_dentro_del_presupuesto(self):
        a = matriz("A", [[1] * 10 for _ in range(10)])
        nueve = "+".join(["A"] * 9)
        ocho = "+".join(["A"] * 8)
        respuesta = self.client.post(RUTA, datos((nueve, nueve, ocho, "A+A", "1"), [a]))
        *primeras, excedida, ultima = respuesta.context["resultados"]
        self.assertTrue(all(fila["resultado"] for fila in primeras))
        self.assertIn("2700 entradas", excedida["error"])
        self.assertEqual(ultima["resultado"]["escalar"], "1")

    def test_limites_acumulados_de_operandos_y_operaciones(self):
        for expresion, limite in (("+".join(["1"] * 50), "150 apariciones"), ("-" * 49 + "1", "147 operaciones")):
            with self.subTest(limite=limite):
                respuesta = self.client.post(RUTA, datos([expresion] * 4, []))
                *primeras, excedida = respuesta.context["resultados"]
                self.assertTrue(all(fila["resultado"] for fila in primeras))
                self.assertIn(limite, excedida["error"])

    def test_envio_de_1000_campos_cabe_con_cinco_expresiones_y_nodo(self):
        operandos = [
            matriz(nombre_matriz(i), [[1] * (4 if i < 45 else 7) for _ in range(4 if i < 45 else 2)])
            for i in range(50)
        ]
        envio = datos(["A"] * 5, operandos, metodo="columnas", csrfmiddlewaretoken="token", confirmacion="", nodo="0|0")
        self.assertEqual(len(envio), settings.DATA_UPLOAD_MAX_NUMBER_FIELDS)
        respuesta = self.client.post(RUTA, envio)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.context["resultados"]), 5)
        self.assertFalse(respuesta.context["form"].errors)

    def test_combinaciones_y_determinaciones_tienen_procedimientos_propios(self):
        operandos = (
            {"nombre": "A", "tipo": "matriz_desconocida", "filas": 2, "columnas": 2},
            {"nombre": "x", "tipo": "vector_simbolico", "filas": 2},
            {"nombre": "w", "tipo": "vector_lineal", "valor": ["1/2 x1", "x2"]},
            {"nombre": "u", "tipo": "vector", "valor": [1, 0]},
            {"nombre": "v", "tipo": "vector", "valor": [0, 1]},
            {"nombre": "b", "tipo": "vector", "valor": [2, 3]},
        )
        respuesta = self.client.post(RUTA, datos(("Ax = w", "x1 u + x2 v = b"), operandos))
        determinacion, combinacion = [fila["resultado"] for fila in respuesta.context["resultados"]]
        self.assertEqual(determinacion["matriz"], [["1/2", "0"], ["0", "1"]])
        self.assertEqual(combinacion["modo"], "combinacion")
        for identificador in ("procedimiento-1", "procedimiento-2", "combination-result-title-2", "numeric-mode"):
            self.assertContains(respuesta, f'id="{identificador}"', count=1)

    def test_rechaza_indices_ajenos_y_tope_de_expresiones(self):
        for nombre in ("expresion_2", "expresion_5"):
            with self.subTest(nombre=nombre), patch(EVALUADOR, side_effect=AssertionError("POST inválido")):
                respuesta = self.client.post(RUTA, datos(("A",), **{nombre: "B"}))
            self.assertTrue(respuesta.context["form"].non_field_errors())
