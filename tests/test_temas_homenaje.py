"""Contratos de los temas homenaje (ChocoLab, BelugaCalc y HeyAlgb): son estilos como
Minimalista, con tokens claro/oscuro, firma en Inicio y créditos de cada logotipo.

El aspecto real (contraste, 390 px, foco) se revisó en Edge; ver docs/temas-homenaje.md.
"""

import hashlib
import os
import re
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase

from frontend.web.calculadora import preferencias

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "frontend" / "web" / "calculadora"
STATIC = APP / "static" / "calculadora"
HOMENAJES = ("chocolab", "belugacalc", "heyalgb")


class TemasHomenajeTests(SimpleTestCase):
    def test_son_estilos_validos_en_servidor_y_en_el_primer_pintado(self):
        inicial = (APP / "templates" / "calculadora" / "components" / "tema_inicial.html").read_text(encoding="utf-8")
        lista = re.search(r"\[([^\]]*)\]\.indexOf\(estilo\)", inicial).group(1)
        # Las mismas claves que acepta preferencias.py, salvo Estudio, que es el valor por defecto.
        self.assertEqual(tuple(re.findall(r'"(\w+)"', lista)), preferencias.VALORES["pygebra-estilo"][1:])
        self.assertTrue(set(HOMENAJES) <= set(preferencias.VALORES["pygebra-estilo"]))

    def test_cada_tema_define_claro_y_oscuro_y_se_carga_al_final(self):
        css = (STATIC / "styles" / "homenajes.css").read_text(encoding="utf-8")
        for estilo in HOMENAJES:
            for tema in ("light", "dark"):
                bloque = re.search(rf'\[data-estilo="{estilo}"\]\[data-theme="{tema}"\] \{{(.*?)\}}', css, re.S)
                self.assertIsNotNone(bloque, f"{estilo} {tema}")
                for token in ("--color-bg", "--color-text", "--color-muted", "--color-brand",
                              "--color-brand-text", "--color-border-input", "--color-focus"):
                    self.assertIn(token + ":", bloque.group(1), f"{estilo} {tema} {token}")
        entrada = (STATIC / "styles.css").read_text(encoding="utf-8")
        self.assertLess(entrada.index("estudio.css"), entrada.index("homenajes.css"))

    def test_inicio_y_opciones_reconocen_a_cada_equipo(self):
        html = self.client.get("/").content.decode("utf-8")
        for estilo, nombre in zip(HOMENAJES, ("ChocoLab", "BelugaCalc", "HeyAlgb")):
            self.assertIn(f'<input type="radio" name="estilo" value="{estilo}">', html)
            self.assertIn(f'data-homenaje="{estilo}"><span class="homenaje-logo">', html)
            self.assertIn(f"En honor a <b>{nombre}</b>", html)
            self.assertIn(f"En honor a {nombre} ·", html)
            self.assertIn(f"calculadora/homenajes/{estilo}.png", html)
        # La identidad de PyGebra no cambia: mismo título y símbolo.
        self.assertIn('<h1 class="home-title">PyGebra</h1>', html)

    def test_cada_logotipo_tiene_credito_y_procedencia_verificable(self):
        creditos = (RAIZ / "docs" / "temas-homenaje.md").read_text(encoding="utf-8")
        archivos = sorted((STATIC / "homenajes").iterdir())
        self.assertEqual([a.name for a in archivos], sorted(f"{e}.png" for e in HOMENAJES))
        for archivo in archivos:
            fila = next(l for l in creditos.splitlines() if l.startswith(f"| `{archivo.name}`"))
            self.assertIn(hashlib.sha256(archivo.read_bytes()).hexdigest(), fila)
