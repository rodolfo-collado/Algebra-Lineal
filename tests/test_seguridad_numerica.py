"""P26.2.1: rechazo antes de convertir y crecimiento exacto acotado."""

import ast
import os
from fractions import Fraction
from pathlib import Path
from random import Random
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import SimpleTestCase

from backend.gauss import aplicar_gauss
from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import formatear_fraccion, producto_punto
from backend.operaciones_filas import eliminar_en_columna, normalizar_fila, registrar_paso
from backend.parser_sistemas import convertir_a_numero
from backend import presupuesto_sistemas
from backend.seguridad_numerica import (
    BITS_MAXIMOS, DIGITOS_MAXIMOS, MENSAJE_CALCULO_GRANDE,
    MENSAJE_NOTACION_CIENTIFICA, MENSAJE_NUMERO_GRANDE,
    dividir_exacto, multiplicar_exacto, restar_exacto, sumar_exacto,
    validar_literal_numerico, validar_valor_exacto,
)
from frontend.web.calculadora.presentacion_numerica import formatear_exacto, representar
from tests.test_ecuaciones_matriciales_web import datos_ecuacion
from tests.test_expresiones_lineales_web import datos as datos_lineales
from tests.test_expresiones_matriciales_web import datos_expresion
from tests.test_matrices_web import datos_matrices
from tests.test_multiplicacion_matrices_web import datos_matriz_vector, datos_producto
from tests.test_operandos_multiples import datos_coleccion
from tests.test_presupuesto_sistemas import datos_matriz
from tests.test_vectores_web import combinacion, datos_vectores


def entradas_web(literal):
    """Cada clase de dato editable; las estructuras son pequeñas y válidas."""
    sistemas = "/matrices/reduccion/"
    matrices = "/matrices/operaciones/"
    vectores = "/vectores/operaciones/"
    ecuaciones = "/matrices/ecuaciones/"
    expresiones = "/matrices/operaciones/"
    yield sistemas, {"metodo": "gauss", "sistema": f"x1={literal}"}
    yield sistemas, datos_matriz([[1, literal]])
    yield matrices, datos_matrices("suma", a=[[literal]], b=[[1]])
    yield matrices, datos_matrices("escalar", a=[[1]], escalar=literal)
    yield matrices, datos_producto(a=[[literal]], b=[[1]])
    yield matrices, datos_matriz_vector(a=[[1]], x=[literal])
    yield vectores, datos_vectores("suma", u=[literal], v=[1])
    yield vectores, datos_vectores("escalar", escalar=literal, u=[1])
    yield vectores, combinacion([[literal]], [1])
    yield vectores, combinacion([[1]], [literal])
    yield ecuaciones, datos_ecuacion(a=[[literal]], b=[1])
    yield ecuaciones, datos_ecuacion(a=[[1]], b=[literal])
    yield "/matrices/inversa/", {"orden": "1", "metodo": "gauss_jordan", "celda_A_0_0": literal}
    for nombre, tipo, valor in (("A", "matriz", [[literal]]), ("u", "vector", [literal]), ("k", "escalar", literal)):
        yield expresiones, datos_expresion(nombre, [{"nombre": nombre, "tipo": tipo, "valor": valor}])


def fraction_vigilada(valor=0, *args, **kwargs):
    if isinstance(valor, str):
        compacto = "".join(valor.split())
        if any(c in compacto for c in "eE") or any(len(parte) > DIGITOS_MAXIMOS for parte in compacto.lstrip("+-").replace("/", ".").split(".")):
            raise AssertionError("Un literal peligroso llegó a Fraction")
    return Fraction(valor, *args, **kwargs)


def matriz_de_crecimiento():
    # Entradas admitidas: 100 cifras por numerador y denominador, solo 42 celdas.
    aleatorio = Random(2621)
    return [[Fraction(aleatorio.randrange(10**99, 10**100), aleatorio.randrange(10**99, 10**100)) for _ in range(7)] for _ in range(6)]


class PruebasLiterales(unittest.TestCase):
    def test_exponentes_se_rechazan_antes_de_fraction(self):
        for literal in ("1e1000000000", "1e-1000000000", "-1E1000000000", "1 e -1000000000", "1e2"):
            with self.subTest(literal=literal), patch("backend.parser_sistemas.Fraction", side_effect=AssertionError("conversión")) as convertir:
                with self.assertRaisesRegex(ValueError, MENSAJE_NOTACION_CIENTIFICA):
                    convertir_a_numero(literal, limitar_entrada=True)
                convertir.assert_not_called()

    def test_componentes_largos_se_rechazan_antes_de_fraction(self):
        largo = "9" * (DIGITOS_MAXIMOS + 1)
        for literal in (largo, "-" + largo, largo + "/2", "1/" + largo, largo + ".5", "0." + largo, "1_" + "0" * DIGITOS_MAXIMOS):
            with self.subTest(literal=literal[:24]), patch("backend.parser_sistemas.Fraction", side_effect=AssertionError("conversión")):
                with self.assertRaisesRegex(ValueError, MENSAJE_NUMERO_GRANDE):
                    convertir_a_numero(literal, limitar_entrada=True)

    def test_normales_y_variantes_historicas(self):
        for literal, esperado in (("3", 3), ("-5", -5), ("+2", 2), ("-7/3", Fraction(-7, 3)), ("0.25", Fraction(1, 4)), (".5", Fraction(1, 2)), ("5.", 5), ("1_000", 1000), (" 1 / 2 ", Fraction(1, 2))):
            with self.subTest(literal=literal):
                self.assertEqual(convertir_a_numero(literal, limitar_entrada=True), esperado)

    def test_limites_de_sistemas_conservados_y_reexportados(self):
        self.assertEqual((presupuesto_sistemas.ECUACIONES_MAXIMAS, presupuesto_sistemas.VARIABLES_MAXIMAS, presupuesto_sistemas.CELDAS_MAXIMAS, presupuesto_sistemas.LONGITUD_SISTEMA_MAXIMA, presupuesto_sistemas.DIGITOS_MAXIMOS), (12, 12, 120, 10_000, 100))
        self.assertIs(presupuesto_sistemas.validar_literal_numerico, validar_literal_numerico)
        tope = "9" * 100
        for literal in (tope, tope + "/" + tope, tope + "." + tope, "0." + tope):
            with self.subTest(literal=literal[:12]):
                convertir_a_numero(literal, limitar_entrada=True)


class PruebasEntradasWeb(SimpleTestCase):
    def test_todas_las_celdas_y_escalares_rechazan_exponentes_y_literales_largos(self):
        for literal, mensaje in (("1e1000000000", MENSAJE_NOTACION_CIENTIFICA), ("1e-1000000000", MENSAJE_NOTACION_CIENTIFICA), ("9" * 101, MENSAJE_NUMERO_GRANDE), ("1/" + "9" * 101, MENSAJE_NUMERO_GRANDE), ("0." + "9" * 101, MENSAJE_NUMERO_GRANDE)):
            for indice, (ruta, datos) in enumerate(entradas_web(literal)):
                with self.subTest(ruta=ruta, indice=indice, literal=literal[:20]), patch("backend.parser_sistemas.Fraction", fraction_vigilada):
                    respuesta = self.client.post(ruta, datos)
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertContains(respuesta, mensaje)
                    self.assertNotContains(respuesta, 'id="resultado"')
                    self.assertNotContains(respuesta, "Traceback")

    def test_literales_normales_siguen_calculando_en_todas_las_herramientas(self):
        for literal in ("3", "-5", "1/2", "0.25"):
            for indice, (ruta, datos) in enumerate(entradas_web(literal)):
                with self.subTest(ruta=ruta, indice=indice, literal=literal):
                    respuesta = self.client.post(ruta, datos)
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertContains(respuesta, 'id="resultado"')

    def test_literal_inline_y_coeficiente_lineal_largo_no_llegan_a_fraction(self):
        largo = "9" * 101
        for datos in (
            datos_expresion(largo + " + 1", []),
            datos_lineales("b", [{"nombre": "b", "tipo": "vector_lineal", "valor": [largo + "x1"]}]),
        ):
            with self.subTest(datos=datos), patch("backend.parser_sistemas.Fraction", fraction_vigilada):
                respuesta = self.client.post("/matrices/operaciones/", datos)
                self.assertContains(respuesta, MENSAJE_NUMERO_GRANDE)
                self.assertNotContains(respuesta, 'id="resultado"')

    def test_expresiones_no_interpretan_cientifica_y_conservan_nombres_con_e(self):
        for texto in ("1e1000000000", "1e-1000000000"):
            with self.subTest(texto=texto), patch("backend.parser_sistemas.Fraction", fraction_vigilada):
                respuesta = self.client.post("/matrices/operaciones/", datos_expresion(texto, []))
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, "no está definido")
                self.assertNotContains(respuesta, 'id="resultado"')
        # La yuxtaposición 1·e2 es sintaxis existente, no un exponente.
        respuesta = self.client.post("/matrices/operaciones/", datos_expresion("1e2", [{"nombre": "e2", "tipo": "escalar", "valor": 7}]))
        self.assertContains(respuesta, 'id="resultado"')

    def test_crecimiento_de_entradas_admitidas_da_error_en_sistemas_ax_y_combinacion(self):
        matriz = matriz_de_crecimiento()
        a, b = [fila[:-1] for fila in matriz], [fila[-1] for fila in matriz]
        for metodo in ("gauss", "gauss_jordan", "comparar"):
            casos = [("/matrices/reduccion/", datos_matriz(matriz, metodo=metodo)), ("/matrices/ecuaciones/", datos_ecuacion(a, b, metodo=metodo))]
            for ruta, datos in casos:
                with self.subTest(ruta=ruta, metodo=metodo):
                    self.assert_error_controlado(self.client.post(ruta, datos))
        self.assert_error_controlado(self.client.post("/vectores/operaciones/", combinacion(list(map(list, zip(*a))), b)))
        # [A | I] crece igual: la inversa de A (6×6) también se detiene con el mensaje controlado.
        from tests.test_matriz_inversa_web import datos_inversa
        self.assert_error_controlado(self.client.post("/matrices/inversa/", datos_inversa(a)))

    def assert_error_controlado(self, respuesta):
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, MENSAJE_CALCULO_GRANDE)
        for fragmento in ('id="resultado"', "Traceback", "Exceeds the limit", "bits"):
            self.assertNotContains(respuesta, fragmento)

    def test_producto_escalar_encadenado_se_detiene_antes_de_presentar(self):
        # 37 factores de 100 cifras caben en una expresión de 73 caracteres.
        datos = datos_expresion("*".join(["k"] * 37), [{"nombre": "k", "tipo": "escalar", "valor": "9" * 100}])
        self.assert_error_controlado(self.client.post("/matrices/operaciones/", datos))

    def test_cadena_de_matrices_admitidas_se_detiene_antes_de_presentar(self):
        # 37 matrices de una celda caben en los presupuestos de operandos y celdas.
        datos = datos_coleccion("producto", [[["9" * 100]]] * 37)
        self.assert_error_controlado(self.client.post("/matrices/operaciones/", datos))


class PruebasIntermedios(unittest.TestCase):
    def test_numerador_denominador_y_frontera_sin_texto(self):
        tope = 1 << (BITS_MAXIMOS - 1)
        self.assertEqual(validar_valor_exacto(tope), tope)
        self.assertEqual(validar_valor_exacto(Fraction(1, tope)), Fraction(1, tope))
        for valor in (1 << BITS_MAXIMOS, -(1 << BITS_MAXIMOS), Fraction(1, 1 << BITS_MAXIMOS)):
            with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                validar_valor_exacto(valor)

    def test_operacion_valida_con_cancelacion_conserva_exactitud(self):
        grande = 1 << (BITS_MAXIMOS - 1)
        self.assertEqual(multiplicar_exacto(Fraction(grande, 3), Fraction(3, grande)), 1)
        self.assertEqual(dividir_exacto(grande, grande), 1)
        self.assertEqual(restar_exacto(grande, grande), 0)
        self.assertEqual(sumar_exacto(Fraction(1, 3), Fraction(1, 6)), Fraction(1, 2))

    def test_operandos_extremos_se_rechazan_antes_de_operar(self):
        class EnteroVigilado(int):
            @property
            def numerator(self):
                return self

            def __mul__(self, otro):
                raise AssertionError("No se debe multiplicar el operando extremo")

        with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
            multiplicar_exacto(EnteroVigilado(1 << BITS_MAXIMOS), 2)

    def test_gauss_y_gauss_jordan_detienen_crecimiento_de_fracciones_admitidas(self):
        matriz = matriz_de_crecimiento()
        copia = [fila[:] for fila in matriz]
        for motor in (aplicar_gauss, aplicar_gauss_jordan):
            with self.subTest(motor=motor.__name__), self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                motor(matriz, 6)
        self.assertEqual(matriz, copia)

    def test_producto_extremo_no_llega_a_resta_ni_a_registro_de_paso(self):
        x = Fraction(1 << (BITS_MAXIMOS // 2 + 1))
        matriz = [[Fraction(1), x], [x, Fraction(0)]]
        pasos = []
        # La primera celda se calcula normalmente; la segunda falla en x*x.
        with patch("backend.operaciones_filas.restar_exacto", wraps=restar_exacto) as restar, patch("backend.operaciones_filas.registrar_paso", side_effect=AssertionError("registro")):
            with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                eliminar_en_columna(matriz, pasos, 0, 0, [1])
        self.assertEqual(restar.call_count, 1)
        self.assertEqual(matriz, [[1, x], [x, 0]])
        self.assertEqual(pasos, [])

    def test_normalizacion_extrema_no_muta_fila_ni_guarda_pasos(self):
        x = Fraction(1 << (BITS_MAXIMOS // 2 + 1))
        matriz, pasos = [[1 / x, x]], []
        with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
            normalizar_fila(matriz, pasos, 0, 1 / x)
        self.assertEqual(matriz, [[1 / x, x]])
        self.assertEqual(pasos, [])

    def test_gauss_jordan_comprueba_tambien_eliminacion_hacia_arriba(self):
        x = Fraction(1 << (BITS_MAXIMOS // 2 + 1))
        matriz = [[Fraction(1), x, Fraction(0)], [Fraction(0), Fraction(1), x]]
        self.assertEqual(aplicar_gauss(matriz, 2)[0], matriz)
        with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
            aplicar_gauss_jordan(matriz, 2)

    def test_entrada_extrema_no_se_copia_en_historial(self):
        matriz = [[1 << BITS_MAXIMOS]]
        with patch("backend.operaciones_filas.copiar_matriz", side_effect=AssertionError("copia")):
            with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                registrar_paso([], matriz, "F1 = F1", matriz)
        for motor in (aplicar_gauss, aplicar_gauss_jordan):
            with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                motor(matriz)

    def test_gauss_y_gauss_jordan_normales_tienen_los_mismos_resultados_exactos(self):
        matriz = [[Fraction(2, 3), Fraction(2, 3), Fraction(10, 3)], [Fraction(1, 2), Fraction(-1, 2), Fraction(1, 2)]]
        escalonada, _, pivotes = aplicar_gauss(matriz, 2)
        reducida, _, pivotes_jordan = aplicar_gauss_jordan(matriz, 2)
        self.assertEqual(escalonada, [[1, 1, 5], [0, 1, 2]])
        self.assertEqual(reducida, [[1, 0, 3], [0, 1, 2]])
        self.assertEqual(pivotes, [(0, 0), (1, 1)])
        self.assertEqual(pivotes_jordan, pivotes)
        self.assertTrue(all(isinstance(n, Fraction) for fila in escalonada + reducida for n in fila))

    def test_producto_punto_revisa_cada_acumulacion(self):
        x = 1 << (BITS_MAXIMOS - 1)
        with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
            producto_punto([x, x, -x], [1, 1, 1])

    def test_presentacion_usa_el_mismo_error_para_enteros_y_fracciones(self):
        for valor in (1 << BITS_MAXIMOS, Fraction(1, 1 << BITS_MAXIMOS)):
            for presentar in (formatear_fraccion, formatear_exacto, representar):
                with self.subTest(presentar=presentar.__name__), self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                    presentar(valor)

    def test_respeta_limite_python_mas_restrictivo_sin_modificarlo(self):
        limite = sys.get_int_max_str_digits()
        with patch("backend.seguridad_numerica.sys.get_int_max_str_digits", return_value=640):
            with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                validar_valor_exacto(1 << 1920)
        self.assertEqual(sys.get_int_max_str_digits(), limite)

    def test_no_se_desactiva_el_limite_global(self):
        limite = sys.get_int_max_str_digits()
        with patch.object(sys, "set_int_max_str_digits", side_effect=AssertionError("No cambiar el límite global")):
            aplicar_gauss([[2, 1], [1, 3]])
            aplicar_gauss_jordan([[2, 1], [1, 3]])
        self.assertEqual(sys.get_int_max_str_digits(), limite)
        raiz = Path(__file__).resolve().parents[1]
        for carpeta in ("backend", "frontend"):
            for archivo in (raiz / carpeta).rglob("*.py"):
                arbol = ast.parse(archivo.read_text(encoding="utf-8"))
                self.assertFalse(any(isinstance(nodo, ast.Attribute) and nodo.attr == "set_int_max_str_digits" for nodo in ast.walk(arbol)), str(archivo))


if __name__ == "__main__":
    unittest.main()
