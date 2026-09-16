"""Operaciones con vectores y combinación lineal (P12): matemática pura del backend."""

import unittest
from fractions import Fraction as F
from unittest.mock import patch

from backend import vectores
from backend.expresiones import crear_expresion, formatear_ecuacion, formatear_expresion
from backend.sistemas import (
    INCONSISTENTE,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
    resolver_sistema_gauss,
    resolver_sistema_gauss_jordan,
)
from backend.vectores import (
    combinar,
    evaluar_combinacion_lineal,
    matriz_de_combinacion,
    multiplicar_escalar,
    restar_vectores,
    sumar_vectores,
    validar_combinacion,
    validar_misma_dimension,
    validar_vector,
)


class PruebasValidacion(unittest.TestCase):
    def test_un_vector_necesita_componentes_numericas(self):
        self.assertEqual(validar_vector([1, F(1, 2)]), (True, ""))
        self.assertEqual(validar_vector([], "u"), (False, "El vector u no tiene componentes."))
        self.assertEqual(validar_vector("1,2"), (False, "El vector debe ser una lista de componentes."))
        self.assertEqual(
            validar_vector([1, "2"], "v"),
            (False, "El vector v tiene una componente que no es un número."),
        )
        self.assertFalse(validar_vector([True, 1])[0])

    def test_misma_dimension(self):
        self.assertEqual(validar_misma_dimension(([1, 2], [3, 4]), ("u", "v")), (True, ""))
        es_valida, mensaje = validar_misma_dimension(([1, 2], [1, 2, 3]), ("u", "v"), "sumar")
        self.assertFalse(es_valida)
        self.assertEqual(
            mensaje,
            "No se pueden sumar vectores de distinta dimensión: u tiene 2, v tiene 3 componentes.",
        )

    def test_combinacion_exige_generadores_y_misma_dimension(self):
        self.assertFalse(validar_combinacion([], [1, 2])[0])
        self.assertIn("al menos un vector generador", validar_combinacion([], [1, 2])[1])
        es_valida, mensaje = validar_combinacion([[1, 2], [1, 2, 3]], [4, 5])
        self.assertFalse(es_valida)
        self.assertIn("v1 tiene 2, v2 tiene 3, b tiene 2 componentes", mensaje)


class PruebasOperaciones(unittest.TestCase):
    def test_suma_componente_a_componente(self):
        self.assertEqual(sumar_vectores([1, 2], [3, 4]), [4, 6])
        self.assertEqual(sumar_vectores([1, 2, 3], [4, 5, 6]), [5, 7, 9])
        self.assertEqual(sumar_vectores([F(1, 2), F(2, 3)], [F(1, 2), F(1, 3)]), [1, 1])
        self.assertEqual(sumar_vectores([F(1, 3)], [F(1, 3)]), [F(2, 3)])

    def test_suma_devuelve_fracciones_exactas_y_no_modifica_las_entradas(self):
        u, v = [1, 2], [3, 4]
        resultado = sumar_vectores(u, v)
        self.assertTrue(all(isinstance(valor, F) for valor in resultado))
        self.assertEqual((u, v), ([1, 2], [3, 4]))

    def test_resta_componente_a_componente(self):
        self.assertEqual(restar_vectores([4, 6], [1, 2]), [3, 4])
        self.assertEqual(restar_vectores([5, 7, 9], [1, 2, 3]), [4, 5, 6])
        self.assertEqual(restar_vectores([F(1, 2), 1], [F(1, 3), 2]), [F(1, 6), -1])

    def test_escalar_multiplica_cada_componente(self):
        self.assertEqual(multiplicar_escalar(3, [1, -2, 4]), [3, -6, 12])
        self.assertEqual(multiplicar_escalar(0, [1, 2, 3]), [0, 0, 0])
        self.assertEqual(multiplicar_escalar(F(1, 2), [1, F(1, 3), -4]), [F(1, 2), F(1, 6), -2])
        self.assertEqual(multiplicar_escalar(-1, [F(2, 5)]), [F(-2, 5)])

    def test_dimension_arbitraria(self):
        u = list(range(1, 8))
        self.assertEqual(sumar_vectores(u, u), [2 * valor for valor in u])
        self.assertEqual(restar_vectores(u, u), [0] * 7)
        self.assertEqual(multiplicar_escalar(2, [1]), [2])

    def test_dimensiones_distintas_se_rechazan_con_mensaje(self):
        for operacion, accion in ((sumar_vectores, "sumar"), (restar_vectores, "restar")):
            with self.subTest(operacion=operacion.__name__):
                with self.assertRaises(ValueError) as contexto:
                    operacion([1, 2], [1, 2, 3])
                self.assertIn(f"No se pueden {accion} vectores de distinta dimensión", str(contexto.exception))

    def test_entradas_invalidas(self):
        with self.assertRaises(ValueError):
            sumar_vectores([], [])
        with self.assertRaises(ValueError):
            multiplicar_escalar("3", [1, 2])
        with self.assertRaises(ValueError):
            multiplicar_escalar(2, [])


class PruebasMatrizDeCombinacion(unittest.TestCase):
    def test_cada_generador_es_una_columna_y_el_objetivo_la_aumentada(self):
        matriz = matriz_de_combinacion([[1, 2], [3, 4]], [5, 6])
        self.assertEqual(matriz, [[1, 3, 5], [2, 4, 6]])
        self.assertTrue(all(isinstance(valor, F) for fila in matriz for valor in fila))

    def test_un_sistema_con_una_ecuacion_por_componente(self):
        matriz = matriz_de_combinacion([[1, 0, 2], [0, 1, 3], [1, 1, 0]], [4, 5, 6])
        self.assertEqual(matriz, [[1, 0, 1, 4], [0, 1, 1, 5], [2, 3, 0, 6]])
        self.assertEqual(len(matriz), 3)
        self.assertEqual(len(matriz[0]), 4)

    def test_rechaza_dimensiones_incompatibles_antes_de_resolver(self):
        with self.assertRaises(ValueError) as contexto:
            matriz_de_combinacion([[1, 2], [1, 2, 3]], [4, 5])
        self.assertIn("distinta dimensión", str(contexto.exception))
        with self.assertRaises(ValueError):
            matriz_de_combinacion([], [1, 2])


class PruebasCombinacionLineal(unittest.TestCase):
    def test_base_estandar_solucion_unica(self):
        resultado = evaluar_combinacion_lineal([[1, 0], [0, 1]], [3, 4])
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertTrue(resultado["es_combinacion"])
        self.assertEqual(resultado["coeficientes"], [3, 4])
        self.assertIsNone(resultado["coeficientes_particulares"])
        self.assertEqual(resultado["solucion_general"], ["c1 = 3", "c2 = 4"])
        self.assertEqual(resultado["ecuaciones"], ["c1 = 3", "c2 = 4"])
        self.assertEqual(resultado["verificacion"], [3, 4])
        self.assertEqual(resultado["nombres"], ["v1", "v2"])
        self.assertEqual(resultado["pasos"], [])

    def test_solucion_unica_con_eliminacion(self):
        # b = 2·v1 - v2 con v1 = (1, 2), v2 = (3, 4): b = (-1, 0)
        resultado = evaluar_combinacion_lineal([[1, 2], [3, 4]], [-1, 0])
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["coeficientes"], [2, -1])
        self.assertEqual(combinar(resultado["coeficientes"], [[1, 2], [3, 4]]), [-1, 0])
        self.assertTrue(resultado["pasos"])
        self.assertEqual(resultado["matriz_aumentada"], [[1, 3, -1], [2, 4, 0]])
        self.assertEqual(resultado["matriz_reducida"], [[1, 0, 2], [0, 1, -1]])
        self.assertEqual(resultado["columnas_pivote"], [1, 2])

    def test_no_pertenece_sistema_inconsistente(self):
        resultado = evaluar_combinacion_lineal([[1, 2], [2, 4]], [3, 7])
        self.assertEqual(resultado["clasificacion"], INCONSISTENTE)
        self.assertFalse(resultado["es_combinacion"])
        self.assertIsNone(resultado["coeficientes"])
        self.assertIsNone(resultado["coeficientes_particulares"])
        self.assertIsNone(resultado["verificacion"])
        self.assertEqual(resultado["solucion_general"], [])
        self.assertIn("0 = 1", " ".join(resultado["justificacion"]))
        self.assertIn("no tiene solución", " ".join(resultado["justificacion"]))

    def test_infinitas_combinaciones_es_combinacion_lineal(self):
        # v2 = 2·v1: b = (3, 6) se escribe de infinitas maneras.
        resultado = evaluar_combinacion_lineal([[1, 2], [2, 4]], [3, 6])
        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertTrue(resultado["es_combinacion"])
        self.assertIsNone(resultado["coeficientes"])
        self.assertEqual(resultado["solucion_general"], ["c1 = 3 - 2c2", "c2 es libre"])
        self.assertEqual(resultado["variables_libres"], [2])
        self.assertEqual(resultado["coeficientes_particulares"], [3, 0])
        self.assertEqual(resultado["verificacion"], [3, 6])
        self.assertIn("c2 no tiene pivote", " ".join(resultado["justificacion"]))

    def test_infinitas_con_tres_generadores_dependientes(self):
        generadores = [[1, 0, 1], [0, 1, 1], [1, 1, 2]]
        resultado = evaluar_combinacion_lineal(generadores, [2, 3, 5])
        self.assertEqual(resultado["clasificacion"], SOLUCIONES_INFINITAS)
        self.assertEqual(resultado["solucion_general"], ["c1 = 2 - c3", "c2 = 3 - c3", "c3 es libre"])
        self.assertEqual(resultado["coeficientes_particulares"], [2, 3, 0])
        self.assertEqual(combinar([1, 2, 1], generadores), [2, 3, 5])
        self.assertEqual(combinar(resultado["coeficientes_particulares"], generadores), [2, 3, 5])

    def test_dimension_mayor_que_tres(self):
        generadores = [[1, 0, 0, 0, 1], [0, 1, 0, 0, 1], [0, 0, 1, 0, 1], [0, 0, 0, 1, 1]]
        objetivo = [1, 2, 3, 4, 10]
        resultado = evaluar_combinacion_lineal(generadores, objetivo)
        self.assertEqual(resultado["dimension"], 5)
        self.assertEqual(resultado["cantidad_vectores"], 4)
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(resultado["coeficientes"], [1, 2, 3, 4])
        self.assertEqual(resultado["verificacion"], objetivo)
        self.assertEqual(len(resultado["matriz_aumentada"]), 5)
        self.assertEqual(len(resultado["matriz_aumentada"][0]), 5)

        # Con la última componente cambiada ya no pertenece al conjunto generado.
        sin_solucion = evaluar_combinacion_lineal(generadores, [1, 2, 3, 4, 11])
        self.assertEqual(sin_solucion["clasificacion"], INCONSISTENTE)

    def test_mas_de_dos_generadores_en_r3(self):
        generadores = [[1, 0, 2], [0, 1, 3], [1, 1, 0]]
        resultado = evaluar_combinacion_lineal(generadores, [4, 5, 6])
        self.assertEqual(resultado["clasificacion"], SOLUCION_UNICA)
        self.assertEqual(combinar(resultado["coeficientes"], generadores), [4, 5, 6])
        self.assertEqual(resultado["ecuaciones"], ["c1 + c3 = 4", "c2 + c3 = 5", "2c1 + 3c2 = 6"])

    def test_fracciones_exactas_en_componentes_y_coeficientes(self):
        resultado = evaluar_combinacion_lineal([[F(1, 2), 0], [0, F(1, 3)]], [1, 1])
        self.assertEqual(resultado["coeficientes"], [2, 3])
        resultado = evaluar_combinacion_lineal([[2, 0], [0, 3]], [1, 1])
        self.assertEqual(resultado["coeficientes"], [F(1, 2), F(1, 3)])
        self.assertEqual(resultado["solucion_general"], ["c1 = 1/2", "c2 = 1/3"])
        self.assertEqual(resultado["verificacion"], [1, 1])

    def test_un_solo_generador(self):
        self.assertEqual(evaluar_combinacion_lineal([[2, 4]], [1, 2])["coeficientes"], [F(1, 2)])
        self.assertEqual(evaluar_combinacion_lineal([[2, 4]], [1, 3])["clasificacion"], INCONSISTENTE)
        self.assertEqual(evaluar_combinacion_lineal([[0, 0]], [0, 0])["clasificacion"], SOLUCIONES_INFINITAS)

    def test_combinar_verifica_con_las_operaciones_del_modulo(self):
        self.assertEqual(combinar([3, 4], [[1, 0], [0, 1]]), [3, 4])
        self.assertEqual(combinar([F(1, 2)], [[2, 4]]), [1, 2])
        with self.assertRaises(ValueError):
            combinar([1], [[1, 2], [3, 4]])
        with self.assertRaises(ValueError):
            combinar([], [])


class PruebasReutilizacionDelMotorDeSistemas(unittest.TestCase):
    def test_resuelve_con_gauss_jordan_del_backend_y_no_con_otro_algoritmo(self):
        with patch("backend.vectores.resolver_sistema_gauss_jordan", wraps=resolver_sistema_gauss_jordan) as motor:
            resultado = evaluar_combinacion_lineal([[1, 2], [3, 4]], [5, 6])
        motor.assert_called_once()
        matriz, nombre = motor.call_args.args
        self.assertEqual(matriz, [[1, 3, 5], [2, 4, 6]])
        self.assertEqual(nombre, "c")
        self.assertEqual(resultado["coeficientes"], [-1, 2])
        self.assertEqual(combinar([-1, 2], [[1, 2], [3, 4]]), [5, 6])

    def test_la_clasificacion_coincide_con_la_del_sistema(self):
        casos = (
            ([[1, 0], [0, 1]], [3, 4]),
            ([[1, 2], [2, 4]], [3, 6]),
            ([[1, 2], [2, 4]], [3, 7]),
            ([[1, 0, 2], [0, 1, 3], [1, 1, 0]], [4, 5, 6]),
        )
        for generadores, objetivo in casos:
            with self.subTest(objetivo=objetivo):
                matriz = matriz_de_combinacion(generadores, objetivo)
                sistema = resolver_sistema_gauss_jordan(matriz)
                combinacion = evaluar_combinacion_lineal(generadores, objetivo)
                self.assertEqual(combinacion["clasificacion"], sistema["clasificacion"])
                self.assertEqual(combinacion["columnas_pivote"], sistema["columnas_pivote"])
                self.assertEqual(combinacion["matriz_reducida"], sistema["matriz_reducida"])
                self.assertEqual(combinacion["pasos"], sistema["pasos"])
                # Misma solución, solo cambia la letra de las incógnitas.
                self.assertEqual(
                    combinacion["solucion_general"],
                    [linea.replace("x", "c") for linea in sistema["solucion_general"]],
                )
                self.assertEqual(combinacion["es_combinacion"], sistema["clasificacion"] != INCONSISTENTE)
                if sistema["clasificacion"] == SOLUCION_UNICA:
                    self.assertEqual(combinacion["coeficientes"], sistema["soluciones"])

    def test_gauss_y_gauss_jordan_conservan_la_letra_x_por_defecto(self):
        matriz = [[1, 1, 3], [1, -1, 1]]
        self.assertEqual(resolver_sistema_gauss(matriz)["solucion_general"], ["x1 = 2", "x2 = 1"])
        self.assertEqual(resolver_sistema_gauss_jordan(matriz)["solucion_general"], ["x1 = 2", "x2 = 1"])
        self.assertEqual(resolver_sistema_gauss(matriz, "c")["solucion_general"], ["c1 = 2", "c2 = 1"])
        infinitas = resolver_sistema_gauss_jordan([[1, 1, 2], [2, 2, 4]], "c")
        self.assertEqual(infinitas["solucion_general"], ["c1 = 2 - c2", "c2 es libre"])
        self.assertEqual(infinitas["ecuaciones_resultantes"], ["c1 + c2 = 2", "0 = 0"])
        self.assertIn("La variable c2 no tiene pivote", " ".join(infinitas["justificacion"]))

    def test_expresiones_aceptan_el_nombre_de_la_incognita(self):
        expresion = crear_expresion(3, {1: -2, 3: F(1, 2)})
        self.assertEqual(formatear_expresion(expresion), "3 - 2x1 + 1/2x3")
        self.assertEqual(formatear_expresion(expresion, "c"), "3 - 2c1 + 1/2c3")
        self.assertEqual(formatear_ecuacion(crear_expresion(0, {2: 1}), 5, "c"), "c2 = 5")


if __name__ == "__main__":
    unittest.main()
