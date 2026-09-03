"""Vistas HTTP de la interfaz web."""

from django.shortcuts import render

from .forms import SistemaForm
from .servicios import resolver_entrada_web


def inicio(request):
    form = SistemaForm(request.POST or None)
    resultado = None

    if request.method == "POST" and form.is_valid():
        try:
            resultado = resolver_entrada_web(
                form.cleaned_data["tipo_entrada"],
                form.cleaned_data["metodo"],
                texto=form.cleaned_data.get("sistema"),
                matriz_aumentada=form.cleaned_data.get("matriz_aumentada"),
            )
        except ValueError as error:
            if form.cleaned_data.get("tipo_entrada") == "matriz":
                form.add_error(None, str(error))
            else:
                form.add_error("sistema", str(error))

    return render(
        request,
        "calculadora/index.html",
        {
            "form": form,
            "resultado": resultado,
            "matrix_values": form.valores_matriz_ingresados(),
        },
    )
