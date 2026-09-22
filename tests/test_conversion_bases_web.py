"""Integración web de Conversión de bases (P11) y de las conversiones multidestino (P16)."""

import os
import re
from pathlib import Path
from fractions import Fraction
from unittest.mock import call, patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase
from django.urls import resolve, reverse
from django.utils.html import strip_tags

from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms import ConversionBasesForm
from frontend.web.calculadora.servicios_bases import convertir_entrada, enumerar, titulo_conversion
from tests.test_interfaz_progresiva import Formulario
from tests.test_navegacion import Documento
from tests.test_teclado import Pagina
from backend.sistemas_numericos import conversion as motor

STATIC = Path(__file__).resolve().parents[1] / "frontend" / "web" / "calculadora" / "static" / "calculadora"
NOMBRES = ("Binario", "Octal", "Decimal", "Hexadecimal")


def texto_plano(respuesta):
    return " ".join(strip_tags(respuesta.content.decode("utf-8")).split())


def resultados_de(respuesta):
    """(origen, [(escritura, base), …]) tal como los lee el panel Resultado, en su orden."""
    texto = texto_plano(respuesta)
    seccion = texto[texto.index("Resultado Número de origen: "):texto.index(" Procedimiento")]
    origen = seccion.split("Número de origen: ")[1].split(" ")[0]
    escrituras = re.findall(rf"= (\S+) ({'|'.join(NOMBRES)})", seccion)
    return origen, escrituras


class PruebasConversionBasesWeb(SimpleTestCase):
    def setUp(self):
        self.ruta = reverse("calculadora:conversion-bases")
        self.herramienta = catalogo.herramienta_por_id("conversion-bases")

    def convertir(self, numero, origen, destinos):
        """POST como el del navegador: una casilla `bases_destino` por destino marcado."""
        if isinstance(destinos, int):
            destinos = (destinos,)
        return self.client.post(self.ruta, {
            "numero": numero,
            "base_origen": str(origen),
            "bases_destino": [str(destino) for destino in destinos],
        })

    def casillas_destino(self, respuesta):
        return [c for c in Documento(respuesta).controles if c.get("name") == "bases_destino"]

    def test_registro_central_disponible(self):
        self.assertIsNotNone(self.herramienta)
        self.assertTrue(self.herramienta.disponible)
        self.assertEqual(self.herramienta.nombre, "Conversión de bases")
        self.assertEqual(self.herramienta.categoria, catalogo.BASES_NUMERICAS)
        self.assertEqual(self.herramienta.ruta, self.ruta)
        self.assertEqual(resolve(self.ruta).view_name, "calculadora:conversion-bases")
        for clave in ("binario", "hexadecimal", "conversión", "sistemas numéricos", "bases"):
            self.assertIn(clave, self.herramienta.palabras_clave)
        self.assertEqual(
            [h.id for h in catalogo.herramientas_de(catalogo.BASES_NUMERICAS)], ["conversion-bases"],
        )

    def test_aparece_en_inicio_sidebar_y_busqueda(self):
        self.assertContains(self.client.get("/"), "Conversión de bases")
        self.assertContains(self.client.get("/"), self.ruta)

        documento = Documento(self.client.get("/"))
        hrefs = [attrs.get("href") for attrs in documento.enlaces_en("Herramientas")]
        self.assertIn(self.ruta, hrefs)

        for consulta in ("sistemas numéricos", "conversión", "binario", "hexadecimal"):
            with self.subTest(consulta=consulta):
                respuesta = self.client.get("/", {"q": consulta})
                self.assertContains(respuesta, "Conversión de bases")
                self.assertContains(respuesta, self.ruta)

    def test_get_breadcrumbs_y_sin_relacionadas(self):
        respuesta = self.client.get(self.ruta)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Sistemas numéricos")
        self.assertContains(respuesta, "Bases numéricas")
        self.assertContains(respuesta, "Conversión de bases")
        self.assertContains(respuesta, 'name="csrfmiddlewaretoken"', html=False)
        self.assertNotContains(respuesta, "Herramientas relacionadas")
        self.assertNotContains(respuesta, "Continúa con este mismo sistema")
        self.assertNotContains(respuesta, "related-list")

    def test_un_selector_de_origen_y_casillas_reales_para_los_destinos(self):
        respuesta = self.client.get(self.ruta)
        html = respuesta.content.decode("utf-8")
        # Una única base de origen, en un selector compacto con las cuatro bases.
        self.assertIn('<select name="base_origen" class="field-select"', html)
        for valor, etiqueta in ((2, "Binario"), (8, "Octal"), (10, "Decimal"), (16, "Hexadecimal")):
            self.assertRegex(html, rf'<option value="{valor}"[^>]*>{etiqueta}</option>')
        self.assertRegex(html, r'name="base_origen"[\s\S]*?<option value="10" selected>Decimal</option>')
        # Ya no hay un único destino, ni botón de intercambio, ni botones por par de bases.
        self.assertNotIn('name="base_destino"', html)
        self.assertNotIn("data-intercambiar-bases", html)
        self.assertNotIn("base-swap", html)
        self.assertNotIn("⇄", html)
        for par in ("Binario → Decimal", "Octal → Binario", "Hexadecimal → Octal"):
            self.assertNotIn(f">{par}<", html)
        # «Convertir a»: fieldset + legend y una casilla real por base, en orden fijo,
        # cada una dentro de su label y descrita por la ayuda y los errores del grupo.
        self.assertRegex(html, r'<fieldset class="choice-fieldset base-targets" data-destinos aria-describedby="destinos-ayuda destinos-aviso destinos-errores">\s*<legend>Convertir a</legend>')
        casillas = self.casillas_destino(respuesta)
        self.assertEqual([c["type"] for c in casillas], ["checkbox"] * 4)
        self.assertEqual([c["value"] for c in casillas], ["2", "8", "10", "16"])
        self.assertEqual(
            [c["id"] for c in casillas],
            ["id_bases_destino_0", "id_bases_destino_1", "id_bases_destino_2", "id_bases_destino_3"],
        )
        for valor, etiqueta in zip(("2", "8", "10", "16"), NOMBRES):
            self.assertRegex(
                html,
                rf'<label class="option" data-destino-base="{valor}"><input type="checkbox" name="bases_destino" value="{valor}" id="id_bases_destino_\d"( checked)?><span>{etiqueta}</span></label>',
            )
        # Predeterminado: decimal → binario, como hasta ahora. El servidor no oculta ni
        # desactiva ninguna casilla: sin JavaScript se ven las cuatro y él rechaza origen = destino.
        self.assertEqual([c["value"] for c in casillas if "checked" in c], ["2"])
        self.assertEqual([c for c in casillas if "disabled" in c], [])
        self.assertNotIn('data-destino-base="10" hidden', html)
        documento = Documento(respuesta)
        self.assertIn("destinos-ayuda", documento.ids)
        self.assertIn("destinos-aviso", documento.ids)
        self.assertIn("destinos-errores", documento.ids)
        self.assertIn('id="destinos-ayuda" class="field-help option-help">Marca una, varias o todas las demás bases.', html)
        # Aviso en vivo de destinos, vacío hasta que JavaScript lo use.
        self.assertIn('id="destinos-aviso" class="field-error" data-validacion-destinos role="alert" hidden', html)
        # Sin tarjetas grandes para elegir la base ni el modo.
        self.assertNotIn('name="modo"', html)
        self.assertNotIn('name="base"', html)
        self.assertNotIn('class="choice"', html)

    def test_teclado_y_etiqueta_siguen_a_la_base_de_origen(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        pagina = Pagina(html)
        self.assertEqual(len(pagina.teclados), 1)
        self.assertEqual(set(pagina.perfiles_publicados), {"base-2", "base-8", "base-10", "base-16"})
        self.assertIn("calculadora/teclado.js", html)
        self.assertIn("calculadora/conversion.js", html)
        self.assertEqual(pagina.contenedores["number-fields"], "base-10")
        self.assertRegex(html, r'<span data-number-label-base="10"\s*>Número decimal</span>')
        self.assertRegex(html, r'data-number-label-base="2"[^>]*hidden[^>]*>Número binario<')
        self.assertEqual(pagina.json["bases-digitos"]["16"]["digitos"], list("0123456789ABCDEF."))
        # Aviso de validación en vivo, vacío hasta que JavaScript lo use.
        self.assertIn('data-validacion-cliente role="alert" hidden', html)

    def test_cambio_de_origen_actualiza_teclado_y_etiqueta_y_conserva_las_casillas_sin_javascript(self):
        respuesta = self.convertir("", 16, 2)
        html = respuesta.content.decode("utf-8")
        self.assertEqual(Pagina(html).contenedores["number-fields"], "base-16")
        self.assertEqual(len(Pagina(html).teclados), 1)
        self.assertRegex(html, r'<span data-number-label-base="16"\s*>Número hexadecimal</span>')
        self.assertRegex(html, r'data-number-label-base="10"[^>]*hidden')
        # Las casillas vuelven tal como se enviaron: binario marcado y las cuatro disponibles.
        casillas = self.casillas_destino(respuesta)
        self.assertEqual([c["value"] for c in casillas if "checked" in c], ["2"])
        self.assertEqual([c for c in casillas if "disabled" in c], [])
        self.assertNotRegex(html.split("base-targets")[1].split("</fieldset>")[0], r"<label[^>]*hidden")

    def test_sin_javascript_el_origen_marcado_como_destino_se_explica_y_se_puede_corregir(self):
        # Sin JavaScript nadie oculta la casilla del origen: si el usuario la deja marcada y
        # cambia el origen a esa misma base, el servidor lo rechaza y la casilla sigue a la
        # vista, marcada, para que pueda desmarcarla; con otra base ya marcada se resuelve.
        respuesta = self.convertir("101", 2, (2, 16))
        self.assertContains(respuesta, "La base de origen y la base de destino deben ser distintas.")
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertEqual([c["value"] for c in self.casillas_destino(respuesta) if "checked" in c], ["2", "16"])
        self.assertEqual([c for c in self.casillas_destino(respuesta) if "disabled" in c], [])
        origen, escrituras = resultados_de(self.convertir("101", 2, 16))
        self.assertEqual((origen, escrituras), ("101₂", [("5₁₆", "Hexadecimal")]))

    def test_el_envio_por_defecto_del_formulario_convierte_decimal_a_binario(self):
        formulario = Formulario(self.client.get(self.ruta).content.decode("utf-8"), "conversion-form")
        # El ayudante solo lee input y textarea: la base de origen (select) viaja con su valor inicial.
        self.assertEqual({nombre for nombre, _ in formulario.datos}, {"csrfmiddlewaretoken", "numero", "bases_destino"})
        datos = formulario.como_datos(numero="13", base_origen="10")
        self.assertEqual(datos["bases_destino"], ["2"])
        respuesta = self.client.post(self.ruta, datos)
        self.assertEqual(resultados_de(respuesta), ("13₁₀", [("1101₂", "Binario")]))
        self.assertContains(respuesta, "Decimal → binario")

    def test_el_campo_del_numero_es_de_una_linea(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        self.assertIn('class="field-input field-input-numeral"', html)
        self.assertIn(f'maxlength="{ConversionBasesForm.LONGITUD_MAXIMA}"', html)
        self.assertNotIn("field-input-code", html)
        self.assertNotIn("<textarea", html)

    def test_todos_los_pares_de_bases_distintas(self):
        # 26₁₀ = 11010₂ = 32₈ = 1A₁₆
        escrituras = {2: "11010", 8: "32", 10: "26", 16: "1A"}
        subindices = {2: "₂", 8: "₈", 10: "₁₀", 16: "₁₆"}
        nombres = {2: "Binario", 8: "Octal", 10: "Decimal", 16: "Hexadecimal"}
        for origen, numero in escrituras.items():
            for destino, esperado in escrituras.items():
                if origen == destino:
                    continue
                with self.subTest(origen=origen, destino=destino):
                    respuesta = self.convertir(numero, origen, destino)
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertEqual(
                        resultados_de(respuesta),
                        (f"{numero}{subindices[origen]}", [(f"{esperado}{subindices[destino]}", nombres[destino])]),
                    )
                    self.assertContains(respuesta, "Procedimiento")

    def test_cada_origen_a_todas_las_demas_bases(self):
        escrituras = {2: "11010", 8: "32", 10: "26", 16: "1A"}
        subindices = {2: "₂", 8: "₈", 10: "₁₀", 16: "₁₆"}
        nombres = {2: "Binario", 8: "Octal", 10: "Decimal", 16: "Hexadecimal"}
        for origen, numero in escrituras.items():
            destinos = [base for base in (2, 8, 10, 16) if base != origen]
            with self.subTest(origen=origen):
                origen_leido, leidas = resultados_de(self.convertir(numero, origen, destinos))
                self.assertEqual(origen_leido, f"{numero}{subindices[origen]}")
                self.assertEqual(leidas, [(f"{escrituras[b]}{subindices[b]}", nombres[b]) for b in destinos])

    def test_casos_de_referencia_de_p16(self):
        casos = (
            ("725", 8, (10,), "725₈", [("469₁₀", "Decimal")]),
            ("725", 8, (2, 10), "725₈", [("111010101₂", "Binario"), ("469₁₀", "Decimal")]),
            ("725", 8, (2, 10, 16), "725₈", [("111010101₂", "Binario"), ("469₁₀", "Decimal"), ("1D5₁₆", "Hexadecimal")]),
            ("1010", 2, (8, 10, 16), "1010₂", [("12₈", "Octal"), ("10₁₀", "Decimal"), ("A₁₆", "Hexadecimal")]),
            ("ff", 16, (2, 8, 10), "FF₁₆", [("11111111₂", "Binario"), ("377₈", "Octal"), ("255₁₀", "Decimal")]),
            ("13", 10, (8,), "13₁₀", [("15₈", "Octal")]),
            ("0", 8, (2, 10, 16), "0₈", [("0₂", "Binario"), ("0₁₀", "Decimal"), ("0₁₆", "Hexadecimal")]),
            ("0017", 8, (2,), "17₈", [("1111₂", "Binario")]),
        )
        for numero, origen, destinos, origen_esperado, esperadas in casos:
            with self.subTest(numero=numero, origen=origen, destinos=destinos):
                respuesta = self.convertir(numero, origen, destinos)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(resultados_de(respuesta), (origen_esperado, esperadas))

    def test_origen_como_destino_no_se_permite(self):
        for base in (2, 8, 10, 16):
            with self.subTest(base=base):
                for destinos in ((base,), (base, 2 if base != 2 else 8)):
                    respuesta = self.convertir("1", base, destinos)
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertContains(respuesta, "La base de origen y la base de destino deben ser distintas.")
                    self.assertNotContains(respuesta, 'id="resultado"')

    def test_hace_falta_al_menos_un_destino(self):
        respuesta = self.client.post(self.ruta, {"numero": "13", "base_origen": "10"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Elige al menos una base de destino.")
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertNotContains(respuesta, "Este campo es obligatorio")

    def test_destinos_desordenados_se_ordenan_como_las_casillas(self):
        respuesta = self.convertir("13", 10, (16, 2))
        self.assertContains(respuesta, "Decimal → binario y hexadecimal")
        self.assertEqual(resultados_de(respuesta), ("13₁₀", [("1101₂", "Binario"), ("D₁₆", "Hexadecimal")]))
        texto = texto_plano(respuesta)
        self.assertEqual(texto.count("Decimal → hexadecimal"), 1)

    def test_contrato_http_estricto(self):
        """Envíos manipulados: se rechazan con un mensaje claro, sin resultado ni traceback."""
        casos = (
            ({"numero": "13", "base_origen": "10", "bases_destino": ["2", "2"]}, "Las bases de destino no deben repetirse."),
            ({"numero": "13", "base_origen": "10", "bases_destino": ["2", "16", "2"]}, "Las bases de destino no deben repetirse."),
            ({"numero": "13", "base_origen": "10", "bases_destino": ["2"], "extra": "1"}, "no forman parte del formulario"),
            ({"numero": ["13", "14"], "base_origen": "10", "bases_destino": ["2"]}, "hay campos repetidos"),
            ({"numero": "13", "base_origen": ["10", "8"], "bases_destino": ["2"]}, "hay campos repetidos"),
            ({"numero": "13", "base_origen": "3", "bases_destino": ["2"]}, "no es una de las opciones disponibles"),
            ({"numero": "13", "base_origen": "abc", "bases_destino": ["2"]}, "no es una de las opciones disponibles"),
            ({"numero": "13", "base_origen": "10", "bases_destino": ["3"]}, "no es una de las opciones disponibles"),
            ({"numero": "13", "base_origen": "10", "bases_destino": ["2", "3"]}, "no es una de las opciones disponibles"),
            ({"numero": "13", "base_origen": "10", "bases_destino": ["<b>x</b>"]}, "no es una de las opciones disponibles"),
            ({"numero": "1" * 129, "base_origen": "10", "bases_destino": ["2"]}, "El número no puede tener más de 128 caracteres."),
            ({"numero": "102", "base_origen": "2", "bases_destino": ["8"]}, "El dígito 2 no es válido en un número binario."),
            ({"numero": "<script>alert(1)</script>", "base_origen": "10", "bases_destino": ["2"]}, "no es válido en un número decimal"),
        )
        for datos, mensaje in casos:
            with self.subTest(datos=datos):
                respuesta = self.client.post(self.ruta, datos)
                self.assertEqual(respuesta.status_code, 200)
                self.assertIn(mensaje, texto_plano(respuesta))
                self.assertNotContains(respuesta, 'id="resultado"')
                self.assertNotContains(respuesta, "Traceback")
                self.assertNotContains(respuesta, "<script>alert")
                self.assertNotContains(respuesta, "<b>x</b>")
        # El tope es inclusivo y las casillas repetidas legítimas (una por base) siguen valiendo.
        self.assertContains(self.convertir("1" * 128, 2, 10), "Procedimiento")
        self.assertContains(self.convertir("13", 10, (2, 8, 16)), "Procedimiento")

    def test_decimal_a_binario_en_una_etapa(self):
        respuesta = self.convertir("13", 10, 2)
        self.assertEqual(resultados_de(respuesta), ("13₁₀", [("1101₂", "Binario")]))
        self.assertContains(respuesta, "Decimal → binario")
        self.assertContains(respuesta, "13 ÷ 2")
        self.assertContains(respuesta, "residuos se leen")
        self.assertNotContains(respuesta, "Etapa 1")
        self.assertNotContains(respuesta, "pasa por decimal")
        self.assertNotContains(respuesta, "etapa intermedia")
        self.assertNotContains(respuesta, "Expansión posicional")

    def test_decimal_a_hexadecimal_sustituye_diez_por_a(self):
        respuesta = self.convertir("26", 10, 16)
        self.assertEqual(resultados_de(respuesta), ("26₁₀", [("1A₁₆", "Hexadecimal")]))
        self.assertContains(respuesta, "10 → A")

    def test_binario_a_decimal_muestra_la_combinacion_lineal(self):
        respuesta = self.convertir("1011", 2, 10)
        self.assertEqual(resultados_de(respuesta), ("1011₂", [("11₁₀", "Decimal")]))
        self.assertContains(respuesta, "Binario → decimal")
        self.assertContains(respuesta, "1·2")
        self.assertContains(respuesta, "<sup>3</sup>", html=False)
        self.assertContains(respuesta, "8 + 0 + 2 + 1")
        self.assertNotContains(respuesta, "Etapa 1")
        self.assertNotContains(respuesta, "Divisiones sucesivas")
        self.assertNotContains(respuesta, "decimal intermedio")
        self.assertNotContains(respuesta, "se reutiliza")

    def test_hexadecimal_a_decimal_en_minusculas(self):
        respuesta = self.convertir("1a", 16, 10)
        self.assertEqual(resultados_de(respuesta), ("1A₁₆", [("26₁₀", "Decimal")]))
        self.assertContains(respuesta, "Hexadecimal → decimal")
        self.assertContains(respuesta, "A = 10")

    def test_binario_a_hexadecimal_en_dos_etapas(self):
        respuesta = self.convertir("1010", 2, 16)
        texto = texto_plano(respuesta)
        self.assertEqual(resultados_de(respuesta), ("1010₂", [("A₁₆", "Hexadecimal")]))
        self.assertIn("pasa por decimal", texto)
        self.assertIn("escriben la base pedida.", texto)
        self.assertNotIn("uno de los resultados pedidos", texto)
        # La ruta muestra el decimal intermedio una vez y la única rama que sale de él.
        self.assertIn("1010₂ → 10₁₀ decimal intermedio → A₁₆", texto)
        self.assertIn("Etapa 1 · Binario → decimal", texto)
        self.assertIn("Etapa 2 · Decimal → hexadecimal", texto)
        self.assertLess(texto.index("Etapa 1"), texto.index("Etapa 2"))
        # Las dos matemáticas de siempre, en orden: expansión y después divisiones.
        self.assertLess(texto.index("Expansión posicional"), texto.index("Divisiones sucesivas"))
        self.assertIn("8 + 0 + 2 + 0", texto)
        self.assertIn("10 ÷ 16", texto)
        self.assertIn("10 → A", texto)
        self.assertIn("Este valor decimal se reutiliza en las etapas siguientes", texto)

    def test_octal_a_binario_en_dos_etapas(self):
        respuesta = self.convertir("17", 8, 2)
        texto = texto_plano(respuesta)
        self.assertEqual(resultados_de(respuesta), ("17₈", [("1111₂", "Binario")]))
        self.assertIn("17₈ → 15₁₀ decimal intermedio → 1111₂", texto)
        self.assertIn("Etapa 1 · Octal → decimal", texto)
        self.assertIn("Etapa 2 · Decimal → binario", texto)

    def test_octal_a_las_otras_tres_bases_comparte_la_expansion(self):
        respuesta = self.convertir("725", 8, (2, 10, 16))
        texto = texto_plano(respuesta)
        self.assertIn("Octal → binario, decimal y hexadecimal", texto)
        # Una sola sección de resultados: el origen una vez y solo las escrituras pedidas, en orden.
        self.assertEqual(texto.count("Resultado "), 1)
        self.assertEqual(texto.count("Número de origen"), 1)
        self.assertEqual(
            resultados_de(respuesta),
            ("725₈", [("111010101₂", "Binario"), ("469₁₀", "Decimal"), ("1D5₁₆", "Hexadecimal")]),
        )
        # La expansión hacia decimal aparece una sola vez y alimenta las dos divisiones.
        self.assertEqual(texto.count("Expansión posicional"), 1)
        self.assertEqual(texto.count("Octal → decimal"), 1)
        self.assertEqual(texto.count("7·8"), 1)
        self.assertIn("725₈ = 7·82 + 2·81 + 5·80 = 448 + 16 + 5 = 469₁₀", texto)
        self.assertEqual(texto.count("decimal intermedio"), 1)
        self.assertIn("725₈ → 469₁₀ decimal intermedio → 111010101₂ 1D5₁₆", texto)
        self.assertIn("escriben las demás bases pedidas.", texto)
        self.assertIn("Ese valor decimal es, además, uno de los resultados pedidos.", texto)
        self.assertIn("Etapa 1 · Octal → decimal", texto)
        self.assertIn("Etapa 2 · Decimal → binario", texto)
        self.assertIn("Etapa 3 · Decimal → hexadecimal", texto)
        self.assertNotIn("Etapa 4", texto)
        # Decimal fue pedido, pero no existe una etapa decimal → decimal ni una segunda expansión.
        self.assertNotIn("Decimal → decimal", texto)
        self.assertEqual(texto.count("Divisiones sucesivas entre"), 2)
        self.assertEqual(texto.count("Divisiones sucesivas de 469₁₀"), 2)
        self.assertIn("469 ÷ 2", texto)
        self.assertIn("469 ÷ 16", texto)
        self.assertIn("13 → D", texto)

    def test_octal_a_binario_y_decimal_expansion_una_vez_y_solo_una_division(self):
        respuesta = self.convertir("725", 8, (2, 10))
        texto = texto_plano(respuesta)
        self.assertEqual(resultados_de(respuesta), ("725₈", [("111010101₂", "Binario"), ("469₁₀", "Decimal")]))
        self.assertEqual(texto.count("Expansión posicional"), 1)
        self.assertEqual(texto.count("Divisiones sucesivas entre"), 1)
        self.assertIn("Etapa 1 · Octal → decimal", texto)
        self.assertIn("Etapa 2 · Decimal → binario", texto)
        self.assertNotIn("Etapa 3", texto)
        self.assertNotIn("Decimal → decimal", texto)
        self.assertNotIn("Decimal → hexadecimal", texto)
        self.assertIn("escriben la otra base pedida.", texto)
        self.assertIn("uno de los resultados pedidos", texto)

    def test_decimal_a_varias_bases_sin_etapa_intermedia(self):
        respuesta = self.convertir("13", 10, (2, 8, 16))
        texto = texto_plano(respuesta)
        self.assertIn("Decimal → binario, octal y hexadecimal", texto)
        self.assertEqual(resultados_de(respuesta), ("13₁₀", [("1101₂", "Binario"), ("15₈", "Octal"), ("D₁₆", "Hexadecimal")]))
        self.assertIn("no hay etapa intermedia", texto)
        self.assertNotIn("Expansión posicional", texto)
        self.assertNotIn("decimal intermedio", texto)
        self.assertNotIn("pasa por decimal", texto)
        self.assertIn("Etapa 1 · Decimal → binario", texto)
        self.assertIn("Etapa 2 · Decimal → octal", texto)
        self.assertIn("Etapa 3 · Decimal → hexadecimal", texto)
        self.assertEqual(texto.count("Divisiones sucesivas de 13₁₀"), 3)
        self.assertIn("13 ÷ 8", texto)
        self.assertIn("13 → D", texto)

    def test_solo_se_muestran_los_destinos_pedidos(self):
        respuesta = self.convertir("17", 8, 16)
        texto = texto_plano(respuesta)
        self.assertIn("Octal → hexadecimal", texto)
        self.assertEqual(resultados_de(respuesta), ("17₈", [("F₁₆", "Hexadecimal")]))
        self.assertNotIn("1111₂", texto)
        self.assertNotIn("Etapa 3", texto)

        respuesta = self.convertir("17", 8, (10, 16))
        texto = texto_plano(respuesta)
        self.assertIn("Octal → decimal y hexadecimal", texto)
        self.assertEqual(resultados_de(respuesta), ("17₈", [("15₁₀", "Decimal"), ("F₁₆", "Hexadecimal")]))
        self.assertNotIn("1111₂", texto)
        self.assertNotIn("Decimal → binario", texto)

    def test_binario_a_octal_y_decimal_reutiliza_el_intermedio(self):
        respuesta = self.convertir("1011", 2, (8, 10))
        texto = texto_plano(respuesta)
        self.assertIn("Binario → octal y decimal", texto)
        self.assertEqual(resultados_de(respuesta), ("1011₂", [("13₈", "Octal"), ("11₁₀", "Decimal")]))
        self.assertIn("1011₂ → 11₁₀ decimal intermedio → 13₈", texto)
        self.assertIn("escriben la otra base pedida.", texto)
        self.assertIn("uno de los resultados pedidos", texto)
        self.assertEqual(texto.count("Expansión posicional"), 1)
        self.assertEqual(texto.count("Divisiones sucesivas entre"), 1)
        self.assertIn("Etapa 1 · Binario → decimal", texto)
        self.assertIn("Etapa 2 · Decimal → octal", texto)
        self.assertNotIn("Etapa 3", texto)

    def test_servicio_devuelve_datos_no_html(self):
        resultado = convertir_entrada(numero="17", base_origen=8, bases_destino=[2, 10, 16])
        self.assertEqual(resultado["titulo"], "Octal → binario, decimal y hexadecimal")
        self.assertEqual(resultado["origen"], "17₈")
        self.assertEqual(resultado["bases_destino"], (2, 10, 16))
        self.assertEqual(
            [(r["base"], r["nombre"], r["destino"]) for r in resultado["resultados"]],
            [(2, "binario", "1111₂"), (10, "decimal", "15₁₀"), (16, "hexadecimal", "F₁₆")],
        )
        self.assertEqual([e["tipo"] for e in resultado["etapas"]], ["expansion", "division", "division"])
        self.assertEqual([e["titulo"] for e in resultado["etapas"]], ["Octal → decimal", "Decimal → binario", "Decimal → hexadecimal"])
        self.assertEqual(resultado["intermedio"], "15₁₀")
        self.assertEqual(resultado["ramas"], ("1111₂", "F₁₆"))
        self.assertTrue(resultado["decimal_pedido"])
        for etapa in resultado["etapas"]:
            self.assertFalse(any("<" in str(valor) for valor in etapa.values()))
        # Sin etapa compartida ni ruta cuando el origen ya es decimal; sin ruta cuando solo se pide decimal.
        directo = convertir_entrada(numero="13", base_origen=10, bases_destino=[2, 16])
        self.assertIsNone(directo["intermedio"])
        self.assertEqual(directo["ramas"], ())
        self.assertEqual([e["tipo"] for e in directo["etapas"]], ["division", "division"])
        solo_decimal = convertir_entrada(numero="1011", base_origen=2, bases_destino=[10])
        self.assertIsNone(solo_decimal["intermedio"])
        self.assertEqual([e["tipo"] for e in solo_decimal["etapas"]], ["expansion"])
        self.assertEqual(solo_decimal["resultados"], ({"base": 10, "nombre": "decimal", "destino": "11₁₀"},))

    def test_titulos_enumeran_los_destinos(self):
        self.assertEqual(enumerar(["binario"]), "binario")
        self.assertEqual(enumerar(["binario", "octal"]), "binario y octal")
        self.assertEqual(enumerar(["binario", "decimal", "hexadecimal"]), "binario, decimal y hexadecimal")
        self.assertEqual(titulo_conversion(8, (2,)), "Octal → binario")
        self.assertEqual(titulo_conversion(16, (2, 8, 10)), "Hexadecimal → binario, octal y decimal")

    def test_conversion_js_sincroniza_las_casillas_con_el_origen(self):
        script = (STATIC / "conversion.js").read_text(encoding="utf-8")
        for contrato in (
            'select[name="base_origen"]',
            'input[name="bases_destino"]',
            "casilla.disabled = esOrigen",
            "if (esOrigen) casilla.checked = false",
            "opcion.hidden = esOrigen",
            '"Elige al menos una base de destino."',
            'origen.addEventListener("change"',
        ):
            with self.subTest(contrato=contrato):
                self.assertIn(contrato, script)
        self.assertNotIn("base_destino\"", script)
        self.assertNotIn("intercambiar", script)

    def test_error_digito_invalido_sin_traceback(self):
        respuesta = self.convertir("102", 2, 10)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "El dígito 2 no es válido en un número binario.")
        self.assertNotContains(respuesta, "ValueError")
        self.assertNotContains(respuesta, "Traceback")
        self.assertNotContains(respuesta, "invalid literal")
        self.assertNotContains(respuesta, 'id="resultado"')
        # El error también aplica cuando los destinos no son decimales.
        self.assertContains(self.convertir("1G", 16, (2, 8)), "G no es un dígito hexadecimal válido.")

    def test_rechaza_negativos_y_vacio(self):
        self.assertContains(self.convertir("", 10, 2), "Ingresa un número.")
        self.assertContains(self.convertir("-13", 10, 2), "no negativos")
        self.assertContains(self.convertir("-11", 2, (8, 16)), "no negativos")

    def test_tema_y_recursos_locales(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        self.assertIn("algebra-lineal-tema", html)
        self.assertNotIn("cdn.", html.lower())
        self.assertNotIn("fonts.googleapis", html.lower())
        self.assertIn("calculadora/styles.css", html)
        self.assertIn("calculadora/teclado.js", html)

    def test_sistemas_sigue_disponible(self):
        self.assertEqual(self.client.get("/sistemas/").status_code, 200)

    def test_conversiones_fraccionarias_y_normalizacion(self):
        casos = (
            ("0.5", 10, 2, "0.1₂"), (".25", 10, 16, "0.4₁₆"),
            ("5.5", 10, 16, "5.8₁₆"), ("5.", 10, 16, "5₁₆"),
            ("0.31", 10, 16, "0.4(F5C28)₁₆"),
            ("0.1", 2, 10, "0.5₁₀"), ("101.101", 2, 10, "5.625₁₀"),
            ("A.F", 16, 10, "10.9375₁₀"), ("17.4", 8, 10, "15.5₁₀"),
            ("101.101", 2, 16, "5.A₁₆"), ("A.F", 16, 2, "1010.1111₂"),
        )
        for numero, origen, destino, esperado in casos:
            with self.subTest(numero=numero, destino=destino):
                respuesta = self.convertir(numero, origen, destino)
                self.assertEqual(resultados_de(respuesta)[1][0][0], esperado)

    def test_procedimiento_fraccionario_separado_y_periodo_visible(self):
        respuesta = self.convertir("0.31", 10, 16)
        self.assertNotContains(respuesta, "Divisiones sucesivas")
        self.assertContains(respuesta, "Multiplicaciones sucesivas")
        self.assertContains(respuesta, "0.31 × 16 = 4.96")
        self.assertContains(respuesta, "0.96 × 16 = 15.36")
        self.assertContains(respuesta, "Periódico · período: F5C28")
        self.assertContains(respuesta, "La fracción restante 0.96 se repite")
        self.assertContains(respuesta, "dígito fraccionario 2")
        texto = texto_plano(self.convertir("5.5", 10, 16))
        self.assertLess(texto.index("Parte entera"), texto.index("Parte fraccionaria"))
        self.assertIn("5 ÷ 16", texto)
        self.assertIn("0.5 × 16 = 8", texto)
        self.assertIn("arriba hacia abajo: 5.8₁₆", texto)
        self.assertNotContains(self.convertir("5", 10, 16), "Parte fraccionaria")

    def test_expansion_fraccionaria_y_multidestino_calculan_una_vez(self):
        with (
            patch.object(motor, "base_a_decimal", wraps=motor.base_a_decimal) as hacia,
            patch.object(motor, "decimal_a_base", wraps=motor.decimal_a_base) as desde,
        ):
            respuesta = self.convertir("101.101", 2, (8, 10, 16))
        hacia.assert_called_once_with("101.101", 2)
        self.assertEqual(desde.call_args_list, [call(Fraction(45, 8), 8), call(Fraction(45, 8), 16)])
        self.assertEqual(resultados_de(respuesta), (
            "101.101₂", [("5.5₈", "Octal"), ("5.625₁₀", "Decimal"), ("5.A₁₆", "Hexadecimal")],
        ))
        self.assertContains(respuesta, "Expansión posicional:", count=1)
        for exponente in (-1, -2, -3):
            self.assertContains(respuesta, f"<sup>{exponente}</sup>")
        self.assertContains(respuesta, "4 + 0 + 1 + 0.5 + 0 + 0.125")
        self.assertContains(respuesta, "no se vuelve a calcular")
        self.assertEqual(resultados_de(self.convertir("00.1", 2, 10))[0], "0.1₂")

    def test_errores_fraccionarios_y_limite_sin_resultado_parcial(self):
        for texto, base in (("1.2.3", 10), (".", 10), ("2.01", 2), ("0.2", 2), ("A.G", 16)):
            with self.subTest(texto=texto):
                self.assertNotContains(self.convertir(texto, base, 8), 'id="resultado"')
        with patch.object(motor, "MAX_PASOS_FRACCIONARIOS", 2):
            respuesta = self.convertir("0.31", 10, (2, 16))
        self.assertContains(respuesta, "límite de seguridad")
        self.assertContains(respuesta, "No se ha truncado ni aproximado")
        self.assertNotContains(respuesta, 'id="resultado"')
