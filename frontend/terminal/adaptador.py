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
    "article", "dd", "div", "dt", "footer", "h2", "h3", "h4", "h5", "h6", "header", "li", "p", "section", "summary",
})
_VACIOS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"})
_OMITIDOS = frozenset({"button", "script", "style", "svg", "form", "select", "label", "output", "template", "noscript"})
_OMITIR_IDS = frozenset({"raices-reproductor", "iteracion-lectura", "lectura-titulo", "raices-grafica"})
_TITULOS_AVISO = frozenset({"Método no aplicable", "Cálculo sin convergencia", "Aproximación sin convergencia"})


class Linea(str):
    """Texto de resultado con una función visual, compatible con el historial previo."""

    ESTILOS = frozenset({
        "texto", "titulo", "seccion", "paso", "nota", "formula", "resultado", "valor", "exito", "aviso",
    })

    def __new__(cls, texto, estilo="texto"):
        linea = super().__new__(cls, texto)
        linea.estilo = estilo if estilo in cls.ESTILOS else "texto"
        return linea

    @classmethod
    def legada(cls, texto):
        """Recupera los encabezados reconocibles de los registros sin formato."""
        if texto == "Resultado":
            return cls(texto, "resultado")
        if texto == "Ver procedimiento":
            return cls("Procedimiento", "seccion")
        if texto in {"Procedimiento detallado", "Cómo se obtuvo", "Verificación"}:
            return cls(texto, "seccion")
        if texto in _TITULOS_AVISO:
            return cls(texto, "aviso")
        if texto == "Raíz aproximada":
            return cls(texto, "exito")
        if texto.startswith("Etapa "):
            return cls(texto, "paso")
        return cls(texto)


@dataclass(frozen=True)
class Tabla:
    titulo: str
    columnas: tuple[str, ...]
    filas: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class _Elemento:
    tag: str
    oculto: bool
    estilo: str = "texto"
    tono: str = ""
    final: bool = False
    inicia_final: bool = False


def _estilo(tag, clases, final, tono):
    if tag == "h2":
        return tono or "titulo"
    if tag == "h3":
        if not final:
            return "seccion"
        return "aviso" if tono == "aviso" else "resultado"
    if tag in {"h4", "h5", "h6", "dt"}:
        return "paso"
    if "raices-raiz" in clases or "raices-estado" in clases:
        if tono == "aviso":
            return "aviso"
        return "valor" if "raices-raiz" in clases else "nota"
    if clases & {"section-kicker", "muted", "field-help", "procedure-note", "disclosure-detail"}:
        return "nota"
    if clases & {"classification-value", "base-results-origin", "base-result", "conjuntos-respuesta"}:
        return tono or "valor"
    if clases & {"expansion-line", "matrix-equation", "matrix-expression", "equations", "raices-comprobacion"}:
        return "formula"
    return "texto"


class ProcedimientoHTML(HTMLParser):
    """Lee el mismo procedimiento que recibe el navegador y conserva sus celdas."""

    def __init__(self, id_resultado="resultado", *, advertencia=False):
        super().__init__(convert_charrefs=True)
        self.id_resultado = id_resultado
        self.bloques = []
        self._activa = False
        self._pila = []
        self._texto = []
        self._estilo_linea = "texto"
        self._inicio_procedimiento = None
        self._inicio_resultado = None
        self._tabla = None
        self._titulo_tabla = ""
        self._caption = None
        self._celda = None
        self._encabezado = False
        self._indice_sub = 0
        self._advertencia = advertencia

    def _linea(self):
        linea = re.sub(r"\s+", " ", "".join(self._texto)).strip()
        if linea:
            estilo = self._estilo_linea
            if linea in _TITULOS_AVISO:
                estilo = "aviso"
            if linea == "Ver procedimiento" and estilo == "seccion":
                linea = "Procedimiento"
            if estilo != "nota" or linea not in {"Conversión", "Procedimiento y resultado"}:
                self.bloques.append(Linea(linea, estilo))
        self._texto.clear()

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if not self._activa:
            self._activa = self.id_resultado in (attr.get("id"), attr.get("aria-labelledby"))
            if not self._activa:
                return
        clase = set(attr.get("class", "").split())
        padre = self._pila[-1] if self._pila else _Elemento("", False)
        oculto = (
            tag in _OMITIDOS or ("sr-only" in clase and tag != "caption") or "hidden" in attr
            or attr.get("id") in _OMITIR_IDS or "raices-lienzo" in clase
            or padre.oculto
        )
        tono = padre.tono
        if attr.get("data-tono") == "aviso" or (self._advertencia and "raices-cabecera" in clase):
            tono = "aviso"
        elif attr.get("data-tono") == "exito":
            tono = "exito"
        inicia_final = "panel-final" in clase
        final = padre.final or inicia_final
        if final and self._advertencia:
            tono = "aviso"
        estilo = _estilo(tag, clase, final, tono)
        if estilo == "texto" and tag not in _BLOQUES:
            estilo = padre.estilo
        if tag not in _VACIOS:
            self._pila.append(_Elemento(tag, oculto, estilo, tono, final, inicia_final))
        if oculto:
            return
        if tag in {"sub", "sup"}:
            self._indice_sub = -1 if tag == "sub" else 1
        if tag == "table" and self._tabla is None:
            self._linea()
            self._tabla = ([], [])
            self._titulo_tabla = attr.get("aria-label", "")
        elif self._tabla is not None:
            if tag == "caption":
                self._caption = []
            elif tag == "tr":
                self._fila = []
                self._encabezado = True
            elif tag in {"td", "th"}:
                self._celda = []
                self._encabezado &= tag == "th" and attr.get("scope") != "row"
        elif tag in _BLOQUES or tag == "br":
            self._linea()
        if self._inicio_procedimiento is None and "disclosure-procedure" in clase:
            self._inicio_procedimiento = len(self.bloques)
        if inicia_final:
            self._inicio_resultado = len(self.bloques)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VACIOS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self._pila:
            return
        if self._pila[-1].tag != tag:
            return
        elemento = self._pila.pop()
        if not elemento.oculto:
            if tag in {"sub", "sup"}:
                self._indice_sub = 0
            if self._tabla is not None:
                columnas, filas = self._tabla
                if tag in {"td", "th"} and self._celda is not None:
                    self._fila.append(" ".join("".join(self._celda).split()))
                    self._celda = None
                elif tag == "tr" and self._fila:
                    if self._encabezado and not filas and not columnas:
                        columnas.extend(self._fila)
                    else:
                        filas.append(tuple(self._fila))
                elif tag == "caption" and self._caption is not None:
                    if not self._titulo_tabla:
                        self._titulo_tabla = " ".join("".join(self._caption).split())
                    self._caption = None
                elif tag == "table":
                    if filas:
                        self.bloques.append(Tabla(self._titulo_tabla, tuple(columnas), tuple(filas)))
                    self._tabla = None
            elif tag in _BLOQUES:
                self._linea()
            if elemento.inicia_final and self._inicio_procedimiento is not None:
                # Presenta la respuesta antes del desarrollo, conservando el orden interno de ambos.
                inicio = self._inicio_procedimiento
                corte = self._inicio_resultado
                self.bloques[inicio:] = self.bloques[corte:] + self.bloques[inicio:corte]
                self._inicio_procedimiento = None
        if not self._pila:
            self._linea()
            self._activa = False

    def handle_data(self, data):
        if not self._pila or self._pila[-1].oculto:
            return
        if self._indice_sub:
            digitos = "₀₁₂₃₄₅₆₇₈₉" if self._indice_sub < 0 else "⁰¹²³⁴⁵⁶⁷⁸⁹"
            data = data.translate(str.maketrans("0123456789", digitos))
        if self._celda is not None:
            self._celda.append(data)
        elif self._caption is not None:
            self._caption.append(data)
        elif self._tabla is None:
            if not data.strip() and not self._texto:
                return
            if not self._texto:
                self._estilo_linea = self._pila[-1].estilo
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
    resultado = respuesta.context_data.get("resultado")
    advertencia = isinstance(resultado, dict) and (
        resultado.get("clasificacion") in ("no_aplicable", "sin_convergencia")
        or resultado.get("aplicable") is False or resultado.get("invertible") is False
        and "explicacion" in resultado
    )
    parser = ProcedimientoHTML(id_resultado, advertencia=advertencia)
    parser.feed(respuesta.rendered_content)
    parser.close()
    return tuple(parser.bloques)
