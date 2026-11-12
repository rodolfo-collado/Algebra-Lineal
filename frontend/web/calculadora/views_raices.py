"""Coordinación HTTP de los métodos de raíces: formulario → backend → datos y presentación."""

import math

from django.http import HttpResponsePermanentRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from backend.biseccion import biseccion
from backend.regla_falsa import regla_falsa
from backend.newton_raphson import newton_raphson
from backend.secante import secante
from backend.derivacion_real import DerivadaReal, natural
from backend.resultados_raices import ClasificacionRaices as Clasificacion, evidencia_muestreo
from .forms_raices import BiseccionForm, RaicesForm, ReglaFalsaForm, NewtonRaphsonForm, SecanteForm
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
def explorar_funcion(request, derivar=False):
    """Muestras de la curva para la gráfica; no ejecuta ningún método.

    Con derivar (Newton), la misma respuesta añade f′(x) para verla mientras se escribe:
    una sola petición por cambio y el motor simbólico solo en el backend."""
    form = RaicesForm(request.POST, explorar=True)
    if not form.is_valid():
        errores = [str(mensaje) for mensajes in form.errors.values() for mensaje in mensajes]
        return JsonResponse({"error": " ".join(errores), "clasificacion": Clasificacion.ENTRADA_INVALIDA}, status=400)
    try:
        puntos = muestrear(form.funcion_real, form.cleaned_data["a"], form.cleaned_data["b"])
    except ValueError as error:
        return JsonResponse({"error": str(error), "clasificacion": Clasificacion.ENTRADA_INVALIDA}, status=400)
    respuesta = {**puntos, **evidencia_muestreo(puntos["y"])}
    if derivar:
        try:
            respuesta["derivada"] = DerivadaReal(form.funcion_real).texto
        except (ValueError, ArithmeticError):
            respuesta["derivada"] = None
    return JsonResponse(respuesta)


def _vista_abierta(*puntos):
    """Encuadre inicial de la gráfica alrededor de los puntos de partida de un método abierto."""
    lo, hi = min(puntos), max(puntos)
    ancho = max(2., max(abs(lo), abs(hi)) * .25, (hi - lo) / 4)
    a, b = lo - ancho, hi + ancho
    return (a, b) if all(map(math.isfinite, (a, b, b - a))) else (-10., 10.)


def _resolver_abierto(request, formulario, nombre, calcular, puntos):
    """Métodos abiertos: el mismo esqueleto que los cerrados, con puntos iniciales en vez de intervalo.

    Al cambiar de método llega ?funcion=…: la función escrita se conserva, nunca el resultado."""
    form = formulario(request.POST if request.method == "POST" else None,
                      initial={"funcion": request.GET.get("funcion", "")[:512]})
    resultado = None
    if request.method == "POST" and form.is_valid():
        try:
            resultado = calcular(form.funcion_real, form.cleaned_data)
        except ValueError as error:
            form.add_error(None, str(error))
    datos = _datos_raices(nombre, form, resultado)
    if resultado:
        a, b = _vista_abierta(*(form.cleaned_data[p] for p in puntos))
        datos.update(inicial_a=a, inicial_b=b)
    return render(request, f"calculadora/modules/{nombre}/index.html", {
        "form": form, "resultado": resultado, "datos_raices": datos,
        "funcion_natural": natural(form.funcion_real.arbol) if resultado else None,
        "perfiles_teclado": perfiles_para("funcion-real"),
    })


@require_http_methods(["GET", "POST"])
def resolver_newton_raphson(request):
    return _resolver_abierto(request, NewtonRaphsonForm, "newton_raphson", lambda f, d: newton_raphson(
        f, d["x0"], d["precision"], d["max_iteraciones"]), ("x0",))


@require_http_methods(["GET", "POST"])
def resolver_secante(request):
    return _resolver_abierto(request, SecanteForm, "secante", lambda f, d: secante(
        f, d["x0"], d["x1"], d["precision"], d["max_iteraciones"]), ("x0", "x1"))


def newton_raphson_ruta_antigua(request, grafica=False):
    """Newton-Raphson pasó a Métodos abiertos. GET usa 301 y conserva la consulta; POST usa 308
    para que el navegador reenvíe el mismo cuerpo, que el formulario entiende tal cual."""
    destino = reverse("calculadora:newton-raphson-grafica" if grafica else "calculadora:newton-raphson")
    if request.GET:
        destino = f"{destino}?{request.GET.urlencode()}"
    return HttpResponsePermanentRedirect(destino, preserve_request=request.method == "POST")
