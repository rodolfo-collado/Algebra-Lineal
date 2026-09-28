"""Aridad por operación: colecciones exactas, contrato HTTP y procedimientos."""

from copy import deepcopy
from fractions import Fraction as F
import os
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.conf import settings
from django.http import QueryDict
from django.test import SimpleTestCase
from django.utils.html import strip_tags

from backend.matrices import producto_punto, resolver_coleccion_matrices, resolver_operacion_matrices
from backend.operandos import CELDAS_MAXIMAS, OPERANDOS_MAXIMOS, nombre_matriz
from backend.vectores import operar_vectores
from frontend.web.calculadora.forms import VectoresForm
from frontend.web.calculadora.forms_matrices import MatricesForm
from frontend.web.calculadora.opciones_matrices import configuracion_operandos
from frontend.web.calculadora.opciones_vectores import DIMENSION_MAXIMA as DIMENSION_VECTORES, nombres_vectores
from frontend.web.calculadora.servicios_matrices import operar_matrices
from tests.test_vectores_web import datos_vectores, combinacion, RUTA as VECTORES
from tests.test_matrices_web import Contenido, datos_matrices, RUTA as MATRICES
from tests.test_multiplicacion_matrices_web import datos_matriz_vector


def datos_coleccion(operacion, matrices, metodo="comparar"):
    datos = {"operacion": operacion, "cantidad": str(len(matrices)),
             "filas": str(len(matrices[0])), "columnas": str(len(matrices[0][0]))}
    for indice, matriz in enumerate(matrices):
        nombre = nombre_matriz(indice)
        if operacion == "producto" and indice:
            datos[f"columnas_{nombre.lower()}"] = str(len(matriz[0]))
        for i, fila in enumerate(matriz):
            for j, valor in enumerate(fila):
                datos[f"celda_{nombre}_{i}_{j}"] = str(valor)
    if operacion == "producto":
        datos["metodo"] = metodo
    return datos


def llena(filas, columnas):
    return [[1] * columnas for _ in range(filas)]


def celdas_dibujadas(html):
    """Celdas de matriz o componentes de vector que el servidor dibujó (sin plantillas inertes)."""
    return sum(nombre.startswith("celda_") or "data-cell" in atributos for nombre, atributos in Contenido(html).campos.items())


class PruebasColecciones(SimpleTestCase):
    def test_vectores_suma_y_resta_exactas_sin_mutar(self):
        vectores = [[F(1, 3), 2], [F(1, 3), -3], [F(1, 3), 4], [1, 5]]
        copia = deepcopy(vectores)
        self.assertEqual(operar_vectores("suma", vectores[:2]), [F(2, 3), -1])
        self.assertEqual(operar_vectores("suma", vectores), [2, 8])
        self.assertEqual(operar_vectores("resta", vectores), [F(-4, 3), -4])
        self.assertEqual(vectores, copia)

    def test_vectores_rechazan_dimension_y_minimo(self):
        for op in ("suma", "resta"):
            for vectores in ([], [[1]], [[1], [2], [3, 4]], [[1], [2], [True]], [[1], [2], []]):
                with self.subTest(op=op, vectores=vectores), self.assertRaises(ValueError):
                    operar_vectores(op, vectores)

    def test_producto_punto_sigue_binario(self):
        self.assertEqual(producto_punto([1, 2], [3, 4]), 11)
        with self.assertRaises(TypeError):
            producto_punto([1], [2], [3])

    def test_matrices_suma_resta_y_minimo(self):
        matrices = [[[F(1, 3), 2]], [[F(1, 3), -3]], [[F(1, 3), 4]]]
        self.assertEqual(resolver_coleccion_matrices("suma", matrices[:2])["resultado"], [[F(2, 3), -1]])
        self.assertEqual(resolver_coleccion_matrices("suma", matrices)["resultado"], [[1, 3]])
        resta = resolver_coleccion_matrices("resta", matrices)
        self.assertEqual(resta["resultado"], [[F(-1, 3), 1]])
        self.assertEqual(resta["pasos"][0][1]["operandos"], (2, -3, 4))
        for op in ("suma", "resta", "producto"):
            for entradas in ([], [[[1]]], [[[1]], [[2]], [[3, 4], [5, 6]]]):
                with self.subTest(op=op, entradas=entradas), self.assertRaises(ValueError):
                    resolver_coleccion_matrices(op, entradas)

    def test_producto_tres_y_cuatro_rectangulares_con_intermedios(self):
        matrices = [[[1, 2]], [[1, 0, 2], [0, 1, 3]], [[1, 2], [3, 4], [5, 6]], [[1], [2]]]
        copia = deepcopy(matrices)
        tres = resolver_coleccion_matrices("producto", matrices[:3])
        cuatro = resolver_coleccion_matrices("producto", matrices)
        self.assertEqual(tres["resultado"], [[47, 58]])
        self.assertEqual(cuatro["resultado"], [[163]])
        self.assertEqual([e["calculo"]["resultado"] for e in cuatro["etapas"]], [[[1, 2, 8]], [[47, 58]], [[163]]])
        self.assertEqual(matrices, copia)
        for etapa in cuatro["etapas"]:
            calculo = etapa["calculo"]
            self.assertEqual([[p["resultado"] for p in fila] for fila in calculo["pasos"]], calculo["resultado"])
            self.assertEqual([list(c["resultado"]) for c in calculo["columnas"]], list(map(list, zip(*calculo["resultado"]))))

    def test_incompatibilidad_intermedia_antes_de_calcular(self):
        matrices = [[[1, 2]], [[1, 2, 3], [4, 5, 6]], [[1], [2]]]
        with patch("backend.matrices.resolver_operacion_matrices") as motor:
            with self.assertRaisesRegex(ValueError, "entre B y C"):
                resolver_coleccion_matrices("producto", matrices)
            motor.assert_not_called()

    def test_colecciones_sin_tope_fijo_y_nombres_mas_alla_de_z(self):
        self.assertEqual(operar_vectores("suma", [[1]] * 40), [40])
        self.assertEqual(resolver_coleccion_matrices("suma", [[[1]]] * 40)["resultado"], [[40]])
        self.assertEqual([nombre_matriz(i) for i in (0, 25, 26, 27, 51, 52)], ["A", "Z", "AA", "AB", "AZ", "BA"])


class PruebasWebColecciones(SimpleTestCase):
    def test_vectores_tres_y_cuatro_con_procedimiento(self):
        for op, esperado in (("suma", "(12, 15, 18)"), ("resta", "(-10, -11, -12)")):
            respuesta = self.client.post(VECTORES, datos_vectores(op, vectores=3, u=[1, 2, 3], v=[4, 5, 6], v3=[7, 8, 9]))
            self.assertContains(respuesta, 'id="resultado"')
            self.assertIn(esperado, strip_tags(respuesta.content.decode()))
            self.assertIn("1 + 4 + 7" if op == "suma" else "1 - 4 - 7", strip_tags(respuesta.content.decode()))

    def test_vectores_contrato_estricto(self):
        base = datos_vectores("suma", vectores=3, u=[1], v=[2], v3=[3])
        casos = [base | {"vectores": "1"}, base | {"v3_1": "4"}, base | {"escalar": "2"},
                 base | {"intruso": "2"}, base | {"operacion": "escalar", "escalar": "1"}]
        faltante = dict(base)
        del faltante["v3_0"]
        casos.append(faltante)
        duplicado = QueryDict("", mutable=True)
        duplicado.update(base)
        duplicado.appendlist("u_0", "9")
        casos.append(duplicado)
        for datos in casos:
            with self.subTest(datos=datos):
                self.assertFalse(VectoresForm(datos).is_valid())

    def test_combinacion_reutiliza_coleccion_sin_maximo(self):
        respuesta = self.client.post(VECTORES, combinacion([[1, 0]] * 12, [3, 0]))
        self.assertContains(respuesta, 'id="resultado"')
        self.assertContains(respuesta, "c12")

    def test_matrices_suma_resta_elemento_a_elemento(self):
        for op, esperado in (("suma", [["12", "15"]]), ("resta", [["-10", "-11"]])):
            form = MatricesForm(datos_coleccion(op, [[[1, 2]], [[4, 5]], [[7, 8]]]))
            self.assertTrue(form.is_valid(), form.errors)
            resultado = operar_matrices(form.cleaned_data["entrada"])
            self.assertEqual(resultado["matriz"], esperado)
            self.assertEqual(len(resultado["entradas"]), 3)
            self.assertEqual(resultado["desarrollo"][0][0], "1 + 4 + 7" if op == "suma" else "1 − 4 − 7")
            self.assertContains(self.client.post(MATRICES, form.data), 'id="resultado"')

    def test_producto_ambos_metodos_comparten_motor_por_etapa(self):
        matrices = [[[1, 2]], [[1, 0, 2], [0, 1, 3]], [[1, 2], [3, 4], [5, 6]], [[1], [2]]]
        for cantidad in (3, 4):
            for metodo in ("fila_columna", "columnas", "comparar"):
                datos = datos_coleccion("producto", matrices[:cantidad], metodo)
                with patch("backend.matrices.resolver_operacion_matrices", wraps=resolver_operacion_matrices) as motor:
                    respuesta = self.client.post(MATRICES, datos)
                self.assertEqual(motor.call_count, cantidad - 1)
                self.assertContains(respuesta, 'id="resultado"')
                texto = strip_tags(respuesta.content.decode())
                for nombre in ("AB", "ABC"):
                    self.assertIn(f"= {nombre}", texto)
                self.assertIn("Resultado intermedio AB:", texto)
                self.assertIn("ABC = (AB)C" if cantidad == 3 else "ABCD = ((AB)C)D", texto)
                self.assertIn("Paso 2: AB · C = ABC", texto)
                if metodo in ("fila_columna", "comparar"):
                    self.assertIn("Fila por columna", texto)
                    self.assertIn("fila₁(AB) · columna₁(C)", texto)
                if metodo in ("columnas", "comparar"):
                    self.assertIn("Por columnas", texto)
                    self.assertIn("Columnas de AB:", texto)
                    self.assertIn("ABC = [ABc₁", texto)

    def test_matrices_dimensiones_y_campos_ajenos(self):
        datos = datos_coleccion("producto", [[[1, 2]], [[1, 2, 3], [4, 5, 6]], [[1], [2]]])
        self.assertFalse(MatricesForm(datos).is_valid())
        base = datos_coleccion("suma", [[[1]], [[2]], [[3]]])
        for invalido in (base | {"cantidad": "1"}, base | {"celda_C_1_0": "0"}, base | {"columnas_c": "1"},
                         base | {"metodo": "columnas"}, base | {"escalar": "2"}, base | {"cantidad": "2"}):
            with self.subTest(datos=invalido):
                self.assertFalse(MatricesForm(invalido).is_valid())

    def test_unaria_y_ax_no_admiten_operandos_extra(self):
        for datos in (datos_matrices("traspuesta", a=[[1, 2]]), datos_matriz_vector()):
            self.assertContains(self.client.post(MATRICES, datos), 'id="resultado"')
            for extra in ({"cantidad": "3"}, {"celda_C_0_0": "1"}):
                self.assertFalse(MatricesForm(datos | extra).is_valid())

    def test_exactos_decimales_en_cada_etapa(self):
        respuesta = self.client.post(MATRICES, datos_coleccion("producto", [[["1/3"]], [[1]], [[1]]]))
        html = respuesta.content.decode()
        self.assertIn("1/3", strip_tags(html))
        self.assertIn("0.3333", html)
        self.assertEqual(html.count('id="numeric-mode"'), 1)
        self.assertEqual(html.count('id="procedimiento"'), 1)

    def test_aplicar_conserva_campos_y_dimensiones_adicionales(self):
        datos = datos_coleccion("producto", [[[1, 2]], [[1, 2, 3], [4, 5, 6]], [[1], [2], [3]]])
        respuesta = self.client.post(MATRICES, datos | {"ajustar": "1"})
        self.assertContains(respuesta, 'name="columnas_c"')
        self.assertContains(respuesta, 'name="celda_C_2_0"')
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_web_cuarenta_operandos(self):
        respuesta = self.client.post(MATRICES, datos_coleccion("suma", [[[1]]] * 40))
        self.assertContains(respuesta, 'id="resultado"')
        self.assertContains(respuesta, 'name="celda_AN_0_0"')


class PruebasPresupuesto(SimpleTestCase):
    """Presupuesto de entrada: operandos × filas × columnas se acota antes de construir campos."""

    def post(self, ruta, datos):
        # El cliente de pruebas relanza cualquier excepción de la vista: un 500 haría fallar la prueba.
        respuesta = self.client.post(ruta, datos)
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.content.decode()

    def test_mas_de_diez_operandos_de_varios_tamanos(self):
        html = self.post(MATRICES, datos_coleccion("suma", [llena(3, 4)] * 12))
        self.assertEqual(Contenido(html).tablas["Matriz resultado"], [["12"] * 4] * 3)
        html = self.post(MATRICES, datos_coleccion("producto", [llena(3, 3)] * 12, "fila_columna"))
        self.assertEqual(Contenido(html).tablas["Matriz resultado"], [[str(3 ** 11)] * 3] * 3)
        self.assertIn("Paso 11: ABCDEFGHIJK · L = ABCDEFGHIJKL", strip_tags(html))
        vectores = {nombre: [1] * 4 for nombre in nombres_vectores("suma", 12)}
        self.assertIn("(12, 12, 12, 12)", strip_tags(self.post(VECTORES, datos_vectores("suma", vectores=12, **vectores))))

    def test_cantidad_absurda_se_descarta_antes_de_construir_la_estructura(self):
        for operacion in ("suma", "resta", "producto"):
            datos = {"operacion": operacion, "cantidad": "100000", "filas": "10", "columnas": "10", "columnas_b": "10"}
            with self.subTest(operacion=operacion), patch(
                    "frontend.web.calculadora.forms_matrices.configuracion_operandos", wraps=configuracion_operandos) as configurar:
                form = MatricesForm(datos)
                self.assertEqual([llamada.args[1] for llamada in configurar.call_args_list], [2])
                self.assertEqual(len(form.nombres_celdas), 200)
                self.assertFalse(form.is_valid())
                self.assertEqual(form.errors["cantidad"], [f"La interfaz admite hasta {OPERANDOS_MAXIMOS} matrices por operación."])
        with patch("frontend.web.calculadora.forms.nombres_vectores", wraps=nombres_vectores) as nombrar:
            form = VectoresForm({"operacion": "suma", "vectores": "100000", "dimension": "10"})
            self.assertFalse(form.is_valid())
            self.assertEqual(len(form.estructura()["filas"]), OPERANDOS_MAXIMOS)
        self.assertTrue(nombrar.called)
        self.assertTrue(all(llamada.args[1] <= OPERANDOS_MAXIMOS for llamada in nombrar.call_args_list))
        self.assertEqual(form.errors["vectores"], [f"La interfaz admite hasta {OPERANDOS_MAXIMOS} vectores por operación."])

    def test_matrices_de_tamano_maximo_con_una_cantidad_razonable(self):
        nueve = [llena(10, 10)] * 9  # 900 celdas: justo el presupuesto
        for operacion, esperado in (("suma", "9"), ("producto", str(10 ** 8))):
            with self.subTest(operacion=operacion):
                datos = datos_coleccion(operacion, nueve, "fila_columna")
                self.assertLess(len(datos) + 1, settings.DATA_UPLOAD_MAX_NUMBER_FIELDS)  # + csrfmiddlewaretoken
                html = self.post(MATRICES, datos)
                self.assertEqual(Contenido(html).tablas["Matriz resultado"], [[esperado] * 10] * 10)
        self.assertTrue(MatricesForm(datos_coleccion("resta", [llena(5, 5)] * 36)).is_valid())  # 36 × 5×5 = 900

    def test_estructura_que_excede_el_presupuesto_se_rechaza_con_mensaje_legible(self):
        producto = {"operacion": "producto", "cantidad": "10", "metodo": "fila_columna", "filas": "10", "columnas": "10",
                    **{f"columnas_{nombre_matriz(i).lower()}": "10" for i in range(1, 10)}}
        for datos, cantidad, celdas in (({"operacion": "suma", "cantidad": "37", "filas": "5", "columnas": "5"}, 37, 925),
                                        (producto, 10, 1000)):
            mensaje = (f"Las {cantidad} matrices suman {celdas} celdas y la interfaz admite hasta {CELDAS_MAXIMAS}: "
                       "quita matrices o reduce sus filas y columnas.")
            for extra in ({}, {"ajustar": "1"}):
                with self.subTest(operacion=datos["operacion"], **extra):
                    form = MatricesForm(datos | extra, ajustar=bool(extra))
                    self.assertFalse(form.is_valid())
                    self.assertEqual(form.non_field_errors(), [mensaje])
                    # Se dibujan las mismas matrices con las dimensiones iniciales, dentro del presupuesto.
                    self.assertEqual(len(form.matrices), cantidad)
                    self.assertEqual(len(form.nombres_celdas), cantidad * 4)
                    html = self.post(MATRICES, datos | extra)
                    self.assertIn(mensaje, html)
                    self.assertNotIn('id="resultado"', html)
                    self.assertEqual(celdas_dibujadas(html), cantidad * 4)

    def test_posts_manipulados_no_producen_errores_internos(self):
        for cantidad in ("100000", "1" + "0" * 40, "1e9", "-5"):
            for operacion, extra in (("suma", {}), ("producto", {"ajustar": "1"}), ("traspuesta", {})):
                datos = {"operacion": operacion, "cantidad": cantidad, "filas": "10", "columnas": "10",
                         "columnas_b": "10", "metodo": "comparar", "celda_ZZ_0_0": "1"} | extra
                with self.subTest(ruta=MATRICES, cantidad=cantidad, operacion=operacion):
                    html = self.post(MATRICES, datos)
                    self.assertIn('class="alert error"', html)
                    self.assertNotIn('id="resultado"', html)
                    self.assertLessEqual(celdas_dibujadas(html), CELDAS_MAXIMAS)
            for operacion, extra in (("suma", {}), ("combinacion", {"ajustar": "1"}), ("escalar", {})):
                datos = {"operacion": operacion, "vectores": cantidad, "dimension": "10", "u_0": "1"} | extra
                with self.subTest(ruta=VECTORES, cantidad=cantidad, operacion=operacion):
                    html = self.post(VECTORES, datos)
                    self.assertNotIn('id="resultado"', html)
                    self.assertLessEqual(celdas_dibujadas(html), CELDAS_MAXIMAS)

    def test_aridades_fijas_no_crecen_con_la_cantidad(self):
        for datos, entradas in ((datos_matrices("traspuesta", a=[[1, 2]]), ("A",)),
                                (datos_matrices("escalar", a=[[1, 2]], escalar=3), ("A",)),
                                (datos_matriz_vector(), ("A", "x"))):
            with self.subTest(operacion=datos["operacion"]):
                form = MatricesForm(datos | {"cantidad": "100000"})
                self.assertEqual(form.configuracion["matrices"], entradas)
                self.assertFalse(form.is_valid())
                self.assertIn("cantidad de matrices", form.non_field_errors()[0])
                self.assertIn('id="resultado"', self.post(MATRICES, datos))
        form = VectoresForm(datos_vectores("escalar", escalar="2", vectores=100000, u=[1, 2]))
        self.assertFalse(form.is_valid())
        self.assertEqual([fila["nombre"] for fila in form.estructura()["filas"]], ["u"])

    def test_combinacion_con_mas_de_seis_generadores_hasta_el_tope(self):
        for cantidad in (7, OPERANDOS_MAXIMOS):
            with self.subTest(generadores=cantidad):
                html = self.post(VECTORES, combinacion([[1, 0]] * cantidad, [3, 0]))
                self.assertIn('id="resultado"', html)
                self.assertIn(f"c{cantidad}", strip_tags(html))
        form = VectoresForm(combinacion([[1, 0]] * (OPERANDOS_MAXIMOS + 1), [3, 0]))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["vectores"], [f"La interfaz admite hasta {OPERANDOS_MAXIMOS} vectores por operación."])

    def test_lo_que_la_interfaz_dibuja_siempre_se_puede_enviar(self):
        # Peor envío de matrices: un producto de 50 operandos (una dimensión extra por matriz) con 900 celdas.
        cadena = [llena(3, 6) if i % 2 == 0 else llena(6, 3) for i in range(OPERANDOS_MAXIMOS)]
        self.assertEqual(sum(len(m) * len(m[0]) for m in cadena), CELDAS_MAXIMAS)
        datos = datos_coleccion("producto", cadena, "fila_columna")
        self.assertLessEqual(len(datos) + 2, settings.DATA_UPLOAD_MAX_NUMBER_FIELDS)  # + csrfmiddlewaretoken y ajustar
        self.assertIn('id="resultado"', self.post(MATRICES, datos))
        # En vectores cierra por construcción: 50 generadores y b de dimensión máxima.
        self.assertLessEqual((OPERANDOS_MAXIMOS + 1) * DIMENSION_VECTORES, CELDAS_MAXIMAS)
        datos = combinacion([[1] * DIMENSION_VECTORES] * OPERANDOS_MAXIMOS, [1] * DIMENSION_VECTORES)
        self.assertLessEqual(len(datos) + 2, settings.DATA_UPLOAD_MAX_NUMBER_FIELDS)
        self.assertIn('id="resultado"', self.post(VECTORES, datos))
