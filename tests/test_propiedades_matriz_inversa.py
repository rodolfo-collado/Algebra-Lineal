"""P26.9: propiedades exactas y aplicación de la inversa, sin recalcular A⁻¹."""

from copy import deepcopy
from fractions import Fraction
import unittest
from unittest.mock import call, patch

from backend.matrices import matriz_identidad, multiplicar_matrices, resolver_operacion_matrices
from backend.matriz_inversa import (
    DIRECTO_2X2, FUNCIONES_ADICIONALES, GAUSS_JORDAN,
    aplicar_funcion_adicional, calcular_inversa, inversa_de_inversa,
    propiedad_producto, propiedad_traspuesta, resolver_por_inversa,
)
from backend.seguridad_numerica import BITS_MAXIMOS, MENSAJE_CALCULO_GRANDE


A = [[3, 4], [5, 6]]
INVERSA = [[-3, 2], [Fraction(5, 2), Fraction(-3, 2)]]
B = [[2, 1], [1, 1]]
A3 = [[0, 1, 2], [1, 0, 3], [4, -3, 8]]
B3 = [[1, 1, 0], [0, 1, 1], [1, 0, 1]]
FRACCIONES = [[Fraction(1, 2), Fraction(-2, 3)], [Fraction(3, 4), Fraction(5, 6)]]
B_FRACCIONES = [[-1, Fraction(1, 3)], [2, 3]]
SINGULAR = [[1, 2], [2, 4]]


class PruebasInversaDeInversa(unittest.TestCase):
    def test_ejemplo_del_profesor_con_ambos_metodos(self):
        for metodo in (GAUSS_JORDAN, DIRECTO_2X2):
            with self.subTest(metodo=metodo):
                datos = inversa_de_inversa(A, INVERSA, metodo)
                self.assertEqual(datos["inversa_de_inversa"], A)
                self.assertEqual(datos["resultado"], A)
                self.assertTrue(datos["coincide_con_a"])
                self.assertTrue(datos["aplicable"])
                self.assertEqual(datos["calculo_inversa_de_inversa"]["metodo"], metodo)

    def test_3x3_y_fracciones_negativas(self):
        for matriz in (A3, FRACCIONES, [[Fraction(-2, 3)]]):
            with self.subTest(matriz=matriz):
                inversa = calcular_inversa(matriz)["inversa"]
                datos = inversa_de_inversa(matriz, inversa)
                self.assertEqual(datos["inversa_de_inversa"], matriz)
                self.assertTrue(datos["coincide_con_a"])
                self.assertTrue(all(isinstance(v, Fraction) for fila in datos["resultado"] for v in fila))

    def test_solo_invierte_la_inversa_recibida(self):
        for metodo in (GAUSS_JORDAN, DIRECTO_2X2):
            with self.subTest(metodo=metodo), patch(
                "backend.matriz_inversa.calcular_inversa", wraps=calcular_inversa,
            ) as motor:
                inversa_de_inversa(A, INVERSA, metodo)
            motor.assert_called_once_with(INVERSA, metodo)

    def test_una_candidata_incorrecta_no_presupone_la_igualdad(self):
        datos = inversa_de_inversa(A, matriz_identidad(2))
        self.assertFalse(datos["coincide_con_a"])
        self.assertEqual(datos["inversa_de_inversa"], matriz_identidad(2))
        singular = inversa_de_inversa(A, SINGULAR)
        self.assertFalse(singular["aplicable"])
        self.assertIsNone(singular["resultado"])


class PruebasPropiedadTraspuesta(unittest.TestCase):
    def test_no_simetrica_2x2_con_ambos_metodos(self):
        for metodo in (GAUSS_JORDAN, DIRECTO_2X2):
            with self.subTest(metodo=metodo):
                datos = propiedad_traspuesta(A, INVERSA, metodo)
                self.assertEqual(datos["traspuesta_a"], [[3, 5], [4, 6]])
                esperado = [[-3, Fraction(5, 2)], [2, Fraction(-3, 2)]]
                self.assertEqual(datos["inversa_traspuesta"], esperado)
                self.assertEqual(datos["traspuesta_inversa"], esperado)
                self.assertEqual(datos["resultado"], esperado)
                self.assertTrue(datos["coinciden"])
                self.assertEqual(datos["calculo_inversa_traspuesta"]["metodo"], metodo)

    def test_no_simetrica_3x3_y_fracciones(self):
        for matriz in (A3, FRACCIONES):
            with self.subTest(matriz=matriz):
                inversa = calcular_inversa(matriz)["inversa"]
                datos = propiedad_traspuesta(matriz, inversa)
                self.assertTrue(datos["coinciden"])
                self.assertEqual(datos["inversa_traspuesta"], datos["traspuesta_inversa"])
                self.assertNotEqual(datos["traspuesta_a"], matriz)

    def test_reutiliza_la_traspuesta_y_solo_invierte_a_traspuesta(self):
        with (
            patch("backend.matriz_inversa.resolver_operacion_matrices", wraps=resolver_operacion_matrices) as operaciones,
            patch("backend.matriz_inversa.calcular_inversa", wraps=calcular_inversa) as inversiones,
        ):
            propiedad_traspuesta(A, INVERSA, DIRECTO_2X2)
        self.assertEqual(operaciones.call_args_list, [
            call("traspuesta", a=A), call("traspuesta", a=INVERSA),
        ])
        inversiones.assert_called_once_with([[3, 5], [4, 6]], DIRECTO_2X2)

    def test_compara_los_dos_resultados_reales(self):
        datos = propiedad_traspuesta(A, matriz_identidad(2))
        self.assertFalse(datos["coinciden"])
        self.assertEqual(datos["traspuesta_inversa"], matriz_identidad(2))


class PruebasPropiedadProducto(unittest.TestCase):
    def test_no_conmutativo_2x2_con_ambos_metodos(self):
        self.assertNotEqual(multiplicar_matrices(A, B), multiplicar_matrices(B, A))
        for metodo in (GAUSS_JORDAN, DIRECTO_2X2):
            with self.subTest(metodo=metodo):
                datos = propiedad_producto(A, INVERSA, B, metodo)
                self.assertEqual(datos["producto_ab"], [[10, 7], [16, 11]])
                esperado = [[Fraction(-11, 2), Fraction(7, 2)], [8, -5]]
                self.assertEqual(datos["inversa_producto"], esperado)
                self.assertEqual(datos["producto_inversas"], esperado)
                self.assertEqual(datos["resultado"], esperado)
                self.assertTrue(datos["coinciden"])
                self.assertTrue(datos["b_invertible"])
                for clave in ("calculo_inversa_b", "calculo_inversa_producto"):
                    self.assertEqual(datos[clave]["metodo"], metodo)

    def test_no_conmutativo_3x3_y_fracciones(self):
        for matriz, segunda in ((A3, B3), (FRACCIONES, B_FRACCIONES)):
            with self.subTest(matriz=matriz):
                inversa = calcular_inversa(matriz)["inversa"]
                self.assertNotEqual(multiplicar_matrices(matriz, segunda), multiplicar_matrices(segunda, matriz))
                datos = propiedad_producto(matriz, inversa, segunda)
                self.assertTrue(datos["coinciden"])
                self.assertEqual(datos["inversa_producto"], datos["producto_inversas"])
                self.assertTrue(all(isinstance(v, Fraction) for fila in datos["resultado"] for v in fila))

    def test_reutiliza_los_dos_productos_y_no_recalcula_a(self):
        for metodo in (GAUSS_JORDAN, DIRECTO_2X2):
            with (
                self.subTest(metodo=metodo),
                patch("backend.matriz_inversa.resolver_operacion_matrices", wraps=resolver_operacion_matrices) as operaciones,
                patch("backend.matriz_inversa.calcular_inversa", wraps=calcular_inversa) as inversiones,
            ):
                datos = propiedad_producto(A, INVERSA, B, metodo)
            self.assertEqual(operaciones.call_args_list, [
                call("producto", a=A, b=B),
                call("producto", a=datos["inversa_b"], b=INVERSA),
            ])
            self.assertEqual(inversiones.call_args_list, [
                call(B, metodo), call(datos["producto_ab"], metodo),
            ])

    def test_b_singular_es_una_condicion_matematica_sin_productos(self):
        for metodo in (GAUSS_JORDAN, DIRECTO_2X2):
            with (
                self.subTest(metodo=metodo),
                patch("backend.matriz_inversa.resolver_operacion_matrices") as operaciones,
                patch("backend.matriz_inversa.calcular_inversa", wraps=calcular_inversa) as inversiones,
            ):
                datos = propiedad_producto(A, INVERSA, SINGULAR, metodo)
            operaciones.assert_not_called()
            inversiones.assert_called_once_with(SINGULAR, metodo)
            self.assertFalse(datos["b_invertible"])
            self.assertFalse(datos["aplicable"])
            self.assertIsNone(datos["resultado"])
            self.assertIn("B no tiene inversa", datos["motivo"])
            self.assertNotIn("producto_ab", datos)

    def test_compara_los_dos_lados_sin_asumir_la_identidad(self):
        datos = propiedad_producto(A, matriz_identidad(2), B)
        self.assertFalse(datos["coinciden"])
        self.assertNotEqual(datos["inversa_producto"], datos["producto_inversas"])


class PruebasResolverPorInversa(unittest.TestCase):
    def test_ejemplo_del_profesor_x_5_menos_3_y_comprobacion_exacta(self):
        for metodo in (GAUSS_JORDAN, DIRECTO_2X2):
            with self.subTest(metodo=metodo):
                inversa = calcular_inversa(A, metodo)["inversa"]
                datos = resolver_por_inversa(A, inversa, [3, 7])
                self.assertEqual(datos["x"], [[5], [-3]])
                self.assertEqual(datos["resultado"], [[5], [-3]])
                self.assertEqual(datos["b"], [[3], [7]])
                self.assertEqual(datos["a_por_x"], [[3], [7]])
                self.assertTrue(datos["coincide_con_b"])
                self.assertTrue(all(isinstance(fila[0], Fraction) for fila in datos["x"]))

    def test_3x3_fracciones_y_negativos(self):
        casos = ((A3, [Fraction(-1, 3), 2, -5]), (FRACCIONES, [Fraction(-1, 3), Fraction(5, 7)]))
        for matriz, vector in casos:
            with self.subTest(matriz=matriz):
                inversa = calcular_inversa(matriz)["inversa"]
                datos = resolver_por_inversa(matriz, inversa, vector)
                self.assertEqual(datos["a_por_x"], [[v] for v in vector])
                self.assertTrue(datos["coincide_con_b"])

    def test_reutiliza_matriz_vector_dos_veces_sin_invertir_ni_reducir(self):
        with (
            patch("backend.matriz_inversa.resolver_operacion_matrices", wraps=resolver_operacion_matrices) as operaciones,
            patch("backend.matriz_inversa.calcular_inversa", side_effect=AssertionError("Recalculó A⁻¹")),
            patch("backend.matriz_inversa.aplicar_gauss_jordan", side_effect=AssertionError("Redujo un sistema")),
            patch("backend.sistemas.resolver_sistema_gauss", side_effect=AssertionError("Usó el solver")),
            patch("backend.sistemas.resolver_sistema_gauss_jordan", side_effect=AssertionError("Usó el solver")),
        ):
            datos = resolver_por_inversa(A, INVERSA, [3, 7])
        self.assertEqual(operaciones.call_args_list, [
            call("matriz_vector", a=INVERSA, vector=[3, 7]),
            call("matriz_vector", a=A, vector=[Fraction(5), Fraction(-3)]),
        ])
        self.assertTrue(datos["coincide_con_b"])

    def test_comprobacion_no_da_por_correcta_una_candidata_equivocada(self):
        datos = resolver_por_inversa(A, matriz_identidad(2), [3, 7])
        self.assertEqual(datos["x"], [[3], [7]])
        self.assertEqual(datos["a_por_x"], [[37], [57]])
        self.assertFalse(datos["coincide_con_b"])


class PruebasContratoPropiedades(unittest.TestCase):
    def test_contrato_cerrado_y_resultado_predeterminado(self):
        self.assertEqual(FUNCIONES_ADICIONALES, ("ninguna", "inversa_inversa", "traspuesta", "producto", "vector"))
        with patch("backend.matriz_inversa.calcular_inversa") as inversiones:
            datos = aplicar_funcion_adicional("ninguna", A, INVERSA)
        inversiones.assert_not_called()
        self.assertEqual(datos["resultado"], INVERSA)
        self.assertTrue(datos["aplicable"])
        self.assertEqual(datos["funcion"], "ninguna")

    def test_dispatcher_ejecuta_cada_funcion_y_una_sola(self):
        casos = (
            ("inversa_inversa", "inversa_de_inversa", {}, (A, INVERSA, DIRECTO_2X2)),
            ("traspuesta", "propiedad_traspuesta", {}, (A, INVERSA, DIRECTO_2X2)),
            ("producto", "propiedad_producto", {"b": B}, (A, INVERSA, B, DIRECTO_2X2)),
            ("vector", "resolver_por_inversa", {"vector": [3, 7]}, (A, INVERSA, [3, 7])),
        )
        for funcion, nombre, extras, argumentos in casos:
            with self.subTest(funcion=funcion), patch(f"backend.matriz_inversa.{nombre}", return_value={"funcion": funcion}) as motor:
                self.assertEqual(aplicar_funcion_adicional(funcion, A, INVERSA, DIRECTO_2X2, **extras), {"funcion": funcion})
            motor.assert_called_once_with(*argumentos)

    def test_rechaza_identificadores_combinaciones_y_operandos_ajenos(self):
        for funcion in ("desconocida", "traspuesta,producto", ["traspuesta", "vector"], "", None):
            with self.subTest(funcion=funcion), self.assertRaisesRegex(ValueError, "función adicional válida"):
                aplicar_funcion_adicional(funcion, A, INVERSA)
        for funcion in FUNCIONES_ADICIONALES:
            extras = {"b": B} if funcion != "producto" else {"vector": [3, 7]}
            with self.subTest(funcion=funcion), self.assertRaisesRegex(ValueError, "solo se admite"):
                aplicar_funcion_adicional(funcion, A, INVERSA, **extras)
        for funcion in ("producto", "vector"):
            with self.subTest(funcion=funcion), self.assertRaisesRegex(ValueError, "requiere"):
                aplicar_funcion_adicional(funcion, A, INVERSA)

    def test_a_singular_detiene_cualquier_funcion_sin_motores(self):
        for funcion in FUNCIONES_ADICIONALES:
            extras = {"b": B} if funcion == "producto" else {"vector": [3, 7]} if funcion == "vector" else {}
            with (
                self.subTest(funcion=funcion),
                patch("backend.matriz_inversa.calcular_inversa") as inversiones,
                patch("backend.matriz_inversa.resolver_operacion_matrices") as operaciones,
            ):
                datos = aplicar_funcion_adicional(funcion, SINGULAR, None, **extras)
            inversiones.assert_not_called()
            operaciones.assert_not_called()
            self.assertFalse(datos["aplicable"])
            self.assertIsNone(datos["resultado"])
            self.assertIn("A no tiene inversa", datos["motivo"])
            if funcion == "vector":
                self.assertIn("x = A⁻¹b", datos["motivo"])
                self.assertNotIn("no tiene solución", datos["motivo"])
                self.assertNotIn("infinitas", datos["motivo"])

    def test_no_muta_entradas_ni_comparte_filas_con_el_resultado(self):
        for funcion in FUNCIONES_ADICIONALES:
            matriz, inversa, segunda, vector = deepcopy((FRACCIONES, calcular_inversa(FRACCIONES)["inversa"], B_FRACCIONES, [Fraction(-1, 3), 2]))
            antes = deepcopy((matriz, inversa, segunda, vector))
            extras = {"b": segunda} if funcion == "producto" else {"vector": vector} if funcion == "vector" else {}
            with self.subTest(funcion=funcion):
                datos = aplicar_funcion_adicional(funcion, matriz, inversa, **extras)
                self.assertEqual((matriz, inversa, segunda, vector), antes)
                datos["resultado"][0][0] = Fraction(17)
                self.assertEqual((matriz, inversa, segunda, vector), antes)

    def test_dimensiones_y_tipos_se_rechazan_antes_de_operar(self):
        casos = (
            (lambda: inversa_de_inversa(A, [[1]]), "mismo orden"),
            (lambda: propiedad_traspuesta(A, [[1]]), "mismo orden"),
            (lambda: propiedad_producto(A, INVERSA, [[1]]), "mismo orden"),
            (lambda: propiedad_producto(A, INVERSA, [[1, 2]]), "matriz cuadrada"),
            (lambda: resolver_por_inversa(A, INVERSA, [1]), "2 componentes"),
            (lambda: resolver_por_inversa(A, INVERSA, []), "no tiene componentes"),
            (lambda: resolver_por_inversa(A, INVERSA, [[3], [7]]), "no es un número"),
            (lambda: resolver_por_inversa(A, INVERSA, [0.5, 1]), "no es un número"),
            (lambda: propiedad_traspuesta([[0.5]], [[2]]), "número exacto"),
            (lambda: propiedad_traspuesta([[2]], [[True]]), "número exacto"),
            (lambda: propiedad_producto(A, INVERSA, [[0.5, 0], [0, 1]]), "número exacto"),
        )
        for ejecutar, mensaje in casos:
            with (
                self.subTest(mensaje=mensaje),
                patch("backend.matriz_inversa.calcular_inversa") as inversiones,
                patch("backend.matriz_inversa.resolver_operacion_matrices") as operaciones,
                self.assertRaisesRegex(ValueError, mensaje),
            ):
                ejecutar()
            inversiones.assert_not_called()
            operaciones.assert_not_called()

    def test_metodo_directo_fuera_de_2x2_y_metodo_desconocido_se_rechazan(self):
        inversa3 = calcular_inversa(A3)["inversa"]
        for funcion in FUNCIONES_ADICIONALES:
            extras = {"b": B3} if funcion == "producto" else {"vector": [1, 2, 3]} if funcion == "vector" else {}
            for metodo, mensaje in ((DIRECTO_2X2, "solo se aplica a matrices 2×2"), ("inventado", "método válido"), (None, "método válido")):
                with self.subTest(funcion=funcion, metodo=metodo), self.assertRaisesRegex(ValueError, mensaje):
                    aplicar_funcion_adicional(funcion, A3, inversa3, metodo, **extras)


class PruebasSeguridadPropiedades(unittest.TestCase):
    def test_la_segunda_inversion_conserva_el_limite_de_crecimiento(self):
        x = Fraction(1 << (BITS_MAXIMOS // 2 + 1))
        casos = (
            lambda: inversa_de_inversa(matriz_identidad(2), [[x, 1], [1, x]], DIRECTO_2X2),
            lambda: propiedad_traspuesta([[1, x], [x, 1]], matriz_identidad(2)),
        )
        for ejecutar in casos:
            with self.subTest(ejecutar=ejecutar), self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                ejecutar()

    def test_entradas_enormes_se_rechazan_tambien_en_traspuestas_y_vectores(self):
        enorme = 1 << BITS_MAXIMOS
        casos = (
            lambda: propiedad_traspuesta([[enorme]], [[1]]),
            lambda: propiedad_traspuesta([[1]], [[enorme]]),
            lambda: resolver_por_inversa([[1]], [[1]], [enorme]),
            lambda: propiedad_producto([[1]], [[1]], [[enorme]]),
        )
        for ejecutar in casos:
            with self.subTest(ejecutar=ejecutar), self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                ejecutar()

    def test_crecimiento_del_producto_y_matriz_vector_usa_la_proteccion_comun(self):
        x = Fraction(1 << (BITS_MAXIMOS // 2 + 1))
        for ejecutar in (
            lambda: propiedad_producto([[x]], [[1]], [[x]]),
            lambda: resolver_por_inversa([[1]], [[x]], [x]),
        ):
            with self.subTest(ejecutar=ejecutar), self.assertRaisesRegex(ValueError, MENSAJE_CALCULO_GRANDE):
                ejecutar()


if __name__ == "__main__":
    unittest.main()
