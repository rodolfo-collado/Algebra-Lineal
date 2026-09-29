"""Contratos de la identidad visual."""

import os
import re
import unittest
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase
from django.urls import reverse

from scripts.sync_brand_mark import TARGET, header_mark


RAIZ = Path(__file__).resolve().parents[1]
STATIC = RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora"
STYLES = STATIC / "styles"


def css_combinado():
    partes = [(STATIC / "styles.css").read_text(encoding="utf-8")]
    for archivo in sorted(STYLES.glob("*.css")):
        partes.append(archivo.read_text(encoding="utf-8"))
    return "\n".join(partes)


class PruebasIdentidadVisual(SimpleTestCase):
    def test_tokens_y_hojas_locales(self):
        self.assertTrue((STATIC / "styles.css").is_file())
        for nombre in ("tokens.css", "base.css", "shell.css", "components.css", "modules.css"):
            with self.subTest(archivo=nombre):
                self.assertTrue((STYLES / nombre).is_file())
                self.assertGreater((STYLES / nombre).stat().st_size, 0)

        entrada = (STATIC / "styles.css").read_text(encoding="utf-8")
        for nombre in ("tokens.css", "base.css", "shell.css", "components.css", "modules.css"):
            self.assertIn(f"styles/{nombre}", entrada)

        tokens = (STYLES / "tokens.css").read_text(encoding="utf-8")
        for variable in (
            "--color-brand",
            "--color-accent",
            "--color-surface-raised",
            "--color-primary",
            "--font-ui",
            "--font-math",
        ):
            self.assertIn(variable, tokens)
        self.assertIn('[data-theme="dark"]', tokens)

    def test_header_pygebra_deriva_del_svg_oficial(self):
        # El parcial del header es el master con clase y aria; no tiene geometría propia.
        self.assertEqual(TARGET.read_text(encoding="utf-8"), header_mark())
        html = self.client.get("/").content.decode("utf-8")
        self.assertIn("<title>Inicio · PyGebra</title>", html)
        self.assertIn('aria-label="PyGebra, inicio"', html)
        self.assertIn('<span class="app-name">PyGebra</span>', html)
        for antiguo in ("app-mark-plate", "app-mark-cell", "app-tagline", "Álgebra Lineal, inicio"):
            self.assertNotIn(antiguo, html)

    def test_inicio_eleva_identidad_y_areas(self):
        respuesta = self.client.get(reverse("calculadora:inicio"))
        self.assertContains(respuesta, "Aprende resolviendo")
        self.assertContains(respuesta, "Explorar por temas")
        self.assertContains(respuesta, "home-hero")
        self.assertContains(respuesta, 'role="search"')
        self.assertContains(respuesta, "tool-link")
        self.assertContains(respuesta, 'data-categoria="sistemas-ecuaciones"')
        ids = DocumentoIds(respuesta).ids
        for fragmento in (
            "algebra-lineal", "sistemas-numericos",
            "sistemas-ecuaciones", "vectores", "matrices", "bases-numericas",
        ):
            self.assertIn(fragmento, ids)

    def test_interfaz_en_espanol_sin_spanglish(self):
        for ruta in ("/", "/sistemas/", "/bases/conversion/"):
            html = self.client.get(ruta).content.decode("utf-8")
            with self.subTest(ruta=ruta):
                for termino in ("Search tools", "Steps", "Related tools", "Coming soon", "Home"):
                    self.assertNotIn(f">{termino}<", html)
                self.assertIn("Buscar herramientas", html)
        self.assertIn("Ver procedimiento", self.client.post(
            "/sistemas/", {"sistema": "x1=1", "metodo": "gauss"},
        ).content.decode("utf-8"))

    def test_tokens_cubren_ambos_temas_para_los_componentes_nuevos(self):
        tokens = (STYLES / "tokens.css").read_text(encoding="utf-8")
        claro, oscuro = tokens.split('[data-theme="dark"]')
        for variable in ("--color-pivot", "--color-backdrop", "--color-brand-soft", "--color-focus"):
            with self.subTest(variable=variable):
                self.assertIn(variable, claro)
                self.assertIn(variable, oscuro)
        self.assertIn("--nav-width", claro)

    def test_sistemas_renderiza_sin_guias_ni_cdn(self):
        respuesta = self.client.post(
            "/sistemas/",
            {"sistema": "x1=1;x2=2", "metodo": "gauss"},
        )
        self.assertNotContains(respuesta, "Guía de concepto")
        self.assertNotContains(respuesta, "concept-guide")
        self.assertContains(respuesta, "pivot-chip")
        self.assertNotContains(respuesta, "fonts.googleapis.com")
        self.assertNotContains(respuesta, "cdn.jsdelivr.net")

    def test_recursos_css_parciales_existen_y_se_importan(self):
        entrada = (STATIC / "styles.css").read_text(encoding="utf-8")
        for nombre in ("tokens.css", "base.css", "shell.css", "components.css", "modules.css"):
            with self.subTest(archivo=nombre):
                self.assertIn(f"styles/{nombre}", entrada)
                self.assertTrue((STYLES / nombre).is_file())
                self.assertGreater((STYLES / nombre).stat().st_size, 0)


class DocumentoIds:
    def __init__(self, respuesta):
        self.ids = re.findall(r'\bid="([^"]+)"', respuesta.content.decode("utf-8"))


class PruebasSelectorTema(unittest.TestCase):
    def test_los_iconos_visibles_representan_el_tema_activo(self):
        contenido = css_combinado()
        selectores_ocultos = {
            " ".join(selector.split())
            for selectores, declaraciones in re.findall(
                r"([^{}]+)\{([^{}]*)\}", contenido
            )
            if re.search(r"\bdisplay\s*:\s*none\s*;", declaraciones)
            for selector in selectores.split(",")
        }

        self.assertIn('[data-theme="light"] .theme-icon-moon', selectores_ocultos)
        self.assertNotIn('[data-theme="light"] .theme-icon-sun', selectores_ocultos)
        self.assertIn('[data-theme="dark"] .theme-icon-sun', selectores_ocultos)
        self.assertNotIn('[data-theme="dark"] .theme-icon-moon', selectores_ocultos)


if __name__ == "__main__":
    unittest.main()
