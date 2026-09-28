"""Numeración romana (P25): conversión decimal ↔ romano, canonicidad y procedimiento."""

import unittest
from fractions import Fraction
from itertools import product
from unittest.mock import patch

from backend.sistemas_numericos import (
    LONGITUD_ROMANA_MAXIMA,
    GrupoRomano,
    SimboloRomano,
    decimal_a_romano,
    romano_a_decimal,
)
from backend.sistemas_numericos import romanos


CASOS = {
    1: "I", 3: "III", 4: "IV", 9: "IX", 14: "XIV", 40: "XL", 44: "XLIV", 58: "LVIII",
    90: "XC", 400: "CD", 944: "CMXLIV", 1963: "MCMLXIII", 2026: "MMXXVI", 3999: "MMMCMXCIX",
}
INTERVALO = "Ingresa un número entero entre 1 y 3999."
DESORDEN = "los símbolos van de mayor a menor valor y solo se admiten las restas IV, IX, XL, XC, CD y CM."


class PruebasDecimalARomano(unittest.TestCase):
    def test_casos_de_referencia(self):
        for valor, esperado in CASOS.items():
            with self.subTest(valor=valor):
                self.assertEqual(decimal_a_romano(valor).resultado, esperado)

    def test_acepta_la_escritura_decimal_como_texto(self):
        for texto, esperado in (("1963", "MCMLXIII"), (" 58 ", "LVIII"), ("0012", "XII"), ("3999", "MMMCMXCIX")):
            with self.subTest(texto=texto):
                conversion = decimal_a_romano(texto)
                self.assertEqual(conversion.resultado, esperado)
                self.assertIsInstance(conversion.valor, int)

    def test_limites_y_valores_fuera_del_intervalo(self):
        self.assertEqual(decimal_a_romano(1).resultado, "I")
        self.assertEqual(decimal_a_romano(3999).resultado, "MMMCMXCIX")
        casos = (
            (0, "La numeración romana no tiene cero."),
            ("0", "La numeración romana no tiene cero."),
            ("-0", "La numeración romana no tiene cero."),
            (-1, "La numeración romana no tiene números negativos."),
            ("-1", "La numeración romana no tiene números negativos."),
            (4000, "La notación romana convencional llega hasta 3999 (MMMCMXCIX)."),
            ("4000", "La notación romana convencional llega hasta 3999 (MMMCMXCIX)."),
        )
        for valor, mensaje in casos:
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError) as error:
                    decimal_a_romano(valor)
                self.assertEqual(str(error.exception), f"{mensaje} {INTERVALO}")

    def test_solo_enteros_escritos_con_digitos(self):
        for texto in ("", "   ", None):
            with self.subTest(texto=texto), self.assertRaisesRegex(ValueError, f"^{INTERVALO}$"):
                decimal_a_romano(texto)
        # Fracciones, separadores, signos, espacios internos, romanos y dígitos no ASCII.
        for texto in ("3.5", "1.963", "1,5", "1/2", "+5", "--5", "5-", "1 2", "1e3", "XIV", "١٢", "１２"):
            with self.subTest(texto=texto), self.assertRaisesRegex(ValueError, "escrito solo con dígitos"):
                decimal_a_romano(texto)
        for valor in (True, 3.0, Fraction(7, 2), Fraction(4, 1)):
            with self.subTest(valor=valor), self.assertRaisesRegex(ValueError, f"^{INTERVALO}$"):
                decimal_a_romano(valor)

    def test_entrada_absurdamente_larga_se_rechaza_antes_de_leer_cifras(self):
        self.assertEqual(decimal_a_romano("0" * (LONGITUD_ROMANA_MAXIMA - 1) + "7").resultado, "VII")
        with patch.object(romanos, "digito_a_valor", side_effect=AssertionError("leyó cifras")):
            for texto in ("1" * (LONGITUD_ROMANA_MAXIMA + 1), "9" * 100_000):
                with self.subTest(longitud=len(texto)), self.assertRaisesRegex(ValueError, f"^{INTERVALO}$"):
                    decimal_a_romano(texto)

    def test_procedimiento_agrupado_por_ordenes_decimales(self):
        conversion = decimal_a_romano(1963)
        self.assertEqual(
            [(grupo.valor, grupo.simbolos) for grupo in conversion.grupos],
            [(1000, "M"), (900, "CM"), (60, "LX"), (3, "III")],
        )
        # Cada grupo registra las entradas de la tabla canónica que lo forman.
        self.assertEqual(
            [[(parte.simbolos, parte.valor) for parte in grupo.partes] for grupo in conversion.grupos],
            [[("M", 1000)], [("CM", 900)], [("L", 50), ("X", 10)], [("I", 1), ("I", 1), ("I", 1)]],
        )
        self.assertEqual(conversion.grupos[1].partes[0].resta, (1000, 100))
        self.assertIsNone(conversion.grupos[2].partes[0].resta)
        # Los órdenes en cero no aparecen: 2026 = 2000 + 20 + 6.
        self.assertEqual(
            decimal_a_romano(2026).grupos,
            (
                GrupoRomano(2000, "MM", (SimboloRomano("M", 1000), SimboloRomano("M", 1000))),
                GrupoRomano(20, "XX", (SimboloRomano("X", 10), SimboloRomano("X", 10))),
                GrupoRomano(6, "VI", (SimboloRomano("V", 5), SimboloRomano("I", 1))),
            ),
        )
        for valor in (1, 944, 3999):
            with self.subTest(valor=valor):
                grupos = decimal_a_romano(valor).grupos
                self.assertEqual(sum(grupo.valor for grupo in grupos), valor)
                self.assertEqual("".join(grupo.simbolos for grupo in grupos), CASOS[valor])

    def test_tabla_canonica_descendente(self):
        self.assertEqual(
            [(entrada.valor, entrada.simbolos) for entrada in romanos.TABLA],
            [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"),
             (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")],
        )
        restas = {entrada.simbolos: entrada.resta for entrada in romanos.TABLA if entrada.resta}
        self.assertEqual(
            restas,
            {"CM": (1000, 100), "CD": (500, 100), "XC": (100, 10), "XL": (50, 10), "IX": (10, 1), "IV": (5, 1)},
        )


class PruebasRomanoADecimal(unittest.TestCase):
    def test_casos_de_referencia(self):
        for esperado, texto in CASOS.items():
            with self.subTest(texto=texto):
                conversion = romano_a_decimal(texto)
                self.assertEqual(conversion.resultado, esperado)
                self.assertEqual(conversion.texto_normalizado, texto)

    def test_normaliza_minusculas_y_espacios_externos(self):
        conversion = romano_a_decimal("mcmlxiii")
        self.assertEqual(conversion.resultado, 1963)
        self.assertEqual(conversion.texto_normalizado, "MCMLXIII")
        self.assertEqual(conversion.texto_original, "mcmlxiii")
        self.assertEqual(romano_a_decimal("  xLiV \t").resultado, 44)

    def test_lectura_de_izquierda_a_derecha(self):
        conversion = romano_a_decimal("MCMLXIII")
        self.assertEqual(
            [(lectura.simbolos, lectura.valor) for lectura in conversion.lecturas],
            [("M", 1000), ("CM", 900), ("L", 50), ("X", 10), ("I", 1), ("I", 1), ("I", 1)],
        )
        self.assertEqual([lectura.resta for lectura in conversion.lecturas][:2], [None, (1000, 100)])
        self.assertEqual(sum(lectura.valor for lectura in conversion.lecturas), 1963)
        # Cada lectura es una entrada de la misma tabla que usa decimal → romano.
        self.assertTrue(all(lectura in romanos.TABLA for lectura in conversion.lecturas))

    def test_invalidos_de_referencia(self):
        casos = (
            ("", "Ingresa un número romano."),
            ("IIII", "IIII no es una representación romana válida. Para 4 se escribe IV."),
            ("VV", "VV no es una representación romana válida. Para 10 se escribe X."),
            ("IVIV", "IVIV no es una representación romana válida. Para 8 se escribe VIII."),
            ("IC", f"IC no es una representación romana válida: {DESORDEN}"),
            ("IL", f"IL no es una representación romana válida: {DESORDEN}"),
            ("VX", f"VX no es una representación romana válida: {DESORDEN}"),
            ("IIV", f"IIV no es una representación romana válida: {DESORDEN}"),
            ("XM", f"XM no es una representación romana válida: {DESORDEN}"),
            ("MMMM", "MMMM no es una representación romana válida: la notación convencional llega hasta 3999 (MMMCMXCIX)."),
            ("ABC", "«A» no es un símbolo romano. Usa solo I, V, X, L, C, D y M."),
        )
        for texto, mensaje in casos:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError) as error:
                    romano_a_decimal(texto)
                self.assertEqual(str(error.exception), mensaje)

    def test_mas_formas_no_canonicas(self):
        # En orden descendente la lectura es aditiva y se sugiere la escritura canónica.
        for texto, sugerencia in (("XXXX", "Para 40 se escribe XL."), ("VIIII", "Para 9 se escribe IX."),
                                  ("DD", "Para 1000 se escribe M."), ("iiii", "Para 4 se escribe IV."),
                                  ("IXIV", "Para 13 se escribe XIII.")):
            with self.subTest(texto=texto), self.assertRaisesRegex(ValueError, sugerencia):
                romano_a_decimal(texto)
        # Fuera de orden no se sugiere ninguna forma: IC no significa CI.
        for texto in ("IXX", "XCC", "LC", "DM", "IVX", "MCMM"):
            with self.subTest(texto=texto), self.assertRaisesRegex(ValueError, "van de mayor a menor"):
                romano_a_decimal(texto)
        with self.assertRaisesRegex(ValueError, "llega hasta 3999"):
            romano_a_decimal("MMMCMXCIXI")

    def test_caracteres_espacios_y_longitud(self):
        for texto in (None, "   "):
            with self.subTest(texto=texto), self.assertRaisesRegex(ValueError, "^Ingresa un número romano.$"):
                romano_a_decimal(texto)
        for texto in ("X IV", "M\tM", "X V"):
            with self.subTest(texto=texto), self.assertRaisesRegex(ValueError, "sin espacios"):
                romano_a_decimal(texto)
        # Solo I, V, X, L, C, D y M en ASCII: ni Unicode romano ni letras que upper() convierte en I.
        for texto, caracter in (("XIV1", "1"), ("1963", "1"), ("Ⅳ", "Ⅳ"), ("xıv", "ı"), ("<b>", "<"), ("-X", "-")):
            with self.subTest(texto=texto), self.assertRaisesRegex(ValueError, f"«{caracter}» no es un símbolo romano"):
                romano_a_decimal(texto)
        self.assertEqual(romano_a_decimal("MMMDCCCLXXXVIII").resultado, 3888)
        with self.assertRaisesRegex(ValueError, "como máximo 15 símbolos"):
            romano_a_decimal("M" * (LONGITUD_ROMANA_MAXIMA + 1))

    def test_valida_antes_de_leer_o_reconvertir(self):
        with patch.object(romanos, "decimal_a_romano", side_effect=AssertionError("reconvirtió")):
            for texto in ("I" * 100_000, "M" * 16, "ABC", "X V", "IC", "VX", "MMMM"):
                with self.subTest(texto=texto[:20]), self.assertRaises(ValueError):
                    romano_a_decimal(texto)


class PruebasPropiedades(unittest.TestCase):
    def test_ida_y_vuelta_de_1_a_3999(self):
        escrituras = set()
        for valor in range(1, 4000):
            romano = decimal_a_romano(valor).resultado
            self.assertEqual(romano_a_decimal(romano).resultado, valor, romano)
            escrituras.add(romano)
        self.assertEqual(len(escrituras), 3999)
        self.assertEqual(max(len(romano) for romano in escrituras), LONGITUD_ROMANA_MAXIMA)
        self.assertLessEqual(set("".join(escrituras)), set("IVXLCDM"))

    def test_toda_cadena_corta_se_acepta_solo_si_es_canonica(self):
        # 7 + 7² + 7³ + 7⁴ = 2800 cadenas: la lectura acepta exactamente las escrituras canónicas.
        canonicas = {decimal_a_romano(valor).resultado: valor for valor in range(1, 4000)}
        for longitud in range(1, 5):
            for simbolos in product("IVXLCDM", repeat=longitud):
                texto = "".join(simbolos)
                if texto in canonicas:
                    self.assertEqual(romano_a_decimal(texto).resultado, canonicas[texto])
                else:
                    with self.assertRaises(ValueError, msg=texto):
                        romano_a_decimal(texto)


if __name__ == "__main__":
    unittest.main()
