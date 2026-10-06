"""Vistas HTTP de la interfaz web."""

from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from backend.sistemas_numericos import NOMBRES_BASE
from backend.presupuesto_sistemas import CELDAS_MAXIMAS, dimensiones_admitidas

from . import catalogo
from .exploraciones import exploraciones_sistema
from .forms import ConversionBasesForm, SistemaForm, VectoresForm
from .forms_ecuaciones import EcuacionMatricialForm
from .forms_expresiones import ExpresionMatricialForm
from .forms_inversa import InversaForm
from .forms_romanos import ConversionRomanosForm
from .opciones_ecuaciones import AYUDA_METODOS as AYUDA_METODOS_ECUACION
from .servicios_ecuaciones import resolver_ecuacion_web
from .servicios_expresiones import evaluar_expresion_web
from .presupuesto_expresiones import confirmacion_pendiente as confirmar_expresion
from .servicios_inversa import calcular_inversa_web, confirmacion_pendiente
from .opciones_sistemas import (
    BLOQUES_PREDETERMINADOS,
    METODO_PREDETERMINADO,
    RUTAS_ANTIGUAS,
    metodos_a_resolver,
    titulo_resultado,
)
from .opciones_vectores import AYUDAS, texto_boton
from .servicios import resolver_entrada_web
from .servicios_bases import convertir_entrada
from .servicios_romanos import convertir_romanos
from .servicios_vectores import operar_vectores
from .teclados import PERFILES_BASE, perfiles_para


@require_GET
def inicio(request):
    consulta = request.GET.get("q", "").strip()
    resultados = catalogo.buscar_herramientas(consulta) if consulta else None
    return render(request, "calculadora/pages/inicio.html", {
        "consulta": consulta,
        "resultados_busqueda": resultados,
        "universo_busqueda": (*resultados, *(h for h in catalogo.HERRAMIENTAS if h not in resultados)) if resultados is not None else (),
    })


@require_http_methods(["GET", "POST"])
def sistemas(request):
    """Reducción por filas: método a elegir (o comparar los dos) y bloques del resultado."""
    # Las rutas antiguas (/sistemas/?metodo=gauss) y los enlaces de «También puedes
    # explorar» llegan por GET con el método, la entrada y los bloques ya preparados.
    inicial = {"metodo": METODO_PREDETERMINADO, **SistemaForm.inicial_desde(request.GET)}

    form = SistemaForm(request.POST or None, initial=inicial)
    resultados = []
    mostrar = frozenset(BLOQUES_PREDETERMINADOS)
    exploraciones = ()

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
            exploraciones = exploraciones_sistema(form.pares_de_entrada(), metodo, mostrar)
        except ValueError as error:
            resultados = []
            if form.cleaned_data.get("tipo_entrada") == "matriz":
                form.grupo_error = "matrix-grid"
                form.add_error(None, str(error))
            else:
                form.add_error("sistema", str(error))

    matrix_values = form.valores_matriz_ingresados()
    if request.method == "GET" and dimensiones_admitidas(
        inicial.get("ecuaciones"), inicial.get("variables")
    ):
        matrix_values = SistemaForm.valores_matriz_desde(
            request.GET, inicial["ecuaciones"], inicial["variables"]
        )

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
            "matrix_values": matrix_values,
            "celdas_maximas": CELDAS_MAXIMAS,
            # Las opciones se despliegan solas cuando difieren de lo predeterminado.
            "opciones_abiertas": set(form.bloques_elegidos()) != set(BLOQUES_PREDETERMINADOS),
            "exploraciones": exploraciones,
            "perfiles_teclado": perfiles_para("sistema", "numerico"),
        },
    )


@require_http_methods(["GET", "POST"])
def sistemas_ruta_antigua(request, herramienta=None):
    """Marcadores históricos hacia Reducción por filas, sin perder entrada ni bloques.

    GET usa 301. /sistemas/ procesa POST con la misma vista (clientes sin
    seguimiento de redirects y benchmark histórico); los slugs usan 308.
    Los parámetros explícitos prevalecen sobre el método sugerido por la ruta.
    La validación de parámetros sigue en SistemaForm, en el destino canónico.
    """
    parametros = {} if herramienta is None else RUTAS_ANTIGUAS.get(herramienta)
    if parametros is None:
        raise Http404("No existe esa herramienta de sistemas.")
    if request.method == "POST" and herramienta is None:
        return sistemas(request)
    consulta = request.GET.copy()
    for clave, valor in parametros.items():
        if clave not in consulta:
            consulta[clave] = valor
    destino = reverse("calculadora:reduccion-filas")
    if consulta:
        destino = f"{destino}?{consulta.urlencode()}"
    return HttpResponsePermanentRedirect(destino, preserve_request=request.method == "POST")


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
        form = VectoresForm(request.POST, ajustar=True)
        if form.is_valid():
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
            "perfiles_teclado": perfiles_para("numerico"),
        },
    )


@require_http_methods(["GET", "POST"])
def operaciones_matrices(request):
    """Operaciones con matrices: símbolos definidos uno a uno y una expresión que los combina.

    A + B, 2A, AB, Ax, Aᵀ o A(B + C) - 2D usan el mismo flujo y el mismo motor de
    expresiones, que reutiliza las operaciones exactas de backend.matrices.
    """
    accion = next((nombre for nombre in ("agregar", "eliminar", "ajustar") if nombre in request.POST), None)
    form = ExpresionMatricialForm(request.POST if request.method == "POST" else None, accion=accion)
    resultado = confirmacion = None
    if request.method == "POST" and form.is_valid():
        if accion:
            form = ExpresionMatricialForm(initial=form.cleaned_data["estado"])
        else:
            try:
                entrada = form.cleaned_data["entrada"]
                confirmacion = confirmar_expresion(entrada, form.cleaned_data["confirmacion"])
                if confirmacion is None:
                    resultado = evaluar_expresion_web(entrada)
            except ValueError as error:
                form.add_error("expresion", str(error))
    return render(request, "calculadora/modules/expresiones/index.html", {
        "form": form, "resultado": resultado, "confirmacion": confirmacion,
        "perfiles_teclado": perfiles_para("numerico", "expresion", "lineal"),
    })


@require_http_methods(["GET", "POST"])
def expresiones_ruta_antigua(request):
    """Expresiones matriciales dejó de ser una herramienta aparte: es Operaciones con matrices.

    GET usa 301 y conserva la consulta. POST usa 308: el navegador reenvía el mismo
    cuerpo, que el formulario unificado entiende tal cual (es el de expresiones).
    """
    destino = reverse("calculadora:operaciones-matrices")
    if request.GET:
        destino = f"{destino}?{request.GET.urlencode()}"
    return HttpResponsePermanentRedirect(destino, preserve_request=request.method == "POST")


@require_http_methods(["GET", "POST"])
def ecuaciones_matriciales(request):
    """Resolver Ax = b: A y b conocidos; x se determina con los motores de Reducción por filas."""
    ajustar = request.method == "POST" and "ajustar" in request.POST
    form = EcuacionMatricialForm(request.POST if request.method == "POST" else None, ajustar=ajustar)
    resultado = None
    if request.method == "POST" and form.is_valid():
        if ajustar:
            # «Aplicar» sin JavaScript: se redibujan A, x y b con las dimensiones nuevas, sin resolver.
            form = EcuacionMatricialForm(initial=form.iniciales())
        else:
            try:
                resultado = resolver_ecuacion_web(form.cleaned_data["entrada"])
            except ValueError as error:
                form.add_error(None, str(error))
    return render(request, "calculadora/modules/ecuaciones/index.html", {
        "form": form, "resultado": resultado, "ayuda_metodos": AYUDA_METODOS_ECUACION,
        # El procedimiento reutiliza los bloques de Reducción por filas, todos visibles.
        "mostrar": frozenset(BLOQUES_PREDETERMINADOS), "perfiles_teclado": perfiles_para("numerico"),
    })


@require_http_methods(["GET", "POST"])
def matriz_inversa(request):
    """Matriz inversa: Gauss-Jordan sobre [A | I] o, si A es 2×2, la regla directa.

    Un cálculo que se estima largo no se ejecuta hasta que el usuario confirma;
    el aviso conserva la matriz y el método porque vive dentro del mismo formulario.
    """
    ajustar = request.method == "POST" and "ajustar" in request.POST
    form = InversaForm(request.POST if request.method == "POST" else None, ajustar=ajustar)
    resultado = confirmacion = None
    if request.method == "POST" and form.is_valid():
        if ajustar:
            # «Aplicar» sin JavaScript y «Cancelar» del aviso: redibujan con lo escrito, sin calcular.
            form = InversaForm(initial=form.iniciales())
        else:
            entrada = form.cleaned_data["entrada"]
            confirmacion = confirmacion_pendiente(entrada, form.cleaned_data["confirmacion"])
            if confirmacion is None:
                try:
                    resultado = calcular_inversa_web(entrada)
                except ValueError as error:
                    form.grupo_error = "inverse-matrix"
                    form.add_error(None, str(error))
    return render(request, "calculadora/modules/inversa/index.html", {
        "form": form, "resultado": resultado, "confirmacion": confirmacion,
        "perfiles_teclado": perfiles_para("numerico"),
    })


@require_http_methods(["GET", "POST"])
def conversion_bases(request):
    """Conversión de un número a una o varias de las otras bases con procedimiento compartido."""
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
                bases_destino=form.cleaned_data["bases_destino"],
            )
        except ValueError as error:
            form.add_error("numero", str(error))

    # El teclado y la etiqueta del número siguen a la base de origen, también sin JavaScript.
    base_origen = form["base_origen"].value() if form.is_bound else form.initial.get("base_origen", 10)
    try:
        base_entrada = int(base_origen)
    except (TypeError, ValueError):
        base_entrada = 10
    if base_entrada not in PERFILES_BASE:
        base_entrada = 10

    return render(
        request,
        "calculadora/modules/bases/index.html",
        {
            "form": form,
            "resultado": resultado,
            "bases_entrada": tuple(
                (base, NOMBRES_BASE[base]) for base in PERFILES_BASE
            ),
            "perfiles_teclado": perfiles_para(*(perfil.id for perfil in PERFILES_BASE.values())),
            "bases_digitos": {
                base: {
                    "nombre": NOMBRES_BASE[base], "perfil": perfil.id,
                    "digitos": [tecla.insercion for tecla in perfil.teclas],
                }
                for base, perfil in PERFILES_BASE.items()
            },
            "perfil_entrada": PERFILES_BASE[base_entrada].id,
            "base_entrada_activa": base_entrada,
        },
    )


@require_http_methods(["GET", "POST"])
def conversion_romanos(request):
    """Arábigo ↔ romano: una dirección, un número, un resultado y su descomposición."""
    form = ConversionRomanosForm(request.POST or None)
    resultado = None
    if request.method == "POST" and form.is_valid():
        try:
            resultado = convertir_romanos(
                direccion=form.cleaned_data["direccion"], numero=form.cleaned_data["numero"],
            )
        except ValueError as error:
            form.add_error("numero", str(error))
    return render(request, "calculadora/modules/romanos/index.html", {"form": form, "resultado": resultado})
