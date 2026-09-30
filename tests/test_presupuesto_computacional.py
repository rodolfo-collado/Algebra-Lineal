"""Presupuesto computacional (P26.2): estimar sin ejecutar y separar cálculo de procedimiento.

Ninguna prueba mide segundos: las referencias de tiempo solo se comparan entre sí.
"""

import os
import random
import re
from contextlib import ExitStack
from fractions import Fraction
from unittest import TestCase
from unittest.mock import Mock, patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.conf import settings
from django.test import SimpleTestCase

from backend import presupuesto_computacional as presupuesto
from backend.gauss import aplicar_gauss
from backend.gauss_jordan import aplicar_gauss_jordan
from backend.operandos import CELDAS_MAXIMAS as CELDAS_OPERANDOS, OPERANDOS_MAXIMOS
from backend.presupuesto_computacional import (
    Categoria,
    PerfilNumerico,
    categoria,
    combinar_estimaciones,
    estimar_gauss,
    estimar_gauss_jordan,
    estimar_producto,
    intervalo_segundos,
    perfil_numerico,
    segundos_referencia,
)
from backend.presupuesto_sistemas import (
    CELDAS_MAXIMAS as CELDAS_SISTEMAS,
    DIGITOS_MAXIMOS,
    ECUACIONES_MAXIMAS,
    LONGITUD_SISTEMA_MAXIMA,
    MENSAJE_NOTACION_CIENTIFICA,
    VARIABLES_MAXIMAS,
    validar_dimensiones,
)
from frontend.web.calculadora.opciones_matrices import DIMENSION_MAXIMA as DIMENSION_MATRICES
from frontend.web.calculadora.opciones_vectores import DIMENSION_MAXIMA as DIMENSION_VECTORES
from frontend.web.calculadora.servicios import estimar_entrada_web
from frontend.web.calculadora.servicios_ecuaciones import estimar_ecuacion_web
from tests.test_ecuaciones_matriciales_web import RUTA as RUTA_ECUACIONES, datos_ecuacion


def costos(estimacion):
    return estimacion.pasos, estimacion.calculo, estimacion.procedimiento


def fracciones(filas, columnas, cifras):
    """Siempre las mismas fracciones, con numerador y denominador de `cifras` cifras."""
    rng = random.Random(26)
    minimo, maximo = 10 ** (cifras - 1), 10**cifras
    return [[Fraction(rng.randrange(minimo, maximo), rng.randrange(minimo, maximo)) for _ in range(columnas)] for _ in range(filas)]


def comparar_ambos(filas, variables):
    """«Comparar ambos» de Resolver un sistema: Gauss y Gauss-Jordan sobre [A | b]."""
    return combinar_estimaciones(*(
        estimar(filas, variables + 1, columnas_pivote=variables) for estimar in (estimar_gauss, estimar_gauss_jordan)
    ))


class PruebasEstimaciones(TestCase):
    def test_una_operacion_pequena_estima_menos_que_una_equivalente_mayor(self):
        for pequena, mayor in (
            (estimar_gauss(2, 3), estimar_gauss(10, 11)),
            (estimar_gauss_jordan(2, 3), estimar_gauss_jordan(10, 11)),
            (estimar_producto(2, 2, 2), estimar_producto(10, 10, 10)),
        ):
            with self.subTest(operacion=pequena.operacion):
                for menor, mayor_costo in zip(costos(pequena), costos(mayor)):
                    self.assertLess(menor, mayor_costo)
                self.assertLess(segundos_referencia(pequena), segundos_referencia(mayor))

    def test_gauss_jordan_crece_con_las_dimensiones(self):
        anterior = estimar_gauss_jordan(1, 2, columnas_pivote=1)
        for n in range(2, 16):
            actual = estimar_gauss_jordan(n, n + 1, columnas_pivote=n)
            for previo, siguiente in zip(costos(anterior), costos(actual)):
                self.assertGreater(siguiente, previo)
            anterior = actual
        # También en rectangulares: una fila o una columna más cuestan más.
        base = estimar_gauss_jordan(4, 6)
        for mayor in (estimar_gauss_jordan(5, 6), estimar_gauss_jordan(4, 7)):
            with self.subTest(dimensiones=mayor.dimensiones):
                self.assertGreater(mayor.calculo, base.calculo)
                self.assertGreater(mayor.procedimiento, base.procedimiento)
        # Gauss-Jordan es el escalonamiento de Gauss más la eliminación hacia arriba.
        self.assertGreater(estimar_gauss_jordan(6, 7).calculo, estimar_gauss(6, 7).calculo)
        self.assertEqual(estimar_gauss_jordan(1, 5).pasos, estimar_gauss(1, 5).pasos)

    def test_multiplicar_matrices_mas_grandes_cuesta_mas(self):
        base = estimar_producto(3, 4, 5)
        for mayor in (estimar_producto(4, 4, 5), estimar_producto(3, 5, 5), estimar_producto(3, 4, 6)):
            with self.subTest(dimensiones=mayor.dimensiones):
                self.assertGreater(mayor.calculo, base.calculo)
                self.assertGreater(mayor.procedimiento, base.procedimiento)
        # Un paso por entrada; un producto y una suma por término de cada entrada.
        self.assertEqual((base.dimensiones, base.pasos, base.calculo), ((3, 4, 5), 3 * 5, 2 * 3 * 4 * 5))

    def test_racionales_mas_complejos_aumentan_el_factor(self):
        sencillos, racionales = fracciones(10, 11, 1), fracciones(10, 11, 10)
        sin_perfil = estimar_gauss_jordan(10, 11, columnas_pivote=10)
        pequenos = estimar_gauss_jordan(10, 11, columnas_pivote=10, perfil=perfil_numerico(sencillos))
        complejos = estimar_gauss_jordan(10, 11, columnas_pivote=10, perfil=perfil_numerico(racionales))
        self.assertEqual(sin_perfil.factor_numerico, 1)
        self.assertLess(pequenos.factor_numerico, complejos.factor_numerico)
        # Mismos pasos: el tamaño de los números encarece cada operación y cada valor mostrado.
        self.assertEqual(pequenos.pasos, complejos.pasos)
        self.assertLess(pequenos.calculo, complejos.calculo)
        self.assertLess(pequenos.procedimiento, complejos.procedimiento)
        # La aritmética crece más que el texto que se muestra, como en el POST completo.
        self.assertGreater(complejos.calculo / pequenos.calculo, complejos.procedimiento / pequenos.procedimiento)
        # Con los mismos bits, el denominador pesa más: se acumula al combinar filas.
        self.assertLess(
            estimar_gauss_jordan(8, 9, perfil=PerfilNumerico(bits_numerador=64)).factor_numerico,
            estimar_gauss_jordan(8, 9, perfil=PerfilNumerico(bits_denominador=64)).factor_numerico,
        )
        # El mismo perfil pesa más cuanto más profunda es la eliminación.
        perfil = perfil_numerico(racionales)
        self.assertLess(
            estimar_gauss_jordan(4, 5, perfil=perfil).factor_numerico,
            estimar_gauss_jordan(12, 13, perfil=perfil).factor_numerico,
        )
        self.assertLess(
            estimar_producto(5, 5, 5, perfil=perfil_numerico(sencillos)).factor_numerico,
            estimar_producto(5, 5, 5, perfil=perfil).factor_numerico,
        )

    def test_el_perfil_mide_bits_sin_convertir_a_texto(self):
        self.assertEqual(perfil_numerico([[0, 1, -8]], [[Fraction(1, 2), Fraction(-3, 1024)]]), PerfilNumerico(4, 10))
        self.assertEqual(perfil_numerico([[7, -7]]), PerfilNumerico(3, 0))
        # Casi un millón de cifras: pasarlo a texto fallaría (Python admite hasta 4300).
        enorme = 1 << 3_000_000
        self.assertEqual(perfil_numerico([[enorme, Fraction(1, enorme + 1)]]), PerfilNumerico(3_000_001, 3_000_000))

    def test_combinar_suma_los_costos_y_conserva_las_partes(self):
        # Como resolver con la inversa más adelante: [A | I], A⁻¹b y la verificación A⁻¹A.
        inversa = estimar_gauss_jordan(4, 8, columnas_pivote=4)
        solucion = estimar_producto(4, 4, 1)
        verificacion = estimar_producto(4, 4, 4)
        total = combinar_estimaciones(inversa, solucion, verificacion, operacion="sistema_por_inversa")
        self.assertEqual((total.operacion, total.partes), ("sistema_por_inversa", (inversa, solucion, verificacion)))
        self.assertEqual(total.pasos, inversa.pasos + solucion.pasos + verificacion.pasos)
        self.assertAlmostEqual(total.calculo, inversa.calculo + solucion.calculo + verificacion.calculo)
        self.assertAlmostEqual(
            total.procedimiento, inversa.procedimiento + solucion.procedimiento + verificacion.procedimiento
        )
        self.assertAlmostEqual(segundos_referencia(total), sum(map(segundos_referencia, total.partes)))
        self.assertGreaterEqual(categoria(total), max(map(categoria, total.partes)))
        # Agrupar de otra manera no cambia el total.
        agrupado = combinar_estimaciones(inversa, combinar_estimaciones(solucion, verificacion))
        for esperado, obtenido in zip(costos(total), costos(agrupado)):
            self.assertAlmostEqual(esperado, obtenido)
        # Una parte con números grandes encarece el conjunto y marca su factor.
        grande = estimar_producto(4, 4, 1, perfil=PerfilNumerico(400, 400))
        con_grandes = combinar_estimaciones(inversa, grande, verificacion)
        self.assertEqual(con_grandes.factor_numerico, grande.factor_numerico)
        self.assertGreater(con_grandes.calculo, total.calculo)
        with self.assertRaises(ValueError):
            combinar_estimaciones()

    def test_calculo_y_procedimiento_se_estiman_por_separado(self):
        pequena = estimar_gauss_jordan(3, 4, columnas_pivote=3)
        grande = estimar_gauss_jordan(12, 13, columnas_pivote=12)
        # Cada paso guarda dos matrices: el procedimiento crece más rápido que el cálculo.
        self.assertGreater(grande.procedimiento / grande.calculo, pequena.procedimiento / pequena.calculo)
        # Que el motor termine rápido no hace barato mostrar el procedimiento.
        calculo = grande.calculo * presupuesto.REFERENCIA_SEGUNDOS_OPERACION
        procedimiento = grande.procedimiento * presupuesto.REFERENCIA_SEGUNDOS_CELDA
        self.assertGreater(procedimiento, 10 * calculo)
        self.assertAlmostEqual(segundos_referencia(grande), calculo + procedimiento)
        # El producto también separa el resultado de la evidencia de sus dos lecturas.
        producto = estimar_producto(10, 10, 10)
        self.assertGreater(producto.procedimiento, producto.calculo)

    def test_estimar_no_ejecuta_los_motores(self):
        motores = (
            "backend.gauss.aplicar_gauss",
            "backend.gauss_jordan.aplicar_gauss_jordan",
            "backend.operaciones_filas.registrar_paso",
            "backend.matrices.multiplicar_matrices",
            "backend.matrices.resolver_operacion_matrices",
        )
        n = 10**9
        with ExitStack() as pila:
            vigilados = [pila.enter_context(patch(ruta, side_effect=AssertionError(ruta))) for ruta in motores]
            # Dimensiones que nadie podría construir: estimar solo hace cuentas con ellas.
            gauss = estimar_gauss(n, n + 1, columnas_pivote=n)
            jordan = estimar_gauss_jordan(n, n + 1, columnas_pivote=n)
            producto = estimar_producto(n, n, n)
        for vigilado in vigilados:
            vigilado.assert_not_called()
        self.assertEqual((gauss.pasos, jordan.pasos, producto.pasos), (n * n - n * (n - 1) // 2, n * n, n * n))

    def test_los_pasos_estimados_acotan_los_del_motor(self):
        rng = random.Random(26)
        matrices = [[[1, 0], [0, 1]], [[0, 0, 0]], [[0], [0], [5]], [[0, 2, 1], [3, 1, 2], [1, 1, 5]]]
        for _ in range(80):
            filas, columnas = rng.randint(1, 6), rng.randint(1, 6)
            matrices.append([[rng.choice((0, 1, -1, 2, -3, 5)) for _ in range(columnas)] for _ in range(filas)])
        for matriz in matrices:
            filas, columnas = len(matriz), len(matriz[0])
            for columnas_pivote in sorted({1, columnas}):
                for motor, estimar in ((aplicar_gauss, estimar_gauss), (aplicar_gauss_jordan, estimar_gauss_jordan)):
                    with self.subTest(matriz=matriz, columnas_pivote=columnas_pivote, motor=motor.__name__):
                        _, pasos, _ = motor(matriz, columnas_pivote)
                        self.assertLessEqual(len(pasos), estimar(filas, columnas, columnas_pivote=columnas_pivote).pasos)
        # La cota se alcanza aun con un intercambio: la fila que baja ya trae su cero.
        _, pasos, _ = aplicar_gauss_jordan([[0, 2, 1], [3, 1, 2], [1, 1, 5]])
        self.assertEqual(len(pasos), estimar_gauss_jordan(3, 3).pasos)

    def test_dimensiones_invalidas(self):
        for dimensiones in ((0, 2), (2, -1), (2.0, 2), (True, 2), (None, 2)):
            with self.subTest(dimensiones=dimensiones), self.assertRaises(ValueError):
                estimar_gauss_jordan(*dimensiones)
        with self.assertRaises(ValueError):
            estimar_producto(2, 0, 2)
        with self.assertRaises(ValueError):
            estimar_gauss(2, 3, columnas_pivote=4)


class PruebasReferencias(TestCase):
    def test_las_categorias_crecen_con_el_tamano(self):
        self.assertEqual(list(Categoria), sorted(Categoria))
        self.assertEqual(categoria(estimar_gauss_jordan(2, 3, columnas_pivote=2)), Categoria.NORMAL)
        anterior = Categoria.NORMAL
        for n in range(1, 60):
            actual = categoria(estimar_gauss_jordan(n, n + 1, columnas_pivote=n))
            self.assertGreaterEqual(actual, anterior)
            anterior = actual
        self.assertEqual(anterior, Categoria.MUY_PESADA)

    def test_el_tiempo_es_un_intervalo_calibrable_no_un_numero(self):
        estimacion = estimar_gauss_jordan(10, 11, columnas_pivote=10)
        bajo, alto = intervalo_segundos(estimacion)
        referencia = segundos_referencia(estimacion)
        self.assertLess(bajo, referencia)
        self.assertLess(referencia, alto)
        self.assertAlmostEqual(alto / bajo, presupuesto.REFERENCIA_MARGEN**2)
        # Recalibrar cambia el tiempo de referencia, no las cantidades estimadas.
        with patch.object(presupuesto, "REFERENCIA_SEGUNDOS_CELDA", 2 * presupuesto.REFERENCIA_SEGUNDOS_CELDA):
            self.assertGreater(segundos_referencia(estimacion), referencia)
            self.assertEqual(estimar_gauss_jordan(10, 11, columnas_pivote=10), estimacion)

    def test_las_referencias_ordenan_las_mediciones_historicas(self):
        """POST completo de «Comparar ambos» en docs/presupuesto-sistemas.md; solo cuenta el orden."""
        medidas = {(6, 6): 0.49, (8, 8): 1.05, (9, 12): 1.95, (12, 9): 2.85, (12, 12): 4.52}
        self.assertEqual(
            sorted(medidas, key=lambda dimensiones: segundos_referencia(comparar_ambos(*dimensiones))),
            sorted(medidas, key=medidas.get),
        )


class PruebasLimites(TestCase):
    def test_los_limites_estructurales_no_cambian_ni_dependen_del_costo(self):
        # P26.2 separa costo y límites; no aumenta ninguno.
        self.assertEqual((ECUACIONES_MAXIMAS, VARIABLES_MAXIMAS, CELDAS_SISTEMAS), (12, 12, 120))
        self.assertEqual((LONGITUD_SISTEMA_MAXIMA, DIGITOS_MAXIMOS), (10_000, 100))
        self.assertEqual((OPERANDOS_MAXIMOS, CELDAS_OPERANDOS), (50, 900))
        self.assertEqual((DIMENSION_MATRICES, DIMENSION_VECTORES), (10, 10))
        self.assertEqual(settings.DATA_UPLOAD_MAX_NUMBER_FIELDS, 1000)
        # Un costo muy alto no es un error de entrada: estimar no valida nada...
        self.assertEqual(categoria(estimar_gauss_jordan(100, 101, columnas_pivote=100)), Categoria.MUY_PESADA)
        # ...y los límites aceptan y rechazan exactamente lo mismo que antes.
        validar_dimensiones(12, 9)
        with self.assertRaisesRegex(ValueError, f"hasta {CELDAS_SISTEMAS} celdas"):
            validar_dimensiones(11, 10)


class PruebasIntegracionServicios(SimpleTestCase):
    def test_sistemas_estima_la_entrada_sin_resolverla(self):
        motor = Mock(side_effect=AssertionError("motor"))
        resolvers = {"gauss": ("Gauss", motor, "", ""), "gauss_jordan": ("Gauss-Jordan", motor, "", "")}
        matriz = [[1, 1, 3], [1, -1, 1]]
        with patch.dict("frontend.web.calculadora.servicios._RESOLVERS", resolvers):
            texto = estimar_entrada_web("sistema", "gauss_jordan", texto="x1 + x2 = 3; x1 - x2 = 1")
            ambos = estimar_entrada_web("matriz", "comparar", matriz_aumentada=matriz)
        motor.assert_not_called()
        # Los pivotes solo se buscan en los coeficientes, como en los motores.
        perfil = perfil_numerico(matriz)
        jordan = estimar_gauss_jordan(2, 3, columnas_pivote=2, perfil=perfil)
        self.assertEqual((texto.operacion, texto.partes), ("gauss_jordan", (jordan,)))
        self.assertEqual((ambos.operacion, ambos.partes), ("comparar", (estimar_gauss(2, 3, columnas_pivote=2, perfil=perfil), jordan)))

    def test_la_estimacion_respeta_el_presupuesto_de_entrada(self):
        # Las mismas protecciones y mensajes que al resolver, antes de cualquier cuenta.
        with self.assertRaisesRegex(ValueError, f"hasta {CELDAS_SISTEMAS} celdas"):
            estimar_entrada_web("matriz", "gauss", matriz_aumentada=[[1] * 11 for _ in range(11)])
        with self.assertRaisesRegex(ValueError, re.escape(MENSAJE_NOTACION_CIENTIFICA)):
            estimar_entrada_web("sistema", "gauss", texto="x1 = 1e5")
        with self.assertRaisesRegex(ValueError, "método"):
            estimar_entrada_web("matriz", "cramer", matriz_aumentada=[[1, 2]])

    def test_ax_b_suma_la_reduccion_y_la_comprobacion_de_cada_metodo(self):
        entrada = {"a": [[2, 1], [1, 3], [0, 1]], "b": [1, 2, Fraction(1, 2)], "metodo": "comparar"}
        with patch(
            "frontend.web.calculadora.servicios_ecuaciones.resolver_ecuacion_matricial",
            side_effect=AssertionError("motor"),
        ) as resolver:
            estimacion = estimar_ecuacion_web(entrada)
        resolver.assert_not_called()
        perfil = perfil_numerico(entrada["a"], [entrada["b"]])
        self.assertEqual(perfil.bits_denominador, 1)
        comprobacion = estimar_producto(3, 2, 1, perfil=perfil)
        self.assertEqual(estimacion.operacion, "comparar")
        self.assertEqual(estimacion.partes, (
            estimar_gauss(3, 3, columnas_pivote=2, perfil=perfil), comprobacion,
            estimar_gauss_jordan(3, 3, columnas_pivote=2, perfil=perfil), comprobacion,
        ))
        self.assertLess(estimar_ecuacion_web({**entrada, "metodo": "gauss_jordan"}).calculo, estimacion.calculo)

    @patch.object(presupuesto, "REFERENCIA_UMBRALES", (0, 0, 0))
    def test_un_costo_alto_no_impide_resolver(self):
        """P26.2 solo consulta la estimación: nada rechaza una entrada válida por su costo."""
        sistema = "x1 + x2 = 3; x1 - x2 = 1"
        self.assertEqual(categoria(estimar_entrada_web("sistema", "comparar", texto=sistema)), Categoria.MUY_PESADA)
        respuesta = self.client.post("/sistemas/", {"sistema": sistema, "metodo": "comparar"})
        self.assertContains(respuesta, 'id="resultado"')
        self.assertContains(respuesta, "x1 = 2")

        entrada = {"a": [[1, 1], [1, -1]], "b": [5, 1], "metodo": "comparar"}
        self.assertEqual(categoria(estimar_ecuacion_web(entrada)), Categoria.MUY_PESADA)
        respuesta = self.client.post(RUTA_ECUACIONES, datos_ecuacion(a=entrada["a"], b=entrada["b"], metodo="comparar"))
        self.assertContains(respuesta, 'id="resultado"')
