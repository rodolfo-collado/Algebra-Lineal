"""P26.6: la traspuesta como operación real del lenguaje de expresiones matriciales."""

from fractions import Fraction
from unittest import TestCase
from unittest.mock import patch

from backend.expresiones_matriciales import Comparacion, aplanar, analizar, analizar_entrada, estructura, evaluar
from backend.expresiones_matriciales.lexer import tokenizar
from backend.expresiones_matriciales.lineal import analizar_lineal
from backend.matrices import (
    multiplicar_escalar_matriz, multiplicar_matrices, multiplicar_matriz_vector, resolver_operacion_matrices,
    restar_matrices, sumar_matrices, trasponer_matriz,
)

NOMBRES = {"A", "B", "C", "D", "T", "x", "u", "k"}
A = [[1, 2, 3], [4, 5, 6]]
B = [[1, 0], [0, 1], [2, 2]]
C = [[1, -1, 0], [0, 2, "1/2"]]
SIMBOLOS = {
    "A": {"tipo": "matriz", "valor": A},
    "B": {"tipo": "matriz", "valor": B},
    "C": {"tipo": "matriz", "valor": [[Fraction(v) for v in fila] for fila in C]},
    "u": {"tipo": "vector", "valor": [1, 2]},
    "k": {"tipo": "escalar", "valor": Fraction(1, 2)},
}


def forma(texto, nombres=NOMBRES):
    return estructura(analizar(texto, nombres))


def T(nodo):
    return ("traspuesta", nodo)


def S(nombre):
    return ("simbolo", nombre)


class PruebasLexer(TestCase):
    def test_los_dos_alias_son_el_mismo_token(self):
        for texto, valor in (("Aᵀ", "ᵀ"), ("A^T", "^T")):
            with self.subTest(texto=texto):
                tokens = [(t.tipo, t.valor) for t in tokenizar(texto) if t.tipo != "fin"]
                self.assertEqual(tokens, [("nombre", "A"), ("traspuesta", valor)])

    def test_un_nombre_no_absorbe_la_traspuesta(self):
        # ᵀ es una letra para isalpha(): sin el corte, «ABᵀ» sería un solo nombre.
        tokens = [(t.tipo, t.valor) for t in tokenizar("ABᵀC") if t.tipo != "fin"]
        self.assertEqual(tokens, [("nombre", "AB"), ("traspuesta", "ᵀ"), ("nombre", "C")])
        tokens = [(t.tipo, t.valor) for t in tokenizar("A^TB") if t.tipo != "fin"]
        self.assertEqual(tokens, [("nombre", "A"), ("traspuesta", "^T"), ("nombre", "B")])

    def test_potencias_e_inversas_se_rechazan_sin_interpretarlas(self):
        for texto in ("A^2", "A^t", "A^", "A^ T", "(AB)^3", "A^x"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "no calcula potencias"):
                    tokenizar(texto)
        for texto in ("A^-1", "A^ -1", "(A + B)^-1"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "no se interpreta como inversa.*Matriz inversa"):
                    tokenizar(texto)


class PruebasParser(TestCase):
    def test_alias_y_aplicacion(self):
        casos = {
            "Aᵀ": T(S("A")),
            "A^T": T(S("A")),
            "(A + B)ᵀ": T(("suma", S("A"), S("B"))),
            "(A + B)^T": T(("suma", S("A"), S("B"))),
            "(AB)ᵀ": T(("producto", S("A"), S("B"))),
            "(AB)^T": T(("producto", S("A"), S("B"))),
            "Aᵀᵀ": T(T(S("A"))),
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(forma(texto), esperado)

    def test_precedencia_postfija(self):
        # ABᵀ significa A · (Bᵀ); para trasponer el producto hacen falta paréntesis.
        self.assertEqual(forma("ABᵀ"), ("producto", S("A"), T(S("B"))))
        self.assertEqual(forma("AB^T"), forma("ABᵀ"))
        self.assertEqual(forma("A*Bᵀ"), forma("ABᵀ"))
        self.assertNotEqual(forma("ABᵀ"), forma("(AB)ᵀ"))
        self.assertEqual(forma("ABCᵀ"), ("producto", ("producto", S("A"), S("B")), T(S("C"))))
        self.assertEqual(forma("AᵀB"), ("producto", T(S("A")), S("B")))
        self.assertEqual(forma("2Aᵀ"), ("producto", ("numero", Fraction(2)), T(S("A"))))
        self.assertEqual(forma("-Aᵀ"), ("negacion", T(S("A"))))
        self.assertEqual(forma("A + Bᵀ"), ("suma", S("A"), T(S("B"))))
        self.assertEqual(forma("2A + Bᵀ"), ("suma", ("producto", ("numero", Fraction(2)), S("A")), T(S("B"))))
        self.assertEqual(forma("A(B + C)ᵀ"), ("producto", S("A"), T(("suma", S("B"), S("C")))))

    def test_la_traspuesta_no_rompe_la_segmentacion_de_nombres(self):
        # Un símbolo llamado T sigue siendo un factor; ^T es la traspuesta.
        self.assertEqual(forma("AT"), ("producto", S("A"), S("T")))
        self.assertEqual(forma("A^T"), T(S("A")))
        self.assertEqual(forma("ATᵀ"), ("producto", S("A"), T(S("T"))))
        self.assertEqual(forma("Mᵀ", {"M", "M1"}), T(S("M")))
        self.assertEqual(forma("M1ᵀ", {"M", "M1"}), T(S("M1")))
        with self.assertRaisesRegex(ValueError, "Escribe \\*"):
            analizar("ABᵀ", {"A", "B", "AB"})
        self.assertEqual(forma("A*Bᵀ", {"A", "B", "AB"}), ("producto", S("A"), T(S("B"))))
        self.assertEqual(forma("ABᵀ", {"AB"}), T(S("AB")))

    def test_errores_de_sintaxis(self):
        for texto, mensaje in (("ᵀ", "Falta la matriz antes"), ("ᵀA", "Falta la matriz antes"),
                               ("A + ^T", "Falta la matriz antes de «\\^T»"), ("(ᵀ)", "Falta la matriz antes"),
                               ("A(", "paréntesis")):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, mensaje):
                    analizar(texto, NOMBRES)

    def test_el_texto_de_cada_nodo_usa_la_notacion_t_superindice(self):
        arbol = analizar("(A + B)^T C", NOMBRES)
        self.assertEqual(arbol.texto, "(A + B)ᵀ C")
        self.assertEqual(arbol.izquierda.texto, "(A + B)ᵀ")
        self.assertEqual(arbol.izquierda.operando.texto, "A + B")
        self.assertEqual(analizar_entrada("(AB)^T = B^TA^T", NOMBRES).texto, "(AB)ᵀ = BᵀAᵀ")


class PruebasRutas(TestCase):
    def ids(self, texto, simbolos=SIMBOLOS):
        return [paso.id for paso in aplanar(evaluar(texto, simbolos).principal)]

    def test_las_rutas_sin_traspuesta_no_cambian(self):
        ejemplo = {"A": {"tipo": "matriz", "valor": [[2, 5], [3, 1]]}, "u": {"tipo": "vector", "valor": [4, -1]}, "v": {"tipo": "vector", "valor": [-3, 5]}}
        self.assertEqual(self.ids("A(u + v)", ejemplo), ["0.0", "0.1.0", "0.1.1", "0.1", "0"])
        cuadradas = {nombre: {"tipo": "matriz", "valor": [[1, 2], [3, 4]]} for nombre in "ABCD"}
        self.assertEqual(self.ids("A(B + C) - 2D", cuadradas), ["0.0.0", "0.0.1.0", "0.0.1.1", "0.0.1", "0.0", "0.1.0", "0.1.1", "0.1", "0"])

    def test_la_traspuesta_es_un_nodo_con_ruta_propia(self):
        self.assertEqual(self.ids("Aᵀ"), ["0.0", "0"])
        self.assertEqual(self.ids("(A + A)ᵀ"), ["0.0.0", "0.0.1", "0.0", "0"])
        self.assertEqual(self.ids("ABᵀ", {**SIMBOLOS, "B": {"tipo": "matriz", "valor": [[1, 2, 3]]}}), ["0.0", "0.1.0", "0.1", "0"])
        self.assertEqual(self.ids("(AB)ᵀ"), ["0.0.0", "0.0.1", "0.0", "0"])

    def test_subexpresion_dentro_y_debajo_de_una_traspuesta(self):
        # Pedir una parte sigue funcionando con nodos de traspuesta en medio.
        cuadradas = {"A": {"tipo": "matriz", "valor": [[1, 2], [3, 4]]}, "B": {"tipo": "matriz", "valor": [[0, 1], [1, 0]]}}
        suma = evaluar("(A + B)ᵀ", cuadradas, "0.0").principal
        self.assertEqual((suma.texto, suma.resultado), ("A + B", [[1, 3], [4, 4]]))
        traspuesta = evaluar("A(A + B)ᵀ", cuadradas, "0.1").principal
        self.assertEqual((traspuesta.texto, traspuesta.resultado), ("(A + B)ᵀ", [[1, 4], [3, 4]]))
        self.assertEqual(evaluar("A(A + B)ᵀ", cuadradas, "0.1.0").principal.texto, "A + B")
        izquierda = evaluar("(AB)ᵀ = BᵀAᵀ", cuadradas, "der:0.0").principal
        self.assertEqual((izquierda.texto, izquierda.resultado), ("Bᵀ", [[0, 1], [1, 0]]))
        with self.assertRaisesRegex(ValueError, "No existe la subexpresión"):
            evaluar("Aᵀ", cuadradas, "0.1")


class PruebasEvaluacion(TestCase):
    def test_reutiliza_la_traspuesta_de_operaciones_con_matrices(self):
        with patch("backend.expresiones_matriciales.evaluador.resolver_operacion_matrices", wraps=resolver_operacion_matrices) as resolver:
            paso = evaluar("Aᵀ", SIMBOLOS).principal
        resolver.assert_called_once_with("traspuesta", [[1, 2, 3], [4, 5, 6]])
        self.assertEqual(paso.resultado, trasponer_matriz(A))
        self.assertEqual((paso.tipo, paso.filas, paso.columnas), ("matriz", 3, 2))
        self.assertEqual(paso.detalle, resolver_operacion_matrices("traspuesta", A))
        self.assertEqual(paso.detalle["pasos"][2][1]["origen"], (2, 3))

    def test_cuadrada_rectangular_fila_y_columna(self):
        for matriz in ([[1, 2], [3, 4]], [[1, 2, 3], [4, 5, 6]], [[1, 2, 3, 4]], [[1], [Fraction(-1, 2)], [3]]):
            with self.subTest(matriz=matriz):
                paso = evaluar("A^T", {"A": {"tipo": "matriz", "valor": matriz}}).principal
                self.assertEqual(paso.resultado, trasponer_matriz(matriz))
                self.assertEqual((paso.filas, paso.columnas), (len(matriz[0]), len(matriz)))

    def test_compuestas_contra_las_primitivas(self):
        ancha = [[1, 0, 2], [0, 1, 2]]
        self.assertEqual(evaluar("ABᵀ", {**SIMBOLOS, "B": {"tipo": "matriz", "valor": ancha}}).principal.resultado,
                         multiplicar_matrices(A, trasponer_matriz(ancha)))
        self.assertEqual(evaluar("(AB)ᵀ", SIMBOLOS).principal.resultado, trasponer_matriz(multiplicar_matrices(A, B)))
        self.assertEqual(evaluar("(A + C)ᵀ", SIMBOLOS).principal.resultado, trasponer_matriz(sumar_matrices(A, SIMBOLOS["C"]["valor"])))
        self.assertEqual(evaluar("2Aᵀ + B", SIMBOLOS).principal.resultado, sumar_matrices(multiplicar_escalar_matriz(2, trasponer_matriz(A)), B))
        self.assertEqual(evaluar("Aᵀu", SIMBOLOS).principal.resultado, multiplicar_matriz_vector(trasponer_matriz(A), [1, 2]))
        self.assertEqual(evaluar("Aᵀᵀ", SIMBOLOS).principal.resultado, A)
        self.assertEqual(evaluar("kAᵀ - Bᵀᵀ", {**SIMBOLOS, "B": {"tipo": "matriz", "valor": [[1, 1], [0, 0], [2, 2]]}}).principal.resultado,
                         restar_matrices(multiplicar_escalar_matriz(Fraction(1, 2), trasponer_matriz(A)), [[1, 1], [0, 0], [2, 2]]))

    def test_identidades_con_traspuestas(self):
        for texto in ("(AB)ᵀ = BᵀAᵀ", "(A + C)ᵀ = Aᵀ + Cᵀ", "(2A)ᵀ = 2Aᵀ", "Aᵀᵀ = A", "(A^T)^T = A"):
            with self.subTest(texto=texto):
                comparacion = evaluar(texto, SIMBOLOS)
                self.assertIsInstance(comparacion, Comparacion)
                self.assertTrue(comparacion.coincide, comparacion.mensaje)
        falsa = evaluar("(AB)ᵀ = AᵀBᵀ", {"A": {"tipo": "matriz", "valor": [[1, 2], [3, 4]]}, "B": {"tipo": "matriz", "valor": [[0, 1], [1, 0]]}})
        self.assertTrue(falsa.comparable)
        self.assertFalse(falsa.coincide)
        incomparable = evaluar("Aᵀ = A", SIMBOLOS)
        self.assertFalse(incomparable.comparable)
        self.assertIn("una matriz 3×2", incomparable.mensaje)

    def test_solo_se_trasponen_matrices_conocidas(self):
        simbolos = {
            **SIMBOLOS,
            "X": {"tipo": "matriz_desconocida", "filas": 2, "columnas": 2},
            "x": {"tipo": "vector_simbolico", "filas": 2},
            "b": {"tipo": "vector_lineal", "valor": ["x1", "x2"]},
        }
        for texto, fragmento in (
            ("uᵀ", "u es un vector de 2 componentes.*matriz de 1×2"),
            ("kᵀ", "k es un escalar"),
            ("2ᵀ", "2 es un escalar"),
            ("Xᵀ", "X es la matriz desconocida 2×2"),
            ("xᵀ", "x es un vector simbólico"),
            ("bᵀ", "b es un vector lineal"),
            ("(A + C)ᵀ + A", r"No se puede calcular \(A \+ C\)ᵀ \+ A"),
            ("AᵀB", "No se puede calcular AᵀB"),
        ):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, fragmento):
                    evaluar(texto, simbolos)

    def test_las_componentes_lineales_no_admiten_traspuesta(self):
        with self.assertRaisesRegex(ValueError, "no admite la traspuesta"):
            analizar_lineal("x1ᵀ + x2")
        with self.assertRaisesRegex(ValueError, "potencia"):
            analizar_lineal("x1^T")


class PruebasExpresionesDelBrief(TestCase):
    """Punto 9 de P26.6: las operaciones simples y compuestas siguen el mismo AST."""

    MATRICES = {nombre: {"tipo": "matriz", "valor": valor} for nombre, valor in {
        "A": [[1, 2], [3, 4]], "B": [[0, 1], [1, 0]], "C": [[2, 0], [0, 2]], "D": [[1, 1], [1, 1]],
    }.items()} | {"k": {"tipo": "escalar", "valor": Fraction(-3, 2)}, "x": {"tipo": "vector", "valor": [5, -1]}}

    def test_asociatividad_documentada(self):
        casos = {
            "A+B": ("suma", S("A"), S("B")),
            "A-B": ("resta", S("A"), S("B")),
            "kA": ("producto", S("k"), S("A")),
            "AB": ("producto", S("A"), S("B")),
            "Ax": ("producto", S("A"), S("x")),
            "A+B+C": ("suma", ("suma", S("A"), S("B")), S("C")),
            "A-B-C": ("resta", ("resta", S("A"), S("B")), S("C")),
            "ABC": ("producto", ("producto", S("A"), S("B")), S("C")),
            "A(B+C)": ("producto", S("A"), ("suma", S("B"), S("C"))),
            "2A-B": ("resta", ("producto", ("numero", Fraction(2)), S("A")), S("B")),
            "AB+C": ("suma", ("producto", S("A"), S("B")), S("C")),
            "A(B+C)-2D": ("resta", ("producto", S("A"), ("suma", S("B"), S("C"))), ("producto", ("numero", Fraction(2)), S("D"))),
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(forma(texto, set(self.MATRICES)), esperado)

    def test_resultados_contra_las_primitivas(self):
        a, b, c, d = (self.MATRICES[n]["valor"] for n in "ABCD")
        esperados = {
            "A+B": sumar_matrices(a, b),
            "A-B": restar_matrices(a, b),
            "kA": multiplicar_escalar_matriz(Fraction(-3, 2), a),
            "AB": multiplicar_matrices(a, b),
            "Ax": multiplicar_matriz_vector(a, [5, -1]),
            "A+B+C": sumar_matrices(sumar_matrices(a, b), c),
            "A-B-C": restar_matrices(restar_matrices(a, b), c),
            "ABC": multiplicar_matrices(multiplicar_matrices(a, b), c),
            "A(B+C)": multiplicar_matrices(a, sumar_matrices(b, c)),
            "2A-B": restar_matrices(multiplicar_escalar_matriz(2, a), b),
            "AB+C": sumar_matrices(multiplicar_matrices(a, b), c),
            "A(B+C)-2D": restar_matrices(multiplicar_matrices(a, sumar_matrices(b, c)), multiplicar_escalar_matriz(2, d)),
        }
        for texto, esperado in esperados.items():
            with self.subTest(texto=texto):
                self.assertEqual(evaluar(texto, self.MATRICES).principal.resultado, esperado)

    def test_la_cadena_de_productos_no_se_reordena(self):
        # Sin optimizar la parentización: ABC se evalúa como (AB)C, igual que el módulo anterior.
        rectangulares = {
            "A": {"tipo": "matriz", "valor": [[1, 2]]},
            "B": {"tipo": "matriz", "valor": [[1, 0, 2], [0, 1, 3]]},
            "C": {"tipo": "matriz", "valor": [[1, 2], [3, 4], [5, 6]]},
        }
        with patch("backend.expresiones_matriciales.evaluador.resolver_operacion_matrices", wraps=resolver_operacion_matrices) as resolver:
            paso = evaluar("ABC", rectangulares).principal
        self.assertEqual([llamada.args[1:] for llamada in resolver.call_args_list], [
            ([[1, 2]], [[1, 0, 2], [0, 1, 3]]),
            ([[1, 2, 8]], [[1, 2], [3, 4], [5, 6]]),
        ])
        self.assertEqual(paso.resultado, [[47, 58]])
