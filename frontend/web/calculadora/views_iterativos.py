"""Vista de métodos iterativos para Ax = b."""

from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

from .forms_iterativos import SistemasIterativosForm
from .servicios_iterativos import iniciales_ejemplo, lista_ejemplos, resolver_iterativos_web
from .teclados import perfiles_para


@require_http_methods(["GET", "POST"])
def metodos_iterativos(request):
    if request.method == "POST":
        ajustar = "ajustar" in request.POST
        form = SistemasIterativosForm(request.POST, ajustar=ajustar)
    else:
        form = SistemasIterativosForm(initial=iniciales_ejemplo(request.GET.get("ejemplo")))

    resultado = None
    if request.method == "POST" and form.is_valid():
        if ajustar:
            form = SistemasIterativosForm(initial=form.iniciales())
        else:
            try:
                resultado = resolver_iterativos_web(form.cleaned_data["entrada"])
            except ValueError as error:
                form.add_error(None, str(error))

    return TemplateResponse(request, "calculadora/modules/iterativos/index.html", {
        "form": form, "iterativos": resultado, "perfiles_teclado": perfiles_para("numerico"),
        # Menú de edición (clic derecho en A o b), como los ejemplos de Conjuntos.
        "ejemplos": lista_ejemplos(), "ejemplos_detalle": "sustituye el sistema",
    })
