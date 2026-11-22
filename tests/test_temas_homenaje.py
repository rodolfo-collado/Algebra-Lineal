"""Contratos de los temas homenaje (ChocoLab, BelugaCalc y HeyAlgb): estilos con tokens
claro/oscuro, composición y movimiento propios, portada con dedicatoria, navegación por áreas
y créditos de cada logotipo.

El aspecto real (contraste, 390 px, foco, transiciones) se revisó en Edge; ver
docs/temas-homenaje.md.
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
        entrada = (STATIC / "styles.css").read_text(encoding="utf-8")
        for estilo in HOMENAJES:
            for tema in ("light", "dark"):
                bloque = re.search(rf'\[data-estilo="{estilo}"\]\[data-theme="{tema}"\] \{{(.*?)\}}', css, re.S)
                self.assertIsNotNone(bloque, f"{estilo} {tema}")
                for token in ("--color-bg", "--color-text", "--color-muted", "--color-brand",
                              "--color-brand-text", "--color-border-input", "--color-focus"):
                    self.assertIn(token + ":", bloque.group(1), f"{estilo} {tema} {token}")
        self.assertLess(entrada.index("estudio.css"), entrada.index("homenajes.css"))
        for estilo in HOMENAJES:
            # Cada tema trae su composición en su propio archivo, cargado después de los tokens.
            self.assertLess(entrada.index("homenajes.css"), entrada.index(f"homenaje-{estilo}.css"))
            propio = (STATIC / "styles" / f"homenaje-{estilo}.css").read_text(encoding="utf-8")
            self.assertIn(f'[data-estilo="{estilo}"] .home-hero', propio)
            self.assertIn(f'[data-estilo="{estilo}"] .canal', propio)

    def test_el_movimiento_respeta_la_preferencia_de_reducirlo(self):
        for estilo in HOMENAJES:
            css = re.sub(r"/\*.*?\*/", "", (STATIC / "styles" / f"homenaje-{estilo}.css").read_text(encoding="utf-8"), flags=re.S)
            movimiento = css.split("@media (prefers-reduced-motion: no-preference)", 1)[1].split("@keyframes", 1)[0]
            fuera = css.replace(movimiento, "")
            self.assertNotRegex(fuera, r"\banimation\s*:", estilo)
            # Cada tema entra con su gesto propio al elegirlo en Opciones.
            self.assertIn(f'[data-cambio-estilo][data-estilo="{estilo}"]::view-transition-new(root)', movimiento)
        # Sus transiciones cumplen el contrato común (test_microinteracciones). Las animaciones
        # sin fin son solo de ambiente, sobre ilustraciones decorativas de la portada o del riel.
        decorativas = {".choco-vapor", ".beluga-mascota", ".beluga-formula", ".hey-estallido"}
        for archivo in sorted((STATIC / "styles").glob("homenaje*.css")):
            css = re.sub(r"/\*.*?\*/", "", archivo.read_text(encoding="utf-8"), flags=re.S)
            for selector, cuerpo in re.findall(r"([^{}]+)\{([^{}]*\binfinite\b[^{}]*)\}", css):
                with self.subTest(archivo=archivo.name, selector=selector.strip()):
                    self.assertTrue(any(d in selector for d in decorativas))
        opciones = (STATIC / "opciones.js").read_text(encoding="utf-8")
        self.assertIn('matchMedia("(prefers-reduced-motion: reduce)").matches', opciones)
        self.assertIn("document.startViewTransition", opciones)

    def test_inicio_y_opciones_reconocen_a_cada_equipo(self):
        html = self.client.get("/").content.decode("utf-8")
        for estilo, nombre in zip(HOMENAJES, ("ChocoLab", "BelugaCalc", "HeyAlgb")):
            self.assertIn(f'<input type="radio" name="estilo" value="{estilo}">', html)
            portada = re.search(rf'<figure class="portada" data-homenaje="{estilo}">(.*?)</figure>', html, re.S).group(1)
            self.assertIn(f"En honor a <b>{nombre}</b>", portada)
            self.assertIn(f"calculadora/homenajes/{estilo}.png", portada)
            # Las ilustraciones son decorativas; la dedicatoria es texto que se lee.
            self.assertNotRegex(portada, r"<figcaption[^>]*aria-hidden")
            self.assertIn(f"<b>{nombre}</b><small>En honor a {nombre}</small>", html)
            self.assertIn(f"calculadora/homenajes/{estilo}.png", html)
        # La identidad de PyGebra no cambia: mismo título y símbolo.
        self.assertIn('<h1 class="home-title">PyGebra</h1>', html)

    def test_la_navegacion_por_areas_marca_donde_esta(self):
        def actual(html):
            nav = re.search(r'<nav class="nav-areas"[^>]*>(.*?)</nav>', html, re.S).group(1)
            return re.findall(r'href="([^"]+)"[^>]*aria-current="(\w+)"', nav)

        self.assertEqual(actual(self.client.get("/").content.decode("utf-8")), [("/", "page")])
        self.assertEqual(actual(self.client.get("/areas/algebra-lineal/").content.decode("utf-8")),
                         [("/areas/algebra-lineal/", "page")])
        # En una herramienta el área es la sección actual, no la página.
        self.assertEqual(actual(self.client.get("/matrices/ecuaciones/").content.decode("utf-8")),
                         [("/areas/algebra-lineal/", "true")])

    def test_la_muesca_de_belugacalc_apunta_al_enlace_activo(self):
        for ruta in ("/", "/areas/sistemas-numericos/", "/areas/conjuntos/", "/matrices/ecuaciones/",
                     "/metodos-numericos/metodos-cerrados/biseccion/"):
            html = self.client.get(ruta).content.decode("utf-8")
            nav = re.search(r'<nav class="nav-areas"[^>]*style="--activo: (\d+)"[^>]*>(.*?)</nav>', html, re.S)
            enlaces = re.findall(r"<li><a[^>]*>", nav.group(2))
            activo = [i for i, enlace in enumerate(enlaces) if "aria-current" in enlace]
            self.assertEqual(activo, [int(nav.group(1))], ruta)

    def test_cada_logotipo_tiene_credito_y_procedencia_verificable(self):
        creditos = (RAIZ / "docs" / "temas-homenaje.md").read_text(encoding="utf-8")
        archivos = sorted((STATIC / "homenajes").iterdir())
        self.assertEqual([a.name for a in archivos], sorted(f"{e}.png" for e in HOMENAJES))
        for archivo in archivos:
            fila = next(l for l in creditos.splitlines() if l.startswith(f"| `{archivo.name}`"))
            self.assertIn(hashlib.sha256(archivo.read_bytes()).hexdigest(), fila)
