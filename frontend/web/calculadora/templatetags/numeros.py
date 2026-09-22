"""Mejora progresiva del bloque de resultados; nunca procesa formularios.

El HTML ya escapado por Django se conserva. Solo los nodos de texto y las
etiquetas accesibles reciben representaciones preparadas por Python. No se
interpreta markup de usuario, ni se sustituyen atributos técnicos o enlaces.
"""

import json
from html.parser import HTMLParser

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ..presentacion_numerica import PRECISIONES, representar_texto

register = template.Library()


def variantes(texto):
    valores = {str(p): representar_texto(texto, p) for p in PRECISIONES}
    if all(v.decimal == texto for v in valores.values()):
        return None
    return {
        "exacto": texto,
        "decimales": {p: v.decimal for p, v in valores.items()},
        "aproximados": [p for p, v in valores.items() if v.es_aproximado],
    }


class ResultadoHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.partes = []
        self.excluidos = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "textarea", "template"):
            self.excluidos.append(tag)
        original = self.get_starttag_text()
        accesibles = {}
        if not self.excluidos:
            for nombre, valor in attrs:
                if nombre in ("aria-label", "title") and valor:
                    datos = variantes(valor)
                    if datos:
                        accesibles[nombre] = datos
        if accesibles:
            original = original[:-1] + str(format_html(
                ' data-numeric-attributes="{}">', json.dumps(accesibles, ensure_ascii=False)
            ))
        self.partes.append(original)

    def handle_startendtag(self, tag, attrs):
        self.partes.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.excluidos and self.excluidos[-1] == tag:
            self.excluidos.pop()
        self.partes.append(f"</{tag}>")

    def handle_data(self, texto):
        datos = None if self.excluidos else variantes(texto)
        if datos:
            self.partes.append(str(format_html(
                '<span data-numeric="{}">{}</span>',
                json.dumps(datos, ensure_ascii=False), texto,
            )))
        else:
            self.partes.append(texto)

    def handle_entityref(self, name):
        self.partes.append(f"&{name};")

    def handle_charref(self, name):
        self.partes.append(f"&#{name};")

    def handle_comment(self, data):
        self.partes.append(f"<!--{data}-->")


@register.simple_block_tag
def numeric_results(content):
    """Una sola adaptación compartida para todos los resultados compatibles."""
    parser = ResultadoHTML()
    parser.feed(content)
    parser.close()
    # Solo preserva HTML de templates, ya autoescapado; los atributos nuevos
    # y el texto sustituido pasan por format_html, nunca por interpolación HTML.
    return mark_safe("".join(parser.partes))
