"""Pantalla de Actualizaciones: que represente cada estado público y que su ambiente sea discreto.

La lógica del actualizador tiene su suite en test_actualizador.py; aquí solo se prueba la
presentación. La percepción del movimiento y de la escena se verifica en WebView2.
"""

import re
from pathlib import Path

from django.test import SimpleTestCase, override_settings

from actualizador import servicio
from frontend.web.calculadora.views import ACCIONES_ACTUALIZACION


STATIC = Path(__file__).resolve().parents[1] / "frontend/web/calculadora/static/calculadora"
CSS = STATIC / "styles" / "actualizaciones.css"
JS = STATIC / "actualizaciones.js"


def sin_comentarios(texto):
    return re.sub(r"/\*.*?\*/", "", texto, flags=re.S)


def variantes(fragmento):
    return [set(valor.split()) for valor in re.findall(r'data-para="([^"]+)"', fragmento)]


@override_settings(DESKTOP_MODE=True)
class PruebasEscenaActualizaciones(SimpleTestCase):
    def setUp(self):
        self.html = self.client.get("/actualizaciones/").content.decode("utf-8")

    def test_cada_estado_publico_tiene_un_titulo_y_un_texto_de_accion(self):
        titulo = re.search(r'<h2 class="lanzador-estado">(.*?)</h2>', self.html, re.S).group(1)
        boton = re.search(r"<button[^>]*data-accion[^>]*>(.*?)</button>", self.html, re.S).group(1)
        css = sin_comentarios(CSS.read_text(encoding="utf-8"))
        for estado in servicio.MENSAJES:
            with self.subTest(estado=estado):
                self.assertEqual(sum(estado in v for v in variantes(titulo)), 1)
                self.assertEqual(sum(estado in v for v in variantes(boton)), 1)
                self.assertIn(f'.lanzador[data-estado="{estado}"] [data-para~="{estado}"]', css)

    def test_el_script_usa_los_estados_y_acciones_del_servidor(self):
        js = JS.read_text(encoding="utf-8")
        mapa = re.search(r"accionPorEstado = \{(.*?)\}", js, re.S).group(1)
        for estado, accion in re.findall(r"(\w+): \"(\w+)\"", mapa):
            with self.subTest(estado=estado):
                self.assertIn(estado, servicio.MENSAJES)
                self.assertIn(accion, ACCIONES_ACTUALIZACION)
        pasos = re.search(r"pasoPorEstado = \{(.*?)\}", js, re.S).group(1)
        for estado in re.findall(r"(\w+): \[", pasos):
            self.assertIn(estado, servicio.MENSAJES)

    def test_estructura_accesible(self):
        # Un solo botón: conserva el foco mientras cambia de acción.
        self.assertEqual(self.html.count("data-accion="), 1)
        self.assertIn('data-mensaje role="status" aria-live="polite"', self.html)
        self.assertRegex(self.html, r'<progress class="sr-only" data-progreso max="100" aria-label="[^"]+"')
        self.assertIn('<ol class="lanzador-ruta" aria-label="Pasos de la actualización">', self.html)
        # La escena es decorativa y sus ids no chocan con los de la página.
        for capa in ("lanzador-cielo", "lanzador-suelo", "lanzador-linea"):
            self.assertIn(f'class="{capa}" aria-hidden="true"', self.html)
        ids = re.findall(r'\bid="([^"]+)"', self.html)
        self.assertEqual(len(ids), len(set(ids)))

    def test_el_ambiente_solo_se_mueve_con_movimiento_permitido(self):
        css = sin_comentarios(CSS.read_text(encoding="utf-8"))
        movimiento = css.split("@media (prefers-reduced-motion: no-preference)", 1)[1].split("@keyframes", 1)[0]
        fuera = css.replace(movimiento, "")
        # base.css cancela todo lo demás con movimiento reducido.
        self.assertNotRegex(fuera, r"\banimation\s*:")
        self.assertNotRegex(fuera, r"\binfinite\b")
        # Los bucles mueven solo la ilustración o la señal de que algo está en curso.
        for selector, _ in re.findall(r"([^{}]+)\{([^{}]*\binfinite\b[^{}]*)\}", movimiento):
            with self.subTest(selector=selector.strip()):
                self.assertRegex(selector, r"lanzador-(solido|marcas|vector|linea::after|nodo::before)")
        # Ningún fotograma mueve el contenido: solo transform y opacity.
        for nombre, cuerpo in re.findall(r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", css):
            with self.subTest(keyframes=nombre):
                self.assertLessEqual(set(re.findall(r"([\w-]+)\s*:", cuerpo)), {"transform", "opacity"})
