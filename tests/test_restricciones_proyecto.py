"""Límites arquitectónicos y seguridad vigentes, sin vetar bibliotecas."""

import ast
from pathlib import Path
import tomllib
import unittest

RAIZ = Path(__file__).resolve().parents[1]


class PruebasLimitesProyecto(unittest.TestCase):
    def test_backend_no_depende_del_frontend_ni_ejecuta_texto(self):
        for archivo in (RAIZ / "backend").rglob("*.py"):
            with self.subTest(archivo=archivo.name):
                for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
                    if isinstance(nodo, ast.Import):
                        self.assertFalse(any(a.name.startswith("frontend") for a in nodo.names))
                    elif isinstance(nodo, ast.ImportFrom):
                        self.assertFalse((nodo.module or "").startswith("frontend"))
                    elif isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                        self.assertNotIn(nodo.func.id, {"eval", "exec"})

    def test_dependencias_de_presentacion_siguen_declaradas(self):
        with (RAIZ / "pyproject.toml").open("rb") as archivo:
            proyecto = tomllib.load(archivo)["project"]
        for nombre in ("django", "colorama", "pywebview", "waitress"):
            self.assertTrue(any(d.lower().startswith(nombre) for d in proyecto["dependencies"]))
