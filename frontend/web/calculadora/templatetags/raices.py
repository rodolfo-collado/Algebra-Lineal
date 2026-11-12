"""Valores de máquina para lectura; los datos matemáticos nunca se modifican."""

from decimal import Decimal
from django import template
from django.utils.html import format_html
from backend.derivacion_real import legible

register = template.Library()


@register.filter
def numero_raices(valor):
    numero = float(valor)
    completo = repr(numero)
    texto = format(Decimal(completo), "f") if numero == 0 or 1e-16 <= abs(numero) < 1e12 else completo
    return format_html('<span data-raices-numero="{}" title="Valor almacenado: {}">{}</span>', completo, completo, texto)


@register.filter
def expresion_legible(texto):
    return legible(texto)
