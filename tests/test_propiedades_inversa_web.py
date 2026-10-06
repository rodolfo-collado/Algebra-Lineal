"""P26.9: aplicaciones, presentación única y confirmación del cálculo completo."""

import os
import re
from fractions import Fraction
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import SimpleTestCase

from backend import matriz_inversa
from backend.presupuesto_computacional import (
    Categoria, categoria, estimar_gauss_jordan, estimar_producto, perfil_numerico,
)
from frontend.web.calculadora.servicios_inversa import (
    calcular_inversa_web, confirmacion_pendiente, estimar_inversa_web, firmar_entrada,
)
from tests.ayudas import elemento_html
from tests.test_matrices_web import Contenido
from tests.test_presentacion_numerica import ValoresHTML
from tests.test_procedimiento_plegable import comprobar_estructura

RUTA = "/matrices/inversa/"
SERVICIO = "frontend.web.calculadora.servicios_inversa"
MOTOR = "backend.matriz_inversa"
A = [[3, 4], [5, 6]]
B = [[1, 2], [3, 5]]
A3 = [[0, 1, 2], [1, 0, 3], [4, -3, 8]]
B3 = [[1, 2, 0], [0, 1, 1], [1, 0, 1]]
SINGULAR = [[1, 2], [2, 4]]
FUNCIONES = ("ninguna", "inversa_inversa", "traspuesta", "producto", "vector")


def entrada(funcion="ninguna", a=None, metodo="gauss_jordan", verificar=False):
    a = A if a is None else a
    datos = {"a": a, "metodo": metodo, "verificar": verificar, "funcion_adicional": funcion}
    if funcion == "producto":
        datos["b"] = B if len(a) == 2 else B3
    if funcion == "vector":
        datos["vector"] = [3, 7] if len(a) == 2 else [1, 2, 3]
    return datos


def post_datos(datos, **extra):
    post = {"orden": str(len(datos["a"])), "metodo": datos["metodo"],
            "funcion_adicional": datos["funcion_adicional"]}
    if datos.get("verificar"):
        post["verificar"] = "on"
    matrices = [("A", datos["a"])]
    if "b" in datos:
        matrices.append(("B", datos["b"]))
    if "vector" in datos:
        matrices.append(("b", [[valor] for valor in datos["vector"]]))
    for nombre, matriz in matrices:
        for i, fila in enumerate(matriz):
            for j, valor in enumerate(fila):
                post[f"celda_{nombre}_{i}_{j}"] = str(valor)
    return post | extra


def html_activo(html):
    return re.sub(r"<template\b[^>]*>.*?</template>", "", html, flags=re.S)


class PruebasPresentacionPropiedades(SimpleTestCase):
    def post(self, datos, **extra):
        respuesta = self.client.post(RUTA, post_datos(datos, **extra))
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, 'role="alert"')
        return respuesta.content.decode()

    def test_radios_unicos_y_seccion_secundaria_predeterminada(self):
        html = html_activo(self.client.get(RUTA).content.decode())
        radios = re.findall(r'<input type="radio" name="funcion_adicional" value="([^"]+)"([^>]*)>', html)
        self.assertEqual([valor for valor, _ in radios], list(FUNCIONES))
        self.assertEqual([valor for valor, attrs in radios if "checked" in attrs], ["ninguna"])
        bloque = elemento_html(html, html.index('id="aplicaciones"'), "details")
        self.assertNotIn("open", bloque.split(">", 1)[0])
        self.assertIn("Aplicaciones y propiedades", bloque)
        for indice in range(5):
            self.assertIn(f'for="id_funcion_adicional_{indice}"', bloque)
        self.assertEqual(set(Contenido(html).tablas), {"Matriz A"})

    def test_cada_opcion_explica_que_calcula_y_describe_su_radio(self):
        # P27.8 (UI-35): la ayuda se ve antes de elegir y queda asociada a su radio.
        esperadas = {
            "ninguna": "Solo calcula A⁻¹.",
            "inversa_inversa": "Comprueba (A⁻¹)⁻¹ = A.",
            "traspuesta": "Comprueba (Aᵀ)⁻¹ = (A⁻¹)ᵀ.",
            "producto": "Comprueba (AB)⁻¹ = B⁻¹A⁻¹.",
            "vector": "Calcula x = A⁻¹b y comprueba Ax = b.",
        }
        html = html_activo(self.client.get(RUTA).content.decode())
        radios = re.findall(r'<input type="radio" name="funcion_adicional" value="([^"]+)"([^>]*)>', html)
        self.assertEqual([valor for valor, _ in radios], list(esperadas))
        for valor, atributos in radios:
            with self.subTest(valor=valor):
                identificador = re.search(r'id="([^"]+)"', atributos)[1]
                self.assertIn(f'aria-describedby="{identificador}_ayuda"', atributos)
                self.assertIn(f'<p class="option-description" id="{identificador}_ayuda">{esperadas[valor]}</p>', html)
        # Con un error del campo, cada radio conserva también la descripción del error.
        error = self.client.post(RUTA, post_datos(entrada(), funcion_adicional="otra")).content.decode()
        for _, atributos in re.findall(r'<input type="radio" name="funcion_adicional" value="([^"]+)"([^>]*)>', html_activo(error)):
            self.assertRegex(atributos, r'aria-describedby="id_funcion_adicional_\d_ayuda id_funcion_adicional_error"')

    def test_campos_condicionales_y_aplicar_sin_javascript(self):
        for funcion in FUNCIONES:
            with self.subTest(funcion=funcion), patch(f"{SERVICIO}.calcular_inversa", side_effect=AssertionError("calculó")):
                html = self.post(entrada(funcion), ajustar="1")
                esperado = {"Matriz A"}
                if funcion == "producto":
                    esperado.add("Matriz B")
                elif funcion == "vector":
                    esperado.add("Vector b")
                self.assertEqual(set(Contenido(html).tablas), esperado)
                self.assertNotIn('id="resultado"', html)
                self.assertIn("<noscript>", html)
                if funcion != "ninguna":
                    detalles = elemento_html(html, html.index('id="aplicaciones"'), "details")
                    self.assertIn("open", detalles.split(">", 1)[0])

    def test_b_y_b_vector_tienen_labels_y_dimension_de_a(self):
        for funcion, nombre in (("producto", "B"), ("vector", "b")):
            with self.subTest(funcion=funcion):
                html = self.post(entrada(funcion, a=A3), ajustar="1")
                campos = Contenido(html).campos
                nombres = [n for n in campos if n.startswith(f"celda_{nombre}_")]
                self.assertEqual(len(nombres), 9 if funcion == "producto" else 3)
                for campo in nombres:
                    self.assertIn(f'for="id_{campo}"', html)
                self.assertLess(html.index('id="aplicaciones"'), html.index(f'data-matriz="{nombre}"'))

    def test_resultados_comparados_con_motor_y_panel_unico(self):
        for metodo in ("gauss_jordan", "directo_2x2"):
            for funcion in FUNCIONES:
                with self.subTest(metodo=metodo, funcion=funcion):
                    datos = entrada(funcion, metodo=metodo)
                    servicio = calcular_inversa_web(datos)
                    html = self.post(datos)
                    tablas = Contenido(html).tablas
                    self.assertEqual(tablas[servicio["etiqueta_final"]], servicio["adicional"]["resultado"])
                    self.assertIn(servicio["expresion_final"], html)
                    self.assertEqual(html.count('class="panel panel-final"'), 1)
                    self.assertEqual(html.count('id="final-title"'), 1)
                    comprobar_estructura(self, html)
                    self.assertLess(html.index('id="procedimiento"'), html.index('class="panel panel-final"'))

    def test_propiedades_3x3_sin_selector_de_metodo(self):
        for funcion in FUNCIONES:
            with self.subTest(funcion=funcion):
                html = html_activo(self.post(entrada(funcion, a=A3)))
                self.assertNotIn('type="radio" name="metodo"', html)
                self.assertIn('type="hidden" name="metodo" value="gauss_jordan"', html)
                self.assertIn('id="resultado"', html)

    def test_traspuesta_muestra_ambos_lados(self):
        html = self.post(entrada("traspuesta"))
        tablas = Contenido(html).tablas
        self.assertEqual(tablas["Traspuesta de A"], [["3", "5"], ["4", "6"]])
        self.assertEqual(tablas["Inversa de Aᵀ para la comparación"], [["-3", "5/2"], ["2", "-3/2"]])
        self.assertEqual(tablas["Traspuesta de la inversa de A"], tablas["Inversa de Aᵀ para la comparación"])
        self.assertIn("Ambas matrices coinciden exactamente.", html)

    def test_producto_muestra_matrices_intermedias_y_comparacion(self):
        html = self.post(entrada("producto"))
        tablas = Contenido(html).tablas
        self.assertEqual(tablas["Producto AB"], [["15", "26"], ["23", "40"]])
        self.assertEqual(tablas["Inversa de B"], [["-5", "2"], ["3", "-1"]])
        self.assertEqual(tablas["Inversa de AB para la comparación"], tablas["Producto de B⁻¹ por A⁻¹"])
        self.assertIn("primero B⁻¹ y después A⁻¹", html)

    def test_ejemplo_de_clase_x_5_menos3_y_comprobacion(self):
        for metodo in ("gauss_jordan", "directo_2x2"):
            with self.subTest(metodo=metodo):
                html = self.post(entrada("vector", metodo=metodo))
                tablas = Contenido(html).tablas
                self.assertEqual(tablas["Vector solución mediante la inversa"], [["5"], ["-3"]])
                self.assertEqual(tablas["Producto de A⁻¹ por b"], [["5"], ["-3"]])
                self.assertEqual(tablas["Producto Ax de comprobación"], [["3"], ["7"]])
                for derivacion in ("Ax = b", "A⁻¹Ax = A⁻¹b", "A⁻¹A = I", "Ix = A⁻¹b", "x = A⁻¹b"):
                    self.assertIn(derivacion, html)
                self.assertIn("El vector obtenido satisface el sistema.", html)
                self.assertIn("(A⁻¹b)₁ = (-3)·3 + 2·7 = 5", html)
                self.assertIn("(Ax)₂ = 5·5 + 6·(-3) = 7", html)

    def test_verificacion_p26_8_precede_la_funcion_adicional(self):
        for funcion in FUNCIONES[1:]:
            with self.subTest(funcion=funcion):
                html = self.post(entrada(funcion, verificar=True))
                self.assertIn("Ambos productos son la matriz identidad.", html)
                self.assertLess(html.index('id="inverse-verification-title"'), html.index('id="inverse-additional-start"'))

    def test_singular_a_es_condicion_matematica_en_todos_los_modos(self):
        for funcion in FUNCIONES:
            with self.subTest(funcion=funcion):
                html = self.post(entrada(funcion, a=SINGULAR))
                self.assertIn("La matriz no tiene inversa.", html)
                self.assertEqual(html.count('class="panel panel-final"'), 1)
                if funcion == "vector":
                    self.assertIn("No se puede usar x = A⁻¹b porque A no tiene inversa.", html)
                    self.assertNotIn("infinitas soluciones", html)
                    self.assertNotIn("no tiene solución", html)

    def test_singular_b_muestra_condicion_natural_y_detiene_calculo(self):
        datos = {**entrada("producto"), "b": SINGULAR}
        with patch(f"{MOTOR}.resolver_operacion_matrices", side_effect=AssertionError("multiplicó B singular")):
            html = self.post(datos)
        self.assertIn("La propiedad del producto no puede aplicarse porque B no tiene inversa.", html)
        self.assertNotIn('aria-label="Producto AB"', html)
        self.assertEqual(html.count('class="panel panel-final"'), 1)

    def test_exacto_decimal_incluye_resultado_y_comparaciones(self):
        fracciones = [[3, 1], [0, 1]]
        for funcion in FUNCIONES[1:]:
            with self.subTest(funcion=funcion):
                datos = entrada(funcion, a=fracciones)
                if funcion == "vector":
                    datos["vector"] = [1, 0]
                html = self.post(datos)
                valores = ValoresHTML(html).valores
                self.assertTrue(any("0.3333" in v["decimales"]["4"] for v in valores))
                self.assertIn('data-numeric-controls hidden', html)
                if funcion != "inversa_inversa":
                    final = html[html.index('class="panel panel-final"'):]
                    self.assertTrue(ValoresHTML(final).valores)
                self.assertEqual(html.count('id="numeric-mode"'), 1)

    def test_no_recalcula_a_y_usa_mismo_metodo_para_inversiones_adicionales(self):
        inversiones_extra = {"ninguna": 0, "inversa_inversa": 1, "traspuesta": 1, "producto": 2, "vector": 0}
        for funcion, cantidad in inversiones_extra.items():
            with self.subTest(funcion=funcion), \
                    patch(f"{SERVICIO}.calcular_inversa", wraps=matriz_inversa.calcular_inversa) as principal, \
                    patch(f"{MOTOR}.calcular_inversa", wraps=matriz_inversa.calcular_inversa) as adicionales:
                self.post(entrada(funcion, metodo="directo_2x2"))
                principal.assert_called_once_with(A, "directo_2x2")
                self.assertEqual(adicionales.call_count, cantidad)
                self.assertTrue(all(llamada.args[1] == "directo_2x2" for llamada in adicionales.call_args_list))

    def test_resultado_no_afirma_igualdad_si_comparacion_exacta_falla(self):
        for funcion, clave in (("inversa_inversa", "coincide_con_a"), ("traspuesta", "coinciden"), ("producto", "coinciden")):
            datos = entrada(funcion)
            inversa = matriz_inversa.calcular_inversa(A)["inversa"]
            calculo = matriz_inversa.aplicar_funcion_adicional(funcion, A, inversa, b=datos.get("b"))
            with self.subTest(funcion=funcion), patch(f"{SERVICIO}.aplicar_funcion_adicional", return_value=calculo | {clave: False}):
                html = self.post(datos)
                final = html[html.index('class="panel panel-final"'):]
                self.assertIn("≠", final)


class PruebasPresupuestoPropiedades(SimpleTestCase):
    def test_total_tiene_inversiones_productos_y_verificacion_elegidos(self):
        cantidades = {"ninguna": (1, 0), "inversa_inversa": (2, 0), "traspuesta": (2, 0),
                      "producto": (3, 2), "vector": (1, 2)}
        for funcion, (inversiones, productos) in cantidades.items():
            for verificar in (False, True):
                with self.subTest(funcion=funcion, verificar=verificar), \
                        patch(f"{SERVICIO}.estimar_gauss_jordan", wraps=estimar_gauss_jordan) as estimar, \
                        patch(f"{SERVICIO}.estimar_producto", wraps=estimar_producto) as producto, \
                        patch(f"{SERVICIO}.calcular_inversa", side_effect=AssertionError("calculó al estimar")), \
                        patch(f"{MOTOR}.resolver_operacion_matrices", side_effect=AssertionError("calculó al estimar")):
                    estimacion = estimar_inversa_web(entrada(funcion, a=A3, verificar=verificar))
                    self.assertEqual(estimar.call_count, inversiones)
                    self.assertEqual(producto.call_count, productos + 2 * verificar)
                    self.assertGreater(estimacion.procedimiento, 0)
                    if funcion == "vector":
                        self.assertTrue(all(llamada.args == (3, 3, 1) for llamada in producto.call_args_list[:2]))

    def test_base_sin_adicional_conserva_estimacion_p26_2(self):
        self.assertEqual(estimar_inversa_web(entrada(a=A3)),
                         estimar_gauss_jordan(3, 6, columnas_pivote=3, perfil=perfil_numerico(A3)))

    def test_verificar_agrega_exactamente_dos_productos_al_total(self):
        for funcion in FUNCIONES:
            with self.subTest(funcion=funcion):
                sin = estimar_inversa_web(entrada(funcion, a=A3))
                con = estimar_inversa_web(entrada(funcion, a=A3, verificar=True))
                self.assertGreater(con.calculo, sin.calculo)
                self.assertGreater(con.procedimiento, sin.procedimiento)
                self.assertEqual([parte.operacion for parte in con.partes[-2:]], ["producto", "producto"])

    def test_directo2x2_se_modela_sin_gauss_y_no_confirma_casos_minimos(self):
        for funcion in FUNCIONES:
            with self.subTest(funcion=funcion), \
                    patch(f"{SERVICIO}.estimar_gauss_jordan", side_effect=AssertionError("estimó GJ directo")):
                datos = entrada(funcion, metodo="directo_2x2", verificar=True)
                costo = estimar_inversa_web(datos)
                self.assertEqual(categoria(costo), Categoria.NORMAL)
                self.assertIsNone(confirmacion_pendiente(datos))

    def test_firma_canonica_liga_todos_los_componentes(self):
        for funcion in FUNCIONES:
            with self.subTest(funcion=funcion):
                datos = entrada(funcion)
                firma = firmar_entrada(datos)
                self.assertRegex(firma, r"^[0-9a-f]{64}$")
                self.assertEqual(firma, firmar_entrada(dict(datos)))
                exactos = {**datos, "a": [[Fraction(v) for v in fila] for fila in datos["a"]]}
                self.assertEqual(firma, firmar_entrada(exactos))
                cambios = [{"a": [[3, 4], [5, 7]]}, {"metodo": "directo_2x2"}, {"verificar": True},
                           {"funcion_adicional": "traspuesta" if funcion != "traspuesta" else "ninguna"}]
                if funcion == "producto":
                    cambios.append({"b": [[1, 2], [3, 6]]})
                elif funcion == "vector":
                    cambios.append({"vector": [3, 8]})
                for cambio in cambios:
                    self.assertNotEqual(firma, firmar_entrada(datos | cambio))

    def test_una_confirmacion_previa_ejecuta_todo_sin_segundo_aviso(self):
        for funcion in FUNCIONES:
            with self.subTest(funcion=funcion), patch(f"{SERVICIO}.categoria", return_value=Categoria.PESADA):
                datos = entrada(funcion, verificar=True)
                with patch(f"{SERVICIO}.calcular_inversa", side_effect=AssertionError("calculó antes de confirmar")), \
                        patch(f"{MOTOR}.calcular_inversa", side_effect=AssertionError("invirtió antes de confirmar")), \
                        patch(f"{MOTOR}.resolver_operacion_matrices", side_effect=AssertionError("multiplicó antes de confirmar")):
                    respuesta = self.client.post(RUTA, post_datos(datos))
                html = respuesta.content.decode()
                self.assertEqual(html.count("data-confirmacion"), 1)
                self.assertNotIn('id="resultado"', html)
                firma = re.search(r'name="confirmacion" value="([0-9a-f]{64})"', html).group(1)
                respuesta = self.client.post(RUTA, post_datos(datos, confirmacion=firma))
                self.assertNotContains(respuesta, "data-confirmacion")
                self.assertContains(respuesta, 'id="resultado"')
                self.assertNotContains(respuesta, 'role="alert"')

    def test_cambiar_b_vector_o_funcion_invalida_confirmacion_sin_calcular(self):
        cambios = [(entrada("producto"), {"b": [[1, 2], [3, 6]]}),
                   (entrada("vector"), {"vector": [3, 8]}),
                   (entrada("ninguna"), {"funcion_adicional": "traspuesta"})]
        for original, cambio in cambios:
            with self.subTest(cambio=cambio), patch(f"{SERVICIO}.categoria", return_value=Categoria.PESADA), \
                    patch(f"{SERVICIO}.calcular_inversa", side_effect=AssertionError("usó firma anterior")):
                firma = firmar_entrada(original)
                respuesta = self.client.post(RUTA, post_datos(original | cambio, confirmacion=firma))
                self.assertContains(respuesta, "data-confirmacion")
                self.assertNotContains(respuesta, 'id="resultado"')

    def test_cancelar_conserva_funcion_y_entradas_sin_ejecutar(self):
        for funcion in ("producto", "vector"):
            with self.subTest(funcion=funcion), patch(f"{SERVICIO}.categoria", return_value=Categoria.PESADA), \
                    patch(f"{SERVICIO}.calcular_inversa", side_effect=AssertionError("calculó al cancelar")):
                datos = entrada(funcion, verificar=True)
                respuesta = self.client.post(RUTA, post_datos(datos, ajustar="1", confirmacion=firmar_entrada(datos)))
                html = respuesta.content.decode()
                self.assertNotIn("data-confirmacion", html)
                self.assertNotIn('id="resultado"', html)
                campos = Contenido(html).campos
                self.assertIn("checked", campos["verificar"])
                nombre = "celda_B_1_1" if funcion == "producto" else "celda_b_1_0"
                self.assertEqual(campos[nombre]["value"], "5" if funcion == "producto" else "7")
