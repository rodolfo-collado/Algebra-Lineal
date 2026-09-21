"""P19: contratos CSS; la percepción del movimiento se verifica en navegador.

P17/P18, navegación, formularios sin JS y empaquetado conservan sus suites.
No se simulan animaciones ni se duplican las pruebas matemáticas aquí.
"""

import re
import unittest
from pathlib import Path


STATIC = Path(__file__).resolve().parents[1] / "frontend/web/calculadora/static/calculadora"
STYLES = STATIC / "styles"


def leer(nombre):
    return re.sub(r"/\*.*?\*/", "", (STYLES / nombre).read_text(encoding="utf-8"), flags=re.S)


class PruebasMicrointeracciones(unittest.TestCase):
    def test_tokens_breves_compartidos_sin_retrasos(self):
        tokens = dict(re.findall(r"(--motion[\w-]*)\s*:\s*([^;]+);", leer("tokens.css")))
        self.assertIn("--motion", tokens)
        self.assertIn("--motion-fast", tokens)
        for nombre, valor in tokens.items():
            with self.subTest(token=nombre):
                self.assertRegex(valor, r"^\d+ms ease(?:-out)?$")
                self.assertGreater(int(valor.split("ms")[0]), 0)
                self.assertLessEqual(int(valor.split("ms")[0]), 240)

    def test_transiciones_declaran_solo_propiedades_visuales(self):
        permitidas = {"background", "background-color", "border-color", "color", "box-shadow", "opacity", "transform", "none"}
        for archivo in STYLES.glob("*.css"):
            for valor in re.findall(r"\btransition\s*:\s*([^;{}]+);", leer(archivo.name)):
                for parte in valor.split(","):
                    with self.subTest(archivo=archivo.name, transicion=parte):
                        self.assertIn(parte.strip().split()[0], permitidas)
                        if parte.strip().split()[0] != "none":
                            self.assertRegex(parte, r"var\(--motion(?:-fast)?\)")

    def test_sin_animaciones_infinitas_ni_retardos(self):
        css = "\n".join(leer(p.name) for p in STYLES.glob("*.css"))
        self.assertNotRegex(css, r"\binfinite\b|(?:animation|transition)-delay\s*:")
        for valor in re.findall(r"\banimation\s*:\s*([^;{}]+);", css):
            if not valor.startswith("none"):
                self.assertRegex(valor, r"^[\w-]+ var\(--motion(?:-fast)?\)$")

    def test_reduced_motion_cancela_animaciones_incluso_pseudoelementos(self):
        reducido = leer("base.css").split("@media (prefers-reduced-motion: reduce)", 1)[1]
        self.assertIn("*::before", reducido)
        self.assertIn("*::after", reducido)
        self.assertIn("::details-content", reducido)
        self.assertRegex(reducido, r"animation:\s*none\s*!important")
        self.assertRegex(reducido, r"transition:\s*none\s*!important")
        # No borrar transforms estructurales (icono del buscador, flecha móvil).
        self.assertNotRegex(reducido, r"transform:\s*none\s*!important")

    def test_pulsacion_solo_en_controles_habilitados_y_sin_reduced_motion(self):
        css = leer("components.css")
        self.assertIn("@media (prefers-reduced-motion: no-preference)", css)
        movimiento = css.split("@media (prefers-reduced-motion: no-preference)", 1)[1]
        self.assertRegex(movimiento, r":not\(:disabled\):active\s*\{\s*transform:")
        for selector in (".btn", ".math-key", ".stepper-btn", ".navigation-toggle", ".theme-toggle", ".sidebar-close"):
            self.assertIn(selector, movimiento)
        self.assertIn(":disabled", css)
        self.assertIn("cursor: not-allowed", css)

    def test_hover_de_botones_y_opciones_excluye_disabled(self):
        css = leer("components.css") + leer("shell.css") + leer("modules.css")
        for selector in (".btn-primary", ".btn-secondary", ".math-key", ".stepper-btn", ".navigation-toggle", ".theme-toggle"):
            self.assertIn(f"{selector}:not(:disabled):hover", css)
            self.assertNotIn(f"{selector}:hover", css)
        for selector in (".option", ".segment"):
            self.assertIn(f"{selector}:has(input:enabled):hover", css)
            self.assertIn(f"{selector}:has(input:disabled)", css)

    def test_seleccion_no_cambia_peso_ni_dimensiones(self):
        css = leer("modules.css")
        for selector in ("option", "segment"):
            estado = re.search(rf"\.{selector}:has\(input:checked\)\s*\{{([^}}]+)\}}", css)[1]
            self.assertNotRegex(estado, r"font-weight|padding|margin|width|height|transform")

    def test_foco_permanece_explicito(self):
        css = leer("base.css") + leer("modules.css")
        for selector in ("button:focus-visible", "summary:focus-visible", ".option:has(input:focus-visible)", ".segment:has(input:focus-visible)"):
            self.assertIn(selector, css)
        for regla in re.findall(r"[^{}]*:focus-visible[^{}]*\{([^{}]+)\}", css):
            self.assertRegex(regla, r"outline:\s*3px solid var\(--color-focus\)")

    def test_entrada_disclosure_nativa_y_resultado_visible(self):
        css = leer("components.css")
        self.assertIn("@supports selector(details::details-content)", css)
        self.assertIn("details[open]::details-content", css)
        self.assertIn(".panel-final", css)
        self.assertNotRegex(css, r"opacity:\s*0(?:\.0+)?\s*;")
        self.assertNotIn("animation-fill-mode", css)
        self.assertNotIn("content-visibility:", css)


if __name__ == "__main__":
    unittest.main()
