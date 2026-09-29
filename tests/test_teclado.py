"""Teclado matemático contextual: un solo componente por herramienta y perfiles declarativos."""

import json
import os
import re
import unittest
from fractions import Fraction
from html.parser import HTMLParser
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase

from backend.parser_sistemas import convertir_a_numero, parsear_sistema
from backend.sistemas_numericos import BASES_SOPORTADAS, NOMBRES_BASE, normalizar_numero, simbolo_de_valor
from frontend.web.calculadora import teclados
from frontend.web.calculadora.teclados import (
    PERFIL_NUMERICO,
    PERFIL_SISTEMA,
    PERFILES,
    PERFILES_BASE,
    GrupoTeclas,
    Perfil,
    Tecla,
    perfiles_para,
    variables,
)


RAIZ = Path(__file__).resolve().parents[1]
STATIC = RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora"

# Cada herramienta declara solo los perfiles que usa; el registro no cambia por pantalla.
HERRAMIENTAS = {
    "/sistemas/": {"sistema", "numerico"},
    "/vectores/operaciones/": {"numerico"},
    "/matrices/operaciones/": {"numerico"},
    "/matrices/expresiones/": {"numerico"},
    "/matrices/ecuaciones/": {"numerico"},
    "/bases/conversion/": {"base-2", "base-8", "base-10", "base-16"},
}

# Contrato HTTP de cada formulario tal como existía antes del teclado único: no debe cambiar.
CONTROLES = {
    "/sistemas/": {
        "csrfmiddlewaretoken", "ecuaciones", "metodo", "mostrar", "mostrar_definido", "sistema",
        "tipo_entrada", "variables",
    },
    "/vectores/operaciones/": {
        "ajustar", "csrfmiddlewaretoken", "dimension", "operacion", "u_0", "u_1", "u_2", "v_0", "v_1",
        "v_2", "vectores",
    },
    "/matrices/operaciones/": {
        "ajustar", "celda_A_0_0", "celda_A_0_1", "celda_A_1_0", "celda_A_1_1", "celda_B_0_0",
        "celda_B_0_1", "celda_B_1_0", "celda_B_1_1", "columnas", "columnas_b", "csrfmiddlewaretoken", "cantidad",
        "filas", "metodo", "operacion",
    },
    "/matrices/ecuaciones/": {
        "ajustar", "celda_A_0_0", "celda_A_0_1", "celda_A_1_0", "celda_A_1_1", "celda_b_0_0",
        "celda_b_1_0", "columnas", "csrfmiddlewaretoken", "filas", "metodo",
    },
    "/matrices/expresiones/": {
        "ajustar", "agregar", "cantidad", "celda_0_0_0", "celda_0_0_1", "celda_0_1_0", "celda_0_1_1",
        "columnas_0", "csrfmiddlewaretoken", "eliminar", "expresion", "filas_0", "nombre_0", "tipo_0",
    },
    "/bases/conversion/": {"base_origen", "bases_destino", "csrfmiddlewaretoken", "numero"},
}

VACIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Botones(HTMLParser):
    """Localiza botones y en qué grupo (teclado o estructura) aparecen."""

    def __init__(self, html):
        super().__init__()
        self.botones = []
        self._grupos = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag == "div" and "class" in atributos and "math-keyboard" in atributos["class"].split():
            self._grupos.append(("teclado", atributos))
        elif tag == "div" and atributos.get("aria-label") == "Estructura de la matriz":
            self._grupos.append(("estructura", atributos))
        elif tag == "div":
            self._grupos.append((None, atributos))
        if tag == "button":
            grupos = [nombre for nombre, _ in self._grupos if nombre]
            self.botones.append((grupos[-1] if grupos else None, atributos))

    def handle_endtag(self, tag):
        if tag == "div" and self._grupos:
            self._grupos.pop()


class Pagina(HTMLParser):
    """Lo que una herramienta declara al teclado: componente, perfiles publicados y campos.

    Sigue la jerarquía de elementos para saber en qué contenedor `data-perfil`
    cae cada campo y qué antecesores tiene el componente.
    """

    def __init__(self, html):
        super().__init__()
        self.teclados = []
        self.desplegables = []
        self.json = {}
        self.campos = []
        self.contenedores = {}
        self.controles = set()
        self.dentro_del_teclado = []
        self.aria_live = []
        self.elementos = []
        self._pila = []
        self._json_id = None
        self._texto = ""
        self.feed(html)

    def _clases(self, atributos):
        return atributos.get("class", "").split()

    def _perfil_actual(self):
        return next((attrs["data-perfil"] for _, attrs in reversed(self._pila) if "data-perfil" in attrs), None)

    def _antecesores(self):
        return [tag for tag, _ in self._pila]

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        # template es inerte: sus controles todavía no pertenecen al formulario.
        inerte = "template" in self._antecesores()
        formulario = next((a for t, a in reversed(self._pila) if t == "form"), {})
        if not inerte:
            self.elementos.append({**atributos, "perfil": self._perfil_actual(), "formulario": formulario.get("id")})
        if "aria-live" in atributos:
            self.aria_live.append((tag, atributos))
        if "data-perfil" in atributos:
            self.contenedores[atributos.get("id") or f"{tag}#{len(self.contenedores)}"] = atributos["data-perfil"]
        if tag == "details" and "disclosure-keyboard" in self._clases(atributos):
            self.desplegables.append({**atributos, "summary": ""})
        if tag == "summary" and self._pila and "disclosure-keyboard" in self._clases(self._pila[-1][1]):
            self._texto = "summary"
        if tag == "div" and "math-keyboard" in self._clases(atributos):
            self.teclados.append({**atributos, "antecesores": self._antecesores(), "perfil": self._perfil_actual()})
        if tag == "script" and atributos.get("type") == "application/json":
            self._json_id = atributos.get("id")
            self._texto = "json"
        if any("math-keyboard" in self._clases(a) for _, a in self._pila):
            self.dentro_del_teclado.append((tag, atributos))
        if not inerte and (tag == "textarea" or (tag == "input" and atributos.get("type", "text") == "text")):
            self.campos.append({"name": atributos.get("name"), "perfil": atributos.get("data-perfil", self._perfil_actual()), "tag": tag})
        if not inerte and formulario.get("method", "").lower() == "post" and tag in ("input", "select", "textarea", "button") and atributos.get("name"):
            self.controles.add(atributos["name"])
        if tag not in VACIOS:
            self._pila.append((tag, atributos))

    def handle_data(self, data):
        if self._texto == "summary":
            self.desplegables[-1]["summary"] += data
        elif self._texto == "json":
            self.json[self._json_id] = json.loads(data)

    def handle_endtag(self, tag):
        if tag in ("summary", "script"):
            self._texto = ""
        if tag not in VACIOS and self._pila:
            for indice in range(len(self._pila) - 1, -1, -1):
                if self._pila[indice][0] == tag:
                    del self._pila[indice:]
                    break

    @property
    def perfiles_publicados(self):
        return self.json[self.teclados[0]["data-perfiles"]]


class PruebasRegistro(unittest.TestCase):
    def test_una_tecla_necesita_etiqueta_insercion_y_nombre(self):
        for etiqueta, insercion, nombre in (("", "x", "n"), ("x", "", "n"), ("x", "x", " ")):
            with self.subTest(etiqueta=etiqueta, insercion=insercion, nombre=nombre):
                with self.assertRaises(ValueError):
                    Tecla(etiqueta, insercion, nombre)

    def test_el_retroceso_queda_dentro_de_lo_insertado(self):
        self.assertEqual(Tecla("( )", "()", "Paréntesis", retroceso=1).retroceso, 1)
        with self.assertRaises(ValueError):
            Tecla("( )", "()", "Paréntesis", retroceso=3)

    def test_las_variables_muestran_subindices_e_insertan_sintaxis_del_parser(self):
        teclas = variables(3)
        self.assertEqual([t.etiqueta for t in teclas], ["x₁", "x₂", "x₃"])
        self.assertEqual([t.insercion for t in teclas], ["x1", "x2", "x3"])
        self.assertEqual(teclas[0].nombre, "Variable x1")

    def test_un_perfil_rechaza_ids_invalidos_grupos_vacios_y_teclas_repetidas(self):
        menos = Tecla("−", "-", "Menos")
        with self.assertRaises(ValueError):
            GrupoTeclas(" ", (menos,))
        with self.assertRaises(ValueError):
            GrupoTeclas("Valores", ())
        for id_ in ("", "Sistema", "base 2", "matriz/aumentada"):
            with self.subTest(id=id_):
                with self.assertRaises(ValueError):
                    Perfil(id_, (GrupoTeclas("Valores", (menos,)),))
        with self.assertRaises(ValueError):
            Perfil("vacio", ())
        # La misma inserción con dos etiquetas, o la misma etiqueta con dos inserciones, confunde.
        with self.assertRaises(ValueError):
            Perfil("repetido", (GrupoTeclas("A", (menos,)), GrupoTeclas("B", (Tecla("-", "-", "Guion"),))))
        with self.assertRaises(ValueError):
            Perfil("repetido", (GrupoTeclas("A", (menos, Tecla("−", "–", "Raya"))),))

    def test_el_registro_tiene_seis_perfiles_completos_sin_duplicados(self):
        self.assertEqual(set(PERFILES), {"sistema", "numerico", "base-2", "base-8", "base-10", "base-16"})
        for id_, perfil in PERFILES.items():
            with self.subTest(perfil=id_):
                self.assertIsInstance(perfil, Perfil)
                self.assertEqual(perfil.id, id_)
                self.assertTrue(perfil.grupos)
                self.assertTrue(perfil.ayuda.strip())
                for grupo in perfil.grupos:
                    self.assertIsInstance(grupo, GrupoTeclas)
                    self.assertTrue(grupo.teclas)
                etiquetas = [tecla.etiqueta for tecla in perfil.teclas]
                inserciones = [tecla.insercion for tecla in perfil.teclas]
                self.assertEqual(len(etiquetas), len(set(etiquetas)))
                self.assertEqual(len(inserciones), len(set(inserciones)))
                self.assertTrue(all(tecla.nombre.strip() for tecla in perfil.teclas))
        self.assertFalse(hasattr(teclados, "TecladoContextual"))
        self.assertFalse(hasattr(teclados, "TECLADOS"))

    def test_notacion_visible_distinta_de_la_sintaxis_interna(self):
        por_etiqueta = {tecla.etiqueta: tecla.insercion for tecla in PERFIL_SISTEMA.teclas}
        self.assertEqual(por_etiqueta["−"], "-")
        self.assertEqual(por_etiqueta["a⁄b"], "/")
        self.assertEqual(por_etiqueta["x₁"], "x1")
        self.assertEqual(por_etiqueta["; nueva ecuación"], ";\n")
        self.assertEqual([grupo.nombre for grupo in PERFIL_SISTEMA.grupos], ["Variables", "Operaciones", "Ecuaciones"])

    def test_lo_que_inserta_el_perfil_de_sistema_lo_entiende_el_parser(self):
        tecla = {t.nombre: t.insercion for t in PERFIL_SISTEMA.teclas}
        texto = (
            "2" + tecla["Variable x1"] + tecla["Más"] + tecla["Variable x2"] + tecla["Igual"] + "3"
            + tecla["Separar la siguiente ecuación"]
            + tecla["Variable x1"] + tecla["Menos"] + "1" + tecla["Barra de fracción"] + "2"
            + tecla["Variable x2"] + tecla["Igual"] + "1"
        )
        matriz = parsear_sistema(texto)
        self.assertEqual(len(matriz), 2)
        self.assertEqual([str(valor) for valor in matriz[1]], ["1", "-1/2", "1"])

    def test_el_perfil_numerico_solo_ofrece_signo_y_fraccion_y_los_toma_del_perfil_de_sistema(self):
        self.assertEqual([t.insercion for t in PERFIL_NUMERICO.teclas], ["-", "/"])
        self.assertEqual([grupo.nombre for grupo in PERFIL_NUMERICO.grupos], ["Valores"])
        # Las mismas teclas, no copias: el registro compone grupos.
        self.assertTrue(set(PERFIL_NUMERICO.teclas) <= set(PERFIL_SISTEMA.teclas))
        menos, fraccion = (t.insercion for t in PERFIL_NUMERICO.teclas)
        self.assertEqual(convertir_a_numero(menos + "1" + fraccion + "2"), Fraction(-1, 2))

    def test_los_perfiles_de_base_corresponden_a_los_digitos_de_cada_base(self):
        self.assertEqual(set(PERFILES_BASE), set(BASES_SOPORTADAS))
        for base, perfil in PERFILES_BASE.items():
            with self.subTest(base=base):
                self.assertEqual(perfil.id, f"base-{base}")
                self.assertEqual([grupo.nombre for grupo in perfil.grupos], ["Dígitos", "Separador", "Signo"])
                digitos = [tecla.insercion for tecla in perfil.grupos[0].teclas]
                self.assertEqual(digitos, [simbolo_de_valor(valor) for valor in range(base)])
                self.assertEqual([tecla.insercion for tecla in perfil.teclas], digitos + [".", "-"])
                self.assertEqual([tecla.etiqueta for tecla in perfil.teclas], digitos + [".", "−"])
                self.assertIs(perfil.teclas[-1], teclados.MENOS)
                self.assertEqual(perfil.teclas[-1].insercion, "-")
                self.assertEqual(len({tecla.insercion for tecla in perfil.teclas}), len(perfil.teclas))
                self.assertEqual(len({tecla.etiqueta for tecla in perfil.teclas}), len(perfil.teclas))
                self.assertEqual(normalizar_numero("0.1", base), "0.1")
                self.assertEqual(normalizar_numero("-1", base), "-1")
                self.assertEqual(normalizar_numero("".join(digitos), base), "".join(digitos))
                self.assertEqual(teclados.digitos(base), "".join(digitos))
        self.assertEqual(teclados.digitos(2), "01")
        self.assertEqual(teclados.digitos(8), "01234567")
        self.assertEqual(teclados.digitos(10), "0123456789")
        self.assertEqual(teclados.digitos(16), "0123456789ABCDEF")
        self.assertNotIn("2", teclados.digitos(2))
        self.assertNotIn("8", teclados.digitos(8))
        self.assertNotIn("A", teclados.digitos(10))

    def test_perfiles_para_publica_solo_lo_declarado_y_es_serializable(self):
        publicado = perfiles_para("sistema", "numerico")
        self.assertEqual(list(publicado), ["sistema", "numerico"])
        self.assertEqual(json.loads(json.dumps(publicado)), publicado)
        numerico = publicado["numerico"]
        self.assertEqual(numerico["ayuda"], PERFIL_NUMERICO.ayuda)
        self.assertEqual(
            numerico["grupos"],
            [{"nombre": "Valores", "teclas": [
                {"etiqueta": "−", "insercion": "-", "nombre": "Menos", "retroceso": 0},
                {"etiqueta": "a⁄b", "insercion": "/", "nombre": "Barra de fracción", "retroceso": 0},
            ]}],
        )
        self.assertEqual(perfiles_para(), {})
        with self.assertRaises(KeyError):
            perfiles_para("sistema", "limites")


class PruebasTecladoEnPantalla(SimpleTestCase):
    def pagina(self, ruta):
        return Pagina(self.client.get(ruta).content.decode("utf-8"))

    def test_cada_herramienta_tiene_un_solo_teclado_contextual_oculto(self):
        for ruta, perfiles in HERRAMIENTAS.items():
            with self.subTest(ruta=ruta):
                pagina = self.pagina(ruta)
                self.assertEqual(len(pagina.teclados), 1)
                self.assertEqual(len(pagina.desplegables), 1)
                teclado, desplegable = pagina.teclados[0], pagina.desplegables[0]
                self.assertIn("hidden", teclado)
                self.assertIn("hidden", desplegable)
                self.assertNotIn("open", desplegable)
                self.assertEqual(desplegable["summary"].strip(), "Teclado matemático")
                # El nombre accesible no depende del perfil activo.
                self.assertEqual(teclado["role"], "group")
                self.assertEqual(teclado["aria-label"], "Teclado matemático")
                self.assertEqual(set(pagina.perfiles_publicados), perfiles)
                self.assertTrue(set(pagina.contenedores.values()) <= perfiles)
                self.assertTrue(pagina.contenedores)
                # El servidor no dibuja teclas ni controles de formulario: las genera teclado.js.
                self.assertEqual([tag for tag, _ in pagina.dentro_del_teclado if tag in ("button", "input", "select", "textarea")], [])
                self.assertNotIn("data-teclado-para", teclado)
                self.assertEqual(pagina.aria_live, [(t, a) for t, a in pagina.aria_live if "math-keyboard" not in a.get("class", "")])

    def test_los_perfiles_publicados_son_los_del_registro(self):
        for ruta, perfiles in HERRAMIENTAS.items():
            with self.subTest(ruta=ruta):
                self.assertEqual(self.pagina(ruta).perfiles_publicados, perfiles_para(*sorted(perfiles)))

    def test_cada_campo_de_texto_cae_en_un_contenedor_con_perfil(self):
        for ruta in HERRAMIENTAS:
            with self.subTest(ruta=ruta):
                pagina = self.pagina(ruta)
                self.assertTrue(pagina.campos)
                for campo in pagina.campos:
                    self.assertIn(campo["perfil"], pagina.perfiles_publicados, campo)

    def test_sistemas_cambia_de_perfil_entre_el_texto_y_la_matriz_con_un_solo_componente(self):
        pagina = self.pagina("/sistemas/")
        self.assertEqual(pagina.contenedores["system-fields"], "sistema")
        self.assertEqual(pagina.contenedores["matrix-fields"], "numerico")
        textarea = next(campo for campo in pagina.campos if campo["tag"] == "textarea")
        self.assertEqual((textarea["name"], textarea["perfil"]), ("sistema", "sistema"))
        # Las celdas las crea matriz.js dentro del contenedor numérico: heredan su perfil.
        html = self.client.get("/sistemas/").content.decode("utf-8")
        self.assertRegex(html, r'id="matrix-fields"[^>]*data-perfil="numerico"')
        self.assertLess(html.index('id="matrix-fields"'), html.index('id="matrix-grid"'))
        # Un solo componente, fuera de ambos fieldsets: ocultar uno no oculta el teclado.
        self.assertNotIn("fieldset", pagina.teclados[0]["antecesores"])
        self.assertIsNone(pagina.teclados[0]["perfil"])

    def test_las_celdas_dinamicas_nacen_dentro_del_contenedor_numerico(self):
        for ruta, atributo, valor, formulario in (
            ("/matrices/operaciones/", "data-matrix-list", "", "matrices-form"),
            ("/matrices/ecuaciones/", "data-equation-entry", "", "ecuacion-form"),
            ("/vectores/operaciones/", "id", "vector-list", "vectores-form"),
        ):
            with self.subTest(ruta=ruta):
                elemento = next(e for e in self.pagina(ruta).elementos if atributo in e and (e[atributo] or "") == valor)
                self.assertEqual(elemento["perfil"], "numerico")
                self.assertEqual(elemento["formulario"], formulario)

    def test_bases_publica_los_cuatro_perfiles_y_el_contenedor_sigue_a_la_base_de_origen(self):
        pagina = self.pagina("/bases/conversion/")
        self.assertEqual(pagina.contenedores["number-fields"], "base-10")
        numero = next(campo for campo in pagina.campos if campo["name"] == "numero")
        self.assertEqual(numero["perfil"], "base-10")
        respuesta = self.client.post("/bases/conversion/", {"numero": "", "base_origen": "16", "bases_destino": ["2"]})
        self.assertEqual(Pagina(respuesta.content.decode("utf-8")).contenedores["number-fields"], "base-16")
        # Un solo componente cambia de dígitos: no hay un teclado por base.
        self.assertNotIn("base-keyboard", respuesta.content.decode("utf-8"))
        self.assertEqual(len(Pagina(respuesta.content.decode("utf-8")).teclados), 1)

    def test_la_validacion_en_vivo_de_bases_comparte_los_digitos_del_teclado(self):
        pagina = self.pagina("/bases/conversion/")
        bases = pagina.json["bases-digitos"]
        self.assertEqual(set(bases), {str(base) for base in BASES_SOPORTADAS})
        for base, datos in bases.items():
            with self.subTest(base=base):
                perfil = pagina.perfiles_publicados[datos["perfil"]]
                self.assertEqual(datos["perfil"], f"base-{base}")
                self.assertEqual(datos["nombre"], NOMBRES_BASE[int(base)])
                self.assertEqual(datos["digitos"], [tecla["insercion"] for grupo in perfil["grupos"] for tecla in grupo["teclas"]])
                self.assertEqual(
                    datos["digitos"],
                    [simbolo_de_valor(valor) for valor in range(int(base))] + [".", "-"],
                )
        # conversion.js no lleva otra lista de dígitos ni conoce los perfiles por su nombre.
        script = (STATIC / "conversion.js").read_text(encoding="utf-8")
        self.assertIn("bases-digitos", script)
        self.assertIn("data-perfil", script.replace("dataset.perfil", "data-perfil"))
        for literal in ("0123456789", "ABCDEF", '"01"', "base-2", "base-16", "data-teclado"):
            self.assertNotIn(literal, script)

    def test_el_inicio_no_muestra_teclado(self):
        respuesta = self.client.get("/")
        self.assertNotContains(respuesta, "math-keyboard")
        self.assertNotContains(respuesta, "calculadora/teclado.js")

    def test_los_controles_de_estructura_van_aparte_del_teclado(self):
        html = self.client.get("/sistemas/").content.decode("utf-8")
        estructura = [attrs for grupo, attrs in Botones(html).botones if grupo == "estructura"]
        self.assertEqual(
            sorted(boton["aria-label"] for boton in estructura),
            ["Agregar una ecuación", "Agregar una variable", "Quitar una ecuación", "Quitar una variable"],
        )
        for boton in estructura:
            self.assertEqual(boton["type"], "button")
            self.assertIn("hidden", boton)
            self.assertNotIn("data-insercion", boton)

    def test_el_contrato_http_de_cada_formulario_no_cambia(self):
        for ruta, controles in CONTROLES.items():
            with self.subTest(ruta=ruta):
                self.assertEqual(self.pagina(ruta).controles, controles)

    def test_sin_javascript_los_formularios_siguen_resolviendo(self):
        respuesta = self.client.post("/sistemas/", {"metodo": "gauss", "sistema": "x1 + x2 = 3; x1 - x2 = 1"})
        self.assertContains(respuesta, "x1 = 2")
        respuesta = self.client.post("/bases/conversion/", {"numero": "1010", "base_origen": "2", "bases_destino": ["10"]})
        self.assertContains(respuesta, "10")
        self.assertEqual(len(Pagina(respuesta.content.decode("utf-8")).teclados), 1)
        self.assertIn("hidden", Pagina(respuesta.content.decode("utf-8")).teclados[0])

    def test_las_teclas_nacen_de_plantillas_inertes_accesibles(self):
        html = self.client.get("/sistemas/").content.decode("utf-8")
        tecla = re.search(r'<template id="math-key-template">(.*?)</template>', html, re.S).group(1)
        self.assertRegex(tecla, r'<button[^>]*type="button"')
        self.assertIn('class="math-key"', tecla)
        self.assertIn("data-insercion", tecla)
        self.assertIn("data-retroceso", tecla)
        grupo = re.search(r'<template id="math-key-group-template">(.*?)</template>', html, re.S).group(1)
        self.assertIn('role="group"', grupo)
        self.assertIn("math-keyboard-group-name", grupo)
        self.assertIn('class="math-keys"', grupo)
        self.assertEqual(html.count('id="math-key-template"'), 1)

    def test_teclado_js_es_generico_y_conserva_las_reglas_de_insercion(self):
        script = (STATIC / "teclado.js").read_text(encoding="utf-8")
        # El contrato con la página son atributos declarativos, no ids de herramientas.
        for atributo in ("data-perfil", "data-perfiles", "data-insercion", "data-retroceso", "math-key-template", "math-key-group-template"):
            self.assertIn(atributo, script)
        for ajeno in (
            "system-fields", "matrix-fields", "number-fields", "vector-fields", "equation-fields",
            "tipo_entrada", "base_origen", "numero", "sistema", "matriz", "matrices", "vectores",
            "ecuaciones", "bases", "numerico", "conversion",
        ):
            self.assertNotIn(ajeno, script)
        # Inserción en el cursor (reemplazando la selección), retroceso, evento input y foco.
        self.assertIn("setRangeText(", script)
        self.assertIn('"end"', script)
        self.assertIn("retroceso", script)
        self.assertIn('new Event("input", { bubbles: true })', script)
        self.assertIn(".focus()", script)
        # Sin anuncios en vivo ni abrir el desplegable por su cuenta.
        self.assertNotIn("aria-live", script)
        self.assertNotIn("open = true", script)
        # Delegación: los campos dinámicos no registran listeners uno a uno.
        self.assertIn('"focusin"', script)
        self.assertIn("MutationObserver", script)

    def test_scripts_locales_del_teclado_y_la_estructura(self):
        for ruta in HERRAMIENTAS:
            with self.subTest(ruta=ruta):
                self.assertContains(self.client.get(ruta), "calculadora/teclado.js")
        matriz = (STATIC / "matriz.js").read_text(encoding="utf-8")
        self.assertIn("data-estructura", matriz)
        self.assertIn("renderMatrix", matriz)
        self.assertContains(self.client.get("/sistemas/"), "calculadora/matriz.js")


if __name__ == "__main__":
    unittest.main()
