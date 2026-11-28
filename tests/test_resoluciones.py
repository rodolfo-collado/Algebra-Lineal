"""Cuaderno de resoluciones: contrato, almacén SQLite, guardado, reapertura y gestión."""

import json
import math
import os
import re
import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
import django
django.setup()

from django.http import QueryDict
from django.test import Client, SimpleTestCase, override_settings

from backend.resultados_raices import ClasificacionRaices
from frontend.terminal.historial import Ejercicio, Historial
from frontend.web.calculadora.resoluciones import almacen as modulo_almacen, contrato, registro
from frontend.web.calculadora.resoluciones.almacen import Almacen, AlmacenNoDisponible, CuadernoLleno
from tests import test_biseccion_web, test_conjuntos_web, test_newton_raphson_web, test_secante_web
from tests.test_determinantes_web import datos_det
from tests.test_expresiones_multiples_web import datos as datos_expresiones
from tests.test_ecuaciones_matriciales_web import datos_ecuacion
from tests.test_matrices_web import datos_simbolos
from tests.test_matriz_inversa_web import datos_inversa
from tests.test_regla_falsa_web import RUTA as RUTA_REGLA_FALSA, datos as datos_regla_falsa
from tests.test_sistemas_iterativos_web import RUTA as RUTA_ITERATIVOS
from tests.test_web import datos_matriz


# Un caso válido por herramienta registrada: la ruta Django, la URL y el POST que la resuelve.
CASOS = {
    "reduccion-filas": ("/matrices/reduccion/", datos_matriz([[1, 2, 3], [4, 5, 6]], "gauss")),
    "ecuaciones-matriciales": ("/matrices/ecuaciones/", datos_ecuacion()),
    "matriz-inversa": ("/matrices/inversa/", datos_inversa([[1, 2], [3, 4]], verificar="on")),
    "determinantes": ("/matrices/determinantes/", datos_det()),
    "biseccion": (test_biseccion_web.RUTA, test_biseccion_web.datos()),
    "regla-falsa": (RUTA_REGLA_FALSA, datos_regla_falsa()),
    "newton-raphson": (test_newton_raphson_web.RUTA, test_newton_raphson_web.datos()),
    "secante": (test_secante_web.RUTA, test_secante_web.datos()),
    "metodos-iterativos": (RUTA_ITERATIVOS, datos_ecuacion([[4, 1], [1, 3]], [1, 2], "jacobi")),
    "relaciones-conjuntos": (test_conjuntos_web.RUTA, test_conjuntos_web.datos()),
    "cardinalidades-conjuntos": ("/conjuntos/cardinalidad/", {
        "numero": "2", "modo": "regiones", "expresion": "A ∪ B", "region_1": "3", "region_2": "4",
        "region_3": "5", "universo": "", "accion": "calcular"}),
    "conversion-bases": ("/bases/conversion/", {"numero": "13", "base_origen": "10", "bases_destino": ["2", "16"]}),
    "conversion-romanos": ("/romanos/conversion/", {"direccion": "decimal_a_romano", "numero": "1963"}),
    # Expresiones múltiples con un error parcial: la fila errónea se guarda con su mensaje.
    "operaciones-matrices": ("/matrices/operaciones/", datos_expresiones(("A + B", "A +", "A + B + C"))),
    "independencia-lineal": ("/vectores/independencia/", {
        "dimension": "3", "cantidad": "3", **{f"celda_v{i}_{fila}_0": str(valor)
                                              for i, vector in enumerate(((1, 2, 0), (0, 1, 3), (2, 5, 3)), 1)
                                              for fila, valor in enumerate(vector)}}),
}
AVISO = re.compile(r'<aside class="resolucion-aviso".*?</aside>', re.S)
TOKEN = re.compile(r'name="csrfmiddlewaretoken" value="[^"]*"')


def principal(html):
    """El contenido de la página sin el aviso del cuaderno ni los tokens CSRF (cambian en cada respuesta)."""
    html = html[html.index("<main"):html.index("</main>")]
    return TOKEN.sub("", AVISO.sub("", html))


class CuadernoTemporal:
    """Cada prueba usa su propio archivo; la caché de almacenes no se comparte entre ellas."""

    def setUp(self):
        super().setUp()
        self.carpeta = Path(self.enterContext(TemporaryDirectory(ignore_cleanup_errors=True)))
        self.archivo = self.carpeta / "resoluciones.sqlite3"
        self.enterContext(override_settings(RESOLUCIONES_ARCHIVO=str(self.archivo)))
        self.addCleanup(modulo_almacen._ALMACENES.clear)

    def reiniciar(self):
        """Lo que ocurre al cerrar y volver a abrir la app: un proceso nuevo sin nada en memoria."""
        modulo_almacen._ALMACENES.clear()


@dataclass(frozen=True)
class Paso:
    divisor: int
    resto: Fraction


class ContratoTests(TestCase):
    def test_codificar_conserva_tipos_y_precision(self):
        valor = {
            "fraccion": Fraction(-7, 3), "decimal": Decimal("0.1"), "float": 0.1 + 0.2, "inf": math.inf,
            "conjunto": frozenset({3, 1, 2}), "tupla": (1, (2, 3)), "paso": Paso(2, Fraction(1, 2)),
            "clasificacion": ClasificacionRaices.RAIZ_APROXIMADA, "claves": {1: "a", 2: "b"}, "$raro": 1,
        }
        texto = contrato.serializar({"v": contrato.codificar(valor)})
        leido = contrato.decodificar(json.loads(texto)["v"])
        self.assertEqual(leido["fraccion"], Fraction(-7, 3))
        self.assertEqual(leido["decimal"], Decimal("0.1"))
        self.assertEqual(leido["float"], 0.1 + 0.2)  # todas las cifras del float original
        self.assertEqual(leido["inf"], math.inf)
        self.assertEqual(leido["conjunto"], frozenset({1, 2, 3}))
        self.assertEqual(leido["tupla"], [1, [2, 3]])
        self.assertEqual(leido["paso"], {"divisor": 2, "resto": Fraction(1, 2)})
        self.assertEqual(leido["clasificacion"], "raiz_aproximada")
        self.assertEqual(leido["claves"], {1: "a", 2: "b"})
        self.assertEqual(leido["$raro"], 1)

    def test_rechaza_lo_que_no_es_dato(self):
        with self.assertRaises(contrato.NoCodificable):
            contrato.codificar({"nodo": object()})

    def test_huella_solo_cuenta_la_matematica_y_el_esquema(self):
        base = {"orden": ["2"], "celda_A_0_0": ["1"], "metodo": ["gauss_jordan"]}
        ruidosa = {**base, "celda_A_0_0": [" 1 "], "csrfmiddlewaretoken": ["x"], "confirmacion": ["firma"],
                   "eleccion": ["otra"]}
        self.assertEqual(contrato.huella("matriz-inversa", 1, base), contrato.huella("matriz-inversa", 1, ruidosa))
        self.assertNotEqual(contrato.huella("matriz-inversa", 1, base), contrato.huella("matriz-inversa", 2, base))
        self.assertNotEqual(contrato.huella("matriz-inversa", 1, base),
                            contrato.huella("matriz-inversa", 1, {**base, "celda_A_0_0": ["2"]}))
        presentacion = {**base, "mostrar": ["pasos"]}
        self.assertEqual(contrato.huella("x", 1, base, frozenset({"mostrar"})),
                         contrato.huella("x", 1, presentacion, frozenset({"mostrar"})))

    def test_leer_distingue_danado_de_futuro(self):
        for texto in ("{", "[]", '{"contrato": "otro", "version": 1}',
                      '{"contrato": "pygebra.resolucion", "version": 1, "herramienta": {}}'):
            with self.subTest(texto=texto), self.assertRaises(contrato.DocumentoInvalido):
                contrato.leer(texto)
        with self.assertRaises(contrato.DocumentoFuturo):
            contrato.leer(json.dumps({"contrato": contrato.CONTRATO, "version": contrato.VERSION + 1}))


class AlmacenTests(TestCase):
    def setUp(self):
        self.carpeta = Path(self.enterContext(TemporaryDirectory(ignore_cleanup_errors=True)))
        self.archivo = self.carpeta / "resoluciones.sqlite3"
        self.enterContext(override_settings(TIME_ZONE="America/Managua"))

    def guardar(self, cuaderno, huella="h1", nombre="Inversa", documento=None):
        documento = documento or contrato.serializar({
            "contrato": contrato.CONTRATO, "version": 1, "herramienta": {"ruta": "matriz-inversa", "esquema": 1},
            "entrada": {}, "resultado": {}, "resumen": "det(A) = −2"})
        return cuaderno.guardar(huella=huella, ruta="matriz-inversa", herramienta="matriz-inversa",
                                nombre=nombre, documento=documento)

    def test_persiste_y_no_duplica_ni_sobrescribe(self):
        identificador, nueva = self.guardar(Almacen(self.archivo))
        self.assertTrue(nueva)
        reabierto = Almacen(self.archivo)
        otro, nueva = self.guardar(reabierto, nombre="Otro nombre",
                                   documento=contrato.serializar({"contrato": "cambiado"}))
        self.assertEqual((otro, nueva), (identificador, False))
        ficha, texto = reabierto.obtener(identificador)
        self.assertEqual(ficha["nombre"], "Inversa")
        self.assertEqual(json.loads(texto)["resumen"], "det(A) = −2")
        self.assertEqual(ficha["estado"], "ok")

    def test_ejercicios_agrupan_renombran_y_se_disuelven_sin_perder_resoluciones(self):
        cuaderno = Almacen(self.archivo)
        a, _ = self.guardar(cuaderno, "a")
        b, _ = self.guardar(cuaderno, "b")
        ejercicio = cuaderno.crear_ejercicio("Tarea 3")
        cuaderno.agrupar([a, b], ejercicio)
        cuaderno.renombrar_ejercicio(ejercicio, "Tarea 3 · matriz A")
        cuaderno.renombrar(a, "Determinante")
        self.assertEqual({f["ejercicio"] for f in cuaderno.listar()}, {ejercicio})
        self.assertEqual(cuaderno.ejercicios()[0]["nombre"], "Tarea 3 · matriz A")
        cuaderno.disolver_ejercicio(ejercicio)
        self.assertEqual([f["ejercicio"] for f in cuaderno.listar()], [None, None])
        cuaderno.eliminar([b])
        self.assertEqual([f["nombre"] for f in cuaderno.listar()], ["Determinante"])

    def test_limites_de_tamano(self):
        cuaderno = Almacen(self.archivo)
        with patch.object(modulo_almacen, "MAX_DOCUMENTO", 10), self.assertRaises(CuadernoLleno):
            self.guardar(cuaderno)
        self.guardar(cuaderno, "a")
        with patch.object(modulo_almacen, "MAX_TOTAL", 300), self.assertRaises(CuadernoLleno):
            self.guardar(cuaderno, "b")
        self.assertEqual(len(cuaderno.listar()), 1)

    def test_fila_danada_o_futura_no_impide_leer_las_demas(self):
        cuaderno = Almacen(self.archivo)
        self.guardar(cuaderno, "bien")
        self.guardar(cuaderno, "roto", documento="{no es json")
        self.guardar(cuaderno, "futuro", documento=json.dumps({"contrato": contrato.CONTRATO, "version": 99}))
        estados = {f["id"]: f["estado"] for f in cuaderno.listar()}
        self.assertEqual(sorted(estados.values()), ["danado", "futuro", "ok"])

    def test_archivo_danado_se_aparta_sin_borrarse(self):
        self.archivo.write_bytes(b"esto no es una base de datos SQLite" * 200)
        cuaderno = Almacen(self.archivo)
        self.guardar(cuaderno)
        self.assertIsNotNone(cuaderno.apartado)
        self.assertTrue(cuaderno.apartado.exists())
        self.assertTrue(cuaderno.apartado.read_bytes().startswith(b"esto no es"))
        self.assertEqual(len(cuaderno.listar()), 1)

    def test_bloqueo_temporal_no_aparta_una_base_valida(self):
        self.guardar(Almacen(self.archivo))
        bloqueo = sqlite3.connect(self.archivo)
        bloqueo.execute("BEGIN EXCLUSIVE")
        try:
            cuaderno = Almacen(self.archivo, espera=0.05)
            with self.assertRaises(AlmacenNoDisponible):
                self.guardar(cuaderno, "otra")
            self.assertIsNone(cuaderno.apartado)
            self.assertEqual(list(self.carpeta.glob("*.apartado-*")), [])
        finally:
            bloqueo.rollback()
            bloqueo.close()
        self.assertEqual(len(Almacen(self.archivo).listar()), 1)

    def test_base_creada_por_una_version_mas_reciente_no_se_toca(self):
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("PRAGMA user_version = 7")
        cuaderno = Almacen(self.archivo)
        with self.assertRaises(modulo_almacen.AlmacenFuturo):
            cuaderno.listar()
        self.assertIsNone(cuaderno.apartado)


class GuardarYReabrirTests(CuadernoTemporal, SimpleTestCase):
    def test_todas_las_herramientas_registradas_tienen_caso(self):
        self.assertEqual(set(CASOS), set(registro.ADAPTADORES))

    def test_cada_herramienta_se_guarda_una_vez_y_se_reabre_identica(self):
        cliente = Client()
        for ruta, (url, datos) in CASOS.items():
            with self.subTest(ruta=ruta):
                original = cliente.post(url, datos)
                aviso = original.context_data["resolucion_cuaderno"]
                self.assertEqual(aviso["estado"], "guardada", aviso)
                self.assertContains(original, 'id="resolucion-aviso"')
                # Recargar o volver atrás reenvía el mismo POST: no se anota dos veces.
                recarga = cliente.post(url, datos).context_data["resolucion_cuaderno"]
                self.assertEqual((recarga["estado"], recarga["id"]), ("existente", aviso["id"]))
                reabierta = cliente.get(aviso["url"].split("#")[0])
                self.assertEqual(reabierta.context_data["resolucion_cuaderno"]["estado"], "abierta")
                self.assertEqual(principal(reabierta.content.decode()), principal(original.content.decode()))
        self.assertEqual(len(modulo_almacen.almacen().listar()), len(CASOS))

    def test_reabrir_no_recalcula(self):
        cliente = Client()
        url, datos = CASOS["matriz-inversa"]
        aviso = cliente.post(url, datos).context_data["resolucion_cuaderno"]
        with patch("frontend.web.calculadora.views.calcular_inversa_web", side_effect=AssertionError("recalculó")):
            respuesta = cliente.get(aviso["url"].split("#")[0])
        self.assertContains(respuesta, "A es invertible")

    def test_persiste_despues_de_reiniciar(self):
        url, datos = CASOS["determinantes"]
        aviso = Client().post(url, datos).context_data["resolucion_cuaderno"]
        self.reiniciar()
        cuaderno = Client().get("/resoluciones/")
        self.assertContains(cuaderno, aviso["nombre"])
        self.assertContains(cuaderno, "det(A) = 30")
        self.assertContains(Client().get(aviso["url"].split("#")[0]), "det(A) = 30")

    def test_documento_conserva_entrada_resultado_y_grafica(self):
        url, datos = CASOS["biseccion"]
        respuesta = Client().post(url, datos)
        _, texto = modulo_almacen.almacen().obtener(respuesta.context_data["resolucion_cuaderno"]["id"])
        doc = contrato.leer(texto)
        self.assertEqual(doc["entrada"]["funcion"], [datos["funcion"]])
        self.assertNotIn("csrfmiddlewaretoken", doc["entrada"])
        resultado = contrato.decodificar(doc["resultado"])["resultado"]
        self.assertEqual(resultado["c"], respuesta.context_data["resultado"]["c"])
        self.assertEqual(len(resultado["iteraciones"]), len(respuesta.context_data["resultado"]["iteraciones"]))
        self.assertEqual(doc["grafica"]["tipo"], "funcion")
        self.assertEqual(len(doc["grafica"]["x"]), 801)
        self.assertTrue(doc["resumen"].startswith("x ≈ "))
        self.assertEqual(doc["herramienta"]["id"], "metodos-cerrados")

    def test_presentacion_no_duplica(self):
        cliente = Client()
        url, datos = CASOS["reduccion-filas"]
        primera = cliente.post(url, datos).context_data["resolucion_cuaderno"]
        otra_vista = cliente.post(url, {**datos, "mostrar": ["clasificacion"]}).context_data["resolucion_cuaderno"]
        self.assertEqual(otra_vista["id"], primera["id"])

    def test_expresiones_multiples_conservan_filas_y_errores_parciales(self):
        cliente = Client()
        url, datos = CASOS["operaciones-matrices"]
        aviso = cliente.post(url, datos).context_data["resolucion_cuaderno"]
        self.assertEqual(aviso["nombre"], "Operaciones · A + B (+2)")
        _, texto = modulo_almacen.almacen().obtener(aviso["id"])
        filas = contrato.decodificar(contrato.leer(texto)["resultado"])["resultados"]
        self.assertEqual([f["expresion"] for f in filas], ["A + B", "A +", "A + B + C"])
        self.assertIsNone(filas[1]["resultado"])
        self.assertTrue(filas[1]["error"])
        self.assertEqual(filas[2]["resultado"]["matriz"], [["0", "7"], ["1", "2"], ["7", "-1"]])
        self.assertNotIn("nodo", filas[0])
        reabierta = cliente.get(aviso["url"].split("#")[0])
        self.assertTrue(reabierta.context_data["form"].errors)  # el error de la fila sigue junto a su campo
        # Una sola expresión sin errores también se anota (resultado único).
        sola = cliente.post(url, datos_simbolos("A+B", [
            {"nombre": "A", "tipo": "matriz", "valor": [[1, 2], [3, 4]]},
            {"nombre": "B", "tipo": "matriz", "valor": [[1, 0], [0, 1]]}])).context_data["resolucion_cuaderno"]
        self.assertEqual(sola["estado"], "guardada")

    def test_entrada_invalida_no_se_guarda(self):
        respuesta = Client().post("/romanos/conversion/", {"direccion": "decimal_a_romano", "numero": "abc"})
        self.assertIsNone(respuesta.context_data["resolucion_cuaderno"])
        self.assertEqual(modulo_almacen.almacen().listar(), [])

    def test_cuaderno_no_disponible_no_impide_ver_el_resultado(self):
        url, datos = CASOS["conversion-romanos"]
        with patch.object(Almacen, "guardar", side_effect=AlmacenNoDisponible("database is locked")):
            respuesta = Client().post(url, datos)
        self.assertContains(respuesta, "MCMLXIII")
        self.assertEqual(respuesta.context_data["resolucion_cuaderno"]["estado"], "no_guardada")
        self.assertContains(respuesta, "no se guardó")

    def test_registro_danado_esquema_antiguo_e_inexistente(self):
        cliente = Client()
        url, datos = CASOS["matriz-inversa"]
        identificador = cliente.post(url, datos).context_data["resolucion_cuaderno"]["id"]
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("UPDATE resoluciones SET documento = json_set(documento, '$.herramienta.esquema', 0)")
        antigua = cliente.get(f"{url}?resolucion={identificador}")
        self.assertEqual(antigua.context_data["resolucion_cuaderno"]["estado"], "antiguo")
        self.assertIsNone(antigua.context_data["resultado"])
        self.assertEqual(antigua.context_data["form"].data["celda_A_1_0"], "3")  # los datos siguen cargados
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("UPDATE resoluciones SET documento = '{roto'")
        danada = cliente.get(f"{url}?resolucion={identificador}")
        self.assertEqual(danada.status_code, 200)
        self.assertEqual(danada.context_data["resolucion_cuaderno"]["estado"], "danado")
        self.assertContains(cliente.get("/resoluciones/"), "el registro está dañado")
        for valor in ("999", "x"):
            self.assertEqual(cliente.get(f"{url}?resolucion={valor}").context_data["resolucion_cuaderno"]["estado"], "inexistente")

    def test_otra_herramienta_no_abre_la_resolucion(self):
        cliente = Client()
        url, datos = CASOS["biseccion"]
        identificador = cliente.post(url, datos).context_data["resolucion_cuaderno"]["id"]
        respuesta = cliente.get(f"{RUTA_REGLA_FALSA}?resolucion={identificador}")
        self.assertEqual(respuesta.context_data["resolucion_cuaderno"]["estado"], "otra_ruta")
        self.assertIsNone(respuesta.context_data["resultado"])


class CuadernoTests(CuadernoTemporal, SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.cliente = Client()
        self.ids = {ruta: self.cliente.post(url, datos).context_data["resolucion_cuaderno"]["id"]
                    for ruta, (url, datos) in CASOS.items()}

    def accion(self, **datos):
        return self.cliente.post("/resoluciones/", datos, follow=True)

    def test_cuaderno_en_blanco(self):
        modulo_almacen.almacen().eliminar(list(self.ids.values()))
        respuesta = self.cliente.get("/resoluciones/")
        self.assertContains(respuesta, "Tu cuaderno está en blanco")
        self.assertContains(respuesta, 'href="/matrices/determinantes/"')

    def test_agrupar_desde_el_cuaderno_y_desde_la_herramienta(self):
        respuesta = self.accion(accion="agrupar", ids=[self.ids["determinantes"], self.ids["matriz-inversa"]],
                                ejercicio="nuevo", nombre_ejercicio="Tarea 3 · matriz A")
        self.assertContains(respuesta, "Llevaste 2 resoluciones a «Tarea 3 · matriz A».")
        ejercicio = modulo_almacen.almacen().ejercicios()[0]["id"]
        # Desde el aviso de la herramienta: vuelve a la resolución, ya dentro del ejercicio.
        respuesta = self.cliente.post("/resoluciones/", {
            "accion": "agrupar", "ids": [self.ids["ecuaciones-matriciales"]], "ejercicio": str(ejercicio),
            "volver_a": "herramienta"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta["Location"].startswith(f"/matrices/ecuaciones/?resolucion={self.ids['ecuaciones-matriciales']}"))
        reabierta = self.cliente.get(respuesta["Location"].split("#")[0])
        self.assertEqual(reabierta.context_data["resolucion_cuaderno"]["ejercicio"]["nombre"], "Tarea 3 · matriz A")
        hoja = self.cliente.get("/resoluciones/").content.decode()
        seccion = hoja[hoja.index(f'id="ejercicio-{ejercicio}"'):hoja.index('id="sueltas-titulo"')]
        self.assertEqual(seccion.count('class="hoja-entrada"'), 3)
        # Sin nombre, el ejercicio se numera; sacar devuelve las resoluciones a «Sueltas».
        self.accion(accion="agrupar", ids=[self.ids["secante"]], ejercicio="nuevo", nombre_ejercicio="  ")
        self.assertEqual(modulo_almacen.almacen().ejercicios()[-1]["nombre"], "Ejercicio 2")
        self.assertContains(self.accion(accion="sacar", ids=[self.ids["secante"]]), "ahora están sueltas")

    def test_buscar_y_filtrar(self):
        self.accion(accion="agrupar", ids=[self.ids["biseccion"]], ejercicio="nuevo", nombre_ejercicio="Raíces de la práctica")
        def resultados(**filtros):
            contexto = self.cliente.get("/resoluciones/", filtros).context_data
            return {fila["id"] for fila in contexto["coincidencias"]}

        self.assertEqual(resultados(q="mcmlxiii"), {self.ids["conversion-romanos"]})  # por el resultado
        self.assertEqual(resultados(q="RAICES practica"), {self.ids["biseccion"]})  # por el ejercicio, sin tildes
        self.assertEqual(resultados(herramienta="metodos-abiertos"), {self.ids["newton-raphson"], self.ids["secante"]})
        self.assertEqual(len(resultados(desde="2000-01-01", hasta="2999-12-31")), len(CASOS))
        self.assertEqual(resultados(q="tarea inexistente"), set())
        self.assertEqual(resultados(hasta="2000-01-01"), set())
        vacio = self.cliente.get("/resoluciones/", {"q": "zzz"})
        self.assertContains(vacio, "Nada coincide con esos filtros.")

    def test_renombrar(self):
        respuesta = self.accion(accion="renombrar", id=self.ids["determinantes"], nombre="  det de la tarea  ")
        self.assertContains(respuesta, "det de la tarea")
        self.assertContains(self.accion(accion="renombrar", id=self.ids["determinantes"], nombre=" "),
                            "Escribe un nombre")

    def test_eliminar_pide_confirmacion(self):
        objetivo = self.ids["conversion-bases"]
        confirmacion = self.cliente.post("/resoluciones/", {"accion": "eliminar", "ids": [objetivo]})
        self.assertContains(confirmacion, "¿Eliminar esta resolución?")
        self.assertEqual(len(modulo_almacen.almacen().listar()), len(CASOS))
        hecho = self.accion(accion="eliminar_confirmado", ids=[objetivo])
        self.assertContains(hecho, "Eliminaste 1 resolución del cuaderno.")
        self.assertNotIn(objetivo, {f["id"] for f in modulo_almacen.almacen().listar()})
        self.assertContains(self.accion(accion="eliminar"), "Primero marca al menos una resolución.")

    def test_las_acciones_conservan_los_filtros(self):
        respuesta = self.cliente.post("/resoluciones/", {
            "accion": "renombrar", "id": self.ids["secante"], "nombre": "Secante",
            "filtros": QueryDict("q=x&herramienta=metodos-abiertos&malicioso=1").urlencode()})
        self.assertEqual(respuesta["Location"].split("#")[0],
                         "/resoluciones/?q=x&herramienta=metodos-abiertos&hecho=renombrada")

    def test_cuaderno_no_disponible(self):
        with patch.object(Almacen, "listar", side_effect=AlmacenNoDisponible("database is locked")):
            respuesta = self.cliente.get("/resoluciones/")
        self.assertEqual(respuesta.status_code, 503)
        self.assertContains(respuesta, "Tus resoluciones anteriores siguen a salvo", status_code=503)


class MigracionTests(TestCase):
    """Un cuaderno v1 (solo ejercicios planos) pasa a v2 sin perder nada y con respaldo."""

    def setUp(self):
        self.carpeta = Path(self.enterContext(TemporaryDirectory(ignore_cleanup_errors=True)))
        self.archivo = self.carpeta / "resoluciones.sqlite3"
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.executescript(modulo_almacen.MIGRACIONES[1])
            db.execute("PRAGMA user_version = 1")
            db.execute("INSERT INTO ejercicios (nombre, creado) VALUES ('Tarea 3', '2026-11-27T10:00:00-06:00')")
            for i, ejercicio in ((1, 1), (2, 1), (3, None)):
                db.execute("INSERT INTO resoluciones (huella, ruta, herramienta, nombre, ejercicio, creado, usado, documento)"
                           " VALUES (?, 'matriz-inversa', 'matriz-inversa', ?, ?, '2026-11-27T10:00:00-06:00',"
                           " '2026-11-27T10:00:00-06:00', '{}')", (f"h{i}", f"R{i}", ejercicio))

    def test_v1_a_v2_conserva_todo_y_deja_respaldo(self):
        cuaderno = Almacen(self.archivo)
        self.assertEqual([(f["nombre"], f["ejercicio"]) for f in sorted(cuaderno.listar(), key=lambda f: f["id"])],
                         [("R1", 1), ("R2", 1), ("R3", None)])
        ejercicio, = cuaderno.ejercicios()
        self.assertEqual((ejercicio["nombre"], ejercicio["proyecto"], ejercicio["incluir"]), ("Tarea 3", None, 1))
        self.assertEqual(cuaderno.proyectos(), [])
        with closing(sqlite3.connect(self.archivo)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], modulo_almacen.VERSION_BASE)
        respaldo = self.archivo.with_name("resoluciones.v1-respaldo.sqlite3")
        with closing(sqlite3.connect(respaldo)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM resoluciones").fetchone()[0], 3)

    def test_migracion_fallida_no_deja_el_cuaderno_a_medias(self):
        with patch.dict(modulo_almacen.MIGRACIONES, {2: "ALTER TABLE ejercicios ADD COLUMN numero TEXT; SELECT * FROM no_existe;"}):
            with self.assertRaises(AlmacenNoDisponible):
                Almacen(self.archivo).listar()
        with closing(sqlite3.connect(self.archivo)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            columnas = {fila[1] for fila in db.execute("PRAGMA table_info(ejercicios)")}
            self.assertNotIn("numero", columnas)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM resoluciones").fetchone()[0], 3)
        self.assertEqual(len(Almacen(self.archivo).listar()), 3)  # y la migración real sigue funcionando


class ProyectosTests(CuadernoTemporal, SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.cliente = Client()
        self.cliente.post("/resoluciones/", {"accion": "crear_proyecto", "nombre": "Banco de Álgebra Lineal",
                                              "objetivo": "64"})
        self.cuaderno = modulo_almacen.almacen()
        self.proyecto = self.cuaderno.proyectos()[0]["id"]
        self.url = f"/resoluciones/proyectos/{self.proyecto}/"

    def accion(self, **datos):
        return self.cliente.post(self.url, datos, follow=True)

    def numeros(self):
        return [e["numero"] for e in self.cuaderno.ejercicios(self.proyecto)]

    def test_orden_natural_de_los_numeros(self):
        numeros = ["10", "2", "3b", "1.10", "3a", None, "1.2", "1"]
        self.assertEqual(sorted(numeros, key=modulo_almacen.clave_numero), ["1", "1.2", "1.10", "2", "3a", "3b", "10", None])

    def test_crear_proyecto_lo_activa_y_prepara_64_ejercicios(self):
        self.assertEqual(self.cuaderno.activo(), (self.proyecto, None))
        respuesta = self.accion(accion="crear_ejercicios", proyecto=self.proyecto, desde="1", hasta="60")
        self.assertContains(respuesta, "Creaste 60 ejercicios nuevos.")
        self.assertEqual(len(self.numeros()), 60)
        self.accion(accion="crear_ejercicios", proyecto=self.proyecto, desde="55", hasta="64")  # sin repetir
        self.assertEqual(self.numeros(), [str(n) for n in range(1, 65)])
        self.assertContains(self.accion(accion="crear_ejercicios", proyecto=self.proyecto, desde="1", hasta="900"),
                            "hasta 200 de una vez")
        contexto = self.cliente.get(self.url).context_data
        self.assertEqual(contexto["progreso"], {"resueltos": 0, "total": 64, "creados": 64, "objetivo": 64,
                                                "porcentaje": 0, "pendientes_por_crear": 0})

    def test_numeros_titulos_enunciados_y_orden(self):
        for numero, titulo in (("3", "Tercero"), ("1", ""), ("10", "Décimo"), ("2", "Segundo")):
            self.accion(accion="crear_ejercicio", proyecto=self.proyecto, numero=numero, nombre=titulo)
        self.assertEqual(self.numeros(), ["3", "1", "10", "2"])
        self.assertContains(self.accion(accion="ordenar", proyecto=self.proyecto), "Ordenaste los ejercicios por número.")
        self.assertEqual(self.numeros(), ["1", "2", "3", "10"])
        tercero = next(e["id"] for e in self.cuaderno.ejercicios(self.proyecto) if e["numero"] == "3")
        self.accion(op=f"mover:ejercicios:{tercero}:-1")
        self.assertEqual(self.numeros(), ["1", "3", "2", "10"])
        self.accion(accion="editar_ejercicio", id=tercero, numero="3", nombre="Inversa de A",
                    enunciado="Calcula A⁻¹ y comprueba AA⁻¹ = I.")
        ejercicio = next(e for e in self.cuaderno.ejercicios(self.proyecto) if e["id"] == tercero)
        self.assertEqual((ejercicio["nombre"], ejercicio["enunciado"]), ("Inversa de A", "Calcula A⁻¹ y comprueba AA⁻¹ = I."))
        pagina = self.cliente.get(self.url)
        self.assertContains(pagina, "Calcula A⁻¹ y comprueba AA⁻¹ = I.")
        self.assertContains(pagina, "Inversa de A")

    def test_secciones_agrupan_y_quitarlas_no_pierde_ejercicios(self):
        self.accion(accion="crear_ejercicios", proyecto=self.proyecto, desde="1", hasta="4")
        self.accion(accion="crear_seccion", proyecto=self.proyecto, nombre="Matrices")
        seccion = self.cuaderno.secciones(self.proyecto)[0]["id"]
        primero, segundo = [e["id"] for e in self.cuaderno.ejercicios(self.proyecto)][:2]
        for ejercicio in (primero, segundo):
            self.accion(accion="editar_ejercicio", id=ejercicio, numero="", nombre="x", ubicacion=f"s:{seccion}")
        grupos = self.cliente.get(self.url).context_data["grupos"]
        self.assertEqual([len(g["ejercicios"]) for g in grupos], [2, 2])
        self.assertEqual(grupos[1]["seccion"]["titulo"], "Matrices")
        self.accion(accion="eliminar_seccion", id=seccion)
        self.assertEqual(len(self.cuaderno.ejercicios(self.proyecto)), 4)
        self.assertEqual(self.cuaderno.secciones(self.proyecto), [])

    def test_proyecto_activo_y_anadir_con_un_clic_desde_la_herramienta(self):
        self.accion(accion="crear_ejercicios", proyecto=self.proyecto, desde="1", hasta="3")
        segundo = [e["id"] for e in self.cuaderno.ejercicios(self.proyecto)][1]
        self.accion(accion="activar", proyecto=self.proyecto, ejercicio=segundo)
        url, datos = CASOS["matriz-inversa"]
        respuesta = self.cliente.post(url, datos)
        self.assertContains(respuesta, 'id="proyecto-activo"')  # visible en la herramienta
        self.assertContains(respuesta, "Añadir a Ej. 2")
        aviso = respuesta.context_data["resolucion_cuaderno"]
        destino = self.cliente.post("/resoluciones/", {"accion": "agrupar", "ids": aviso["id"], "ejercicio": segundo,
                                                       "volver_a": "herramienta"})
        reabierta = self.cliente.get(destino["Location"].split("#")[0])
        self.assertEqual(reabierta.context_data["resolucion_cuaderno"]["ejercicio"]["etiqueta"], "Ejercicio 2")
        self.assertNotContains(reabierta, "Añadir a Ej. 2")  # ya está en él
        # Crear un ejercicio nuevo desde el indicador lo deja activo.
        self.cliente.post("/resoluciones/", {"accion": "crear_ejercicio", "proyecto": self.proyecto, "numero": "4",
                                             "activar": "1", "volver": "/matrices/inversa/"})
        self.assertEqual(self.cuaderno.activo()[1], self.cuaderno.ejercicios(self.proyecto)[-1]["id"])
        self.cliente.post("/resoluciones/", {"accion": "desactivar"})
        self.assertNotContains(self.cliente.get("/matrices/inversa/"), 'id="proyecto-activo"')

    def test_volver_solo_a_rutas_locales(self):
        for volver in ("https://ejemplo.com/", "//ejemplo.com/x", "javascript:alert(1)"):
            respuesta = self.cliente.post("/resoluciones/", {"accion": "desactivar", "volver": volver})
            self.assertTrue(respuesta["Location"].startswith("/resoluciones/"), respuesta["Location"])

    def test_borrador_excluye_sin_borrar_y_persiste(self):
        self.accion(accion="crear_ejercicios", proyecto=self.proyecto, desde="1", hasta="3")
        ejercicios = [e["id"] for e in self.cuaderno.ejercicios(self.proyecto)]
        ids = []
        for ruta in ("matriz-inversa", "determinantes"):
            url, datos = CASOS[ruta]
            ids.append(self.cliente.post(url, datos).context_data["resolucion_cuaderno"]["id"])
        self.cliente.post("/resoluciones/", {"accion": "agrupar", "ids": ids, "ejercicio": ejercicios[0]})
        self.accion(op=f"incluir:resoluciones:{ids[1]}:0")
        self.accion(op=f"incluir:ejercicios:{ejercicios[2]}:0")
        self.reiniciar()
        contexto = self.cliente.get(self.url).context_data
        self.assertEqual(contexto["borrador"], {"ejercicios": 2, "resoluciones": 1, "sin_resolver": 1})
        indice = [e["id"] for g in contexto["indice"] for e in g["ejercicios"]]
        self.assertEqual(indice, ejercicios[:2])
        self.assertEqual(len(modulo_almacen.almacen().listar()), 2)  # nada se borró
        # Reordenar resoluciones dentro del ejercicio también persiste.
        self.accion(op=f"mover:resoluciones:{ids[1]}:-1")
        primero = self.cliente.get(self.url).context_data["grupos"][0]["ejercicios"][0]
        self.assertEqual([r["id"] for r in primero["resoluciones"]], [ids[1], ids[0]])

    def test_proyecto_reune_resoluciones_de_todos_los_modulos(self):
        self.accion(accion="crear_ejercicios", proyecto=self.proyecto, desde="1", hasta=str(len(CASOS)))
        ejercicios = [e["id"] for e in self.cuaderno.ejercicios(self.proyecto)]
        for ejercicio, (url, datos) in zip(ejercicios, CASOS.values()):
            aviso = self.cliente.post(url, datos).context_data["resolucion_cuaderno"]
            self.cliente.post("/resoluciones/", {"accion": "agrupar", "ids": aviso["id"], "ejercicio": ejercicio})
        contexto = self.cliente.get(self.url).context_data
        self.assertEqual(contexto["progreso"]["resueltos"], len(CASOS))
        herramientas = {r["herramienta"] for g in contexto["grupos"] for e in g["ejercicios"] for r in e["resoluciones"]}
        self.assertEqual(len(herramientas), 13)  # catálogo: métodos cerrados/abiertos agrupan dos rutas
        self.assertFalse([r for g in contexto["grupos"] for e in g["ejercicios"] for r in e["resoluciones"] if not r["url"]])

    def test_mover_quitar_y_eliminar_sin_perder_resoluciones(self):
        self.cliente.post("/resoluciones/", {"accion": "crear_proyecto", "nombre": "Otro"})
        otro = next(p["id"] for p in self.cuaderno.proyectos() if p["nombre"] == "Otro")
        self.accion(accion="crear_ejercicio", proyecto=self.proyecto, numero="1", nombre="Inversa")
        ejercicio = self.cuaderno.ejercicios(self.proyecto)[0]["id"]
        url, datos = CASOS["matriz-inversa"]
        resolucion = self.cliente.post(url, datos).context_data["resolucion_cuaderno"]["id"]
        self.cliente.post("/resoluciones/", {"accion": "agrupar", "ids": resolucion, "ejercicio": ejercicio})
        self.accion(accion="editar_ejercicio", id=ejercicio, numero="1", nombre="Inversa", ubicacion=f"p:{otro}")
        self.assertEqual([e["id"] for e in self.cuaderno.ejercicios(otro)], [ejercicio])
        self.accion(accion="editar_ejercicio", id=ejercicio, numero="1", nombre="Inversa", ubicacion="independiente")
        self.assertEqual(self.cuaderno.ejercicios(None)[0]["id"], ejercicio)
        self.accion(accion="editar_ejercicio", id=ejercicio, numero="1", nombre="Inversa", ubicacion=f"p:{self.proyecto}")
        confirmacion = self.accion(accion="eliminar_proyecto", proyecto=self.proyecto)
        self.assertContains(confirmacion, "siguen en el cuaderno como ejercicios independientes")
        self.assertEqual(len(self.cuaderno.proyectos()), 2)
        self.cliente.post(self.url, {"accion": "eliminar_proyecto_confirmado", "proyecto": self.proyecto})
        self.assertEqual([p["nombre"] for p in self.cuaderno.proyectos()], ["Otro"])
        self.assertEqual(self.cuaderno.ejercicios(None)[0]["id"], ejercicio)
        self.assertEqual(self.cuaderno.listar()[0]["ejercicio"], ejercicio)
        self.assertEqual(self.cliente.get(self.url).status_code, 404)

    def test_proyecto_de_64_ejercicios_sigue_siendo_agil(self):
        self.accion(accion="crear_seccion", proyecto=self.proyecto, nombre="Sistemas")
        self.accion(accion="crear_ejercicios", proyecto=self.proyecto, desde="1", hasta="60")
        ejercicios = [e["id"] for e in self.cuaderno.ejercicios(self.proyecto)]
        for indice, (url, datos) in enumerate(list(CASOS.values()) * 3):
            aviso = self.cliente.post(url, datos).context_data["resolucion_cuaderno"]
            self.cliente.post("/resoluciones/", {"accion": "agrupar", "ids": aviso["id"],
                                                 "ejercicio": ejercicios[indice % len(ejercicios)]})
        inicio = time.perf_counter()
        pagina = self.cliente.get(self.url)
        transcurrido = time.perf_counter() - inicio
        self.assertLess(transcurrido, 3, f"La página del proyecto tardó {transcurrido:.2f} s")
        contexto = pagina.context_data
        self.assertEqual(len(contexto["mapa"]), 60)
        self.assertEqual(len(contexto["huecos"]), 4)  # objetivo 64: cuatro casillas por preparar
        self.assertEqual(contexto["progreso"]["resueltos"], len(CASOS))
        self.assertEqual(pagina.content.decode().count('class="hoja ejercicio"'), 60)
        pendientes = self.cliente.get(self.url, {"ver": "pendientes"}).context_data
        self.assertEqual(sum(len(g["ejercicios"]) for g in pendientes["grupos"]), 60 - len(CASOS))


class HistorialConsolaTests(TestCase):
    """La consola omite un ejercicio dañado sin perder los demás ni sus ajustes."""

    def test_registro_danado_no_borra_el_historial(self):
        with TemporaryDirectory(ignore_cleanup_errors=True) as carpeta:
            historial = Historial(Path(carpeta) / "consola.sqlite3")
            historial.abrir()
            historial.agregar(Ejercicio("conversion", "Conversión · 42", {"numero": "42"}, ("Resultado",)))
            historial.preferencia("tema", "pygebra-claro")
            with closing(sqlite3.connect(historial.archivo)) as db, db:
                db.execute("INSERT INTO ejercicios (datos) VALUES ('{roto')")
                db.execute("""INSERT INTO ejercicios (datos) VALUES ('{"comando": "x"}')""")
            ejercicios, ajustes = historial.abrir()
            self.assertEqual([e.titulo for e in ejercicios], ["Conversión · 42"])
            self.assertEqual(ajustes, {"tema": "pygebra-claro"})
            self.assertEqual(historial.omitidos, 2)
