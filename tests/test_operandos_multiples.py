"""Aridad por operación: colecciones exactas, contrato HTTP, procedimientos y presupuesto común."""

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
from backend.operandos import CAMPOS_MAXIMOS, CELDAS_MAXIMAS, OPERANDOS_MAXIMOS, nombre_matriz
from backend.vectores import evaluar_combinacion_lineal, operar_vectores
from frontend.web.calculadora.forms import VectoresForm
from frontend.web.calculadora.forms_expresiones import ExpresionMatricialForm, nombre_libre
from frontend.web.calculadora.presupuesto_expresiones import firmar_entrada
from frontend.web.calculadora.opciones_vectores import DIMENSION_MAXIMA as DIMENSION_VECTORES, nombres_vectores
from tests.ayudas import elemento_html
from tests.test_procedimiento_plegable import comprobar_estructura, partes
from tests.test_vectores_web import datos_vectores, combinacion, RUTA as VECTORES
from tests.test_matrices_web import Contenido, datos_simbolos, matriz, RUTA as MATRICES


def nombres(cantidad):
    """A … Z, A1 …: los nombres que la interfaz propone al agregar símbolos."""
    usados = []
    for _ in range(cantidad):
        usados.append(nombre_libre(set(usados)))
    return usados


def datos_coleccion(operacion, matrices, metodo="comparar"):
    """Varias matrices operadas en cadena como una expresión: A + B + C…, A - B - C… o ABC…"""
    simbolos = [matriz(nombre, valor) for nombre, valor in zip(nombres(len(matrices)), matrices)]
    etiquetas = [simbolo["nombre"] for simbolo in simbolos]
    if operacion == "producto":
        expresion = "".join(etiquetas) if all(len(nombre) == 1 for nombre in etiquetas) else "*".join(etiquetas)
    else:
        expresion = (" + " if operacion == "suma" else " - ").join(etiquetas)
    return datos_simbolos(expresion, simbolos, metodo=metodo if operacion == "producto" else None)


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

    def test_errores_de_suma_y_resta_nombran_los_vectores_como_la_interfaz(self):
        self.assertEqual(nombres_vectores("suma", 4), ("u", "v", "v3", "v4"))
        for operacion, verbo in (("suma", "sumar"), ("resta", "restar")):
            with self.subTest(operacion=operacion):
                with self.assertRaises(ValueError) as dimension:
                    operar_vectores(operacion, [[1], [2], [3, 4], [5]])
                self.assertEqual(str(dimension.exception), f"No se pueden {verbo} vectores de distinta dimensión: "
                                                           "u tiene 1, v tiene 1, v3 tiene 2, v4 tiene 1 componentes.")
                with self.assertRaisesRegex(ValueError, "^El vector v no tiene componentes.$"):
                    operar_vectores(operacion, [[1], [], [3]])
        # La combinación lineal conserva v1, v2, … y el objetivo b.
        with self.assertRaisesRegex(ValueError, "v1 tiene 1, v2 tiene 2, b tiene 1 componentes"):
            evaluar_combinacion_lineal([[1], [1, 2]], [1])

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
        self.assertContains(respuesta, "x12")

    def test_matrices_suma_y_resta_de_tres_paso_a_paso(self):
        # El árbol agrupa por la izquierda: (A + B) + C. Cada paso conserva su desarrollo por entradas.
        for op, esperado, primero, segundo in (("suma", [["12", "15"]], "1 + 4", "5 + 7"), ("resta", [["-10", "-11"]], "1 − 4", "(-3) − 7")):
            with self.subTest(op=op):
                html = self.client.post(MATRICES, datos_coleccion(op, [[[1, 2]], [[4, 5]], [[7, 8]]])).content.decode()
                self.assertEqual(Contenido(html).tablas["Resultado"], esperado)
                procedimiento, _ = partes(html)
                self.assertIn(primero, procedimiento)
                self.assertIn(segundo, procedimiento)

    def test_producto_ambos_metodos_un_calculo_por_paso(self):
        matrices = [[[1, 2]], [[1, 0, 2], [0, 1, 3]], [[1, 2], [3, 4], [5, 6]], [[1], [2]]]
        for cantidad in (3, 4):
            for metodo in ("fila_columna", "columnas", "comparar"):
                datos = datos_coleccion("producto", matrices[:cantidad], metodo)
                with self.subTest(cantidad=cantidad, metodo=metodo), patch(
                        "backend.expresiones_matriciales.evaluador.resolver_operacion_matrices", wraps=resolver_operacion_matrices) as motor:
                    respuesta = self.client.post(MATRICES, datos)
                    self.assertEqual(motor.call_count, cantidad - 1)
                self.assertContains(respuesta, 'id="resultado"')
                texto = " ".join(strip_tags(respuesta.content.decode()).split())
                self.assertIn("AB = ", texto)
                self.assertIn("ABC", texto)
                if metodo in ("fila_columna", "comparar"):
                    self.assertIn("Fila por columna", texto)
                    self.assertIn("fila₁(AB) · columna₁(C)", texto)
                if metodo in ("columnas", "comparar"):
                    self.assertIn("Por columnas", texto)
                    self.assertIn("Columnas de AB:", texto)
                    self.assertIn("ABC = [ABc₁", texto)

    def test_cadena_no_repite_la_matriz_final_dentro_del_procedimiento(self):
        matrices = [[[1, 2]], [[1, 0, 2], [0, 1, 3]], [[1, 2], [3, 4], [5, 6]], [[1], [2]]]
        for cantidad in (3, 4):
            etiquetas = [nombre_matriz(i) for i in range(cantidad)]
            intermedios = ["".join(etiquetas[:i]) for i in range(2, cantidad)]
            anterior, ultima, final = intermedios[-1], etiquetas[-1], "".join(etiquetas)
            for metodo in ("fila_columna", "columnas", "comparar"):
                with self.subTest(cantidad=cantidad, metodo=metodo):
                    html = self.client.post(MATRICES, datos_coleccion("producto", matrices[:cantidad], metodo)).content.decode()
                    comprobar_estructura(self, html)
                    procedimiento, _ = partes(html)
                    bloque = elemento_html(html, html.index('id="procedimiento"'), "details")
                    # El último paso conserva su subexpresión, sus lecturas y sus operaciones…
                    self.assertIn(f"{final} · 1×", procedimiento)
                    if metodo != "columnas":
                        self.assertIn(f"({final})₁₁ = fila₁({anterior}) · columna₁({ultima})", procedimiento)
                    if metodo != "fila_columna":
                        self.assertIn(f"{final} = [{anterior}{ultima.lower()}₁", procedimiento)
                    # …y solo los intermedios cierran con su valor: el final vive en el panel.
                    for nombre in intermedios:
                        self.assertRegex(bloque, rf'(?s)<span class="matrix-expression">{nombre} =</span>\s*<div class="matrix">(?:(?!</table>).)*aria-label="{nombre}"')
                    self.assertNotIn(f'<table class="matrix-table" aria-label="{final}"', html)
                    self.assertNotIn("Resultado final", procedimiento)
                    self.assertEqual(html.count('<table class="matrix-table" aria-label="Resultado"'), 1)

    def test_matrices_dimensiones_y_campos_ajenos(self):
        incompatible = self.client.post(MATRICES, datos_coleccion("producto", [[[1, 2]], [[1, 2, 3], [4, 5, 6]], [[1], [2]]]))
        self.assertContains(incompatible, "No se puede calcular ABC: AB es 1×3 y C es 2×1.")
        base = datos_coleccion("suma", [[[1]], [[2]], [[3]]])
        for invalido in (base | {"cantidad": "1"}, base | {"celda_2_1_0": "0"}, base | {"columnas_3": "1"},
                         base | {"operacion": "suma"}, base | {"escalar": "2"}, base | {"cantidad": "2"}):
            with self.subTest(datos=invalido):
                self.assertFalse(ExpresionMatricialForm(invalido).is_valid())

    def test_exactos_decimales_en_cada_etapa(self):
        respuesta = self.client.post(MATRICES, datos_coleccion("producto", [[["1/3"]], [[1]], [[1]]]))
        html = respuesta.content.decode()
        self.assertIn("1/3", strip_tags(html))
        self.assertIn("0.3333", html)
        self.assertEqual(html.count('id="numeric-mode"'), 1)
        self.assertEqual(html.count('id="procedimiento"'), 1)

    def test_aplicar_conserva_simbolos_y_dimensiones(self):
        datos = datos_coleccion("producto", [[[1, 2]], [[1, 2, 3], [4, 5, 6]], [[1], [2], [3]]])
        respuesta = self.client.post(MATRICES, datos | {"ajustar": "1"})
        self.assertContains(respuesta, 'name="filas_2"')
        self.assertContains(respuesta, 'name="celda_2_2_0"')
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_web_cuarenta_operandos(self):
        respuesta = self.client.post(MATRICES, datos_coleccion("suma", [[[1]]] * 40))
        self.assertContains(respuesta, 'id="resultado"')
        self.assertEqual(Contenido(respuesta.content.decode()).tablas["Resultado"], [["40"]])
        # Después de Z los nombres siguen A1, B1…: no se confunden con un producto implícito.
        self.assertContains(respuesta, 'name="celda_39_0_0"')
        self.assertContains(respuesta, 'value="N1"')


class PruebasPresupuesto(SimpleTestCase):
    """Presupuesto común (P26.6): símbolos, celdas y campos antes de construir; apariciones al calcular."""

    def post(self, ruta, datos):
        # El cliente de pruebas relanza cualquier excepción de la vista: un 500 haría fallar la prueba.
        respuesta = self.client.post(ruta, datos)
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.content.decode()

    def test_mas_de_ocho_simbolos_y_mas_de_diez_operandos(self):
        # El tope histórico de Expresiones (8 símbolos) ya no limita: el presupuesto es el común.
        html = self.post(MATRICES, datos_coleccion("suma", [llena(3, 4)] * 12))
        self.assertEqual(Contenido(html).tablas["Resultado"], [["12"] * 4] * 3)
        html = self.post(MATRICES, datos_coleccion("producto", [llena(3, 3)] * 12, "fila_columna"))
        self.assertEqual(Contenido(html).tablas["Resultado"], [[str(3 ** 11)] * 3] * 3)
        self.assertIn("ABCDEFGHIJKL", strip_tags(html))
        vectores = {nombre: [1] * 4 for nombre in nombres_vectores("suma", 12)}
        self.assertIn("(12, 12, 12, 12)", strip_tags(self.post(VECTORES, datos_vectores("suma", vectores=12, **vectores))))

    def test_cantidad_absurda_se_descarta_antes_de_construir_la_estructura(self):
        for cantidad in ("100000", "51"):
            datos = datos_coleccion("suma", [[[1]], [[2]]]) | {"cantidad": cantidad}
            with self.subTest(cantidad=cantidad):
                form = ExpresionMatricialForm(datos)
                self.assertEqual(form.bloques, [])
                self.assertEqual(form.nombres_celdas, [])
                self.assertFalse(form.is_valid())
                self.assertEqual(form.errors["cantidad"], [f"La interfaz admite hasta {OPERANDOS_MAXIMOS} símbolos."])
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
                self.assertLess(len(datos) + 2, settings.DATA_UPLOAD_MAX_NUMBER_FIELDS)  # + csrfmiddlewaretoken y el botón
                html = self.post(MATRICES, datos)
                if operacion == "producto":
                    # P26.7: cabe estructuralmente, pero el costo requiere confirmar.
                    self.assertIn("data-confirmacion", html)
                    self.assertNotIn('id="resultado"', html)
                    form = ExpresionMatricialForm(datos)
                    self.assertTrue(form.is_valid(), form.errors)
                    html = self.post(MATRICES, datos | {"confirmacion": firmar_entrada(form.cleaned_data["entrada"])})
                self.assertEqual(Contenido(html).tablas["Resultado"], [[esperado] * 10] * 10)
        self.assertTrue(ExpresionMatricialForm(datos_coleccion("resta", [llena(5, 5)] * 22)).is_valid())  # 22 × 25 = 550

    def test_estructura_que_excede_el_presupuesto_se_rechaza_con_mensaje_legible(self):
        # Envíos manipulados que Django aún deja pasar (menos de 1000 campos): la interfaz nunca los dibuja.
        casos = (
            # Nueve 10×10 y una 1×1: 901 celdas.
            ([llena(10, 10)] * 9 + [[[1]]], "Los 10 símbolos suman 901 celdas y la interfaz admite hasta 900: quita símbolos o reduce sus dimensiones."),
            # 50 matrices con 791 celdas caben en celdas, pero no en campos: 200 de estructura + 791 = 991.
            ([llena(4, 4)] * 45 + [llena(2, 7)] * 4 + [llena(3, 5)],
             f"Los 50 símbolos ocupan 991 campos del formulario (nombre, tipo, dimensiones y celdas) y la interfaz admite hasta {CAMPOS_MAXIMOS}: quita símbolos o reduce sus dimensiones."),
        )
        for matrices, mensaje in casos:
            datos = datos_coleccion("suma", matrices)
            for extra in ({}, {"ajustar": "1"}):
                with self.subTest(cantidad=len(matrices), **extra):
                    form = ExpresionMatricialForm(datos | extra, accion="ajustar" if extra else None)
                    self.assertFalse(form.is_valid())
                    self.assertEqual(form.non_field_errors(), [mensaje])
                    # Se dibujan los mismos símbolos con las dimensiones iniciales, dentro del presupuesto.
                    self.assertEqual(len(form.bloques), len(matrices))
                    self.assertEqual(len(form.nombres_celdas), len(matrices) * 4)
                    html = self.post(MATRICES, datos | extra)
                    self.assertIn(mensaje, html)
                    self.assertNotIn('id="resultado"', html)
                    self.assertEqual(celdas_dibujadas(html), len(matrices) * 4)

    def test_simbolos_sin_celdas_tambien_cuentan(self):
        # Una matriz desconocida no dibuja celdas, pero sí nombre, tipo y dimensiones.
        desconocidas = [{"nombre": nombre, "tipo": "matriz_desconocida", "filas": 10, "columnas": 10} for nombre in nombres(OPERANDOS_MAXIMOS)]
        form = ExpresionMatricialForm(datos_simbolos("A", desconocidas, ajustar="1"), accion="ajustar")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.nombres_celdas, [])
        demasiadas = desconocidas + [{"nombre": "Z9", "tipo": "matriz_desconocida", "filas": 1, "columnas": 1}]
        form = ExpresionMatricialForm(datos_simbolos("A", demasiadas, ajustar="1"), accion="ajustar")
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["cantidad"], [f"La interfaz admite hasta {OPERANDOS_MAXIMOS} símbolos."])

    def test_agregar_respeta_el_tope_y_el_presupuesto(self):
        cincuenta = datos_coleccion("suma", [[[1]]] * OPERANDOS_MAXIMOS) | {"agregar": "1"}
        self.assertIn(f"No se puede agregar otro símbolo: la interfaz admite hasta {OPERANDOS_MAXIMOS}.", self.post(MATRICES, cincuenta))
        llenos = datos_coleccion("suma", [llena(10, 10)] * 9) | {"agregar": "1"}
        html = self.post(MATRICES, llenos)
        self.assertIn("No se puede agregar otro símbolo: una matriz 2×2 más no cabe.", html)
        self.assertEqual(celdas_dibujadas(html), 900)

    def test_repetir_un_simbolo_no_elude_los_topes(self):
        # Cada aparición cuenta como un operando del módulo anterior, con todas sus entradas.
        grande = [matriz("A", llena(10, 10))]
        datos = datos_simbolos("A" * 9, grande)
        self.assertIn("data-confirmacion", self.post(MATRICES, datos))
        form = ExpresionMatricialForm(datos)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn('id="resultado"', self.post(MATRICES, datos | {"confirmacion": firmar_entrada(form.cleaned_data["entrada"])}))
        html = self.post(MATRICES, datos_simbolos("A" * 10, grande))
        self.assertIn("Los operandos de la expresión suman 1000 entradas y la interfaz admite hasta 900", html)
        self.assertNotIn('id="resultado"', html)
        pequena = [matriz("A", [[1]])]
        self.assertIn('id="resultado"', self.post(MATRICES, datos_simbolos("+".join(["A"] * 50), pequena)))
        html = self.post(MATRICES, datos_simbolos("+".join(["A"] * 51), pequena))
        self.assertIn(f"La expresión tiene 51 operandos y la interfaz admite hasta {OPERANDOS_MAXIMOS}", html)
        # Los números también son operandos; en una igualdad cuentan ambos lados.
        html = self.post(MATRICES, datos_simbolos(" + ".join(["1"] * 26) + " = " + " + ".join(["1"] * 25), []))
        self.assertIn("La expresión tiene 51 operandos", html)

    def test_las_cadenas_de_traspuestas_y_signos_tambien_cuentan(self):
        # Sin más operandos, una cadena unaria repetiría el procedimiento: 49 operaciones, como 50 operandos.
        grande = [matriz("A", [[i * 10 + j for j in range(10)] for i in range(10)])]
        for expresion in ("A" + "ᵀ" * 49, "-" * 49 + "A", "A" + "^T" * 49):
            with self.subTest(expresion=expresion[:6]):
                self.assertIn('id="resultado"', self.post(MATRICES, datos_simbolos(expresion, grande)))
        for expresion in ("A" + "ᵀ" * 50, "-" * 50 + "A", "-(" * 49 + "Aᵀ" + ")" * 49):
            with self.subTest(expresion=expresion[:6]):
                html = self.post(MATRICES, datos_simbolos(expresion, grande))
                self.assertIn(f"La expresión tiene 50 operaciones y la interfaz admite hasta {OPERANDOS_MAXIMOS - 1}", html)
                self.assertNotIn('id="resultado"', html)

    def test_posts_manipulados_no_producen_errores_internos(self):
        for cantidad in ("100000", "1" + "0" * 40, "1e9", "-5"):
            for extra in ({}, {"ajustar": "1"}, {"agregar": "1"}):
                datos = {"cantidad": cantidad, "expresion": "A", "tipo_0": "matriz", "filas_0": "10", "columnas_0": "10",
                         "nombre_0": "A", "metodo": "comparar", "celda_99_0_0": "1"} | extra
                with self.subTest(ruta=MATRICES, cantidad=cantidad, **extra):
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

    def test_combinacion_con_mas_de_seis_generadores_hasta_el_tope(self):
        for cantidad in (7, OPERANDOS_MAXIMOS):
            with self.subTest(generadores=cantidad):
                html = self.post(VECTORES, combinacion([[1, 0]] * cantidad, [3, 0]))
                self.assertIn('id="resultado"', html)
                self.assertIn(f"x{cantidad}", strip_tags(html))
        form = VectoresForm(combinacion([[1, 0]] * (OPERANDOS_MAXIMOS + 1), [3, 0]))
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["vectores"], [f"La interfaz admite hasta {OPERANDOS_MAXIMOS} vectores por operación."])

    def test_lo_que_la_interfaz_dibuja_siempre_se_puede_enviar(self):
        # Peor envío de símbolos: 50 matrices con 790 celdas llenan los 990 campos de estructura y celdas.
        matrices = [llena(4, 4)] * 45 + [llena(2, 7)] * 5
        datos = datos_coleccion("suma", matrices)
        self.assertEqual(sum(len(m) * len(m[0]) for m in matrices) + 4 * OPERANDOS_MAXIMOS, CAMPOS_MAXIMOS)
        # + csrfmiddlewaretoken, metodo y el botón pulsado: dentro del límite de Django.
        self.assertLessEqual(len(datos) + 3, settings.DATA_UPLOAD_MAX_NUMBER_FIELDS)
        self.assertNotIn('class="alert error"', self.post(MATRICES, datos | {"ajustar": "1", "metodo": "comparar"}))
        # Y el mayor cálculo de 50 matrices que cabe: 50 de 3×5.
        html = self.post(MATRICES, datos_coleccion("suma", [llena(3, 5)] * OPERANDOS_MAXIMOS))
        self.assertEqual(Contenido(html).tablas["Resultado"], [["50"] * 5] * 3)
        # En vectores cierra por construcción: 50 generadores y b de dimensión máxima.
        self.assertLessEqual((OPERANDOS_MAXIMOS + 1) * DIMENSION_VECTORES, CELDAS_MAXIMAS)
        datos = combinacion([[1] * DIMENSION_VECTORES] * OPERANDOS_MAXIMOS, [1] * DIMENSION_VECTORES)
        self.assertLessEqual(len(datos) + 2, settings.DATA_UPLOAD_MAX_NUMBER_FIELDS)
        self.assertIn('id="resultado"', self.post(VECTORES, datos))
