"""Pruebas de lo que hace cada opcion del menu."""

import unittest
from fractions import Fraction
from unittest import mock

from backend.sistemas import INCONSISTENTE, SOLUCION_UNICA, SOLUCIONES_INFINITAS
from frontend.terminal import opciones
from tests.ayudas import capturar, capturar_con_resultado, sin_ansi

SOLUCION_UNICA_3X4 = [[1, 2, 3, 6], [2, -3, 2, 14], [3, 1, -1, -2]]
INFINITAS_2X4 = [[1, 1, 1, 6], [0, 1, 2, 5]]
INCONSISTENTE_2X3 = [[1, 1, 2], [1, 1, 5]]
UNA_LIBRE_3X4 = [[1, 0, -5, 1], [0, 1, 1, 4], [0, 0, 0, 0]]
VARIAS_LIBRES_3X6 = [[1, 6, 0, 3, 0, 0], [0, 0, 1, -4, 0, 5], [0, 0, 0, 0, 1, 7]]
ENTRE_PIVOTES_2X4 = [[1, 1, 1, 5], [0, 1, 1, 2]]
INCONSISTENTE_2X4 = [[1, 0, -2, 4], [0, 0, 0, 3]]

TITULOS = (
    "Pasos realizados",
    "Matriz escalonada",
    "Matriz reducida",
    "Sistema resultante",
    "Clasificación",
    "Sustitución regresiva",
    "Solución",
)


def resolver(funcion, matriz):
    return sin_ansi(capturar(funcion, matriz))


def titulos_en_orden(salida):
    return [linea for linea in salida.splitlines() if linea in TITULOS]


def seccion(salida, titulo):
    """Las lineas con contenido de una seccion, hasta el titulo siguiente."""
    lineas = salida.splitlines()
    contenido = []

    for linea in lineas[lineas.index(titulo) + 1:]:
        if linea in TITULOS:
            break
        if linea.strip():
            contenido.append(linea)

    return contenido


class PruebasCreacionDeSistemaDirecto(unittest.TestCase):
    def test_un_sistema_valido_devuelve_la_matriz_aumentada(self):
        texto = "x1 - 3x2 - 5x3 = 0; x2 + x3 = 3"

        with mock.patch.object(opciones, "pedir_texto_sistema", return_value=texto):
            matriz, salida = capturar_con_resultado(opciones.crear_sistema_directo)

        self.assertEqual(matriz, [[1, -3, -5, 0], [0, 1, 1, 3]])
        self.assertIn("Sistema creado correctamente", sin_ansi(salida))

    def test_muestra_un_ejemplo_del_formato(self):
        with mock.patch.object(opciones, "pedir_texto_sistema", return_value="x1 = 1"):
            _, salida = capturar_con_resultado(opciones.crear_sistema_directo)

        self.assertIn("x1 - 3x2 - 5x3 = 0; x2 + x3 = 3", sin_ansi(salida))

    def test_un_texto_invalido_devuelve_none_y_muestra_el_error(self):
        with mock.patch.object(opciones, "pedir_texto_sistema", return_value="x1 + x2"):
            matriz, salida = capturar_con_resultado(opciones.crear_sistema_directo)

        limpia = sin_ansi(salida)

        self.assertIsNone(matriz)
        self.assertIn("Formato de sistema inválido", limpia)
        self.assertNotIn("Traceback", limpia)

    def test_ningun_formato_invalido_provoca_una_excepcion(self):
        entradas_invalidas = (
            "",
            "x1 + x2",
            "x1 = 2 = 3",
            "x0 + x1 = 2",
            "2y1 + x2 = 3",
            "x1 ++ x2 = 3",
            "x1 = hola",
            "x1 + = 3",
            "x1 = 2;; x2 = 3",
        )

        for texto in entradas_invalidas:
            with self.subTest(texto=texto):
                with mock.patch.object(
                    opciones, "pedir_texto_sistema", return_value=texto
                ):
                    matriz, salida = capturar_con_resultado(
                        opciones.crear_sistema_directo
                    )

                self.assertIsNone(matriz)
                self.assertIn("Formato de sistema inválido", sin_ansi(salida))


class PruebasCreacionDeSistemaManual(unittest.TestCase):
    def test_devuelve_la_matriz_construida(self):
        sistema = [[1, -3, -5, 0], [0, 1, 1, 3]]

        with mock.patch.object(opciones, "pedir_sistema_manual", return_value=sistema):
            matriz, salida = capturar_con_resultado(opciones.crear_sistema_manual)

        self.assertEqual(matriz, sistema)
        self.assertIn("Sistema creado correctamente", sin_ansi(salida))


class PruebasResolverPorGauss(unittest.TestCase):
    def test_solucion_unica_muestra_el_procedimiento_completo(self):
        salida = resolver(opciones.resolver_por_gauss, SOLUCION_UNICA_3X4)

        self.assertIn("Pasos realizados", salida)
        self.assertIn("Matriz escalonada", salida)
        self.assertIn("Sustitución regresiva", salida)
        self.assertIn(SOLUCION_UNICA, salida)
        self.assertIn("x1 = 1", salida)
        self.assertIn("x2 = -2", salida)
        self.assertIn("x3 = 3", salida)

    def test_no_muestra_la_matriz_reducida(self):
        salida = resolver(opciones.resolver_por_gauss, SOLUCION_UNICA_3X4)

        self.assertNotIn("Matriz reducida", salida)

    def test_soluciones_infinitas_no_sustituyen(self):
        salida = resolver(opciones.resolver_por_gauss, INFINITAS_2X4)

        self.assertIn(SOLUCIONES_INFINITAS, salida)
        self.assertNotIn("Sustitución regresiva", salida)

    def test_sistema_inconsistente_no_sustituye(self):
        salida = resolver(opciones.resolver_por_gauss, INCONSISTENTE_2X3)

        self.assertIn(INCONSISTENTE, salida)
        self.assertNotIn("Sustitución regresiva", salida)


class PruebasResolverPorGaussJordan(unittest.TestCase):
    def test_solucion_unica_muestra_la_forma_reducida(self):
        salida = resolver(opciones.resolver_por_gauss_jordan, SOLUCION_UNICA_3X4)

        self.assertIn("Pasos realizados", salida)
        self.assertIn("Matriz reducida", salida)
        self.assertIn(SOLUCION_UNICA, salida)
        self.assertIn("x1 = 1", salida)

    def test_no_muestra_sustitucion_regresiva(self):
        salida = resolver(opciones.resolver_por_gauss_jordan, SOLUCION_UNICA_3X4)

        self.assertNotIn("Sustitución regresiva", salida)
        self.assertNotIn("Matriz escalonada", salida)

    def test_soluciones_infinitas(self):
        salida = resolver(opciones.resolver_por_gauss_jordan, INFINITAS_2X4)

        self.assertIn(SOLUCIONES_INFINITAS, salida)

    def test_sistema_inconsistente(self):
        salida = resolver(opciones.resolver_por_gauss_jordan, INCONSISTENTE_2X3)

        self.assertIn(INCONSISTENTE, salida)


class PruebasOrdenDeLaSalida(unittest.TestCase):
    """Siempre aparecen matriz, sistema resultante, clasificacion y solucion."""

    def test_gauss(self):
        salida = resolver(opciones.resolver_por_gauss, SOLUCION_UNICA_3X4)

        self.assertEqual(
            titulos_en_orden(salida),
            [
                "Pasos realizados",
                "Matriz escalonada",
                "Sistema resultante",
                "Clasificación",
                "Sustitución regresiva",
                "Solución",
            ],
        )

    def test_gauss_jordan(self):
        salida = resolver(opciones.resolver_por_gauss_jordan, SOLUCION_UNICA_3X4)

        self.assertEqual(
            titulos_en_orden(salida),
            [
                "Pasos realizados",
                "Matriz reducida",
                "Clasificación",
                "Solución",
            ],
        )

    def test_gauss_jordan_no_repite_una_solucion_directa(self):
        salida = resolver(opciones.resolver_por_gauss_jordan, SOLUCION_UNICA_3X4)

        self.assertNotIn("Sistema resultante", salida)
        self.assertIn("Solución", salida)
        self.assertIn("x1 = 1", salida)
        self.assertIn("x2 = -2", salida)
        self.assertIn("x3 = 3", salida)

    def test_la_solucion_directa_mantiene_fracciones_exactas(self):
        salida = resolver(
            opciones.resolver_por_gauss_jordan,
            [[1, 0, 3], [0, 3, 2]],
        )

        self.assertNotIn("Sistema resultante", salida)
        self.assertIn("x1 = 3", salida)
        self.assertIn("x2 = 2/3", salida)

    def test_una_fila_redundante_no_obliga_a_repetir_el_sistema(self):
        salida = resolver(
            opciones.resolver_por_gauss_jordan,
            [[1, 0, 2], [0, 1, 3], [0, 0, 0]],
        )

        self.assertIn(SOLUCION_UNICA, salida)
        self.assertNotIn("Sistema resultante", salida)

    def test_las_variables_libres_no_ocupan_una_seccion_aparte(self):
        salida = resolver(opciones.resolver_por_gauss, UNA_LIBRE_3X4)

        self.assertNotIn("Variables básicas", salida)
        self.assertNotIn("Variables libres", salida)


class PruebasSistemaResultanteEnPantalla(unittest.TestCase):
    def test_incluye_las_filas_nulas(self):
        salida = resolver(opciones.resolver_por_gauss, UNA_LIBRE_3X4)

        self.assertEqual(
            seccion(salida, "Sistema resultante"),
            ["x1 - 5x3 = 1", "x2 + x3 = 4", "0 = 0"],
        )

    def test_incluye_la_contradiccion(self):
        salida = resolver(opciones.resolver_por_gauss, INCONSISTENTE_2X4)

        self.assertEqual(
            seccion(salida, "Sistema resultante"), ["x1 - 2x3 = 4", "0 = 3"]
        )

    def test_inconsistencia_muestra_la_evidencia_completa(self):
        matriz = [[1, 0, 2, 4], [0, 1, -1, 3], [0, 0, 0, 5]]
        salida = resolver(opciones.resolver_por_gauss_jordan, matriz)

        for fragmento in (
            "Sistema resultante",
            "0 = 5",
            "fila 3",
            "[0 0 0 | 5]",
            INCONSISTENTE,
            "no tiene solución",
        ):
            self.assertIn(fragmento, salida)


class PruebasSolucionEnPantalla(unittest.TestCase):
    def test_solucion_unica(self):
        salida = resolver(opciones.resolver_por_gauss, SOLUCION_UNICA_3X4)

        self.assertEqual(
            seccion(salida, "Solución"), ["x1 = 1", "x2 = -2", "x3 = 3"]
        )

    def test_una_variable_libre(self):
        salida = resolver(opciones.resolver_por_gauss_jordan, UNA_LIBRE_3X4)

        self.assertIn("Sistema resultante", salida)
        self.assertIn(SOLUCIONES_INFINITAS, salida)
        self.assertIn("fila 3", salida)
        self.assertIn("[0 0 0 | 0]", salida)
        self.assertIn("x3 no tiene pivote", salida)
        self.assertIn("x1 = 1 + 5x3", salida)
        self.assertIn("x2 = 4 - x3", salida)
        self.assertIn("x3 es libre", salida)

    def test_infinita_sin_fila_nula_se_justifica_por_el_pivote_faltante(self):
        salida = resolver(
            opciones.resolver_por_gauss_jordan,
            [[1, 2, -1, 4], [0, 1, 1, 2]],
        )

        self.assertIn("Sistema resultante", salida)
        self.assertIn(SOLUCIONES_INFINITAS, salida)
        self.assertIn("x3 no tiene pivote", salida)
        self.assertIn("x3 es libre", salida)
        self.assertNotIn("[0 0 0 | 0]", salida)

    def test_varias_variables_libres(self):
        salida = resolver(opciones.resolver_por_gauss, VARIAS_LIBRES_3X6)

        self.assertIn("x2 y x4 no tienen pivote", salida)
        for linea in (
            "x1 = -6x2 - 3x4",
            "x2 es libre",
            "x3 = 5 + 4x4",
            "x4 es libre",
            "x5 = 7",
        ):
            self.assertIn(linea, salida)

    def test_una_variable_pivote_no_depende_de_otra(self):
        salida = resolver(opciones.resolver_por_gauss, ENTRE_PIVOTES_2X4)

        self.assertIn("x3 no tiene pivote", salida)
        self.assertIn("x1 = 3", salida)
        self.assertIn("x2 = 2 - x3", salida)
        self.assertIn("x3 es libre", salida)

    def test_sistema_inconsistente(self):
        for funcion in (opciones.resolver_por_gauss, opciones.resolver_por_gauss_jordan):
            with self.subTest(metodo=funcion.__name__):
                salida = resolver(funcion, INCONSISTENTE_2X4)

                self.assertIn("Sistema resultante", salida)
                self.assertIn("0 = 3", salida)
                self.assertIn("fila 2", salida)
                self.assertIn("[0 0 0 | 3]", salida)
                self.assertIn("no tiene solución", salida)
                self.assertNotIn("es libre", salida)


class PruebasEquivalenciaEnPantalla(unittest.TestCase):
    """Ambas opciones deben coincidir en clasificacion y soluciones."""

    def test_misma_clasificacion_y_mismas_soluciones(self):
        for matriz in (SOLUCION_UNICA_3X4, INFINITAS_2X4, INCONSISTENTE_2X3):
            with self.subTest(matriz=matriz):
                por_gauss = resolver(opciones.resolver_por_gauss, matriz)
                por_gauss_jordan = resolver(
                    opciones.resolver_por_gauss_jordan, matriz
                )

                for clasificacion in (
                    SOLUCION_UNICA, SOLUCIONES_INFINITAS, INCONSISTENTE
                ):
                    self.assertEqual(
                        clasificacion in por_gauss,
                        clasificacion in por_gauss_jordan
                    )

    def test_las_soluciones_finales_coinciden(self):
        por_gauss = resolver(opciones.resolver_por_gauss, SOLUCION_UNICA_3X4)
        por_gauss_jordan = resolver(
            opciones.resolver_por_gauss_jordan, SOLUCION_UNICA_3X4
        )

        for linea in ("x1 = 1", "x2 = -2", "x3 = 3"):
            self.assertIn(linea, por_gauss)
            self.assertIn(linea, por_gauss_jordan)

    def test_la_solucion_coincide_tambien_con_variables_libres(self):
        matrices = (
            UNA_LIBRE_3X4, VARIAS_LIBRES_3X6, ENTRE_PIVOTES_2X4, INCONSISTENTE_2X4
        )

        for matriz in matrices:
            with self.subTest(matriz=matriz):
                por_gauss = resolver(opciones.resolver_por_gauss, matriz)
                por_gauss_jordan = resolver(
                    opciones.resolver_por_gauss_jordan, matriz
                )

                self.assertEqual(
                    seccion(por_gauss, "Solución"),
                    seccion(por_gauss_jordan, "Solución"),
                )

    def test_el_sistema_resultante_puede_diferir(self):
        por_gauss = resolver(opciones.resolver_por_gauss, ENTRE_PIVOTES_2X4)
        por_gauss_jordan = resolver(
            opciones.resolver_por_gauss_jordan, ENTRE_PIVOTES_2X4
        )

        self.assertNotEqual(
            seccion(por_gauss, "Sistema resultante"),
            seccion(por_gauss_jordan, "Sistema resultante"),
        )


class PruebasValidacionAntesDeResolver(unittest.TestCase):
    def test_sin_matriz_activa_avisa(self):
        for funcion in (opciones.resolver_por_gauss, opciones.resolver_por_gauss_jordan):
            with self.subTest(metodo=funcion.__name__):
                salida = resolver(funcion, [])

                self.assertIn("No hay ninguna matriz", salida)

    def test_una_sola_columna_no_es_un_sistema(self):
        for funcion in (opciones.resolver_por_gauss, opciones.resolver_por_gauss_jordan):
            with self.subTest(metodo=funcion.__name__):
                salida = resolver(funcion, [[1], [2]])

                self.assertIn("al menos una columna de coeficientes", salida)

    def test_una_matriz_no_rectangular_no_es_un_sistema(self):
        for funcion in (opciones.resolver_por_gauss, opciones.resolver_por_gauss_jordan):
            with self.subTest(metodo=funcion.__name__):
                salida = resolver(funcion, [[1, 2], [3, 4, 5]])

                self.assertIn("no es rectangular", salida)

    def test_una_matriz_creada_a_mano_puede_resolverse_como_sistema(self):
        # No importa como se creo la matriz: la ultima columna se interpreta
        # como terminos independientes al elegir un metodo.
        salida = resolver(opciones.resolver_por_gauss, [[1, 1, 3], [1, -1, 1]])

        self.assertIn(SOLUCION_UNICA, salida)
        self.assertIn("x1 = 2", salida)
        self.assertIn("x2 = 1", salida)


class PruebasOpcionesDeMatriz(unittest.TestCase):
    def test_ver_matriz_sin_matriz_activa(self):
        salida = resolver(opciones.mostrar_matriz, [])

        self.assertIn("No hay ninguna matriz", salida)

    def test_ver_matriz_con_fracciones(self):
        salida = resolver(opciones.mostrar_matriz, [[Fraction(1, 2), 3]])

        self.assertIn("1/2", salida)

    def test_consultar_un_elemento_fraccionario(self):
        with mock.patch.object(opciones, "pedir_indices", return_value=(1, 1)):
            salida = resolver(opciones.consultar_elemento, [[Fraction(3, 4), 1]])

        self.assertIn("3/4", salida)

    def test_modificar_un_elemento(self):
        matriz = [[1, 2], [3, 4]]

        with mock.patch.object(opciones, "pedir_indices", return_value=(1, 2)), \
                mock.patch.object(opciones, "pedir_nuevo_numero", return_value=9):
            capturar(opciones.modificar_elemento, matriz)

        self.assertEqual(matriz, [[1, 9], [3, 4]])


class PruebasPasosEnPantalla(unittest.TestCase):
    def test_una_matriz_ya_resuelta_avisa_que_no_hubo_operaciones(self):
        salida = resolver(opciones.resolver_por_gauss_jordan, [[1, 0, 2], [0, 1, 1]])

        self.assertIn("No fue necesario realizar operaciones", salida)

    def test_la_sustitucion_muestra_la_expresion_cuando_aporta_informacion(self):
        salida = resolver(opciones.resolver_por_gauss, [[1, 1, 3], [1, -1, 1]])

        self.assertIn("x2 = 1", salida)
        self.assertIn("x1 = 3 - (1)(1) = 2", salida)


if __name__ == "__main__":
    unittest.main()
