"""Recurso de versión de PyInstaller, generado desde pyproject.toml con stdlib."""

import re
import tomllib
from pathlib import Path


def version_info(project_file: Path) -> str:
    with project_file.open("rb") as stream:
        version = tomllib.load(stream)["project"]["version"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?", version):
        raise ValueError("Windows requiere una versión de 3 o 4 componentes numéricos.")
    parts = tuple(map(int, version.split(".")))
    if any(part > 65535 for part in parts):
        raise ValueError("Cada componente de la versión Windows debe ser <= 65535.")
    numeric = parts + (0,) * (4 - len(parts))
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={numeric!r}, prodvers={numeric!r},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1,
    subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('ProductName', 'PyGebra'),
      StringStruct('FileDescription', 'PyGebra'),
      StringStruct('CompanyName', 'Proyecto PyGebra'),
      StringStruct('OriginalFilename', 'AlgebraLineal.exe'),
      StringStruct('FileVersion', {version!r}),
      StringStruct('ProductVersion', {version!r})])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])])
"""
