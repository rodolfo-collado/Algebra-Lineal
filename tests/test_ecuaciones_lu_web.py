"""Contratos web de LU: dos etapas, resultado único y presupuesto previo."""

import os
import re
from fractions import Fraction as F
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import SimpleTestCase

from backend.presupuesto_computacional import Categoria, estimar_gauss_jordan, estimar_lu, perfil_numerico
from frontend.web.calculadora.forms_ecuaciones import EcuacionMatricialForm
from frontend.web.calculadora.opciones_ecuaciones import metodos_a_resolver
from frontend.web.calculadora.servicios_ecuaciones import estimar_ecuacion_web, resolver_ecuacion_web
from tests.test_ecuaciones_lu import A_CLASE, B_CLASE, X_CLASE, Y_CLASE
from tests.test_ecuaciones_matriciales_web import RUTA, datos_ecuacion, texto_resultado
from tests.test_matrices_web import Contenido
from tests.test_presentacion_numerica import ValoresHTML
from tests.test_procedimiento_plegable import Estructura

SERVICIO = "frontend.web.calculadora.servicios_ecuaciones"


class PruebasProcedimientoLU(SimpleTestCase):
    def resolver(self, a=A_CLASE, b=B_CLASE):
        respuesta = self.client.post(RUTA, datos_ecuacion(a, b, metodo="lu"))
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode()
        self.assertIn('id="resultado"', html)
        self.assertNotIn('role="alert"', html)
        estructura = Estructura(html)
        self.assertFalse(estructura.principal()["open"])
        self.assertEqual(estructura.paneles_finales, [{"dentro": 0}])
        self.assertLess(html.index('id="procedimiento"'), html.index("panel-final"))
        return html, Contenido(html), texto_resultado(html)

    def test_ejemplo_muestra_l_u_y_las_dos_reducciones_completas(self):
        html, doc, texto = self.resolver()
        self.assertIn("1 · Factorización A = LU", texto)
        self.assertIn("2 · Resolver Ly = b", texto)
        self.assertIn("3 · Resolver Ux = y", texto)
        resultado = resolver_ecuacion_web({"a": A_CLASE, "b": B_CLASE, "metodo": "lu"})
        self.assertEqual(doc.tablas["Matriz L"], resultado["lu"]["l"])
        self.assertEqual(doc.tablas["Matriz U"], resultado["lu"]["u"])
        for etapa in resultado["lu"]["etapas"]:
            self.assertEqual(doc.tablas[etapa["inicial"]], etapa["matriz_inicial"])
            self.assertEqual(doc.tablas[etapa["final"]], etapa["matriz_final"])
            for paso in etapa["pasos"]:
                self.assertIn(paso["operacion"], texto)
            self.assertEqual(html.count('class="step"'), sum(len(e["pasos"]) for e in resultado["lu"]["etapas"]))
        self.assertEqual([fila[-1] for fila in doc.tablas["[I | y]"]], list(map(str, Y_CLASE)))
        self.assertEqual([fila[-1] for fila in doc.tablas["[I | x]"]], list(map(str, X_CLASE)))
        self.assertEqual(doc.tablas["Vector solución x"], [[str(v)] for v in X_CLASE])
        self.assertEqual(texto.count("Ax = b tiene solución única."), 1)
        procedimiento = html[html.index('id="procedimiento"'):html.index("panel-final")]
        self.assertNotIn('aria-label="Vector solución x"', procedimiento)
        self.assertNotIn("Sustitución regresiva", texto)
        self.assertIn("Antes", texto)
        self.assertIn("Después", texto)
        ids = re.findall(r'id="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_aplicable_no_afirma_que_el_sistema_no_tiene_solucion(self):
        for a in ([[0, 1], [1, 0]], [[1, 1, 0], [1, 1, 1], [0, 1, 1]]):
            with self.subTest(a=a):
                html, doc, texto = self.resolver(a, [1] * len(a))
                self.assertIn("LU sin permutaciones no aplicable", texto)
                self.assertIn("Usa Gauss o Gauss-Jordan", texto)
                self.assertNotIn("Ax = b no tiene solución", texto)
                self.assertNotIn("Vector solución x", doc.tablas)
                self.assertNotIn("[I | x]", doc.tablas)
                self.assertIn("Matriz al detener LU", doc.tablas)
                self.assertNotIn('id="interpretacion"', html)

    def test_singular_muestra_la_reduccion_real_y_su_clasificacion(self):
        for b, enunciado in (([3, 6], "infinitas soluciones"), ([3, 7], "no tiene solución")):
            with self.subTest(b=b):
                _, doc, texto = self.resolver([[1, 2], [2, 4]], b)
                self.assertIn(enunciado, texto)
                self.assertIn("U es singular", texto)
                self.assertIn("Forma reducida de [U | y]", doc.tablas)
                self.assertNotIn("[I | x]", doc.tablas)
                self.assertNotIn("Vector solución x", doc.tablas)

    def test_rectangulares_rechazadas_y_aplicar_conserva_el_metodo(self):
        datos = datos_ecuacion([[1, 2, 3]], [1], metodo="lu")
        with patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
            form = EcuacionMatricialForm(datos)
            self.assertFalse(form.is_valid())
            self.assertIn("requiere una matriz A cuadrada", str(form.errors["metodo"]))
            respuesta = self.client.post(RUTA, datos)
            self.assertContains(respuesta, "Para matrices rectangulares usa Gauss o Gauss-Jordan")
            self.assertNotContains(respuesta, 'id="resultado"')
            aplicar = self.client.post(RUTA, {**datos, "ajustar": "1"})
            self.assertNotContains(aplicar, 'role="alert"')
            self.assertRegex(aplicar.content.decode(), r'name="metodo" value="lu"[^>]*checked')

    def test_comparar_sigue_siendo_solo_gauss_y_jordan(self):
        self.assertEqual(metodos_a_resolver("comparar"), ("gauss", "gauss_jordan"))
        resultado = resolver_ecuacion_web({"a": A_CLASE, "b": B_CLASE, "metodo": "comparar"})
        self.assertEqual([m["metodo"] for m in resultado["metodos"]], ["Gauss", "Gauss-Jordan"])
        self.assertNotIn("lu", resultado)

    def test_fracciones_exactas_y_metadatos_decimal_en_ambas_etapas(self):
        html, doc, _ = self.resolver([[3, 0], [-1, -2]], [1, F(1, 6)])
        self.assertEqual(doc.tablas["Vector solución x"], [["1/3"], ["-1/4"]])
        valores = ValoresHTML(html)
        self.assertIn('id="numeric-mode"', html)
        self.assertTrue(any(v["exacto"] == "1/3" and v["decimales"]["4"] == "0.3333" for v in valores.valores))
        self.assertTrue(any("F2 = F2 + (1/3)F1" in v["exacto"] for v in valores.valores))
        self.assertFalse(valores.ocultos)


class PruebasPresupuestoLU(SimpleTestCase):
    def test_estima_las_tres_etapas_y_comprobacion_sin_ejecutarlas(self):
        entrada = {"a": A_CLASE, "b": B_CLASE, "metodo": "lu"}
        with patch("backend.ecuaciones_matriciales.factorizar_lu", side_effect=AssertionError("factorizó")), \
                patch("backend.ecuaciones_matriciales.aplicar_gauss_jordan", side_effect=AssertionError("redujo")):
            estimacion = estimar_ecuacion_web(entrada)
        self.assertEqual([e.operacion for e in estimacion.partes], ["lu", "gauss_jordan", "gauss_jordan", "producto"])
        self.assertEqual(estimacion.partes[0], estimar_lu(4, 4, perfil=perfil_numerico(A_CLASE)))
        self.assertEqual([e.dimensiones for e in estimacion.partes], [(4, 4), (4, 5), (4, 5), (4, 4, 1)])
        self.assertGreaterEqual(estimacion.procedimiento, 2 * 4 * 5 * 2 * estimar_gauss_jordan(4, 5, columnas_pivote=4).pasos)
        for e in estimacion.partes[1:3]:
            self.assertEqual(e.pasos, 16)
        self.assertLess(estimar_ecuacion_web({"a": [[1]], "b": [1], "metodo": "lu"}).calculo, estimacion.calculo)
        with self.assertRaisesRegex(ValueError, "cuadrada"):
            estimar_ecuacion_web({"a": [[1, 2]], "b": [1], "metodo": "lu"})

    @patch(f"{SERVICIO}.categoria", return_value=Categoria.PESADA)
    def test_confirmacion_previa_continuar_cambios_y_cancelar(self, _):
        datos = datos_ecuacion(A_CLASE, B_CLASE, metodo="lu")
        with patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
            respuesta = self.client.post(RUTA, datos)
        self.assertContains(respuesta, "Antes de calcular")
        self.assertNotContains(respuesta, 'id="resultado"')
        html = respuesta.content.decode()
        firma = re.search(r'name="confirmacion" value="([^"]+)"', html)[1]
        self.assertEqual(Contenido(html).campos["celda_b_0_0"]["value"], "-9")
        confirmado = self.client.post(RUTA, {**datos, "confirmacion": firma})
        self.assertContains(confirmado, "Ax = b tiene solución única.")
        for cambio in ({"celda_A_0_0": "4"}, {"celda_b_0_0": "-10"}, {"confirmacion": "inventada"}):
            with self.subTest(cambio=cambio), patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
                respuesta = self.client.post(RUTA, {**datos, "confirmacion": firma, **cambio})
                self.assertContains(respuesta, "Antes de calcular")
        with patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
            cancelado = self.client.post(RUTA, {**datos, "ajustar": "1"})
        self.assertNotContains(cancelado, "Antes de calcular")
        self.assertEqual(Contenido(cancelado.content.decode()).campos["celda_b_0_0"]["value"], "-9")

    def test_un_caso_grande_pide_confirmacion_sin_forzar_categoria(self):
        a = [[1 if i == j else 0 for j in range(10)] for i in range(10)]
        with patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
            respuesta = self.client.post(RUTA, datos_ecuacion(a, [1] * 10, metodo="lu"))
        self.assertContains(respuesta, "Antes de calcular")
