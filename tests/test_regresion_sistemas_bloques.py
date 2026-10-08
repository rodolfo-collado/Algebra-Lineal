"""P26.3 conserva Sistemas y Ax = b respecto de develop tras el PR #60.

Las expectativas estáticas proceden del árbol Git indicado en la fixture,
incluidos todos los pasos, sustituciones y el texto del panel final de Django.
No se calcula una solución alternativa para construir las expectativas.
"""

from fractions import Fraction
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase
from django.utils.html import strip_tags

from backend.ecuaciones_matriciales import resolver_ecuacion_matricial
from backend.parser_sistemas import analizar_sistema
from backend.sistemas import resolver_sistema_gauss, resolver_sistema_gauss_jordan
from frontend.web.calculadora.servicios import resolver_entrada_web, resolver_sistema_web
from frontend.web.calculadora.servicios_ecuaciones import resolver_ecuacion_web
from tests._regresion_sistemas_bloques_base import CASOS_BASE
from tests.ayudas import antes_de_p2711, elemento_html
from tests.test_web import datos_matriz


RESOLVERS = {
    "gauss": resolver_sistema_gauss,
    "gauss_jordan": resolver_sistema_gauss_jordan,
}


def exactos(valor):
    """Serialización de pruebas que conserva índices, tipos lógicos y racionales."""
    if isinstance(valor, Fraction):
        return str(valor)
    if isinstance(valor, dict):
        return {clave: exactos(elemento) for clave, elemento in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [exactos(elemento) for elemento in valor]
    return valor


def matriz_del_caso(caso):
    return [[Fraction(valor) for valor in fila] for fila in caso["matriz"]]


def resultado_base(caso, metodo):
    """Recompone las partes estáticas compartidas y propias de cada método."""
    propios = caso[metodo]
    resultado = {
        **caso["comun"],
        **{clave: valor for clave, valor in propios.items()
           if clave not in {"pasos", "pasos_adicionales", "sustitucion_web"}},
    }
    pasos = list(caso["gauss"]["pasos"])
    if metodo == "gauss_jordan":
        pasos.extend(propios["pasos_adicionales"])
    resultado["pasos"] = [
        {"operacion": operacion, "antes": antes, "despues": despues}
        for operacion, antes, despues in pasos
    ]
    return resultado


def presentacion_base(caso, metodo):
    """Contrato textual y estructural original, sin usar adaptadores productivos."""
    resultado = resultado_base(caso, metodo)
    gauss = metodo == "gauss"
    clave_matriz = "matriz_escalonada" if gauss else "matriz_reducida"
    clasificacion_clave = {
        "Consistente de solución única": "unica",
        "Consistente de soluciones infinitas": "infinitas",
        "Inconsistente": "inconsistente",
    }[resultado["clasificacion"]]
    return {
        "metodo": "Gauss" if gauss else "Gauss-Jordan",
        "matriz_inicial": caso["matriz"],
        "pasos": [{"numero": numero, **paso}
                  for numero, paso in enumerate(resultado["pasos"], start=1)],
        "matriz_final": resultado[clave_matriz],
        "columnas_pivote": resultado["columnas_pivote"],
        "etiqueta_matriz": "Matriz escalonada" if gauss else "Matriz reducida",
        "mostrar_sistema_resultante": not resultado["solucion_directa"],
        "ecuaciones_resultantes": resultado["ecuaciones_resultantes"],
        "clasificacion": resultado["clasificacion"],
        "clasificacion_clave": clasificacion_clave,
        "justificacion": resultado["justificacion"],
        "solucion_general": resultado["solucion_general"],
        "sustitucion": caso[metodo]["sustitucion_web"],
    }


class PruebasRegresionSistemasBloques(SimpleTestCase):
    def test_backend_conserva_resultado_completo_y_procedimiento_de_ambos_motores(self):
        for nombre, caso in CASOS_BASE.items():
            for metodo, resolver in RESOLVERS.items():
                with self.subTest(caso=nombre, metodo=metodo):
                    matriz = matriz_del_caso(caso)
                    resultado = resolver(matriz)
                    self.assertEqual(exactos(resultado), resultado_base(caso, metodo))
                    self.assertEqual(exactos(matriz), caso["matriz"])
                    clave = "matriz_escalonada" if metodo == "gauss" else "matriz_reducida"
                    self.assertTrue(all(isinstance(valor, Fraction)
                                        for fila in resultado[clave] for valor in fila))
                    self.assertTrue(all(isinstance(valor, Fraction)
                                        for valor in resultado["soluciones"]))

    def test_parser_conserva_matriz_y_reescrituras_originales(self):
        for nombre, caso in CASOS_BASE.items():
            with self.subTest(caso=nombre):
                matriz, reescritas = analizar_sistema(caso["texto"], limitar_entrada=True)
                self.assertEqual(exactos([[Fraction(v) for v in fila] for fila in matriz]), caso["matriz"])
                self.assertEqual(reescritas, caso["reescritas"])

    def test_servicios_de_texto_y_matriz_conservan_todo_el_contrato(self):
        for nombre, caso in CASOS_BASE.items():
            for metodo in RESOLVERS:
                with self.subTest(caso=nombre, metodo=metodo):
                    esperado = presentacion_base(caso, metodo)
                    self.assertEqual(
                        resolver_entrada_web("matriz", metodo, matriz_aumentada=matriz_del_caso(caso)),
                        esperado,
                    )
                    esperado_texto = {**esperado, "reescritas": caso["reescritas"]}
                    self.assertEqual(
                        resolver_entrada_web("sistema", metodo, texto=caso["texto"]), esperado_texto
                    )
                    self.assertEqual(resolver_sistema_web(caso["texto"], metodo), esperado_texto)

    def test_ax_b_conserva_la_misma_resolucion_y_comprobacion_exacta(self):
        for nombre, caso in CASOS_BASE.items():
            matriz = matriz_del_caso(caso)
            a, b = [fila[:-1] for fila in matriz], [fila[-1] for fila in matriz]
            for metodo in RESOLVERS:
                with self.subTest(caso=nombre, metodo=metodo):
                    calculo = resolver_ecuacion_matricial(a, b, metodo)
                    base = resultado_base(caso, metodo)
                    self.assertEqual(exactos({clave: calculo[clave] for clave in base}), base)
                    self.assertEqual(exactos(calculo["matriz_aumentada"]), caso["matriz"])
                    unica = bool(base["soluciones"])
                    self.assertEqual(exactos(calculo["x"]), base["soluciones"] if unica else None)
                    self.assertEqual(calculo["verificacion"], b if unica else None)
                    self.assertEqual(calculo["b_en_generado"], base["clasificacion"] != "Inconsistente")
                    presentado = resolver_ecuacion_web({"a": a, "b": b, "metodo": metodo})
                    self.assertEqual(presentado["metodos"], [presentacion_base(caso, metodo)])
                    self.assertEqual(presentado["clasificacion"], base["clasificacion"])
                    self.assertEqual(presentado["solucion_general"], base["solucion_general"])
                    if unica:
                        self.assertTrue(presentado["comprobacion"]["coincide"])
                    else:
                        self.assertIsNone(presentado["comprobacion"])

    def test_ax_b_comparar_conserva_los_dos_procedimientos_y_un_resultado(self):
        for nombre, caso in CASOS_BASE.items():
            with self.subTest(caso=nombre):
                matriz = matriz_del_caso(caso)
                presentado = resolver_ecuacion_web({
                    "a": [fila[:-1] for fila in matriz], "b": [fila[-1] for fila in matriz], "metodo": "comparar"
                })
                self.assertEqual(presentado["metodos"], [presentacion_base(caso, metodo) for metodo in RESOLVERS])
                self.assertEqual(presentado["clasificacion"], caso["comun"]["clasificacion"])
                self.assertEqual(presentado["solucion_general"], caso["comun"]["solucion_general"])

    def test_django_conserva_el_panel_final_en_ambas_entradas_y_al_comparar(self):
        for nombre, caso in CASOS_BASE.items():
            for metodo in (*RESOLVERS, "comparar"):
                entradas = {
                    "matriz": datos_matriz(matriz_del_caso(caso), metodo),
                    "sistema": {"tipo_entrada": "sistema", "metodo": metodo, "sistema": caso["texto"]},
                }
                for tipo, datos in entradas.items():
                    with self.subTest(caso=nombre, metodo=metodo, entrada=tipo):
                        respuesta = self.client.post("/matrices/reduccion/", datos)
                        self.assertEqual(respuesta.status_code, 200)
                        # P27.11 solo cambia el título del panel, la leyenda y la notación x₁.
                        html = antes_de_p2711(respuesta.content.decode("utf-8"))
                        panel = elemento_html(html, html.index('class="panel panel-final"'), "section")
                        self.assertEqual(" ".join(strip_tags(panel).split()), caso["final_html"])
                        self.assertEqual(html.count('id="final-title"'), 1)
                        self.assertLess(html.index('id="procedimiento"'), html.index('id="final-title"'))
