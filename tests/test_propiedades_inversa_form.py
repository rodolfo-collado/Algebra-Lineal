"""P26.9: contrato condicional de entrada y flujo equivalente mediante Aplicar."""

import os
import re
from fractions import Fraction
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.http import QueryDict
from django.test import SimpleTestCase

from frontend.web.calculadora.forms_inversa import InversaForm
from tests.test_matrices_web import Contenido

RUTA = "/matrices/inversa/"
CALCULO = "frontend.web.calculadora.views.calcular_inversa_web"
A = [[3, 4], [5, 6]]
B = [[1, 2], [3, 5]]


def entrada(a=A, funcion="ninguna", *, b=None, vector=None, metodo="gauss_jordan", **extra):
    datos = {"orden": str(len(a)), "funcion_adicional": funcion}
    if metodo is not None:
        datos["metodo"] = metodo
    for nombre, matriz in (("A", a), ("B", b), ("b", [[v] for v in vector] if vector is not None else None)):
        if matriz is not None:
            for i, fila in enumerate(matriz):
                for j, valor in enumerate(fila):
                    datos[f"celda_{nombre}_{i}_{j}"] = str(valor)
    return datos | extra


def activos(html):
    """La plantilla inerte del método no participa en el formulario servidor."""
    return re.sub(r"<template\b[^>]*>.*?</template>", "", html, flags=re.S)


class ContratoInversa(SimpleTestCase):
    def validar(self, datos, ajustar=False):
        form = InversaForm(datos, ajustar=ajustar)
        self.assertTrue(form.is_valid(), form.errors)
        return form

    def rechazar(self, datos, mensaje):
        form = InversaForm(datos)
        self.assertFalse(form.is_valid())
        self.assertIn(mensaje, str(form.errors))
        self.assertNotIn("entrada", form.cleaned_data)

    def test_predeterminada_y_compatibilidad_del_post_sin_funcion(self):
        self.assertEqual(InversaForm().estructura["funcion_adicional"], "ninguna")
        datos = entrada()
        del datos["funcion_adicional"]
        self.assertEqual(self.validar(datos).cleaned_data["entrada"]["funcion_adicional"], "ninguna")

    def test_generacion_condicional_y_contrato_exacto(self):
        for funcion in ("ninguna", "inversa_inversa", "traspuesta", "producto", "vector"):
            with self.subTest(funcion=funcion):
                datos = entrada(funcion=funcion, b=B if funcion == "producto" else None,
                                vector=[3, 7] if funcion == "vector" else None, verificar="on")
                form = self.validar(datos)
                resultado = form.cleaned_data["entrada"]
                self.assertEqual(resultado["funcion_adicional"], funcion)
                self.assertIs(resultado["verificar"], True)
                self.assertEqual(resultado["a"], [[Fraction(v) for v in fila] for fila in A])
                self.assertEqual([m["nombre"] for m in form.matrices],
                                 ["A"] + (["B"] if funcion == "producto" else ["b"] if funcion == "vector" else []))
                self.assertEqual(set(resultado), {"a", "metodo", "verificar", "funcion_adicional"}
                                 | ({"b"} if funcion == "producto" else {"vector"} if funcion == "vector" else set()))

    def test_b_y_vector_obligatorios_exactos_y_de_orden_heredado(self):
        form = self.validar(entrada(funcion="producto", b=[["1/2", -2], ["0.25", 3]]))
        self.assertEqual(form.cleaned_data["entrada"]["b"], [[Fraction(1, 2), Fraction(-2)], [Fraction(1, 4), Fraction(3)]])
        form = self.validar(entrada(funcion="vector", vector=["-1/3", "0.5"]))
        self.assertEqual(form.cleaned_data["entrada"]["vector"], [Fraction(-1, 3), Fraction(1, 2)])
        for datos in (entrada(funcion="producto"), entrada(funcion="vector"),
                      entrada(funcion="producto", b=[[1]]), entrada(funcion="vector", vector=[1, 2, 3])):
            self.rechazar(datos, "no coinciden")
        for funcion, extra in (("producto", {"b": [[1, ""], [0, 1]]}), ("vector", {"vector": [3, ""]})):
            self.rechazar(entrada(funcion=funcion, **extra), "Completa")

    def test_identificadores_y_combinaciones_ajenas_rechazados(self):
        for funcion in ("", "desconocida", "producto,vector", "traspuesta+inversa_inversa", "suma", "AX=B"):
            self.rechazar(entrada(funcion=funcion), "función adicional válida")
        for funcion in ("ninguna", "inversa_inversa", "traspuesta"):
            for extra in ({"b": B}, {"vector": [3, 7]}):
                self.rechazar(entrada(funcion=funcion, **extra), "no coinciden")
        self.rechazar(entrada(funcion="producto", b=B, vector=[3, 7]), "no coinciden")
        self.rechazar(entrada(funcion="vector", b=B, vector=[3, 7]), "no coinciden")
        self.rechazar(entrada(expresion="A+B"), "no coinciden")

    def test_repetidos_rechazados_incluso_con_aplicar(self):
        for campo, repetido in (("funcion_adicional", "producto"), ("orden", "3"),
                                ("metodo", "directo_2x2"), ("celda_A_0_0", "9"), ("verificar", "off")):
            datos = QueryDict("", mutable=True)
            datos.update(entrada(verificar="on"))
            datos.appendlist(campo, repetido)
            for ajustar in (False, True):
                form = InversaForm(datos, ajustar=ajustar)
                self.assertFalse(form.is_valid())
                self.assertIn("campos repetidos", str(form.errors))
        for funcion, extra, campo in (("producto", {"b": B}, "celda_B_0_0"),
                                     ("vector", {"vector": [3, 7]}, "celda_b_0_0")):
            datos = QueryDict("", mutable=True)
            datos.update(entrada(funcion=funcion, **extra))
            datos.appendlist(campo, "9")
            self.rechazar(datos, "campos repetidos")

    def test_gauss_automatico_y_directo_manipulado(self):
        for a in ([[7]], [[1, 0, 0], [0, 1, 0], [0, 0, 1]]):
            self.assertEqual(self.validar(entrada(a, metodo=None)).cleaned_data["entrada"]["metodo"], "gauss_jordan")
            self.rechazar(entrada(a, metodo="directo_2x2"), "solo se puede usar cuando A es 2×2")
        self.rechazar(entrada(metodo=None), "Selecciona un método")
        self.assertEqual(self.validar(entrada(metodo="directo_2x2")).cleaned_data["entrada"]["metodo"], "directo_2x2")

    def test_aplicar_conserva_solo_estado_activo_y_supervivientes(self):
        for funcion, extra in (("producto", {"b": B}), ("vector", {"vector": [3, 7]})):
            datos = entrada(funcion=funcion, orden="3", metodo="directo_2x2", verificar="on", **extra)
            datos["celda_A_0_0"] = "1/"
            form = self.validar(datos, ajustar=True)
            iniciales = form.iniciales()
            self.assertEqual(iniciales["metodo"], "gauss_jordan")
            self.assertEqual(iniciales["funcion_adicional"], funcion)
            self.assertIs(iniciales["verificar"], True)
            self.assertEqual(iniciales["celda_A_0_0"], "1/")
            nombre = "B" if funcion == "producto" else "b"
            self.assertEqual(iniciales[f"celda_{nombre}_1_0"], "3" if funcion == "producto" else "7")
            self.assertEqual(iniciales[f"celda_{nombre}_2_0"], "")
            self.assertNotIn("entrada", form.cleaned_data)
        form = self.validar(entrada(funcion="traspuesta", b=B, vector=[3, 7]), ajustar=True)
        self.assertFalse(any(k.startswith(("celda_B_", "celda_b_")) for k in form.iniciales()))
        form = self.validar(entrada(metodo="directo_2x2"), ajustar=True)
        self.assertEqual(form.iniciales()["metodo"], "directo_2x2")


class EntradaServidorSinJavaScript(SimpleTestCase):
    def aplicar(self, datos):
        with patch(CALCULO, side_effect=AssertionError("Aplicar no debe calcular")):
            respuesta = self.client.post(RUTA, datos | {"ajustar": "1"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, 'role="alert"')
        self.assertNotContains(respuesta, 'id="resultado"')
        return respuesta.content.decode()

    def test_radios_comparten_fieldset_labels_y_predeterminada(self):
        html = activos(self.client.get(RUTA).content.decode())
        grupo = re.search(r'<fieldset[^>]*>\s*<legend[^>]*>[^<]*</legend>\s*<div[^>]*>\s*<label[^>]*>\s*<input[^>]*name="funcion_adicional".*?</fieldset>', html, re.S)
        self.assertIsNotNone(grupo)
        radios = re.findall(r'<input[^>]*name="funcion_adicional"[^>]*>', grupo.group())
        self.assertEqual(len(radios), 5)
        self.assertEqual(sum("checked" in radio for radio in radios), 1)
        self.assertIn('value="ninguna"', next(radio for radio in radios if "checked" in radio))
        doc = Contenido(html)
        for radio in radios:
            identificador = re.search(r'id="([^"]+)"', radio).group(1)
            self.assertTrue(doc.labels.get(identificador))
        self.assertRegex(html, r'<legend[^>]*>Aplicaciones y propiedades</legend>')

    def test_b_b_aparecen_solo_con_su_opcion_y_labels(self):
        for funcion in ("ninguna", "inversa_inversa", "traspuesta", "producto", "vector"):
            html = self.aplicar(entrada(funcion=funcion))
            doc = Contenido(html)
            self.assertEqual(set(doc.tablas), {"Matriz A"} | ({"Matriz B"} if funcion == "producto" else {"Vector b"} if funcion == "vector" else set()))
            if funcion in ("producto", "vector"):
                nombre = "B" if funcion == "producto" else "b"
                clave = f"celda_{nombre}_1_0"
                self.assertEqual(doc.labels[doc.campos[clave]["id"]], "Matriz B, fila 2, columna 1" if nombre == "B" else "Vector b, componente 2")
            self.assertNotIn('name="filas_B"', html)
            self.assertNotIn('name="columnas_B"', html)

    def test_selector_metodo_ausente_fuera2_y_vuelve_gauss(self):
        for orden in (1, 3, 5):
            html = activos(self.aplicar(entrada(orden=str(orden), metodo="directo_2x2")))
            self.assertNotRegex(html, r'<input[^>]*type="radio"[^>]*name="metodo"')
            self.assertNotIn("<legend>Método</legend>", html)
        html = activos(self.aplicar(entrada(metodo="gauss_jordan")))
        self.assertEqual(len(re.findall(r'<input[^>]*type="radio"[^>]*name="metodo"', html)), 2)
        self.assertIn('<legend>Método</legend>', html)
        # Sin JS, volver desde una página 3×3 a 2×2 puede enviar solo el
        # tamaño y Aplicar; el selector aparece con el método predeterminado.
        html = activos(self.aplicar({"orden": "2", "funcion_adicional": "ninguna"}))
        radio = re.search(r'<input[^>]*name="metodo"[^>]*value="gauss_jordan"[^>]*>', html).group()
        self.assertIn("checked", radio)

    def test_aplicar_cambio_de_funcion_elimina_entradas_anteriores(self):
        html = self.aplicar(entrada(funcion="vector", b=B))
        self.assertNotIn("celda_B_", activos(html))
        self.assertIn("celda_b_1_0", activos(html))
        html = self.aplicar(entrada(funcion="producto", vector=[3, 7]))
        self.assertNotIn("celda_b_", activos(html))
        self.assertIn("celda_B_1_1", activos(html))
