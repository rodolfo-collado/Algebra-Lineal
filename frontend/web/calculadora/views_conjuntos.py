"""Flujo HTTP del editor y la única evaluación de expresiones."""

from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from backend.conjuntos.literales import analizar_literal
from backend.conjuntos.presupuesto import Presupuesto
from .forms_conjuntos import EJEMPLOS, GUIA, CardinalidadesForm, ConjuntosForm, elegir_nombres, inicial_ejemplo, rellenar
from .servicios_conjuntos import cardinalidades_web, relacion_web, resumen_definiciones
from .teclados import perfiles_para


def _resumir(form):
    """Lectura de cada fila (elementos y cuántos son) cuando su contenido es válido."""
    for bloque in form.bloques:
        nombre, contenido = bloque["nombre"].value() or "", bloque["contenido"].value() or ""
        try:
            valor = analizar_literal(contenido, presupuesto=Presupuesto())
        except ValueError:
            bloque["resumen"] = None
            continue
        bloque["resumen"] = resumen_definiciones({nombre: valor}).get(nombre)


def _elemento_guia(form):
    """Un elemento real del primer conjunto, para que «x ∈ A» de la guía tenga sentido."""
    nombres = [b["nombre"].value() for b in form.bloques if b["nombre"].value()]
    a = elegir_nombres(nombres)[0]
    primero = next((b.get("resumen") for b in form.bloques if b["nombre"].value() == a), None)
    return primero["elementos"][0] if primero and primero.get("elementos") else "1"


def _guia(form):
    nombres = [b["nombre"].value() for b in form.bloques if b["nombre"].value()]
    elemento = _elemento_guia(form)
    return [(grupo, [{"clave": clave, "nombre": nombre, "plantilla": plantilla, "descripcion": descripcion,
                      "texto": rellenar(plantilla, nombres, elemento)}
                     for clave, nombre, plantilla, descripcion in filas]) for grupo, filas in GUIA]


@require_http_methods(["GET", "POST"])
def relaciones_conjuntos(request):
    inicial = inicial_ejemplo(request.GET.get("ejemplo", ""))
    form = ConjuntosForm(request.POST if request.method == "POST" else None, initial=inicial)
    resultado = None
    if request.method == "POST" and form.is_valid():
        venn = {}
        try:
            if form.accion == "calcular" and "eliminar" not in request.POST:
                venn = {"venn_nombres": tuple(n.strip() for n in form.cleaned_data.get("venn_nombres", "").split(",") if n.strip()),
                        "venn_universo": form.cleaned_data.get("venn_universo", "").strip() or None}
                resultado = relacion_web(form.expresion, form.entorno, presupuesto=form.presupuesto,
                                         punto=form.cleaned_data.get("punto", "").strip(), **venn)
        except ValueError as error:
            pedido = venn.get("venn_nombres") or venn.get("venn_universo")
            form.add_error("venn_nombres" if pedido and ("Venn" in str(error) or "universo" in str(error)) else "expresion", str(error))
        if resultado and resultado["error_punto"]:
            # El resultado sigue siendo válido: el error queda junto al punto, en la recta.
            form.add_error("punto", resultado["error_punto"])
        elif not form.errors:
            inicial = {"cantidad": len(form.filas), "expresion": form.expresion,
                       "definicion": "" if form.accion == "agregar" else form.cleaned_data.get("definicion", ""),
                       **{n: form.cleaned_data.get(n, "") for n in ("punto", "venn_nombres", "venn_universo")}}
            for i, (nombre, contenido) in enumerate(form.filas):
                inicial.update({f"nombre_{i}": nombre, f"contenido_{i}": contenido, f"anterior_{i}": nombre})
            form = ConjuntosForm(initial=inicial)
    _resumir(form)
    return render(request, "calculadora/modules/conjuntos/index.html", {
        "form": form, "resultado": resultado, "guia": _guia(form), "elemento_guia": _elemento_guia(form),
        # La guía se ofrece abierta mientras no hay nada escrito; después deja sitio al cálculo.
        "guia_abierta": not (form["expresion"].value() or "").strip(),
        "ejemplos": [(clave, titulo) for clave, (titulo, *_resto) in EJEMPLOS.items()],
        "perfiles_teclado": perfiles_para("literal-conjuntos", "relacion-conjuntos"),
    })


@require_http_methods(['GET', 'POST'])
def cardinalidades_conjuntos(request):
    form = CardinalidadesForm(request.POST if request.method == 'POST' else None,
                              initial={'numero': '2', 'modo': 'regiones', 'expresion': 'A ∪ B'})
    resultado = None
    if request.method == 'POST' and form.is_valid() and request.POST.get('accion', 'calcular') == 'calcular':
        try:
            datos = {m: form.cleaned_data[f'region_{m}'] for m in range(1, 1 << len(form.nombres))}
            resultado = cardinalidades_web(form.nombres, datos, modo=form.cleaned_data['modo'],
                                           universo=form.cleaned_data['universo'], expresion=form.cleaned_data['expresion'])
        except ValueError as error:
            mensaje = str(error)
            # Datos incoherentes afectan a varios campos: aviso general; el universo, junto a su campo.
            campo = None if 'incoherentes' in mensaje else 'universo' if 'universo' in mensaje and 'expresión' not in mensaje else 'expresion'
            form.add_error(campo, mensaje)
    return render(request, 'calculadora/modules/conjuntos/cardinalidades.html', {
        'form': form, 'resultado': resultado, 'perfiles_teclado': perfiles_para('regiones-conjuntos')})
