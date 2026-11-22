import json
import re

from django.test import SimpleTestCase
from django.test.utils import setup_test_environment, teardown_test_environment
from django.urls import resolve, reverse

from frontend.web.calculadora import catalogo
from tests.test_ecuaciones_matriciales_web import RUTA as RUTA_DIRECTOS, datos_ecuacion
from tests.test_navegacion import Documento
from tests.test_sistemas_iterativos import CLASE_A, CLASE_B, PRACTICA_A, PRACTICA_B


RUTA = "/metodos-numericos/metodos-iterativos/"


class SistemasIterativosWebTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_test_environment()
        cls.addClassCleanup(teardown_test_environment)

    def test_ruta_area_migas_y_navegacion_entre_familias(self):
        self.assertEqual(reverse("calculadora:metodos-iterativos"), RUTA)
        self.assertEqual(catalogo.herramienta_por_ruta(resolve(RUTA)), catalogo.METODOS_ITERATIVOS)
        area = "/areas/metodos-numericos/"
        familias = (catalogo.METODOS_CERRADOS, catalogo.METODOS_ABIERTOS, catalogo.METODOS_ITERATIVOS)
        for ruta in (area, *[familia.ruta for familia in familias]):
            with self.subTest(ruta=ruta):
                pagina = self.client.get(ruta)
                for familia in familias:
                    self.assertContains(pagina, f'href="{familia.ruta}"')
        respuesta = self.client.get(RUTA)
        migas = Documento(respuesta).enlaces_en("Ruta de navegación")
        self.assertEqual([miga["href"] for miga in migas], ["/", area, f"{area}#sistemas-lineales"])
        self.assertContains(respuesta, f'href="{RUTA}" aria-current="page"')
        self.assertEqual(respuesta.context["form"]["metodo"].value(), "jacobi")
        self.assertNotContains(respuesta, "metodo_determinante")

    def test_ax_b_enlaza_a_iterativos_y_solo_acepta_metodos_directos(self):
        respuesta = self.client.get(RUTA_DIRECTOS)
        self.assertContains(respuesta, f'<a class="text-link" href="{RUTA}">Métodos iterativos</a>', html=True)
        self.assertNotContains(respuesta, 'name="inicial_iterativo"')
        self.assertNotContains(respuesta, 'value="jacobi"')
        directa = self.client.post(RUTA_DIRECTOS, datos_ecuacion([[2]], [4], "gauss_jordan"))
        self.assertContains(directa, "Solución única")
        intento = self.client.post(RUTA_DIRECTOS, datos_ecuacion([[2]], [4], "jacobi"))
        self.assertContains(intento, "Selecciona un método válido.")
        self.assertNotContains(intento, 'id="resultado"')

    def test_aplicar_sin_javascript_reconstruye_la_matriz_y_conserva_opciones(self):
        respuesta = self.client.post(RUTA, {
            "ajustar": "1", "filas": "3", "columnas": "3", "metodo": "gauss_seidel",
            "celda_A_0_0": "5", "inicial_iterativo": "1 2 3",
            "tolerancia_iterativa": "0.0002", "max_iteraciones": "3",
        })
        form = respuesta.context["form"]
        self.assertEqual(form["celda_A_0_0"].value(), "5")
        self.assertEqual(form["celda_A_2_2"].value(), "")
        self.assertEqual(form["metodo"].value(), "gauss_seidel")
        self.assertEqual(form["inicial_iterativo"].value(), "1 2 3")
        self.assertEqual(form["tolerancia_iterativa"].value(), "0.0002")
        self.assertEqual(form["max_iteraciones"].value(), "3")
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_catalogo_y_ejemplos_preparan_ax_b_sin_resolver(self):
        for consulta in ("Jacobi", "Gauss-Seidel", "Gauss Seidel"):
            self.assertEqual(catalogo.buscar_herramientas(consulta), (catalogo.METODOS_ITERATIVOS,))
        for slug, a, b, limite in (
            ("clase", CLASE_A, CLASE_B, 100),
            ("diapositiva-28", PRACTICA_A, PRACTICA_B, 3),
        ):
            with self.subTest(slug=slug):
                respuesta = self.client.get(RUTA, {"ejemplo": slug})
                form = respuesta.context["form"]
                self.assertEqual(form["metodo"].value(), "comparar_iterativos")
                self.assertEqual(form["max_iteraciones"].value(), limite)
                self.assertEqual(form["tolerancia_iterativa"].value(), "0.0001")
                for i, fila in enumerate(a):
                    for j, coef in enumerate(fila):
                        self.assertEqual(form[f"celda_A_{i}_{j}"].value(), str(coef))
                    self.assertEqual(form[f"celda_b_{i}_0"].value(), str(b[i]))
                self.assertNotContains(respuesta, 'id="resultado"')

    def test_comparar_muestra_ambos_metodos_en_un_resultado(self):
        respuesta = self.client.post(RUTA, datos_ecuacion(CLASE_A, CLASE_B, "comparar_iterativos"))
        jacobi, seidel = respuesta.context["iterativos"]
        self.assertEqual((jacobi["final"]["k"], seidel["final"]["k"]), (15, 6))
        self.assertContains(respuesta, 'data-estado="convergio"', count=2)
        self.assertContains(respuesta, 'data-dominancia="estricta"')
        self.assertContains(respuesta, 'aria-controls="desarrollo-jacobi"')
        self.assertContains(respuesta, 'aria-controls="desarrollo-gauss_seidel"')
        self.assertContains(respuesta, "Escala logarítmica", count=2)
        self.assertNotContains(respuesta, "Solución única")

    def test_tabla_json_y_despejes_iniciales_coinciden(self):
        respuesta = self.client.post(RUTA, datos_ecuacion(CLASE_A, CLASE_B, "gauss_seidel"))
        html = respuesta.content.decode()
        json_script = re.search(r'<script id="gauss_seidel" type="application/json">(.*?)</script>', html)
        filas = json.loads(json_script[1])
        resultado = respuesta.context["iterativos"][0]
        self.assertEqual(filas, resultado["filas"])
        fila = re.search(r'<tr data-iteracion="2">(.*?)</tr>', html, re.S)
        self.assertEqual(re.findall(r"<td>(.*?)</td>", fila[1]), [
            *filas[2]["x"], filas[2]["cambio"], filas[2]["norma"],
        ])
        desarrollo = resultado["desarrollo"][1]
        self.assertEqual(desarrollo["valor"], filas[1]["x"][1])
        self.assertEqual([(t["origen"], t["valor"]) for t in desarrollo["terminos"]], [
            ("nueva", filas[1]["x"][0]), ("anterior", filas[0]["x"][2]), ("anterior", filas[0]["x"][3]),
        ])
        self.assertContains(respuesta, "x₂ nueva")
        self.assertContains(respuesta, "x₄ anterior")

    def test_practica_muestra_ultimas_aproximaciones_al_agotar_el_limite(self):
        respuesta = self.client.post(RUTA, datos_ecuacion(
            PRACTICA_A, PRACTICA_B, "comparar_iterativos", max_iteraciones="3",
        ))
        self.assertContains(respuesta, "No convergió en 3 iteraciones", count=2)
        for resultado in respuesta.context["iterativos"]:
            self.assertEqual(resultado["final"]["k"], 3)
            self.assertEqual(len(resultado["filas"]), 4)

    def test_parametros_validos_y_aviso_no_dominante(self):
        respuesta = self.client.post(RUTA, datos_ecuacion(
            [[1, 2], [1, 4]], [3, 5], "jacobi",
            inicial_iterativo="1/2 3/2", tolerancia_iterativa="0.0002", max_iteraciones="250",
        ))
        self.assertContains(respuesta, 'data-dominancia="no-estricta"')
        self.assertContains(respuesta, 'data-estado="convergio"')
        resultado = respuesta.context["iterativos"][0]
        self.assertEqual(resultado["filas"][0]["x"], ["0.5", "1.5"])
        self.assertEqual(resultado["tolerancia"], "0.0002")

    def test_entradas_invalidas_preservan_formulario_y_mensajes(self):
        for a, extra, mensaje in (
            ([[1, 2, 3], [4, 5, 6]], {}, "requieren una matriz A cuadrada"),
            ([[0, 1], [1, 1]], {}, "diagonal de la fila 1 es cero"),
            ([[2, 1], [1, 2]], {"max_iteraciones": "501"}, "Escribe un entero de 1 a 500"),
            ([[2, 1], [1, 2]], {"tolerancia_iterativa": "-1"}, "La tolerancia debe ser positiva"),
            ([[2, 1], [1, 2]], {"inicial_iterativo": "1"}, "Escribe 2 componentes"),
        ):
            with self.subTest(extra=extra, mensaje=mensaje):
                respuesta = self.client.post(RUTA, datos_ecuacion(a, [1, 1], "jacobi", **extra))
                self.assertContains(respuesta, mensaje)
                self.assertNotContains(respuesta, 'id="resultado"')
                self.assertEqual(respuesta.context["form"]["metodo"].value(), "jacobi")
                self.assertEqual(respuesta.context["form"]["celda_b_0_0"].value(), "1")

    def test_residuo_comprueba_los_coeficientes_exactos_de_la_entrada(self):
        respuesta = self.client.post(RUTA, datos_ecuacion(
            [[1]], [10_000_000_000_000_001], "jacobi", max_iteraciones="3",
        ))
        self.assertContains(respuesta, 'data-estado="limite"')
        resultado = respuesta.context["iterativos"][0]
        self.assertEqual(resultado["residuo_final"], ["1"])
        self.assertEqual(resultado["final"]["norma"], "1")

    def test_rango_sin_primera_actualizacion_muestra_vector_inicial(self):
        respuesta = self.client.post(RUTA, datos_ecuacion(
            [[f"1/{10**99}", 0], [0, f"1/{10**99}"]], [10**99, -(10**99)], "gauss_seidel",
            inicial_iterativo="0 0", max_iteraciones="1",
        ))
        self.assertContains(respuesta, 'data-estado="limite"')
        self.assertContains(respuesta, "Ver sustituciones")

        # Los literales caben en el presupuesto, pero el crecimiento desborda en la vuelta 1.
        respuesta = self.client.post(RUTA, datos_ecuacion(
            [[f"1/{10**99}", 10**99], [10**99, f"1/{10**99}"]], [10**99, 10**99], "gauss_seidel",
        ))
        self.assertContains(respuesta, 'data-estado="rango"')
        self.assertContains(respuesta, "En la iteración 1 se superó el rango numérico.")
        self.assertContains(respuesta, "Vector inicial")
        self.assertNotContains(respuesta, "Ver sustituciones")
