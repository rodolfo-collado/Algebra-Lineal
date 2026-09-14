"""Vistas HTTP de la interfaz web."""

from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from .catalogo import MODULOS, SISTEMAS, contexto_navegacion
from .conexiones import COMPARACIONES
from .forms import SistemaForm
from .servicios import resolver_entrada_web


@require_GET
def inicio(request):
    return render(request, "calculadora/pages/inicio.html", {
        **contexto_navegacion(),
        "proximos_modulos": tuple(m for m in MODULOS if m.estado == "proximamente"),
    })


@require_http_methods(["GET", "POST"])
def sistemas(request):
    datos = request.POST.copy() if request.method == "POST" else None
    if datos is not None and "metodo_alternativo" in datos:
        # Un solo valor canónico; ChoiceField valida también acciones manipuladas.
        datos["metodo"] = datos.get("metodo_alternativo")
    form = SistemaForm(datos)
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
        "calculadora/modules/sistemas/index.html",
        {
            **contexto_navegacion(SISTEMAS),
            "form": form,
            "resultado": resultado,
            "matrix_values": form.valores_matriz_ingresados(),
            "comparacion": COMPARACIONES.get(form.cleaned_data["metodo"])
            if resultado else None,
        },
    )
