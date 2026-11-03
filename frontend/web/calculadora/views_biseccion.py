"""Coordinación HTTP: formulario → backend → datos y presentación."""

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_POST
from backend.biseccion import biseccion
from .forms_biseccion import BiseccionForm
from .servicios_biseccion import muestrear, verificacion_biseccion
from .teclados import perfiles_para


@require_http_methods(["GET", "POST"])
def resolver_biseccion(request):
    form = BiseccionForm(request.POST if request.method == "POST" else None)
    resultado = None
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            resultado = biseccion(form.funcion_real, d["a"], d["b"], d["precision"], d["max_iteraciones"])
        except ValueError as error:
            form.add_error(None, str(error))
    datos = {"resultado": resultado, "grafica_url": "grafica/"}
    if resultado:
        datos.update({"funcion": form.cleaned_data["funcion"], "clave": form.funcion_real.clave,
                      "inicial_a": form.cleaned_data["a"], "inicial_b": form.cleaned_data["b"]})
    verificacion = verificacion_biseccion(form.funcion_real, form.cleaned_data["a"], form.cleaned_data["b"], resultado) if resultado else None
    return render(request, "calculadora/modules/biseccion/index.html", {
        "form": form, "resultado": resultado, "datos_biseccion": datos,
        "verificacion": verificacion, "perfiles_teclado": perfiles_para("funcion-real"),
    })


@require_POST
def explorar_biseccion(request):
    form = BiseccionForm(request.POST, explorar=True)
    if not form.is_valid():
        errores = [str(mensaje) for mensajes in form.errors.values() for mensaje in mensajes]
        return JsonResponse({"error": " ".join(errores)}, status=400)
    try:
        puntos = muestrear(form.funcion_real, form.cleaned_data["a"], form.cleaned_data["b"])
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse(puntos)
