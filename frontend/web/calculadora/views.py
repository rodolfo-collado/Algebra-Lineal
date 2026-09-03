"""Vistas HTTP de la interfaz web."""

from django.shortcuts import render

from .forms import SistemaForm
from .servicios import resolver_sistema_web


def inicio(request):
    form = SistemaForm(request.POST or None)
    resultado = None

    if request.method == "POST" and form.is_valid():
        try:
            resultado = resolver_sistema_web(
                form.cleaned_data["sistema"], form.cleaned_data["metodo"]
            )
        except ValueError as error:
            form.add_error("sistema", str(error))

    return render(
        request,
        "calculadora/index.html",
        {"form": form, "resultado": resultado},
    )
