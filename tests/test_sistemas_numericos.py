"""Núcleo de conversión de bases: resultados, procedimiento y errores."""

import ast
import unittest
from pathlib import Path
from unittest.mock import call, patch

from backend.sistemas_numericos import conversion as conversion_modulo
from backend.sistemas_numericos import (
    base_a_decimal,
    convertir,
    convertir_a_varias_bases,
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
        with self.assertRaisesRegex(ValueError, "no negativos"):
            convertir("-1", 10, 16)
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
        conversion = convertir_a_varias_bases("17", 8, (2, 10, 16))
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
        with patch.object(conversion_modulo, "base_a_decimal", wraps=base_a_decimal) as hacia:
            conversion = convertir_a_varias_bases("13", 10, (2, 8, 16))
        self.assertEqual(hacia.call_count, 0)
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
