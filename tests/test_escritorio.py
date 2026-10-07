"""P27.7: experiencia de escritorio sin convertir PyGebra en un navegador.

Preferencias entre aperturas (archivo propio), señal de escritorio y contratos
del historial (Alt+←/→, pageshow, sessionStorage).
"""

import json
import multiprocessing
import os
import re
import tempfile
import threading
import unittest
from uuid import uuid4
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import Client, SimpleTestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from frontend.web.calculadora import catalogo, preferencias


RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "frontend" / "web" / "calculadora"
STATIC = APP / "static" / "calculadora"
TEMPLATES = APP / "templates"
HERRAMIENTAS = [h.ruta for h in catalogo.HERRAMIENTAS if h.disponible]


def guardar_en_proceso(ruta, clave, valor, iniciado, leido=None, continuar=None):
    """Escritor independiente; permite pausar una lectura antes del reemplazo."""
    original = Path.read_text

    def leer_pausado(archivo, *args, **kwargs):
        datos = original(archivo, *args, **kwargs)
        if archivo == Path(ruta) and leido is not None:
            leido.set()
            if not continuar.wait(8):
                raise TimeoutError("No se liberó el escritor de prueba.")
        return datos

    with override_settings(DESKTOP_MODE=True, DESKTOP_PREFERENCES_FILE=ruta), \
            patch.object(Path, "read_text", leer_pausado):
        iniciado.set()
        preferencias.guardar(clave, valor)


class EnEscritorio(SimpleTestCase):
    """Modo escritorio con un archivo de preferencias aislado."""

    def setUp(self):
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        self.archivo = Path(directorio.name) / "PyGebra" / "preferencias.json"
        ajustes = override_settings(DESKTOP_MODE=True, DESKTOP_PREFERENCES_FILE=str(self.archivo))
        ajustes.enable()
        self.addCleanup(ajustes.disable)

    def guardado(self):
        return json.loads(self.archivo.read_text(encoding="utf-8"))


class PruebasArchivoDePreferencias(EnEscritorio):
    def test_sin_archivo_no_hay_preferencias_ni_se_crea_nada(self):
        self.assertEqual(preferencias.leer(), {})
        self.assertFalse(self.archivo.parent.exists())

    def test_guarda_solo_las_tres_claves_y_sus_valores_cerrados(self):
        for clave, valor in (("pygebra-tema", "dark"), ("pygebra-formato-numerico", "decimal"),
                             ("pygebra-precision-decimal", "8")):
            self.assertTrue(preferencias.guardar(clave, valor))
        for clave, valor in (
            ("pygebra-tema", "azul"), ("pygebra-precision-decimal", "3"),
            ("pygebra-precision-decimal", 8), ("algebra-lineal-menu-secciones", '["matrices"]'),
            ("ultima-url", "/matrices/inversa/"), ("matriz", "1,2;3,4"), (None, None),
        ):
            with self.subTest(clave=clave, valor=valor):
                self.assertFalse(preferencias.guardar(clave, valor))
        self.assertEqual(self.guardado(), {
            "pygebra-tema": "dark", "pygebra-formato-numerico": "decimal", "pygebra-precision-decimal": "8",
        })
        self.assertEqual(sorted(p.name for p in self.archivo.parent.iterdir()), ["preferencias.json", "preferencias.lock"])

    def test_lectura_descarta_claves_ajenas_valores_invalidos_y_archivos_danados(self):
        self.archivo.parent.mkdir(parents=True)
        self.archivo.write_text(json.dumps({
            "pygebra-tema": "light", "pygebra-precision-decimal": 8, "sistema": "x1+x2=3",
            "pygebra-formato-numerico": "\"><script>alert(1)</script>",
        }), encoding="utf-8")
        self.assertEqual(preferencias.leer(), {"pygebra-tema": "light"})
        for contenido in ("{no es json", "[]", '"dark"'):
            with self.subTest(contenido=contenido):
                self.archivo.write_text(contenido, encoding="utf-8")
                self.assertEqual(preferencias.leer(), {})
        # Un archivo dañado se reemplaza entero por las preferencias válidas.
        self.assertTrue(preferencias.guardar("pygebra-tema", "dark"))
        self.assertEqual(self.guardado(), {"pygebra-tema": "dark"})

    def test_escrituras_y_lecturas_simultaneas_no_se_pisan(self):
        # numeros.js envía formato y precisión a la vez; Waitress los atiende en hilos distintos.
        pares = [("pygebra-tema", "dark"), ("pygebra-formato-numerico", "decimal"), ("pygebra-precision-decimal", "6")]
        hilos = [threading.Thread(target=preferencias.guardar, args=par) for par in pares * 8]
        hilos += [threading.Thread(target=preferencias.leer) for _ in range(8)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()
        self.assertEqual(self.guardado(), dict(pares))

    def test_un_fallo_al_reemplazar_no_deja_temporales(self):
        self.assertTrue(preferencias.guardar("pygebra-tema", "dark"))
        with patch("frontend.web.calculadora.preferencias.os.replace", side_effect=PermissionError("en uso")):
            with self.assertRaises(PermissionError):
                preferencias.guardar("pygebra-tema", "light")
        self.assertEqual(sorted(p.name for p in self.archivo.parent.iterdir()), ["preferencias.json", "preferencias.lock"])
        self.assertEqual(self.guardado(), {"pygebra-tema": "dark"})

    def test_dos_procesos_no_pierden_preferencias(self):
        self.archivo.parent.mkdir(parents=True)
        self.archivo.write_text("{}", encoding="utf-8")
        contexto = multiprocessing.get_context("spawn")
        iniciado_a, iniciado_b, leido, continuar = [contexto.Event() for _ in range(4)]
        procesos = [
            contexto.Process(target=guardar_en_proceso, args=(str(self.archivo), "pygebra-tema", "dark", iniciado_a, leido, continuar)),
            contexto.Process(target=guardar_en_proceso, args=(str(self.archivo), "pygebra-precision-decimal", "8", iniciado_b)),
        ]
        try:
            procesos[0].start()
            self.assertTrue(leido.wait(8))
            procesos[1].start()
            self.assertTrue(iniciado_b.wait(8))
            # Sin lock entre procesos, B termina y luego A sobrescribe su clave.
            procesos[1].join(1)
            continuar.set()
            for proceso in procesos:
                proceso.join(8)
                self.assertEqual(proceso.exitcode, 0)
            self.assertEqual(self.guardado(), {"pygebra-tema": "dark", "pygebra-precision-decimal": "8"})
        finally:
            continuar.set()
            for proceso in procesos:
                if proceso.pid is not None and proceso.is_alive():
                    proceso.terminate()
                    proceso.join(3)

    def test_un_fallo_durante_la_escritura_conserva_el_json_y_limpia_temporales(self):
        preferencias.guardar("pygebra-tema", "dark")
        with patch.object(preferencias.json, "dump", side_effect=OSError("disco lleno")):
            with self.assertRaises(OSError):
                preferencias.guardar("pygebra-tema", "light")
        self.assertEqual(self.guardado(), {"pygebra-tema": "dark"})
        self.assertEqual(list(self.archivo.parent.glob("*.tmp")), [])

    def test_la_web_no_lee_ni_escribe_aunque_haya_ruta(self):
        with override_settings(DESKTOP_MODE=False):
            self.assertFalse(preferencias.guardar("pygebra-tema", "dark"))
            self.assertEqual(preferencias.leer(), {})
        self.assertFalse(self.archivo.exists())


class PruebasEndpointDePreferencias(EnEscritorio):
    def test_ruta_publica_del_endpoint(self):
        # tema_inicial.html la usa literal: debe coincidir con urls.py.
        self.assertEqual(reverse("calculadora:preferencias"), "/preferencias/")
        script = (TEMPLATES / "calculadora" / "components" / "tema_inicial.html").read_text(encoding="utf-8")
        self.assertIn('fetch("/preferencias/"', script)

    def test_post_valido_guarda_y_responde_sin_contenido(self):
        respuesta = self.client.post("/preferencias/", {"clave": "pygebra-tema", "valor": "dark"})
        self.assertEqual(respuesta.status_code, 204)
        self.assertEqual(self.guardado(), {"pygebra-tema": "dark"})

    def test_peticion_retrasada_no_sobrescribe_la_eleccion_mas_reciente(self):
        sesion = str(uuid4())
        for numero, valor in ((2, "light"), (1, "dark")):
            respuesta = self.client.post("/preferencias/", {"clave": "pygebra-tema", "valor": valor},
                                         HTTP_X_PYGEBRA_ESCRITURA=f"{sesion}:{numero}")
            self.assertEqual(respuesta.status_code, 204)
        self.assertEqual(self.guardado(), {"pygebra-tema": "light"})

    def test_rechaza_identificadores_de_escritura_invalidos(self):
        for escritura in ("incorrecto", f"{uuid4()}:0", f"{uuid4()}:1.5", f"{uuid4()}:9007199254740992"):
            with self.subTest(escritura=escritura):
                respuesta = self.client.post("/preferencias/", {"clave": "pygebra-tema", "valor": "dark"},
                                             HTTP_X_PYGEBRA_ESCRITURA=escritura)
                self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(self.archivo.exists())

    def test_rechaza_otras_claves_valores_y_metodos(self):
        for datos in ({"clave": "sistema", "valor": "x1=1"}, {"clave": "pygebra-tema", "valor": "rojo"}, {}):
            with self.subTest(datos=datos):
                self.assertEqual(self.client.post("/preferencias/", datos).status_code, 400)
        self.assertEqual(self.client.get("/preferencias/").status_code, 405)
        self.assertFalse(self.archivo.exists())

    def test_rechaza_post_grande_tambien_con_archivos_multipart(self):
        respuesta = self.client.post("/preferencias/", {
            "clave": "pygebra-tema", "valor": "dark",
            "archivo": SimpleUploadedFile("extra.bin", b"x" * 2048),
        })
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(self.archivo.exists())

    def test_exige_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        respuesta = cliente.post("/preferencias/", {"clave": "pygebra-tema", "valor": "dark"})
        self.assertEqual(respuesta.status_code, 403)
        pagina = cliente.get("/")
        token = re.search(r'<meta name="csrf-token" content="([^"]+)">', pagina.content.decode()).group(1)
        respuesta = cliente.post("/preferencias/", {"clave": "pygebra-tema", "valor": "dark"}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(respuesta.status_code, 204)

    def test_la_web_no_tiene_endpoint(self):
        with override_settings(DESKTOP_MODE=False):
            respuesta = self.client.post("/preferencias/", {"clave": "pygebra-tema", "valor": "dark"})
        self.assertEqual(respuesta.status_code, 404)
        self.assertFalse(self.archivo.exists())


class PruebasSenalDeEscritorio(EnEscritorio):
    def html(self, ruta="/"):
        return self.client.get(ruta).content.decode()

    def test_escritorio_publica_una_senal_y_solo_preferencias_validas(self):
        self.archivo.parent.mkdir(parents=True)
        self.archivo.write_text(json.dumps({
            "pygebra-tema": "dark", "pygebra-precision-decimal": "8", "pygebra-formato-numerico": "otro",
        }), encoding="utf-8")
        for ruta in ["/", *HERRAMIENTAS]:
            with self.subTest(ruta=ruta):
                html = self.html(ruta)
                raiz = re.search(r"<html[^>]*>", html).group(0)
                self.assertEqual(raiz, '<html lang="es" data-theme="light" data-desktop '
                                       'data-pygebra-tema="dark" data-pygebra-precision-decimal="8">')
                self.assertRegex(html, r'<meta name="csrf-token" content="[^"]+">')

    def test_la_web_no_cambia(self):
        self.archivo.parent.mkdir(parents=True)
        self.archivo.write_text(json.dumps({"pygebra-tema": "dark"}), encoding="utf-8")
        with override_settings(DESKTOP_MODE=False):
            for ruta in ["/", *HERRAMIENTAS]:
                with self.subTest(ruta=ruta):
                    html = self.html(ruta)
                    self.assertEqual(re.search(r"<html[^>]*>", html).group(0), '<html lang="es" data-theme="light">')
                    self.assertNotIn('<meta name="csrf-token"', html)

    def test_sin_controles_de_navegador_visibles(self):
        header = (TEMPLATES / "calculadora" / "components" / "header.html").read_text(encoding="utf-8")
        botones = re.findall(r'<button[^>]*id="([^"]+)"', header)
        self.assertEqual(botones, ["navigation-toggle", "theme-toggle"])
        html = self.html("/matrices/reduccion/")
        for ausente in ("history.back", "Atrás", "Adelante", 'type="url"'):
            with self.subTest(ausente=ausente):
                self.assertNotIn(ausente, html)


class PruebasHistorialYRestauracion(SimpleTestCase):
    def test_alt_flechas_solo_en_escritorio_y_sin_pila_propia(self):
        script = (STATIC / "navigation.js").read_text(encoding="utf-8")
        bloque = script[script.index('if (root.hasAttribute("data-desktop"))'):script.index("if (!button || !sidebar) return;")]
        for contrato in ("event.altKey", "event.ctrlKey", "event.metaKey", "event.shiftKey",
                         "event.isComposing", "event.defaultPrevented", '"ArrowLeft") history.back()',
                         '"ArrowRight") history.forward()', "event.preventDefault()"):
            with self.subTest(contrato=contrato):
                self.assertIn(contrato, bloque)
        for ausente in ("pushState", "replaceState", "sessionStorage.setItem(\"historial"):
            self.assertNotIn(ausente, script)

    def test_las_cuadriculas_dejan_alt_flechas_al_historial(self):
        compartido = (STATIC / "entradas.js").read_text(encoding="utf-8")
        self.assertIn("event.altKey", compartido)
        for nombre in ("matriz.js", "vectores.js", "ecuaciones.js", "expresiones.js", "inversa.js"):
            with self.subTest(script=nombre):
                self.assertIn("window.entradasSeguras.flechaDeCelda(event)", (STATIC / nombre).read_text(encoding="utf-8"))

    def test_pageshow_restaurado_cierra_menu_y_resincroniza_preferencias(self):
        navegacion = (STATIC / "navigation.js").read_text(encoding="utf-8")
        restaurar = navegacion[navegacion.index('window.addEventListener("pageshow"'):]
        for contrato in ("event.persisted", "abierto = false", "aplicar()", "sidebar.contains(document.activeElement)", "button.focus()"):
            with self.subTest(contrato=contrato):
                self.assertIn(contrato, restaurar)
        self.assertIn("if (event.persisted) applyTheme(storedTheme() || systemTheme())", (STATIC / "tema.js").read_text(encoding="utf-8"))
        numeros = (STATIC / "numeros.js").read_text(encoding="utf-8")
        self.assertIn("if (event.persisted) sincronizar()", numeros)
        # Solo representación: ni input/change sintéticos ni envíos.
        for ausente in ("dispatchEvent", "submit", "localStorage."):
            self.assertNotIn(ausente, numeros)

    def test_feedback_conserva_su_restauracion_de_espera(self):
        self.assertIn('window.addEventListener("pageshow", () => {', (STATIC / "feedback.js").read_text(encoding="utf-8"))

    def test_categorias_del_menu_solo_durante_la_ejecucion(self):
        script = (STATIC / "navigation.js").read_text(encoding="utf-8")
        self.assertIn("sessionStorage.getItem(clave)", script)
        self.assertIn("sessionStorage.setItem(clave, valor)", script)
        self.assertIn("localStorage.removeItem(STORAGE_SECCIONES)", script)
        self.assertNotIn("localStorage.setItem", script)
        self.assertNotIn("localStorage.getItem", script)

    def test_solo_tres_preferencias_llegan_a_localstorage(self):
        claves = set()
        for archivo in [*STATIC.glob("*.js"), TEMPLATES / "calculadora" / "components" / "tema_inicial.html"]:
            claves |= set(re.findall(r'localStorage\.setItem\("([^"]+)"', archivo.read_text(encoding="utf-8")))
        self.assertEqual(claves, {"pygebra-tema"})
        inicial = (TEMPLATES / "calculadora" / "components" / "tema_inicial.html").read_text(encoding="utf-8")
        self.assertIn("localStorage.setItem(clave, valor)", inicial)
        self.assertEqual(set(preferencias.VALORES), {"pygebra-tema", "pygebra-formato-numerico", "pygebra-precision-decimal"})

    def test_volver_no_restaura_formularios_que_no_corresponden_al_resultado(self):
        cliente = Client()
        for ruta in HERRAMIENTAS:
            with self.subTest(ruta=ruta):
                html = cliente.get(ruta).content.decode()
                formulario = re.search(r"<form[^>]*data-entrada-calculo[^>]*>", html).group(0)
                self.assertIn('autocomplete="off"', formulario)
        formato = (TEMPLATES / "calculadora" / "components" / "numeric_format.html").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r'<select[^>]*autocomplete="off"', formato)), 2)

    def test_la_web_conserva_el_menu_contextual_del_navegador(self):
        for archivo in STATIC.glob("*.js"):
            with self.subTest(script=archivo.name):
                self.assertNotIn("contextmenu", archivo.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
