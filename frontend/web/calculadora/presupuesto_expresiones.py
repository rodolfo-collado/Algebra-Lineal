"""Estimación previa y firma de confirmación para Operaciones con matrices."""

import json
from fractions import Fraction

from django.utils.crypto import constant_time_compare, salted_hmac

from backend.operandos import CELDAS_MAXIMAS, OPERANDOS_MAXIMOS
from backend.presupuesto_computacional import (
    Categoria, categoria, combinar_estimaciones, estimar_gauss_jordan, intervalo_segundos, perfil_numerico,
)
from backend.expresiones_matriciales.combinacion import plantear as plantear_combinacion
from backend.presupuesto_expresiones import analizar_presupuesto

from .servicios_presupuesto import texto_intervalo

MENSAJES_ESPERA = {
    Categoria.PESADA: "La expresión es válida, pero este cálculo puede tardar unos segundos.",
    Categoria.MUY_PESADA: "La expresión es válida, pero este cálculo puede tardar bastante.",
}
MENSAJES_ESPERA_LOTE = {
    Categoria.PESADA: "El cálculo de las expresiones puede tardar unos segundos.",
    Categoria.MUY_PESADA: "El cálculo de las expresiones puede tardar bastante.",
}
_SAL_CONFIRMACION = "pygebra.operaciones-matrices.confirmacion"
# Permite varias expresiones del tamaño habitual, con una cota total de trabajo.
_LIMITES_LOTE = (
    (3 * OPERANDOS_MAXIMOS, "apariciones de operandos"),
    (3 * (OPERANDOS_MAXIMOS - 1), "operaciones"),
    (3 * CELDAS_MAXIMAS, "entradas"),
)


def estimar_expresion_web(entrada, *, incluir_combinacion=False):
    combinacion = plantear_combinacion(entrada["expresion"], entrada["simbolos"])
    if combinacion is not None:
        if not incluir_combinacion:
            return None
        generadores = combinacion["generadores"]
        objetivo = combinacion["objetivo"][1]
        perfil = perfil_numerico([valor for _, valor in generadores], [objetivo])
        return estimar_gauss_jordan(len(objetivo), len(generadores) + 1, columnas_pivote=len(generadores), perfil=perfil)
    return analizar_presupuesto(entrada["expresion"], entrada["simbolos"], entrada.get("nodo")).total


def _exacto(valor):
    # Serialización canónica de valores ya validados, nunca para estimar costos.
    if isinstance(valor, (int, Fraction)):
        return [valor.numerator, valor.denominator]
    if isinstance(valor, str):
        return valor
    return [_exacto(entrada) for entrada in valor]


def sumar_uso(acumulado, uso):
    total = tuple(anterior + actual for anterior, actual in zip(acumulado, uso))
    for cantidad, (limite, unidad) in zip(total, _LIMITES_LOTE):
        if cantidad > limite:
            raise ValueError(f"Esta expresión supera el límite de {limite} {unidad} por resolución. "
                             "Calcula menos expresiones juntas o simplifícalas.")
    return total


def firmar_entrada(entrada, lote=()):
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
    datos = {
        "expresion": entrada["expresion"], "simbolos": simbolos,
        "metodo": entrada["metodo"], "nodo": entrada.get("nodo"),
    }
    if lote:
        datos["lote"] = lote
    contenido = json.dumps(datos, sort_keys=True, separators=(",", ":"))
    return salted_hmac(_SAL_CONFIRMACION, contenido, algorithm="sha256").hexdigest()


def confirmacion_pendiente(entrada, firma, estimaciones, lote=()):
    if not estimaciones:
        return None
    estimacion = combinar_estimaciones(*estimaciones) if lote else estimaciones[0]
    nivel = categoria(estimacion)
    if nivel < Categoria.PESADA:
        return None
    esperada = firmar_entrada(entrada, lote)
    if constant_time_compare(firma or "", esperada):
        return None
    return {
        "firma": esperada,
        "mensaje": (MENSAJES_ESPERA_LOTE if lote else MENSAJES_ESPERA)[nivel],
        "tiempo": texto_intervalo(*intervalo_segundos(estimacion)),
    }
