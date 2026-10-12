"""Release estable más reciente de GitHub y URLs oficiales de sus artefactos.

Una sola llamada a la API pública, únicamente cuando el usuario busca actualizaciones.
``releases/latest`` ya excluye drafts y prereleases; aun así se comprueban aquí.
Las URLs de descarga se construyen con el repositorio y el tag, nunca se toman
del JSON, para que solo se descargue desde ``github.com/<repositorio>/releases``.
"""

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .versiones import parsear


REPOSITORIO = "rodolfo-collado/Algebra-Lineal"
API_ULTIMA_RELEASE = f"https://api.github.com/repos/{REPOSITORIO}/releases/latest"
CHECKSUMS = "SHA256SUMS.txt"
TIMEOUT_SEGUNDOS = 15
CABECERAS = {"User-Agent": "PyGebra-Actualizador"}


class ErrorConexion(Exception):
    """GitHub no respondió o la conexión falló."""


class ReleaseInvalida(Exception):
    """La release existe pero no tiene la forma que publica el flujo oficial."""


@dataclass(frozen=True)
class Artefacto:
    nombre: str
    url: str
    tamano: int


@dataclass(frozen=True)
class Release:
    version: str
    # Nombre → tamaño de cada asset publicado.
    assets: dict

    def artefacto(self, nombre):
        """Asset oficial de esta release; falta o tamaño inválido es ReleaseInvalida."""
        tamano = self.assets.get(nombre)
        if isinstance(tamano, bool) or not isinstance(tamano, int) or tamano <= 0:
            raise ReleaseInvalida(f"La release v{self.version} no publica {nombre}.")
        url = f"https://github.com/{REPOSITORIO}/releases/download/v{self.version}/{nombre}"
        return Artefacto(nombre, url, tamano)

    @property
    def instalador(self):
        return self.artefacto(nombre_instalador(self.version))

    @property
    def checksums(self):
        return self.artefacto(CHECKSUMS)


def nombre_instalador(version):
    return f"PyGebra-Setup-{version}.exe"


def interpretar(datos):
    """Release estable ``vX.Y.Z``, o None si es draft, prerelease o tag no estable.

    Los artefactos se resuelven después, solo si la versión es más nueva: una
    release igual o anterior sin instalador no impide decir «actualizado».
    """
    if not isinstance(datos, dict):
        raise ReleaseInvalida("Respuesta inesperada de GitHub.")
    tag = datos.get("tag_name")
    if datos.get("draft") or datos.get("prerelease") or not isinstance(tag, str):
        return None
    if not tag.startswith("v") or parsear(tag[1:]) is None:
        return None
    assets = {
        asset.get("name"): asset.get("size")
        for asset in datos.get("assets") or ()
        if isinstance(asset, dict)
    }
    return Release(tag[1:], assets)


def consultar_ultima(abrir=urlopen):
    """Consulta la release marcada como más reciente; None si no hay ninguna estable."""
    peticion = Request(
        API_ULTIMA_RELEASE,
        headers={**CABECERAS, "Accept": "application/vnd.github+json"},
    )
    try:
        with abrir(peticion, timeout=TIMEOUT_SEGUNDOS) as respuesta:
            cuerpo = respuesta.read()
    except HTTPError as error:
        # 404: el repositorio todavía no tiene releases estables.
        if error.code == 404:
            return None
        raise ErrorConexion(f"GitHub respondió HTTP {error.code}.") from error
    except (URLError, OSError) as error:
        raise ErrorConexion("No se pudo conectar con GitHub.") from error
    try:
        datos = json.loads(cuerpo)
    except ValueError as error:
        raise ReleaseInvalida("Respuesta inesperada de GitHub.") from error
    return interpretar(datos)
