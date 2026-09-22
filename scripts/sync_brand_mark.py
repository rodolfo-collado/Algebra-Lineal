"""Sincroniza el símbolo del header desde el SVG canónico, sin redibujarlo."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/brand/svg/pygebra-mark.svg"
TARGET = ROOT / "frontend/web/calculadora/templates/calculadora/components/mark.html"


def header_mark():
    return (
        "{% comment %}Generado desde assets/brand/svg/pygebra-mark.svg por scripts/sync_brand_mark.py.{% endcomment %}\n"
        + SOURCE.read_text(encoding="utf-8").replace(
            "<svg ", '<svg class="app-mark" aria-hidden="true" focusable="false" ', 1
        )
    )


if __name__ == "__main__":
    TARGET.write_text(header_mark(), encoding="utf-8", newline="\n")
