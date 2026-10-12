"""Determinantes: cinco métodos exactos, su evidencia y los límites del procedimiento."""

import unittest
from fractions import Fraction as F
from itertools import permutations
from random import Random
from unittest.mock import patch

from backend.determinantes import calcular_determinante
from backend.determinantes.cofactores import ORDEN_MAXIMO_COFACTORES, menor
from backend.determinantes.comun import directo_2x2
from backend.determinantes.presupuesto import estimar_determinante
from backend.factorizacion_lu import factorizar_lu
from backend.matrices import resolver_operacion_matrices
from backend.matriz_inversa import calcular_inversa
from backend.presupuesto_computacional import Categoria, categoria
from backend.seguridad_numerica import BITS_MAXIMOS


def leibniz(a):
    """Referencia independiente: suma de permutaciones con signo."""
    total = F(0)
    for perm in permutations(range(len(a))):
        signo = (-1) ** sum(perm[i] > perm[j] for i in range(len(a)) for j in range(i + 1, len(a)))
        termino = F(signo)
        for i, j in enumerate(perm):
            termino *= a[i][j]
        total += termino
    return total


def metodos_para(n):
    metodos = ["reduccion", "lu", "cofactores"]
    if n == 2:
        metodos.append("directo_2x2")
    if n == 3:
        metodos.append("sarrus")
    return metodos


def producto_lu(datos):
    return resolver_operacion_matrices("producto", a=datos["l"], b=datos["u"])["resultado"]


def nodos(arbol):
    """Términos con menor calculado en todo el árbol de cofactores."""
    total = 0
    for termino in arbol.get("terminos", []):
        if termino["hijo"] is not None:
            total += 1 + nodos(termino["hijo"])
    return total


class FormulaDirecta(unittest.TestCase):
    def test_ad_menos_bc_negativo_y_singular(self):
        for a, esperado in (([[3, 4], [5, 6]], -2), ([[1, 2], [2, 4]], 0), ([[F(1, 2), 3], [0, F(2, 3)]], F(1, 3))):
            with self.subTest(a=a):
                d = calcular_determinante(a, "directo_2x2")
                self.assertEqual(d["determinante"], esperado)
                self.assertEqual((d["ad"], d["bc"]), (a[0][0] * a[1][1], a[0][1] * a[1][0]))

    def test_solo_2x2(self):
        for a in ([[1]], [[1, 2, 3], [4, 5, 6], [7, 8, 9]]):
            with self.subTest(n=len(a)), self.assertRaisesRegex(ValueError, "2×2"):
                calcular_determinante(a, "directo_2x2")

    def test_matriz_inversa_reutiliza_la_misma_formula(self):
        # Una sola implementación de ad − bc: la regla 2×2 de la inversa la llama.
        with patch("backend.matriz_inversa.directo_2x2", wraps=directo_2x2) as formula:
            inversa = calcular_inversa([[1, 2], [3, 4]], "directo_2x2")
        formula.assert_called_once()
        self.assertEqual(inversa["determinante"], -2)
        self.assertEqual(inversa["ad_menos_bc"], -2)
        self.assertEqual(inversa["inversa"], [[-2, 1], [F(3, 2), F(-1, 2)]])


class Sarrus(unittest.TestCase):
    def test_seis_diagonales(self):
        d = calcular_determinante([[1, 2, 3], [4, 5, 6], [7, 8, 10]], "sarrus")
        self.assertEqual([x["producto"] for x in d["positivas"]["diagonales"]], [50, 84, 96])
        self.assertEqual([x["producto"] for x in d["negativas"]["diagonales"]], [48, 80, 105])
        self.assertEqual([x["posiciones"] for x in d["positivas"]["diagonales"]][0], [(0, 0), (1, 1), (2, 2)])
        self.assertEqual([x["posiciones"] for x in d["negativas"]["diagonales"]][2], [(0, 2), (1, 1), (2, 0)])
        self.assertEqual((d["positivas"]["suma"], d["negativas"]["suma"]), (230, 233))
        self.assertEqual(d["determinante"], -3)

    def test_solo_3x3(self):
        for n in (1, 2, 4):
            with self.subTest(n=n), self.assertRaisesRegex(ValueError, "Sarrus solo se aplica a matrices 3×3"):
                calcular_determinante([[1] * n for _ in range(n)], "sarrus")


class Cofactores(unittest.TestCase):
    A = [[2, 1, 3], [0, 4, 2], [1, 0, 5]]

    def test_cualquier_fila_o_columna_da_el_mismo_determinante(self):
        for eje in ("fila", "columna"):
            for indice in range(1, 4):
                with self.subTest(eje=eje, indice=indice):
                    d = calcular_determinante(self.A, "cofactores", f"{eje}_{indice}")
                    self.assertEqual(d["determinante"], 30)
                    self.assertEqual((d["eje"], d["indice"], d["automatico"]), (eje, indice, False))
                    self.assertEqual(sum(t["contribucion"] for t in d["terminos"]), 30)
                    linea = [(t["fila"], t["columna"]) for t in d["terminos"]]
                    esperada = [(indice, k) for k in range(1, 4)] if eje == "fila" else [(k, indice) for k in range(1, 4)]
                    self.assertEqual(linea, esperada)

    def test_menor_signo_cofactor_y_contribucion(self):
        a = [[1, 2, 3], [4, 5, 6], [7, 8, 10]]
        self.assertEqual(menor(a, 0, 1), [[4, 6], [7, 10]])
        t = calcular_determinante(a, "cofactores", "fila_1")["terminos"][1]
        self.assertEqual((t["valor_menor"], t["signo"], t["cofactor"], t["contribucion"]), (-2, -1, 2, 4))
        # Signos en tablero: + − + / − + − / + − +.
        signos = [[t["signo"] for t in calcular_determinante(a, "cofactores", f"fila_{i}")["terminos"]] for i in (1, 2, 3)]
        self.assertEqual(signos, [[1, -1, 1], [-1, 1, -1], [1, -1, 1]])

    def test_menores_2x2_usan_ad_menos_bc_y_los_mayores_se_desarrollan(self):
        d = calcular_determinante(self.A, "cofactores", "fila_1")
        hijo = d["terminos"][0]["hijo"]
        self.assertEqual((hijo["ad"], hijo["bc"], hijo["determinante"]), (20, 0, 20))
        d4 = calcular_determinante([[2, 1, 3, 0], [0, 4, 2, 1], [1, 0, 5, 2], [3, 1, 0, 1]], "cofactores")
        hijo = d4["terminos"][0]["hijo"]
        self.assertTrue(hijo["automatico"])
        self.assertEqual(len(hijo["terminos"]), 3)
        self.assertEqual(d4["determinante"], leibniz([[2, 1, 3, 0], [0, 4, 2, 1], [1, 0, 5, 2], [3, 1, 0, 1]]))

    def test_automatico_elige_mas_ceros_y_desempata_por_la_primera_fila(self):
        d = calcular_determinante([[1, 0, 2], [3, 0, 4], [5, 1, 6]], "cofactores")
        self.assertEqual((d["eje"], d["indice"], d["automatico"]), ("columna", 2, True))
        d = calcular_determinante([[1, 2], [0, 0]], "cofactores")
        self.assertEqual((d["eje"], d["indice"], d["determinante"]), ("fila", 2, 0))
        d = calcular_determinante([[1, 1], [1, 1]], "cofactores")
        self.assertEqual((d["eje"], d["indice"]), ("fila", 1))

    def test_un_cero_no_calcula_su_menor(self):
        d = calcular_determinante([[1, 0, 2], [3, 0, 4], [5, 1, 6]], "cofactores", "fila_1")
        cero = d["terminos"][1]
        self.assertIsNone(cero["hijo"])
        self.assertEqual((cero["contribucion"], cero["valor_menor"], cero["cofactor"]), (0, None, None))

    def test_expansion_inexistente(self):
        for expansion in ("fila_4", "columna_0", "diagonal", "", None):
            with self.subTest(expansion=expansion), self.assertRaises(ValueError):
                calcular_determinante(self.A, "cofactores", expansion)
        with self.assertRaises(ValueError):
            calcular_determinante([[1]], "cofactores", "fila_2")


class FactorizacionLU(unittest.TestCase):
    def test_l_guarda_multiplicadores_y_a_es_lu(self):
        a = [[2, 1, 1], [4, -6, 0], [-2, 7, 2]]
        d = factorizar_lu(a)
        self.assertTrue(d["aplicable"])
        self.assertIsNone(d["pivote_nulo"])
        self.assertEqual(d["l"], [[1, 0, 0], [2, 1, 0], [-1, -1, 1]])
        self.assertEqual(d["u"], [[2, 1, 1], [0, -8, -2], [0, 0, 1]])
        self.assertEqual(producto_lu(d), a)
        self.assertEqual(a, [[2, 1, 1], [4, -6, 0], [-2, 7, 2]])
        # Solo reemplazos: ningún paso intercambia ni normaliza.
        self.assertTrue(all("correccion_determinante" not in p for p in d["pasos"]))
        self.assertEqual(calcular_determinante(a, "lu")["determinante"], -16)

    def test_l_triangular_inferior_con_unos_y_u_triangular_superior(self):
        rng = Random(30)
        for _ in range(20):
            a = [[F(rng.randint(1, 5), rng.randint(1, 3)) if i == j else F(rng.randint(-4, 4)) for j in range(4)] for i in range(4)]
            d = factorizar_lu(a)
            if not d["aplicable"]:
                continue
            with self.subTest(a=a):
                self.assertTrue(all(d["l"][i][i] == 1 and all(d["l"][i][j] == 0 for j in range(i + 1, 4)) for i in range(4)))
                self.assertTrue(all(d["u"][i][j] == 0 for i in range(4) for j in range(i)))
                self.assertEqual(producto_lu(d), a)

    def test_un_pivote_cero_con_algo_debajo_detiene_lu(self):
        for a, pivote in (([[0, 1], [1, 0]], 1), ([[1, 1, 0], [1, 1, 1], [0, 1, 1]], 2)):
            with self.subTest(a=a):
                d = calcular_determinante(a, "lu")
                self.assertFalse(d["aplicable"])
                self.assertNotIn("determinante", d)
                self.assertEqual(d["pivote_nulo"], {"fila": pivote, "columna": pivote})

    def test_un_pivote_cero_sin_nada_debajo_sigue(self):
        a = [[0, 2, 3], [0, 4, 5], [0, 0, 0]]
        d = calcular_determinante(a, "lu")
        self.assertTrue(d["aplicable"])
        self.assertEqual(d["determinante"], 0)
        self.assertEqual(producto_lu(d), a)

    def test_es_reutilizable_sin_determinantes(self):
        with self.assertRaisesRegex(ValueError, "cuadrada"):
            factorizar_lu([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(factorizar_lu([[5]])["u"], [[5]])


class Reduccion(unittest.TestCase):
    def test_corrige_intercambios_y_normalizaciones(self):
        for a in ([[0, 2], [3, 4]], [[2, 1], [4, 3]], [[2, 3], [0, -5]], [[0, 2, 1], [3, 4, 5], [1, 1, 1]]):
            with self.subTest(a=a):
                d = calcular_determinante(a)
                correccion = F(1)
                for p in d["pasos"]:
                    correccion *= p.get("correccion_determinante", 1)
                self.assertEqual(d["determinante"], d["producto_diagonal"] * correccion)
                self.assertEqual(d["determinante"], leibniz(a))

    def test_no_basta_multiplicar_la_diagonal_de_gauss(self):
        # Gauss normaliza los pivotes: su diagonal es de unos aunque det(A) = −6.
        d = calcular_determinante([[0, 2], [3, 4]], "reduccion")
        self.assertEqual(d["diagonal"], [1, 1])
        self.assertEqual(d["determinante"], -6)
        # F1 <-> F2 (×−1), F1 = (1/3)F1 (×3) y F2 = (1/2)F2 (×2): (−1)·3·2 = −6.
        self.assertEqual([p.get("correccion_determinante") for p in d["pasos"]], [-1, 3, 2])

    def test_sin_intercambios_y_singular(self):
        d = calcular_determinante([[2, 4], [1, 3]], "reduccion")
        self.assertNotIn(-1, [p.get("correccion_determinante") for p in d["pasos"]])
        self.assertEqual(d["determinante"], 2)
        d = calcular_determinante([[1, 2], [2, 4]], "reduccion")
        self.assertEqual((d["producto_diagonal"], d["determinante"]), (0, 0))


class Propiedades(unittest.TestCase):
    def test_intercambiar_dos_filas_cambia_el_signo_en_todos_los_metodos(self):
        a = [[2, 1, 3], [0, 4, 2], [1, 0, 5]]
        b = [a[0], a[2], a[1]]
        for metodo in metodos_para(3):
            with self.subTest(metodo=metodo):
                self.assertEqual(calcular_determinante(b, metodo)["determinante"],
                                 -calcular_determinante(a, metodo)["determinante"])

    def test_escalar_una_fila_escala_el_determinante(self):
        a = [[2, 1, 3], [0, 4, 2], [1, 0, 5]]
        b = [a[0], [F(3, 2) * v for v in a[1]], a[2]]
        for metodo in metodos_para(3):
            with self.subTest(metodo=metodo):
                self.assertEqual(calcular_determinante(b, metodo)["determinante"], F(3, 2) * 30)

    def test_triangular_es_el_producto_de_la_diagonal(self):
        superior = [[2, 7, -1, 4], [0, -3, 5, 1], [0, 0, F(1, 2), 9], [0, 0, 0, 4]]
        inferior = [[fila[j] for fila in superior] for j in range(4)]
        for a in (superior, inferior):
            for metodo in metodos_para(4):
                with self.subTest(metodo=metodo, superior=a is superior):
                    self.assertEqual(calcular_determinante(a, metodo)["determinante"], -12)

    def test_fila_de_ceros(self):
        a = [[1, 2, 3], [0, 0, 0], [4, 5, 6]]
        for metodo in metodos_para(3):
            with self.subTest(metodo=metodo):
                d = calcular_determinante(a, metodo)
                if d["aplicable"]:
                    self.assertEqual(d["determinante"], 0)

    def test_uno_por_uno(self):
        for valor in (0, -5, F(2, 3)):
            for metodo in ("cofactores", "lu", "reduccion"):
                with self.subTest(valor=valor, metodo=metodo):
                    self.assertEqual(calcular_determinante([[valor]], metodo)["determinante"], valor)

    def test_todos_los_metodos_coinciden_con_leibniz(self):
        rng = Random(91)
        for n in range(1, 6):
            for _ in range(12 if n < 5 else 4):
                a = [[F(rng.randint(-3, 3), rng.randint(1, 4)) for _ in range(n)] for _ in range(n)]
                original = [f[:] for f in a]
                esperado = leibniz(a)
                for metodo in metodos_para(n):
                    with self.subTest(n=n, a=a, metodo=metodo):
                        d = calcular_determinante(a, metodo)
                        if d["aplicable"]:
                            self.assertEqual(d["determinante"], esperado)
                            self.assertIsInstance(d["determinante"], F)
                self.assertEqual(a, original)
                # Gauss-Jordan sobre [A | I] recupera el mismo det(A) de sus pasos.
                self.assertEqual(calcular_inversa(a)["determinante"], esperado)
                self.assertEqual(calcular_inversa(a)["invertible"], esperado != 0)


class Entradas(unittest.TestCase):
    def test_matrices_invalidas_y_no_cuadradas(self):
        for a in ([], [[]], [[1, 2]], [[1], [1, 2]], [[True]], [[0.5]], [["1"]], [[1, 2, 3], [4, 5, 6]]):
            with self.subTest(a=a), self.assertRaises(ValueError):
                calcular_determinante(a)
        with self.assertRaisesRegex(ValueError, "Solo las matrices cuadradas tienen determinante: A es 2×3"):
            calcular_determinante([[1, 2, 3], [4, 5, 6]], "lu")

    def test_metodo_invalido(self):
        for metodo in ("otro", "Sarrus", None, [], {}):
            with self.subTest(metodo=metodo), self.assertRaisesRegex(ValueError, "método válido"):
                calcular_determinante([[1]], metodo)

    def test_seguridad_numerica(self):
        for metodo in ("reduccion", "lu", "cofactores"):
            with self.subTest(metodo=metodo), self.assertRaises(ValueError):
                calcular_determinante([[1 << BITS_MAXIMOS]], metodo)
        enorme = 1 << 7000
        for metodo in ("directo_2x2", "cofactores", "lu", "reduccion"):
            with self.subTest(metodo=metodo), self.assertRaises(ValueError):
                calcular_determinante([[enorme, 0], [0, enorme]], metodo)


class Presupuesto(unittest.TestCase):
    def test_cofactores_tiene_un_limite_estructural(self):
        a = [[1] * (ORDEN_MAXIMO_COFACTORES + 1) for _ in range(ORDEN_MAXIMO_COFACTORES + 1)]
        with self.assertRaisesRegex(ValueError, "factorial"):
            calcular_determinante(a, "cofactores")
        with self.assertRaisesRegex(ValueError, "factorial"):
            estimar_determinante(a, "cofactores")
        # LU y reducción no tienen ese límite.
        self.assertEqual(calcular_determinante(a, "reduccion")["determinante"], 0)

    def test_cofactores_crece_mas_rapido_que_reduccion(self):
        previo = None
        for n in range(2, ORDEN_MAXIMO_COFACTORES + 1):
            a = [[1] * n for _ in range(n)]
            actual = estimar_determinante(a, "cofactores")
            if previo:
                self.assertGreater(actual.calculo, previo.calculo)
                self.assertGreater(actual.procedimiento, n * previo.procedimiento / 2)
            previo = actual
        a = [[1] * 6 for _ in range(6)]
        self.assertGreater(estimar_determinante(a, "cofactores").procedimiento,
                           estimar_determinante(a, "reduccion").procedimiento)

    def test_la_cota_de_cofactores_cubre_el_arbol_real(self):
        rng = Random(6)
        for n in range(2, ORDEN_MAXIMO_COFACTORES + 1):
            a = [[rng.randint(1, 9) for _ in range(n)] for _ in range(n)]
            with self.subTest(n=n):
                self.assertGreaterEqual(estimar_determinante(a, "cofactores").pasos,
                                        nodos(calcular_determinante(a, "cofactores")))

    def test_6x6_de_enteros_no_pide_confirmacion_pero_numeros_grandes_si(self):
        pequena = [[(i * 7 + j * 3) % 10 for j in range(6)] for i in range(6)]
        self.assertLess(categoria(estimar_determinante(pequena, "cofactores")), Categoria.PESADA)
        grande = [[F(10 ** 90 + i + j, 10 ** 60 + 1) for j in range(6)] for i in range(6)]
        self.assertGreaterEqual(categoria(estimar_determinante(grande, "cofactores")), Categoria.PESADA)


if __name__ == "__main__":
    unittest.main()
