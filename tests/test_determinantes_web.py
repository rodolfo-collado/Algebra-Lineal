"""Determinantes en la web: entrada, métodos contextuales, procedimiento, resultado y paso a Matriz inversa."""

import os
import re
from fractions import Fraction
from html import unescape
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import SimpleTestCase
from django.urls import resolve, reverse
from django.utils.html import strip_tags

from backend.presupuesto_computacional import Categoria
from backend.seguridad_numerica import MENSAJE_CALCULO_GRANDE
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.servicios_determinantes import firmar_entrada
from tests.test_matrices_web import Contenido
from tests.test_navegacion import Documento
from tests.test_procedimiento_plegable import comprobar_estructura, partes

RUTA = "/matrices/determinantes/"
RUTA_INVERSA = "/matrices/inversa/"
SERVICIO = "frontend.web.calculadora.servicios_determinantes"
ESTATICOS = Path(__file__).resolve().parents[1] / "frontend" / "web" / "calculadora" / "static" / "calculadora"
A3 = [[2, 1, 3], [0, 4, 2], [1, 0, 5]]


def datos_det(a=None, metodo="reduccion", expansion=None, **extra):
    a = A3 if a is None else a
    datos = {"orden": str(len(a)), "metodo": metodo}
    if expansion is not None:
        datos["expansion"] = expansion
    for i, fila in enumerate(a):
        for j, valor in enumerate(fila):
            datos[f"celda_A_{i}_{j}"] = str(valor)
    return datos | extra


def texto(html):
    return " ".join(unescape(strip_tags(re.sub(r">\s*<", "> <", html))).split())


def metodos_visibles(html):
    """(valor, desactivado) de cada radio de método, en orden."""
    return [(valor, "disabled" in atributos) for valor, atributos in
            re.findall(r'<input type="radio" name="metodo" value="([^"]+)"([^>]*)>', html)]


def forzar(nivel=Categoria.PESADA):
    return (patch(f"{SERVICIO}.categoria", return_value=nivel),
            patch(f"{SERVICIO}.intervalo_segundos", return_value=(2.0, 18.0)))


class PruebasCatalogo(SimpleTestCase):
    def test_matrices_termina_en_inversa_y_determinantes(self):
        herramienta = catalogo.DETERMINANTES
        self.assertEqual(catalogo.herramientas_de(catalogo.MATRICES)[-2:], (catalogo.MATRIZ_INVERSA, herramienta))
        self.assertTrue(herramienta.disponible)
        self.assertEqual(reverse("calculadora:determinantes"), RUTA)
        self.assertEqual(catalogo.herramienta_por_ruta(resolve(RUTA)), herramienta)
        self.assertFalse(catalogo.HERRAMIENTAS[-1].disponible)

    def test_relacion_en_los_dos_sentidos_con_matriz_inversa(self):
        self.assertIn("matriz-inversa", catalogo.DETERMINANTES.relacionadas)
        self.assertIn("determinantes", catalogo.MATRIZ_INVERSA.relacionadas)
        datos = datos_det([[1, 2], [3, 4]], "directo_2x2")
        self.assertIn(f'href="{RUTA_INVERSA}"', self.client.post(RUTA, datos).content.decode())
        inversa = self.client.post(RUTA_INVERSA, {"orden": "2", "metodo": "gauss_jordan", "celda_A_0_0": "1",
                                                  "celda_A_0_1": "2", "celda_A_1_0": "3", "celda_A_1_1": "4"})
        self.assertIn(f'href="{RUTA}"', inversa.content.decode())

    def test_buscador_y_migas(self):
        for consulta in ("determinante", "det", "cofactores", "sarrus", "factorización lu"):
            with self.subTest(consulta=consulta):
                self.assertEqual(catalogo.buscar_herramientas(consulta)[0], catalogo.DETERMINANTES)
        # Las búsquedas de Gauss y de inversa conservan su destino.
        self.assertEqual(catalogo.buscar_herramientas("inversa"), (catalogo.MATRIZ_INVERSA,))
        self.assertNotIn(catalogo.DETERMINANTES, catalogo.buscar_herramientas("gauss"))
        doc = Documento(self.client.get(RUTA))
        self.assertEqual([a["href"] for a in doc.enlaces_en("Ruta de navegación")], ["/", "/#algebra-lineal", "/#matrices"])
        self.assertEqual([a["href"] for a in doc.enlaces_en("Herramientas") if a.get("aria-current") == "page"], [RUTA])


class PruebasEntrada(SimpleTestCase):
    def test_get_2x2_con_formula_directa_y_sin_sarrus(self):
        html = self.client.get(RUTA).content.decode()
        self.assertEqual(metodos_visibles(html), [("directo_2x2", False), ("sarrus", True), ("cofactores", False),
                                                  ("lu", False), ("reduccion", False)])
        self.assertRegex(html, r'<input type="radio" name="metodo" value="directo_2x2"[^>]*checked')
        self.assertRegex(html, r'<label class="option" for="id_metodo_1" hidden>')
        self.assertIn('data-perfil="numerico"', html)
        self.assertIn("math-keyboard", html)
        self.assertEqual(Contenido(html).campos.keys() >= {"celda_A_0_0", "celda_A_1_1", "orden"}, True)
        # «Desarrollar por» ofrece Automático, cada fila y cada columna.
        self.assertEqual(re.findall(r'<option value="([^"]+)"', html.split('name="expansion"')[1].split("</select>")[0]),
                         ["auto", "fila_1", "fila_2", "columna_1", "columna_2"])

    def test_el_tamano_decide_los_metodos_disponibles(self):
        casos = {1: ("cofactores", ["cofactores", "lu", "reduccion"]), 3: ("sarrus", ["sarrus", "cofactores", "lu", "reduccion"]),
                 6: ("cofactores", ["cofactores", "lu", "reduccion"]), 7: ("reduccion", ["lu", "reduccion"])}
        for orden, (sugerido, activos) in casos.items():
            with self.subTest(orden=orden):
                html = self.client.post(RUTA, {"orden": str(orden), "ajustar": "1"}).content.decode()
                self.assertEqual([v for v, desactivado in metodos_visibles(html) if not desactivado], activos)
                self.assertRegex(html, rf'value="{sugerido}"[^>]*checked')

    def test_aplicar_conserva_celdas_y_sanea_metodo_y_expansion(self):
        datos = datos_det([[1, 2], [3, 4]], "directo_2x2", "columna_2", orden="3", ajustar="1")
        html = self.client.post(RUTA, datos).content.decode()
        campos = Contenido(html).campos
        self.assertEqual(campos["celda_A_1_1"]["value"], "4")
        self.assertNotIn("value", campos["celda_A_2_2"])
        self.assertRegex(html, r'value="sarrus"[^>]*checked')
        self.assertNotIn('id="resultado"', html)
        datos = datos_det(A3, "cofactores", "fila_3", orden="2", ajustar="1")
        html = self.client.post(RUTA, datos).content.decode()
        self.assertRegex(html, r'<option value="auto" selected>')

    def test_metodos_manipulados_se_rechazan(self):
        casos = ((A3, "directo_2x2"), ([[1, 2], [3, 4]], "sarrus"), ([[1] * 7 for _ in range(7)], "cofactores"),
                 (A3, "otro"))
        for a, metodo in casos:
            with self.subTest(n=len(a), metodo=metodo), \
                    patch(f"{SERVICIO}.calcular_determinante", side_effect=AssertionError("calculó")):
                html = self.client.post(RUTA, datos_det(a, metodo)).content.decode()
                self.assertNotIn('id="resultado"', html)
                self.assertIn('id="id_metodo_error"', html)

    def test_expansion_inexistente_y_contrato_estricto(self):
        for datos in (datos_det(A3, "cofactores", "fila_4"), datos_det(A3, extra="1"),
                      {k: v for k, v in datos_det(A3).items() if k != "celda_A_2_2"}):
            with self.subTest(datos=datos):
                html = self.client.post(RUTA, datos).content.decode()
                self.assertNotIn('id="resultado"', html)
                self.assertIn("error", html)
        repetido = self.client.post(RUTA, f"orden=1&metodo=lu&celda_A_0_0=1&celda_A_0_0=2",
                                    content_type="application/x-www-form-urlencoded")
        self.assertContains(repetido, "hay campos repetidos")

    def test_celdas_vacias_o_invalidas_se_marcan_en_su_celda(self):
        html = self.client.post(RUTA, datos_det([[1, "x"], ["", 4]], "lu")).content.decode()
        self.assertIn('id="id_celda_A_0_1_error"', html)
        self.assertIn('id="id_celda_A_1_0_error"', html)
        self.assertNotIn('id="resultado"', html)

    def test_la_expansion_solo_se_usa_con_cofactores(self):
        with patch(f"{SERVICIO}.calcular_determinante", wraps=__import__("backend.determinantes", fromlist=["x"]).calcular_determinante) as calcular:
            self.client.post(RUTA, datos_det(A3, "lu", "fila_2"))
            self.client.post(RUTA, datos_det(A3, "cofactores", "columna_3"))
        self.assertEqual([llamada.args[1:] for llamada in calcular.call_args_list], [("lu", "auto"), ("cofactores", "columna_3")])


class PruebasResultado(SimpleTestCase):
    def calcular(self, a, metodo, expansion=None):
        html = self.client.post(RUTA, datos_det(a, metodo, expansion)).content.decode()
        comprobar_estructura(self, html)
        return html, *partes(html)

    def test_todos_los_metodos_dan_el_mismo_resultado(self):
        casos = {2: ([[3, 4], [5, 6]], "-2"), 3: ([[1, 2, 3], [4, 5, 6], [7, 8, 10]], "-3"),
                 4: ([[2, 1, 3, 0], [0, 4, 2, 1], [1, 0, 5, 2], [3, 1, 0, 1]], "106")}
        for n, (a, esperado) in casos.items():
            metodos = ["cofactores", "lu", "reduccion"] + (["directo_2x2"] if n == 2 else []) + (["sarrus"] if n == 3 else [])
            for metodo in metodos:
                with self.subTest(n=n, metodo=metodo):
                    _, _, resultado = self.calcular(a, metodo)
                    self.assertTrue(resultado.startswith(f"Resultado det(A) = {esperado} Como det(A) ≠ 0, A es invertible."), resultado)

    def test_formula_directa(self):
        _, procedimiento, _ = self.calcular([[3, 4], [5, 6]], "directo_2x2")
        self.assertIn("det(A) = ad − bc = 3·6 − 4·5 = 18 − 20 = -2", procedimiento)

    def test_sarrus_repite_columnas_y_resta_sumas(self):
        _, procedimiento, _ = self.calcular([[1, 2, 3], [4, 5, 6], [7, 8, 10]], "sarrus")
        for linea in ("a₁₁·a₂₂·a₃₃ = 1·5·10 = 50", "Suma: 50 + 84 + 96 = 230", "a₁₃·a₂₂·a₃₁ = 3·5·7 = 105",
                      "Suma: 48 + 80 + 105 = 233", "det(A) = 230 − 233 = -3"):
            self.assertIn(linea, procedimiento)

    def test_sarrus_las_copias_siguen_siendo_c1_y_c2(self):
        html = self.client.post(RUTA, datos_det([[1, 2, 3], [4, 5, 6], [7, 8, 10]], "sarrus")).content.decode()
        figuras = re.findall(r'<div class="sarrus" .*?</div>\s*</div>\s*</div>', html, re.S)
        self.assertEqual(len(figuras), 3)
        figura = figuras[0]
        cabecera = re.search(r'<div class="sarrus-cabecera"[^>]*>(.*?)</div>', figura, re.S)[1]
        self.assertEqual(re.findall(r">(C\d)<", cabecera), ["C1", "C2", "C3", "C1", "C2"])
        self.assertEqual(re.findall(r'class="sarrus-copia">(C\d)<', cabecera), ["C1", "C2"])
        self.assertIn(">copias<", cabecera)
        self.assertEqual(re.findall(r">(F\d)<", figura), ["F1", "F2", "F3"])
        celdas = re.findall(r'<span class="sarrus-celda( sarrus-copia)?"[^>]*><span class="sarrus-indice">(.*?)</span>', figura)
        self.assertEqual([indice for _, indice in celdas[:5]], ["a₁₁", "a₁₂", "a₁₃", "a₁₁", "a₁₂"])
        self.assertEqual([bool(copia) for copia, _ in celdas], [False, False, False, True, True] * 3)
        # Las copias conservan su índice original: nunca aparecen a₁₄ ni a₃₅.
        self.assertNotRegex(figura, "a[₁₂₃][₄₅]")
        self.assertEqual(len(re.findall(r'class="sarrus-celda sarrus-copia" aria-hidden="true"', figura)), 6)

    def test_sarrus_cada_linea_recorre_los_factores_de_su_producto(self):
        html = self.client.post(RUTA, datos_det([[1, 2, 3], [4, 5, 6], [7, 8, 10]], "sarrus")).content.decode()
        indices = [re.findall(r'<span class="sarrus-indice">(.*?)</span>', f)
                   for f in re.findall(r'<div class="sarrus" .*?</div>\s*</div>\s*</div>', html, re.S)]
        extendida = [indices[0][fila * 5:(fila + 1) * 5] for fila in range(3)]
        for grupo, figura in (("↘", 1), ("↙", 2)):
            svg = re.findall(r'<svg class="sarrus-diagonales".*?</svg>', html, re.S)[figura - 1]
            lineas = re.findall(r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)" data-trazo="(\w+)"', svg)
            lista = re.findall(rf'data-trazo="(\w+)"/></svg>{grupo} (a\S+) =', html)
            self.assertEqual(len(lineas), 3)
            self.assertEqual(len({trazo for *_, trazo in lineas}), 3)
            for (x1, y1, x2, y2, trazo), (trazo_lista, producto) in zip(lineas, lista):
                with self.subTest(grupo=grupo, producto=producto):
                    x1, y1, x2, y2 = map(float, (x1, y1, x2, y2))
                    recorridas = [extendida[fila][int(x1 + (fila + 0.5 - y1) * (x2 - x1) / (y2 - y1))] for fila in range(3)]
                    self.assertEqual("·".join(recorridas), producto)
                    self.assertEqual(trazo, trazo_lista)

    def test_cofactores_por_fila_columna_y_automatico(self):
        _, procedimiento, _ = self.calcular(A3, "cofactores", "columna_1")
        self.assertIn("Se desarrolla por la columna 1, la que se eligió.", procedimiento)
        self.assertIn("det(A) = a₁₁C₁₁ + a₂₁C₂₁ + a₃₁C₃₁", procedimiento)
        self.assertIn("a₂₁ = 0: su término vale 0 y no hace falta calcular su menor.", procedimiento)
        self.assertIn("M₁₁ = ad − bc = 4·5 − 2·0 = 20 − 0 = 20", procedimiento)
        self.assertIn("Signo: (−1)³⁺¹ = +1", procedimiento)
        self.assertIn("det(A) = 40 + 0 + (-10) = 30", procedimiento)
        _, procedimiento, _ = self.calcular(A3, "cofactores", "auto")
        self.assertIn("Automático elige la fila 2: tiene 1 cero y ninguna otra fila o columna tiene más.", procedimiento)

    def test_cofactores_anida_los_menores_grandes_en_desplegables_cerrados(self):
        html, procedimiento, _ = self.calcular([[2, 1, 3, 0], [0, 4, 2, 1], [1, 0, 5, 2], [3, 1, 0, 1]], "cofactores")
        estructura = comprobar_estructura(self, html)
        anidados = [d for d in estructura.details if d["nivel"] == 1]
        self.assertEqual([" ".join(d["summary"].split()) for d in anidados],
                         ["Cómo se obtiene M₁₁", "Cómo se obtiene M₁₂", "Cómo se obtiene M₁₃"])
        self.assertTrue(all(d["encabezado"] == "h5" for d in anidados))
        self.assertIn("Aquí las posiciones mᵢⱼ se cuentan dentro de este menor.", procedimiento)

    def test_lu_muestra_l_u_y_la_diagonal(self):
        html, procedimiento, _ = self.calcular([[2, 1, 1], [4, -6, 0], [-2, 7, 2]], "lu")
        tablas = Contenido(html).tablas
        self.assertEqual(tablas["Matriz L"], [["1", "0", "0"], ["2", "1", "0"], ["-1", "-1", "1"]])
        self.assertEqual(tablas["Matriz U"], [["2", "1", "1"], ["0", "-8", "-2"], ["0", "0", "1"]])
        self.assertIn("det(A) = det(L)·det(U) = 1·det(U)", procedimiento)
        self.assertIn("det(U) = 2·(-8)·1 = -16", procedimiento)
        self.assertIn("F2 = F2 - (2)F1", procedimiento)

    def test_lu_construye_columnas_antes_de_presentar_a_igual_lu(self):
        html, procedimiento, resultado = self.calcular([[2, 1, 1], [4, -6, 0], [-2, 7, 2]], "lu")
        for linea in ("Columna 1 de L · pivote en fila 1, columna 1 de U", "U antes de las eliminaciones",
                      "l₁₁ = 2 / 2 = 1", "l₂₁ = 4 / 2 = 2", "l₃₁ = (-2) / 2 = -1",
                      "l₂₂ = (-8) / (-8) = 1", "l₃₂ = 8 / (-8) = -1",
                      "La misma secuencia de 3 reemplazos aplicada a L, en el mismo orden", "Verificación exacta: L → I"):
            self.assertIn(linea, procedimiento)
        self.assertLess(procedimiento.index("l₃₁ ="), procedimiento.index("F2 = F2 - (2)F1"))
        self.assertLess(procedimiento.index("l₃₂ ="), procedimiento.index("2 · A = LU"))
        self.assertEqual(Contenido(html).tablas["L después de los mismos reemplazos"],
                         [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]])
        self.assertNotIn("det(A) = -16", procedimiento)
        self.assertEqual(resultado.count("det(A) = -16"), 1)

    def test_lu_muestra_divisiones_exactas_y_columnas_saltadas(self):
        _, procedimiento, _ = self.calcular([["1/2", 1, 0], ["-3/4", "2/3", 2], [0, "1/3", 1]], "lu")
        for linea in ("l₂₁ = (-3/4) / (1/2) = -3/2", "l₃₁ = 0 / (1/2) = 0",
                      "l₃₂ = (1/3) / (13/6) = 2/13"):
            self.assertIn(linea, procedimiento)
        _, procedimiento, resultado = self.calcular([[0, 2, 3], [0, 4, 5], [0, 0, 0]], "lu")
        self.assertIn("Columna 1 de L · pivote en fila 1, columna 2 de U", procedimiento)
        self.assertIn("Columna 2 de L · pivote en fila 2, columna 3 de U", procedimiento)
        self.assertIn("l₂₁ = 4 / 2 = 2", procedimiento)
        self.assertIn("Verificación exacta: L → I", procedimiento)
        self.assertTrue(resultado.startswith("Resultado det(A) = 0"))

    def test_lu_nula_y_uno_por_uno_verifican_sin_reemplazos(self):
        for a in ([[0, 0], [0, 0]], [["-2/3"]]):
            with self.subTest(a=a):
                _, procedimiento, _ = self.calcular(a, "lu")
                self.assertIn("La misma secuencia de 0 reemplazos aplicada a L", procedimiento)
                self.assertIn("Verificación exacta: L → I", procedimiento)

    def test_lu_que_necesitaria_intercambio_se_detiene_sin_inventar_un_determinante(self):
        html, procedimiento, resultado = self.calcular([[0, 1], [1, 0]], "lu")
        self.assertIn("El pivote u₁₁ es 0 y debajo hay un número distinto de 0.", procedimiento)
        self.assertTrue(resultado.startswith("Resultado LU sin intercambios no puede continuar con esta matriz."))
        self.assertNotIn("det(A) =", resultado)
        self.assertNotIn("data-transferencia", html)

    def test_reduccion_explica_intercambio_diagonal_y_ajuste_sin_normalizaciones(self):
        html, procedimiento, resultado = self.calcular([[0, 2], [3, 4]], "reduccion")
        self.assertIn("Paso 1 (F1 <-> F2): este intercambio cambia el signo del determinante.", unescape(procedimiento))
        self.assertIn("Los pivotes se conservan: no se normalizan filas.", procedimiento)
        self.assertNotIn("F1 = (1/3)F1", procedimiento)
        self.assertNotIn("divide cada fila", procedimiento)
        self.assertNotIn("se corrige multiplicando", procedimiento)
        self.assertIn("det(U) = 3·2 = 6", procedimiento)
        self.assertIn("Cantidad de intercambios: s = 1", procedimiento)
        self.assertIn("det(A) = (−1)¹·det(U) = (-1)·6", procedimiento)
        self.assertEqual(Contenido(html).tablas["Matriz triangular U"], [["3", "4"], ["0", "2"]])
        self.assertNotIn("det(A) = -6", procedimiento)
        self.assertEqual(resultado.count("det(A) = -6"), 1)
        _, procedimiento, _ = self.calcular([[2, 4], [1, 3]], "reduccion")
        self.assertNotIn("<->", unescape(procedimiento))
        self.assertIn("No hubo intercambios: s = 0 y det(A) = det(U)", procedimiento)
        self.assertIn("F2 = F2 - (1/2)F1", procedimiento)
        self.assertIn("det(U) = 2·1 = 2", procedimiento)

    def test_reduccion_varios_intercambios_y_fracciones(self):
        _, procedimiento, resultado = self.calcular([[0, 0, 2], [3, 0, 4], [0, -5, 6]], "reduccion")
        self.assertEqual(procedimiento.count("este intercambio cambia el signo"), 2)
        self.assertIn("det(U) = 3·(-5)·2 = -30", procedimiento)
        self.assertIn("det(A) = (−1)²·det(U) = 1·(-30)", procedimiento)
        self.assertTrue(resultado.startswith("Resultado det(A) = -30"))
        _, procedimiento, resultado = self.calcular([["-1/2", "2/3"], ["3/4", "-2/5"]], "reduccion")
        self.assertIn("F2 = F2 + (3/2)F1", procedimiento)
        self.assertIn("det(U) = (-1/2)·(3/5) = -3/10", procedimiento)
        self.assertTrue(resultado.startswith("Resultado det(A) = -3/10"))

    def test_fracciones_y_decimales_exactos(self):
        _, _, resultado = self.calcular([["1/2", "0.25"], ["3", "1/3"]], "directo_2x2")
        self.assertTrue(resultado.startswith("Resultado det(A) = -7/12"), resultado)

    def test_singular_no_ofrece_una_inversa(self):
        for metodo in ("directo_2x2", "cofactores", "lu", "reduccion"):
            with self.subTest(metodo=metodo):
                html, _, resultado = self.calcular([[1, 2], [2, 4]], metodo)
                self.assertEqual(resultado, "Resultado det(A) = 0 Como det(A) = 0, A no es invertible: no tiene matriz inversa.")
                self.assertNotIn("Calcular su matriz inversa", html)
                self.assertNotIn("data-transferencia", html)

    def test_uno_por_uno(self):
        _, procedimiento, resultado = self.calcular([["-5"]], "cofactores")
        self.assertIn("En una matriz 1×1, el determinante es su única entrada: -5.", procedimiento)
        self.assertTrue(resultado.startswith("Resultado det(A) = -5"))


class PruebasTransferencia(SimpleTestCase):
    def test_det_no_nulo_ofrece_un_post_con_a_exacta(self):
        html = self.client.post(RUTA, datos_det([["1/2", "0.5"], ["-3", 4]], "lu")).content.decode()
        formulario = html[html.index("data-transferencia") - 200:]
        formulario = formulario[:formulario.index("</form>")]
        self.assertIn(f'action="{RUTA_INVERSA}#inversa-form"', formulario)
        self.assertIn('method="post"', formulario)
        campos = dict(re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', formulario))
        campos.pop("csrfmiddlewaretoken", None)
        self.assertEqual(campos, {"orden": "2", "celda_A_0_0": "1/2", "celda_A_0_1": "1/2",
                                  "celda_A_1_0": "-3", "celda_A_1_1": "4"})
        self.assertIn('name="cargar_matriz"', formulario)

    def test_inversa_carga_a_sin_calcular(self):
        datos = {"orden": "3", "cargar_matriz": "1", **{f"celda_A_{i}_{j}": str(v) for i, f in enumerate(A3) for j, v in enumerate(f)}}
        with patch("frontend.web.calculadora.servicios_inversa.calcular_inversa", side_effect=AssertionError("calculó")):
            html = self.client.post(RUTA_INVERSA, datos).content.decode()
        campos = Contenido(html).campos
        self.assertEqual([campos[f"celda_A_{i}_{j}"]["value"] for i in range(3) for j in range(3)],
                         [str(v) for fila in A3 for v in fila])
        self.assertEqual(campos["orden"]["value"], "3")
        self.assertEqual(campos["metodo"]["value"], "gauss_jordan")
        self.assertNotIn('id="resultado"', html)
        self.assertNotIn("data-respuesta-errores", html)
        # Nada se guarda: la página vuelve vacía en la siguiente visita.
        self.assertNotIn('value="2"', self.client.get(RUTA_INVERSA).content.decode().split('name="celda_A_0_0"')[1][:80])

    def test_una_transferencia_manipulada_se_valida_y_no_calcula(self):
        for datos in ({"orden": "2", "cargar_matriz": "1", "celda_A_0_0": "x", "celda_A_0_1": "1", "celda_A_1_0": "1", "celda_A_1_1": "1"},
                      {"orden": "2", "cargar_matriz": "1", "celda_A_0_0": "1"},
                      {"orden": "2", "cargar_matriz": "1", "celda_A_0_0": "1", "celda_A_0_1": "1", "celda_A_1_0": "1",
                       "celda_A_1_1": "1", "intruso": "1"}):
            with self.subTest(datos=datos), \
                    patch("frontend.web.calculadora.servicios_inversa.calcular_inversa", side_effect=AssertionError("calculó")):
                html = self.client.post(RUTA_INVERSA, datos).content.decode()
                self.assertIn("data-respuesta-errores", html)
                self.assertNotIn('id="resultado"', html)

    def test_la_inversa_que_llega_coincide_con_el_determinante(self):
        datos = {"orden": "3", "cargar_matriz": "1", **{f"celda_A_{i}_{j}": str(v) for i, f in enumerate(A3) for j, v in enumerate(f)}}
        html = self.client.post(RUTA_INVERSA, datos).content.decode()
        campos = Contenido(html).campos
        # Lo que enviaría «Calcular inversa» sin tocar nada: A cargada y Gauss-Jordan.
        reenvio = {k: v["value"] for k, v in campos.items() if k.startswith("celda_A_") or k in ("orden", "metodo")}
        resultado = texto(self.client.post(RUTA_INVERSA, reenvio).content.decode())
        self.assertIn("det(A) = 30 ≠ 0: A es invertible.", resultado)


class PruebasConfirmacion(SimpleTestCase):
    def test_pesada_pregunta_antes_de_calcular_y_continuar_calcula(self):
        datos = datos_det(A3, "cofactores", "auto")
        normal, pesada = forzar()
        with normal, pesada, patch(f"{SERVICIO}.calcular_determinante", side_effect=AssertionError("calculó")):
            html = self.client.post(RUTA, datos).content.decode()
        self.assertIn("data-confirmacion", html)
        self.assertIn("Reducción por filas o Factorización LU obtienen el mismo determinante con menos pasos.", html)
        self.assertIn("Calcular det(A) y su procedimiento", html)
        firma = re.search(r'name="confirmacion" value="([0-9a-f]+)"', html)[1]
        self.assertEqual(firma, firmar_entrada({"a": [[Fraction(v) for v in f] for f in A3], "metodo": "cofactores", "expansion": "auto"}))
        normal, pesada = forzar()
        with normal, pesada:
            html = self.client.post(RUTA, datos | {"confirmacion": firma}).content.decode()
        self.assertIn('id="resultado"', html)
        normal, pesada = forzar()
        with normal, pesada, patch(f"{SERVICIO}.calcular_determinante", side_effect=AssertionError("otra entrada")):
            html = self.client.post(RUTA, datos_det(A3, "cofactores", "fila_1", confirmacion=firma)).content.decode()
        self.assertIn("data-confirmacion", html)

    def test_cancelar_conserva_la_entrada_sin_calcular(self):
        html = self.client.post(RUTA, datos_det(A3, "lu", ajustar="1")).content.decode()
        self.assertEqual(Contenido(html).campos["celda_A_2_2"]["value"], "5")
        self.assertNotIn('id="resultado"', html)


class PruebasSeguridad(SimpleTestCase):
    def test_un_literal_enorme_se_rechaza_en_su_celda(self):
        html = self.client.post(RUTA, datos_det([["1e1000000"]], "lu")).content.decode()
        self.assertIn('id="id_celda_A_0_0_error"', html)
        self.assertNotIn('id="resultado"', html)

    def test_un_calculo_que_crece_demasiado_da_un_error_controlado(self):
        # Las cotas del backend (BITS_MAXIMOS) lanzan ValueError; la vista lo muestra junto a A.
        with patch(f"{SERVICIO}.calcular_determinante", side_effect=ValueError(MENSAJE_CALCULO_GRANDE)):
            html = self.client.post(RUTA, datos_det(A3, "lu")).content.decode()
        self.assertIn('data-error-group="determinant-matrix"', html)
        self.assertIn(MENSAJE_CALCULO_GRANDE, unescape(html))
        self.assertNotIn('id="resultado"', html)


class PruebasRecursos(SimpleTestCase):
    def test_la_pagina_registra_su_formulario_en_los_scripts_compartidos(self):
        # Enter calcula, Aplicar se oculta y la selección matricial funciona como en las demás matrices.
        for archivo in ("entradas.js", "seleccion_matricial.js"):
            self.assertIn("#determinantes-form", (ESTATICOS / archivo).read_text(encoding="utf-8"))
        html = self.client.get(RUTA).content.decode()
        for recurso in ("determinantes.js", "teclado.js", "seleccion_matricial.js", 'id="matrix-entry-template"', 'id="matrix-cell-template"'):
            self.assertIn(recurso, html)
