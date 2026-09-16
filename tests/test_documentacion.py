"""Enlaces locales de la documentación, sin red ni un parser Markdown completo."""

from collections import Counter
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit


RAIZ = Path(__file__).resolve().parents[1]
DOCUMENTOS = [RAIZ / "README.md", RAIZ / "CONTRIBUTING.md", *sorted((RAIZ / "docs").glob("*.md"))]


def sin_bloques(texto):
    return re.sub(r"^```[^\n]*\n.*?^```\s*$", "", texto, flags=re.M | re.S)


def anchors(texto):
    vistos = Counter()
    resultado = set()
    for titulo in re.findall(r"^#{1,6} (.+)$", sin_bloques(texto), flags=re.M):
        slug = re.sub(r"[^\w\- ]", "", titulo.lower()).replace(" ", "-")
        resultado.add(slug if vistos[slug] == 0 else f"{slug}-{vistos[slug]}")
        vistos[slug] += 1
    resultado.update(re.findall(r'(?:id|name)="([^"]+)"', texto))
    return resultado


class PruebasDocumentacion(unittest.TestCase):
    def test_enlaces_relativos_existen_y_sus_anchors_tambien(self):
        for documento in DOCUMENTOS:
            texto = sin_bloques(documento.read_text(encoding="utf-8"))
            destinos = re.findall(r"\]\(([^\s)]+)\)", texto)
            destinos += re.findall(r'(?:href|src)="([^"]+)"', texto)
            for destino in destinos:
                url = urlsplit(destino.strip("<>"))
                if url.scheme or url.netloc:
                    continue
                with self.subTest(archivo=documento.name, enlace=destino):
                    ruta = (documento.parent / unquote(url.path)).resolve() if url.path else documento
                    self.assertTrue(ruta.is_file(), f"No existe {ruta}")
                    if url.fragment and ruta.suffix == ".md":
                        self.assertIn(unquote(url.fragment), anchors(ruta.read_text(encoding="utf-8")))

    def test_bloques_markdown_cerrados(self):
        for documento in DOCUMENTOS:
            with self.subTest(archivo=documento.name):
                fences = re.findall(r"^\s*```", documento.read_text(encoding="utf-8"), flags=re.M)
                self.assertEqual(len(fences) % 2, 0)


if __name__ == "__main__":
    unittest.main()
