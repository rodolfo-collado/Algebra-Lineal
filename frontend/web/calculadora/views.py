"""Vistas HTTP de la interfaz web."""

from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from .catalogo import CATEGORIAS, MODULOS, SISTEMAS, contexto_navegacion, grupos_disponibles
from .conexiones import COMPARACIONES
from .forms import SistemaForm
from .guias import guias_para_resultado
from .servicios import resolver_entrada_web


@require_GET
def inicio(request):
    grupos = grupos_disponibles()
    ids_disponibles = {categoria.id for categoria, _ in grupos}
    proximos_por_categoria = tuple(
        (categoria, modulos)
        for categoria in CATEGORIAS
        if categoria.id not in ids_disponibles
        and (
            modulos := tuple(
                modulo
                for modulo in MODULOS
                if modulo.categoria == categoria and modulo.estado == "proximamente"
            )
        )
    )
    return render(request, "calculadora/pages/inicio.html", {
        **contexto_navegacion(),
        "categorias": CATEGORIAS,
        "grupos_modulos": grupos,
        "proximos_por_categoria": proximos_por_categoria,
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
    guias_contexto = ()
    guias_resultado = ()

    if request.method == "POST" and form.is_valid():
        try:
            resultado = resolver_entrada_web(
                form.cleaned_data["tipo_entrada"],
                form.cleaned_data["metodo"],
                texto=form.cleaned_data.get("sistema"),
                matriz_aumentada=form.cleaned_data.get("matriz_aumentada"),
            )
            guias = guias_para_resultado(
                metodo=form.cleaned_data["metodo"],
                clasificacion_clave=resultado["clasificacion_clave"],
                columnas_pivote=resultado["columnas_pivote"],
            )
            guias_contexto = guias[:1]
            guias_resultado = guias[1:]
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
            "guias_contexto": guias_contexto,
            "guias_resultado": guias_resultado,
        },
    )
