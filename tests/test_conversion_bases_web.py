"""Integración web de Conversión de bases (P11) y de las conversiones multidestino (P16)."""

import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase
from django.urls import resolve, reverse
from django.utils.html import strip_tags

from frontend.web.calculadora import catalogo
from frontend.web.calculadora.servicios_bases import convertir_entrada, enumerar, titulo_conversion
from tests.test_interfaz_progresiva import Formulario
from tests.test_navegacion import Documento

STATIC = Path(__file__).resolve().parents[1] / "frontend" / "web" / "calculadora" / "static" / "calculadora"


def texto_plano(respuesta):
    return " ".join(strip_tags(respuesta.content.decode("utf-8")).split())


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
        # Ya no hay un único destino ni un botón para intercambiarlo con el origen.
        self.assertNotIn('name="base_destino"', html)
        self.assertNotIn("data-intercambiar-bases", html)
        self.assertNotIn("base-swap", html)
        # «Convertir a»: un grupo accesible de casillas, una por base, en orden fijo.
        self.assertIn("<legend>Convertir a</legend>", html)
        casillas = self.casillas_destino(respuesta)
        self.assertEqual([c["type"] for c in casillas], ["checkbox"] * 4)
        self.assertEqual([c["value"] for c in casillas], ["2", "8", "10", "16"])
        self.assertEqual(
            [c["id"] for c in casillas],
            ["id_bases_destino_0", "id_bases_destino_1", "id_bases_destino_2", "id_bases_destino_3"],
        )
        # Predeterminado: decimal → binario, como hasta ahora; la casilla del origen no se ofrece.
        self.assertEqual([c["value"] for c in casillas if "checked" in c], ["2"])
        self.assertEqual([c["value"] for c in casillas if "disabled" in c], ["10"])
        self.assertRegex(html, r'<label class="option" data-destino-base="10" hidden>')
        for base in (2, 8, 16):
            self.assertRegex(html, rf'<label class="option" data-destino-base="{base}">')
        self.assertIn("Marca una, varias o todas las demás bases.", html)
        # Aviso en vivo de destinos, vacío hasta que JavaScript lo use.
        self.assertIn('data-validacion-destinos role="alert" hidden', html)
        # Sin tarjetas grandes para elegir la base ni el modo.
        self.assertNotIn('name="modo"', html)
        self.assertNotIn('name="base"', html)
        self.assertNotIn('class="choice"', html)

    def test_teclado_y_etiqueta_siguen_a_la_base_de_origen(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        for base in (2, 8, 10, 16):
            self.assertIn(f'data-teclado="base-{base}"', html)
        self.assertIn("calculadora/teclado.js", html)
        self.assertIn("calculadora/conversion.js", html)
        # Por defecto el origen es decimal: solo ese contenedor y esa etiqueta quedan visibles.
        self.assertRegex(html, r'<div class="base-keyboard" data-teclado-base="10" data-nombre-base="decimal"\s*>')
        self.assertRegex(html, r'data-teclado-base="2"[^>]*hidden')
        self.assertRegex(html, r'data-teclado-base="16"[^>]*hidden')
        self.assertRegex(html, r'<span data-number-label-base="10"\s*>Número decimal</span>')
        self.assertRegex(html, r'data-number-label-base="2"[^>]*hidden[^>]*>Número binario<')
        self.assertIn('data-insercion="A"', html)
        self.assertIn('data-insercion="F"', html)
        # Aviso de validación en vivo, vacío hasta que JavaScript lo use.
        self.assertIn('data-validacion-cliente role="alert" hidden', html)

    def test_cambio_de_origen_actualiza_teclado_etiqueta_y_casillas_sin_javascript(self):
        respuesta = self.convertir("", 16, 2)
        html = respuesta.content.decode("utf-8")
        self.assertRegex(html, r'<div class="base-keyboard" data-teclado-base="16" data-nombre-base="hexadecimal"\s*>')
        self.assertRegex(html, r'data-teclado-base="10"[^>]*hidden')
        self.assertRegex(html, r'<span data-number-label-base="16"\s*>Número hexadecimal</span>')
        self.assertRegex(html, r'data-number-label-base="10"[^>]*hidden')
        # Ahora la casilla oculta es la hexadecimal y la decimal vuelve a ofrecerse; binario sigue marcado.
        casillas = self.casillas_destino(respuesta)
        self.assertEqual([c["value"] for c in casillas if "disabled" in c], ["16"])
        self.assertEqual([c["value"] for c in casillas if "checked" in c], ["2"])
        self.assertRegex(html, r'<label class="option" data-destino-base="16" hidden>')
        self.assertRegex(html, r'<label class="option" data-destino-base="10">')

    def test_el_envio_por_defecto_del_formulario_convierte_decimal_a_binario(self):
        formulario = Formulario(self.client.get(self.ruta).content.decode("utf-8"), "conversion-form")
        # El ayudante solo lee input y textarea: la base de origen (select) viaja con su valor inicial.
        self.assertEqual({nombre for nombre, _ in formulario.datos}, {"csrfmiddlewaretoken", "numero", "bases_destino"})
        datos = formulario.como_datos(numero="13", base_origen="10")
        self.assertEqual(datos["bases_destino"], ["2"])
        respuesta = self.client.post(self.ruta, datos)
        self.assertContains(respuesta, "13₁₀ = 1101₂")
        self.assertContains(respuesta, "Decimal → binario")

    def test_el_campo_del_numero_es_de_una_linea(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        self.assertIn('class="field-input field-input-numeral"', html)
        self.assertNotIn("field-input-code", html)
        self.assertNotIn("<textarea", html)

    def test_todos_los_pares_de_bases_distintas(self):
        # 26₁₀ = 11010₂ = 32₈ = 1A₁₆
        escrituras = {2: "11010", 8: "32", 10: "26", 16: "1A"}
        subindices = {2: "₂", 8: "₈", 10: "₁₀", 16: "₁₆"}
        for origen, numero in escrituras.items():
            for destino, esperado in escrituras.items():
                if origen == destino:
                    continue
                with self.subTest(origen=origen, destino=destino):
                    respuesta = self.convertir(numero, origen, destino)
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertContains(respuesta, f"{numero}{subindices[origen]}")
                    self.assertContains(respuesta, f"{esperado}{subindices[destino]}")
                    self.assertContains(respuesta, "Procedimiento")

    def test_cada_origen_a_todas_las_demas_bases(self):
        escrituras = {2: "11010", 8: "32", 10: "26", 16: "1A"}
        subindices = {2: "₂", 8: "₈", 10: "₁₀", 16: "₁₆"}
        for origen, numero in escrituras.items():
            destinos = [base for base in (2, 8, 10, 16) if base != origen]
            with self.subTest(origen=origen):
                texto = texto_plano(self.convertir(numero, origen, destinos))
                for destino in destinos:
                    self.assertIn(f"{numero}{subindices[origen]} = {escrituras[destino]}{subindices[destino]}", texto)
                self.assertNotIn(f"= {numero}{subindices[origen]}", texto)

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

    def test_destinos_repetidos_o_desordenados_se_normalizan(self):
        respuesta = self.convertir("13", 10, (16, 2, 16))
        texto = texto_plano(respuesta)
        self.assertIn("Decimal → binario y hexadecimal", texto)
        self.assertLess(texto.index("13₁₀ = 1101₂"), texto.index("13₁₀ = D₁₆"))
        self.assertEqual(texto.count("13₁₀ = D₁₆"), 1)
        self.assertEqual(texto.count("Decimal → hexadecimal"), 1)

    def test_decimal_a_binario_en_una_etapa(self):
        respuesta = self.convertir("13", 10, 2)
        self.assertContains(respuesta, "13₁₀")
        self.assertContains(respuesta, "1101₂")
        self.assertContains(respuesta, "Decimal → binario")
        self.assertContains(respuesta, "13 ÷ 2")
        self.assertContains(respuesta, "residuos se leen")
        self.assertNotContains(respuesta, "Etapa 1")
        self.assertNotContains(respuesta, "pasa por decimal")
        self.assertNotContains(respuesta, "etapa intermedia")
        self.assertNotContains(respuesta, "Expansión posicional")

    def test_decimal_a_hexadecimal_sustituye_diez_por_a(self):
        respuesta = self.convertir("26", 10, 16)
        self.assertContains(respuesta, "1A₁₆")
        self.assertContains(respuesta, "10 → A")

    def test_binario_a_decimal_muestra_la_combinacion_lineal(self):
        respuesta = self.convertir("1011", 2, 10)
        self.assertContains(respuesta, "1011₂")
        self.assertContains(respuesta, "11₁₀")
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
        self.assertContains(respuesta, "1A₁₆")
        self.assertContains(respuesta, "Hexadecimal → decimal")
        self.assertContains(respuesta, "A = 10")
        self.assertContains(respuesta, "26₁₀")

    def test_binario_a_hexadecimal_en_dos_etapas(self):
        respuesta = self.convertir("1010", 2, 16)
        texto = texto_plano(respuesta)
        self.assertIn("1010₂ = A₁₆", texto)
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
        texto = texto_plano(self.convertir("17", 8, 2))
        self.assertIn("17₈ = 1111₂", texto)
        self.assertIn("17₈ → 15₁₀ decimal intermedio → 1111₂", texto)
        self.assertIn("Etapa 1 · Octal → decimal", texto)
        self.assertIn("Etapa 2 · Decimal → binario", texto)

    def test_octal_a_las_otras_tres_bases_comparte_la_expansion(self):
        respuesta = self.convertir("17", 8, (2, 10, 16))
        texto = texto_plano(respuesta)
        self.assertIn("Octal → binario, decimal y hexadecimal", texto)
        # Solo los resultados pedidos, en el orden de las casillas, con el mismo origen.
        resultado = texto[texto.index("Resultado"):texto.index("Procedimiento")]
        self.assertEqual(resultado, "Resultado 17₈ = 1111₂ 17₈ = 15₁₀ 17₈ = F₁₆ ")
        # La expansión hacia decimal aparece una sola vez y alimenta las dos divisiones.
        self.assertEqual(texto.count("Expansión posicional"), 1)
        self.assertEqual(texto.count("Octal → decimal"), 1)
        self.assertEqual(texto.count("1·8"), 1)
        self.assertIn("17₈ → 15₁₀ decimal intermedio → 1111₂ F₁₆", texto)
        self.assertIn("escriben las demás bases pedidas.", texto)
        self.assertIn("Ese valor decimal es, además, uno de los resultados pedidos.", texto)
        self.assertIn("Etapa 1 · Octal → decimal", texto)
        self.assertIn("Etapa 2 · Decimal → binario", texto)
        self.assertIn("Etapa 3 · Decimal → hexadecimal", texto)
        self.assertNotIn("Etapa 4", texto)
        # Decimal fue pedido, pero no existe una etapa decimal → decimal ni una segunda expansión.
        self.assertNotIn("Decimal → decimal", texto)
        self.assertEqual(texto.count("Divisiones sucesivas entre"), 2)
        self.assertEqual(texto.count("Divisiones sucesivas de 15₁₀"), 2)
        self.assertIn("15 ÷ 2", texto)
        self.assertIn("15 ÷ 16", texto)
        self.assertIn("15 → F", texto)

    def test_decimal_a_varias_bases_sin_etapa_intermedia(self):
        texto = texto_plano(self.convertir("13", 10, (2, 8, 16)))
        self.assertIn("Decimal → binario, octal y hexadecimal", texto)
        resultado = texto[texto.index("Resultado"):texto.index("Procedimiento")]
        self.assertEqual(resultado, "Resultado 13₁₀ = 1101₂ 13₁₀ = 15₈ 13₁₀ = D₁₆ ")
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
        texto = texto_plano(self.convertir("17", 8, 16))
        self.assertIn("Octal → hexadecimal", texto)
        self.assertIn("17₈ = F₁₆", texto)
        self.assertNotIn("1111₂", texto)
        self.assertNotIn("17₈ = 15₁₀", texto)
        self.assertNotIn("Etapa 3", texto)

        texto = texto_plano(self.convertir("17", 8, (10, 16)))
        self.assertIn("Octal → decimal y hexadecimal", texto)
        self.assertIn("17₈ = 15₁₀", texto)
        self.assertIn("17₈ = F₁₆", texto)
        self.assertNotIn("1111₂", texto)
        self.assertNotIn("Decimal → binario", texto)

    def test_binario_a_octal_y_decimal_reutiliza_el_intermedio(self):
        texto = texto_plano(self.convertir("1011", 2, (8, 10)))
        self.assertIn("Binario → octal y decimal", texto)
        self.assertIn("1011₂ = 13₈", texto)
        self.assertIn("1011₂ = 11₁₀", texto)
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
        self.assertEqual([r["destino"] for r in resultado["resultados"]], ["1111₂", "15₁₀", "F₁₆"])
        self.assertEqual([r["igualdad"] for r in resultado["resultados"]], ["17₈ = 1111₂", "17₈ = 15₁₀", "17₈ = F₁₆"])
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
        self.assertEqual(solo_decimal["resultados"][0]["igualdad"], "1011₂ = 11₁₀")

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

    def test_base_invalida_en_el_formulario(self):
        for datos in (
            {"numero": "1", "base_origen": "3", "bases_destino": ["2"]},
            {"numero": "1", "base_origen": "10", "bases_destino": ["3"]},
            {"numero": "1", "base_origen": "10", "bases_destino": ["2", "3"]},
        ):
            with self.subTest(datos=datos):
                respuesta = self.client.post(self.ruta, datos)
                self.assertEqual(respuesta.status_code, 200)
                self.assertNotContains(respuesta, 'id="resultado"')
                self.assertNotContains(respuesta, "Traceback")

    def test_tema_y_recursos_locales(self):
        html = self.client.get(self.ruta).content.decode("utf-8")
        self.assertIn("algebra-lineal-tema", html)
        self.assertNotIn("cdn.", html.lower())
        self.assertNotIn("fonts.googleapis", html.lower())
        self.assertIn("calculadora/styles.css", html)
        self.assertIn("calculadora/teclado.js", html)

    def test_sistemas_sigue_disponible(self):
        self.assertEqual(self.client.get("/sistemas/").status_code, 200)
