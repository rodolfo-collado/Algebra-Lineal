"""Preguntas, previsualización y recorrido de los métodos de raíces."""

from math import isfinite
import re

from backend.derivacion_real import DerivadaReal
from backend.funciones_reales import FuncionReal
from frontend.web.calculadora.forms_raices import BiseccionForm, NewtonRaphsonForm, ReglaFalsaForm, SecanteForm
from frontend.web.calculadora.servicios_raices import muestrear
from frontend.web.calculadora.views_raices import _vista_abierta

from .dialogos import campo
from .graficas import Curva, MarcaGrafica, PasoGrafico


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

        def validar_funcion(texto, decimal):
            texto = preparar_raices({"funcion": texto}, decimal)["funcion"]
            try:
                FuncionReal(texto)
            except ValueError as error:
                raise ValueError(mensaje_previsualizacion(error, texto)) from error

        def validar_b(valor, decimal):
            anterior = _punto(preparar_raices(datos, decimal), "a")
            if anterior is not None and valor <= anterior:
                raise ValueError("El extremo b debe ser mayor que a.")

        def validar_x1(valor, decimal):
            if valor == _punto(preparar_raices(datos, decimal), "x0"):
                raise ValueError("x₁ debe ser distinto de x₀: la secante necesita dos puntos.")

        def validar_precision(valor, _decimal):
            if valor is not None and valor <= 0:
                raise ValueError(f"La {form.magnitud} debe ser positiva.")

        validar_punto = {"b": validar_b, "x1": validar_x1}
        return (
            campo(form, "funcion", ayuda="Ejemplos: x^2 - 2, 2x + 1 o sin(x).", verificar=validar_funcion),
            *(campo(form, n, verificar=validar_punto.get(n)) for n in puntos),
            campo(form, "precision", verificar=validar_precision),
            campo(form, "max_iteraciones"),
        )
    return preguntas


DIALOGOS_RAICES = {nombre: _dialogo(form) for nombre, form in _FORMULARIOS.items()}
_CAMPOS_VISTA = frozenset({"funcion", "a", "b", "x0", "x1"})
_ETIQUETAS_PUNTO = {"a": "a", "b": "b", "x0": "x₀", "x1": "x₁"}
_CLAVES_RAIZ = {"biseccion": "c", "regla-falsa": "xr"}


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
    puntos = {nombre: x for nombre in _ETIQUETAS_PUNTO if (x := _punto(datos, nombre)) is not None}
    marcas = []
    for nombre, x in puntos.items():
        try:
            y = funcion(x)
        except (ValueError, ArithmeticError):
            y = None
        marcas.append(MarcaGrafica(_ETIQUETAS_PUNTO[nombre], x, y))
    if resultado and resultado["convergio"]:
        raiz = resultado.get(_CLAVES_RAIZ.get(herramienta, "x"))
        if raiz is not None:
            marcas.append(MarcaGrafica("Raíz", raiz, 0.))
    if "a" in puntos and "b" in puntos:
        a, b = puntos["a"], puntos["b"]
        if a >= b:
            raise ValueError("El extremo a debe ser menor que b.")
        if resultado is None and max(abs(a), abs(b)) <= 100 and (
            any(m.y is None for m in marcas) or (marcas[0].y < 0) == (marcas[1].y < 0)
        ):
            a, b = min(a, -10.), max(b, 10.)
        margen = (b - a) * .08
        if isfinite(a - margen) and isfinite(b + margen) and isfinite(b - a + 2 * margen):
            a, b = a - margen, b + margen
    else:
        abscisas = [*puntos.values(), *(x for paso in pasos for x, _ in paso.puntos)]
        if herramienta in _CLAVES_RAIZ and abscisas and abs(abscisas[0]) <= 100:
            a, b = min(-10., abscisas[0]), max(10., abscisas[0])
        else:
            a, b = _vista_abierta(*abscisas) if abscisas else (-10., 10.)
    muestras = muestrear(funcion, a, b)
    if all(y is None for y in muestras["y"]):
        raise ValueError("La función no tiene valores reales en la vista. Escribe puntos dentro de su dominio.")
    etiqueta = f"f(x) = {funcion.texto}"
    if herramienta == "newton-raphson":
        try:
            etiqueta += "   f′(x) = " + DerivadaReal(funcion).texto
        except (ValueError, ArithmeticError):
            pass
    return Curva(etiqueta, tuple(muestras["x"]), tuple(muestras["y"]), pasos, tuple(marcas))


def mensaje_previsualizacion(error, texto):
    if texto.rstrip().endswith(("+", "-", "−", "*", "/", "^")):
        return "Falta un término después del operador. Ejemplo: x^2 - 2."
    return f"{error} · Ejemplo: x^2 - 2."
