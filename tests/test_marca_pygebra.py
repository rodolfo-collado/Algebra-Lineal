"""El símbolo oficial de PyGebra es un solo path, y los derivados salen de él."""

import struct
import unittest
import zlib
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
BRAND = RAIZ / "assets" / "brand"
CANONICAL_D = "M2 12H62V34H22V42H40V40L56 46L40 52V50H14V26H54V20H2Z"
PNG_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)


def png_size(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"{path.name} no es un PNG")
    return struct.unpack(">II", data[16:24])


def png_alpha_extrema(path):
    data = path.read_bytes()
    width, height = struct.unpack(">II", data[16:24])
    index = 8
    idat = b""
    while index < len(data):
        length = struct.unpack(">I", data[index : index + 4])[0]
        tag = data[index + 4 : index + 8]
        chunk = data[index + 8 : index + 8 + length]
        if tag == b"IDAT":
            idat += chunk
        elif tag == b"IEND":
            break
        index += 12 + length
    raw = zlib.decompress(idat)
    stride = width * 4 + 1
    alphas = [
        raw[y * stride + 1 + x * 4 + 3]
        for y in range(height)
        for x in range(width)
    ]
    return min(alphas), max(alphas)


class PruebasMarcaPyGebra(unittest.TestCase):
    def test_los_svg_comparten_el_path_canonico(self):
        esperados = {
            "pygebra-mark.svg": ('fill="currentColor"', 'viewBox="0 0 64 64"'),
            "pygebra-mark-black.svg": ('fill="#000000"', 'viewBox="0 0 64 64"'),
            "pygebra-mark-white.svg": ('fill="#FFFFFF"', 'viewBox="0 0 64 64"'),
            "pygebra-mark-tight.svg": ('fill="currentColor"', 'viewBox="2 12 60 40"'),
        }
        for nombre, marcas in esperados.items():
            texto = (BRAND / "svg" / nombre).read_text(encoding="utf-8")
            with self.subTest(archivo=nombre):
                self.assertEqual(texto.count(CANONICAL_D), 1)
                for marca in marcas:
                    self.assertIn(marca, texto)
                self.assertNotIn("<image", texto)
                self.assertNotIn("filter=", texto)
                self.assertNotIn("gradient", texto.lower())

    def test_los_png_tienen_el_lado_pedido_y_transparencia(self):
        for lado in PNG_SIZES:
            for tinta in ("black", "white"):
                ruta = BRAND / "png" / f"pygebra-mark-{tinta}-{lado}.png"
                with self.subTest(archivo=ruta.name):
                    self.assertEqual(png_size(ruta), (lado, lado))
                    minimo, maximo = png_alpha_extrema(ruta)
                    self.assertEqual(minimo, 0)
                    self.assertGreater(maximo, 200)

    def test_el_ico_de_escritorio_trae_siete_imagenes(self):
        contenido = (BRAND / "app" / "pygebra.ico").read_bytes()
        self.assertEqual(contenido[:4], b"\x00\x00\x01\x00")
        self.assertEqual(struct.unpack("<H", contenido[4:6])[0], 7)

    def test_los_iconos_de_aplicacion_dejan_aire(self):
        for lado in (192, 256, 512):
            for nombre in (f"app-icon-{lado}.png", f"app-icon-white-{lado}.png"):
                ruta = BRAND / "app" / nombre
                with self.subTest(archivo=nombre):
                    self.assertEqual(png_size(ruta), (lado, lado))
                    minimo, _maximo = png_alpha_extrema(ruta)
                    self.assertEqual(minimo, 0)
