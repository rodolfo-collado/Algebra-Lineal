import unittest
from fractions import Fraction
from math import inf, nan

from backend.sistemas_iterativos import ITERACIONES_MAXIMAS, resolver_iterativo


CLASE_A = [[10, -1, 2, 0], [-1, 11, -1, 3], [2, -1, 10, -1], [0, 3, -1, 8]]
CLASE_B = [6, 25, -11, 15]
PRACTICA_A = [[8, -1, 1, 0], [-1, 10, -2, 1], [1, -2, 9, -1], [0, 1, -1, 7]]
PRACTICA_B = [8, 7, -4, 5]


class SistemasIterativosTest(unittest.TestCase):
    def assertVector(self, real, esperado):
        self.assertEqual(len(real), len(esperado))
        for valor, referencia in zip(real, esperado):
            self.assertAlmostEqual(valor, float(referencia), places=13)

    def test_jacobi_corrige_las_cuentas_de_la_diapositiva_15(self):
        resultado = resolver_iterativo(CLASE_A, CLASE_B, "jacobi")
        self.assertVector(resultado.iteraciones[1].x, (0.6, Fraction(25, 11), -1.1, 1.875))
        # La diapositiva imprime 1.704545 y 0.906818; las sustituciones dan
        # 151/88 y 779/880, como en la tabla de la diapositiva 16 y del Word.
        self.assertVector(resultado.iteraciones[2].x, (
            Fraction(288, 275), Fraction(151, 88), Fraction(-3543, 4400), Fraction(779, 880),
        ))

    def test_gauss_seidel_corrige_diapositivas_20_21_y_sustituciones_del_word(self):
        resultado = resolver_iterativo(CLASE_A, CLASE_B, "gauss_seidel")
        # Diapositiva 20: 0.751591 es un error aritmético que se arrastra a la 21.
        self.assertAlmostEqual(resultado.iteraciones[1].x[3], 3867 / 4400, places=13)
        # Word §5: al calcular x2 aún se leen x3 y x4 de k=1.
        # Al calcular x3, x4 también viene de k=1. La tabla del Word es correcta.
        self.assertVector(resultado.iteraciones[2].x, (
            Fraction(2833, 2750), Fraction(492939, 242000),
            Fraction(-306873, 302500), Fraction(9528423, 9680000),
        ))

    def test_primeras_tres_iteraciones_de_la_diapositiva_28(self):
        casos = {
            "jacobi": (
                (1, Fraction(7, 10), Fraction(-4, 9), Fraction(5, 7)),
                (Fraction(823, 720), Fraction(403, 630), Fraction(-101, 315), Fraction(347, 630)),
                (Fraction(1129, 1008), Fraction(35033, 50400), Fraction(-16697, 45360), Fraction(509, 882)),
            ),
            "gauss_seidel": (
                (1, Fraction(4, 5), Fraction(-17, 45), Fraction(172, 315)),
                (Fraction(413, 360), Fraction(17251, 25200), Fraction(-10181, 28350), Fraction(897293, 1587600)),
                (Fraction(2051107, 1814400), Fraction(86962829, 127008000),
                 Fraction(-50737549, 142884000), Fraction(4526794147, 8001504000)),
            ),
        }
        for metodo, esperado in casos.items():
            with self.subTest(metodo=metodo):
                resultado = resolver_iterativo(PRACTICA_A, PRACTICA_B, metodo, max_iteraciones=3)
                self.assertEqual(resultado.estado, "limite")
                for fila, vector in zip(resultado.iteraciones[1:], esperado, strict=True):
                    self.assertVector(fila.x, vector)

    def test_parada_por_los_dos_criterios_y_aproximacion_a_la_solucion(self):
        for a, b, metodo, k, exacta in (
            (CLASE_A, CLASE_B, "jacobi", 15, (1, 2, -1, 1)),
            (CLASE_A, CLASE_B, "gauss_seidel", 6, (1, 2, -1, 1)),
            (PRACTICA_A, PRACTICA_B, "jacobi", 11, (5188/4591, 3147/4591, -1629/4591, 2597/4591)),
            (PRACTICA_A, PRACTICA_B, "gauss_seidel", 5, (5188/4591, 3147/4591, -1629/4591, 2597/4591)),
        ):
            with self.subTest(metodo=metodo, k=k):
                resultado = resolver_iterativo(a, b, metodo)
                self.assertEqual(resultado.estado, "convergio")
                self.assertEqual(resultado.final.k, k)
                self.assertEqual(resultado.filas_no_dominantes, ())
                self.assertTrue(all(abs(x - y) < 0.0001 for x, y in zip(resultado.final.x, exacta)))
                self.assertLess(resultado.final.cambio, 0.0001)
                self.assertLess(resultado.final.norma_residuo, 0.0001)
                anterior = resultado.iteraciones[-2]
                self.assertGreaterEqual(max(anterior.cambio, anterior.norma_residuo), 0.0001)

        jacobi = resolver_iterativo(CLASE_A, CLASE_B, "jacobi")
        self.assertLess(jacobi.iteraciones[13].cambio, 0.0001)
        self.assertGreater(jacobi.iteraciones[13].norma_residuo, 0.0001)

    def test_ambos_criterios_son_estrictos(self):
        solo_cambio = resolver_iterativo([[2]], [2], "jacobi", tolerancia=1, max_iteraciones=1)
        self.assertEqual((solo_cambio.final.cambio, solo_cambio.final.norma_residuo), (1, 0))
        self.assertEqual(solo_cambio.estado, "limite")
        solo_residuo = resolver_iterativo([[4, 2], [2, 4]], [2, 2], "jacobi",
                                         tolerancia=1, max_iteraciones=1)
        self.assertEqual((solo_residuo.final.cambio, solo_residuo.final.norma_residuo), (0.5, 1))
        self.assertEqual(solo_residuo.estado, "limite")

    def test_tabla_despejes_y_residuo_comparten_el_mismo_estado(self):
        for metodo in ("jacobi", "gauss_seidel"):
            with self.subTest(metodo=metodo):
                resultado = resolver_iterativo(CLASE_A, CLASE_B, metodo, inicial=(1, -1, 2, -2))
                self.assertEqual(resultado.iteraciones[0].x, (1, -1, 2, -2))
                self.assertIsNone(resultado.iteraciones[0].cambio)
                for anterior, actual in zip(resultado.iteraciones, resultado.iteraciones[1:]):
                    for i, despeje in enumerate(resultado.despejes):
                        total = 0
                        for termino in despeje.terminos:
                            j = termino.columna
                            self.assertEqual(termino.usa_nuevo, metodo == "gauss_seidel" and j < i)
                            origen = actual if termino.usa_nuevo else anterior
                            total += termino.coeficiente * origen.x[j]
                        self.assertAlmostEqual((despeje.independiente - total) / despeje.diagonal, actual.x[i])
                    self.assertVector(actual.residuo, [
                        bi - sum(c * x for c, x in zip(fila, actual.x))
                        for fila, bi in zip(CLASE_A, CLASE_B)
                    ])
                    self.assertEqual(actual.norma_residuo, max(map(abs, actual.residuo)))
                    self.assertEqual(actual.cambio, max(abs(x - y) for x, y in zip(actual.x, anterior.x)))
                self.assertIs(resultado.final, resultado.iteraciones[-1])

    def test_no_dominante_puede_converger_o_agotar_el_limite(self):
        for metodo in ("jacobi", "gauss_seidel"):
            con_solucion = resolver_iterativo([[1, 2], [1, 4]], [3, 5], metodo)
            self.assertEqual(con_solucion.filas_no_dominantes, (1,))
            self.assertEqual(con_solucion.estado, "convergio")
            agota = resolver_iterativo([[1, 2], [2, 1]], [3, 3], metodo, max_iteraciones=12)
            self.assertEqual(agota.filas_no_dominantes, (1, 2))
            self.assertEqual(agota.estado, "limite")
            self.assertEqual(agota.final.k, 12)

    def test_desbordamiento_preserva_la_ultima_fila_finita(self):
        resultado = resolver_iterativo([[1e-250, 1], [1, 1e-250]], [1, 1], "jacobi")
        self.assertEqual(resultado.estado, "rango")
        self.assertEqual(resultado.final.k, 1)
        self.assertEqual(resultado.final.x, (1e250, 1e250))

    def test_residuo_y_dominancia_respetan_los_coeficientes_ingresados(self):
        entero = 10_000_000_000_000_000
        resultado = resolver_iterativo([[1]], [entero + 1], "jacobi", max_iteraciones=3)
        self.assertEqual(resultado.final.x, (entero,))
        self.assertEqual(resultado.final.cambio, 0)
        self.assertEqual(resultado.final.norma_residuo, 1)
        self.assertEqual(resultado.estado, "limite")
        dominante = resolver_iterativo([[entero + 1, entero], [0, 1]], [0, 1], "jacobi")
        self.assertEqual(dominante.filas_no_dominantes, ())

    def test_entradas_invalidas(self):
        casos = (
            ([], [], "jacobi", {}),
            ([[1, 2]], [1], "jacobi", {}),
            ([[1, 2], [1]], [1, 2], "jacobi", {}),
            ([[0, 1], [1, 1]], [2, 2], "jacobi", {}),
            ([[1]], [1, 2], "jacobi", {}),
            ([[1]], [2], "gauss", {}),
            ([[nan]], [2], "jacobi", {}),
            ([[1]], [inf], "jacobi", {}),
            ([[10**500]], [2], "jacobi", {}),
            ([[1e308]], [1], "jacobi", {"inicial": [2]}),
            ([[1]], [2], "jacobi", {"inicial": [1, 2]}),
            ([[1]], [2], "jacobi", {"inicial": ["0"]}),
            ([[1]], [2], "jacobi", {"tolerancia": 0}),
            ([[1]], [2], "jacobi", {"tolerancia": inf}),
            ([[1]], [2], "jacobi", {"max_iteraciones": ITERACIONES_MAXIMAS + 1}),
            ([[1]], [2], "jacobi", {"max_iteraciones": 1.5}),
            ([[1] * 11] * 11, [1] * 11, "jacobi", {}),
        )
        for a, b, metodo, opciones in casos:
            with self.subTest(metodo=metodo, opciones=opciones):
                with self.assertRaises(ValueError):
                    resolver_iterativo(a, b, metodo, **opciones)
        with self.assertRaisesRegex(ValueError, "diagonal de la fila 2 es cero"):
            resolver_iterativo([[1, 2], [1, 0]], [2, 2], "gauss_seidel")
