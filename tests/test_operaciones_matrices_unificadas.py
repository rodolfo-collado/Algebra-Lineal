"""P26.6: Operaciones con matrices y Expresiones matriciales son una sola herramienta.

Equivalencia con el módulo anterior (fixture capturado antes de editar), ruta histórica,
catálogo final y estructura del procedimiento por nodos del árbol.
"""

import json
import os
import re
from fractions import Fraction
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.test import Client, SimpleTestCase
from django.test.utils import setup_test_environment, teardown_test_environment
from django.urls import resolve
from django.utils.html import strip_tags

from backend.matrices import (
    multiplicar_escalar_matriz, multiplicar_matrices, multiplicar_matriz_vector, restar_matrices, sumar_matrices,
    trasponer_matriz,
)
from frontend.web.calculadora import catalogo
from frontend.web.calculadora.servicios import formatear_matriz
from tests.ayudas import elemento_html
from tests.test_matrices_web import RUTA, Contenido, datos_simbolos, matriz
from tests.test_navegacion import Documento

ANTIGUA = "/matrices/expresiones/"
CAPTURA = json.loads((Path(__file__).parent / "fixtures/operaciones_matrices_p265.json").read_text(encoding="utf-8"))
_CELDA_ANTIGUA = re.compile(r"celda_([A-Za-z]+)_(\d+)_(\d+)")


def json_plano(valor):
    """Tuplas como listas y valores como texto, igual que el fixture."""
    return json.loads(json.dumps(valor, default=str))


def entrada_unificada(caso):
    """El POST del módulo anterior escrito como operandos y expresión del formulario unificado."""
    celdas = {}
    for clave, valor in caso["post"].items():
        partes = _CELDA_ANTIGUA.fullmatch(clave)
        if partes:
            celdas.setdefault(partes.group(1), {})[(int(partes.group(2)), int(partes.group(3)))] = valor
    simbolos = []
    for nombre in sorted(celdas, key=lambda n: (n == "x", n)):
        filas = 1 + max(i for i, _ in celdas[nombre])
        columnas = 1 + max(j for _, j in celdas[nombre])
        valores = [[celdas[nombre][(i, j)] for j in range(columnas)] for i in range(filas)]
        if nombre == "x":
            simbolos.append({"nombre": "x", "tipo": "vector", "valor": [fila[0] for fila in valores]})
        else:
            simbolos.append(matriz(nombre, valores))
    matrices = [simbolo["nombre"] for simbolo in simbolos if simbolo["tipo"] == "matriz"]
    operacion = caso["operacion"]
    if operacion == "escalar":
        simbolos.append({"nombre": "k", "tipo": "escalar", "valor": caso["post"]["escalar"]})
        expresion = "kA"
    elif operacion == "traspuesta":
        expresion = "Aᵀ"
    elif operacion == "matriz_vector":
        expresion = "Ax"
    elif operacion == "producto":
        expresion = "".join(matrices)
    else:
        expresion = (" + " if operacion == "suma" else " - ").join(matrices)
    return datos_simbolos(expresion, simbolos, metodo=caso["metodo"])


class ContextoHTTP(SimpleTestCase):
    # unittest discover no activa la instrumentación de plantillas: sin ella no hay `context`.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_test_environment()
        cls.addClassCleanup(teardown_test_environment)


class PruebasEquivalenciaP265(ContextoHTTP):
    """Fixture capturado ANTES de editar desde develop c5d241e: no se genera con el código bajo prueba."""

    def calcular(self, caso):
        respuesta = self.client.post(RUTA, entrada_unificada(caso))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.context["form"].errors, respuesta.context["form"].errors)
        resultado = json_plano(respuesta.context["resultado"])
        return resultado, [paso for paso in resultado["pasos"] if paso["matricial"]], respuesta.content.decode()

    def test_la_referencia_es_la_del_modulo_anterior(self):
        self.assertEqual(CAPTURA["base"], "c5d241e7df2fb061a6f4eee34346c64b220d78a3")
        self.assertEqual(CAPTURA["ruta_original"], RUTA)
        operaciones = {caso["operacion"] for caso in CAPTURA["casos"]}
        self.assertEqual(operaciones, {"suma", "resta", "escalar", "traspuesta", "producto", "matriz_vector"})
        self.assertEqual(len(CAPTURA["casos"]), 40)

    def test_el_resultado_matematico_es_identico_en_los_40_casos(self):
        for caso in CAPTURA["casos"]:
            with self.subTest(caso=caso["nombre"]):
                resultado, _, html = self.calcular(caso)
                self.assertEqual(resultado["matriz"], caso["resultado"]["matriz"])
                self.assertEqual(Contenido(html).tablas["Resultado"], caso["resultado"]["matriz"])

    def test_suma_resta_escalar_y_traspuesta_de_un_paso_conservan_el_procedimiento(self):
        claves = ("operacion", "desarrollo", "formula", "ayuda", "factor", "traslados", "dimensiones_entrada", "dimensiones_resultado")
        for caso in CAPTURA["casos"]:
            antiguo = caso["resultado"]
            if caso["operacion"] in ("producto", "matriz_vector") or len(antiguo["entradas"]) > 2:
                continue
            with self.subTest(caso=caso["nombre"]):
                _, pasos, _ = self.calcular(caso)
                self.assertEqual(len(pasos), 1)
                nuevo = pasos[0]["matricial"]
                for clave in claves:
                    self.assertEqual(nuevo[clave], antiguo[clave], clave)
                self.assertEqual([(e["nombre"], e["matriz"]) for e in nuevo["entradas"]],
                                 [(e["nombre"], e["matriz"]) for e in antiguo["entradas"]])

    def test_tres_o_mas_matrices_combinan_las_mismas_entradas_en_el_mismo_orden(self):
        # El módulo anterior escribía A + B + C en una celda; el árbol lo hace en pasos: (A + B) + C.
        for caso in CAPTURA["casos"]:
            antiguo = caso["resultado"]
            if caso["operacion"] not in ("suma", "resta") or len(antiguo["entradas"]) <= 2:
                continue
            with self.subTest(caso=caso["nombre"]):
                _, pasos, _ = self.calcular(caso)
                self.assertEqual(len(pasos), len(antiguo["entradas"]) - 1)
                signo = f" {antiguo['simbolo']} "
                for i, fila in enumerate(antiguo["desarrollo"]):
                    for j, celda in enumerate(fila):
                        operandos = pasos[0]["matricial"]["desarrollo"][i][j].split(signo)
                        operandos += [paso["matricial"]["desarrollo"][i][j].split(signo)[1] for paso in pasos[1:]]
                        self.assertEqual(operandos, celda.split(signo))

    def test_productos_conservan_las_lecturas_identicas(self):
        for caso in CAPTURA["casos"]:
            if caso["operacion"] not in ("producto", "matriz_vector"):
                continue
            antiguo = caso["resultado"]
            with self.subTest(caso=caso["nombre"]):
                _, pasos, _ = self.calcular(caso)
                etapas = [etapa["resultado"] for etapa in antiguo["etapas"]] if "etapas" in antiguo else [antiguo]
                self.assertEqual(len(pasos), len(etapas))
                for paso, etapa in zip(pasos, etapas):
                    nuevo = paso["matricial"]
                    # Fila por columna, por columnas o ambas: títulos, fórmulas, cada igualdad y cada matriz.
                    self.assertEqual(nuevo["metodos"], etapa["metodos"])
                    self.assertEqual((nuevo["comparando"], nuevo["abierto"]), (etapa["comparando"], etapa["abierto"]))
                    self.assertEqual(nuevo["matriz"], etapa["matriz"])
                if "etapas" not in antiguo:
                    self.assertEqual(pasos[0]["matricial"]["forma"], antiguo["forma"])

    def test_la_presentacion_dibuja_las_mismas_igualdades(self):
        caso = next(c for c in CAPTURA["casos"] if c["nombre"] == "producto_fracciones_comparar")
        _, _, html = self.calcular(caso)
        texto = " ".join(strip_tags(html).split())
        for metodo in caso["resultado"]["metodos"]:
            for grupo in metodo["grupos"]:
                for linea in grupo.get("lineas", []):
                    self.assertIn(linea, texto)
                if "simbolica" in grupo:
                    self.assertIn(grupo["simbolica"], texto)


class PruebasRutaHistorica(ContextoHTTP):
    def test_get_redirige_con_301_y_conserva_la_consulta(self):
        respuesta = self.client.get(ANTIGUA)
        self.assertEqual((respuesta.status_code, respuesta["Location"]), (301, RUTA))
        respuesta = self.client.get(ANTIGUA, {"a": "1", "b": ["2", "3"]})
        self.assertEqual(respuesta.status_code, 301)
        destino = urlsplit(respuesta["Location"])
        self.assertEqual(destino.path, RUTA)
        self.assertEqual(parse_qs(destino.query), {"a": ["1"], "b": ["2", "3"]})
        final = self.client.get(ANTIGUA, follow=True)
        self.assertEqual(final.redirect_chain, [(RUTA, 301)])
        self.assertEqual(final.context["herramienta_actual"], catalogo.OPERACIONES_MATRICES)
        self.assertContains(final, "Operaciones con matrices · PyGebra")

    def test_post_conserva_el_cuerpo_con_308_y_da_el_mismo_resultado(self):
        ejemplo = [matriz("A", [[2, 5], [3, 1]]), {"nombre": "u", "tipo": "vector", "valor": [4, -1]},
                   {"nombre": "v", "tipo": "vector", "valor": [-3, 5]}]
        lineal = [{"nombre": "A", "tipo": "matriz_desconocida", "filas": 2, "columnas": 2},
                  {"nombre": "x", "tipo": "vector_simbolico", "filas": 2},
                  {"nombre": "b", "tipo": "vector_lineal", "valor": ["x1 + x2", "x2"]}]
        envios = (
            datos_simbolos("A(u + v)", ejemplo),
            datos_simbolos("A(u + v) = Au + Av", ejemplo),
            datos_simbolos("A(u + v)", ejemplo, nodo="0.1"),
            datos_simbolos("Ax = b", lineal),
            datos_simbolos("A + Z", ejemplo),
            datos_simbolos("", ejemplo, agregar="1"),
        )
        for datos in envios:
            with self.subTest(datos=datos.get("expresion"), extra={k: datos[k] for k in ("nodo", "agregar") if k in datos}):
                redireccion = self.client.post(ANTIGUA, datos)
                self.assertEqual((redireccion.status_code, redireccion["Location"]), (308, RUTA))
                legado = self.client.post(ANTIGUA, datos, follow=True)
                directo = self.client.post(RUTA, datos)
                self.assertEqual(legado.redirect_chain, [(RUTA, 308)])
                self.assertEqual(legado.wsgi_request.method, "POST")
                self.assertEqual(legado.wsgi_request.POST, directo.wsgi_request.POST)
                self.assertEqual(json_plano(legado.context["resultado"]), json_plano(directo.context["resultado"]))
                self.assertEqual(legado.context["form"].errors, directo.context["form"].errors)
                self.assertContains(legado, f'action="{RUTA}#resultado"')

    def test_csrf_metodos_y_navegacion(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(ANTIGUA, datos_simbolos("A", [matriz("A", [[1]])])).status_code, 403)
        self.assertEqual(self.client.put(ANTIGUA).status_code, 405)
        # Es un alias de ruta, no una herramienta: no identifica nada en el catálogo.
        self.assertIsNone(catalogo.herramienta_por_ruta(resolve(ANTIGUA)))
        for herramienta in catalogo.herramientas_disponibles():
            with self.subTest(ruta=herramienta.ruta):
                html = self.client.get(herramienta.ruta).content.decode()
                self.assertNotIn(f'href="{ANTIGUA}"', html)
                self.assertNotIn("Expresiones matriciales", html)
        self.assertNotIn(f'href="{ANTIGUA}"', self.client.get("/").content.decode())


class PruebasCatalogoFinal(ContextoHTTP):
    def test_matrices_tiene_cuatro_herramientas_en_orden(self):
        self.assertEqual(
            [h.nombre for h in catalogo.herramientas_de(catalogo.MATRICES)],
            ["Operaciones con matrices", "Reducción por filas", "Resolver Ax = b", "Matriz inversa"],
        )
        herramienta = catalogo.OPERACIONES_MATRICES
        self.assertEqual(herramienta.descripcion, "Realiza y combina operaciones con matrices, vectores y escalares paso a paso.")
        self.assertNotIn("expresiones matriciales", catalogo.MATRICES.descripcion.lower())
        self.assertNotIn("expresiones-matriciales", {r for h in catalogo.HERRAMIENTAS for r in h.relacionadas})

    def test_inicio_menu_y_breadcrumbs(self):
        inicio = self.client.get("/")
        html = inicio.content.decode()
        self.assertIn(f'href="{RUTA}"', elemento_html(html, html.index('id="matrices"'), "details"))
        enlaces = [a["href"] for _, a in Documento(inicio).enlaces if a.get("class") == "tool-link" and a["href"].startswith("/matrices/")]
        self.assertEqual(enlaces, ["/matrices/operaciones/", "/matrices/reduccion/", "/matrices/ecuaciones/", "/matrices/inversa/"])
        menu = [a["href"] for a in Documento(inicio).enlaces_en("Herramientas") if a["href"].startswith("/matrices/")]
        self.assertEqual(menu, enlaces)
        pagina = self.client.get(RUTA)
        documento = Documento(pagina)
        self.assertEqual([a["href"] for a in documento.enlaces_en("Ruta de navegación")], ["/", "/#algebra-lineal", "/#matrices"])
        self.assertContains(pagina, '<span aria-current="page">Operaciones con matrices</span>', html=True)
        self.assertContains(pagina, "Realiza y combina operaciones con matrices, vectores y escalares paso a paso.")

    def test_busquedas_historicas_llevan_a_operaciones_con_y_sin_javascript(self):
        for consulta in ("expresiones matriciales", "expresión", "expresiones", "matrices", "suma", "resta", "producto",
                         "transpuesta", "traspuesta", "2A", "AB", "Aᵀ", "A^T", "combinar"):
            with self.subTest(consulta=consulta):
                self.assertIn(catalogo.OPERACIONES_MATRICES, catalogo.buscar_herramientas(consulta))
                pagina = self.client.get("/", {"q": consulta})
                self.assertContains(pagina, f'href="{RUTA}"')
                self.assertNotContains(pagina, "Expresiones matriciales")
                self.assertIn(catalogo.OPERACIONES_MATRICES.indice, Documento(pagina).indices)
        # Lo propio de otras herramientas sigue sin arrastrarla.
        for consulta in ("gauss", "pivote", "inversa", "resolver", "binario", "romano"):
            self.assertNotIn(catalogo.OPERACIONES_MATRICES, catalogo.buscar_herramientas(consulta))


class PruebasProcedimientoPorNodos(SimpleTestCase):
    SIMBOLOS = [matriz("A", [[1, 2], [3, 4]]), matriz("B", [[0, 1], [1, 0]]), matriz("C", [[2, 0], [0, "1/2"]]),
                matriz("D", [[1, 1], [1, 1]]), {"nombre": "x", "tipo": "vector", "valor": [5, -1]}]

    def pasos(self, expresion, **extra):
        html = self.client.post(RUTA, datos_simbolos(expresion, self.SIMBOLOS, **extra)).content.decode()
        self.assertIn('id="resultado"', html)
        procedimiento = elemento_html(html, html.index('id="procedimiento"'), "details")
        titulos = [" ".join(strip_tags(t).split()) for t in re.findall(r'<h4 class="stage-title expression-step-title">(.*?)</h4>', procedimiento, re.S)]
        return [titulo.split(" · ")[0] for titulo in titulos], procedimiento, html

    def test_cada_nodo_en_el_orden_del_arbol(self):
        casos = {
            "A(B + C)": ["B + C", "A(B + C)"],
            "(A + B)ᵀ": ["A + B", "(A + B)ᵀ"],
            "(A + B)^T": ["A + B", "(A + B)ᵀ"],
            "AB + C": ["AB", "AB + C"],
            "A(B + C) - 2D": ["B + C", "A(B + C)", "2D", "A(B + C) - 2D"],
            "ABᵀ": ["Bᵀ", "ABᵀ"],
            "(AB)ᵀ": ["AB", "(AB)ᵀ"],
            "2A + Bᵀ": ["2A", "Bᵀ", "2A + Bᵀ"],
            "A + B + C": ["A + B", "A + B + C"],
            "A - B - C": ["A - B", "A - B - C"],
        }
        for expresion, esperados in casos.items():
            with self.subTest(expresion=expresion):
                titulos, _, _ = self.pasos(expresion)
                self.assertEqual(titulos, esperados)

    def test_el_resultado_se_muestra_una_vez_y_los_intermedios_cierran_con_su_valor(self):
        _, procedimiento, html = self.pasos("A(B + C)")
        self.assertEqual(html.count('<table class="matrix-table" aria-label="Resultado"'), 1)
        # B + C cierra con su valor (lo usa el paso siguiente); A(B + C) no lo repite.
        self.assertRegex(procedimiento, r'<span class="matrix-expression">B \+ C =</span>\s*<div class="matrix">')
        self.assertIn('aria-label="B + C"', procedimiento)
        self.assertNotIn('aria-label="A(B + C)"', procedimiento)
        self.assertEqual(procedimiento.count('name="nodo"'), 1)
        self.assertIn('name="nodo" value="0.1"', procedimiento)

    def test_la_traspuesta_dentro_de_una_expresion_es_un_paso(self):
        _, procedimiento, _ = self.pasos("2A + Bᵀ")
        texto = " ".join(strip_tags(procedimiento).split())
        self.assertIn("Las filas de B pasan a ser las columnas de Bᵀ.", texto)
        self.assertIn("(Bᵀ)ᵢⱼ = Bⱼᵢ", texto)
        self.assertIn("Fila 1 de B → columna 1 de Bᵀ: 0, 1.", texto)
        self.assertIn("b[i, j] identifica la entrada de B en la fila i, columna j.", texto)
        _, procedimiento, _ = self.pasos("(A + B)ᵀ")
        texto = " ".join(strip_tags(procedimiento).split())
        self.assertIn("Las filas de (A + B) pasan a ser las columnas de (A + B)ᵀ.", texto)
        self.assertIn("((A + B)ᵀ)ᵢⱼ = (A + B)ⱼᵢ", texto)
        self.assertIn("(A + B)[2, 1]", texto)

    def test_productos_compuestos_con_la_lectura_elegida(self):
        _, procedimiento, _ = self.pasos("A(B + C)", metodo="comparar")
        texto = " ".join(strip_tags(procedimiento).split())
        self.assertIn("(A(B + C))₁₁ = fila₁(A) · columna₁(B + C) = a₁₁(B + C)₁₁ + a₁₂(B + C)₂₁", texto)
        self.assertIn("A(B + C)₁ = (B + C)₁₁a₁ + (B + C)₂₁a₂", texto)
        _, procedimiento, _ = self.pasos("(A + B)x", metodo="columnas")
        texto = " ".join(strip_tags(procedimiento).split())
        self.assertIn("(A + B)x = x₁(A + B)₁ + x₂(A + B)₂ = 5(A + B)₁ − (A + B)₂", texto)
        self.assertIn("Combinación lineal de columnas", texto)
        _, procedimiento, _ = self.pasos("AB + C")
        texto = " ".join(strip_tags(procedimiento).split())
        # Dentro de una expresión mayor, las entradas se llaman como el paso, no cᵢⱼ (C es un operando).
        self.assertIn("(AB)₁₁ = fila₁(A) · columna₁(B)", texto)
        self.assertNotIn("c₁₁ = fila₁(A)", texto)

    def test_las_expresiones_del_qa_contra_las_primitivas(self):
        a, b, c = [[1, 2], [3, 4]], [[0, 1], [1, 0]], [[2, 0], [0, Fraction(1, 2)]]
        esperados = {
            "A+B": sumar_matrices(a, b), "A+B+C": sumar_matrices(sumar_matrices(a, b), c),
            "A-B-C": restar_matrices(restar_matrices(a, b), c), "2A": multiplicar_escalar_matriz(2, a),
            "AB": multiplicar_matrices(a, b), "ABC": multiplicar_matrices(multiplicar_matrices(a, b), c),
            "Ax": [[v] for v in multiplicar_matriz_vector(a, [5, -1])],
            "A(B+C)": multiplicar_matrices(a, sumar_matrices(b, c)), "AB+C": sumar_matrices(multiplicar_matrices(a, b), c),
            "Aᵀ": trasponer_matriz(a), "A^T": trasponer_matriz(a), "(A+B)ᵀ": trasponer_matriz(sumar_matrices(a, b)),
            "ABᵀ": multiplicar_matrices(a, trasponer_matriz(b)), "(AB)ᵀ": trasponer_matriz(multiplicar_matrices(a, b)),
        }
        for expresion, esperado in esperados.items():
            with self.subTest(expresion=expresion):
                html = self.client.post(RUTA, datos_simbolos(expresion, self.SIMBOLOS)).content.decode()
                self.assertEqual(Contenido(html).tablas["Resultado"], formatear_matriz(esperado))

    def test_exacto_decimal_alcanza_los_valores_intermedios(self):
        _, procedimiento, html = self.pasos("(A + C)B")
        self.assertIn("1/2", strip_tags(procedimiento))
        self.assertIn("data-numeric", procedimiento)
        self.assertEqual(html.count('id="numeric-mode"'), 1)


class PruebasIgualdadYSubexpresiones(SimpleTestCase):
    SIMBOLOS = [matriz("A", [[1, 2], [3, 4]]), matriz("B", [[0, 1], [1, 0]])]

    def test_igualdades_con_traspuestas_se_comparan_sin_resolver(self):
        verdadera = strip_tags(self.client.post(RUTA, datos_simbolos("(AB)ᵀ = BᵀAᵀ", self.SIMBOLOS)).content.decode())
        self.assertIn("Ambos lados coinciden", verdadera)
        self.assertIn("Ambos lados producen la misma matriz para los valores dados.", verdadera)
        falsa = strip_tags(self.client.post(RUTA, datos_simbolos("(AB)ᵀ = AᵀBᵀ", self.SIMBOLOS)).content.decode())
        self.assertIn("Los resultados son diferentes", falsa)
        incomparable = strip_tags(self.client.post(RUTA, datos_simbolos("A = Aᵀ + B", [matriz("A", [[1, 2, 3]]), matriz("B", [[1], [1], [1]])])).content.decode())
        self.assertIn("No se pueden comparar ambos lados", incomparable)

    def test_calcular_solo_una_parte_con_traspuestas_en_medio(self):
        html = self.client.post(RUTA, datos_simbolos("A(A + B)ᵀ", self.SIMBOLOS, nodo="0.1")).content.decode()
        texto = " ".join(strip_tags(html).split())
        self.assertIn("Subexpresión · 2×2", texto)
        self.assertEqual(Contenido(html).tablas["Resultado"], [["1", "4"], ["3", "4"]])
        html = self.client.post(RUTA, datos_simbolos("A(A + B)ᵀ", self.SIMBOLOS, nodo="0.1.0")).content.decode()
        self.assertEqual(Contenido(html).tablas["Resultado"], [["1", "3"], ["4", "4"]])
        lados = self.client.post(RUTA, datos_simbolos("(AB)ᵀ = BᵀAᵀ", self.SIMBOLOS, nodo="der:0.1")).content.decode()
        self.assertEqual(Contenido(lados).tablas["Resultado"], [["1", "3"], ["2", "4"]])
        # Los botones del procedimiento apuntan a las rutas reales del árbol con traspuestas.
        completo = self.client.post(RUTA, datos_simbolos("A(A + B)ᵀ", self.SIMBOLOS)).content.decode()
        self.assertEqual(re.findall(r'name="nodo" value="([^"]+)"', completo), ["0.1.0", "0.1"])
        for ruta in ("0.2", "0.1.1", "izq:0"):
            respuesta = self.client.post(RUTA, datos_simbolos("A(A + B)ᵀ", self.SIMBOLOS, nodo=ruta))
            self.assertContains(respuesta, "No existe la subexpresión")

    def test_potencias_e_inversas_no_se_interpretan(self):
        for expresion, mensaje in (("A^2", "no calcula potencias"), ("A^-1", "La inversa se calcula en la herramienta Matriz inversa")):
            respuesta = self.client.post(RUTA, datos_simbolos(expresion, self.SIMBOLOS))
            self.assertContains(respuesta, mensaje)
            self.assertNotContains(respuesta, 'id="resultado"')
