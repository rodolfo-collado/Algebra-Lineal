"""Estimación previa y firma de confirmación para Operaciones con matrices."""

import json
from fractions import Fraction

from django.utils.crypto import constant_time_compare, salted_hmac

from backend.presupuesto_computacional import Categoria, categoria, intervalo_segundos
from backend.presupuesto_expresiones import analizar_presupuesto

from .servicios_presupuesto import texto_intervalo

MENSAJES_ESPERA = {
    Categoria.PESADA: "La expresión es válida, pero este cálculo puede tardar unos segundos.",
    Categoria.MUY_PESADA: "La expresión es válida, pero este cálculo puede tardar bastante.",
}
_SAL_CONFIRMACION = "pygebra.operaciones-matrices.confirmacion"


def estimar_expresion_web(entrada):
    return analizar_presupuesto(entrada["expresion"], entrada["simbolos"], entrada.get("nodo")).total


def _exacto(valor):
    # Serialización canónica de valores ya validados, nunca para estimar costos.
    if isinstance(valor, (int, Fraction)):
        return [valor.numerator, valor.denominator]
    if isinstance(valor, str):
        return valor
    return [_exacto(entrada) for entrada in valor]


def firmar_entrada(entrada):
    """SHA-256 con HMAC de Django sobre el cálculo exacto y su presentación.

    JSON evita ambigüedades de separadores. Ordenar símbolos no altera el
    cálculo; dimensiones y valores racionales sí forman parte de la firma.
    """
    simbolos = {}
    for nombre, definicion in entrada["simbolos"].items():
        if definicion["tipo"] not in ("matriz", "vector", "escalar"):
            simbolos[nombre] = definicion
            continue
        tipo, valor = definicion["tipo"], definicion["valor"]
        filas = len(valor) if tipo in ("matriz", "vector") else None
        columnas = len(valor[0]) if tipo == "matriz" else None
        simbolos[nombre] = {"tipo": tipo, "filas": filas, "columnas": columnas, "valor": _exacto(valor)}
    contenido = json.dumps({
        "expresion": entrada["expresion"], "simbolos": simbolos,
        "metodo": entrada["metodo"], "nodo": entrada.get("nodo"),
    }, sort_keys=True, separators=(",", ":"))
    return salted_hmac(_SAL_CONFIRMACION, contenido, algorithm="sha256").hexdigest()


def confirmacion_pendiente(entrada, firma=""):
    estimacion = estimar_expresion_web(entrada)
    if estimacion is None or categoria(estimacion) < Categoria.PESADA:
        return None
    esperada = firmar_entrada(entrada)
    if constant_time_compare(firma or "", esperada):
        return None
    return {
        "firma": esperada, "mensaje": MENSAJES_ESPERA[categoria(estimacion)],
        "tiempo": texto_intervalo(*intervalo_segundos(estimacion)),
    }
