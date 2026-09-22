"""Motor de expresiones matriciales: tokens, árbol, tipos, evaluación y regresiones."""

import ast
from fractions import Fraction
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from backend.expresiones_matriciales import (
    Comparacion, Igualdad, aplanar, analizar, analizar_entrada, estructura, evaluar,
)
from backend.expresiones_matriciales.lexer import tokenizar
from backend.matrices import (
    multiplicar_escalar_matriz,
    multiplicar_matrices,
    multiplicar_matriz_vector,
    resolver_operacion_matrices,
    restar_matrices,
    sumar_matrices,
)
from backend.vectores import multiplicar_escalar, restar_vectores, sumar_vectores

A = [[2, 5], [3, 1]]
B = [[1, 0], [0, 1]]
C = [[0, 1], [1, 0]]
U = [4, -1]
V = [-3, 5]
NOMBRES = {"A", "B", "C", "D", "u", "v", "k"}
EJEMPLO = {
    "A": {"tipo": "matriz", "valor": A},
    "u": {"tipo": "vector", "valor": U},
    "v": {"tipo": "vector", "valor": V},
}
MATRICES = {
    "A": {"tipo": "matriz", "valor": A},
    "B": {"tipo": "matriz", "valor": B},
    "C": {"tipo": "matriz", "valor": C},
    "D": {"tipo": "matriz", "valor": [[1, 1], [1, 1]]},
    "k": {"tipo": "escalar", "valor": Fraction(1, 2)},
}


def pasos(expresion, simbolos=EJEMPLO, nodo=None):
    return aplanar(evaluar(expresion, simbolos, nodo).principal)


def operativos(expresion, simbolos=EJEMPLO, nodo=None):
    return [paso for paso in pasos(expresion, simbolos, nodo) if paso.operacion not in ("numero", "simbolo")]


class PruebasLexer(TestCase):
    def test_numeros_simbolos_y_operadores(self):
        tipos = [(token.tipo, token.valor) for token in tokenizar("2A + 1/2 - k") if token.tipo != "fin"]
        self.assertEqual(tipos, [
            ("numero", "2"), ("nombre", "A"), ("mas", "+"), ("numero", "1/2"), ("menos", "-"), ("nombre", "k"),
        ])

    def test_fraccion_es_un_solo_token_y_el_signo_no(self):
        tokens = [token for token in tokenizar("-3/4") if token.tipo != "fin"]
        self.assertEqual([(token.tipo, token.valor) for token in tokens], [("menos", "-"), ("numero", "3/4")])

    def test_un_igual_es_un_token_y_no_rompe_el_resto(self):
        tipos = [(token.tipo, token.valor) for token in tokenizar("-3/4 + 2.5A = 1/2") if token.tipo != "fin"]
        self.assertEqual(tipos, [
            ("menos", "-"), ("numero", "3/4"), ("mas", "+"), ("numero", "2.5"), ("nombre", "A"),
            ("igual", "="), ("numero", "1/2"),
        ])
        self.assertEqual(sum(token.tipo == "igual" for token in tokenizar("A = B = C")), 2)

    def test_rechaza_relacionales_division_suelta_y_caracteres_ajenos(self):
        for texto in ("A == B", "A != B", "A < B", "A > B", "A <= B", "A >= B", "1 / 2", "A$B"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, "no forma parte|fracciones"):
                    tokenizar(texto)


class PruebasParser(TestCase):
    def test_precedencia_y_parentesis(self):
        self.assertEqual(estructura(analizar("A + BC", NOMBRES)), ("suma", ("simbolo", "A"), ("producto", ("simbolo", "B"), ("simbolo", "C"))))
        self.assertEqual(
            estructura(analizar("(A + B)C", NOMBRES)),
            ("producto", ("suma", ("simbolo", "A"), ("simbolo", "B")), ("simbolo", "C")),
        )
        self.assertEqual(
            estructura(analizar("A - B - C", NOMBRES)),
            ("resta", ("resta", ("simbolo", "A"), ("simbolo", "B")), ("simbolo", "C")),
        )

    def test_implicita_y_asterisco_producen_el_mismo_arbol(self):
        for implicita, explicita in (("2A", "2 * A"), ("AB", "A*B"), ("Au", "A * u"), ("A(u + v)", "A * (u + v)")):
            with self.subTest(implicita=implicita):
                self.assertEqual(estructura(analizar(implicita, NOMBRES)), estructura(analizar(explicita, NOMBRES)))

    def test_menos_unario_y_fraccion(self):
        self.assertEqual(estructura(analizar("-3B", NOMBRES)), ("producto", ("negacion", ("numero", Fraction(3))), ("simbolo", "B")))
        self.assertEqual(analizar("1/2", set()).valor, Fraction(1, 2))
        self.assertEqual(analizar("-3/4", set()).operando.valor, Fraction(3, 4))

    def test_sintaxis_invalida(self):
        for texto in ("", "A + * B", "A(", "(A+B", "()", "*A"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    analizar(texto, NOMBRES)

    def test_simbolo_inexistente(self):
        with self.assertRaisesRegex(ValueError, "El símbolo Z no está definido"):
            analizar("A + Z", {"A"})

    def test_multiplicacion_implicita_ambigua(self):
        with self.assertRaisesRegex(ValueError, "Escribe \\*"):
            analizar("AB", {"A", "B", "AB"})
        self.assertEqual(estructura(analizar("A*B", {"A", "B", "AB"})), ("producto", ("simbolo", "A"), ("simbolo", "B")))
        self.assertEqual(estructura(analizar("AB", {"AB"})), ("simbolo", "AB"))


class PruebasAST(TestCase):
    def test_el_arbol_conserva_hijos_y_el_texto_de_cada_subexpresion(self):
        arbol = analizar("A(u + v)", EJEMPLO)
        self.assertEqual(arbol.operacion, "producto")
        self.assertEqual(arbol.texto, "A(u + v)")
        self.assertEqual(arbol.derecha.texto, "u + v")
        self.assertEqual(tuple(hijo.nombre for hijo in arbol.derecha.hijos()), ("u", "v"))

    def test_las_rutas_son_estables(self):
        ids = [paso.id for paso in pasos("A(u + v)")]
        self.assertEqual(ids, ["0.0", "0.1.0", "0.1.1", "0.1", "0"])


class PruebasEvaluacion(TestCase):
    def test_ejemplo_obligatorio(self):
        self.assertEqual(
            [(paso.texto, paso.resultado) for paso in operativos("A(u + v)")],
            [("u + v", [1, 4]), ("A(u + v)", [22, 7])],
        )
        self.assertEqual(
            [(paso.texto, paso.resultado) for paso in operativos("Au + Av")],
            [("Au", [3, 11]), ("Av", [19, -4]), ("Au + Av", [22, 7])],
        )

    def test_la_misma_subexpresion_se_puede_pedir_sola(self):
        parcial = evaluar("A(B + C) - 2D", MATRICES, "0.0.1")
        self.assertEqual(parcial.principal.texto, "B + C")
        self.assertEqual(parcial.principal.id, "0.0.1")
        self.assertEqual(set(parcial.por_id()), {"0.0.1", "0.0.1.0", "0.0.1.1"})

    def test_casos_anidados_escalares_y_mixtos(self):
        self.assertEqual(evaluar("A + (B + C)", MATRICES).principal.resultado, sumar_matrices(A, sumar_matrices(B, C)))
        self.assertEqual(evaluar("A(BC)", MATRICES).principal.resultado, multiplicar_matrices(A, multiplicar_matrices(B, C)))
        self.assertEqual(evaluar("(A + B)C", MATRICES).principal.resultado, multiplicar_matrices(sumar_matrices(A, B), C))
        self.assertEqual(evaluar("2A", MATRICES).principal.resultado, multiplicar_escalar_matriz(2, A))
        self.assertEqual(evaluar("-3B", MATRICES).principal.resultado, multiplicar_escalar_matriz(-3, B))
        self.assertEqual(evaluar("2(A + B)", MATRICES).principal.resultado, multiplicar_escalar_matriz(2, sumar_matrices(A, B)))
        self.assertEqual(evaluar("A(u + v) - Au", EJEMPLO).principal.resultado, restar_vectores([22, 7], [3, 11]))
        self.assertEqual(evaluar("A * (u + v)", EJEMPLO).principal.resultado, evaluar("A(u + v)", EJEMPLO).principal.resultado)

    def test_fracciones_exactas(self):
        simbolos = {"A": {"tipo": "matriz", "valor": [[Fraction(1, 2), 2]]}, "k": {"tipo": "escalar", "valor": Fraction(-3, 4)}}
        self.assertEqual(evaluar("k*A", simbolos).principal.resultado, [[Fraction(-3, 8), Fraction(-3, 2)]])
        self.assertEqual(evaluar("(1/2)*A", {"A": simbolos["A"]}).principal.resultado[0][0], Fraction(1, 4))


class PruebasTiposYDimensiones(TestCase):
    def test_suma_de_tipos_distintos_y_producto_no_definido(self):
        with self.assertRaisesRegex(ValueError, "Solo se pueden sumar o restar"):
            evaluar("A + u", EJEMPLO)
        with self.assertRaisesRegex(ValueError, "producto punto no se infiere"):
            evaluar("u*v", EJEMPLO)
        with self.assertRaisesRegex(ValueError, "vector por una matriz"):
            evaluar("u*A", EJEMPLO)

    def test_el_error_senala_la_subexpresion_que_falla(self):
        ancho = {"A": {"tipo": "matriz", "valor": [[1, 0], [0, 1]]}, "B": {"tipo": "matriz", "valor": [[1, 2], [3, 4]]}, "C": {"tipo": "matriz", "valor": [[1, 2, 3]]}}
        with self.assertRaisesRegex(ValueError, r"No se puede calcular B \+ C: B es 2×2 y C es 1×3"):
            evaluar("A(B + C)", ancho)
        incompatible = {
            "A": {"tipo": "matriz", "valor": [[1, 2, 3], [4, 5, 6]]},
            "B": {"tipo": "matriz", "valor": [[1, 0], [0, 1], [0, 0], [0, 0]]},
            "C": {"tipo": "matriz", "valor": [[0, 1], [1, 0], [0, 0], [1, 0]]},
        }
        with self.assertRaisesRegex(ValueError, r"B \+ C es 4×2"):
            evaluar("A(B + C)", incompatible)

    def test_ruta_inexistente(self):
        with self.assertRaisesRegex(ValueError, "No existe la subexpresión"):
            evaluar("A + B", MATRICES, "9")


class PruebasProcedimiento(TestCase):
    def test_reutiliza_el_procedimiento_de_matriz_por_vector_y_de_matrices(self):
        producto = operativos("A(u + v)")[-1]
        esperado = resolver_operacion_matrices("matriz_vector", A, vector=[1, 4])
        self.assertEqual(producto.detalle["operacion"], "matriz_vector")
        self.assertEqual(producto.detalle["pasos"], esperado["pasos"])
        self.assertEqual(producto.detalle["columnas"], esperado["columnas"])
        suma = evaluar("B + C", MATRICES).principal
        self.assertEqual(suma.detalle["pasos"], resolver_operacion_matrices("suma", B, C)["pasos"])

    def test_la_suma_de_vectores_no_recalcula_el_resultado(self):
        with patch("backend.expresiones_matriciales.evaluador.sumar_vectores", wraps=sumar_vectores) as suma:
            resultado = evaluar("u + v", EJEMPLO).principal.resultado
        self.assertEqual(resultado, [1, 4])
        self.assertEqual(suma.call_count, 1)


class PruebasRegresion(TestCase):
    def test_coincide_con_las_primitivas(self):
        casos = (
            ("A + B", sumar_matrices, (A, B), "backend.matrices.sumar_matrices"),
            ("A - B", restar_matrices, (A, B), "backend.matrices.restar_matrices"),
            ("2*A", multiplicar_escalar_matriz, (2, A), "backend.matrices.multiplicar_escalar_matriz"),
            ("AB", multiplicar_matrices, (A, B), "backend.matrices.multiplicar_matrices"),
            ("Au", multiplicar_matriz_vector, (A, U), "backend.matrices.multiplicar_matriz_vector"),
        )
        for expresion, primitiva, argumentos, ruta in casos:
            with self.subTest(expresion=expresion):
                with patch(ruta, wraps=primitiva) as envuelta:
                    obtenido = evaluar(expresion, {**MATRICES, "u": EJEMPLO["u"]}).principal.resultado
                self.assertEqual(obtenido, primitiva(*argumentos))
                envuelta.assert_called()

    def test_el_escalar_por_vector_usa_la_primitiva_de_vectores(self):
        with patch("backend.expresiones_matriciales.evaluador.multiplicar_escalar", wraps=multiplicar_escalar) as producto:
            self.assertEqual(evaluar("2u", {"u": EJEMPLO["u"]}).principal.resultado, [8, -2])
        producto.assert_called()

    def test_el_modulo_no_evalua_texto_ni_importa_algebra_externa(self):
        raiz = Path(__file__).resolve().parents[1] / "backend" / "expresiones_matriciales"
        for archivo in raiz.glob("*.py"):
            arbol = ast.parse(archivo.read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                    self.assertNotIn(nodo.func.id, {"eval", "exec"})
                if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                    modulos = [alias.name for alias in nodo.names] if isinstance(nodo, ast.Import) else [nodo.module or ""]
                    for modulo in modulos:
                        self.assertFalse(modulo.startswith(("numpy", "sympy", "scipy")))


def visibles(paso):
    return [(item.texto, item.resultado) for item in aplanar(paso) if item.operacion not in ("numero", "simbolo")]


class PruebasIgualdad(TestCase):
    def test_dos_arboles_independientes_con_la_precedencia_de_cada_lado(self):
        entrada = analizar_entrada("A + BC = (A + B)C", NOMBRES)
        self.assertIsInstance(entrada, Igualdad)
        self.assertFalse(hasattr(entrada, "operacion"))
        self.assertEqual(estructura(entrada), (
            "igualdad",
            ("suma", ("simbolo", "A"), ("producto", ("simbolo", "B"), ("simbolo", "C"))),
            ("producto", ("suma", ("simbolo", "A"), ("simbolo", "B")), ("simbolo", "C")),
        ))
        with self.assertRaisesRegex(ValueError, "no es una operación"):
            analizar("A = B", NOMBRES)

    def test_ejemplo_obligatorio(self):
        comparacion = evaluar("A(u + v) = Au + Av", EJEMPLO)
        self.assertIsInstance(comparacion, Comparacion)
        self.assertEqual(visibles(comparacion.izquierda), [("u + v", [1, 4]), ("A(u + v)", [22, 7])])
        self.assertEqual(visibles(comparacion.derecha), [("Au", [3, 11]), ("Av", [19, -4]), ("Au + Av", [22, 7])])
        self.assertTrue(comparacion.comparable)
        self.assertTrue(comparacion.coincide)
        self.assertEqual(comparacion.tipo, "vector")
        self.assertIn("[22, 7]", comparacion.mensaje)
        self.assertNotIn("demostr", comparacion.mensaje)
        producto = aplanar(comparacion.izquierda)[-1]
        esperado = resolver_operacion_matrices("matriz_vector", A, vector=[1, 4])
        self.assertEqual(producto.detalle["pasos"], esperado["pasos"])
        self.assertEqual(producto.detalle["columnas"], esperado["columnas"])
        au = next(paso for paso in aplanar(comparacion.derecha) if paso.texto == "Au")
        self.assertEqual(au.detalle["operacion"], "matriz_vector")

    def test_identidades_con_valores_concretos(self):
        casos = (
            ("2(A + B) = 2A + 2B", MATRICES),
            ("A(B + C) = AB + AC", MATRICES),
            ("A(u - v) = Au - Av", EJEMPLO),
            ("A * (u + v) = A*u + A*v", EJEMPLO),
            ("(1/2)A + (1/2)A = A", MATRICES),
            ("(1/3)A + (2/3)A = A", {"A": MATRICES["A"]}),
            ("(1/3) + (1/3) + (1/3) = 1", {}),
            ("0.5 = 1/2", {}),
        )
        for texto, simbolos in casos:
            with self.subTest(texto=texto):
                comparacion = evaluar(texto, simbolos)
                self.assertTrue(comparacion.coincide, comparacion.mensaje)
                self.assertEqual(comparacion.izquierda.resultado, comparacion.derecha.resultado)

    def test_igualdades_falsas_siguen_siendo_un_resultado(self):
        distinta = evaluar("A + B = A - B", MATRICES)
        self.assertTrue(distinta.comparable)
        self.assertFalse(distinta.coincide)
        self.assertNotEqual(distinta.izquierda.resultado, distinta.derecha.resultado)
        self.assertIn("diferentes", distinta.mensaje)
        vectores = evaluar("Au = Av", EJEMPLO)
        self.assertEqual(vectores.izquierda.resultado, [3, 11])
        self.assertEqual(vectores.derecha.resultado, [19, -4])
        self.assertFalse(vectores.coincide)

    def test_escalares_vectores_y_matrices_comparables(self):
        self.assertTrue(evaluar("1/2 + 1/2 = 1", {}).coincide)
        self.assertFalse(evaluar("1/3 = 0.3333", {}).coincide)
        self.assertTrue(evaluar("u = u", EJEMPLO).coincide)
        self.assertFalse(evaluar("u = v", EJEMPLO).coincide)
        self.assertTrue(evaluar("A = A", MATRICES).coincide)
        self.assertFalse(evaluar("A = B", MATRICES).coincide)

    def test_tipos_o_dimensiones_distintas_no_son_falso(self):
        casos = (
            ("A = u", EJEMPLO, "una matriz 2×2", "un vector de 2 componentes"),
            ("k = A", MATRICES, "un escalar", "una matriz 2×2"),
            ("u = w", {"u": EJEMPLO["u"], "w": {"tipo": "vector", "valor": [1, 2, 3]}}, "2 componentes", "3 componentes"),
            (
                "P = Q",
                {"P": {"tipo": "matriz", "valor": [[1, 2, 3], [4, 5, 6]]}, "Q": {"tipo": "matriz", "valor": [[1, 2], [3, 4], [5, 6]]}},
                "una matriz 2×3",
                "una matriz 3×2",
            ),
        )
        for texto, simbolos, izq, der in casos:
            with self.subTest(texto=texto):
                comparacion = evaluar(texto, simbolos)
                self.assertFalse(comparacion.comparable)
                self.assertIsNone(comparacion.coincide)
                self.assertIn("No se pueden comparar ambos lados", comparacion.mensaje)
                self.assertIn(izq, comparacion.mensaje)
                self.assertIn(der, comparacion.mensaje)
                self.assertNotIn("Falso", comparacion.mensaje)

    def test_el_error_indica_el_lado_y_la_subexpresion(self):
        ancho = {
            "A": {"tipo": "matriz", "valor": [[1, 0], [0, 1]]},
            "B": {"tipo": "matriz", "valor": [[1, 2], [3, 4]]},
            "C": {"tipo": "matriz", "valor": [[1, 2, 3]]},
            "D": {"tipo": "matriz", "valor": [[1, 0], [0, 1]]},
        }
        with self.assertRaisesRegex(ValueError, r"En el lado izquierdo: No se puede calcular B \+ C"):
            evaluar("A(B + C) = D", ancho)
        with self.assertRaisesRegex(ValueError, r"En el lado derecho: No se puede calcular B \+ C"):
            evaluar("D = A(B + C)", ancho)
        with self.assertRaisesRegex(ValueError, r"En el lado derecho: El símbolo Z no está definido"):
            evaluar("A = Z", {"A": MATRICES["A"]})
        with self.assertRaisesRegex(ValueError, r"\AEl símbolo Z no está definido"):
            evaluar("A + Z", {"A": MATRICES["A"]})

    def test_sintaxis_invalida(self):
        casos = (
            ("A =", "lado derecho"),
            ("= A", "lado izquierdo"),
            ("A = B = C", "una igualdad"),
            ("A == B", "=="),
            ("A + = B", "lado izquierdo"),
            ("(A", "paréntesis"),
            ("A)", "paréntesis"),
            ("(A = B", "lado izquierdo"),
            ("A = (B", "lado derecho"),
        )
        for texto, fragmento in casos:
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, fragmento):
                    analizar_entrada(texto, NOMBRES)

    def test_rutas_de_cada_lado_y_evaluacion_parcial(self):
        comparacion = evaluar("A(u + v) = Au + Av", EJEMPLO)
        izquierdas = [paso.id for paso in aplanar(comparacion.izquierda)]
        derechas = [paso.id for paso in aplanar(comparacion.derecha)]
        self.assertTrue(all(ruta.startswith("izq:") for ruta in izquierdas))
        self.assertTrue(all(ruta.startswith("der:") for ruta in derechas))
        self.assertFalse(set(izquierdas) & set(derechas))
        self.assertIn("izq:0.1", izquierdas)
        self.assertIn("der:0.0", derechas)
        suma = evaluar("A(u + v) = Au + Av", EJEMPLO, "izq:0.1")
        self.assertEqual(suma.principal.id, "izq:0.1")
        self.assertEqual(suma.principal.resultado, [1, 4])
        self.assertEqual(evaluar("A(u + v) = Au + Av", EJEMPLO, "der:0.0").principal.resultado, [3, 11])
        self.assertEqual(evaluar("A(u + v) = Au + Av", EJEMPLO, "der:0.1").principal.resultado, [19, -4])
        self.assertEqual(evaluar("A(u + v) = Au + Av", EJEMPLO, "der:0").principal.resultado, [22, 7])
        for ruta in ("0.1", "izq:9", "der:0.1.9", "izq:", "medio:0"):
            with self.subTest(ruta=ruta):
                with self.assertRaisesRegex(ValueError, "No existe la subexpresión"):
                    evaluar("A(u + v) = Au + Av", EJEMPLO, ruta)

    def test_las_expresiones_de_p20_siguen_sin_igualdad(self):
        simbolos = {**MATRICES, "u": EJEMPLO["u"], "v": EJEMPLO["v"]}
        for texto in ("A + B", "A - B", "AB", "Au", "A(u + v)", "2A", "-3B", "A * B"):
            with self.subTest(texto=texto):
                resultado = evaluar(texto, simbolos)
                self.assertNotIsInstance(resultado, Comparacion)
                self.assertEqual(resultado.principal.id, "0")
