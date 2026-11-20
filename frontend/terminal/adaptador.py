"""Adaptación local de los formularios y procedimientos compartidos con la web."""

from dataclasses import dataclass
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import sys

from django.http import HttpRequest, QueryDict
from django.urls import resolve, reverse


_BACKEND = Path(__file__).resolve().parents[2] / "backend"
_BLOQUES = frozenset({
    "article", "div", "footer", "h2", "h3", "h4", "h5", "header", "li", "p", "section", "summary",
})
_VACIOS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"})
_OMITIDOS = frozenset({"button", "script", "style", "svg", "form", "select", "label", "output", "template", "noscript"})
_OMITIR_IDS = frozenset({"raices-reproductor", "iteracion-lectura", "lectura-titulo", "raices-grafica"})


@dataclass(frozen=True)
class Tabla:
    titulo: str
    columnas: tuple[str, ...]
    filas: tuple[tuple[str, ...], ...]


class ProcedimientoHTML(HTMLParser):
    """Lee el mismo procedimiento que recibe el navegador y conserva sus celdas."""

    def __init__(self, id_resultado="resultado"):
        super().__init__(convert_charrefs=True)
        self.id_resultado = id_resultado
        self.bloques = []
        self._activa = False
        self._pila = []
        self._texto = []
        self._tabla = None
        self._celda = None
        self._encabezado = False
        self._indice_sub = 0

    def _linea(self):
        linea = re.sub(r"\s+", " ", "".join(self._texto)).strip()
        if linea:
            self.bloques.append(linea)
        self._texto.clear()

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if not self._activa:
            self._activa = self.id_resultado in (attr.get("id"), attr.get("aria-labelledby"))
            if not self._activa:
                return
        clase = attr.get("class", "").split()
        oculto = (
            tag in _OMITIDOS or "sr-only" in clase or "hidden" in attr
            or attr.get("id") in _OMITIR_IDS or "raices-lienzo" in clase
            or (bool(self._pila) and self._pila[-1][1])
        )
        if tag not in _VACIOS:
            self._pila.append((tag, oculto))
        if oculto:
            return
        if tag in {"sub", "sup"}:
            self._indice_sub = -1 if tag == "sub" else 1
        if tag == "table" and self._tabla is None:
            self._linea()
            self._tabla = (attr.get("aria-label", ""), [], [])
        elif self._tabla is not None:
            if tag == "tr":
                self._fila = []
                self._encabezado = False
            elif tag in {"td", "th"}:
                self._celda = []
                self._encabezado |= tag == "th"
        elif tag in _BLOQUES or tag == "br":
            self._linea()

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VACIOS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self._pila:
            return
        if self._pila[-1][0] != tag:
            return
        _, oculto = self._pila.pop()
        if not oculto:
            if tag in {"sub", "sup"}:
                self._indice_sub = 0
            if self._tabla is not None:
                titulo, columnas, filas = self._tabla
                if tag in {"td", "th"} and self._celda is not None:
                    self._fila.append(" ".join("".join(self._celda).split()))
                    self._celda = None
                elif tag == "tr" and self._fila:
                    if self._encabezado and not filas and not columnas:
                        columnas.extend(self._fila)
                    else:
                        filas.append(tuple(self._fila))
                elif tag == "table":
                    if filas:
                        self.bloques.append(Tabla(titulo, tuple(columnas), tuple(filas)))
                    self._tabla = None
            elif tag in _BLOQUES:
                self._linea()
        if not self._pila:
            self._linea()
            self._activa = False

    def handle_data(self, data):
        if not self._pila or self._pila[-1][1]:
            return
        if self._indice_sub:
            digitos = "₀₁₂₃₄₅₆₇₈₉" if self._indice_sub < 0 else "⁰¹²³⁴⁵⁶⁷⁸⁹"
            data = data.translate(str.maketrans("0123456789", digitos))
        if self._celda is not None:
            self._celda.append(data)
        elif self._tabla is None:
            self._texto.append(data)


def peticion(herramienta, datos=None, *, consulta=None):
    """Ejecuta una vista local con sus validaciones, sin abrir un servidor."""
    request = HttpRequest()
    request.path = request.path_info = reverse(f"calculadora:{herramienta}")
    request.resolver_match = ruta = resolve(request.path)
    request.method = "GET" if datos is None else "POST"
    request.GET = _consulta(consulta or {})
    request.POST = _consulta(datos or {})
    return ruta.func(request, *ruta.args, **ruta.kwargs)


def _consulta(datos):
    consulta = QueryDict(mutable=True)
    for nombre, valor in datos.items():
        valores = valor if isinstance(valor, (tuple, list)) else [valor]
        consulta.setlist(nombre, [str(v) for v in valores])
    return consulta


def ejecutar(herramienta, datos, depurar=False):
    """Devuelve el contexto y los archivos ejecutados durante esta operación."""
    if not depurar:
        return peticion(herramienta, datos), ()
    # Carga el enrutador antes de trazar para excluir los imports de arranque.
    reverse(f"calculadora:{herramienta}")
    archivos = {}

    def trazar(frame, evento, argumento):
        if evento == "call":
            archivo = frame.f_code.co_filename
            if archivo.startswith(str(_BACKEND) + os.sep):
                archivos[archivo] = None

    anterior = sys.getprofile()
    sys.setprofile(trazar)
    try:
        respuesta = peticion(herramienta, datos)
    finally:
        sys.setprofile(anterior)
    return respuesta, tuple(archivos)


def procedimiento(respuesta, id_resultado="resultado"):
    parser = ProcedimientoHTML(id_resultado)
    parser.feed(respuesta.rendered_content)
    parser.close()
    return tuple(parser.bloques)
