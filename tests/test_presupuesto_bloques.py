"""P26.3 reutiliza las cotas de P26.2 para el ancho completo de [A | I]."""

import random
import unittest
from unittest.mock import patch

from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import aumentar_matrices, matriz_identidad
from backend.presupuesto_computacional import estimar_gauss_jordan


class PruebasPresupuestoBloques(unittest.TestCase):
    def test_aumento_con_identidad_cuenta_pivotes_izquierdos_y_ancho_total(self):
        for orden in (1, 2, 3, 6, 12):
            with self.subTest(orden=orden):
                estimacion = estimar_gauss_jordan(orden, 2 * orden, columnas_pivote=orden)
                self.assertEqual(estimacion.operacion, "gauss_jordan")
                self.assertEqual(estimacion.dimensiones, (orden, 2 * orden))
                self.assertEqual(estimacion.pasos, orden**2)
                # n normalizaciones y n(n-1) eliminaciones; cada una toca 2n columnas.
                self.assertEqual(estimacion.calculo, 2 * orden * (orden + 2 * orden * (orden - 1)))
                # Cada paso conserva las dos matrices completas, antes y después.
                self.assertEqual(estimacion.procedimiento, 2 * orden * (2 * orden) * orden**2)
                self.assertEqual(estimacion.factor_numerico, 1)

    def test_ampliar_derecha_mantiene_la_cota_de_pasos_y_cuenta_todas_las_celdas(self):
        for orden in (1, 2, 3, 8):
            with self.subTest(orden=orden):
                sistema = estimar_gauss_jordan(orden, orden + 1, columnas_pivote=orden)
                bloques = estimar_gauss_jordan(orden, 2 * orden, columnas_pivote=orden)
                self.assertEqual(bloques.pasos, sistema.pasos)
                self.assertAlmostEqual(bloques.calculo / sistema.calculo, 2 * orden / (orden + 1))
                self.assertAlmostEqual(bloques.procedimiento / sistema.procedimiento, 2 * orden / (orden + 1))

    def test_los_pasos_reales_de_aumentos_con_identidad_respetan_la_cota(self):
        aleatorio = random.Random(263)
        matrices = [
            [[3, 4], [5, 6]],
            [[0, 1, 2], [1, 0, 3], [4, -3, 8]],
            [[1, 2], [2, 4]],
            [[0, 2], [3, 0]],
            [[0, 0], [0, 0]],
        ]
        for orden in range(1, 7):
            for _ in range(8):
                matrices.append([[aleatorio.choice((0, 1, -1, 2, -3, 5)) for _ in range(orden)] for _ in range(orden)])
        for a in matrices:
            orden = len(a)
            with self.subTest(a=a):
                _, pasos, _ = aplicar_gauss_jordan(aumentar_matrices(a, matriz_identidad(orden)), columnas_pivote=orden)
                self.assertLessEqual(len(pasos), estimar_gauss_jordan(orden, 2 * orden, columnas_pivote=orden).pasos)

    def test_estimar_aumento_no_ejecuta_gauss_jordan(self):
        with patch("backend.gauss_jordan.aplicar_gauss_jordan", side_effect=AssertionError("No ejecutar el motor")) as motor:
            estimacion = estimar_gauss_jordan(10**6, 2 * 10**6, columnas_pivote=10**6)
        motor.assert_not_called()
        self.assertEqual(estimacion.pasos, 10**12)


if __name__ == "__main__":
    unittest.main()
