"""Versión instalada y comparación de versiones estables ``X.Y.Z``."""

import re
import tomllib
from pathlib import Path


# PyInstaller incluye pyproject.toml en la raíz de _internal, igual que en el checkout.
PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"
# Mismo formato que publica la release automática: sin prefijo, sufijos ni ceros a la izquierda.
_ESTABLE = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")


def parsear(texto):
    """Devuelve la versión como tupla comparable o None si no es estable ``X.Y.Z``."""
    coincidencia = _ESTABLE.fullmatch(texto) if isinstance(texto, str) else None
    return tuple(int(parte) for parte in coincidencia.groups()) if coincidencia else None


def version_instalada(ruta=PYPROJECT):
    """Versión del proyecto empaquetado; la misma que el instalador y el EXE."""
    with open(ruta, "rb") as archivo:
        version = tomllib.load(archivo)["project"]["version"]
    if parsear(version) is None:
        raise ValueError(f"Versión instalada no válida: {version!r}")
    return version


def es_mas_nueva(remota, instalada):
    """Compara numéricamente: 0.10.0 es más nueva que 0.9.0."""
    return parsear(remota) > parsear(instalada)
