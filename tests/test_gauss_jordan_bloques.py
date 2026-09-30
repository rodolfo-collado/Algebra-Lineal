"""P26.3: el mismo Gauss-Jordan transforma todos los bloques con pivotes en A."""

from fractions import Fraction
import unittest
from unittest.mock import patch

from backend.gauss import aplicar_gauss
from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import aumentar_matrices, matriz_identidad, multiplicar_matrices, separar_bloques
from backend.seguridad_numerica import MENSAJE_CALCULO_GRANDE


class PruebasAumentoConIdentidad(unittest.TestCase):
    def comprobar_reduccion(self, a, derecha_esperada):
        orden = len(a)
        identidad = matriz_identidad(orden)
        aumentada = aumentar_matrices(a, identidad)
        reducida, pasos, pivotes = aplicar_gauss_jordan(aumentada, columnas_pivote=orden)
        izquierda, derecha = separar_bloques(reducida, orden)
        self.assertEqual(izquierda, identidad)
        self.assertEqual(derecha, derecha_esperada)
        self.assertEqual(pivotes, [(i, i) for i in range(orden)])
        self.assertEqual(multiplicar_matrices(a, derecha), identidad)
        self.assertEqual(multiplicar_matrices(derecha, a), identidad)
        self.assertTrue(all(isinstance(valor, Fraction) for fila in reducida for valor in fila))
        self.assertEqual(aumentada, aumentar_matrices(a, identidad))
        return pasos

    def test_orden_uno(self):
        self.comprobar_reduccion([[3]], [[Fraction(1, 3)]])

    def test_ejemplo_dos_por_dos_del_profesor(self):
        self.comprobar_reduccion(
            [[3, 4], [5, 6]],
            [[-3, 2], [Fraction(5, 2), Fraction(-3, 2)]],
        )

    def test_ejemplo_tres_por_tres_del_profesor(self):
        pasos = self.comprobar_reduccion(
            [[0, 1, 2], [1, 0, 3], [4, -3, 8]],
            [[Fraction(-9, 2), 7, Fraction(-3, 2)], [-2, 4, -1], [Fraction(3, 2), -2, Fraction(1, 2)]],
        )
        self.assertEqual(pasos[0]["operacion"], "F1 <-> F2")

    def test_matriz_que_requiere_intercambiar_filas(self):
        self.comprobar_reduccion([[0, 2], [3, 0]], [[0, Fraction(1, 3)], [Fraction(1, 2), 0]])

    def test_fracciones_exactas_en_ambos_bloques(self):
        self.comprobar_reduccion(
            [[Fraction(1, 2), Fraction(1, 3)], [0, Fraction(2, 3)]],
            [[2, -1], [0, Fraction(3, 2)]],
        )

    def test_singular_conserva_la_evidencia_de_que_la_izquierda_no_llego_a_identidad(self):
        a = [[1, 2], [2, 4]]
        identidad = matriz_identidad(2)
        reducida, _, pivotes = aplicar_gauss_jordan(aumentar_matrices(a, identidad), columnas_pivote=2)
        izquierda, derecha = separar_bloques(reducida, 2)
        self.assertEqual(izquierda, [[1, 2], [0, 0]])
        self.assertNotEqual(izquierda, identidad)
        self.assertEqual(pivotes, [(0, 0)])
        self.assertLess(len(pivotes), len(a))
        self.assertEqual(derecha, [[1, 0], [-2, 1]])
        self.assertTrue(all(columna < 2 for _, columna in pivotes))


class PruebasContratoMultiplesColumnas(unittest.TestCase):
    def test_bloque_izquierdo_rectangular_y_derecho_de_tres_columnas(self):
        a = [[0, 2, 4], [0, 0, 3]]
        b = [[2, 4, 6], [3, 6, 9]]
        reducida, _, pivotes = aplicar_gauss_jordan(aumentar_matrices(a, b), columnas_pivote=3)
        izquierda, derecha = separar_bloques(reducida, 3)
        self.assertEqual(izquierda, [[0, 1, 0], [0, 0, 1]])
        self.assertEqual(derecha, [[-1, -2, -3], [1, 2, 3]])
        self.assertEqual(pivotes, [(0, 1), (1, 2)])

    def test_una_columna_izquierda_y_varias_columnas_derechas(self):
        reducida, _, pivotes = aplicar_gauss_jordan(
            aumentar_matrices([[2], [4]], [[2, 4, 6], [8, 12, 16]]), columnas_pivote=1,
        )
        self.assertEqual(reducida, [[1, 1, 2, 3], [0, 4, 4, 4]])
        self.assertEqual(pivotes, [(0, 0)])

    def test_bloque_izquierdo_cero_no_busca_pivotes_en_derecha(self):
        aumentada = aumentar_matrices([[0, 0], [0, 0]], [[1, 2], [3, 4]])
        reducida, pasos, pivotes = aplicar_gauss_jordan(aumentada, columnas_pivote=2)
        self.assertEqual(reducida, aumentada)
        self.assertEqual(pasos, [])
        self.assertEqual(pivotes, [])

    def test_intercambio_normalizacion_y_eliminacion_conservan_todas_las_columnas_en_cada_paso(self):
        entrada = aumentar_matrices([[0, 2], [3, 1]], [[5, 7], [11, 13]])
        reducida, pasos, pivotes = aplicar_gauss_jordan(entrada, columnas_pivote=2)
        self.assertEqual(pivotes, [(0, 0), (1, 1)])
        self.assertEqual(pasos, [
            {
                "antes": [[0, 2, 5, 7], [3, 1, 11, 13]],
                "operacion": "F1 <-> F2",
                "despues": [[3, 1, 11, 13], [0, 2, 5, 7]],
            },
            {
                "antes": [[3, 1, 11, 13], [0, 2, 5, 7]],
                "operacion": "F1 = (1/3)F1",
                "despues": [[1, Fraction(1, 3), Fraction(11, 3), Fraction(13, 3)], [0, 2, 5, 7]],
            },
            {
                "antes": [[1, Fraction(1, 3), Fraction(11, 3), Fraction(13, 3)], [0, 2, 5, 7]],
                "operacion": "F2 = (1/2)F2",
                "despues": [[1, Fraction(1, 3), Fraction(11, 3), Fraction(13, 3)], [0, 1, Fraction(5, 2), Fraction(7, 2)]],
            },
            {
                "antes": [[1, Fraction(1, 3), Fraction(11, 3), Fraction(13, 3)], [0, 1, Fraction(5, 2), Fraction(7, 2)]],
                "operacion": "F1 = F1 - (1/3)F2",
                "despues": [[1, 0, Fraction(17, 6), Fraction(19, 6)], [0, 1, Fraction(5, 2), Fraction(7, 2)]],
            },
        ])
        self.assertEqual(reducida, pasos[-1]["despues"])
        self.assertEqual(entrada, [[0, 2, 5, 7], [3, 1, 11, 13]])
        for paso in pasos:
            for matriz in (paso["antes"], paso["despues"]):
                self.assertTrue(all(len(fila) == 4 for fila in matriz))
                self.assertTrue(all(isinstance(valor, Fraction) for fila in matriz for valor in fila))
        pasos[-1]["despues"][0][2] = Fraction(99)
        self.assertEqual(reducida[0][2], Fraction(17, 6))
        self.assertEqual(pasos[-1]["antes"][0][2], Fraction(11, 3))


class PruebasSeguridadBloqueDerecho(unittest.TestCase):
    def test_normalizacion_se_detiene_por_crecimiento_en_una_columna_derecha(self):
        self.comprobar_error_sin_registro([[Fraction(1, 16)]], [[1, 16]], columnas_pivote=1)

    def test_eliminacion_hacia_abajo_se_detiene_por_crecimiento_en_derecha(self):
        self.comprobar_error_sin_registro([[1], [16]], [[0, 16], [1, 0]], columnas_pivote=1)

    def test_eliminacion_hacia_arriba_comprueba_tambien_todo_el_bloque_derecho(self):
        entrada = aumentar_matrices([[1, 16], [0, 1]], [[0, 0], [0, 16]])
        with patch("backend.seguridad_numerica.BITS_MAXIMOS", 8):
            self.assertEqual(aplicar_gauss(entrada, columnas_pivote=2), (entrada, [], [(0, 0), (1, 1)]))
        self.comprobar_error_sin_registro([[1, 16], [0, 1]], [[0, 0], [0, 16]], columnas_pivote=2)

    def comprobar_error_sin_registro(self, a, b, columnas_pivote):
        entrada = aumentar_matrices(a, b)
        copia = [fila[:] for fila in entrada]
        with patch("backend.seguridad_numerica.BITS_MAXIMOS", 8), patch(
            "backend.operaciones_filas.registrar_paso", side_effect=AssertionError("No registrar el valor inseguro"),
        ) as registrar:
            with self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                aplicar_gauss_jordan(entrada, columnas_pivote=columnas_pivote)
        registrar.assert_not_called()
        self.assertEqual(entrada, copia)


if __name__ == "__main__":
    unittest.main()
