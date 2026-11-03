"""Flujo HTTP del editor y la única evaluación de relaciones."""

from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from backend.conjuntos.parser import analizar_relacion
from .forms_conjuntos import ConjuntosForm, inicial_editor
from .servicios_conjuntos import relacion_web
from .teclados import perfiles_para


@require_http_methods(["GET", "POST"])
def relaciones_conjuntos(request):
    form = ConjuntosForm(request.POST if request.method == "POST" else None, initial=inicial_editor())
    resultado = None
    if request.method == "POST" and form.is_valid():
        try:
            if form.accion == "calcular" and "eliminar" not in request.POST:
                resultado = relacion_web(form.expresion, form.entorno, presupuesto=form.presupuesto)
            elif form.accion == "construir":
                analizar_relacion(form.expresion, presupuesto=form.presupuesto)
        except ValueError as error:
            form.add_error("expresion", str(error))
        if not form.errors:
            inicial = inicial_editor(form.filas, form.expresion,
                                     definicion="" if form.accion == "agregar" else form.cleaned_data.get("definicion", ""),
                                     **{n: form.cleaned_data.get(n, "") for n in ("izquierdo", "operador", "derecho")})
            form = ConjuntosForm(initial=inicial)
    return render(request, "calculadora/modules/conjuntos/index.html", {
        "form": form, "resultado": resultado,
        "perfiles_teclado": perfiles_para("literal-conjuntos", "relacion-conjuntos"),
    })
