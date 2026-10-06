"""P27.4: errores accesibles y confirmaciones sin cambiar el cálculo ni el POST."""

from django.test import SimpleTestCase

from tests.test_teclado import Pagina
from tests.test_matrices_web import datos_matrices
from tests.test_ecuaciones_matriciales_web import datos_ecuacion
from tests.test_matriz_inversa_web import datos_inversa
from tests.test_vectores_web import datos_vectores
from tests.test_presupuesto_expresiones_web import PESADA, SIMBOLOS
from tests.test_matrices_web import datos_simbolos


class PruebasFeedback(SimpleTestCase):
    def test_campos_invalidos_asociados_en_las_siete_herramientas(self):
        casos = [
            ("/matrices/reduccion/", {"sistema": "", "metodo": "gauss"}, "sistema"),
            ("/matrices/ecuaciones/", datos_ecuacion(celda_A_0_0=""), "celda_A_0_0"),
            ("/matrices/inversa/", datos_inversa(celda_A_0_0=""), "celda_A_0_0"),
            ("/matrices/operaciones/", datos_matrices(""), "expresion"),
            ("/vectores/operaciones/", datos_vectores("suma", u=[1, "x"], v=[1, 2]), "u_1"),
            ("/bases/conversion/", {"numero": "1", "base_origen": "10"}, "bases_destino"),
            ("/romanos/conversion/", {"numero": "IIII", "direccion": "romano_a_decimal"}, "numero"),
        ]
        for ruta, datos, nombre in casos:
            with self.subTest(ruta=ruta):
                respuesta = self.client.post(ruta, datos)
                self.assertEqual(respuesta.status_code, 200)
                pagina = Pagina(respuesta.content.decode())
                campos = [e for e in pagina.elementos if e.get("name") == nombre]
                self.assertTrue(campos)
                for campo in campos:
                    self.assertEqual(campo.get("aria-invalid"), "true")
                    self.assertIn(f"id_{nombre}_error", campo["aria-describedby"].split())
                self.assertContains(respuesta, f'data-error-field="id_{nombre}"', count=1)
                self.assertNotContains(respuesta, 'id="resultado"')
                self.assertContains(respuesta, "data-respuesta-errores", count=1)

    def test_ayuda_existente_no_se_pierde_al_asociar_error(self):
        respuesta = self.client.post("/romanos/conversion/", {"numero": "0", "direccion": "decimal_a_romano"})
        numero = next(e for e in Pagina(respuesta.content.decode()).elementos if e.get("name") == "numero")
        self.assertEqual(numero["aria-describedby"].split(), ["numero-ayuda", "id_numero_error"])

    def test_error_general_unico_sin_resumen_duplicado(self):
        respuesta = self.client.post("/romanos/conversion/", {"numero": "4", "direccion": "decimal_a_romano", "ajeno": "1"})
        self.assertContains(respuesta, 'class="alert error" role="alert" tabindex="-1" data-error-general', count=1)
        self.assertContains(respuesta, "El envío incluye campos que no forman parte del formulario.", count=1)
        self.assertNotContains(respuesta, "Revisa los campos indicados")

    def test_error_de_matriz_completa_se_presenta_una_vez_junto_al_grupo(self):
        respuesta = self.client.post("/matrices/inversa/", {k: v for k, v in datos_inversa().items() if k != "celda_A_0_0"})
        self.assertContains(respuesta, 'data-error-group="inverse-matrix"', count=1)
        self.assertNotContains(respuesta, "data-error-field")
        html = respuesta.content.decode()
        self.assertGreater(html.index('id="errores-grupo"'), html.index('data-inverse-entry'))
        self.assertEqual(html.count('role="alert"'), 1)

    def test_confirmacion_antes_de_calcular_con_firma_y_operacion(self):
        respuesta = self.client.post("/matrices/operaciones/", datos_simbolos(PESADA, SIMBOLOS, metodo="comparar"))
        html = respuesta.content.decode()
        self.assertContains(respuesta, "data-confirmacion", count=1)
        self.assertLess(html.index("data-confirmacion"), html.index('class="workspace-actions"'))
        self.assertContains(respuesta, f"<strong>{PESADA}</strong>")
        self.assertContains(respuesta, "El cálculo completo todavía no se ha ejecutado.")
        self.assertRegex(html, r'data-calculo name="confirmacion" value="[0-9a-f]{64}"')
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_get_limpio_sin_error_ni_foco_solicitado(self):
        for ruta in ("/bases/conversion/", "/matrices/operaciones/", "/matrices/inversa/"):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertNotContains(respuesta, "data-respuesta-errores")
                self.assertNotContains(respuesta, "data-error-field")
                self.assertContains(respuesta, "calculadora/feedback.js", count=1)

    def test_capitalizacion_conserva_nombre_definido_por_usuario(self):
        respuesta = self.client.post("/matrices/operaciones/", datos_matrices("MiA+B", nombre_0="MiA", celda_0_0_0=""))
        self.assertContains(respuesta, "Completa matriz MiA, fila 1, columna 1.")
