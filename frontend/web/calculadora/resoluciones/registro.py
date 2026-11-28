"""Qué guarda cada herramienta en el cuaderno y cómo se vuelve a abrir.

El middleware es genérico; las particularidades viven aquí, una entrada por ruta Django.
Para incorporar una herramienta basta con añadir su ``Adaptador``:

- ``claves``: claves del contexto de la plantilla que forman el resultado. Deben ser datos
  (lo que entrega su servicio), codificables por ``contrato.codificar``.
- ``nombre``: el método, cuando una herramienta reúne varios en rutas distintas.
- ``principal``: la clave cuya presencia indica que hubo un resultado.
- ``esquema``: súbelo cuando cambie la forma de esas claves; los documentos anteriores se
  abrirán con sus datos y sin resultado, ofreciendo calcular de nuevo.
- ``ignorar``: campos de presentación que no cambian la matemática (no cuentan en la huella).
- ``formulario(form_de_la_vista, datos, resultado)``: el formulario de la página reabierta.
  Por defecto, el mismo tipo de formulario ligado a los datos guardados.
- ``preparar(contexto)``: lo que se guarda de cada clave cuando no basta con copiarla (quitar
  objetos que no son datos, como los nodos del AST de Operaciones).
- ``errores_parciales``: un resultado se guarda aunque el formulario marque errores en
  algunas filas (expresiones múltiples).
- ``por_consulta``: la vista sabe rellenar su editor desde la consulta GET (Conjuntos).
- ``resumen(contexto)``: una línea con la respuesta, para el cuaderno.
- ``grafica(contexto)``: muestras que la página pide aparte y la exportación necesitará.

``docs/resoluciones.md`` explica cómo registrar una herramienta nueva.
"""

from dataclasses import dataclass, field
from typing import Callable

from ..servicios_raices import muestrear


def _ligado(form, datos, resultado):
    return type(form)(datos)


def _numero(valor):
    """Lectura breve de un float para el resumen; el documento guarda todas sus cifras."""
    return f"{valor:.10g}" if isinstance(valor, float) else str(valor)


@dataclass(frozen=True)
class Adaptador:
    claves: tuple[str, ...]
    # Nombre del método cuando la herramienta reúne varios (Métodos cerrados → Bisección).
    nombre: str | None = None
    principal: str = "resultado"
    esquema: int = 1
    ignorar: frozenset = frozenset()
    formulario: Callable = _ligado
    por_consulta: bool = False
    resumen: Callable = field(default=lambda contexto: "")
    grafica: Callable | None = None
    preparar: Callable | None = None
    errores_parciales: bool = False

    def es_valida(self, contexto):
        """Hubo resultado, no espera una confirmación de costo y el formulario no tiene errores."""
        form = contexto.get("form")
        if not contexto.get(self.principal) or contexto.get("confirmacion"):
            return False
        return self.errores_parciales or not (form and form.errors)

    def datos(self, contexto):
        """Las claves del resultado tal como se guardan."""
        if self.preparar is not None:
            return self.preparar(contexto)
        return {clave: contexto.get(clave) for clave in self.claves}

    def resumir(self, contexto):
        try:
            return str(self.resumen(contexto) or "")[:160]
        except (KeyError, TypeError, AttributeError, IndexError, ValueError):
            return ""

    def graficar(self, contexto):
        if self.grafica is None:
            return None
        try:
            return self.grafica(contexto)
        except (KeyError, TypeError, AttributeError, ValueError, ArithmeticError):
            return None


# ---- Particularidades ----

def _resumen_raiz(clave):
    def resumir(contexto):
        r = contexto["resultado"]
        if r.get("convergio"):
            return f"x ≈ {_numero(r[clave])}"
        return r.get("mensaje", "")
    return resumir


def _grafica_raices(contexto):
    """La curva que la página dibuja al abrir: 801 muestras de f en el encuadre inicial."""
    datos, form = contexto["datos_raices"], contexto["form"]
    a, b = datos["inicial_a"], datos["inicial_b"]
    return {"tipo": "funcion", "funcion": datos["funcion"], "intervalo": [a, b], **muestrear(form.funcion_real, a, b)}


def _determinante(form, datos, resultado):
    # El método ya estaba elegido cuando se calculó: la página reabierta lo muestra así.
    return type(form)(datos, elegir=True)


def _conjuntos(form, datos, resultado):
    """La vista ya armó el editor desde la consulta; solo falta el punto de la recta."""
    form.initial["punto"] = datos.get("punto", "")
    return form


def _resumen_bases(contexto):
    r = contexto["resultado"]
    return f"{r['origen']} = " + " = ".join(fila["destino"] for fila in r["resultados"])


def _preparar_expresiones(contexto):
    """Cada fila conserva su expresión, su resultado estructurado o su error; el nodo del AST no."""
    return {
        "resultados": [{clave: valor for clave, valor in fila.items() if clave != "nodo"}
                       for fila in contexto["resultados"]],
        "resultado": contexto.get("resultado"), "hay_resultados": contexto.get("hay_resultados"),
    }


def _expresiones(form, datos, resultado):
    """Los errores de evaluación de cada fila los añade la vista al calcular: se reponen igual."""
    form = type(form)(datos)
    form.full_clean()
    for fila in resultado.get("resultados") or ():
        if fila.get("error") and fila["indice"] < len(form.expresiones):
            campo = form.expresiones[fila["indice"]].name
            if fila["error"] not in form.errors.get(campo, ()):
                form.add_error(campo, fila["error"])
    return form


def _resumen_expresiones(contexto):
    filas = contexto["resultados"]
    validas = [f for f in filas if f["resultado"] is not None]
    if len(filas) == 1:
        return validas[0]["resultado"].get("igualdad") or validas[0]["expresion"]
    errores = len(filas) - len(validas)
    texto = f"{len(validas)} de {len(filas)} expresiones resueltas"
    return texto if errores else f"{len(filas)} expresiones resueltas"


def _raiz(nombre, extra, aproximacion):
    """Los cuatro métodos de raíces comparten resultado, datos de la gráfica y muestras."""
    return Adaptador(("resultado", "datos_raices", extra), nombre=nombre,
                     resumen=_resumen_raiz(aproximacion), grafica=_grafica_raices)


ADAPTADORES = {
    # Una o varias expresiones; las filas con error se guardan con su mensaje, como se ven.
    "operaciones-matrices": Adaptador(
        ("resultados", "resultado", "hay_resultados"), principal="hay_resultados", errores_parciales=True,
        preparar=_preparar_expresiones, formulario=_expresiones, resumen=_resumen_expresiones),
    "independencia-lineal": Adaptador(
        ("resultado",), resumen=lambda c: (
            f"{'Linealmente independientes' if c['resultado']['es_independiente'] else 'Linealmente dependientes'}"
            f" · rango {c['resultado']['rango']}")),
    "reduccion-filas": Adaptador(
        ("resultados", "resultado", "comparando", "mostrar", "titulo_resultado", "matrix_values", "opciones_abiertas",
         "exploraciones"),
        ignorar=frozenset({"mostrar"}),
        resumen=lambda c: c["resultado"]["clasificacion"]),
    "ecuaciones-matriciales": Adaptador(
        ("resultado",), resumen=lambda c: c["resultado"]["enunciado"].rstrip(".")),
    "matriz-inversa": Adaptador(
        ("resultado",), resumen=lambda c: (
            f"{'A es invertible' if c['resultado']['invertible'] else 'A no es invertible'}"
            f" · det(A) = {c['resultado']['determinante']}")),
    "determinantes": Adaptador(
        ("resultado",), formulario=_determinante,
        resumen=lambda c: f"{c['resultado'].get('nombre_determinante', 'det(A)')} = "
                          f"{c['resultado']['determinante']}"),
    "biseccion": _raiz("Bisección", "verificacion", "c"),
    "regla-falsa": _raiz("Regla falsa", "verificacion", "c"),
    "newton-raphson": _raiz("Newton-Raphson", "funcion_natural", "x"),
    "secante": _raiz("Secante", "funcion_natural", "x"),
    "metodos-iterativos": Adaptador(
        ("iterativos",), principal="iterativos", resumen=lambda c: c["iterativos"]["titulo"]),
    "relaciones-conjuntos": Adaptador(
        ("resultado", "diagrama", "regiones_aplicadas"), formulario=_conjuntos, por_consulta=True,
        resumen=lambda c: f"{c['resultado']['expresion']} → {c['resultado']['respuesta']}"),
    "cardinalidades-conjuntos": Adaptador(
        ("resultado",), resumen=lambda c: f"|{c['resultado']['expresion']}| = {c['resultado']['resultado']}"),
    "conversion-bases": Adaptador(
        ("resultado", "perfil_entrada", "base_entrada_activa"), resumen=_resumen_bases),
    "conversion-romanos": Adaptador(
        ("resultado",), resumen=lambda c: f"{c['resultado']['origen']} = {c['resultado']['resultado']}"),
}
# Rutas antiguas que siguen procesando POST con la vista de una herramienta registrada.
ALIAS = {"sistemas": "reduccion-filas"}


def ruta_canonica(resolver_match):
    nombre = getattr(resolver_match, "url_name", None)
    return ALIAS.get(nombre, nombre)


def adaptador(resolver_match):
    """El adaptador de la ruta resuelta, o None si la herramienta no guarda en el cuaderno."""
    if resolver_match is None or resolver_match.namespace != "calculadora":
        return None
    return ADAPTADORES.get(ruta_canonica(resolver_match))
