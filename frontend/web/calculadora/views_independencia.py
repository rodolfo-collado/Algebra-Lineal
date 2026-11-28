"""Flujo de análisis y ejemplos editables de independencia lineal."""

from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

from backend.independencia_lineal import analizar_independencia_lineal

from .forms_independencia import IndependenciaForm
from .servicios_independencia import presentar_independencia
from .teclados import perfiles_para

EJEMPLOS = {
    "independiente": ("Independientes con fracciones", (("1/3", "1", "0"), ("1", "0", "1"))),
    "dependiente": ("Dependientes en ℝ³", ((1, 2, 0), (0, 1, 3), (2, 5, 3))),
    "varias-libres": ("Más vectores que dimensiones", ((1, 0), (0, 1), (1, 1), (0, 0))),
}


def _ejemplo(clave):
    if clave not in EJEMPLOS:
        return {}
    _, vectores = EJEMPLOS[clave]
    return {
        "dimension": len(vectores[0]),
        "cantidad": len(vectores),
        **{
            f"celda_v{indice}_{fila}_0": valor
            for indice, vector in enumerate(vectores, 1)
            for fila, valor in enumerate(vector)
        },
    }


@require_http_methods(["GET", "POST"])
def independencia_lineal(request):
    resolucion = resultado = None
    if request.method == "POST":
        form = IndependenciaForm(request.POST, ajustar="ajustar" in request.POST)
        if form.is_valid():
            if form.ajustar:
                form = IndependenciaForm(initial=form.iniciales())
            else:
                try:
                    resolucion = analizar_independencia_lineal(form.cleaned_data["vectores"])
                    resultado = presentar_independencia(resolucion)
                except ValueError as error:
                    form.add_error(None, str(error))
    else:
        form = IndependenciaForm(initial=_ejemplo(request.GET.get("ejemplo")))

    return TemplateResponse(request, "calculadora/modules/independencia/index.html", {
        "form": form,
        "resolucion": resolucion,
        "resultado": resultado,
        "ejemplos": [(clave, rotulo) for clave, (rotulo, _) in EJEMPLOS.items()],
        "perfiles_teclado": perfiles_para("numerico"),
    })
