"""Preguntas, previsualización y recorrido de los métodos de raíces."""

from math import isfinite
import re

from backend.derivacion_real import DerivadaReal
from backend.funciones_reales import FuncionReal
from frontend.web.calculadora.forms_raices import BiseccionForm, NewtonRaphsonForm, ReglaFalsaForm, SecanteForm
from frontend.web.calculadora.servicios_raices import muestrear
from frontend.web.calculadora.views_raices import _vista_abierta

from .dialogos import campo
from .graficas import Curva, PasoGrafico


_FORMULARIOS = {
    "biseccion": BiseccionForm,
    "regla-falsa": ReglaFalsaForm,
    "newton-raphson": NewtonRaphsonForm,
    "secante": SecanteForm,
}


def _dialogo(formulario):
    def preguntas(datos):
        form = formulario()
        puntos = tuple(n for n in form.fields if n in {"a", "b", "x0", "x1"})
        return (
            campo(form, "funcion", ayuda="Ejemplos: x^2 - 2, 2x + 1 o sin(x)."),
            *(campo(form, n) for n in puntos),
            campo(form, "precision"),
            campo(form, "max_iteraciones"),
        )
    return preguntas


DIALOGOS_RAICES = {nombre: _dialogo(form) for nombre, form in _FORMULARIOS.items()}
_CAMPOS_VISTA = frozenset({"funcion", "a", "b", "x0", "x1"})


def preparar_raices(datos, decimal):
    if decimal == ",":
        return {n: re.sub(r"(?<=[0-9]),(?=[0-9])", ".", v) for n, v in datos.items()}
    return datos


def _punto(datos, nombre):
    crudo = datos.get(nombre)
    if not crudo:
        return None
    try:
        valor = float(crudo)
    except ValueError as error:
        raise ValueError(f"{nombre} debe ser un número real.") from error
    if not isfinite(valor):
        raise ValueError(f"{nombre} debe ser finito.")
    return valor


def _paso(herramienta, fila):
    if herramienta == "biseccion":
        a, b, c = (fila[k] for k in ("a", "b", "c"))
        return PasoGrafico(f"a = {a:.6g} · b = {b:.6g} · c = {c:.6g}", ((a, 0.), (b, 0.), (c, fila["fc"])))
    if herramienta == "regla-falsa":
        a, b, x = (fila[k] for k in ("a", "b", "xr"))
        return PasoGrafico(f"a = {a:.6g} · b = {b:.6g} · xᵣ = {x:.6g}",
                           ((a, fila["fa"]), (b, fila["fb"]), (x, 0.)), True)
    x = fila["siguiente"]
    if herramienta == "newton-raphson":
        puntos = ((fila["xn"], fila["fxn"]), (x, 0.))
    else:
        puntos = ((fila["anterior"], fila["fanterior"]), (fila["actual"], fila["factual"]), (x, 0.))
    return PasoGrafico(f"x siguiente = {x:.6g}", puntos, True)


def curva(herramienta, datos, resultado=None):
    texto = datos.get("funcion", "").strip()
    if not texto:
        return None
    funcion = FuncionReal(texto)
    pasos = tuple(_paso(herramienta, f) for f in resultado.get("iteraciones", ())) if resultado else ()
    if herramienta in {"biseccion", "regla-falsa"}:
        a, b = _punto(datos, "a"), _punto(datos, "b")
        if a is None and b is None:
            a, b = -10., 10.
        elif a is None:
            a, _ = _vista_abierta(b)
        elif b is None:
            _, b = _vista_abierta(a)
    else:
        puntos = [_punto(datos, n) for n in ("x0", "x1")]
        puntos.extend(x for paso in pasos for x, _ in paso.puntos)
        a, b = _vista_abierta(*(tuple(p for p in puntos if p is not None) or (-7.5, 7.5)))
    muestras = muestrear(funcion, a, b)
    if all(y is None for y in muestras["y"]):
        raise ValueError("La función no tiene valores reales en la vista. Escribe puntos dentro de su dominio.")
    etiqueta = f"f(x) = {funcion.texto}"
    if herramienta == "newton-raphson":
        try:
            etiqueta += "   f′(x) = " + DerivadaReal(funcion).texto
        except (ValueError, ArithmeticError):
            pass
    return Curva(etiqueta, tuple(muestras["x"]), tuple(muestras["y"]), pasos)


def mensaje_previsualizacion(error, texto):
    if texto.rstrip().endswith(("+", "-", "−", "*", "/", "^")):
        return "Falta un término después del operador. Ejemplo: x^2 - 2."
    return f"{error} · Ejemplo: x^2 - 2."
