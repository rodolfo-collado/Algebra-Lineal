"""Núcleo de conversión de bases: resultados, procedimiento y errores."""

import ast
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import call, patch

from backend.sistemas_numericos import conversion as conversion_modulo
from backend.sistemas_numericos import (
    base_a_decimal,
    convertir,
    convertir_a_varias_bases,
    decimal_a_base,
    escribir_decimal_exacto,
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


class PruebasConversionEntreBases(unittest.TestCase):
    """`convertir` compone los dos algoritmos: no hay uno por cada par de bases."""

    def test_todos_los_pares_de_bases_distintas(self):
        # 26₁₀ = 11010₂ = 32₈ = 1A₁₆
        escrituras = {2: "11010", 8: "32", 10: "26", 16: "1A"}
        for origen, texto in escrituras.items():
            for destino, esperado in escrituras.items():
                if origen == destino:
                    continue
                with self.subTest(origen=origen, destino=destino):
                    conversion = convertir(texto, origen, destino)
                    self.assertEqual(conversion.resultado, esperado)
                    self.assertEqual(conversion.valor_decimal, 26)

    def test_una_etapa_cuando_interviene_decimal(self):
        desde = convertir("13", 10, 2)
        self.assertIsNone(desde.hacia_decimal)
        self.assertEqual(desde.desde_decimal.resultado, "1101")
        self.assertEqual([type(etapa).__name__ for etapa in desde.etapas], ["ConversionDesdeDecimal"])

        hacia = convertir("1011", 2, 10)
        self.assertIsNone(hacia.desde_decimal)
        self.assertEqual(hacia.hacia_decimal.resultado, 11)
        self.assertEqual(hacia.resultado, "11")
        self.assertEqual([type(etapa).__name__ for etapa in hacia.etapas], ["ConversionHaciaDecimal"])

    def test_dos_etapas_cuando_ninguna_base_es_decimal(self):
        conversion = convertir("1010", 2, 16)
        self.assertEqual(conversion.valor_decimal, 10)
        self.assertEqual(conversion.resultado, "A")
        self.assertEqual(
            [type(etapa).__name__ for etapa in conversion.etapas],
            ["ConversionHaciaDecimal", "ConversionDesdeDecimal"],
        )
        # Etapa 1: expansión posicional 1·2³ + 0·2² + 1·2¹ + 0·2⁰ = 10.
        self.assertEqual([p.contribucion for p in conversion.hacia_decimal.pasos], [8, 0, 2, 0])
        # Etapa 2: 10 ÷ 16 = 0, residuo 10 → A.
        self.assertEqual(
            [(p.dividendo, p.cociente, p.residuo, p.simbolo_residuo) for p in conversion.desde_decimal.pasos],
            [(10, 0, 10, "A")],
        )

    def test_origen_y_destino_deben_ser_distintos(self):
        for base in (2, 8, 10, 16):
            with self.subTest(base=base):
                with self.assertRaisesRegex(ValueError, "deben ser distintas"):
                    convertir("1", base, base)

    def test_reutiliza_la_validacion_existente(self):
        with self.assertRaisesRegex(ValueError, "dígito 2.*binario"):
            convertir("102", 2, 16)
        with self.assertRaisesRegex(ValueError, "Ingresa un número"):
            convertir("   ", 8, 2)
        with self.assertRaisesRegex(ValueError, "al inicio"):
            convertir("--1", 10, 16)
        with self.assertRaisesRegex(ValueError, "base debe ser"):
            convertir("1", 3, 10)
        self.assertEqual(convertir("  ff ", 16, 2).resultado, "11111111")
        self.assertEqual(convertir("0", 8, 16).resultado, "0")


class PruebasConversionMultidestino(unittest.TestCase):
    """`convertir_a_varias_bases` obtiene el decimal una vez y lo reparte entre los destinos pedidos."""

    def test_todos_los_destinos_desde_cada_origen(self):
        # 26₁₀ = 11010₂ = 32₈ = 1A₁₆
        escrituras = {2: "11010", 8: "32", 10: "26", 16: "1A"}
        for origen, texto in escrituras.items():
            destinos = tuple(base for base in (2, 8, 10, 16) if base != origen)
            with self.subTest(origen=origen):
                conversion = convertir_a_varias_bases(texto, origen, destinos)
                self.assertEqual(conversion.valor_decimal, 26)
                self.assertEqual(conversion.bases_destino, destinos)
                self.assertEqual(
                    {d.base_destino: d.resultado for d in conversion.destinos},
                    {base: escrituras[base] for base in destinos},
                )

    def test_el_decimal_se_calcula_una_sola_vez_y_se_reutiliza(self):
        with (
            patch.object(conversion_modulo, "base_a_decimal", wraps=base_a_decimal) as hacia,
            patch.object(conversion_modulo, "decimal_a_base", wraps=decimal_a_base) as desde,
        ):
            conversion = convertir_a_varias_bases("17", 8, (2, 16))
        self.assertEqual(hacia.call_count, 1)
        self.assertEqual(desde.call_args_list, [call(15, 2), call(15, 16)])
        self.assertEqual(conversion.hacia_decimal.resultado, 15)
        self.assertEqual([p.contribucion for p in conversion.hacia_decimal.pasos], [8, 7])
        for destino in conversion.destinos:
            with self.subTest(base=destino.base_destino):
                self.assertEqual(destino.desde_decimal.valor_decimal, 15)
        self.assertEqual([d.resultado for d in conversion.destinos], ["1111", "F"])

    def test_decimal_entre_los_destinos_reutiliza_el_intermedio_sin_segunda_etapa(self):
        with (
            patch.object(conversion_modulo, "base_a_decimal", wraps=base_a_decimal) as hacia,
            patch.object(conversion_modulo, "parsear_decimal", wraps=parsear_decimal) as parseo,
            patch.object(conversion_modulo, "decimal_a_base", wraps=decimal_a_base) as desde,
        ):
            conversion = convertir_a_varias_bases("17", 8, (2, 10, 16))
        # Pedir decimal no añade ninguna llamada: ni una segunda expansión ni un parseo.
        self.assertEqual(hacia.call_count, 1)
        self.assertEqual(parseo.call_count, 0)
        self.assertEqual(desde.call_args_list, [call(15, 2), call(15, 16)])
        decimal = conversion.destinos[1]
        self.assertEqual(decimal.base_destino, 10)
        self.assertEqual(decimal.resultado, "15")
        self.assertIsNone(decimal.desde_decimal)
        self.assertEqual([d.base_destino for d in conversion.destinos if d.desde_decimal], [2, 16])
        # Solo un destino decimal: la escritura es el propio valor intermedio y no hay divisiones.
        solo_decimal = convertir_a_varias_bases("1011", 2, (10,))
        self.assertEqual(solo_decimal.destinos[0].resultado, "11")
        self.assertIsNone(solo_decimal.destinos[0].desde_decimal)
        self.assertEqual(solo_decimal.hacia_decimal.resultado, 11)

    def test_origen_decimal_no_crea_una_etapa_hacia_decimal(self):
        with (
            patch.object(conversion_modulo, "base_a_decimal", wraps=base_a_decimal) as hacia,
            patch.object(conversion_modulo, "parsear_decimal", wraps=parsear_decimal) as parseo,
            patch.object(conversion_modulo, "decimal_a_base", wraps=decimal_a_base) as desde,
        ):
            conversion = convertir_a_varias_bases("13", 10, (2, 8, 16))
        # El decimal se lee una sola vez con `parsear_decimal` y alimenta las tres divisiones.
        self.assertEqual(hacia.call_count, 0)
        self.assertEqual(parseo.call_args_list, [call("13")])
        self.assertEqual(desde.call_args_list, [call(13, 2), call(13, 8), call(13, 16)])
        self.assertIsNone(conversion.hacia_decimal)
        self.assertEqual(conversion.valor_decimal, 13)
        self.assertEqual([d.resultado for d in conversion.destinos], ["1101", "15", "D"])
        self.assertTrue(all(d.desde_decimal for d in conversion.destinos))
        self.assertEqual(
            [(p.dividendo, p.cociente, p.residuo) for p in conversion.destinos[0].desde_decimal.pasos],
            [(13, 6, 1), (6, 3, 0), (3, 1, 1), (1, 0, 1)],
        )

    def test_solo_se_calculan_los_destinos_pedidos_y_en_su_orden(self):
        with patch.object(conversion_modulo, "decimal_a_base", wraps=decimal_a_base) as desde:
            conversion = convertir_a_varias_bases("1A", 16, (2,))
        self.assertEqual(desde.call_args_list, [call(26, 2)])
        self.assertEqual(conversion.bases_destino, (2,))
        self.assertEqual(convertir_a_varias_bases("1A", 16, [8, 2]).bases_destino, (8, 2))

    def test_validaciones_de_los_destinos(self):
        with self.assertRaisesRegex(ValueError, "al menos una base de destino"):
            convertir_a_varias_bases("17", 8, ())
        with self.assertRaisesRegex(ValueError, "no deben repetirse"):
            convertir_a_varias_bases("17", 8, (2, 2))
        with self.assertRaisesRegex(ValueError, "deben ser distintas"):
            convertir_a_varias_bases("17", 8, (2, 8))
        with self.assertRaisesRegex(ValueError, "base debe ser"):
            convertir_a_varias_bases("17", 8, (2, 3))
        with self.assertRaisesRegex(ValueError, "base debe ser"):
            convertir_a_varias_bases("17", 3, (2,))
        # Las bases se comprueban antes que los dígitos del número.
        with self.assertRaisesRegex(ValueError, "deben ser distintas"):
            convertir_a_varias_bases("102", 2, (2,))
        with self.assertRaisesRegex(ValueError, "dígito 2.*binario"):
            convertir_a_varias_bases("102", 2, (8, 16))

    def test_casos_de_referencia_de_p16(self):
        # Un solo destino: el mismo motor que `convertir`.
        individuales = (
            ("13", 10, 2, "1101"), ("13", 10, 8, "15"), ("26", 10, 16, "1A"),
            ("1010", 2, 10, "10"), ("1010", 2, 16, "A"), ("725", 8, 10, "469"), ("FF", 16, 10, "255"),
        )
        for texto, origen, destino, esperado in individuales:
            with self.subTest(texto=texto, origen=origen, destino=destino):
                self.assertEqual(convertir_a_varias_bases(texto, origen, (destino,)).destinos[0].resultado, esperado)
                self.assertEqual(convertir(texto, origen, destino).resultado, esperado)
        # Uno, dos y tres destinos; ceros iniciales, cero y hexadecimal en minúsculas.
        multiples = (
            ("13", 10, (2, 8, 16), ["1101", "15", "D"]),
            ("1010", 2, (8, 10, 16), ["12", "10", "A"]),
            ("725", 8, (2, 10), ["111010101", "469"]),
            ("ff", 16, (2, 8, 10), ["11111111", "377", "255"]),
            ("0017", 8, (2,), ["1111"]),
            ("0", 16, (2, 8, 10), ["0", "0", "0"]),
        )
        for texto, origen, destinos, esperados in multiples:
            with self.subTest(texto=texto, origen=origen, destinos=destinos):
                conversion = convertir_a_varias_bases(texto, origen, destinos)
                self.assertEqual([d.resultado for d in conversion.destinos], esperados)
                self.assertEqual(conversion.bases_destino, destinos)
        cero = convertir_a_varias_bases("0", 16, (2, 8, 10))
        self.assertEqual(cero.valor_decimal, 0)
        self.assertTrue(all(d.desde_decimal.pasos == () for d in cero.destinos if d.desde_decimal))
        with self.assertRaisesRegex(ValueError, "dígito 9.*octal"):
            convertir_a_varias_bases("729", 8, (2, 10, 16))

    def test_convertir_es_el_caso_de_un_solo_destino(self):
        for texto, origen, destino in (("1010", 2, 16), ("13", 10, 2), ("1011", 2, 10)):
            with self.subTest(origen=origen, destino=destino):
                simple = convertir(texto, origen, destino)
                multiple = convertir_a_varias_bases(texto, origen, (destino,))
                (unico,) = multiple.destinos
                self.assertEqual(simple.resultado, unico.resultado)
                self.assertEqual(simple.valor_decimal, multiple.valor_decimal)
                self.assertEqual(simple.hacia_decimal, multiple.hacia_decimal)
                self.assertEqual(simple.desde_decimal, unico.desde_decimal)


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

    def test_signo_solo_al_inicio(self):
        self.assertEqual(normalizar_numero("-13", 10), "-13")
        self.assertEqual(normalizar_numero("-1011", 2), "-1011")
        self.assertEqual(decimal_a_base(-1, 2).resultado, "-1")

    def test_parsear_decimal(self):
        self.assertEqual(parsear_decimal("0"), 0)
        self.assertEqual(parsear_decimal("013"), 13)
        self.assertEqual(parsear_decimal(" 26 "), 26)


class PruebasFraccionarias(unittest.TestCase):
    def test_decimal_a_base_finita_y_periodica(self):
        for texto, base, esperado in (
            ("0.5", 2, "0.1"), ("0.25", 16, "0.4"), ("5.5", 16, "5.8"),
            ("0.31", 16, "0.4(F5C28)"), ("5.31", 2, "101.01(00111101011100001010)"),
        ):
            with self.subTest(texto=texto, base=base):
                self.assertEqual(convertir(texto, 10, base).resultado, esperado)

    def test_procedimientos_exactos_separados(self):
        resultado = decimal_a_base(Fraction(11, 2), 16)
        self.assertEqual(resultado.pasos, decimal_a_base(5, 16).pasos)
        self.assertEqual(resultado.parte_entera, "5")
        self.assertEqual(resultado.parte_no_periodica, "8")
        self.assertEqual(resultado.parte_periodica, "")
        self.assertIsNone(resultado.inicio_periodo)
        paso, = resultado.multiplicaciones
        self.assertEqual((paso.fraccion_inicial, paso.base, paso.producto, paso.digito,
                          paso.simbolo_digito, paso.fraccion_restante),
                         (Fraction(1, 2), 16, 8, 8, "8", 0))
        self.assertEqual(decimal_a_base(Fraction(1, 2), 2).pasos, ())
        self.assertEqual(decimal_a_base(15, 2).multiplicaciones, ())

    def test_periodo_y_preperiodo(self):
        resultado = decimal_a_base(Fraction(31, 100), 16)
        self.assertEqual((resultado.parte_no_periodica, resultado.parte_periodica, resultado.inicio_periodo),
                         ("4", "F5C28", 1))
        self.assertEqual(len(resultado.multiplicaciones), 6)
        self.assertEqual(resultado.multiplicaciones[-1].fraccion_restante,
                         resultado.multiplicaciones[1].fraccion_inicial)
        puro = decimal_a_base(Fraction(1, 3), 2)
        self.assertEqual((puro.resultado, puro.parte_no_periodica, puro.inicio_periodo), ("0.(01)", "", 0))

    def test_base_a_decimal_y_exponentes_negativos(self):
        for texto, base, esperado in (
            ("0.1", 2, "0.5"), ("101.101", 2, "5.625"),
            ("A.F", 16, "10.9375"), ("17.4", 8, "15.5"),
        ):
            with self.subTest(texto=texto):
                resultado = convertir(texto, base, 10)
                self.assertEqual(resultado.resultado, esperado)
                self.assertEqual(resultado.valor_decimal, Fraction(esperado))
        pasos = base_a_decimal("101.101", 2).pasos
        self.assertEqual([p.posicion for p in pasos], [2, 1, 0, -1, -2, -3])
        self.assertEqual([p.potencia for p in pasos], [4, 2, 1, Fraction(1, 2), Fraction(1, 4), Fraction(1, 8)])

    def test_multidestino_reutiliza_el_mismo_valor_exacto(self):
        with (
            patch.object(conversion_modulo, "base_a_decimal", wraps=base_a_decimal) as hacia,
            patch.object(conversion_modulo, "decimal_a_base", wraps=decimal_a_base) as desde,
            patch.object(conversion_modulo, "parsear_decimal", wraps=parsear_decimal) as parseo,
        ):
            resultado = convertir_a_varias_bases("101.101", 2, (10, 8, 16))
        hacia.assert_called_once_with("101.101", 2)
        parseo.assert_not_called()
        self.assertEqual(desde.call_args_list, [call(Fraction(45, 8), 8), call(Fraction(45, 8), 16)])
        self.assertEqual([r.resultado for r in resultado.destinos], ["5.625", "5.5", "5.A"])
        for r in resultado.destinos[1:]:
            self.assertIs(r.desde_decimal.valor_decimal, resultado.valor_decimal)
        self.assertEqual(convertir("A.F", 16, 2).resultado, "1010.1111")
        self.assertEqual(convertir("A.F", 16, 8).resultado, "12.74")
        with patch.object(conversion_modulo, "parsear_decimal", wraps=parsear_decimal) as parseo:
            convertir_a_varias_bases("5.31", 10, (2, 8, 16))
        parseo.assert_called_once_with("5.31")

    def test_normalizacion_y_validacion(self):
        for texto, base, esperado in ((".31", 10, "0.31"), ("5.", 10, "5"),
                                      (" 00.aF ", 16, "00.AF"), ("15", 10, "15")):
            self.assertEqual(normalizar_numero(texto, base), esperado)
        for texto, base in (("1.2.3", 10), (".", 10), ("", 10), ("2.01", 2),
                            ("0.2", 2), ("A.G", 16), ("8.1", 8), ("0.8", 8),
                            ("+0.5", 10), ("0,5", 10), ("1. 2", 10), ("--1", 10)):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                normalizar_numero(texto, base)
        self.assertEqual(normalizar_numero("-0.5", 10), "-0.5")
        self.assertEqual(normalizar_numero("-.31", 10), "-0.31")
        for valor in (0.5, True, "0.5"):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                decimal_a_base(valor, 2)
        self.assertEqual(parsear_decimal(".31"), Fraction(31, 100))
        self.assertEqual(convertir("15", 10, 2).resultado, "1111")
        self.assertEqual(convertir("254", 10, 16).resultado, "FE")
        self.assertEqual(convertir("1111", 2, 10).resultado, "15")

    def test_limite_no_trunca_y_detecta_ciclo_en_el_ultimo_paso(self):
        with patch.object(conversion_modulo, "MAX_PASOS_FRACCIONARIOS", 6):
            self.assertEqual(convertir("0.31", 10, 16).resultado, "0.4(F5C28)")
        with patch.object(conversion_modulo, "MAX_PASOS_FRACCIONARIOS", 5):
            with self.assertRaisesRegex(ValueError, "No se ha truncado ni aproximado"):
                convertir("0.31", 10, 16)
        with patch.object(conversion_modulo, "MAX_PASOS_FRACCIONARIOS", 1):
            self.assertEqual(convertir("0.5", 10, 2).resultado, "0.1")
        with self.assertRaisesRegex(ValueError, "límite de seguridad"):
            convertir("0.00001", 10, 2)

    def test_escritura_decimal_sin_redondeo(self):
        for texto in ("0", "123", "0.00000000000000000001", "12345678901234567890.123456789"):
            self.assertEqual(escribir_decimal_exacto(parsear_decimal(texto)), texto)
        self.assertEqual(escribir_decimal_exacto(Fraction(-1, 8)), "-0.125")
        with self.assertRaises(ValueError):
            escribir_decimal_exacto(Fraction(1, 3))

    def test_expansiones_reconstruyen_el_racional_por_serie_geometrica(self):
        # Una comprobación independiente del algoritmo, para finitos y periódicos.
        for base in (2, 8, 16):
            for denominador in range(2, 40):
                valor = Fraction(denominador + 1, denominador)
                resultado = decimal_a_base(valor, base)
                def evaluar(digitos):
                    return sum(digito_a_valor(d) * base ** i for i, d in enumerate(reversed(digitos)))
                n = len(resultado.parte_no_periodica)
                reconstruido = Fraction(evaluar(resultado.parte_entera))
                reconstruido += Fraction(evaluar(resultado.parte_no_periodica), base ** n)
                if resultado.parte_periodica:
                    k = len(resultado.parte_periodica)
                    reconstruido += Fraction(evaluar(resultado.parte_periodica), base ** n * (base ** k - 1))
                self.assertEqual(reconstruido, valor)


class PruebasNumerosNegativos(unittest.TestCase):
    def test_enteros_conservan_el_signo_en_las_cuatro_bases(self):
        self.assertEqual(convertir("-13", 10, 2).resultado, "-1101")
        self.assertEqual(convertir("-13", 10, 8).resultado, "-15")
        self.assertEqual(convertir("-13", 10, 16).resultado, "-D")
        self.assertEqual(convertir("-1101", 2, 10).resultado, "-13")
        self.assertEqual(convertir("-15", 8, 10).resultado, "-13")
        self.assertEqual(convertir("-D", 16, 10).resultado, "-13")
        pasos = decimal_a_base(-13, 2)
        self.assertEqual(pasos.pasos, decimal_a_base(13, 2).pasos)
        self.assertTrue(all(paso.dividendo > 0 for paso in pasos.pasos))
        self.assertTrue(convertir("-13", 10, 2).negativo)

    def test_fracciones_y_periodo_usan_la_magnitud(self):
        self.assertEqual(convertir("-0.5", 10, 2).resultado, "-0.1")
        self.assertEqual(convertir("-5.5", 10, 16).resultado, "-5.8")
        self.assertEqual(convertir("-101.101", 2, 10).resultado, "-5.625")
        self.assertEqual(convertir("-A.F", 16, 10).resultado, "-10.9375")
        self.assertEqual(parsear_decimal("-5.625"), Fraction(-45, 8))
        self.assertEqual(parsear_decimal("-5"), -5)
        positivo = decimal_a_base(Fraction(31, 100), 16)
        negativo = decimal_a_base(Fraction(-31, 100), 16)
        self.assertEqual(negativo.resultado, "-" + positivo.resultado)
        self.assertEqual(negativo.parte_periodica, positivo.parte_periodica)
        self.assertEqual(negativo.parte_no_periodica, positivo.parte_no_periodica)
        self.assertEqual(negativo.multiplicaciones, positivo.multiplicaciones)
        self.assertTrue(all(paso.fraccion_inicial >= 0 for paso in negativo.multiplicaciones))
        expansion = base_a_decimal("-101.101", 2)
        self.assertEqual(expansion.resultado, Fraction(-45, 8))
        self.assertTrue(all(paso.contribucion >= 0 for paso in expansion.pasos))
        self.assertEqual(sum(paso.contribucion for paso in expansion.pasos), Fraction(45, 8))

    def test_multidestino_calcula_el_decimal_una_vez(self):
        with (
            patch.object(conversion_modulo, "parsear_decimal", wraps=parsear_decimal) as parseo,
            patch.object(conversion_modulo, "decimal_a_base", wraps=decimal_a_base) as desde,
        ):
            conversion = convertir_a_varias_bases("-13", 10, (2, 8, 16))
        parseo.assert_called_once_with("-13")
        self.assertEqual([llamada.args[0] for llamada in desde.call_args_list], [-13, -13, -13])
        self.assertTrue(all(llamada.args[0] is conversion.valor_decimal for llamada in desde.call_args_list))
        self.assertEqual([destino.resultado for destino in conversion.destinos], ["-1101", "-15", "-D"])
        self.assertTrue(conversion.negativo)

        with (
            patch.object(conversion_modulo, "base_a_decimal", wraps=base_a_decimal) as hacia,
            patch.object(conversion_modulo, "decimal_a_base", wraps=decimal_a_base) as desde,
        ):
            conversion = convertir_a_varias_bases("-101.101", 2, (10, 8, 16))
        hacia.assert_called_once_with("-101.101", 2)
        self.assertEqual(desde.call_count, 2)
        self.assertTrue(all(llamada.args[0] is conversion.valor_decimal for llamada in desde.call_args_list))
        self.assertEqual(
            [destino.resultado for destino in conversion.destinos],
            ["-5.625", "-5.5", "-5.A"],
        )

    def test_cero_negativo_se_escribe_sin_signo(self):
        for texto, base in (("-0", 10), ("-0.0", 8), ("-000", 2), ("-000.000", 16)):
            with self.subTest(texto=texto, base=base):
                conversion = convertir_a_varias_bases(
                    texto, base, tuple(destino for destino in (2, 8, 10, 16) if destino != base)
                )
                self.assertEqual(conversion.valor_decimal, 0)
                self.assertFalse(conversion.negativo)
                self.assertTrue(all(destino.resultado == "0" for destino in conversion.destinos))

    def test_sintaxis_invalida_y_regresiones_positivas(self):
        for texto, base in (
            ("-", 10), ("+", 10), ("+13", 10), ("--13", 10), ("+-13", 10),
            ("-+13", 10), ("1-3", 10), ("10-", 10), ("A-F", 16), ("-.", 10),
        ):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                normalizar_numero(texto, base)
        for texto, base, esperado in (
            ("13", 10, "13"), ("0.31", 10, "0.31"), ("101.101", 2, "101.101"),
            ("A.F", 16, "A.F"), (".5", 10, "0.5"), ("5.", 10, "5"),
            ("-13", 10, "-13"), ("-0.31", 10, "-0.31"), ("-.31", 10, "-0.31"),
            ("-5.", 10, "-5"), ("-101.101", 2, "-101.101"), ("-a.f", 16, "-A.F"),
        ):
            with self.subTest(texto=texto):
                self.assertEqual(normalizar_numero(texto, base), esperado)
        self.assertEqual(convertir("13", 10, 2).resultado, "1101")
        self.assertEqual(convertir("0.31", 10, 16).resultado, "0.4(F5C28)")
        self.assertEqual(convertir("101.101", 2, 10).resultado, "5.625")
        self.assertEqual(convertir("A.F", 16, 10).resultado, "10.9375")
        self.assertFalse(convertir("13", 10, 2).negativo)


class PruebasSinConversionesAutomaticas(unittest.TestCase):
    def test_el_modulo_no_usa_bin_oct_hex_ni_int_con_base(self):
        prohibidas = []
        for ruta in RAIZ_MODULO.rglob("*.py"):
            arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Call):
                    if isinstance(nodo.func, ast.Name) and nodo.func.id in {"bin", "oct", "hex", "float"}:
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
