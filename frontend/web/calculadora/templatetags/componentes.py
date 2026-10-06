"""Etiquetas de plantilla de los componentes compartidos de la calculadora."""

from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_block_tag
def disclosure(content, titulo, id=None, clase="", nivel=3, abierto=False, detalle="", icono=""):
    """Bloque plegable nativo: {% disclosure titulo="Ver procedimiento" %}…{% enddisclosure %}.

    Renderiza details/summary reales, así que funciona sin JavaScript y con
    teclado. El título va dentro del summary como h3 (h4, h5 o h6 con nivel=4,
    5 o 6) para conservar la jerarquía de encabezados; `clase` añade clases al
    details, `detalle` un resumen secundario e `icono="opciones"` marca las
    opciones de configuración. El chevrón va siempre primero.
    """
    return render_to_string("calculadora/components/disclosure.html", {
        "contenido": content, "titulo": titulo, "id": id, "clase": clase,
        "nivel": nivel, "abierto": abierto, "detalle": detalle, "icono": icono,
    })
