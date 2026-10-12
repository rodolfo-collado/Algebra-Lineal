"""Estado del flujo de actualización que muestra la interfaz.

Nada ocurre sin una acción del usuario: buscar, descargar e instalar son pasos
separados. La descarga corre en un hilo para que la ventana siga respondiendo, y
cualquier fallo termina en un estado con mensaje, nunca en una excepción que
cierre PyGebra. La instalación actual no se toca hasta lanzar un instalador
completo y verificado.
"""

import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from urllib.request import urlopen

from . import descarga, instalador, releases, verificacion, versiones


INICIAL = "inicial"
BUSCANDO = "buscando"
ACTUALIZADO = "actualizado"
DISPONIBLE = "disponible"
DESCARGANDO = "descargando"
VERIFICANDO = "verificando"
LISTO = "listo"
INSTALANDO = "instalando"
ERROR_CONEXION = "error_conexion"
CHECKSUM_INVALIDO = "checksum_invalido"
ERROR = "error"

OCUPADO = frozenset({BUSCANDO, DESCARGANDO, VERIFICANDO, INSTALANDO})

MENSAJES = {
    INICIAL: "PyGebra solo se conecta a Internet cuando buscas o descargas una actualización.",
    BUSCANDO: "Buscando actualizaciones…",
    ACTUALIZADO: "PyGebra está actualizado.",
    DISPONIBLE: "Hay una nueva versión disponible: PyGebra {disponible}.",
    DESCARGANDO: "Descargando PyGebra {disponible}…",
    VERIFICANDO: "Verificando la descarga…",
    LISTO: (
        "La actualización está lista para instalar. PyGebra se cerrará durante la "
        "instalación y volverá a abrirse al terminar."
    ),
    INSTALANDO: "Abriendo el instalador. PyGebra se cerrará en unos segundos.",
    ERROR_CONEXION: (
        "No se pudo conectar con el servidor de actualizaciones. "
        "Comprueba tu conexión a Internet e inténtalo de nuevo."
    ),
    CHECKSUM_INVALIDO: (
        "La descarga no superó la verificación de seguridad y se descartó. "
        "No se instaló nada. Inténtalo de nuevo más tarde."
    ),
    ERROR: "No se pudo completar la actualización. Inténtalo de nuevo más tarde.",
}

# %TEMP% es por usuario en Windows; cada descarga empieza con la carpeta vacía.
CARPETA = Path(tempfile.gettempdir()) / "PyGebra-actualizacion"


def _en_hilo(funcion):
    threading.Thread(target=funcion, name="PyGebra-Actualizacion", daemon=True).start()


class Actualizador:
    def __init__(self, *, abrir=urlopen, popen=subprocess.Popen, carpeta=CARPETA,
                 pyproject=versiones.PYPROJECT, en_segundo_plano=_en_hilo):
        self._abrir = abrir
        self._popen = popen
        self._carpeta = Path(carpeta)
        self._pyproject = pyproject
        self._en_segundo_plano = en_segundo_plano
        self._lock = threading.Lock()
        self._estado = INICIAL
        self._release = None
        self._progreso = None
        self._descargado = None
        # La app de escritorio lo fija para cerrarse tras lanzar el instalador.
        self.cerrar_aplicacion = None

    def _version_instalada(self):
        try:
            return versiones.version_instalada(self._pyproject)
        except (OSError, KeyError, ValueError):
            return None

    def _resumen(self):
        disponible = self._release.version if self._release else None
        return {
            "estado": self._estado,
            "mensaje": MENSAJES[self._estado].format(disponible=disponible),
            "version_instalada": self._version_instalada(),
            "version_disponible": disponible,
            "progreso": self._progreso,
        }

    def estado(self):
        with self._lock:
            return self._resumen()

    def _terminar(self, estado, release=None):
        with self._lock:
            self._estado, self._release, self._progreso = estado, release, None
            return self._resumen()

    def buscar(self):
        with self._lock:
            if self._estado in OCUPADO:
                return self._resumen()
            self._estado, self._release, self._progreso, self._descargado = BUSCANDO, None, None, None
        try:
            instalada = versiones.version_instalada(self._pyproject)
            release = releases.consultar_ultima(self._abrir)
            if release is None or not versiones.es_mas_nueva(release.version, instalada):
                return self._terminar(ACTUALIZADO)
            # Un artefacto inexistente se informa ahora, antes de ofrecer la descarga.
            release.instalador, release.checksums
        except releases.ErrorConexion:
            return self._terminar(ERROR_CONEXION)
        except Exception:
            return self._terminar(ERROR)
        return self._terminar(DISPONIBLE, release)

    def descargar(self):
        with self._lock:
            if self._estado != DISPONIBLE:
                return self._resumen()
            self._estado, self._progreso = DESCARGANDO, 0
            release = self._release
        self._en_segundo_plano(lambda: self._descargar(release))
        return self.estado()

    def _avanzar(self, recibidos, total):
        with self._lock:
            self._progreso = recibidos * 100 // total

    def _descargar(self, release):
        try:
            shutil.rmtree(self._carpeta, ignore_errors=True)
            self._carpeta.mkdir(parents=True, exist_ok=True)
            # Primero el checksum: si falta la entrada no se descargan los ~25 MB.
            sumas = release.checksums
            ruta_sumas = self._carpeta / sumas.nombre
            descarga.descargar(sumas.url, ruta_sumas, sumas.tamano, self._abrir)
            setup = release.instalador
            esperado = verificacion.checksum_publicado(
                ruta_sumas.read_text(encoding="utf-8"), setup.nombre
            )
            ruta = self._carpeta / setup.nombre
            descarga.descargar(setup.url, ruta, setup.tamano, self._abrir, self._avanzar)
            with self._lock:
                self._estado, self._progreso = VERIFICANDO, None
            verificacion.verificar(ruta, esperado)
        except descarga.DescargaFallida:
            final = ERROR_CONEXION
        except verificacion.ChecksumInvalido:
            final = CHECKSUM_INVALIDO
        except Exception:
            final = ERROR
        else:
            with self._lock:
                self._estado, self._descargado = LISTO, (ruta, esperado)
            return
        # Ninguna descarga inválida o a medias queda en disco.
        shutil.rmtree(self._carpeta, ignore_errors=True)
        self._terminar(final)

    def instalar(self):
        with self._lock:
            if self._estado != LISTO:
                return self._resumen()
            ruta, esperado = self._descargado
        try:
            instalador.lanzar(ruta, esperado, self._popen)
        except verificacion.ChecksumInvalido:
            final = CHECKSUM_INVALIDO
        except Exception:
            final = ERROR
        else:
            with self._lock:
                self._estado = INSTALANDO
                resumen = self._resumen()
            if self.cerrar_aplicacion is not None:
                self.cerrar_aplicacion()
            return resumen
        shutil.rmtree(self._carpeta, ignore_errors=True)
        return self._terminar(final)


ACTUALIZADOR = Actualizador()
