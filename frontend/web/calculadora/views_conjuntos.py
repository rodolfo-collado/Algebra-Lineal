"""Flujo HTTP del editor y la única evaluación de relaciones."""

from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from backend.conjuntos.parser import analizar_relacion
from .forms_conjuntos import ConjuntosForm, CardinalidadesForm, inicial_editor
from .servicios_conjuntos import relacion_web
from .teclados import perfiles_para
from backend.conjuntos.cardinalidades import resolver_cardinalidades


@require_http_methods(["GET", "POST"])
def relaciones_conjuntos(request):
    form = ConjuntosForm(request.POST if request.method == "POST" else None, initial=inicial_editor())
    resultado = None
    if request.method == "POST" and form.is_valid():
        try:
            if form.accion == "calcular" and "eliminar" not in request.POST:
                resultado = relacion_web(form.expresion, form.entorno, presupuesto=form.presupuesto,
                    punto=form.cleaned_data.get('punto',''),
                    venn_nombres=tuple(n.strip() for n in form.cleaned_data.get('venn_nombres','').split(',') if n.strip()),
                    venn_universo=form.cleaned_data.get('venn_universo') or None)
            elif form.accion == "construir":
                analizar_relacion(form.expresion, presupuesto=form.presupuesto)
        except ValueError as error:
            form.add_error("expresion", str(error))
        if not form.errors:
            inicial = inicial_editor(form.filas, form.expresion,
                                     definicion="" if form.accion == "agregar" else form.cleaned_data.get("definicion", ""),
                                     **{n: form.cleaned_data.get(n, "") for n in ("izquierdo", "operador", "derecho", 'punto','venn_nombres','venn_universo')})
            form = ConjuntosForm(initial=inicial)
    return render(request, "calculadora/modules/conjuntos/index.html", {
        "form": form, "resultado": resultado,
        'campos_visualizacion': [form[n] for n in ('punto','venn_nombres','venn_universo')],
        "perfiles_teclado": perfiles_para("literal-conjuntos", "relacion-conjuntos"),
    })


@require_http_methods(['GET','POST'])
def cardinalidades_conjuntos(request):
    form = CardinalidadesForm(request.POST if request.method == 'POST' else None,
                               initial={'numero':'2','modo':'regiones','expresion':'A ∪ B'})
    resultado = None
    if request.method == 'POST' and form.is_valid() and request.POST.get('accion','calcular') == 'calcular':
        try:
            datos = {m:form.cleaned_data[f'region_{m}'] for m in range(1,1 << len(form.nombres))}
            resultado = resolver_cardinalidades(form.nombres,datos,modo=form.cleaned_data['modo'],
                universo=form.cleaned_data['universo'],expresion=form.cleaned_data['expresion'])
            regiones = [{'mascara':m, 'cantidad':None if v is None else str(v), 'seleccionada':m in resultado['seleccionadas'],
                         'pertenece':tuple(bool(m & (1 << i)) for i in range(len(form.nombres))), 'etiquetas':[],
                         'exterior_conocido':v is not None} for m,v in sorted(resultado['regiones'].items())]
            resultado['datos'] = {'venn':{'nombres':form.nombres,'regiones':regiones},
                'resultado':str(resultado['resultado']), 'union':str(resultado['union']),
                'pasos':[{**p, 'resultado':str(p['resultado']),
                          **({'inicial':str(p['inicial'])} if 'inicial' in p else {}),
                          **({'terminos':[{**t,'valor':str(t['valor'])} for t in p['terminos']]} if 'terminos' in p else {})} for p in resultado['pasos']]}
            resultado['filas'] = regiones
        except ValueError as error:
            form.add_error('expresion',str(error))
    return render(request,'calculadora/modules/conjuntos/cardinalidades.html',{'form':form,'resultado':resultado,
        'perfiles_teclado':perfiles_para('relacion-conjuntos')})
