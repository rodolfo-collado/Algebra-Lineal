"""Transporte HTTPS del actualizador."""

import ssl
import sys
from urllib.request import urlopen


def abrir_https(peticion, *, timeout):
    if sys.platform != "win32":
        return urlopen(peticion, timeout=timeout)

    import truststore

    # CryptoAPI puede obtener raíces bajo demanda en un Windows recién instalado.
    contexto = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    contexto.set_alpn_protocols(["http/1.1"])
    return urlopen(peticion, timeout=timeout, context=contexto)
