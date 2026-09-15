"""Vistas HTTP de la interfaz web."""

from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from . import catalogo
from .forms import SistemaForm
from .guias import guias_para_resultado
from .herramientas_sistemas import HERRAMIENTAS as HERRAMIENTAS_SISTEMAS
from .servicios import resolver_entrada_web
from .teclados import TECLADO_MATRIZ, TECLADO_SISTEMA


@require_GET
def inicio(request):
    consulta = request.GET.get("q", "").strip()
    return render(request, "calculadora/pages/inicio.html", {
        "consulta": consulta,
        "resultados_busqueda": catalogo.buscar_herramientas(consulta) if consulta else None,
        "herramientas_disponibles": catalogo.herramientas_disponibles(),
    })


@require_http_methods(["GET", "POST"])
def sistemas(request, herramienta="sistemas"):
    """Una vista para todas las herramientas de sistemas; `herramienta` llega desde la URL."""
    # El registro decide qué herramientas existen: una ruta no registrada es 404.
    actual = catalogo.herramienta_por_ruta(request.resolver_match)
    if actual is None or actual.id not in HERRAMIENTAS_SISTEMAS:
        raise Http404("No existe esa herramienta de sistemas.")
    configuracion = HERRAMIENTAS_SISTEMAS[actual.id]

    datos = request.POST.copy() if request.method == "POST" else None
    if datos is not None and configuracion.metodo_fijo:
        # La herramienta decide el método; una entrada compartida desde otra
        # herramienta llega con su propio método y aquí se sustituye.
        datos["metodo"] = configuracion.metodo_fijo
    form = SistemaForm(datos, initial={"metodo": configuracion.metodo_fijo or "gauss_jordan"})
    resultado = None
    guias = ()

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
        except ValueError as error:
            if form.cleaned_data.get("tipo_entrada") == "matriz":
                form.add_error(None, str(error))
            else:
                form.add_error("sistema", str(error))

    return render(
        request,
        "calculadora/modules/sistemas/index.html",
        {
            "form": form,
            "configuracion": configuracion,
            "metodo_fijo_nombre": dict(SistemaForm.METODOS).get(configuracion.metodo_fijo),
            "resultado": resultado,
            "titulo_resultado": configuracion.titulo_resultado
            or (resultado["metodo"] if resultado else None),
            "matrix_values": form.valores_matriz_ingresados(),
            "guias": guias,
            "teclado_sistema": TECLADO_SISTEMA,
            "teclado_matriz": TECLADO_MATRIZ,
            "formulario_compartido": "sistema-form",
            # Las herramientas de esta categoría comparten el formulario: tras
            # resolver, una relacionada puede recibir la misma entrada.
            "ids_comparten_entrada": tuple(HERRAMIENTAS_SISTEMAS),
        },
    )
