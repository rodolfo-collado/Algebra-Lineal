"""P26.7: inferencia pura del AST; nunca ejecuta las operaciones que estima."""

from fractions import Fraction
from unittest import TestCase
from unittest.mock import patch

from backend.expresiones_matriciales import evaluar
from backend.expresiones_matriciales.formas import Forma
from backend.presupuesto_computacional import Categoria, categoria, combinar_estimaciones, estimar_producto, perfil_numerico
from backend.presupuesto_expresiones import analizar_presupuesto


def matriz(filas, columnas, valor=1):
    return {"tipo": "matriz", "valor": [[valor] * columnas for _ in range(filas)]}


class PruebasPresupuestoExpresiones(TestCase):
    def analizar(self, texto, simbolos, nodo=None):
        with patch("backend.expresiones_matriciales.evaluador.resolver_operacion_matrices",
                   side_effect=AssertionError("La inferencia ejecutó el motor")):
            return analizar_presupuesto(texto, simbolos, nodo)

    def test_productos_en_el_orden_del_ast_y_composicion_total(self):
        cadena = {"A": matriz(2, 3), "B": matriz(3, 4), "C": matriz(4, 5), "D": matriz(5, 2)}
        casos = (
            ("AB", cadena, [(2, 3, 4)], Forma("matriz", 2, 4)),
            ("ABC", cadena, [(2, 3, 4), (2, 4, 5)], Forma("matriz", 2, 5)),
            ("ABCD", cadena, [(2, 3, 4), (2, 4, 5), (2, 5, 2)], Forma("matriz", 2, 2)),
            ("(AB)(CD)", cadena, [(2, 3, 4), (4, 5, 2), (2, 4, 2)], Forma("matriz", 2, 2)),
            ("A(B+C)", {"A": matriz(2, 3), "B": matriz(3, 4), "C": matriz(3, 4)}, [(2, 3, 4)], Forma("matriz", 2, 4)),
            ("(A+B)ᵀC", {"A": matriz(2, 3), "B": matriz(2, 3), "C": matriz(2, 4)}, [(3, 2, 4)], Forma("matriz", 3, 4)),
            ("Ax", {"A": matriz(2, 3), "x": {"tipo": "vector", "valor": [1, 1, 1]}}, [(2, 3, 1)], Forma("vector", 2)),
        )
        for texto, simbolos, dimensiones, forma in casos:
            with self.subTest(texto=texto):
                analisis = self.analizar(texto, simbolos)
                esperadas = tuple(estimar_producto(*dims, perfil=perfil_numerico([[1]])) for dims in dimensiones)
                self.assertEqual(analisis.formas, (forma,))
                self.assertEqual([e.dimensiones for e in analisis.productos], dimensiones)
                self.assertEqual(analisis.productos, esperadas)
                self.assertEqual(analisis.total, combinar_estimaciones(*esperadas, operacion="expresion_matricial"))

    def test_igualdad_combina_ambos_lados_incluso_si_no_son_comparables(self):
        analisis = self.analizar("AB = BA", {"A": matriz(2, 3), "B": matriz(3, 2)})
        self.assertEqual([e.dimensiones for e in analisis.productos], [(2, 3, 2), (3, 2, 3)])
        self.assertEqual(analisis.formas, (Forma("matriz", 2, 2), Forma("matriz", 3, 3)))
        self.assertEqual(analisis.total.partes, analisis.productos)

    def test_suma_resta_escalar_negacion_y_traspuesta_sin_producto(self):
        simbolos = {"A": matriz(2, 3), "B": matriz(2, 3), "x": {"tipo": "vector", "valor": [1, 2]},
                    "k": {"tipo": "escalar", "valor": 3}}
        for texto, forma in (("A+B", Forma("matriz", 2, 3)), ("2A-B", Forma("matriz", 2, 3)),
                             ("Aᵀ", Forma("matriz", 3, 2)), ("-A", Forma("matriz", 2, 3)),
                             ("xk", Forma("vector", 2)), ("kx", Forma("vector", 2)),
                             ("x-x", Forma("vector", 2)), ("k-2", Forma("escalar")), ("kA", Forma("matriz", 2, 3)),
                             ("Ak", Forma("matriz", 2, 3)), ("2k", Forma("escalar"))):
            with self.subTest(texto=texto):
                analisis = self.analizar(texto, simbolos)
                self.assertEqual(analisis.formas, (forma,))
                self.assertEqual(analisis.productos, ())
                self.assertIsNone(analisis.total)

    def test_perfil_de_valores_exactos_descendientes_y_literales_sin_texto(self):
        valor = Fraction(2**200, 3**100)
        simbolos = {"A": matriz(2, 3, valor), "B": matriz(3, 4), "k": {"tipo": "escalar", "valor": 2**210}}
        analisis = self.analizar("(kA)B", simbolos)
        perfil = perfil_numerico(simbolos["A"]["valor"], simbolos["B"]["valor"], [[2**210]])
        self.assertEqual(analisis.productos, (estimar_producto(2, 3, 4, perfil=perfil),))
        self.assertEqual(self.analizar("123AB", simbolos).productos,
                         (estimar_producto(2, 3, 4, perfil=perfil_numerico([[valor, 123, 1]])),))

    def test_los_errores_dimensionales_son_los_del_evaluador(self):
        simbolos = {"A": matriz(2, 3), "B": matriz(2, 2), "x": {"tipo": "vector", "valor": [1, 2]},
                    "y": {"tipo": "vector", "valor": [1, 2, 3]}}
        for texto in ("AB", "A+B", "Ax", "x+y", "xA", "xy", "xᵀ", "A+2", "AB=BA", "A=AB"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError) as real:
                    evaluar(texto, simbolos)
                with self.assertRaises(ValueError) as ligero:
                    self.analizar(texto, simbolos)
                self.assertEqual(str(ligero.exception), str(real.exception))

    def test_simbolicos_se_delegan_sin_presupuesto_numerico(self):
        simbolos = {"A": matriz(10, 10), "x": {"tipo": "vector_simbolico", "filas": 10},
                    "M": {"tipo": "matriz_desconocida", "filas": 10, "columnas": 10},
                    "b": {"tipo": "vector_lineal", "valor": ["x1"] * 10}}
        for texto in ("Ax", "Mx=b", "2x+b", "AAAAAx=b"):
            with self.subTest(texto=texto):
                analisis = self.analizar(texto, simbolos)
                self.assertTrue(analisis.simbolica)
                self.assertIsNone(analisis.total)
                self.assertEqual(analisis.productos, ())
        self.assertFalse(self.analizar("AA", simbolos).simbolica)  # operando simbólico sin usar

    def test_solo_la_parte_seleccionada_y_sus_descendientes(self):
        simbolos = {"A": matriz(2, 3), "B": matriz(3, 4), "C": matriz(4, 5), "D": matriz(5, 2)}
        self.assertEqual([e.dimensiones for e in self.analizar("(AB)(CD)", simbolos, "0.1").productos], [(4, 5, 2)])
        self.assertIsNone(self.analizar("(AB)(CD)", simbolos, "0.1.0").total)
        self.assertEqual([e.dimensiones for e in self.analizar("ABC=AB", simbolos, "izq:0.0").productos], [(2, 3, 4)])
        self.assertIsNone(self.analizar("AB=ABC", simbolos, "der:0.1").total)
        for nodo in ("0.9", "izq:0", "der:0.9", "0"):
            texto = "AB" if nodo == "izq:0" else "AB=AB" if nodo != "0.9" else "AB"
            with self.subTest(nodo=nodo), self.assertRaisesRegex(ValueError, "No existe la subexpresión"):
                self.analizar(texto, simbolos, nodo)
        # Una operación inválida o simbólica fuera del nodo solicitado no se ejecuta ni se valida dimensionalmente.
        self.assertIsNone(self.analizar("AB+A", {"A": matriz(2, 3), "B": matriz(2, 2)}, "0.1").total)

    def test_cadena_exterior_de_regresion_es_muy_pesada_sin_ejecutarse(self):
        analisis = self.analizar("(uv)" * 25, {"u": matriz(10, 1), "v": matriz(1, 10)})
        self.assertEqual(len(analisis.productos), 49)
        self.assertEqual(sum(e.dimensiones == (10, 1, 10) for e in analisis.productos), 25)
        self.assertEqual(sum(e.dimensiones == (10, 10, 10) for e in analisis.productos), 24)
        self.assertGreaterEqual(categoria(analisis.total), Categoria.PESADA)
