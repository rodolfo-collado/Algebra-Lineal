"""Contrato matemático y seguridad del primer incremento de Conjuntos."""

from fractions import Fraction
import unittest

from backend.conjuntos.literales import analizar_literal, analizar_definicion
from backend.conjuntos.parser import analizar_relacion, renombrar_referencias
from backend.conjuntos.evaluador import evaluar_relacion
from backend.conjuntos.modelo import Conjunto, presentar
from backend.conjuntos.presupuesto import Presupuesto
from backend.operandos import CELDAS_MAXIMAS, OPERANDOS_MAXIMOS


class ConjuntosTests(unittest.TestCase):
    def test_aceptacion(self):
        entorno = {"A": analizar_literal("{1, 2}"), "B": analizar_literal("{2, {1, 2}}")}
        for texto, esperado in (
            ("2 ∈ A", True), ("3 ∈ A", False), ("A ∈ B", True), ("A ⊆ B", False),
            ("{2} ⊆ B", True), ("A ⊂ A", False), ("∅ ⊆ A", True), ("∅ ∈ A", False),
            ("{1, 2} = {2, 1, 1}", True), ("{1, 2} ≠ {2, 1}", False),
            ("3 ∉ A", True), ("{} ⊂ A", True), ("{} ⊂ ∅", False),
            ('"1" ∈ {1}', False), ('"∈" ∈ {"∈"}', True),
            ("(({1})) ⊆ ({1, 2})", True), ("1/2 = 0.5", True),
        ):
            with self.subTest(texto=texto):
                self.assertIs(evaluar_relacion(analizar_relacion(texto), entorno).valor, esperado)

    def test_modelo_inmutable_y_tipos(self):
        valor = analizar_literal('{1, 1.0, 2/2, "1", {1}, {{1}}, ∅, {}}')
        self.assertEqual(len(valor.elementos), 5)
        self.assertIn(Fraction(1), valor.elementos)
        self.assertIn("1", valor.elementos)
        self.assertNotEqual(analizar_literal("{1}"), analizar_literal("{{1}}"))
        self.assertEqual(hash(analizar_literal("{1,2}")), hash(analizar_literal("{2,1}")))
        self.assertIsInstance(valor, Conjunto)

    def test_definicion_y_nombres(self):
        for nombre in ("A", "B", "S", "T", "Conjunto1", "Grupo_2"):
            self.assertEqual(analizar_definicion(f"{nombre} = {{1}}"), (nombre, analizar_literal("{1}")))
        for nombre in ("", "1A", "A B", "__import__", "True", "in", "union", "par", "intervalo"):
            with self.subTest(nombre=nombre), self.assertRaises(ValueError):
                analizar_definicion(f"{nombre} = {{}}")

    def test_presentacion_se_puede_volver_a_leer(self):
        for texto in ('{-.5, - 1 / 2, "a,b", "una \\"cita\\"", {∅}}', '{"∈", "A", "\\\\", "\\u00f1"}',
                      '{0, {}, {{}}, {{1, 2}, {2, 1}}}'):
            with self.subTest(texto=texto):
                valor = analizar_literal(texto)
                self.assertEqual(analizar_literal(presentar(valor)), valor)

    def test_unicode_incompleto_y_agrupacion_excesiva(self):
        with self.assertRaises(ValueError):
            analizar_literal('{"\\ud800"}')
        with self.assertRaises(ValueError):
            analizar_relacion("(" * OPERANDOS_MAXIMOS + "A" + ")" * OPERANDOS_MAXIMOS + " = A")

    def test_renombrar_solo_referencias(self):
        self.assertEqual(renombrar_referencias('A ∈ B', {"A": "S"}), 'S ∈ B')
        self.assertEqual(renombrar_referencias('"A" ∈ {"A"}', {"A": "S"}), '"A" ∈ {"A"}')
        self.assertEqual(renombrar_referencias('A = AA', {"A": "B", "AA": "A"}), 'B = A')
        with self.assertRaises(ValueError):
            renombrar_referencias("A = A", {"A": "S" * 6000})

    def test_errores_y_entradas_maliciosas(self):
        for texto in ("{", "{1,}", "{1 2}", "{A}", "{x for x in A}", "{1|2}",
                      '{"sin cerrar}', "{1e999999}", "{1/0}", "{1_000}", "{1;2}",
                      "{__import__('os').system('echo ataque')}"):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                analizar_literal(texto)
        for texto in ("A", "A = B = C", "A ∪ B", "(1,2) ∈ A", "A ∈", "A == B", "A <= B", "A[0] = 1"):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                analizar_relacion(texto)
        for texto in ("1 ⊆ {1}", "{1} ⊂ 1", "1 ∈ 2", "{} = 1", "Z ∈ {}"):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                evaluar_relacion(analizar_relacion(texto), {})

    def test_presupuesto_antes_de_normalizar(self):
        for texto in ("{" + ",".join(["1"] * CELDAS_MAXIMAS) + "}",
                      "{" * (OPERANDOS_MAXIMOS + 1) + "}" * (OPERANDOS_MAXIMOS + 1),
                      "{" + "1" * 101 + "}", " " * 10001):
            with self.subTest(longitud=len(texto)), self.assertRaises(ValueError):
                analizar_literal(texto)
        presupuesto = Presupuesto()
        analizar_literal("{" + ",".join(map(str, range(450))) + "}", presupuesto=presupuesto)
        with self.assertRaises(ValueError):
            analizar_literal("{" + ",".join(map(str, range(450))) + "}", presupuesto=presupuesto)


if __name__ == "__main__":
    unittest.main()
