"""Contrato reutilizable de LU rectangular y evidencia del procedimiento de clase."""

import unittest
from fractions import Fraction as F

from backend.factorizacion_lu import factorizar_lu
from backend.matrices import matriz_identidad, resolver_operacion_matrices
from backend.seguridad_numerica import BITS_MAXIMOS


A_CLASE = [[2, 4, -1, 5, -2], [-4, -5, 3, -8, 1],
           [2, -5, -4, 1, 8], [-6, 0, 7, -3, 1]]
L_CLASE = [[1, 0, 0, 0], [-2, 1, 0, 0], [1, -3, 1, 0], [-3, 4, 2, 1]]
U_CLASE = [[2, 4, -1, 5, -2], [0, 3, 1, 2, -3], [0, 0, 0, 2, 1], [0, 0, 0, 0, 5]]


class LUGeneral(unittest.TestCase):
    def comprobar(self, a):
        original = [fila[:] for fila in a]
        d = factorizar_lu(a)
        self.assertTrue(d["aplicable"])
        m, n = len(a), len(a[0])
        self.assertEqual([len(fila) for fila in d["l"]], [m] * m)
        self.assertEqual([len(fila) for fila in d["u"]], [n] * m)
        self.assertEqual(resolver_operacion_matrices("producto", a=d["l"], b=d["u"])["resultado"], a)
        self.assertTrue(all(d["l"][i][i] == 1 and all(d["l"][i][j] == 0 for j in range(i + 1, m)) for i in range(m)))
        actual_a, actual_l = [fila[:] for fila in a], [fila[:] for fila in d["l"]]
        pasos = iter(d["pasos"])
        for etapa in d["etapas"]:
            self.assertEqual(etapa["u_antes"], actual_a)
            r, c = etapa["fila_pivote"] - 1, etapa["columna_pivote"] - 1
            self.assertEqual(etapa["pivote"], actual_a[r][c])
            self.assertEqual(etapa["columna_l"], r + 1)
            self.assertEqual([e["fila"] for e in etapa["entradas"]], list(range(r + 1, m + 1)))
            for entrada in etapa["entradas"]:
                i = entrada["fila"] - 1
                self.assertEqual(entrada["entrada"], actual_a[i][c])
                self.assertEqual(entrada["cociente"], F(actual_a[i][c]) / actual_a[r][c])
                self.assertEqual(entrada["posicion_l"], (i + 1, r + 1))
                self.assertEqual(d["l"][i][r], entrada["cociente"])
            for op in etapa["operaciones"]:
                paso = next(pasos)
                self.assertEqual(paso["antes"], actual_a)
                self.assertEqual(op["operacion"], paso["operacion"])
                i, j, k = op["fila"] - 1, op["fila_pivote"] - 1, op["factor"]
                # Reproducir la misma operación en ambas matrices, con una referencia independiente.
                for matriz in (actual_a, actual_l):
                    matriz[i] = [x - k * y for x, y in zip(matriz[i], matriz[j])]
                self.assertEqual(paso["despues"], actual_a)
                self.assertNotIn("correccion_determinante", paso)
        self.assertIsNone(next(pasos, None))
        self.assertEqual(actual_a, d["u"])
        self.assertEqual(actual_l, matriz_identidad(m))
        self.assertEqual(d["verificacion"]["l_reducida"], actual_l)
        self.assertTrue(d["verificacion"]["es_identidad"])
        self.assertEqual(d["verificacion"]["reemplazos"], len(d["pasos"]))
        self.assertEqual(a, original)
        return d

    def test_ejemplo_4x5_de_las_diapositivas(self):
        d = self.comprobar(A_CLASE)
        self.assertEqual(d["l"], L_CLASE)
        self.assertEqual(d["u"], U_CLASE)
        self.assertEqual([(e["fila_pivote"], e["columna_pivote"]) for e in d["etapas"]],
                         [(1, 1), (2, 2), (3, 4), (4, 5)])
        self.assertEqual([[x["cociente"] for x in e["entradas"]] for e in d["etapas"]],
                         [[1, -2, 1, -3], [1, -3, 4], [1, 2], [1]])

    def test_rectangulares_altas_anchas_y_columnas_iniciales_nulas(self):
        for a in ([[2, 4], [4, 11], [-2, 5], [0, 3]],
                  [[0, 2, 3, 1], [0, 4, 8, 5]],
                  [[0, 0, 2, 1], [0, 0, 4, 5], [0, 0, -2, 2]],
                  [[0, 0, 0], [0, 0, 0]], [[5]], [[0]], [[F(-2, 3)], [F(1, 2)]],
                  [[0, F(-2, 3), F(1, 2)]]):
            with self.subTest(a=a):
                self.comprobar(a)

    def test_intercambio_necesario_tras_saltar_una_columna_sigue_no_aplicable(self):
        a = [[0, 1, 2], [0, 2, 4], [0, 0, 1]]
        d = factorizar_lu(a)
        self.assertFalse(d["aplicable"])
        self.assertEqual(d["pivote_nulo"], {"fila": 2, "columna": 3})
        self.assertEqual(len(d["etapas"]), 1)
        self.assertIsNone(d["verificacion"])
        self.assertFalse(any("<->" in p["operacion"] for p in d["pasos"]))

    def test_validacion_y_seguridad_del_helper_rectangular(self):
        for a in ([], [[]], [[1], [1, 2]], [[True]], [[0.5]], [["1"]], [[1 << BITS_MAXIMOS, 1]],
                  [[F(1, 1 << 7000), 0, 1], [1 << 7000, 1, 0]]):
            with self.subTest(a=a), self.assertRaises(ValueError):
                factorizar_lu(a)


if __name__ == "__main__":
    unittest.main()
