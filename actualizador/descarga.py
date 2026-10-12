"""Descarga a un archivo ``.part`` que solo toma su nombre final si llegó completo."""

import os
from http.client import HTTPException
from urllib.error import URLError
from urllib.request import Request, urlopen

from .releases import CABECERAS, TIMEOUT_SEGUNDOS


BLOQUE = 64 * 1024


class DescargaFallida(Exception):
    """La descarga se interrumpió, no coincide con el tamaño publicado o no se pudo guardar."""


def descargar(url, destino, tamano, abrir=urlopen, progreso=None):
    """Guarda exactamente ``tamano`` bytes en ``destino``; si falla no deja nada."""
    parcial = destino.with_name(destino.name + ".part")
    recibidos = 0
    try:
        with abrir(Request(url, headers=CABECERAS), timeout=TIMEOUT_SEGUNDOS) as respuesta:
            with open(parcial, "wb") as archivo:
                while bloque := respuesta.read(BLOQUE):
                    recibidos += len(bloque)
                    if recibidos > tamano:
                        raise DescargaFallida("La descarga es mayor que el archivo publicado.")
                    archivo.write(bloque)
                    if progreso is not None:
                        progreso(recibidos, tamano)
        if recibidos != tamano:
            raise DescargaFallida("La descarga terminó incompleta.")
        os.replace(parcial, destino)
    except (URLError, OSError, HTTPException) as error:
        # HTTPException cubre IncompleteRead cuando el servidor corta la conexión.
        raise DescargaFallida("No se pudo completar la descarga.") from error
    finally:
        parcial.unlink(missing_ok=True)
