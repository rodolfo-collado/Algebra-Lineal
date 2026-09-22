# -*- coding: utf-8 -*-
"""Regenera los PNG e ICO de PyGebra a partir del path canónico.

Solo usa la biblioteca estándar. Desde la raíz del repositorio:

    python scripts/generate_brand_assets.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
BRAND = RAIZ / "assets" / "brand"
ESTATICOS = RAIZ / "frontend" / "web" / "calculadora" / "static" / "calculadora"

# Geometría aprobada. No reconstruirla.
CANONICAL_D = "M2 12H62V34H22V42H40V40L56 46L40 52V50H14V26H54V20H2Z"
VIEWBOX = 64
PNG_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)
FAVICON_ICO_SIZES = (16, 32, 48)
DESKTOP_ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
APP_SIZES = (192, 256, 512)
# El lienzo 64 ocupa esta fracción del lado. El símbolo no se estira.
APP_VIEWBOX_FRACTION = 0.68

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def polygon(d: str) -> list[tuple[float, float]]:
    tokens: list[str] = []
    number = ""
    for char in d:
        if char in "MHVLZ":
            if number:
                tokens.append(number)
                number = ""
            tokens.append(char)
        elif char == " ":
            if number:
                tokens.append(number)
                number = ""
        else:
            number += char
    if number:
        tokens.append(number)

    points: list[tuple[float, float]] = []
    x = y = 0.0
    index = 0
    while index < len(tokens):
        command = tokens[index]
        index += 1
        if command == "Z":
            break
        if command == "M":
            x, y = float(tokens[index]), float(tokens[index + 1])
            index += 2
        elif command == "H":
            x = float(tokens[index])
            index += 1
        elif command == "V":
            y = float(tokens[index])
            index += 1
        elif command == "L":
            x, y = float(tokens[index]), float(tokens[index + 1])
            index += 2
        else:
            raise ValueError(f"comando no admitido: {command}")
        points.append((x, y))
    return points


POINTS = polygon(CANONICAL_D)


def inside(x: float, y: float) -> bool:
    """Inclusión par-impar. Las aristas horizontales no cruzan el rayo."""
    hit = False
    count = len(POINTS)
    for index in range(count):
        x1, y1 = POINTS[index]
        x2, y2 = POINTS[(index + 1) % count]
        if (y1 > y) == (y2 > y):
            continue
        x_hit = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
        if x < x_hit:
            hit = not hit
    return hit


def raster(size: int, color: tuple[int, int, int], samples: int = 4) -> bytes:
    """RGBA, arriba-izquierda en el origen, fondo transparente."""
    step = samples
    total = step * step
    red, green, blue = color
    pixels = bytearray(size * size * 4)
    scale = VIEWBOX / (size * step)
    for py in range(size):
        for px in range(size):
            covered = 0
            for sy in range(step):
                vy = (py * step + sy + 0.5) * scale
                for sx in range(step):
                    vx = (px * step + sx + 0.5) * scale
                    if inside(vx, vy):
                        covered += 1
            if covered:
                offset = (py * size + px) * 4
                pixels[offset] = red
                pixels[offset + 1] = green
                pixels[offset + 2] = blue
                pixels[offset + 3] = (covered * 255 + total // 2) // total
    return bytes(pixels)


def fit_on_square(canvas: int, color: tuple[int, int, int]) -> bytes:
    side = max(1, round(canvas * APP_VIEWBOX_FRACTION))
    mark = raster(side, color, samples=4 if side > 64 else 6)
    image = bytearray(canvas * canvas * 4)
    origin_x = (canvas - side) // 2
    origin_y = (canvas - side) // 2
    row_bytes = side * 4
    for y in range(side):
        start = ((origin_y + y) * canvas + origin_x) * 4
        image[start : start + row_bytes] = mark[y * row_bytes : (y + 1) * row_bytes]
    return bytes(image)


def png(rgba: bytes, width: int, height: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = b"".join(
        b"\x00" + rgba[y * width * 4 : (y + 1) * width * 4] for y in range(height)
    )
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def ico(images: list[tuple[int, bytes]]) -> bytes:
    """ICO con mapas de 32 bits y máscara AND. `images` es (lado, RGBA)."""
    entries = bytearray()
    payload = bytearray()
    offset = 6 + 16 * len(images)
    for side, rgba in images:
        xor_rows = bytearray()
        and_stride = ((side + 31) // 32) * 4
        and_rows = bytearray()
        for y in range(side - 1, -1, -1):
            row = rgba[y * side * 4 : (y + 1) * side * 4]
            for index in range(0, len(row), 4):
                red, green, blue, alpha = row[index : index + 4]
                xor_rows += bytes((blue, green, red, alpha))
            mask = bytearray(and_stride)
            for x in range(side):
                if row[x * 4 + 3] == 0:
                    mask[x // 8] |= 0x80 >> (x % 8)
            and_rows += mask
        header = struct.pack(
            "<IiiHHIIiiII",
            40,
            side,
            side * 2,
            1,
            32,
            0,
            len(xor_rows) + len(and_rows),
            0,
            0,
            0,
            0,
        )
        blob = header + xor_rows + and_rows
        entries += struct.pack(
            "<BBBBHHII",
            side if side < 256 else 0,
            side if side < 256 else 0,
            0,
            0,
            1,
            32,
            len(blob),
            offset,
        )
        payload += blob
        offset += len(blob)
    header = struct.pack("<HHH", 0, 1, len(images))
    return header + bytes(entries) + bytes(payload)


def svg(fill: str, view_box: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="'
        + view_box
        + '">\n  <path fill="'
        + fill
        + '" d="'
        + CANONICAL_D
        + '"/>\n</svg>\n'
    )


def favicon_svg() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">\n'
        "  <style>\n"
        "    path { fill: #000000 }\n"
        "    @media (prefers-color-scheme: dark) { path { fill: #FFFFFF } }\n"
        "  </style>\n"
        f'  <path d="{CANONICAL_D}"/>\n'
        "</svg>\n"
    )


def write(path: Path, data: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8", newline="\n")
    else:
        path.write_bytes(data)


def check_raster(size: int, rgba: bytes, color: tuple[int, int, int]) -> None:
    def pixel(x: int, y: int) -> tuple[int, int, int, int]:
        # x, y en coordenadas del lienzo 64, centro del pixel correspondiente.
        px = min(size - 1, max(0, round((x + 0.5) * size / VIEWBOX - 0.5)))
        py = min(size - 1, max(0, round((y + 0.5) * size / VIEWBOX - 0.5)))
        index = (py * size + px) * 4
        return tuple(rgba[index : index + 4])  # type: ignore[return-value]

    bar = pixel(32, 16)
    gap = pixel(30, 23)
    assert bar[3] > 200 and bar[:3] == color, bar
    assert gap[3] == 0, gap


def main() -> None:
    svg_dir = BRAND / "svg"
    png_dir = BRAND / "png"
    favicon_dir = BRAND / "favicon"
    app_dir = BRAND / "app"

    write(svg_dir / "pygebra-mark.svg", svg("currentColor", "0 0 64 64"))
    write(svg_dir / "pygebra-mark-black.svg", svg("#000000", "0 0 64 64"))
    write(svg_dir / "pygebra-mark-white.svg", svg("#FFFFFF", "0 0 64 64"))
    write(svg_dir / "pygebra-mark-tight.svg", svg("currentColor", "2 12 60 40"))

    favicon = favicon_svg()
    write(favicon_dir / "favicon.svg", favicon)
    write(ESTATICOS / "favicon.svg", favicon)

    cache: dict[tuple[int, tuple[int, int, int]], bytes] = {}

    def image(size: int, color: tuple[int, int, int]) -> bytes:
        key = (size, color)
        if key not in cache:
            samples = 6 if size <= 48 else 4
            cache[key] = raster(size, color, samples=samples)
            if size >= 32:
                check_raster(size, cache[key], color)
        return cache[key]

    for size in PNG_SIZES:
        for name, color in (("black", BLACK), ("white", WHITE)):
            rgba = image(size, color)
            write(png_dir / f"pygebra-mark-{name}-{size}.png", png(rgba, size, size))

    for size in (16, 32):
        rgba = image(size, BLACK)
        write(favicon_dir / f"favicon-{size}x{size}.png", png(rgba, size, size))

    favicon_ico = ico([(size, image(size, BLACK)) for size in FAVICON_ICO_SIZES])
    write(favicon_dir / "favicon.ico", favicon_ico)
    write(ESTATICOS / "favicon.ico", favicon_ico)

    desktop_ico = ico([(size, image(size, BLACK)) for size in DESKTOP_ICO_SIZES])
    write(app_dir / "pygebra.ico", desktop_ico)

    for size in APP_SIZES:
        for name, color in (("", BLACK), ("-white", WHITE)):
            composed = fit_on_square(size, color)
            write(app_dir / f"app-icon{name}-{size}.png", png(composed, size, size))

    assert (svg_dir / "pygebra-mark.svg").read_text(encoding="utf-8").count(CANONICAL_D) == 1
    assert favicon_ico[:4] == b"\x00\x00\x01\x00"
    assert desktop_ico[:4] == b"\x00\x00\x01\x00"
    print(f"assets regenerados en {BRAND.relative_to(RAIZ).as_posix()}")


if __name__ == "__main__":
    main()
