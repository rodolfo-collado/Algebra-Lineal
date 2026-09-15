"""Núcleo de conversión de bases: resultados, procedimiento y errores."""

import ast
import unittest
from pathlib import Path

from backend.sistemas_numericos import (
    base_a_decimal,
    decimal_a_base,
    digito_a_valor,
    normalizar_numero,
    parsear_decimal,
    potencia_entera,
    simbolo_de_valor,
    validar_base,
)


RAIZ_MODULO = Path(__file__).resolve().parents[1] / "backend" / "sistemas_numericos"


class PruebasDigitos(unittest.TestCase):
    def test_equivalencia_hexadecimal(self):
        self.assertEqual(simbolo_de_valor(10), "A")
        self.assertEqual(simbolo_de_valor(15), "F")
        self.assertEqual(digito_a_valor("A"), 10)
        self.assertEqual(digito_a_valor("f"), 15)
        self.assertEqual(digito_a_valor("F"), 15)

    def test_potencia_entera_por_multiplicaciones(self):
        self.assertEqual(potencia_entera(2, 0), 1)
        self.assertEqual(potencia_entera(2, 3), 8)
        self.assertEqual(potencia_entera(16, 1), 16)
        self.assertEqual(potencia_entera(8, 2), 64)


class PruebasDecimalABase(unittest.TestCase):
    def test_decimal_a_binario(self):
        casos = {0: "0", 1: "1", 2: "10", 10: "1010", 13: "1101", 26: "11010"}
        for valor, esperado in casos.items():
            with self.subTest(valor=valor):
                self.assertEqual(decimal_a_base(valor, 2).resultado, esperado)

    def test_decimal_a_octal(self):
        casos = {0: "0", 8: "10", 10: "12", 26: "32"}
        for valor, esperado in casos.items():
            with self.subTest(valor=valor):
                self.assertEqual(decimal_a_base(valor, 8).resultado, esperado)

    def test_decimal_a_hexadecimal(self):
        casos = {0: "0", 10: "A", 15: "F", 16: "10", 26: "1A", 255: "FF"}
        for valor, esperado in casos.items():
            with self.subTest(valor=valor):
                self.assertEqual(decimal_a_base(valor, 16).resultado, esperado)

    def test_procedimiento_13_a_binario(self):
        conversion = decimal_a_base(13, 2)
        self.assertEqual(
            [(p.dividendo, p.cociente, p.residuo, p.simbolo_residuo) for p in conversion.pasos],
            [
                (13, 6, 1, "1"),
                (6, 3, 0, "0"),
                (3, 1, 1, "1"),
                (1, 0, 1, "1"),
            ],
        )
        self.assertEqual(conversion.resultado, "1101")

    def test_procedimiento_26_a_hexadecimal_sustituye_diez_por_A(self):
        conversion = decimal_a_base(26, 16)
        self.assertEqual(conversion.pasos[0].residuo, 10)
        self.assertEqual(conversion.pasos[0].simbolo_residuo, "A")
        self.assertEqual(conversion.pasos[1].residuo, 1)
        self.assertEqual(conversion.pasos[1].simbolo_residuo, "1")
        self.assertEqual(conversion.resultado, "1A")

    def test_cero_no_genera_pasos_de_division(self):
        conversion = decimal_a_base(0, 2)
        self.assertEqual(conversion.resultado, "0")
        self.assertEqual(conversion.pasos, ())


class PruebasBaseADecimal(unittest.TestCase):
    def test_binario_a_decimal(self):
        casos = {"0": 0, "1": 1, "1011": 11, "11010": 26}
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(base_a_decimal(texto, 2).resultado, esperado)

    def test_octal_a_decimal(self):
        casos = {"10": 8, "17": 15, "32": 26}
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(base_a_decimal(texto, 8).resultado, esperado)

    def test_hexadecimal_a_decimal(self):
        casos = {"A": 10, "F": 15, "10": 16, "1A": 26, "FF": 255, "1a": 26, "ff": 255}
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(base_a_decimal(texto, 16).resultado, esperado)

    def test_combinacion_lineal_1011_binario(self):
        conversion = base_a_decimal("1011", 2)
        terminos = [
            (p.digito, p.valor, p.posicion, p.potencia, p.contribucion)
            for p in conversion.pasos
        ]
        self.assertEqual(
            terminos,
            [
                ("1", 1, 3, 8, 8),
                ("0", 0, 2, 4, 0),
                ("1", 1, 1, 2, 2),
                ("1", 1, 0, 1, 1),
            ],
        )
        self.assertEqual(conversion.resultado, 11)

    def test_combinacion_lineal_157_octal(self):
        conversion = base_a_decimal("157", 8)
        self.assertEqual(
            [(p.valor, p.potencia, p.contribucion) for p in conversion.pasos],
            [(1, 64, 64), (5, 8, 40), (7, 1, 7)],
        )
        self.assertEqual(conversion.resultado, 111)

    def test_combinacion_lineal_1A_hexadecimal(self):
        conversion = base_a_decimal("1A", 16)
        self.assertEqual(conversion.pasos[1].digito, "A")
        self.assertEqual(conversion.pasos[1].valor, 10)
        self.assertEqual(
            [(p.valor, p.potencia, p.contribucion) for p in conversion.pasos],
            [(1, 16, 16), (10, 1, 10)],
        )
        self.assertEqual(conversion.resultado, 26)

    def test_ceros_iniciales_no_cambian_el_valor(self):
        self.assertEqual(base_a_decimal("001011", 2).resultado, 11)
        self.assertEqual(base_a_decimal("00", 8).resultado, 0)


class PruebasValidacion(unittest.TestCase):
    def test_digitos_invalidos(self):
        with self.assertRaisesRegex(ValueError, "dígito 2.*binario"):
            normalizar_numero("102", 2)
        with self.assertRaisesRegex(ValueError, "dígito 8.*octal"):
            normalizar_numero("89", 8)
        with self.assertRaisesRegex(ValueError, "dígito 9.*octal"):
            normalizar_numero("19", 8)
        with self.assertRaisesRegex(ValueError, "G no es un dígito hexadecimal"):
            normalizar_numero("1G", 16)

    def test_entrada_vacia_y_espacios(self):
        with self.assertRaisesRegex(ValueError, "Ingresa un número"):
            normalizar_numero("", 10)
        with self.assertRaisesRegex(ValueError, "Ingresa un número"):
            normalizar_numero("   ", 2)
        self.assertEqual(normalizar_numero("  1011  ", 2), "1011")
        with self.assertRaisesRegex(ValueError, "espacios"):
            normalizar_numero("10 11", 2)

    def test_hexadecimal_minusculas_se_normalizan(self):
        self.assertEqual(normalizar_numero("1a", 16), "1A")
        self.assertEqual(normalizar_numero("ff", 16), "FF")

    def test_base_invalida(self):
        with self.assertRaisesRegex(ValueError, "base debe ser"):
            validar_base(3)
        with self.assertRaisesRegex(ValueError, "base debe ser"):
            decimal_a_base(10, 3)

    def test_caracteres_arbitrarios(self):
        with self.assertRaises(ValueError):
            normalizar_numero("12$", 10)
        with self.assertRaises(ValueError):
            normalizar_numero("hola", 16)

    def test_negativos_rechazados(self):
        with self.assertRaisesRegex(ValueError, "no negativos"):
            normalizar_numero("-13", 10)
        with self.assertRaisesRegex(ValueError, "no negativos"):
            decimal_a_base(-1, 2)
        with self.assertRaisesRegex(ValueError, "no negativos"):
            normalizar_numero("-1011", 2)

    def test_parsear_decimal(self):
        self.assertEqual(parsear_decimal("0"), 0)
        self.assertEqual(parsear_decimal("013"), 13)
        self.assertEqual(parsear_decimal(" 26 "), 26)


class PruebasSinConversionesAutomaticas(unittest.TestCase):
    def test_el_modulo_no_usa_bin_oct_hex_ni_int_con_base(self):
        prohibidas = []
        for ruta in RAIZ_MODULO.rglob("*.py"):
            arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Call):
                    if isinstance(nodo.func, ast.Name) and nodo.func.id in {"bin", "oct", "hex"}:
                        prohibidas.append(f"{ruta.name}:{nodo.lineno} {nodo.func.id}()")
                    if (
                        isinstance(nodo.func, ast.Name)
                        and nodo.func.id == "int"
                        and len(nodo.args) >= 2
                    ):
                        prohibidas.append(f"{ruta.name}:{nodo.lineno} int(..., base)")
        self.assertEqual(prohibidas, [])


if __name__ == "__main__":
    unittest.main()
