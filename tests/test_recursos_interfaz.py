"""Comprueba que la interfaz desktop no dependa de recursos de red."""

import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

HOSTS_PROHIBIDOS = (
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    "ajax.googleapis.com",
    "code.jquery.com",
    "maxcdn.bootstrapcdn.com",
)

RUTAS_INTERFAZ = (
    RAIZ / "frontend" / "web" / "calculadora" / "templates",
    RAIZ / "frontend" / "web" / "calculadora" / "static",
)

EXTENSIONES = {".html", ".css", ".js", ".svg"}

ASSETS_LOCALES = (
    RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora" / "styles.css",
    RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora" / "matriz.js",
    RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora" / "tema.js",
    RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora" / "mark.svg",
    RAIZ / "assets" / "algebra-lineal.ico",
    RAIZ / "assets" / "algebra-lineal.svg",
)


NAMESPACE_PERMITIDOS = (
    "http://www.w3.org/2000/svg",
    "http://www.w3.org/1999/xlink",
)


def archivos_de_interfaz():
    for raiz in RUTAS_INTERFAZ:
        for archivo in sorted(raiz.rglob("*")):
            if "__pycache__" in archivo.parts:
                continue
            if archivo.is_file() and archivo.suffix.lower() in EXTENSIONES:
                yield archivo


def texto_sin_namespaces(texto):
    limpio = texto
    for namespace in NAMESPACE_PERMITIDOS:
        limpio = limpio.replace(namespace, "")
    return limpio


class PruebasRecursosLocales(unittest.TestCase):
    def test_existen_los_assets_locales(self):
        for ruta in ASSETS_LOCALES:
            with self.subTest(archivo=ruta.relative_to(RAIZ).as_posix()):
                self.assertTrue(ruta.is_file(), f"Falta {ruta.name}")
                self.assertGreater(ruta.stat().st_size, 0)

    def test_el_icono_es_un_ico_versionado(self):
        contenido = (RAIZ / "assets" / "algebra-lineal.ico").read_bytes()

        self.assertEqual(contenido[:4], b"\x00\x00\x01\x00")

    def test_la_interfaz_no_referencia_cdns_ni_fuentes_remotas(self):
        for archivo in archivos_de_interfaz():
            texto = archivo.read_text(encoding="utf-8").lower()
            ruta = archivo.relative_to(RAIZ).as_posix()
            with self.subTest(archivo=ruta):
                encontradas = [host for host in HOSTS_PROHIBIDOS if host in texto]
                self.assertEqual(
                    encontradas,
                    [],
                    f"{ruta} referencia recursos remotos: {', '.join(encontradas)}.",
                )
                self.assertNotIn(
                    "://",
                    texto_sin_namespaces(texto),
                    f"{ruta} contiene una URL absoluta; la interfaz debe ser offline.",
                )


if __name__ == "__main__":
    unittest.main()
