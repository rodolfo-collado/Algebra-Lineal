"""SHA-256 del instalador frente a la línea de ``SHA256SUMS.txt`` publicada."""

import hashlib
import hmac
import re


_HEX = re.compile(r"[0-9a-f]{64}")


class ChecksumInvalido(Exception):
    """El archivo no coincide o el checksum publicado no se puede usar."""


def checksum_publicado(texto, nombre):
    """Checksum de ``nombre`` en formato ``sha256sum``; exige exactamente una entrada."""
    encontrados = set()
    for linea in texto.splitlines():
        partes = linea.split()
        # «*» marca el modo binario de sha256sum; el nombre es el mismo.
        if len(partes) == 2 and partes[1].removeprefix("*") == nombre:
            encontrados.add(partes[0].lower())
    if len(encontrados) != 1:
        raise ChecksumInvalido(f"SHA256SUMS.txt no tiene una entrada única para {nombre}.")
    esperado = encontrados.pop()
    if not _HEX.fullmatch(esperado):
        raise ChecksumInvalido(f"El checksum publicado para {nombre} no es SHA-256.")
    return esperado


def sha256_archivo(ruta):
    with open(ruta, "rb") as archivo:
        return hashlib.file_digest(archivo, "sha256").hexdigest()


def verificar(ruta, esperado):
    """Lanza ChecksumInvalido salvo que el archivo en disco coincida exactamente."""
    if not hmac.compare_digest(sha256_archivo(ruta), esperado):
        raise ChecksumInvalido("El instalador descargado no coincide con el checksum publicado.")
