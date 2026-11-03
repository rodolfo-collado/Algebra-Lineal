"""Biblioteca local intacta, licencia y recursos incluidos por PyInstaller."""

import hashlib
from pathlib import Path
import unittest


RAIZ = Path(__file__).resolve().parents[1]
STATIC = RAIZ / "frontend/web/calculadora/static/calculadora"
HASHES = {
    "plotly-basic-4.1.2.min.js": "fa18ed1c94c06576c0a867bb2477534716c39e5b22affe673f2a184317974926",
    "plotly-locale-es-4.1.2.js": "9e6bd4d160fc5759322535efaaf21bdaa7a3472b3b7d2992200f7b63fc976c4c",
    "LICENSE-plotly.txt": "8c45d9eaf50c2f72dd9c7ab9ef440788ba58a3538484b5c51c1f17d5128752e7",
}


class BiseccionAssetsTests(unittest.TestCase):
    def test_distribucion_oficial_intacta_y_con_licencia(self):
        for nombre, esperado in HASHES.items():
            with self.subTest(archivo=nombre):
                self.assertEqual(hashlib.sha256((STATIC / "vendor" / nombre).read_bytes()).hexdigest(), esperado)

    def test_paquete_windows_incluye_modulos_y_directorio_static_completo(self):
        spec = (RAIZ / "AlgebraLineal.spec").read_text(encoding="utf-8")
        for modulo in ["backend.biseccion", "backend.funciones_reales", "forms_biseccion", "views_biseccion", "servicios_biseccion"]:
            self.assertIn(modulo, spec)
        self.assertIn('"frontend/web/calculadora/static"', spec)
        self.assertTrue((STATIC / "biseccion.js").is_file())
