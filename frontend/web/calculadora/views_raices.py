"""Coordinación HTTP de los métodos de raíces: formulario → backend → datos y presentación."""

import math

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_POST
from backend.biseccion import biseccion
from backend.regla_falsa import regla_falsa
from backend.newton_raphson import newton_raphson
from backend.resultados_raices import ClasificacionRaices as Clasificacion, evidencia_muestreo
from .forms_raices import BiseccionForm, RaicesForm, ReglaFalsaForm, NewtonRaphsonForm
from .servicios_raices import muestrear, verificacion_inicial
from .teclados import perfiles_para


def _datos_raices(nombre, form, resultado):
    datos = {"metodo": nombre, "resultado": resultado, "grafica_url": "grafica/",
             "clasificacion": resultado["clasificacion"] if resultado else
             Clasificacion.ENTRADA_INVALIDA if form.is_bound else None}
    if resultado:
        datos.update(funcion=form.funcion_real.texto, clave=form.funcion_real.clave)
    return datos


def _resolver(request, formulario, metodo, nombre):
    form = formulario(request.POST if request.method == "POST" else None)
    resultado = verificacion = None
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            resultado = metodo(form.funcion_real, d["a"], d["b"], d["precision"], d["max_iteraciones"])
        except ValueError as error:
            form.add_error(None, str(error))
    datos = _datos_raices(nombre, form, resultado)
    if resultado:
        d = form.cleaned_data
        datos.update(inicial_a=d["a"], inicial_b=d["b"])
        if resultado["residuo"] is not None:
            verificacion = verificacion_inicial(resultado["inicial"])
    return render(request, f"calculadora/modules/{nombre}/index.html", {
        "form": form, "resultado": resultado, "datos_raices": datos,
        "verificacion": verificacion, "perfiles_teclado": perfiles_para("funcion-real"),
    })


@require_http_methods(["GET", "POST"])
def resolver_biseccion(request):
    return _resolver(request, BiseccionForm, biseccion, "biseccion")


@require_http_methods(["GET", "POST"])
def resolver_regla_falsa(request):
    return _resolver(request, ReglaFalsaForm, regla_falsa, "regla_falsa")


@require_POST
def explorar_funcion(request):
    """Muestras de la curva para la gráfica; no ejecuta ningún método."""
    form = RaicesForm(request.POST, explorar=True)
    if not form.is_valid():
        errores = [str(mensaje) for mensajes in form.errors.values() for mensaje in mensajes]
        return JsonResponse({"error": " ".join(errores), "clasificacion": Clasificacion.ENTRADA_INVALIDA}, status=400)
    try:
        puntos = muestrear(form.funcion_real, form.cleaned_data["a"], form.cleaned_data["b"])
    except ValueError as error:
        return JsonResponse({"error": str(error), "clasificacion": Clasificacion.ENTRADA_INVALIDA}, status=400)
    return JsonResponse({**puntos, **evidencia_muestreo(puntos["y"])})


@require_http_methods(["GET", "POST"])
def resolver_newton_raphson(request):
    form = NewtonRaphsonForm(request.POST if request.method == "POST" else None)
    resultado = None
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            resultado = newton_raphson(form.funcion_real, d["x0"],
                                       d["precision"], d["max_iteraciones"])
        except ValueError as error:
            form.add_error(None, str(error))
    datos = _datos_raices("newton_raphson", form, resultado)
    if resultado:
        x0 = form.cleaned_data["x0"]
        ancho = max(2., abs(x0) * .25)
        a, b = x0 - ancho, x0 + ancho
        if not all(map(math.isfinite, (a, b, b - a))):
            a, b = -10., 10.
        datos.update({"inicial_a": a, "inicial_b": b})
    return render(request, "calculadora/modules/newton_raphson/index.html", {
        "form": form, "resultado": resultado, "datos_raices": datos,
        "perfiles_teclado": perfiles_para("funcion-real"),
    })
