"""Integración web de Conversión de números romanos (P25)."""

import os
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase
from django.urls import resolve, reverse
from django.utils.html import strip_tags

from frontend.web.calculadora import catalogo
from frontend.web.calculadora.forms_romanos import ConversionRomanosForm
from frontend.web.calculadora.servicios_romanos import convertir_romanos
from tests.ayudas import elemento_html
from tests.test_navegacion import Documento
from tests.test_procedimiento_plegable import Estructura

RUTA = "/romanos/conversion/"


def texto_plano(respuesta):
    return " ".join(strip_tags(respuesta.content.decode("utf-8")).split())


def texto_de(respuesta, marca, etiqueta):
    html = respuesta.content.decode("utf-8")
    return " ".join(strip_tags(elemento_html(html, html.index(marca), etiqueta)).split())


def resultado_de(respuesta):
    """(origen, resultado, nombre) tal como se leen en el panel Resultado."""
    seccion = texto_de(respuesta, "panel-final", "section")
    return re.fullmatch(r"Resultado Número de origen: (\S+) = (\S+) (Romano|Arábigo)", seccion).groups()


def procedimiento_de(respuesta):
    return texto_de(respuesta, 'id="procedimiento"', "details")


class PruebasRegistro(SimpleTestCase):
    def setUp(self):
        self.herramienta = catalogo.herramienta_por_id("conversion-romanos")

    def test_ruta_y_nombre(self):
        self.assertEqual(reverse("calculadora:conversion-romanos"), RUTA)
        self.assertEqual(resolve(RUTA).view_name, "calculadora:conversion-romanos")
        self.assertEqual(self.herramienta.ruta, RUTA)
        self.assertEqual(catalogo.herramienta_por_ruta(resolve(RUTA)), self.herramienta)

    def test_categoria_propia_dentro_de_sistemas_numericos(self):
        self.assertTrue(self.herramienta.disponible)
        self.assertEqual(self.herramienta.nombre, "Conversión de números romanos")
        self.assertEqual(self.herramienta.categoria, catalogo.NUMERACION_ROMANA)
        self.assertEqual(catalogo.NUMERACION_ROMANA.nombre, "Numeración romana")
        self.assertEqual(self.herramienta.area, catalogo.SISTEMAS_NUMERICOS)
        # No es una base posicional: Bases numéricas conserva solo su herramienta.
        self.assertEqual(catalogo.herramientas_de(catalogo.BASES_NUMERICAS), (catalogo.CONVERSION_BASES,))
        self.assertEqual(catalogo.herramientas_de(catalogo.NUMERACION_ROMANA), (self.herramienta,))
        for clave in ("romano", "romanos", "números romanos", "numeración romana", "arábigo a romano", "romano a arábigo",
                      "decimal a romano", "romano a decimal"):
            self.assertIn(clave, self.herramienta.palabras_clave)

    def test_relacion_en_ambos_sentidos_con_conversion_de_bases(self):
        self.assertEqual(self.herramienta.relacionadas, ("conversion-bases",))
        self.assertEqual(catalogo.CONVERSION_BASES.relacionadas, ("conversion-romanos",))
        self.assertEqual(catalogo.relacionadas_disponibles(self.herramienta), (catalogo.CONVERSION_BASES,))

    def test_inicio_presenta_el_tema_con_su_herramienta(self):
        respuesta = self.client.get("/")
        html = respuesta.content.decode("utf-8")
        self.assertIn("numeracion-romana", Documento(respuesta).ids)
        inicio_tema = html.index('id="numeracion-romana"')
        tema = html[inicio_tema:html.index("</details>", inicio_tema)]
        for texto in ("Numeración romana", "Conversión entre números arábigos y romanos.", f'href="{RUTA}"',
                      "Conversión de números romanos", self.herramienta.descripcion):
            self.assertIn(texto, tema)
        # El tema va después de Bases numéricas, dentro del área Sistemas numéricos.
        self.assertLess(html.index('id="sistemas-numericos"'), html.index('id="bases-numericas"'))
        self.assertLess(html.index('id="bases-numericas"'), inicio_tema)
        self.assertContains(respuesta, "Representación de números en distintas bases y en numeración romana.")

    def test_busqueda(self):
        # «decimal» ya no se muestra, pero sigue encontrando la herramienta en el buscador.
        for consulta in ("romano", "Romanos", "números romanos", "numeracion romana", "arábigo a romano",
                         "romano a arabigo", "decimal a romano", "romano a decimal"):
            with self.subTest(consulta=consulta):
                self.assertEqual(catalogo.buscar_herramientas(consulta)[0], self.herramienta)
                respuesta = self.client.get("/", {"q": consulta})
                self.assertContains(respuesta, "Conversión de números romanos")
                self.assertContains(respuesta, f'href="{RUTA}"')
        self.assertNotIn(self.herramienta, catalogo.buscar_herramientas("binario"))
        self.assertIn(self.herramienta, catalogo.buscar_herramientas("sistemas numéricos"))
        # Conversión de bases sigue primero al buscar «conversión».
        self.assertEqual(catalogo.buscar_herramientas("conversion")[:2], (catalogo.CONVERSION_BASES, self.herramienta))

    def test_breadcrumbs_y_cajon(self):
        respuesta = self.client.get(RUTA)
        documento = Documento(respuesta)
        self.assertEqual(
            [a["href"] for a in documento.enlaces_en("Ruta de navegación")],
            ["/", "/#sistemas-numericos", "/#numeracion-romana"],
        )
        self.assertContains(respuesta, '<span aria-current="page">Conversión de números romanos</span>', html=True)
        activos = [a["href"] for a in documento.enlaces_en("Herramientas") if a.get("aria-current") == "page"]
        self.assertEqual(activos, [RUTA])
        self.assertEqual([c for c, abierta in documento.categorias.items() if abierta], ["numeracion-romana"])
        self.assertContains(respuesta, "Conversión de números romanos · PyGebra")


class PruebasFormulario(SimpleTestCase):
    def test_get_muestra_direccion_numero_y_convertir(self):
        respuesta = self.client.get(RUTA)
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode("utf-8")
        documento = Documento(respuesta)
        radios = [c for c in documento.controles if c.get("name") == "direccion"]
        self.assertEqual([(r["type"], r["value"]) for r in radios], [("radio", "decimal_a_romano"), ("radio", "romano_a_decimal")])
        self.assertEqual([r["value"] for r in radios if "checked" in r], ["decimal_a_romano"])
        self.assertRegex(html, r'<legend>Dirección</legend>\s*<div class="segmented">')
        self.assertIn("<span>Arábigo → romano</span>", html)
        self.assertIn("<span>Romano → arábigo</span>", html)
        (numero,) = [c for c in documento.controles if c.get("name") == "numero"]
        self.assertEqual(numero["type"], "text")
        self.assertEqual(numero["maxlength"], "15")
        self.assertEqual(numero["aria-describedby"], "numero-ayuda")
        self.assertIn("numero-ayuda", documento.ids)
        # UI-40: etiqueta y ayuda por dirección; el CSS muestra la de la dirección elegida.
        self.assertIn('<span data-direccion="decimal_a_romano">Número arábigo</span>', html)
        self.assertIn('<span data-direccion="romano_a_decimal">Número romano</span>', html)
        self.assertIn("Un entero del 1 al 3999, escrito con cifras.", html)
        self.assertIn("Escrito con I, V, X, L, C, D y M", html)
        self.assertEqual([c.get("type") for c in documento.controles if c.get("class") == "btn btn-primary"], ["submit"])
        self.assertIn(">Convertir</button>", html)
        formulario = next(f for f in documento.formularios if f.get("id") == "romanos-form")
        self.assertEqual((formulario["method"], formulario["action"]), ("post", f"{RUTA}#resultado"))
        # Sin resultado, sin teclado matemático ni selector Exacto/Decimal.
        for ausente in ('id="resultado"', "math-keyboard", "data-numeric-controls", "numeros.js", "teclado.js", "<textarea"):
            self.assertNotIn(ausente, html)

    def test_get_con_parametros_no_convierte(self):
        respuesta = self.client.get(RUTA, {"direccion": "decimal_a_romano", "numero": "1963"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, 'id="resultado"')

    def test_solo_get_y_post(self):
        for metodo in ("put", "delete", "patch"):
            with self.subTest(metodo=metodo):
                self.assertEqual(getattr(self.client, metodo)(RUTA).status_code, 405)

    def test_el_envio_por_defecto_convierte_de_decimal_a_romano(self):
        respuesta = self.client.post(RUTA, {"direccion": "decimal_a_romano", "numero": "1963"})
        self.assertEqual(resultado_de(respuesta), ("1963", "MCMLXIII", "Romano"))


class PruebasConversionWeb(SimpleTestCase):
    def convertir(self, direccion, numero):
        return self.client.post(RUTA, {"direccion": direccion, "numero": numero})

    def test_decimal_a_romano(self):
        casos = (("1", "I"), ("4", "IV"), ("14", "XIV"), ("944", "CMXLIV"), ("1963", "MCMLXIII"),
                 ("2026", "MMXXVI"), ("3999", "MMMCMXCIX"), (" 0058 ", "LVIII"))
        for numero, esperado in casos:
            with self.subTest(numero=numero):
                respuesta = self.convertir("decimal_a_romano", numero)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(resultado_de(respuesta), (str(int(numero)), esperado, "Romano"))
                self.assertContains(respuesta, '<h2 id="results-title">Arábigo → romano</h2>', html=True)

    def test_romano_a_decimal_y_minusculas(self):
        casos = (("I", "I", "1"), ("MCMLXIII", "MCMLXIII", "1963"), ("mcmlxiii", "MCMLXIII", "1963"),
                 ("  xLiV ", "XLIV", "44"), ("MMMCMXCIX", "MMMCMXCIX", "3999"))
        for numero, origen, esperado in casos:
            with self.subTest(numero=numero):
                respuesta = self.convertir("romano_a_decimal", numero)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(resultado_de(respuesta), (origen, esperado, "Arábigo"))
                self.assertContains(respuesta, '<h2 id="results-title">Romano → arábigo</h2>', html=True)

    def test_procedimiento_plegado_y_despues_un_solo_resultado(self):
        for direccion, numero in (("decimal_a_romano", "1963"), ("romano_a_decimal", "MCMLXIII")):
            with self.subTest(direccion=direccion):
                html = self.convertir(direccion, numero).content.decode("utf-8")
                self.assertEqual(html.count('id="resultado"'), 1)
                self.assertEqual(html.count("Número de origen"), 1)
                estructura = Estructura(html)
                self.assertEqual(len(estructura.paneles_finales), 1)
                self.assertEqual(estructura.paneles_finales[0]["dentro"], 0)
                procedimiento = estructura.principal()
                self.assertEqual(procedimiento["id"], "procedimiento")
                self.assertFalse(procedimiento["open"])
                self.assertEqual(procedimiento["encabezado"], "h3")
                self.assertEqual(len(estructura.details), 1)
                self.assertLess(estructura.indice("details", id="procedimiento"), estructura.indice("panel-final"))

    def test_procedimiento_decimal_a_romano_agrupado(self):
        texto = procedimiento_de(self.convertir("decimal_a_romano", "1963"))
        self.assertIn("Se separan millares, centenas, decenas y unidades", texto)
        self.assertIn("1963 = 1000 + 900 + 60 + 3", texto)
        self.assertIn("Parte Romano 1000 M 900 CM (1000 − 100) 60 LX (50 + 10) 3 III (1 + 1 + 1)", texto)
        self.assertIn("Las partes se escriben una tras otra, de mayor a menor: 1963 = MCMLXIII", texto)
        # Los órdenes en cero no generan filas: 2026 = 2000 + 20 + 6.
        texto = procedimiento_de(self.convertir("decimal_a_romano", "2026"))
        self.assertIn("2026 = 2000 + 20 + 6", texto)
        self.assertIn("2000 MM (1000 + 1000) 20 XX (10 + 10) 6 VI (5 + 1)", texto)
        # Con una sola parte no hay descomposición ni unión que mostrar.
        texto = procedimiento_de(self.convertir("decimal_a_romano", "4"))
        self.assertIn("Parte Romano 4 IV (5 − 1)", texto)
        self.assertNotIn("4 = ", texto)
        self.assertNotIn("una tras otra", texto)

    def test_procedimiento_romano_a_decimal_de_izquierda_a_derecha(self):
        texto = procedimiento_de(self.convertir("romano_a_decimal", "MCMLXIII"))
        self.assertIn("Se lee de izquierda a derecha", texto)
        self.assertIn("Símbolos Valor M 1000 CM 900 (1000 − 100) L 50 X 10 I 1 I 1 I 1", texto)
        self.assertIn("MCMLXIII = 1000 + 900 + 50 + 10 + 1 + 1 + 1 = 1963", texto)
        texto = procedimiento_de(self.convertir("romano_a_decimal", "iv"))
        self.assertIn("Símbolos Valor IV 4 (5 − 1)", texto)
        self.assertNotIn("IV = ", texto)

    def test_servicio_devuelve_datos_no_html(self):
        resultado = convertir_romanos(direccion="decimal_a_romano", numero="944")
        self.assertEqual(
            {clave: resultado[clave] for clave in ("titulo", "origen", "resultado", "nombre_resultado", "descomposicion")},
            {"titulo": "Arábigo → romano", "origen": "944", "resultado": "CMXLIV", "nombre_resultado": "Romano",
             "descomposicion": "900 + 40 + 4"},
        )
        self.assertEqual(
            resultado["filas"],
            ({"valor": 900, "simbolos": "CM", "detalle": "1000 − 100"},
             {"valor": 40, "simbolos": "XL", "detalle": "50 − 10"},
             {"valor": 4, "simbolos": "IV", "detalle": "5 − 1"}),
        )
        inverso = convertir_romanos(direccion="romano_a_decimal", numero="lviii")
        self.assertEqual((inverso["origen"], inverso["resultado"], inverso["suma"]), ("LVIII", "58", "50 + 5 + 1 + 1 + 1"))
        self.assertEqual((inverso["titulo"], inverso["nombre_resultado"]), ("Romano → arábigo", "Arábigo"))
        self.assertEqual([fila["detalle"] for fila in inverso["filas"]], ["", "", "", "", ""])
        for valor in (*resultado.values(), *inverso.values()):
            self.assertNotIn("<", str(valor))


class PruebasErroresWeb(SimpleTestCase):
    def enviar(self, datos):
        respuesta = self.client.post(RUTA, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, 'id="resultado"')
        self.assertNotContains(respuesta, "Traceback")
        self.assertNotContains(respuesta, "ValueError")
        return respuesta

    def test_limites_decimales(self):
        casos = (
            ("0", "La numeración romana no tiene cero. Ingresa un número entero entre 1 y 3999."),
            ("4000", "La notación romana convencional llega hasta 3999 (MMMCMXCIX). Ingresa un número entero entre 1 y 3999."),
            ("-1", "La numeración romana no tiene números negativos. Ingresa un número entero entre 1 y 3999."),
            ("", "Ingresa un número entero entre 1 y 3999."),
            ("3.5", "Ingresa un número entero entre 1 y 3999, escrito solo con dígitos."),
            ("12a", "Ingresa un número entero entre 1 y 3999, escrito solo con dígitos."),
            ("XIV", "XIV parece un número romano. Cambia a Romano → arábigo."),
        )
        for numero, mensaje in casos:
            with self.subTest(numero=numero):
                respuesta = self.enviar({"direccion": "decimal_a_romano", "numero": numero})
                self.assertIn(mensaje, texto_plano(respuesta))
                self.assertNotContains(respuesta, "Este campo es obligatorio")

    def test_romanos_no_canonicos_y_caracteres_invalidos(self):
        casos = (
            ("", "Ingresa un número romano."),
            ("IIII", "IIII no es una representación romana válida. Para 4 se escribe IV."),
            ("vv", "VV no es una representación romana válida. Para 10 se escribe X."),
            ("IC", "IC no es una representación romana válida: los símbolos van de mayor a menor valor"),
            ("MMMM", "llega hasta 3999 (MMMCMXCIX)"),
            ("ABC", "«A» no es un símbolo romano. Usa solo I, V, X, L, C, D y M."),
            ("1963", "1963 está escrito con cifras arábigas. Cambia a Arábigo → romano."),
            ("X IV", "Escribe el número romano sin espacios."),
        )
        for numero, mensaje in casos:
            with self.subTest(numero=numero):
                respuesta = self.enviar({"direccion": "romano_a_decimal", "numero": numero})
                self.assertIn(mensaje, texto_plano(respuesta))
                # El error queda junto al campo y el valor enviado se conserva para corregirlo.
                self.assertRegex(respuesta.content.decode("utf-8"), r'<ul class="errorlist field-error"[^>]*role="alert"><li>[^<]+</li></ul>')
                self.assertRegex(respuesta.content.decode("utf-8"), r'name="direccion" value="romano_a_decimal"[^>]*checked')

    def test_longitud_maxima(self):
        respuesta = self.enviar({"direccion": "romano_a_decimal", "numero": "M" * 16})
        self.assertIn("El número no puede tener más de 15 caracteres.", texto_plano(respuesta))
        respuesta = self.enviar({"direccion": "decimal_a_romano", "numero": "1" * 10_000})
        self.assertIn("El número no puede tener más de 15 caracteres.", texto_plano(respuesta))
        # El tope es inclusivo: la escritura más larga del intervalo cabe.
        self.assertEqual(
            resultado_de(self.client.post(RUTA, {"direccion": "romano_a_decimal", "numero": "MMMDCCCLXXXVIII"})),
            ("MMMDCCCLXXXVIII", "3888", "Arábigo"),
        )
        self.assertEqual(ConversionRomanosForm.base_fields["numero"].max_length, 15)

    def test_contrato_http_estricto(self):
        casos = (
            ({"direccion": "decimal_a_romano", "numero": "12", "extra": "1"}, "no forman parte del formulario"),
            ({"direccion": "decimal_a_romano", "numero": "12", "base_origen": "10"}, "no forman parte del formulario"),
            ({"direccion": "decimal_a_romano", "numero": ["12", "13"]}, "hay campos repetidos"),
            ({"direccion": ["decimal_a_romano", "romano_a_decimal"], "numero": "12"}, "hay campos repetidos"),
            ({"direccion": ["decimal_a_romano", "decimal_a_romano"], "numero": "12"}, "hay campos repetidos"),
            ({"direccion": "hexadecimal", "numero": "12"}, "Elige una dirección válida: Arábigo → romano o Romano → arábigo."),
            ({"direccion": "", "numero": "12"}, "Elige la dirección de la conversión."),
            ({"numero": "12"}, "Elige la dirección de la conversión."),
            ({"direccion": "<script>alert(1)</script>", "numero": "12"}, "Elige una dirección válida"),
        )
        for datos, mensaje in casos:
            with self.subTest(datos=datos):
                respuesta = self.enviar(datos)
                self.assertIn(mensaje, texto_plano(respuesta))
                self.assertNotContains(respuesta, "<script>alert")

    def test_contenido_malicioso_escapado(self):
        for direccion, numero in (("romano_a_decimal", "<b>x</b>"), ("decimal_a_romano", "<b>1</b>"),
                                  ("romano_a_decimal", '"><i>'), ("decimal_a_romano", "<img src=x>")):
            with self.subTest(direccion=direccion, numero=numero):
                respuesta = self.enviar({"direccion": direccion, "numero": numero})
                html = respuesta.content.decode("utf-8")
                for etiqueta in ("<b>", "<i>", "<img"):
                    self.assertNotIn(etiqueta, html.split("<main", 1)[1])
                self.assertIn("&lt;", html)
        respuesta = self.enviar({"direccion": "romano_a_decimal", "numero": "<b>x</b>"})
        self.assertContains(respuesta, 'value="&lt;b&gt;x&lt;/b&gt;"')
        self.assertContains(respuesta, "«&lt;» no es un símbolo romano.")

    def test_ninguna_entrada_rompe_la_pagina(self):
        entradas = ("", " ", "0", "-0", "4000", "99999999999999", "1e3", "٣", "Ⅳ", "ıv", "IIII", "IC", "MMMM",
                    "IVIV", "\x00", "%00", "{{ 7|add:1 }}", "{% now 'Y' %}", "​", "Ḿ")
        for direccion in ("decimal_a_romano", "romano_a_decimal"):
            for numero in entradas:
                with self.subTest(direccion=direccion, numero=numero):
                    respuesta = self.enviar({"direccion": direccion, "numero": numero})
                    self.assertRegex(respuesta.content.decode("utf-8"), r'<ul class="errorlist field-error"[^>]*role="alert">')


class PruebasRelacionadas(SimpleTestCase):
    def test_tras_convertir_se_sugiere_la_otra_herramienta_del_area(self):
        romanos = self.client.post(RUTA, {"direccion": "decimal_a_romano", "numero": "12"})
        enlaces = [a["href"] for _, a in Documento(romanos).enlaces if a.get("class") == "related-link"]
        self.assertEqual(enlaces, ["/bases/conversion/"])
        bases = self.client.post("/bases/conversion/", {"numero": "13", "base_origen": "10", "bases_destino": ["2"]})
        enlaces = [a["href"] for _, a in Documento(bases).enlaces if a.get("class") == "related-link"]
        self.assertEqual(enlaces, [RUTA])
        # Sin resultado no hay sugerencias.
        for respuesta in (self.client.get(RUTA), self.client.get("/bases/conversion/"),
                          self.client.post(RUTA, {"direccion": "romano_a_decimal", "numero": "IIII"})):
            self.assertNotContains(respuesta, "related-list")


class PruebasTerminologia(SimpleTestCase):
    """P26.1: la herramienta habla de números arábigos, no decimales.

    «Decimal» sigue siendo correcto en Exacto/Decimal y en Conversión de bases,
    que esta página sugiere tras convertir: se prohíben las direcciones
    antiguas, no la palabra.
    """

    DIRECCIONES_ANTIGUAS = re.compile(r"decimal\s*[→↔]\s*romano|romano\s*[→↔]\s*decimal", re.IGNORECASE)

    def test_la_pagina_no_vuelve_a_mostrar_decimal_romano(self):
        respuestas = {
            "sin enviar": self.client.get(RUTA),
            "arábigo → romano": self.client.post(RUTA, {"direccion": "decimal_a_romano", "numero": "1963"}),
            "romano → arábigo": self.client.post(RUTA, {"direccion": "romano_a_decimal", "numero": "MCMLXIII"}),
            "dirección manipulada": self.client.post(RUTA, {"direccion": "hexadecimal", "numero": "12"}),
        }
        for caso, respuesta in respuestas.items():
            with self.subTest(caso=caso):
                html = respuesta.content.decode("utf-8")
                self.assertEqual(self.DIRECCIONES_ANTIGUAS.findall(html), [])
                self.assertIn("<span>Arábigo → romano</span>", html)
                self.assertIn("<span>Romano → arábigo</span>", html)
                entradilla = texto_de(respuesta, 'class="tool-lead"', "p")
                self.assertIn("números arábigos y romanos", entradilla)
                self.assertNotIn("decimal", entradilla.lower())
