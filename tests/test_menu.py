"""Pruebas del menu principal y del submenu de creacion de sistemas."""

import re
import unittest
from unittest import mock

from frontend.terminal import consola, menu
from tests.ayudas import capturar, capturar_con_resultado, sin_ansi

_OPCION_NUMERADA = re.compile(r"^\s*\d+\.\s")


def opciones_visibles(salida):
    return [
        linea.strip()
        for linea in sin_ansi(salida).splitlines()
        if _OPCION_NUMERADA.match(linea)
    ]


def ejecutar_menu_con(respuestas):
    """Recorre el menu respondiendo con una lista fija de opciones."""
    with mock.patch.object(consola, "pedir", side_effect=respuestas), \
            mock.patch.object(consola, "limpiar_pantalla"), \
            mock.patch.object(consola, "pausar"):
        return capturar(menu.ejecutar_menu)


def elegir_en_submenu(respuestas):
    with mock.patch.object(consola, "pedir", side_effect=respuestas), \
            mock.patch.object(consola, "limpiar_pantalla"), \
            mock.patch.object(consola, "pausar"):
        return capturar_con_resultado(menu.crear_sistema)


class PruebasMenuPrincipal(unittest.TestCase):
    def test_ofrece_nueve_opciones(self):
        opciones = opciones_visibles(capturar(menu.mostrar_menu, []))

        self.assertEqual(len(opciones), 9)

    def test_las_opciones_estan_numeradas_del_uno_al_nueve(self):
        opciones = opciones_visibles(capturar(menu.mostrar_menu, []))
        numeros = [opcion.split(".")[0] for opcion in opciones]

        self.assertEqual(numeros, [str(numero) for numero in range(1, 10)])

    def test_incluye_las_opciones_de_sistemas(self):
        opciones = opciones_visibles(capturar(menu.mostrar_menu, []))

        self.assertIn("3. Crear sistema de ecuaciones", opciones)
        self.assertIn("7. Resolver por Gauss", opciones)
        self.assertIn("8. Resolver por Gauss-Jordan", opciones)

    def test_ya_no_ofrece_reducir_la_matriz(self):
        texto = " ".join(opciones_visibles(capturar(menu.mostrar_menu, []))).lower()

        self.assertNotIn("reducir", texto)

    def test_describe_la_matriz_activa(self):
        self.assertEqual(menu.describir_matriz_activa([]), "Sin matriz activa.")
        self.assertEqual(
            menu.describir_matriz_activa([[1, 2, 3], [4, 5, 6]]),
            "Matriz activa de 2 x 3."
        )

    def test_la_opcion_nueve_termina_el_programa(self):
        salida = sin_ansi(ejecutar_menu_con(["9"]))

        self.assertIn("Hasta luego.", salida)

    def test_una_opcion_invalida_avisa_y_sigue(self):
        salida = sin_ansi(ejecutar_menu_con(["99", "9"]))

        self.assertIn("Selección inválida", salida)
        self.assertIn("Hasta luego.", salida)


class PruebasDespachoDeOpciones(unittest.TestCase):
    def test_la_opcion_siete_resuelve_por_gauss(self):
        matriz = [[1, 1, 3], [1, -1, 1]]

        with mock.patch.object(menu, "generador_matriz", return_value=matriz), \
                mock.patch.object(menu, "resolver_por_gauss") as resolver:
            ejecutar_menu_con(["1", "7", "9"])

        resolver.assert_called_once_with(matriz)

    def test_la_opcion_ocho_resuelve_por_gauss_jordan(self):
        matriz = [[1, 1, 3], [1, -1, 1]]

        with mock.patch.object(menu, "generador_matriz", return_value=matriz), \
                mock.patch.object(menu, "resolver_por_gauss_jordan") as resolver:
            ejecutar_menu_con(["1", "8", "9"])

        resolver.assert_called_once_with(matriz)

    def test_un_sistema_creado_pasa_a_ser_la_matriz_activa(self):
        sistema = [[1, -3, -5, 0], [0, 1, 1, 3]]

        with mock.patch.object(menu, "crear_sistema_directo", return_value=sistema), \
                mock.patch.object(menu, "resolver_por_gauss") as resolver:
            ejecutar_menu_con(["3", "1", "7", "9"])

        resolver.assert_called_once_with(sistema)

    def test_volver_del_submenu_conserva_la_matriz_activa(self):
        matriz = [[1, 2], [3, 4]]

        with mock.patch.object(menu, "generador_matriz", return_value=matriz), \
                mock.patch.object(menu, "crear_sistema_directo") as directo, \
                mock.patch.object(menu, "crear_sistema_manual") as manual, \
                mock.patch.object(menu, "mostrar_matriz") as ver:
            ejecutar_menu_con(["1", "3", "3", "6", "9"])

        ver.assert_called_once_with(matriz)
        directo.assert_not_called()
        manual.assert_not_called()

    def test_un_error_al_crear_el_sistema_conserva_la_matriz_activa(self):
        matriz = [[1, 2], [3, 4]]

        with mock.patch.object(menu, "generador_matriz", return_value=matriz), \
                mock.patch.object(menu, "crear_sistema_directo", return_value=None), \
                mock.patch.object(menu, "mostrar_matriz") as ver:
            ejecutar_menu_con(["1", "3", "1", "6", "9"])

        ver.assert_called_once_with(matriz)

    def test_volver_no_crea_una_matriz_vacia(self):
        with mock.patch.object(menu, "mostrar_matriz") as ver:
            ejecutar_menu_con(["3", "3", "6", "9"])

        ver.assert_called_once_with([])


class PruebasSubmenuDeSistemas(unittest.TestCase):
    def test_ofrece_tres_opciones(self):
        opciones = opciones_visibles(capturar(menu.mostrar_submenu_sistemas))

        self.assertEqual(
            opciones,
            [
                "1. Ingresar sistema directamente",
                "2. Ingresar coeficientes manualmente",
                "3. Volver"
            ]
        )

    def test_la_primera_opcion_usa_el_ingreso_directo(self):
        sistema = [[1, 1, 3], [1, -1, 1]]

        with mock.patch.object(
            menu, "crear_sistema_directo", return_value=sistema
        ) as directo:
            matriz, _ = elegir_en_submenu(["1"])

        self.assertEqual(matriz, sistema)
        directo.assert_called_once_with()

    def test_la_segunda_opcion_usa_el_ingreso_manual(self):
        sistema = [[1, -3, -5, 0], [0, 1, 1, 3]]

        with mock.patch.object(
            menu, "crear_sistema_manual", return_value=sistema
        ) as manual:
            matriz, _ = elegir_en_submenu(["2"])

        self.assertEqual(matriz, sistema)
        manual.assert_called_once_with()

    def test_la_tercera_opcion_devuelve_none(self):
        matriz, _ = elegir_en_submenu(["3"])

        self.assertIsNone(matriz)

    def test_una_seleccion_invalida_vuelve_a_preguntar(self):
        matriz, salida = elegir_en_submenu(["7", "3"])

        self.assertIsNone(matriz)
        self.assertIn("Selección inválida", sin_ansi(salida))

    def test_un_error_de_interpretacion_devuelve_none(self):
        with mock.patch.object(menu, "crear_sistema_directo", return_value=None):
            matriz, _ = elegir_en_submenu(["1"])

        self.assertIsNone(matriz)


if __name__ == "__main__":
    unittest.main()
