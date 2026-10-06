"""Contratos web de P13B migrados a la herramienta unificada (P26.6): AB y Ax, sus lecturas y seguridad."""

import os
import re
from fractions import Fraction
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import Client, SimpleTestCase

from backend.matrices import resolver_operacion_matrices
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms_expresiones import ExpresionMatricialForm
from frontend.web.calculadora.opciones_matrices import ENTRADAS_DESPLEGADAS, METODOS, METODOS_MATRIZ_VECTOR
from frontend.web.calculadora.servicios_matrices import subindice
from tests.test_matrices_web import RUTA, Contenido, datos_simbolos, matriz
from tests.test_navegacion import Documento


def datos_producto(a=None, b=None, metodo="fila_columna", **extra):
    """AB: dos matrices y la lectura elegida para el procedimiento."""
    a = [[1, 2], [3, 4]] if a is None else a
    b = [[5, 6], [7, 8]] if b is None else b
    return datos_simbolos("AB", [matriz("A", a), matriz("B", b)], metodo=metodo, **extra)


def datos_matriz_vector(a=None, x=None, metodo="fila_columna", **extra):
    """Ax con x conocido: el producto, no la ecuación."""
    a = [[1, 2, -1], [0, -5, 3]] if a is None else a
    x = [4, 3, 7] if x is None else x
    return datos_simbolos("Ax", [matriz("A", a), {"nombre": "x", "tipo": "vector", "valor": x}], metodo=metodo, **extra)


def lineas(html):
    """Las igualdades del procedimiento entrada por entrada, en orden (sin la ayuda del formulario)."""
    resultado = html[html.index('id="resultado"'):]
    return [re.sub(r"<[^>]+>", "", linea).strip() for linea in re.findall(r'<li>(.*?)</li>', resultado, re.S) if " = " in linea]


class PruebasCatalogoP13B(SimpleTestCase):
    def test_los_productos_no_son_herramientas_aparte(self):
        # AB y Ax se escriben en Operaciones con matrices; Resolver Ax = b busca x, no un producto.
        documento = Documento(self.client.get(RUTA))
        enlaces = [a["href"] for a in documento.enlaces_en("Herramientas") if a["href"].startswith("/matrices/")]
        self.assertEqual(enlaces, [RUTA, "/matrices/reduccion/", "/matrices/ecuaciones/", "/matrices/inversa/"])
        self.assertNotIn("Multiplicación de matrices", [a.get("title") for a in documento.enlaces_en("Herramientas")])

    def test_busqueda_encuentra_los_productos(self):
        consultas = ("multiplicación de matrices", "producto de matrices", "matriz por matriz", "Ax", "matriz vector",
                     "fila columna", "fila vector", "producto punto", "combinación lineal", "columnas")
        for consulta in consultas:
            with self.subTest(consulta=consulta):
                self.assertIn(catalogo.OPERACIONES_MATRICES, catalogo.buscar_herramientas(consulta))
                self.assertContains(self.client.get("/", {"q": consulta}), f'href="{RUTA}"')
        # Las palabras propias de sistemas siguen sin arrastrar a matrices.
        for consulta in ("gauss", "pivote", "binario"):
            self.assertNotIn(catalogo.OPERACIONES_MATRICES, catalogo.buscar_herramientas(consulta))

    def test_la_ayuda_menciona_ab_ax_y_las_lecturas(self):
        respuesta = self.client.get(RUTA)
        self.assertContains(respuesta, "Realiza y combina operaciones con matrices, vectores y escalares paso a paso.")
        for fragmento in ("<code>AB</code>", "<code>Ax</code>", "regla fila-vector", "combinación lineal de columnas"):
            self.assertContains(respuesta, fragmento)


class PruebasOpcionPresentacion(SimpleTestCase):
    def test_tres_lecturas_como_radios_plegadas_con_ayuda(self):
        html = self.client.get(RUTA).content.decode()
        self.assertEqual(re.findall(r'<input type="radio" name="metodo" value="(\w+)"', html), ["fila_columna", "columnas", "comparar"])
        self.assertRegex(html, r'name="metodo" value="fila_columna"[^>]*checked')
        self.assertIn("<legend>Cómo mostrar los productos</legend>", html)
        # Plegada mientras sea la predeterminada; abierta cuando el envío eligió otra.
        self.assertRegex(html, r'<details class="disclosure" id="opciones-procedimiento">')
        abierta = self.client.post(RUTA, datos_producto(metodo="comparar", ajustar="1")).content.decode()
        self.assertRegex(abierta, r'<details class="disclosure" id="opciones-procedimiento" open>')
        self.assertRegex(abierta, r'name="metodo" value="comparar"[^>]*checked')
        self.assertEqual(dict(METODOS)["columnas"], "Por columnas")
        self.assertEqual(dict(METODOS_MATRIZ_VECTOR)["fila_columna"], "Regla fila-vector")

    def test_la_lectura_no_cambia_el_resultado_ni_multiplica_dos_veces(self):
        resultados = []
        for metodo in ("fila_columna", "columnas", "comparar"):
            with patch("backend.expresiones_matriciales.evaluador.resolver_operacion_matrices", wraps=resolver_operacion_matrices) as motor:
                html = self.client.post(RUTA, datos_producto(a=[[1, 2, 3]], b=[[1], [0], [2]], metodo=metodo)).content.decode()
            self.assertEqual(motor.call_count, 1)
            resultados.append(Contenido(html).tablas["Resultado"])
        self.assertEqual(resultados, [[["7"]]] * 3)

    def test_aplicar_agregar_y_eliminar_conservan_la_lectura(self):
        for accion in ({"ajustar": "1"}, {"agregar": "1"}, {"eliminar": "1"}):
            with self.subTest(accion=accion):
                html = self.client.post(RUTA, datos_producto(metodo="columnas", **accion)).content.decode()
                self.assertRegex(html, r'name="metodo" value="columnas"[^>]*checked')

    def test_lectura_invalida(self):
        for metodo in ("gauss", "ambos", "<script>alert(1)</script>"):
            respuesta = self.client.post(RUTA, datos_producto(metodo=metodo))
            self.assertContains(respuesta, "Selecciona una forma válida de mostrar los productos.")
            self.assertNotContains(respuesta, 'id="resultado"')
            self.assertNotContains(respuesta, "<script>alert(1)</script>")

    def test_sin_lectura_se_usa_fila_por_columna(self):
        # Compatibilidad con los envíos de Expresiones matriciales, que no tenían esta opción.
        html = self.client.post(RUTA, datos_producto(metodo=None)).content.decode()
        self.assertIn(">Fila por columna</h5>", html)
        self.assertNotIn("Columna por columna", html)


class PruebasResultadosProducto(SimpleTestCase):
    def calcular(self, datos):
        respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode()
        self.assertNotIn('role="alert"', html)
        self.assertIn('id="resultado"', html)
        return html, Contenido(html)

    def test_dos_por_dos_fila_por_columna(self):
        html, doc = self.calcular(datos_producto())
        self.assertEqual(doc.tablas["Resultado"], [["19", "22"], ["43", "50"]])
        self.assertEqual(doc.tablas["Desarrollo por entradas"], [["1·5 + 2·7", "1·6 + 2·8"], ["3·5 + 4·7", "3·6 + 4·8"]])
        self.assertEqual(lineas(html)[:2], [
            "c₁₁ = fila₁(A) · columna₁(B) = a₁₁b₁₁ + a₁₂b₂₁ = 1·5 + 2·7 = 5 + 14 = 19",
            "c₁₂ = fila₁(A) · columna₂(B) = a₁₁b₁₂ + a₁₂b₂₂ = 1·6 + 2·8 = 6 + 16 = 22",
        ])
        self.assertIn("Fila 1 de AB", html)
        self.assertIn("c₁₁ = 19, c₁₂ = 22", html)
        # Una sola lectura: su desarrollo va directo dentro de «Ver procedimiento», sin sub-bloques.
        self.assertEqual(html.count('id="procedimiento"'), 1)
        self.assertNotIn("disclosure-nested", html)
        self.assertNotIn("Columna por columna", html)

    def test_dos_por_tres_por_tres_por_dos_y_tres_por_dos_por_dos_por_cuatro(self):
        html, doc = self.calcular(datos_producto(a=[[1, 2, 3], [4, 5, 6]], b=[[7, 8], [9, 10], [11, 12]]))
        self.assertEqual(doc.tablas["Resultado"], [["58", "64"], ["139", "154"]])
        self.assertIn("Expresión · 2×2", html)
        html, doc = self.calcular(datos_producto(a=[[1, 0], [0, 1], [2, 3]], b=[[1, 2, 3, 4], [5, 6, 7, 8]], metodo="columnas"))
        self.assertEqual(doc.tablas["Resultado"], [["1", "2", "3", "4"], ["5", "6", "7", "8"], ["17", "22", "27", "32"]])
        self.assertIn("A: 3×2 · B: 2×4 → AB: 3×4.", html)

    def test_fracciones_exactas_con_la_igualdad_del_enunciado(self):
        html, doc = self.calcular(datos_producto(a=[[3, -1, 5]], b=[[2], [4], ["1/2"]]))
        self.assertEqual(doc.tablas["Resultado"], [["9/2"]])
        self.assertEqual(lineas(html), ["c₁₁ = fila₁(A) · columna₁(B) = a₁₁b₁₁ + a₁₂b₂₁ + a₁₃b₃₁ = 3·2 + (-1)·4 + 5·(1/2) = 6 + (-4) + 5/2 = 9/2"])

    def test_por_columnas_muestra_la_combinacion_lineal_y_el_ensamble(self):
        html, doc = self.calcular(datos_producto(a=[[2, 3, 4], [-1, 5, -3], [6, -2, 8]], b=[[2, 1], [-1, 0], [3, "1/2"]], metodo="columnas"))
        self.assertEqual(doc.tablas["Resultado"], [["13", "4"], ["-16", "-5/2"], ["38", "10"]])
        self.assertIn("Ab₁ = b₁₁a₁ + b₂₁a₂ + b₃₁a₃ = 2a₁ − a₂ + 3a₃", html)
        self.assertIn("Ab₂ = b₁₂a₁ + b₂₂a₂ + b₃₂a₃ = a₁ + 0a₂ + (1/2)a₃", html)
        self.assertEqual(doc.tablas["Columna 1 de A"], [["2"], ["-1"], ["6"]])
        self.assertEqual(doc.tablas["Columna 3 de A multiplicada por 3"], [["12"], ["-9"], ["24"]])
        self.assertEqual(doc.tablas["Columna 1 de AB"], [["13"], ["-16"], ["38"]])
        self.assertEqual(doc.tablas["Columna 2 de AB"], [["4"], ["-5/2"], ["10"]])
        self.assertIn("AB = [Ab₁ Ab₂] =", html)
        self.assertEqual(doc.tablas["Resultado ensamblado"], doc.tablas["Resultado"])
        self.assertNotIn("Entrada por entrada", html)

    def test_comparar_muestra_el_resultado_una_vez_y_los_dos_procedimientos(self):
        html, doc = self.calcular(datos_producto(metodo="comparar"))
        self.assertEqual(html.count('id="results-title"'), 1)
        self.assertEqual(html.count('<table class="matrix-table" aria-label="Resultado"'), 1)
        # «Ver procedimiento» plegado con un sub-bloque por lectura y, después, un único resultado.
        self.assertEqual(html.count('id="procedimiento"'), 1)
        self.assertEqual(html.count('class="disclosure disclosure-nested"'), 2)
        self.assertIn(">Fila por columna</h5>", html)
        self.assertIn(">Por columnas</h5>", html)
        self.assertLess(html.index('id="procedimiento"'), html.index('id="final-title"'))
        self.assertLess(html.index(">Fila por columna</h5>"), html.index(">Por columnas</h5>"))
        # Ambas lecturas terminan en la misma matriz.
        self.assertEqual(doc.tablas["Resultado del desarrollo"], doc.tablas["Resultado"])
        self.assertEqual(doc.tablas["Resultado ensamblado"], doc.tablas["Resultado"])

    def test_ax_regla_fila_vector(self):
        html, doc = self.calcular(datos_matriz_vector())
        self.assertEqual(doc.tablas["Resultado"], [["3"], ["6"]])
        self.assertEqual(doc.tablas["x"], [["4"], ["3"], ["7"]])
        self.assertIn("Expresión · 2 componentes", html)
        self.assertIn("A (2×3) · x (3) → Ax (2).", html)
        self.assertEqual(lineas(html), [
            "(Ax)₁ = fila₁(A) · x = a₁₁x₁ + a₁₂x₂ + a₁₃x₃ = 1·4 + 2·3 + (-1)·7 = 4 + 6 + (-7) = 3",
            "(Ax)₂ = fila₂(A) · x = a₂₁x₁ + a₂₂x₂ + a₂₃x₃ = 0·4 + (-5)·3 + 3·7 = 0 + (-15) + 21 = 6",
        ])
        self.assertIn("Entradas de Ax", html)
        self.assertIn("Regla fila-vector", html)

    def test_ax_combinacion_lineal_de_columnas(self):
        html, doc = self.calcular(datos_matriz_vector(a=[[2, 3, 4], [-1, 5, -3], [6, -2, 8]], x=[2, -1, 3], metodo="columnas"))
        self.assertEqual(doc.tablas["Resultado"], [["13"], ["-16"], ["38"]])
        self.assertIn("Ax = x₁a₁ + x₂a₂ + x₃a₃ = 2a₁ − a₂ + 3a₃", html)
        self.assertEqual(doc.tablas["Columna 2 de A multiplicada por -1"], [["-3"], ["-5"], ["2"]])
        self.assertEqual(doc.tablas["Vector Ax"], [["13"], ["-16"], ["38"]])
        self.assertIn("Combinación lineal de columnas", html)
        self.assertIn("combinación lineal de las columnas de A", html)
        self.assertNotIn("forman el resultado", html)

    def test_ax_comparar_y_fracciones(self):
        html, doc = self.calcular(datos_matriz_vector(a=[["1/2", -1], [3, "2/3"]], x=[4, "-3/2"], metodo="comparar"))
        self.assertEqual(doc.tablas["Resultado"], [["7/2"], ["11"]])
        self.assertEqual(html.count('<table class="matrix-table" aria-label="Resultado"'), 1)
        self.assertIn(">Regla fila-vector</h5>", html)
        self.assertIn(">Combinación lineal de columnas</h5>", html)
        self.assertIn("(Ax)₁ = fila₁(A) · x = a₁₁x₁ + a₁₂x₂ = (1/2)·4 + (-1)·(-3/2) = 2 + 3/2 = 7/2", lineas(html))
        self.assertIn("Ax = x₁a₁ + x₂a₂ = 4a₁ − (3/2)a₂", html)

    def test_ax_una_fila_y_una_columna(self):
        html, doc = self.calcular(datos_matriz_vector(a=[[1, 2, 3]], x=[4, 5, 6]))
        self.assertEqual(doc.tablas["Resultado"], [["32"]])
        self.assertIn("Expresión · 1 componente<", html)
        html, doc = self.calcular(datos_matriz_vector(a=[[1], [2], [3]], x=["1/2"], metodo="comparar"))
        self.assertEqual(doc.tablas["Resultado"], [["1/2"], ["1"], ["3/2"]])
        self.assertIn("(Ax)₁ = fila₁(A) · x = a₁₁x₁ = 1·(1/2) = 1/2", lineas(html))

    def test_otro_nombre_de_vector_conserva_la_lectura(self):
        # Au con u conocido: la misma regla fila-vector, con el nombre del vector.
        datos = datos_simbolos("Au", [matriz("A", [[1, 2], [3, 4]]), {"nombre": "u", "tipo": "vector", "valor": [1, -1]}], metodo="comparar")
        html, doc = self.calcular(datos)
        self.assertIn("(Au)₁ = fila₁(A) · u = a₁₁u₁ + a₁₂u₂ = 1·1 + 2·(-1) = 1 + (-2) = -1", lineas(html))
        self.assertIn("Au = u₁a₁ + u₂a₂ = a₁ − a₂", html)
        self.assertEqual(doc.tablas["Vector Au"], [["-1"], ["-1"]])

    def test_grupos_abiertos_solo_con_resultados_pequenos(self):
        html, _ = self.calcular(datos_producto())
        self.assertEqual(html.count('<details class="disclosure procedure-group" open>'), 2)
        grande = [[1] * 4 for _ in range(4)]
        html, _ = self.calcular(datos_producto(a=grande, b=grande, metodo="comparar"))
        self.assertNotIn('<details class="disclosure procedure-group" open>', html)
        self.assertEqual(html.count('<details class="disclosure procedure-group">'), 8)
        self.assertEqual(ENTRADAS_DESPLEGADAS, 12)

    def test_procedimiento_plegado_antes_del_resultado_y_recursos_locales(self):
        html, _ = self.calcular(datos_producto(metodo="comparar"))
        self.assertLess(html.index('id="results-title"'), html.index('id="procedimiento"'))
        self.assertLess(html.index('id="procedimiento"'), html.index('id="final-title"'))
        for recurso in ("expresiones.js", "teclado.js", "tema.js", "styles.css"):
            self.assertIn(f"/static/calculadora/{recurso}", html)
        self.assertNotIn('src="https://', html)
        self.assertNotIn('href="https://', html)
        self.assertIn('class="expression-field" data-perfil="expresion"', html)

    def test_subindices_legibles_hasta_diez(self):
        self.assertEqual(subindice(2, 3), "₂₃")
        self.assertEqual(subindice(10, 2), "₁₀,₂")
        self.assertEqual(subindice(7), "₇")
        html, _ = self.calcular(datos_producto(a=[[1] * 10], b=[[1] for _ in range(10)]))
        self.assertIn("a₁,₁₀b₁₀,₁", html)

    def test_error_del_backend_llega_legible(self):
        html = self.client.post(RUTA, datos_producto(a=[[1, 2, 3]], b=[[1, 2], [3, 4]])).content.decode()
        self.assertIn("No se puede calcular AB: A es 1×3 y B es 2×2. Para multiplicar matrices, las columnas de la primera deben coincidir con las filas de la segunda.", html)
        self.assertNotIn('id="resultado"', html)


class PruebasRechazoProducto(SimpleTestCase):
    def rechazar(self, datos, mensaje=None):
        respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'role="alert"')
        self.assertNotContains(respuesta, 'id="resultado"')
        if mensaje:
            self.assertContains(respuesta, mensaje)
        return respuesta

    def test_vector_x_manipulado(self):
        self.rechazar(datos_matriz_vector(x=[1, 2]), "Para multiplicar una matriz por un vector")
        self.rechazar(datos_matriz_vector(celda_1_3_0="1"), "Las celdas recibidas no coinciden")
        self.rechazar(datos_matriz_vector(celda_1_0_1="1"), "Las celdas recibidas no coinciden")
        for valor in ("", "abc", "1/0", "2/", "1,5"):
            with self.subTest(valor=valor):
                self.rechazar(datos_matriz_vector(celda_1_1_0=valor))
        self.rechazar(datos_matriz_vector(celda_1_1_0=""), "Completa vector x, componente 2.")

    def test_celdas_de_b_vacias_o_invalidas(self):
        self.rechazar(datos_producto(celda_1_0_0=""), "Completa matriz B, fila 1, columna 1.")
        self.rechazar(datos_producto(celda_1_1_1="1/0"), "no es un número válido")

    def test_estructura_de_b_manipulada(self):
        datos = datos_producto()
        del datos["celda_1_1_1"]
        self.rechazar(datos, "Las celdas recibidas no coinciden")
        self.rechazar(datos_producto(celda_1_2_0="1"), "Las celdas recibidas no coinciden")
        self.rechazar(datos_producto(filas_1="3"), "Las celdas recibidas no coinciden")

    def test_html_se_escapa_en_x_y_en_b(self):
        ataque = '<img src=x onerror="alert(1)">'
        for datos in (datos_matriz_vector(celda_1_0_0=ataque), datos_producto(celda_1_0_0=ataque), datos_matriz_vector(celda_1_0_0=ataque, ajustar="1")):
            respuesta = self.client.post(RUTA, datos)
            self.assertNotContains(respuesta, ataque)
            self.assertContains(respuesta, "&lt;img")

    def test_csrf_exigido_en_los_productos(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(RUTA, datos_producto()).status_code, 403)
        self.assertEqual(cliente.post(RUTA, datos_matriz_vector()).status_code, 403)
        cliente.get(RUTA)
        token = cliente.cookies["csrftoken"].value
        self.assertContains(cliente.post(RUTA, datos_matriz_vector(csrfmiddlewaretoken=token)), 'id="resultado"')

    def test_formulario_entrega_x_como_vector_exacto(self):
        form = ExpresionMatricialForm(datos_matriz_vector(a=[["1/2", 1, 0]], x=["-2", "1/3", 5], metodo="comparar"))
        self.assertTrue(form.is_valid(), form.errors)
        entrada = form.cleaned_data["entrada"]
        self.assertEqual(entrada["simbolos"]["x"], {"tipo": "vector", "valor": [-2, Fraction(1, 3), 5]})
        self.assertEqual(entrada["simbolos"]["A"], {"tipo": "matriz", "valor": [[Fraction(1, 2), 1, 0]]})
        self.assertEqual(entrada["metodo"], "comparar")


class PruebasAccesibilidadProducto(SimpleTestCase):
    def test_labels_reales_y_lecturas_como_radios(self):
        html = self.client.post(RUTA, datos_matriz_vector(ajustar="1")).content.decode()
        doc = Contenido(html)
        for nombre, attrs in doc.campos.items():
            if nombre.startswith(("celda_", "filas_", "columnas_")):
                self.assertTrue(doc.labels.get(attrs["id"]), nombre)
        self.assertEqual(len(re.findall(r'<input type="radio" name="metodo"', html)), 3)
        self.assertIn("<legend>Cómo mostrar los productos</legend>", html)

    def test_procedimiento_comprensible_sin_color(self):
        html = self.client.post(RUTA, datos_producto(metodo="comparar")).content.decode()
        # Cada igualdad nombra la fila y la columna; los grupos son el {% disclosure %} común,
        # con su título como encabezado y el resumen de valores como detalle (P27.8).
        self.assertIn("c₂₁ = fila₂(A) · columna₁(B)", html)
        self.assertIn('<h6 class="disclosure-title">Fila 2 de AB</h6>', html)
        self.assertNotIn("procedure-summary", html)
        self.assertIn('role="region" aria-label="Desarrollo de Ab₁"', html)
        self.assertIn('aria-label="Columnas de A"', html)
        self.assertNotIn('tabindex="0"', html)
        for etiqueta in ("Columna 1 de A", "Columna 1 de AB", "Resultado ensamblado"):
            self.assertIn(f'aria-label="{etiqueta}"', html)
