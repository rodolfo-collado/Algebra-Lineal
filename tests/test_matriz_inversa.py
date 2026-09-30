"""P26.4: matriz inversa por Gauss-Jordan sobre [A | I] y por la regla directa 2×2."""

from fractions import Fraction
from random import Random
import unittest
from unittest.mock import patch

from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import matriz_identidad, multiplicar_matrices
from backend.matriz_inversa import (
    DIRECTO_2X2, GAUSS_JORDAN, METODO_PREDETERMINADO, calcular_inversa,
    inversa_gauss_jordan, inversa_metodo_2x2, validar_matriz_cuadrada,
)
from backend.presupuesto_computacional import estimar_gauss_jordan
from backend.seguridad_numerica import BITS_MAXIMOS, MENSAJE_CALCULO_GRANDE

PROFESOR_2X2 = [[3, 4], [5, 6]]
INVERSA_2X2 = [[-3, 2], [Fraction(5, 2), Fraction(-3, 2)]]
PROFESOR_3X3 = [[0, 1, 2], [1, 0, 3], [4, -3, 8]]
INVERSA_3X3 = [
    [Fraction(-9, 2), 7, Fraction(-3, 2)],
    [-2, 4, -1],
    [Fraction(3, 2), -2, Fraction(1, 2)],
]
SINGULAR = [[1, 2], [2, 4]]

# 2×2 invertibles: enteros, negativos, fracciones y casos en que Gauss-Jordan intercambia filas.
INVERTIBLES_2X2 = (
    PROFESOR_2X2,
    [[2, 1], [1, 1]],
    [[-1, 3], [2, -5]],
    [[-4, -2], [-3, -1]],
    [[Fraction(1, 2), Fraction(1, 3)], [Fraction(-3, 4), 2]],
    [[Fraction(2, 3), -1], [Fraction(5, 7), Fraction(-1, 9)]],
    [[0, 1], [1, 0]],
    [[0, 2], [3, 4]],
    [[0, Fraction(-1, 2)], [Fraction(5, 3), 7]],
)


def es_identidad(matriz):
    return matriz == matriz_identidad(len(matriz))


class PruebasGaussJordan(unittest.TestCase):
    def test_ejemplo_del_profesor_2x2(self):
        calculo = inversa_gauss_jordan(PROFESOR_2X2)
        self.assertTrue(calculo["invertible"])
        self.assertEqual(calculo["inversa"], INVERSA_2X2)
        self.assertEqual(calculo["metodo"], GAUSS_JORDAN)
        self.assertEqual(calculo["orden"], 2)
        self.assertEqual(calculo["matriz"], PROFESOR_2X2)
        self.assertEqual(calculo["aumentada"], [[3, 4, 1, 0], [5, 6, 0, 1]])
        self.assertTrue(es_identidad(calculo["izquierda"]))
        self.assertEqual(calculo["derecha"], calculo["inversa"])
        self.assertEqual(calculo["pivotes"], [(0, 0), (1, 1)])
        self.assertEqual(
            [paso["operacion"] for paso in calculo["pasos"]],
            ["F1 = (1/3)F1", "F2 = F2 - (5)F1", "F2 = (-3/2)F2", "F1 = F1 - (4/3)F2"],
        )
        self.assertEqual(calculo["reducida"], [[1, 0, -3, 2], [0, 1, Fraction(5, 2), Fraction(-3, 2)]])
        self.assertTrue(all(isinstance(valor, Fraction) for fila in calculo["inversa"] for valor in fila))

    def test_ejemplo_del_profesor_3x3_con_intercambio_de_filas(self):
        calculo = inversa_gauss_jordan(PROFESOR_3X3)
        self.assertTrue(calculo["invertible"])
        self.assertEqual(calculo["inversa"], INVERSA_3X3)
        # a₁₁ = 0: el primer paso trae una fila con pivote.
        self.assertEqual(calculo["pasos"][0]["operacion"], "F1 <-> F2")
        self.assertEqual(calculo["pivotes"], [(0, 0), (1, 1), (2, 2)])

    def test_singular_no_llega_a_la_identidad(self):
        calculo = inversa_gauss_jordan(SINGULAR)
        self.assertFalse(calculo["invertible"])
        self.assertIsNone(calculo["inversa"])
        self.assertEqual(calculo["izquierda"], [[1, 2], [0, 0]])
        self.assertEqual(calculo["derecha"], [[1, 0], [-2, 1]])
        self.assertEqual(calculo["pivotes"], [(0, 0)])
        # Una columna sin pivote al principio también deja la izquierda lejos de I.
        for matriz in ([[0, 1], [0, 2]], [[0, 0], [0, 0]], [[1, 2, 3], [4, 5, 6], [7, 8, 9]]):
            with self.subTest(matriz=matriz):
                calculo = inversa_gauss_jordan(matriz)
                self.assertFalse(calculo["invertible"])
                self.assertLess(len(calculo["pivotes"]), len(matriz))
                self.assertFalse(es_identidad(calculo["izquierda"]))

    def test_uno_por_uno(self):
        calculo = inversa_gauss_jordan([[4]])
        self.assertEqual(calculo["inversa"], [[Fraction(1, 4)]])
        self.assertEqual([paso["operacion"] for paso in calculo["pasos"]], ["F1 = (1/4)F1"])
        self.assertFalse(inversa_gauss_jordan([[0]])["invertible"])

    def test_la_identidad_es_su_propia_inversa_sin_pasos(self):
        for n in (1, 3, 10):
            calculo = inversa_gauss_jordan(matriz_identidad(n))
            self.assertEqual(calculo["inversa"], matriz_identidad(n))
            self.assertEqual(calculo["pasos"], [])

    def test_a_por_su_inversa_da_la_identidad(self):
        aleatorio = Random(264)
        casos = [PROFESOR_2X2, PROFESOR_3X3, *INVERTIBLES_2X2]
        casos += [[[Fraction(aleatorio.randint(-9, 9), aleatorio.randint(1, 5)) for _ in range(n)] for _ in range(n)] for n in (3, 4, 6)]
        for matriz in casos:
            calculo = inversa_gauss_jordan(matriz)
            if calculo["invertible"]:
                with self.subTest(matriz=matriz):
                    self.assertTrue(es_identidad(multiplicar_matrices(matriz, calculo["inversa"])))
                    self.assertTrue(es_identidad(multiplicar_matrices(calculo["inversa"], matriz)))

    def test_reutiliza_el_motor_con_pivotes_solo_en_a(self):
        with patch("backend.matriz_inversa.aplicar_gauss_jordan", wraps=aplicar_gauss_jordan) as motor:
            inversa_gauss_jordan(PROFESOR_3X3)
        motor.assert_called_once()
        self.assertEqual(motor.call_args.args[0], [[0, 1, 2, 1, 0, 0], [1, 0, 3, 0, 1, 0], [4, -3, 8, 0, 0, 1]])
        self.assertEqual(motor.call_args.kwargs, {"columnas_pivote": 3})

    def test_no_modifica_la_entrada(self):
        matriz = [[0, 1, 2], [1, 0, 3], [4, -3, 8]]
        copia = [fila[:] for fila in matriz]
        inversa_gauss_jordan(matriz)
        inversa_metodo_2x2([fila[:2] for fila in matriz[:2]])
        self.assertEqual(matriz, copia)

    def test_la_cota_del_presupuesto_acota_los_pasos_reales(self):
        aleatorio = Random(26)
        casos = [PROFESOR_2X2, PROFESOR_3X3, SINGULAR, [[0, 1], [0, 2]], [[4]], matriz_identidad(4)]
        casos += [[[aleatorio.randint(-3, 3) for _ in range(n)] for _ in range(n)] for n in range(1, 9) for _ in range(5)]
        for matriz in casos:
            n = len(matriz)
            with self.subTest(matriz=matriz):
                cota = estimar_gauss_jordan(n, 2 * n, columnas_pivote=n).pasos
                self.assertLessEqual(len(inversa_gauss_jordan(matriz)["pasos"]), cota)


class PruebasMetodo2x2(unittest.TestCase):
    def test_ejemplo_del_profesor(self):
        calculo = inversa_metodo_2x2(PROFESOR_2X2)
        self.assertEqual(calculo["metodo"], DIRECTO_2X2)
        self.assertEqual(calculo["entradas"], {"a": 3, "b": 4, "c": 5, "d": 6})
        self.assertEqual((calculo["ad"], calculo["bc"], calculo["ad_menos_bc"]), (18, 20, -2))
        self.assertEqual(calculo["intercambiada"], [[6, -4], [-5, 3]])
        self.assertEqual(calculo["factor"], Fraction(-1, 2))
        self.assertTrue(calculo["invertible"])
        self.assertEqual(calculo["inversa"], INVERSA_2X2)
        self.assertTrue(all(isinstance(valor, Fraction) for fila in calculo["inversa"] for valor in fila))

    def test_ad_menos_bc_igual_a_cero_no_tiene_inversa(self):
        for matriz in (SINGULAR, [[0, 0], [0, 0]], [[Fraction(1, 2), 1], [1, 2]], [[-3, 6], [1, -2]]):
            with self.subTest(matriz=matriz):
                calculo = inversa_metodo_2x2(matriz)
                self.assertEqual(calculo["ad_menos_bc"], 0)
                self.assertFalse(calculo["invertible"])
                self.assertIsNone(calculo["factor"])
                self.assertIsNone(calculo["inversa"])
        self.assertEqual(inversa_metodo_2x2(SINGULAR)["intercambiada"], [[4, -2], [-2, 1]])

    def test_es_un_metodo_propio_sin_gauss_jordan(self):
        with patch("backend.matriz_inversa.aplicar_gauss_jordan", side_effect=AssertionError("usó Gauss-Jordan")):
            self.assertEqual(inversa_metodo_2x2(PROFESOR_2X2)["inversa"], INVERSA_2X2)

    def test_solo_para_matrices_2x2(self):
        for matriz in ([[4]], PROFESOR_3X3, [[1] * 10 for _ in range(10)]):
            with self.subTest(n=len(matriz)), self.assertRaisesRegex(ValueError, "solo se aplica a matrices 2×2"):
                inversa_metodo_2x2(matriz)
        with self.assertRaisesRegex(ValueError, "matriz cuadrada"):
            inversa_metodo_2x2([[1, 2, 3], [4, 5, 6]])


class PruebasConsistencia(unittest.TestCase):
    def test_ambos_metodos_dan_la_misma_inversa_en_2x2(self):
        for matriz in INVERTIBLES_2X2:
            with self.subTest(matriz=matriz):
                gauss_jordan = inversa_gauss_jordan(matriz)
                directo = inversa_metodo_2x2(matriz)
                self.assertTrue(gauss_jordan["invertible"])
                self.assertEqual(gauss_jordan["inversa"], directo["inversa"])
        # Los que exigen intercambio de filas lo hacen de verdad.
        self.assertEqual(inversa_gauss_jordan([[0, 2], [3, 4]])["pasos"][0]["operacion"], "F1 <-> F2")

    def test_coinciden_tambien_al_decidir_que_no_hay_inversa(self):
        aleatorio = Random(2604)
        valores = [0, 1, -1, 2, -3, Fraction(1, 2), Fraction(-2, 3)]
        for _ in range(400):
            matriz = [[aleatorio.choice(valores) for _ in range(2)] for _ in range(2)]
            gauss_jordan, directo = inversa_gauss_jordan(matriz), inversa_metodo_2x2(matriz)
            with self.subTest(matriz=matriz):
                self.assertEqual(gauss_jordan["invertible"], directo["invertible"])
                self.assertEqual(gauss_jordan["inversa"], directo["inversa"])


class PruebasValidacion(unittest.TestCase):
    def test_rechaza_matrices_no_cuadradas_vacias_o_no_exactas(self):
        casos = (
            ([[1, 2, 3], [4, 5, 6]], "Solo una matriz cuadrada puede tener inversa: A es 2×3."),
            ([[1], [2]], "A es 2×1"),
            ([], "vacía"),
            ([[1, 2], [3]], "rectangular"),
            ([[0.5, 1], [1, 1]], "número exacto"),
            ([["1", 2], [3, 4]], "número exacto"),
            ([[True, 0], [0, 1]], "número exacto"),
        )
        for matriz, mensaje in casos:
            for calcular in (inversa_gauss_jordan, inversa_metodo_2x2):
                with self.subTest(matriz=matriz, metodo=calcular.__name__), self.assertRaisesRegex(ValueError, mensaje):
                    calcular(matriz)
        self.assertEqual(validar_matriz_cuadrada(PROFESOR_3X3), (True, ""))

    def test_calcular_inversa_elige_el_metodo(self):
        self.assertEqual(METODO_PREDETERMINADO, GAUSS_JORDAN)
        self.assertEqual(calcular_inversa(PROFESOR_2X2)["metodo"], GAUSS_JORDAN)
        self.assertEqual(calcular_inversa(PROFESOR_2X2, DIRECTO_2X2)["metodo"], DIRECTO_2X2)
        for metodo in ("gauss", "determinante", "", None, ["gauss_jordan"]):
            with self.subTest(metodo=metodo), self.assertRaisesRegex(ValueError, "Selecciona un método válido"):
                calcular_inversa(PROFESOR_2X2, metodo)
        # Un método 2×2 manipulado sobre otra dimensión se rechaza también aquí.
        with self.assertRaisesRegex(ValueError, "solo se aplica a matrices 2×2"):
            calcular_inversa(PROFESOR_3X3, DIRECTO_2X2)


class PruebasSeguridadNumerica(unittest.TestCase):
    def test_entradas_extremas_se_rechazan_con_el_mensaje_controlado(self):
        enorme = 1 << BITS_MAXIMOS
        for calcular in (inversa_gauss_jordan, inversa_metodo_2x2):
            with self.subTest(metodo=calcular.__name__), self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                calcular([[enorme, 1], [1, 1]])

    def test_productos_que_crecen_demasiado_se_detienen(self):
        x = Fraction(1 << (BITS_MAXIMOS // 2 + 1))
        with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
            inversa_metodo_2x2([[x, 1], [1, x]])
        # Gauss-Jordan: la eliminación de x·x ya supera el límite.
        with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
            inversa_gauss_jordan([[1, x], [x, 1]])

    def test_fracciones_admitidas_que_crecen_en_la_eliminacion(self):
        from tests.test_seguridad_numerica import matriz_de_crecimiento

        matriz = [fila[:6] for fila in matriz_de_crecimiento()]
        with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
            inversa_gauss_jordan(matriz)
        # La regla 2×2 con literales de 100 cifras sí cabe: pocos productos.
        calculo = inversa_metodo_2x2([fila[:2] for fila in matriz[:2]])
        self.assertTrue(es_identidad(multiplicar_matrices([fila[:2] for fila in matriz[:2]], calculo["inversa"])))


if __name__ == "__main__":
    unittest.main()
