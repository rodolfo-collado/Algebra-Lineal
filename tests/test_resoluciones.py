"""Cuaderno de resoluciones: contrato, almacén SQLite, guardado, reapertura y gestión."""

import json
import math
import os
import re
import sqlite3
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
                aviso = original.context_data["resolucion"]
                self.assertEqual(aviso["estado"], "guardada", aviso)
                self.assertContains(original, 'id="resolucion-aviso"')
                # Recargar o volver atrás reenvía el mismo POST: no se anota dos veces.
                recarga = cliente.post(url, datos).context_data["resolucion"]
                self.assertEqual((recarga["estado"], recarga["id"]), ("existente", aviso["id"]))
                reabierta = cliente.get(aviso["url"].split("#")[0])
                self.assertEqual(reabierta.context_data["resolucion"]["estado"], "abierta")
                self.assertEqual(principal(reabierta.content.decode()), principal(original.content.decode()))
        self.assertEqual(len(modulo_almacen.almacen().listar()), len(CASOS))

    def test_reabrir_no_recalcula(self):
        cliente = Client()
        url, datos = CASOS["matriz-inversa"]
        aviso = cliente.post(url, datos).context_data["resolucion"]
        with patch("frontend.web.calculadora.views.calcular_inversa_web", side_effect=AssertionError("recalculó")):
            respuesta = cliente.get(aviso["url"].split("#")[0])
        self.assertContains(respuesta, "A es invertible")

    def test_persiste_despues_de_reiniciar(self):
        url, datos = CASOS["determinantes"]
        aviso = Client().post(url, datos).context_data["resolucion"]
        self.reiniciar()
        cuaderno = Client().get("/resoluciones/")
        self.assertContains(cuaderno, aviso["nombre"])
        self.assertContains(cuaderno, "det(A) = 30")
        self.assertContains(Client().get(aviso["url"].split("#")[0]), "det(A) = 30")

    def test_documento_conserva_entrada_resultado_y_grafica(self):
        url, datos = CASOS["biseccion"]
        respuesta = Client().post(url, datos)
        _, texto = modulo_almacen.almacen().obtener(respuesta.context_data["resolucion"]["id"])
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

    def test_presentacion_no_duplica_y_operaciones_queda_fuera(self):
        cliente = Client()
        url, datos = CASOS["reduccion-filas"]
        primera = cliente.post(url, datos).context_data["resolucion"]
        otra_vista = cliente.post(url, {**datos, "mostrar": ["clasificacion"]}).context_data["resolucion"]
        self.assertEqual(otra_vista["id"], primera["id"])
        operaciones = cliente.post("/matrices/operaciones/", datos_simbolos(
            "A+B", [{"nombre": "A", "tipo": "matriz", "valor": [[1, 2], [3, 4]]},
                    {"nombre": "B", "tipo": "matriz", "valor": [[1, 0], [0, 1]]}]))
        self.assertNotIn("resolucion", operaciones.context_data)

    def test_entrada_invalida_no_se_guarda(self):
        respuesta = Client().post("/romanos/conversion/", {"direccion": "decimal_a_romano", "numero": "abc"})
        self.assertIsNone(respuesta.context_data["resolucion"])
        self.assertEqual(modulo_almacen.almacen().listar(), [])

    def test_cuaderno_no_disponible_no_impide_ver_el_resultado(self):
        url, datos = CASOS["conversion-romanos"]
        with patch.object(Almacen, "guardar", side_effect=AlmacenNoDisponible("database is locked")):
            respuesta = Client().post(url, datos)
        self.assertContains(respuesta, "MCMLXIII")
        self.assertEqual(respuesta.context_data["resolucion"]["estado"], "no_guardada")
        self.assertContains(respuesta, "no se guardó")

    def test_registro_danado_esquema_antiguo_e_inexistente(self):
        cliente = Client()
        url, datos = CASOS["matriz-inversa"]
        identificador = cliente.post(url, datos).context_data["resolucion"]["id"]
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("UPDATE resoluciones SET documento = json_set(documento, '$.herramienta.esquema', 0)")
        antigua = cliente.get(f"{url}?resolucion={identificador}")
        self.assertEqual(antigua.context_data["resolucion"]["estado"], "antiguo")
        self.assertIsNone(antigua.context_data["resultado"])
        self.assertEqual(antigua.context_data["form"].data["celda_A_1_0"], "3")  # los datos siguen cargados
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("UPDATE resoluciones SET documento = '{roto'")
        danada = cliente.get(f"{url}?resolucion={identificador}")
        self.assertEqual(danada.status_code, 200)
        self.assertEqual(danada.context_data["resolucion"]["estado"], "danado")
        self.assertContains(cliente.get("/resoluciones/"), "el registro está dañado")
        for valor in ("999", "x"):
            self.assertEqual(cliente.get(f"{url}?resolucion={valor}").context_data["resolucion"]["estado"], "inexistente")

    def test_otra_herramienta_no_abre_la_resolucion(self):
        cliente = Client()
        url, datos = CASOS["biseccion"]
        identificador = cliente.post(url, datos).context_data["resolucion"]["id"]
        respuesta = cliente.get(f"{RUTA_REGLA_FALSA}?resolucion={identificador}")
        self.assertEqual(respuesta.context_data["resolucion"]["estado"], "otra_ruta")
        self.assertIsNone(respuesta.context_data["resultado"])


class CuadernoTests(CuadernoTemporal, SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.cliente = Client()
        self.ids = {ruta: self.cliente.post(url, datos).context_data["resolucion"]["id"]
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
        self.assertContains(respuesta, "Reuniste 2 resoluciones en «Tarea 3 · matriz A».")
        ejercicio = modulo_almacen.almacen().ejercicios()[0]["id"]
        # Desde el aviso de la herramienta: vuelve a la resolución, ya dentro del ejercicio.
        respuesta = self.cliente.post("/resoluciones/", {
            "accion": "agrupar", "ids": [self.ids["ecuaciones-matriciales"]], "ejercicio": str(ejercicio),
            "volver": "herramienta"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta["Location"].startswith(f"/matrices/ecuaciones/?resolucion={self.ids['ecuaciones-matriciales']}"))
        reabierta = self.cliente.get(respuesta["Location"].split("#")[0])
        self.assertEqual(reabierta.context_data["resolucion"]["ejercicio"]["nombre"], "Tarea 3 · matriz A")
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
            grupos = [h["pasos"] for h in contexto["ejercicios"]] + [d["resoluciones"] for d in contexto["sueltas"]]
            return {fila["id"] for grupo in grupos for fila in grupo}

        self.assertEqual(resultados(q="mcmlxiii"), {self.ids["conversion-romanos"]})  # por el resultado
        self.assertEqual(resultados(q="RAICES practica"), {self.ids["biseccion"]})  # por el ejercicio, sin tildes
        self.assertEqual(resultados(herramienta="metodos-abiertos"), {self.ids["newton-raphson"], self.ids["secante"]})
        self.assertEqual(len(resultados(desde="2000-01-01", hasta="2999-12-31")), len(CASOS))
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
