"""Etiquetas de plantilla de los componentes compartidos de la calculadora."""

from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_block_tag
def disclosure(content, titulo, id=None, clase="", nivel=3, abierto=False, detalle=""):
    """Bloque plegable nativo: {% disclosure titulo="Ver procedimiento" %}…{% enddisclosure %}.

    Renderiza details/summary reales, así que funciona sin JavaScript y con
    teclado. El título va dentro del summary como h3 (o h4 con nivel=4) para
    conservar la jerarquía de encabezados; `clase` añade clases al details.
    """
    return render_to_string("calculadora/components/disclosure.html", {
        "contenido": content, "titulo": titulo, "id": id, "clase": clase,
        "nivel": nivel, "abierto": abierto, "detalle": detalle,
    })
