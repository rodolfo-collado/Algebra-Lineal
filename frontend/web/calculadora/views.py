"""Vistas HTTP de la interfaz web."""

from urllib.parse import urlencode

from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from backend.sistemas_numericos import NOMBRES_BASE

from . import catalogo
from .forms import ConversionBasesForm, SistemaForm, VectoresForm
from .forms_matrices import MatricesForm
from .opciones_matrices import CONFIGURACION as OPCIONES_MATRICES
from .servicios_matrices import operar_matrices
from .guias import guias_para_resultado
from .opciones_sistemas import (
    BLOQUES_PREDETERMINADOS,
    METODO_PREDETERMINADO,
    METODOS,
    RUTAS_ANTIGUAS,
    metodos_a_resolver,
    titulo_resultado,
)
from .opciones_vectores import AYUDAS, texto_boton
from .servicios import resolver_entrada_web
from .servicios_bases import convertir_entrada
from .servicios_vectores import operar_vectores
from .teclados import TECLADO_MATRIZ, TECLADO_SISTEMA, TECLADOS_BASE


@require_GET
def inicio(request):
    consulta = request.GET.get("q", "").strip()
    return render(request, "calculadora/pages/inicio.html", {
        "consulta": consulta,
        "resultados_busqueda": catalogo.buscar_herramientas(consulta) if consulta else None,
        "herramientas_disponibles": catalogo.herramientas_disponibles(),
    })


@require_http_methods(["GET", "POST"])
def sistemas(request):
    """Resolver un sistema: método a elegir (o comparar los dos) y bloques del resultado."""
    inicial = {"metodo": METODO_PREDETERMINADO}
    # Las rutas antiguas llegan como /sistemas/?metodo=gauss: el método viene preseleccionado.
    if request.GET.get("metodo") in dict(METODOS):
        inicial["metodo"] = request.GET["metodo"]

    form = SistemaForm(request.POST or None, initial=inicial)
    resultados = []
    mostrar = frozenset(BLOQUES_PREDETERMINADOS)
    guias = ()

    if request.method == "POST" and form.is_valid():
        metodo = form.cleaned_data["metodo"]
        mostrar = frozenset(form.cleaned_data["mostrar"])
        try:
            # «Comparar ambos» resuelve la misma entrada con cada método; la
            # clasificación y la solución coinciden por construcción y se muestran una vez.
            resultados = [
                resolver_entrada_web(
                    form.cleaned_data["tipo_entrada"],
                    nombre_metodo,
                    texto=form.cleaned_data.get("sistema"),
                    matriz_aumentada=form.cleaned_data.get("matriz_aumentada"),
                )
                for nombre_metodo in metodos_a_resolver(metodo)
            ]
            guias = guias_para_resultado(
                metodo=metodo,
                clasificacion_clave=resultados[0]["clasificacion_clave"],
                columnas_pivote=resultados[0]["columnas_pivote"] if "pivotes" in mostrar else None,
            )
        except ValueError as error:
            resultados = []
            if form.cleaned_data.get("tipo_entrada") == "matriz":
                form.add_error(None, str(error))
            else:
                form.add_error("sistema", str(error))

    return render(
        request,
        "calculadora/modules/sistemas/index.html",
        {
            "form": form,
            "resultados": resultados,
            "resultado": resultados[0] if resultados else None,
            "comparando": len(resultados) > 1,
            "mostrar": mostrar,
            "titulo_resultado": titulo_resultado(form.cleaned_data["metodo"]) if resultados else None,
            "matrix_values": form.valores_matriz_ingresados(),
            "guias": guias,
            "teclado_sistema": TECLADO_SISTEMA,
            "teclado_matriz": TECLADO_MATRIZ,
        },
    )


def sistemas_ruta_antigua(request, herramienta):
    """Las cinco pseudo-herramientas de P10.1 hoy son opciones de Resolver un sistema."""
    parametros = RUTAS_ANTIGUAS.get(herramienta)
    if parametros is None:
        raise Http404("No existe esa herramienta de sistemas.")
    destino = reverse("calculadora:sistemas")
    if parametros:
        destino = f"{destino}?{urlencode(parametros)}"
    return HttpResponsePermanentRedirect(destino)


@require_http_methods(["GET", "POST"])
def operaciones_vectores(request):
    """Operaciones con vectores: suma, resta, escalar y combinación lineal en un solo flujo."""
    actual = catalogo.herramienta_por_ruta(request.resolver_match)
    if actual is None or actual.id != "operaciones-vectores":
        raise Http404("No existe esa herramienta.")

    resultado = None
    if request.method == "POST" and "ajustar" not in request.POST:
        form = VectoresForm(request.POST)
        if form.is_valid():
            try:
                resultado = operar_vectores(form.cleaned_data["entrada"])
            except ValueError as error:
                form.add_error(None, str(error))
    elif request.method == "POST":
        # «Aplicar» sin JavaScript: se redibuja la estructura con lo escrito, sin calcular.
        form = VectoresForm(initial=VectoresForm.iniciales_desde(request.POST))
    else:
        form = VectoresForm()

    estructura = form.estructura()
    return render(
        request,
        "calculadora/modules/vectores/index.html",
        {
            "form": form,
            "resultado": resultado,
            "estructura": estructura,
            "ayudas_operacion": AYUDAS,
            "texto_boton": texto_boton(estructura["operacion"]),
            "valores_vectores": form.valores_ingresados(),
            "teclado_vector": TECLADO_MATRIZ,
        },
    )


@require_http_methods(["GET", "POST"])
def operaciones_matrices(request):
    ajustar = request.method == "POST" and "ajustar" in request.POST
    form = MatricesForm(request.POST if request.method == "POST" else None, ajustar=ajustar)
    resultado = None
    if request.method == "POST" and form.is_valid():
        if ajustar:
            form = MatricesForm(initial=form.iniciales())
        else:
            try:
                resultado = operar_matrices(form.cleaned_data["entrada"])
            except ValueError as error:
                form.add_error(None, str(error))
    return render(request, "calculadora/modules/matrices/index.html", {
        "form": form, "resultado": resultado, "opciones_matrices": OPCIONES_MATRICES,
        "teclado_matriz": TECLADO_MATRIZ,
    })


@require_http_methods(["GET", "POST"])
def conversion_bases(request):
    """Conversión entre binario, octal, decimal y hexadecimal con procedimiento visible."""
    actual = catalogo.herramienta_por_ruta(request.resolver_match)
    if actual is None or actual.id != "conversion-bases":
        raise Http404("No existe esa herramienta.")

    form = ConversionBasesForm(request.POST or None)
    resultado = None

    if request.method == "POST" and form.is_valid():
        try:
            resultado = convertir_entrada(
                numero=form.cleaned_data["numero"],
                base_origen=form.cleaned_data["base_origen"],
                base_destino=form.cleaned_data["base_destino"],
            )
        except ValueError as error:
            form.add_error("numero", str(error))

    # El teclado y la etiqueta del número siguen a la base de origen, también sin JavaScript.
    base_origen = form["base_origen"].value() if form.is_bound else form.initial.get("base_origen", 10)
    try:
        base_entrada = int(base_origen)
    except (TypeError, ValueError):
        base_entrada = 10
    if base_entrada not in TECLADOS_BASE:
        base_entrada = 10

    return render(
        request,
        "calculadora/modules/bases/index.html",
        {
            "form": form,
            "resultado": resultado,
            "bases_entrada": tuple(
                (base, NOMBRES_BASE[base], teclado) for base, teclado in TECLADOS_BASE.items()
            ),
            "base_entrada_activa": base_entrada,
        },
    )
