"""Valores de máquina para lectura; los datos matemáticos nunca se modifican."""

from decimal import Decimal
from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def numero_raices(valor, tipo=""):
    """Decimal llano del valor almacenado (sin notación científica).

    `tipo` agrupa magnitudes comparables (x, f, error…): en el navegador, las protecciones contra
    valores distintos que parecen iguales solo comparan números del mismo tipo y grupo.
    """
    completo = repr(float(valor))
    texto = format(Decimal(completo), "f")
    if tipo:
        return format_html('<span data-raices-numero="{}" data-raices-tipo="{}" title="Valor almacenado: {}">{}</span>',
                           completo, tipo, texto, texto)
    return format_html('<span data-raices-numero="{}" title="Valor almacenado: {}">{}</span>', completo, texto, texto)
