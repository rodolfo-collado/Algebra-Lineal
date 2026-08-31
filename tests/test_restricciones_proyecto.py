"""Verifica de forma automatica las restricciones academicas del proyecto.

Los algoritmos de algebra lineal deben escribirse a mano, asi que ni el codigo
ni las dependencias declaradas pueden apoyarse en NumPy, SciPy o SymPy.
"""

import ast
import tomllib
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

LIBRERIAS_PROHIBIDAS = frozenset({"numpy", "scipy", "sympy"})

# Codigo ejecutable del repositorio, sin contar el entorno virtual.
RUTAS_REVISADAS = ("backend", "frontend", "tests", "main.py")


def archivos_python():
    for nombre in RUTAS_REVISADAS:
        ruta = RAIZ / nombre
        if ruta.is_dir():
            yield from sorted(ruta.rglob("*.py"))
        else:
            yield ruta


def modulos_importados(codigo):
    """Devuelve el modulo raiz de cada import del codigo, segun su arbol sintactico."""
    raices = set()
    for nodo in ast.walk(ast.parse(codigo)):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                raices.add(alias.name.split(".")[0].lower())
        elif isinstance(nodo, ast.ImportFrom):
            # Un import relativo (level > 0) nunca apunta a una libreria externa.
            if nodo.level == 0 and nodo.module:
                raices.add(nodo.module.split(".")[0].lower())

    return raices


def nombre_de_requisito(requisito):
    """Extrae el nombre normalizado de un requisito como `colorama==0.4.6`."""
    letras = []
    for caracter in requisito.strip():
        if caracter.isalnum() or caracter in "-_.":
            letras.append(caracter)
        else:
            break

    nombre = "".join(letras).lower()
    for separador in "_.":
        nombre = nombre.replace(separador, "-")

    return nombre


def dependencias_declaradas():
    """Agrupa por origen los requisitos declarados en pyproject.toml."""
    with open(RAIZ / "pyproject.toml", "rb") as archivo:
        configuracion = tomllib.load(archivo)

    proyecto = configuracion.get("project", {})
    origenes = {"project.dependencies": proyecto.get("dependencies", [])}

    for extra, requisitos in proyecto.get("optional-dependencies", {}).items():
        origenes[f"project.optional-dependencies.{extra}"] = requisitos

    for grupo, requisitos in configuracion.get("dependency-groups", {}).items():
        # Un grupo puede incluir otros grupos mediante tablas; solo interesan las cadenas.
        origenes[f"dependency-groups.{grupo}"] = [
            requisito for requisito in requisitos if isinstance(requisito, str)
        ]

    return origenes


class PruebasImportsProhibidos(unittest.TestCase):
    def test_el_codigo_no_importa_librerias_matematicas(self):
        for archivo in archivos_python():
            ruta = archivo.relative_to(RAIZ).as_posix()
            with self.subTest(archivo=ruta):
                encontradas = sorted(
                    modulos_importados(archivo.read_text(encoding="utf-8"))
                    & LIBRERIAS_PROHIBIDAS
                )

                self.assertEqual(
                    encontradas,
                    [],
                    f"{ruta} importa librerias prohibidas: {', '.join(encontradas)}. "
                    "Los algoritmos deben implementarse manualmente."
                )

    def test_se_revisa_todo_el_codigo_del_repositorio(self):
        revisados = {archivo.relative_to(RAIZ).as_posix() for archivo in archivos_python()}

        self.assertIn("main.py", revisados)
        self.assertIn("backend/expresiones.py", revisados)
        self.assertIn("backend/gauss.py", revisados)
        self.assertIn("backend/gauss_jordan.py", revisados)
        self.assertIn("backend/parser_sistemas.py", revisados)
        self.assertIn("frontend/terminal/opciones.py", revisados)
        self.assertIn("tests/test_restricciones_proyecto.py", revisados)


class PruebasDeteccionDeImports(unittest.TestCase):
    """El detector debe reconocer las formas habituales de importar una libreria."""

    def test_detecta_import_directo(self):
        self.assertIn("numpy", modulos_importados("import numpy"))

    def test_detecta_import_con_alias(self):
        self.assertIn("numpy", modulos_importados("import numpy as np"))

    def test_detecta_from_import(self):
        self.assertIn("scipy", modulos_importados("from scipy import linalg"))

    def test_detecta_import_de_submodulo(self):
        self.assertIn("sympy", modulos_importados("from sympy.matrices import Matrix"))
        self.assertIn("scipy", modulos_importados("import scipy.linalg as sla"))

    def test_detecta_import_dentro_de_una_funcion(self):
        codigo = "def resolver():\n    import numpy\n"

        self.assertIn("numpy", modulos_importados(codigo))

    def test_ignora_los_imports_relativos(self):
        self.assertEqual(modulos_importados("from . import matrices"), set())

    def test_un_texto_no_cuenta_como_import(self):
        self.assertEqual(modulos_importados("mensaje = 'import numpy'"), set())


class PruebasDependenciasDeclaradas(unittest.TestCase):
    def test_pyproject_no_declara_librerias_matematicas(self):
        for origen, requisitos in dependencias_declaradas().items():
            with self.subTest(origen=origen):
                encontradas = sorted(
                    {nombre_de_requisito(requisito) for requisito in requisitos}
                    & LIBRERIAS_PROHIBIDAS
                )

                self.assertEqual(
                    encontradas,
                    [],
                    f"{origen} declara dependencias prohibidas: {', '.join(encontradas)}."
                )

    def test_colorama_sigue_declarado_como_dependencia(self):
        nombres = {
            nombre_de_requisito(requisito)
            for requisito in dependencias_declaradas()["project.dependencies"]
        }

        self.assertIn("colorama", nombres)

    def test_la_prohibicion_solo_cubre_librerias_matematicas(self):
        """Las dependencias de interfaz o infraestructura siguen siendo validas."""
        self.assertNotIn("colorama", LIBRERIAS_PROHIBIDAS)
        self.assertNotIn("django", LIBRERIAS_PROHIBIDAS)

    def test_reconoce_el_nombre_de_un_requisito_con_version_o_extras(self):
        self.assertEqual(nombre_de_requisito("colorama==0.4.6"), "colorama")
        self.assertEqual(nombre_de_requisito("numpy>=2.0"), "numpy")
        self.assertEqual(nombre_de_requisito("scipy[all]"), "scipy")
        self.assertEqual(nombre_de_requisito('sympy ; python_version >= "3.13"'), "sympy")


if __name__ == "__main__":
    unittest.main()
