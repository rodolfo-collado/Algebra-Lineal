"""Clasificaciones que comparten los métodos de raíces y la exploración."""

from enum import StrEnum


class ClasificacionRaices(StrEnum):
    ENTRADA_INVALIDA = "entrada_invalida"
    NO_APLICABLE = "no_aplicable"
    RAIZ_APROXIMADA = "raiz_aproximada"
    SIN_CONVERGENCIA = "sin_convergencia"
    SIN_RAICES_DEMOSTRADO = "sin_raices_demostrado"
    EXPLORACION_NO_CONCLUYENTE = "exploracion_no_concluyente"
    INDICIOS_NUMERICOS = "indicios_numericos"


def evidencia_muestreo(ordenadas):
    """Contar indicios numéricos a partir de muestras con sus huecos preservados."""
    ceros = ordenadas.count(0)
    cambios = sum(a is not None and b is not None and a != 0 and b != 0 and (a < 0) != (b < 0)
                  for a, b in zip(ordenadas, ordenadas[1:]))
    clasificacion = (ClasificacionRaices.INDICIOS_NUMERICOS if ceros or cambios
                     else ClasificacionRaices.EXPLORACION_NO_CONCLUYENTE)
    return {"clasificacion": clasificacion,
            "evidencia": {"muestras_validas": len(ordenadas) - ordenadas.count(None),
                          "ceros_calculados": ceros, "cambios_de_signo": cambios}}
