import json
import re
from html import unescape

from django.test import SimpleTestCase
from django.test.utils import setup_test_environment, teardown_test_environment
from django.urls import resolve, reverse

from backend.sistemas_iterativos import resolver_iterativo
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.presentacion_numerica import representar_flotante
from frontend.web.calculadora.servicios_iterativos import EJEMPLOS
from tests.test_ecuaciones_matriciales_web import RUTA as RUTA_DIRECTOS, datos_ecuacion
from tests.test_navegacion import Documento
from tests.test_sistemas_iterativos import CLASE_A, CLASE_B, PRACTICA_A, PRACTICA_B


RUTA = "/metodos-numericos/metodos-iterativos/"


def fila_html(html, metodo, k):
    """Celdas (data-valor) de la fila k en la tabla del método."""
    articulo = html[html.index(f'data-iterativo="{metodo}"'):]
    fila = re.search(rf'<tr data-iteracion="{k}"[^>]*>(.*?)</tr>', articulo, re.S)[1]
    return re.findall(r'<td data-valor="([^"]*)">', fila)


class SistemasIterativosWebTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_test_environment()
        cls.addClassCleanup(teardown_test_environment)

    def resolver(self, a, b, metodo, **extra):
        return self.client.post(RUTA, datos_ecuacion(a, b, metodo, **extra))

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
        # Ax = b directo no ofrece ejemplos en su menú de edición.
        self.assertNotContains(respuesta, "data-ejemplos-menu")
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

    def test_ejemplos_en_el_menu_de_edicion_y_sin_javascript(self):
        for consulta in ("Jacobi", "Gauss-Seidel", "Gauss Seidel"):
            self.assertEqual(catalogo.buscar_herramientas(consulta), (catalogo.METODOS_ITERATIVOS,))
        pagina = self.client.get(RUTA)
        menu = pagina.content.decode().split('id="menu-edicion-template"')[1]
        self.assertIn("Cargar ejemplo · sustituye el sistema", menu)
        noscript = re.search(r"<noscript>(.*?)</noscript>", pagina.content.decode(), re.S)[1]
        for clave, (titulo, *_datos) in EJEMPLOS.items():
            self.assertIn(f'href="?ejemplo={clave}">{titulo}</a>', menu)
            self.assertIn(f'href="?ejemplo={clave}">{titulo}</a>', noscript)
        # Ya no hay un desplegable visible de ejemplos en el formulario.
        self.assertNotContains(pagina, "Ejemplos de Jacobi y Gauss-Seidel")
        for clave, (_titulo, a, b) in EJEMPLOS.items():
            with self.subTest(clave=clave):
                form = self.client.get(RUTA, {"ejemplo": clave}).context["form"]
                self.assertEqual(form["metodo"].value(), "comparar_iterativos")
                self.assertEqual(form["max_iteraciones"].value(), 3 if clave == "diapositiva-28" else 100)
                self.assertEqual(form["tolerancia_iterativa"].value(), "0.0001")
                for i, fila in enumerate(a):
                    for j, coef in enumerate(fila):
                        self.assertEqual(form[f"celda_A_{i}_{j}"].value(), str(coef))
                    self.assertEqual(form[f"celda_b_{i}_0"].value(), str(b[i]))
        self.assertEqual(EJEMPLOS["clase"][1:], (tuple(map(tuple, CLASE_A)), tuple(CLASE_B)))
        self.assertEqual(EJEMPLOS["diapositiva-28"][1:], (tuple(map(tuple, PRACTICA_A)), tuple(PRACTICA_B)))

    def test_comparar_reune_ambos_metodos_con_las_mismas_condiciones(self):
        respuesta = self.resolver(CLASE_A, CLASE_B, "comparar_iterativos")
        resultado = respuesta.context["iterativos"]
        jacobi, seidel = resultado["metodos"]
        self.assertEqual((jacobi["final"]["k"], seidel["final"]["k"]), (15, 6))
        self.assertEqual(resultado["titulo"], "Gauss-Seidel converge en 6 y Jacobi en 15 iteraciones")
        self.assertContains(respuesta, "Mismas condiciones para ambos: x⁽⁰⁾ = (0, 0, 0, 0), ε = 0.0001, hasta 100 iteraciones.")
        self.assertContains(respuesta, 'data-estado="convergio"', count=4)  # tabla comparativa + zona de estudio
        self.assertContains(respuesta, 'data-dominancia="estricta"')
        self.assertContains(respuesta, 'data-grafica="comparacion"')
        self.assertContains(respuesta, 'data-mostrar="jacobi" aria-pressed="true"')
        self.assertContains(respuesta, 'data-mostrar="gauss_seidel" aria-pressed="false"')
        self.assertContains(respuesta, 'data-grafica="variables"', count=2)
        self.assertContains(respuesta, 'data-grafica="error"', count=2)
        self.assertContains(respuesta, "data-numeric-controls")
        for script in ("numeros.js", "plotly-basic-4.1.2.min.js", "sistemas_iterativos.js"):
            self.assertContains(respuesta, script)
        self.assertNotContains(respuesta, "Solución única")

    def test_tabla_y_sustituciones_leen_las_iteraciones_del_motor(self):
        respuesta = self.resolver(CLASE_A, CLASE_B, "gauss_seidel")
        html = respuesta.content.decode()
        motor = resolver_iterativo(CLASE_A, CLASE_B, "gauss_seidel")
        for paso in motor.iteraciones:
            self.assertEqual(fila_html(html, "gauss_seidel", paso.k)[:4], [repr(x) for x in paso.x])
        # x₂⁽¹⁾ en Gauss-Seidel: x₁ ya es nuevo; x₃ y x₄ siguen siendo de x⁽⁰⁾.
        despeje = respuesta.context["iterativos"]["metodos"][0]["despejes"][1]
        self.assertEqual([(t["variable"], t["signo"], t["factor"], t["origen"]) for t in despeje["terminos"]], [
            ("x₁", "+", "", "nuevo"), ("x₃", "+", "", "anterior"), ("x₄", "−", "3", "anterior"),
        ])
        self.assertEqual([t["valor"] for t in despeje["terminos"]], [motor.iteraciones[1].x[0], 0.0, 0.0])
        self.assertEqual(despeje["valor"], motor.iteraciones[1].x[1])
        self.assertEqual((despeje["independiente"], despeje["diagonal"]), ("25", "11"))
        self.assertContains(respuesta, 'data-orden="secuencial"')
        self.assertContains(respuesta, '(<span class="iterativo-valor" data-origen="nuevo" data-columna="0">')
        jacobi = self.resolver(CLASE_A, CLASE_B, "jacobi")
        self.assertContains(jacobi, 'data-orden="simultaneo"')
        self.assertNotContains(jacobi, '(<span class="iterativo-valor" data-origen="nuevo"')
        self.assertContains(jacobi, "Actualización <strong>simultánea</strong>")

    def test_numeros_de_maquina_usan_el_formato_global(self):
        respuesta = self.resolver(CLASE_A, CLASE_B, "jacobi")
        html = respuesta.content.decode()
        variantes = [json.loads(unescape(datos)) for datos in re.findall(r'data-numeric="([^"]+)"', html)]
        x2 = next(v for v in variantes if v["exacto"] == repr(25 / 11))
        self.assertEqual(x2["decimales"], {"2": "2.27", "4": "2.2727", "6": "2.272727", "8": "2.27272727"})
        # Un residuo pequeño se lee con su primera cifra significativa, nunca como 0.
        for v in variantes:
            if v["exacto"] != "0" and not v["exacto"].lstrip("-").startswith("0."):
                continue
            self.assertTrue(all(d.strip("-0.") for d in v["decimales"].values()), v)
        self.assertEqual(representar_flotante(4.663227051907399e-05)[1]["decimales"]["4"], "0.00005")
        # La tolerancia y los coeficientes exactos (1/2) también pasan por el formato global.
        fraccion = self.resolver([[2, "1/2"], ["1/2", 2]], [1, 1], "jacobi")
        self.assertContains(fraccion, "(1/2)")
        self.assertIn('"exacto": "− (1/2)", "decimales": {"2": "− (0.5)"', unescape(fraccion.content.decode()))

    def test_limite_de_iteraciones_muestra_la_ultima_aproximacion(self):
        respuesta = self.resolver(PRACTICA_A, PRACTICA_B, "comparar_iterativos", max_iteraciones="3")
        self.assertContains(respuesta, "no bajaron ambos de la tolerancia", count=2)
        self.assertContains(respuesta, "No converge en 3 iteraciones", count=2)
        self.assertEqual(respuesta.context["iterativos"]["titulo"],
                         "Jacobi no converge en 3 iteraciones; Gauss-Seidel no converge en 3 iteraciones")
        for resultado in respuesta.context["iterativos"]["metodos"]:
            self.assertEqual(resultado["final"]["k"], 3)
            self.assertEqual(len(resultado["filas"]), 4)
            self.assertFalse(resultado["cumple_cambio"] and resultado["cumple_residuo"])

    def test_sin_dominancia_y_parametros_validos(self):
        respuesta = self.resolver([[1, 2], [1, 4]], [3, 5], "jacobi",
                                  inicial_iterativo="1/2 3/2", tolerancia_iterativa="0.0002", max_iteraciones="250")
        self.assertContains(respuesta, 'data-dominancia="no-estricta"')
        self.assertContains(respuesta, "en la fila 1: la convergencia no está garantizada")
        self.assertContains(respuesta, 'data-estado="convergio"')
        self.assertContains(respuesta, "&lt; ε · cumple", count=2)
        resultado = respuesta.context["iterativos"]
        self.assertEqual(resultado["metodos"][0]["filas"][0]["x"], (0.5, 1.5))
        self.assertEqual(resultado["tolerancia"], 0.0002)
        self.assertEqual([(f["fila"], f["diagonal"], f["resto"], f["cumple"]) for f in resultado["dominancia"]],
                         [(1, "1", "2", False), (2, "4", "1", True)])

    def test_divergencia_del_ejemplo_sin_dominancia(self):
        _titulo, a, b = EJEMPLOS["sin-dominancia"]
        respuesta = self.resolver(a, b, "comparar_iterativos")
        for resultado in respuesta.context["iterativos"]["metodos"]:
            self.assertEqual((resultado["estado"], resultado["final"]["k"]), ("limite", 100))
            self.assertIn("El cambio máximo crece", resultado["mensaje"])
        self.assertContains(respuesta, "en las filas 1, 2")
        self.assertContains(respuesta, 'data-tono="aviso"')

    def test_vector_inicial_que_ya_es_solucion(self):
        respuesta = self.resolver(CLASE_A, CLASE_B, "gauss_seidel", inicial_iterativo="1 2 -1 1")
        resultado = respuesta.context["iterativos"]["metodos"][0]
        self.assertEqual((resultado["estado"], resultado["final"]["k"], resultado["final"]["cambio"]), ("convergio", 1, 0))
        self.assertEqual(respuesta.context["iterativos"]["titulo"], "Gauss-Seidel converge en 1 iteración")
        self.assertContains(respuesta, "x⁽⁰⁾ ya satisface Ax = b: la iteración 1 lo confirma con cambio 0.")

    def test_comprobaciones_de_dominancia_y_ax_b(self):
        respuesta = self.resolver(CLASE_A, CLASE_B, "comparar_iterativos")
        html = respuesta.content.decode()
        comprobaciones = html[html.index('id="comprobaciones-iterativas"'):]
        self.assertEqual(re.findall(r'<tr data-cumple="(si|no)"><th scope="row">(\d)</th><td>(\d+)</td><td>(\d+)</td>', comprobaciones),
                         [("si", "1", "10", "3"), ("si", "2", "11", "5"), ("si", "3", "10", "4"), ("si", "4", "8", "4")])
        self.assertIn("Ax = b con x⁽15⁾ de Jacobi", comprobaciones)
        self.assertIn("Ax = b con x⁽6⁾ de Gauss-Seidel", comprobaciones)
        for resultado in respuesta.context["iterativos"]["metodos"]:
            for fila, bi in zip(resultado["verificacion"], CLASE_B):
                self.assertAlmostEqual(fila["ax"] + fila["r"], bi, places=12)
                self.assertLess(abs(fila["r"]), 1e-4)

    def test_entradas_invalidas_preservan_formulario_y_mensajes(self):
        for a, extra, mensaje in (
            ([[1, 2, 3], [4, 5, 6]], {}, "requieren una matriz A cuadrada"),
            ([[0, 1], [1, 1]], {}, "diagonal de la fila 1 es cero"),
            ([[2, 1], [1, 2]], {"max_iteraciones": "501"}, "Escribe un entero de 1 a 500"),
            ([[2, 1], [1, 2]], {"tolerancia_iterativa": "-1"}, "La tolerancia debe ser positiva"),
            ([[2, 1], [1, 2]], {"inicial_iterativo": "1"}, "Escribe 2 componentes"),
        ):
            with self.subTest(extra=extra, mensaje=mensaje):
                respuesta = self.resolver(a, [1, 1], "jacobi", **extra)
                self.assertContains(respuesta, mensaje)
                self.assertNotContains(respuesta, 'id="resultado"')
                self.assertEqual(respuesta.context["form"]["metodo"].value(), "jacobi")
                self.assertEqual(respuesta.context["form"]["celda_b_0_0"].value(), "1")

    def test_residuo_comprueba_los_coeficientes_exactos_de_la_entrada(self):
        respuesta = self.resolver([[1]], [10_000_000_000_000_001], "jacobi", max_iteraciones="3")
        self.assertContains(respuesta, 'data-estado="limite"')
        resultado = respuesta.context["iterativos"]["metodos"][0]
        self.assertEqual(resultado["final"]["norma"], 1)
        self.assertEqual(resultado["verificacion"][0]["r"], 1)
        self.assertEqual(resultado["verificacion"][0]["b"], "10000000000000001")

    def test_rango_sin_primera_actualizacion_muestra_vector_inicial(self):
        respuesta = self.resolver([[f"1/{10**99}", 0], [0, f"1/{10**99}"]], [10**99, -(10**99)], "gauss_seidel",
                                  inicial_iterativo="0 0", max_iteraciones="1")
        self.assertContains(respuesta, 'data-estado="limite"')
        self.assertContains(respuesta, 'data-ultima="1"')
        self.assertContains(respuesta, 'class="iterativo-sustituciones"')

        # Los literales caben en el presupuesto, pero el crecimiento desborda en la vuelta 1.
        respuesta = self.resolver([[f"1/{10**99}", 10**99], [10**99, f"1/{10**99}"]], [10**99, 10**99], "gauss_seidel")
        self.assertContains(respuesta, 'data-estado="rango"')
        self.assertContains(respuesta, "En la iteración 1 se superó el rango numérico.")
        self.assertContains(respuesta, "x⁽0⁾")
        self.assertContains(respuesta, 'data-ultima="0"')
        self.assertNotContains(respuesta, 'class="iterativo-sustituciones"')
