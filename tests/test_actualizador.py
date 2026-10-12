"""Actualizador de escritorio: versiones, releases, descarga, SHA-256 e instalador.

Ninguna prueba usa la red: un ``abrir`` falso sirve la API de GitHub y los
artefactos desde memoria, y ``popen`` registra el instalador que se lanzaría.
"""

import hashlib
import io
import json
import os
import tempfile
import tomllib
import unittest
from http.client import IncompleteRead
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase, override_settings

import desktop
from actualizador import descarga, instalador, releases, servicio, verificacion, versiones


RAIZ = Path(__file__).resolve().parents[1]
INSTALADOR = b"MZ instalador oficial de prueba" * 1000
API = releases.API_ULTIMA_RELEASE
U = "https://github.com/x.exe"
BASE = f"https://github.com/{releases.REPOSITORIO}/releases/download"


def sumas(version, contenido=INSTALADOR):
    return f"{hashlib.sha256(contenido).hexdigest()}  PyGebra-Setup-{version}.exe\n".encode()


def release_api(version, *, prerelease=False, draft=False, assets=None):
    if assets is None:
        assets = {f"PyGebra-Setup-{version}.exe": len(INSTALADOR), "SHA256SUMS.txt": len(sumas(version))}
    return json.dumps({
        "tag_name": f"v{version}", "prerelease": prerelease, "draft": draft,
        "assets": [
            # La URL publicada se ignora: el actualizador construye la oficial.
            {"name": nombre, "size": tamano, "browser_download_url": "https://ejemplo.invalid/x"}
            for nombre, tamano in assets.items()
        ],
    }).encode()


class Cortada(io.BytesIO):
    """Respuesta que entrega un bloque y luego pierde la conexión."""

    def read(self, *args):
        if self.tell():
            raise IncompleteRead(b"")
        return super().read(10)


class Red:
    """``urlopen`` falso: URL → bytes, excepción o respuesta ya construida."""

    def __init__(self, rutas):
        self.rutas = rutas
        self.pedidas = []

    def __call__(self, peticion, timeout):
        url = peticion.full_url
        self.pedidas.append(url)
        valor = self.rutas.get(url, HTTPError(url, 404, "Not Found", {}, None))
        if isinstance(valor, BaseException):
            raise valor
        return valor if isinstance(valor, io.IOBase) else io.BytesIO(valor)


def red_con_release(version, *, instalador=INSTALADOR, checksums=None):
    return Red({
        API: release_api(version),
        f"{BASE}/v{version}/SHA256SUMS.txt": checksums if checksums is not None else sumas(version),
        f"{BASE}/v{version}/PyGebra-Setup-{version}.exe": instalador,
    })


class PruebasVersiones(unittest.TestCase):
    def test_version_instalada_es_la_del_proyecto(self):
        esperada = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        self.assertEqual(versiones.version_instalada(), esperada)

    def test_comparacion_numerica(self):
        self.assertFalse(versiones.es_mas_nueva("0.9.0", "0.9.0"))
        self.assertTrue(versiones.es_mas_nueva("0.9.1", "0.9.0"))
        self.assertTrue(versiones.es_mas_nueva("0.10.0", "0.9.0"))
        self.assertFalse(versiones.es_mas_nueva("0.8.0", "0.9.0"))

    def test_solo_versiones_estables(self):
        for texto in ("1.0.0-rc1", "1.0", "v1.0.0", "01.0.0", "1.0.0.0", "", None):
            with self.subTest(texto=texto):
                self.assertIsNone(versiones.parsear(texto))


class PruebasReleases(unittest.TestCase):
    def test_release_estable_con_urls_oficiales(self):
        release = releases.consultar_ultima(red_con_release("1.2.3"))
        self.assertEqual(release.version, "1.2.3")
        self.assertEqual(release.instalador.url, f"{BASE}/v1.2.3/PyGebra-Setup-1.2.3.exe")
        self.assertEqual(release.instalador.tamano, len(INSTALADOR))
        self.assertEqual(release.checksums.url, f"{BASE}/v1.2.3/SHA256SUMS.txt")

    def test_prereleases_drafts_y_tags_no_estables_se_ignoran(self):
        for datos in (release_api("2.0.0", prerelease=True), release_api("2.0.0", draft=True),
                      release_api("2.0.0-rc1"), json.dumps({"tag_name": "nightly"}).encode()):
            with self.subTest(datos=datos[:60]):
                self.assertIsNone(releases.consultar_ultima(Red({API: datos})))

    def test_sin_releases_publicadas(self):
        self.assertIsNone(releases.consultar_ultima(Red({})))

    def test_fallo_de_red(self):
        for error in (URLError("sin red"), TimeoutError(), HTTPError(API, 503, "x", {}, None)):
            with self.subTest(error=error), self.assertRaises(releases.ErrorConexion):
                releases.consultar_ultima(Red({API: error}))

    def test_respuesta_no_json(self):
        with self.assertRaises(releases.ReleaseInvalida):
            releases.consultar_ultima(Red({API: b"<html>"}))

    def test_artefacto_inexistente(self):
        release = releases.interpretar(json.loads(release_api("1.0.0", assets={"SHA256SUMS.txt": 90})))
        with self.assertRaises(releases.ReleaseInvalida):
            release.instalador


class ConCarpeta(unittest.TestCase):
    def setUp(self):
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        self.carpeta = Path(directorio.name)


class PruebasDescarga(ConCarpeta):
    def test_descarga_completa(self):
        destino = self.carpeta / "setup.exe"
        progreso = []
        descarga.descargar(U, destino, len(INSTALADOR), Red({U: INSTALADOR}), lambda r, t: progreso.append(r))
        self.assertEqual(destino.read_bytes(), INSTALADOR)
        self.assertEqual(progreso[-1], len(INSTALADOR))

    def test_descarga_interrumpida_no_deja_archivos(self):
        for respuesta in (Cortada(INSTALADOR), INSTALADOR[:-1], URLError("caída")):
            with self.subTest(respuesta=type(respuesta)), self.assertRaises(descarga.DescargaFallida):
                descarga.descargar(U, self.carpeta / "setup.exe", len(INSTALADOR), Red({U: respuesta}))
            self.assertEqual(list(self.carpeta.iterdir()), [])

    def test_descarga_mayor_que_lo_publicado(self):
        with self.assertRaises(descarga.DescargaFallida):
            descarga.descargar(U, self.carpeta / "setup.exe", 10, Red({U: INSTALADOR}))
        self.assertEqual(list(self.carpeta.iterdir()), [])


class PruebasVerificacion(ConCarpeta):
    def setUp(self):
        super().setUp()
        self.archivo = self.carpeta / "PyGebra-Setup-1.0.0.exe"
        self.archivo.write_bytes(INSTALADOR)
        self.esperado = hashlib.sha256(INSTALADOR).hexdigest()

    def test_checksum_correcto(self):
        texto = sumas("1.0.0").decode().upper().replace("PYGEBRA-SETUP-1.0.0.EXE", "*PyGebra-Setup-1.0.0.exe")
        esperado = verificacion.checksum_publicado(texto, self.archivo.name)
        self.assertEqual(esperado, self.esperado)
        verificacion.verificar(self.archivo, esperado)

    def test_checksum_incorrecto(self):
        with self.assertRaises(verificacion.ChecksumInvalido):
            verificacion.verificar(self.archivo, hashlib.sha256(b"otro").hexdigest())

    def test_sin_entrada_o_ambigua(self):
        otro = hashlib.sha256(b"otro").hexdigest()
        for texto in ("", f"{otro}  PyGebra-Setup-0.9.0.exe\n",
                      f"{self.esperado}  {self.archivo.name}\n{otro}  {self.archivo.name}\n",
                      f"no-es-sha  {self.archivo.name}\n"):
            with self.subTest(texto=texto), self.assertRaises(verificacion.ChecksumInvalido):
                verificacion.checksum_publicado(texto, self.archivo.name)


class PruebasInstalador(ConCarpeta):
    def test_no_ejecuta_si_el_checksum_no_coincide(self):
        archivo = self.carpeta / "setup.exe"
        archivo.write_bytes(INSTALADOR)
        popen = Mock()
        with self.assertRaises(verificacion.ChecksumInvalido):
            instalador.lanzar(archivo, hashlib.sha256(b"otro").hexdigest(), popen)
        popen.assert_not_called()

    def test_ejecuta_el_instalador_verificado_en_modo_actualizacion(self):
        archivo = self.carpeta / "setup.exe"
        archivo.write_bytes(INSTALADOR)
        popen = Mock()
        instalador.lanzar(archivo, hashlib.sha256(INSTALADOR).hexdigest(), popen)
        argumentos = popen.call_args.args[0]
        self.assertEqual(argumentos, [str(archivo), "/SILENT", "/NORESTART", "/ACTUALIZAR=1"])


class PruebasFlujo(ConCarpeta):
    """Flujo completo del servicio con la descarga en el mismo hilo."""

    def actualizador(self, red, version_local="1.0.0"):
        pyproject = self.carpeta / "pyproject.toml"
        pyproject.write_text(f'[project]\nversion = "{version_local}"\n', encoding="utf-8")
        self.popen = Mock()
        self.descargas = self.carpeta / "descargas"
        actualizador = servicio.Actualizador(
            abrir=red, popen=self.popen, carpeta=self.descargas, pyproject=pyproject,
            en_segundo_plano=lambda funcion: funcion(),
        )
        actualizador.cerrar_aplicacion = Mock()
        return actualizador

    def test_misma_version_no_descarga_nada(self):
        red = red_con_release("1.0.0")
        actualizador = self.actualizador(red)
        self.assertEqual(actualizador.estado()["estado"], servicio.INICIAL)
        self.assertEqual(red.pedidas, [])  # Nada se consulta sin pedirlo.
        estado = actualizador.buscar()
        self.assertEqual(estado["estado"], servicio.ACTUALIZADO)
        self.assertEqual(estado["mensaje"], "PyGebra está actualizado.")
        self.assertEqual(red.pedidas, [API])
        self.assertEqual(actualizador.descargar()["estado"], servicio.ACTUALIZADO)
        self.assertFalse(self.descargas.exists())

    def test_version_remota_menor_o_prerelease(self):
        for red in (red_con_release("0.9.0"), Red({API: release_api("2.0.0", prerelease=True)})):
            with self.subTest(red=red.rutas[API][:40]):
                self.assertEqual(self.actualizador(red).buscar()["estado"], servicio.ACTUALIZADO)

    def test_version_remota_mayor_descarga_verifica_e_instala(self):
        actualizador = self.actualizador(red_con_release("1.1.0"))
        estado = actualizador.buscar()
        self.assertEqual(estado["estado"], servicio.DISPONIBLE)
        self.assertEqual(estado["version_disponible"], "1.1.0")
        self.assertEqual(estado["version_instalada"], "1.0.0")
        self.assertIn("1.1.0", estado["mensaje"])
        self.popen.assert_not_called()
        self.assertEqual(actualizador.descargar()["estado"], servicio.LISTO)
        self.popen.assert_not_called()
        estado = actualizador.instalar()
        self.assertEqual(estado["estado"], servicio.INSTALANDO)
        ruta = self.descargas / "PyGebra-Setup-1.1.0.exe"
        self.assertEqual(self.popen.call_args.args[0][0], str(ruta))
        self.assertEqual(ruta.read_bytes(), INSTALADOR)
        actualizador.cerrar_aplicacion.assert_called_once()

    def test_fallo_de_red_al_buscar(self):
        actualizador = self.actualizador(Red({API: URLError("sin red")}))
        self.assertEqual(actualizador.buscar()["estado"], servicio.ERROR_CONEXION)
        # Se puede reintentar.
        actualizador._abrir = red_con_release("1.0.0")
        self.assertEqual(actualizador.buscar()["estado"], servicio.ACTUALIZADO)

    def test_artefacto_inexistente(self):
        red = Red({API: release_api("1.1.0", assets={"SHA256SUMS.txt": 90})})
        actualizador = self.actualizador(red)
        self.assertEqual(actualizador.buscar()["estado"], servicio.ERROR)
        self.assertEqual(actualizador.descargar()["estado"], servicio.ERROR)
        self.assertEqual(red.pedidas, [API])

    def test_descarga_interrumpida(self):
        actualizador = self.actualizador(red_con_release("1.1.0", instalador=Cortada(INSTALADOR)))
        actualizador.buscar()
        self.assertEqual(actualizador.descargar()["estado"], servicio.ERROR_CONEXION)
        self.assertFalse(self.descargas.exists())
        self.assertEqual(actualizador.instalar()["estado"], servicio.ERROR_CONEXION)
        self.popen.assert_not_called()

    def test_checksum_incorrecto_descarta_y_no_ejecuta(self):
        red = red_con_release("1.1.0", checksums=sumas("1.1.0", b"otro contenido"))
        actualizador = self.actualizador(red)
        actualizador.buscar()
        estado = actualizador.descargar()
        self.assertEqual(estado["estado"], servicio.CHECKSUM_INVALIDO)
        self.assertIn("No se instaló nada", estado["mensaje"])
        self.assertFalse(self.descargas.exists())
        actualizador.instalar()
        self.popen.assert_not_called()
        actualizador.cerrar_aplicacion.assert_not_called()

    def test_checksums_sin_la_entrada_no_descarga_el_instalador(self):
        red = red_con_release("1.1.0", checksums=sumas("1.0.9"))
        actualizador = self.actualizador(red)
        actualizador.buscar()
        self.assertEqual(actualizador.descargar()["estado"], servicio.CHECKSUM_INVALIDO)
        self.assertNotIn(f"{BASE}/v1.1.0/PyGebra-Setup-1.1.0.exe", red.pedidas)
        self.popen.assert_not_called()

    def test_instalador_alterado_tras_verificar_no_se_ejecuta(self):
        actualizador = self.actualizador(red_con_release("1.1.0"))
        actualizador.buscar()
        actualizador.descargar()
        (self.descargas / "PyGebra-Setup-1.1.0.exe").write_bytes(b"alterado")
        self.assertEqual(actualizador.instalar()["estado"], servicio.CHECKSUM_INVALIDO)
        self.popen.assert_not_called()
        self.assertFalse(self.descargas.exists())

    def test_error_al_lanzar_no_rompe_la_app(self):
        actualizador = self.actualizador(red_con_release("1.1.0"))
        actualizador.buscar()
        actualizador.descargar()
        self.popen.side_effect = OSError("bloqueado")
        self.assertEqual(actualizador.instalar()["estado"], servicio.ERROR)
        actualizador.cerrar_aplicacion.assert_not_called()

    def test_progreso_durante_la_descarga(self):
        actualizador = self.actualizador(red_con_release("1.1.0"))
        actualizador.buscar()
        vistos = []
        original = actualizador._avanzar
        actualizador._avanzar = lambda r, t: (original(r, t), vistos.append(actualizador.estado()))
        actualizador.descargar()
        self.assertEqual({e["estado"] for e in vistos}, {servicio.DESCARGANDO})
        self.assertEqual(vistos[-1]["progreso"], 100)
        self.assertEqual(vistos[-1]["mensaje"], "Descargando PyGebra 1.1.0…")


@override_settings(DESKTOP_MODE=True)
class PruebasPaginaEscritorio(SimpleTestCase):
    def test_pagina_sin_consultar_internet(self):
        with patch.object(servicio.ACTUALIZADOR, "_abrir", Mock(side_effect=AssertionError("red"))):
            respuesta = self.client.get("/actualizaciones/")
        self.assertContains(respuesta, "Buscar actualizaciones")
        self.assertContains(respuesta, "Versión instalada: <strong>PyGebra")
        self.assertContains(respuesta, 'data-estado="inicial"')
        self.assertContains(respuesta, "calculadora/actualizaciones.js")
        self.assertContains(respuesta, 'href="/actualizaciones/" aria-current="page"')

    def test_acciones_devuelven_el_estado(self):
        for accion in ("buscar", "descargar", "instalar"):
            with self.subTest(accion=accion), \
                    patch.dict("frontend.web.calculadora.views.ACCIONES_ACTUALIZACION",
                               {accion: Mock(return_value={"estado": "x"})}):
                respuesta = self.client.post(f"/actualizaciones/{accion}/")
                self.assertEqual(respuesta.json(), {"estado": "x"})
        self.assertEqual(self.client.post("/actualizaciones/borrar/").status_code, 404)
        self.assertEqual(self.client.get("/actualizaciones/buscar/").status_code, 405)
        self.assertEqual(self.client.get("/actualizaciones/estado/").json()["estado"],
                         servicio.ACTUALIZADOR.estado()["estado"])

    def test_el_menu_enlaza_actualizaciones(self):
        html = self.client.get("/").content.decode()
        # Función de la app: al pie del cajón, fuera del árbol de áreas matemáticas.
        areas = html.index('id="arbol-herramientas"')
        pie = html.index('<nav class="sidebar-footer" aria-label="Aplicación">')
        self.assertLess(html.index("</nav>", areas), pie)
        self.assertLess(pie, html.index('href="/actualizaciones/"'))


class PruebasPaginaWeb(SimpleTestCase):
    @override_settings(DESKTOP_MODE=False)
    def test_la_web_no_ofrece_actualizaciones(self):
        for ruta in ("/actualizaciones/", "/actualizaciones/estado/"):
            self.assertEqual(self.client.get(ruta).status_code, 404)
        self.assertEqual(self.client.post("/actualizaciones/buscar/").status_code, 404)
        self.assertNotContains(self.client.get("/"), 'href="/actualizaciones/"')


class PruebasEscritorio(unittest.TestCase):
    def test_mutex_solo_en_windows(self):
        # test_instalador comprueba que el .iss usa el mismo nombre.
        with patch.object(desktop.sys, "platform", "linux"):
            self.assertIsNone(desktop.create_running_mutex())

    def test_tras_lanzar_el_instalador_se_cierra_la_ventana(self):
        ventana = Mock()
        anterior = servicio.ACTUALIZADOR.cerrar_aplicacion
        self.addCleanup(setattr, servicio.ACTUALIZADOR, "cerrar_aplicacion", anterior)
        with patch.object(desktop.threading, "Timer") as timer:
            desktop.install_update_close(ventana)
            servicio.ACTUALIZADOR.cerrar_aplicacion()
        timer.assert_called_once_with(desktop.UPDATE_CLOSE_DELAY_SECONDS, ventana.destroy)
        timer.return_value.start.assert_called_once()


if __name__ == "__main__":
    unittest.main()
