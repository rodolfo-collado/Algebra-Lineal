"""Cramer web: selección contextual, desarrollos compartidos y confirmación previa."""

import os
import re
from fractions import Fraction as F
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import SimpleTestCase

from backend.determinantes.presupuesto import estimar_determinante
from backend.ecuaciones_matriciales import matrices_de_cramer
from backend.presupuesto_computacional import Categoria
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms_determinantes import metodo_disponible, metodo_sugerido
from frontend.web.calculadora.forms_ecuaciones import EcuacionMatricialForm
from frontend.web.calculadora.opciones_ecuaciones import metodos_a_resolver
from frontend.web.calculadora.servicios_ecuaciones import confirmacion_pendiente, estimar_ecuacion_web, resolver_ecuacion_web
from tests.test_ecuaciones_cramer import A_CLASE, B_CLASE, A3, B3
from tests.test_ecuaciones_matriciales_web import RUTA, datos_ecuacion, texto_resultado
from tests.test_matrices_web import Contenido
from tests.test_presentacion_numerica import ValoresHTML
from tests.test_procedimiento_plegable import Estructura

SERVICIO = "frontend.web.calculadora.servicios_ecuaciones"


def entrada(a=A_CLASE, b=B_CLASE, metodo="directo_2x2"):
    return {"a": a, "b": b, "metodo": "cramer", "metodo_determinante": metodo}


class PruebasCramerWeb(SimpleTestCase):
    def test_catalogo_cramer_lleva_a_resolver_y_no_es_un_metodo_de_determinantes(self):
        self.assertEqual(catalogo.buscar_herramientas("regla de cramer"), (catalogo.ECUACIONES_MATRICIALES,))
        from frontend.web.calculadora.forms_determinantes import METODOS
        self.assertNotIn("cramer", dict(METODOS))

    def resolver(self, a=A_CLASE, b=B_CLASE, metodo="directo_2x2"):
        respuesta = self.client.post(RUTA, datos_ecuacion(a, b, "cramer", metodo_determinante=metodo))
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode()
        self.assertIn('id="resultado"', html)
        self.assertNotIn('role="alert"', html)
        estructura = Estructura(html)
        self.assertFalse(estructura.principal()["open"])
        self.assertEqual(estructura.paneles_finales, [{"dentro": 0}])
        return html, Contenido(html), texto_resultado(html), estructura

    def test_ejemplo_disclosures_anidados_y_vector_final_unico(self):
        html, doc, texto, estructura = self.resolver()
        self.assertEqual(doc.tablas["A₁"], [["6", "-2"], ["8", "4"]])
        self.assertEqual(doc.tablas["A₂"], [["3", "6"], ["-5", "8"]])
        self.assertEqual(doc.tablas["Vector solución x"], [["20"], ["27"]])
        self.assertEqual(doc.tablas["Producto Ax"], [["6"], ["8"]])
        self.assertIn("D = det(A) = 2", texto)
        self.assertIn("D₁ = det(A₁) = 40", texto)
        self.assertIn("D₂ = det(A₂) = 54", texto)
        self.assertIn("x₁ = D₁/D = 40 / 2 = 20", texto)
        self.assertIn("x₂ = D₂/D = 54 / 2 = 27", texto)
        self.assertIn("24 − (-16) = 40", texto)
        self.assertIn("24 − (-30) = 54", texto)
        calculos = [d for d in estructura.details if "Ver cálculo de" in d["summary"]]
        self.assertEqual([d["summary"].strip() for d in calculos], ["Ver cálculo de D", "Ver cálculo de D₁", "Ver cálculo de D₂"])
        self.assertTrue(all(d["nivel"] == 1 and not d["open"] for d in calculos))
        procedimiento, final = html.split('id="procedimiento"', 1)[1].split('class="panel panel-final"', 1)
        self.assertNotIn('aria-label="Vector solución x"', procedimiento)
        self.assertEqual(len(re.findall(r'<table[^>]*aria-label="Vector solución x"', final)), 1)
        self.assertNotIn('class="equations solution-list"', final)
        self.assertEqual(texto.count("Ax = b tiene solución única."), 1)
        ids = re.findall(r'id="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))

    def test_todos_los_desarrollos_son_los_compartidos(self):
        for metodo, contenido in (("sarrus", "Diagonales que suman"), ("cofactores", "Sumar los términos"),
                                   ("lu", "Las mismas operaciones llevan L a I"), ("reduccion", "Cómo cambió el determinante")):
            with self.subTest(metodo=metodo):
                _, doc, texto, estructura = self.resolver(A3, B3, metodo)
                self.assertEqual(doc.tablas["Vector solución x"], [["2"], ["-1"], ["3"]])
                self.assertEqual(texto.count(contenido), 4)
                self.assertEqual(len([d for d in estructura.details if "Ver cálculo de" in d["summary"]]), 4)
                r = resolver_ecuacion_web(entrada(A3, B3, metodo))
                self.assertEqual([r["cramer"]["principal"]["metodo"], *(e["determinante"]["metodo"] for e in r["cramer"]["reemplazos"])], [metodo] * 4)

    def test_singular_no_clasifica_y_lu_detenida_no_inventa_di(self):
        for b in ([3, 6], [3, 7]):
            with self.subTest(b=b):
                _, doc, texto, estructura = self.resolver([[1, 2], [2, 4]], b)
                self.assertIn("Regla de Cramer no aplicable: D = 0.", texto)
                self.assertIn("Usa Gauss o Gauss-Jordan", texto)
                self.assertNotIn("Ax = b no tiene solución", texto)
                self.assertNotIn("Ax = b tiene infinitas soluciones", texto)
                self.assertNotIn("Vector solución x", doc.tablas)
                self.assertEqual(len([d for d in estructura.details if "Ver cálculo de" in d["summary"]]), 1)
        _, doc, texto, _ = self.resolver([[2, 1], [1, 2]], [0, 3], "lu")
        self.assertIn("No se pudo completar Cramer", texto)
        self.assertIn("LU se detiene", texto)
        self.assertNotIn("Vector solución x", doc.tablas)
        self.assertNotIn("D₁ = det(A₁) =", texto)

    def test_disponibilidad_y_sugerencia_vienen_de_determinantes(self):
        for n in range(1, 11):
            form = EcuacionMatricialForm(initial={"filas": n, "columnas": n, "metodo": "cramer"})
            self.assertEqual(form["metodo_determinante"].value(), metodo_sugerido(n))
            opciones = [op for grupo in form.fields["metodo_determinante"].widget.optgroups("metodo_determinante", [metodo_sugerido(n)]) for op in grupo[1]]
            for opcion in opciones:
                self.assertEqual(not opcion["attrs"].get("disabled", False), metodo_disponible(opcion["value"], n))
                self.assertEqual(str(n) in opcion["attrs"]["data-sugerido"].split(","), opcion["value"] == metodo_sugerido(n))
        datos = datos_ecuacion(A_CLASE, B_CLASE, "cramer")
        form = EcuacionMatricialForm(datos)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["entrada"]["metodo_determinante"], "directo_2x2")

    def test_campos_repetidos_incluido_metodo_determinante_se_rechazan(self):
        from django.http import QueryDict
        datos = QueryDict("", mutable=True)
        datos.update(datos_ecuacion(A_CLASE, B_CLASE, "cramer", metodo_determinante="directo_2x2"))
        datos.appendlist("metodo_determinante", "reduccion")
        form = EcuacionMatricialForm(datos)
        self.assertFalse(form.is_valid())
        self.assertIn("campos repetidos", str(form.non_field_errors()))

    def test_rectangular_desactiva_cramer_y_post_manipulado_se_rechaza(self):
        datos = datos_ecuacion([[1, 2, 3]], [1], "cramer", metodo_determinante="cofactores")
        with patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
            respuesta = self.client.post(RUTA, datos)
        self.assertContains(respuesta, "Regla de Cramer requiere una matriz A cuadrada")
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertRegex(respuesta.content.decode(), r'name="metodo" value="cramer"[^>]*disabled')

    def test_aplicar_sin_js_a_rectangular_vuelve_a_gauss_jordan_sin_calcular(self):
        # Sin JS, Aplicar envía las celdas 2×2 con las dimensiones nuevas (2×3).
        datos = datos_ecuacion(A_CLASE, B_CLASE, "cramer", metodo_determinante="directo_2x2", columnas="3", ajustar="1")
        with patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
            respuesta = self.client.post(RUTA, datos)
        html = respuesta.content.decode()
        for ausente in ('id="resultado"', 'role="alert"', "Selecciona un método", "Antes de calcular"):
            self.assertNotIn(ausente, html)
        self.assertRegex(html, r'name="metodo" value="gauss_jordan"[^>]*checked')
        cramer = re.search(r'<input type="radio" name="metodo" value="cramer"[^>]*>', html)[0]
        self.assertIn("disabled", cramer)
        self.assertNotIn("checked", cramer)
        campos = Contenido(html).campos
        self.assertEqual([campos[f"celda_A_{i}_{j}"]["value"] for i in range(2) for j in range(2)], ["3", "-2", "-5", "4"])
        self.assertEqual([campos[f"celda_b_{i}_0"]["value"] for i in range(2)], ["6", "8"])
        self.assertEqual([campos[f"celda_A_{i}_2"].get("value", "") for i in range(2)], ["", ""])
        # Con A cuadrada, Aplicar conserva Cramer: solo cae la opción que el tamaño nuevo no admite.
        cuadrada = self.client.post(RUTA, datos_ecuacion(A_CLASE, B_CLASE, "cramer", metodo_determinante="directo_2x2", ajustar="1"))
        self.assertRegex(cuadrada.content.decode(), r'name="metodo" value="cramer"[^>]*checked')

    def test_metodos_invalidos_y_no_disponibles_rechazados_antes_de_calcular(self):
        for a, b, metodo in ((A_CLASE, B_CLASE, "inventado"), (A_CLASE, B_CLASE, "sarrus"),
                             (A3, B3, "directo_2x2"), ([[int(i == j) for j in range(7)] for i in range(7)], [1] * 7, "cofactores")):
            with self.subTest(metodo=metodo, n=len(a)), \
                    patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
                respuesta = self.client.post(RUTA, datos_ecuacion(a, b, "cramer", metodo_determinante=metodo))
                self.assertNotContains(respuesta, 'id="resultado"')
                self.assertContains(respuesta, 'id="id_metodo_determinante_error"')

    def test_aplicar_conserva_celdas_y_sanea_metodo_del_nuevo_tamano(self):
        respuesta = self.client.post(RUTA, datos_ecuacion(A3, B3, "cramer", metodo_determinante="directo_2x2", ajustar="1"))
        self.assertNotContains(respuesta, 'role="alert"')
        self.assertNotContains(respuesta, 'id="resultado"')
        doc = Contenido(respuesta.content.decode())
        self.assertEqual(doc.campos["celda_A_0_0"]["value"], "2")
        self.assertRegex(respuesta.content.decode(), r'name="metodo_determinante" value="sarrus"[^>]*checked')

    def test_exactitud_y_metadatos_decimal_tambien_en_el_procedimiento(self):
        html, doc, texto, _ = self.resolver([[3, 0], [0, -2]], [1, F(1, 6)])
        self.assertEqual(doc.tablas["Vector solución x"], [["1/3"], ["-1/12"]])
        valores = ValoresHTML(html)
        self.assertTrue(any(v["exacto"] == "1/3" and v["decimales"]["4"] == "0.3333" for v in valores.valores))
        self.assertTrue(any("x₂ = D₂/D" in v["exacto"] for v in valores.valores))
        self.assertIn('id="numeric-mode"', html)
        self.assertFalse(valores.ocultos)

    def test_presentacion_no_recalcula_y_comparar_sigue_siendo_dos_motores(self):
        with patch("frontend.web.calculadora.servicios_determinantes.calcular_determinante", side_effect=AssertionError("recalculó")):
            self.resolver()
        self.assertEqual(metodos_a_resolver("comparar"), ("gauss", "gauss_jordan"))
        r = resolver_ecuacion_web({"a": A_CLASE, "b": B_CLASE, "metodo": "comparar"})
        self.assertEqual([m["metodo"] for m in r["metodos"]], ["Gauss", "Gauss-Jordan"])
        self.assertNotIn("cramer", r)


class PruebasPresupuestoCramer(SimpleTestCase):
    def test_n_mas_uno_estimaciones_incluso_si_d_es_cero_y_costo_de_presentacion(self):
        for a, b in ((A_CLASE, B_CLASE), (A3, B3), ([[1, 2], [2, 4]], [3, 6])):
            metodo = metodo_sugerido(len(a))
            with self.subTest(n=len(a)), \
                    patch(f"{SERVICIO}.estimar_determinante", wraps=estimar_determinante) as estimador, \
                    patch("backend.ecuaciones_matriciales.calcular_determinante", side_effect=AssertionError("calculó")):
                estimacion = estimar_ecuacion_web(entrada(a, b, metodo))
            matrices = [a, *matrices_de_cramer(a, b)]
            self.assertEqual([c.args for c in estimador.call_args_list], [(m, metodo) for m in matrices])
            partes = [estimar_determinante(m, metodo) for m in matrices]
            self.assertEqual(list(estimacion.partes[:len(a) + 1]), partes)
            self.assertGreater(estimacion.procedimiento, sum(p.procedimiento for p in partes))
            self.assertEqual(estimacion.partes[-1].operacion, "producto")

    @patch(f"{SERVICIO}.categoria", return_value=Categoria.PESADA)
    def test_confirmar_cambios_en_a_b_y_metodo_invalidan_firma_y_cancelar_no_calcula(self, _):
        datos = datos_ecuacion(A_CLASE, B_CLASE, "cramer", metodo_determinante="directo_2x2")
        with patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
            respuesta = self.client.post(RUTA, datos)
        self.assertContains(respuesta, "Antes de calcular")
        self.assertContains(respuesta, "3 determinantes")
        self.assertContains(respuesta, "por Regla de Cramer")
        firma = re.search(r'name="confirmacion" value="([^"]+)"', respuesta.content.decode())[1]
        confirmado = self.client.post(RUTA, {**datos, "confirmacion": firma})
        self.assertContains(confirmado, "Ax = b tiene solución única.")
        for cambio in ({"celda_A_0_0": "4"}, {"celda_b_0_0": "7"}, {"metodo_determinante": "reduccion"}, {"confirmacion": "inventada"}):
            with self.subTest(cambio=cambio), patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
                self.assertContains(self.client.post(RUTA, {**datos, "confirmacion": firma, **cambio}), "Antes de calcular")
        with patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
            cancelado = self.client.post(RUTA, {**datos, "ajustar": "1"})
        self.assertNotContains(cancelado, "Antes de calcular")
        self.assertEqual(Contenido(cancelado.content.decode()).campos["celda_b_0_0"]["value"], "6")

    def test_confirmacion_real_por_cofactores_sin_forzar_categoria(self):
        a = [[2 if i == j else 1 for j in range(6)] for i in range(6)]
        with patch(f"{SERVICIO}.resolver_ecuacion_matricial", side_effect=AssertionError("calculó")):
            respuesta = self.client.post(RUTA, datos_ecuacion(a, [1] * 6, "cramer", metodo_determinante="cofactores"))
        self.assertContains(respuesta, "Antes de calcular")
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_rectangular_o_metodo_invalido_no_se_estiman_como_otro_metodo(self):
        for datos in (entrada([[1, 2]], [3], "reduccion"), entrada(metodo="inventado"), entrada(metodo="sarrus")):
            with self.subTest(datos=datos), self.assertRaises(ValueError):
                estimar_ecuacion_web(datos)

    def test_calculo_pequeno_no_pide_confirmacion(self):
        self.assertIsNone(confirmacion_pendiente(entrada()))
