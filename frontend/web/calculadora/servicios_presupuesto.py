"""Formato visible del intervalo de espera, compartido por las confirmaciones."""

from backend.matrices import contar


def _duracion(segundos):
    if segundos < 90:
        return max(1, round(segundos)), "segundo"
    return round(segundos / 60), "minuto"


def texto_intervalo(bajo, alto):
    """«entre 1 y 11 segundos», «entre 13 segundos y 2 minutos»."""
    (desde, unidad_desde), (hasta, unidad_hasta) = _duracion(bajo), _duracion(alto)
    if unidad_desde == unidad_hasta:
        return f"entre {desde} y {contar(hasta, unidad_hasta)}"
    return f"entre {contar(desde, unidad_desde)} y {contar(hasta, unidad_hasta)}"
