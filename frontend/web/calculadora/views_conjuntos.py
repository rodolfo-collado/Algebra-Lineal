"""Flujo HTTP del editor y la única evaluación de expresiones."""

from random import sample
from urllib.parse import urlencode

from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from backend.conjuntos.literales import analizar_literal, validar_nombre
from backend.conjuntos.presupuesto import Presupuesto
from backend.conjuntos.modelo import Conjunto
from backend.conjuntos.parser import analizar_expresion
from backend.conjuntos.regiones import construir_venn
from .forms_conjuntos import (EJEMPLOS, GUIA, CardinalidadesForm, ConjuntosForm, elegir_nombres, escribir_region, inicial_editor,
                              inicial_ejemplo, nombres_diagrama, rellenar)
from .servicios_conjuntos import cardinalidades_web, panorama_web, relacion_web, resumen_definiciones
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


def _entorno(inicial):
    """Definiciones que se pueden leer; una fila a medio escribir se queda fuera del diagrama."""
    entorno, presupuesto = {}, Presupuesto()
    for i in range(inicial["cantidad"]):
        nombre = inicial[f"nombre_{i}"]
        try:
            validar_nombre(nombre)
            entorno.setdefault(nombre, analizar_literal(inicial[f"contenido_{i}"], presupuesto=presupuesto))
        except ValueError:
            continue
    return entorno


def _con_diagrama(inicial, azar=False):
    """Completa los datos iniciales con el diagrama leído de las definiciones.

    Devuelve los datos con una región por campo y lo que la plantilla dibuja alrededor:
    nombres, universo, tarjetas y el enlace al modo de cantidades. Sin conjuntos finitos
    (solo intervalos) no hay diagrama; si las opciones pedidas no sirven, se explica en `aviso`."""
    entorno = _entorno(inicial)
    finitos = [n for n, v in entorno.items() if isinstance(v, Conjunto)]
    elegidos = inicial.get("venn_nombres", "")
    pedido = inicial.get("venn_universo", "").strip()
    cardinalidad = reverse("calculadora:cardinalidades-conjuntos")
    if entorno and not finitos and not elegidos.strip():
        return inicial, None
    nombres = nombres_diagrama(finitos, elegidos)
    presupuesto = Presupuesto()

    def leer(universo):
        if len(nombres) not in (2, 3):
            raise ValueError("Elige dos o tres conjuntos para el diagrama, separados por comas.")
        ampliado = {**entorno, **{n: entorno.get(n, Conjunto()) for n in nombres}}
        if universo and universo not in ampliado:
            ampliado[universo] = Conjunto(e for n in nombres if isinstance(ampliado[n], Conjunto) for e in ampliado[n].elementos)
        return construir_venn(nombres, ampliado, analizar_expresion(" ∪ ".join(nombres)),
                              universo=universo, presupuesto=presupuesto)

    # Sin universo pedido se ofrece U: el exterior queda disponible sin configurar nada.
    universo = pedido or ("U" if "U" not in nombres else None)
    aviso = None
    try:
        regiones = leer(universo)
    except ValueError as error:
        aviso = str(error)
        if pedido or not universo:
            return inicial, {"aviso": aviso, "cantidades_url": cardinalidad}
        # Un U que existe pero no contiene a los conjuntos no es su universo: se dibuja sin exterior.
        try:
            regiones, universo, aviso = leer(None), None, None
        except ValueError as error:
            return inicial, {"aviso": str(error), "cantidades_url": cardinalidad}
    valores = {f'venn_region_{r["mascara"]}': escribir_region(r["elementos"])
               for r in regiones if r["mascara"] or universo}
    if azar:
        numeros = iter(sample(range(1, 50), len(valores) * 2))
        valores = {n: f"{next(numeros)}, {next(numeros)}" for n in valores}
    definido = universo in entorno
    panorama = None
    if any(n in entorno for n in nombres):
        try:
            panorama = panorama_web(nombres, universo if definido else None, {r["mascara"]: r["elementos"] for r in regiones})
        except ValueError:
            pass  # Nombres tan largos que agotan el presupuesto de lectura: el diagrama sigue, sin tarjetas.
    # ponytail: Cardinalidad nombra sus conjuntos A, B y C; con otros nombres el enlace no lleva cantidades.
    if panorama and nombres in (("A", "B"), ("A", "B", "C")):
        consulta = {"numero": len(nombres), **{f'region_{r["mascara"]}': len(r["elementos"]) for r in regiones if r["mascara"]}}
        if definido:
            consulta["universo"] = len(entorno[universo].elementos)
        cardinalidad += "?" + urlencode(consulta)
    inicial = {**inicial, **valores, "base_nombres": ", ".join(nombres), "base_universo": universo or "",
               "venn_fuente": "regiones" if azar else ""}
    return inicial, {"nombres": nombres, "universo": universo, "exterior_conocido": definido, "aviso": aviso,
                     "panorama": panorama, "cantidades_url": cardinalidad}


def _formulario(inicial, errores=(), azar=False):
    """Formulario ya sincronizado con el modelo: filas, regiones del diagrama y tarjetas.

    Un error de cálculo (la expresión, un punto) conserva esa sincronización: los datos
    normalizados se vuelven a enviar al formulario para que el error quede junto a su campo."""
    inicial, diagrama = _con_diagrama(inicial, azar)
    errores = list(errores)
    if diagrama and diagrama["aviso"] and (inicial.get("venn_nombres", "").strip() or inicial.get("venn_universo", "").strip()):
        errores.append(("venn_universo" if "universo" in diagrama["aviso"] else "venn_nombres", diagrama["aviso"]))
    if not errores:
        return ConjuntosForm(initial=inicial), diagrama
    form = ConjuntosForm({nombre: str(valor) for nombre, valor in inicial.items()} | {"accion": "guardar"})
    form.is_valid()
    for campo, mensaje in errores:
        form.add_error(campo, mensaje)
    return form, diagrama


@require_http_methods(["GET", "POST"])
def relaciones_conjuntos(request):
    inicial = inicial_ejemplo(request.GET.get("ejemplo", ""))
    form = ConjuntosForm(request.POST) if request.method == "POST" else None
    resultado = diagrama = None
    regiones_aplicadas = False
    if form is not None and form.is_valid():
        errores = []
        venn = {}
        try:
            if form.accion == "calcular" and "eliminar" not in request.POST:
                venn = {"venn_nombres": tuple(n.strip() for n in form.cleaned_data.get("venn_nombres", "").split(",") if n.strip()),
                        "venn_universo": form.cleaned_data.get("venn_universo", "").strip() or None}
                resultado = relacion_web(form.expresion, form.entorno, presupuesto=form.presupuesto,
                                         punto=form.cleaned_data.get("punto", "").strip(), **venn)
        except ValueError as error:
            pedido = venn.get("venn_nombres") or venn.get("venn_universo")
            campo = "venn_nombres" if pedido and ("Venn" in str(error) or "universo" in str(error)) else "expresion"
            errores.append((campo, str(error)))
        if resultado and resultado["error_punto"]:
            # El resultado sigue siendo válido: el error queda junto al punto, en la recta.
            errores.append(("punto", resultado["error_punto"]))
        regiones_aplicadas = form.regiones_aplicadas and not resultado and not errores
        inicial = inicial_editor(form.filas, form.expresion,
                                 definicion="" if form.accion == "agregar" else form.cleaned_data.get("definicion", ""),
                                 **{n: form.cleaned_data.get(n, "") for n in ("punto", "venn_nombres", "venn_universo")})
        form, diagrama = _formulario(inicial, errores, azar=form.accion == "azar_regiones")
    elif form is None:
        form, diagrama = _formulario(inicial)
    elif form.regiones:
        # Entrada que no se pudo leer: el diagrama conserva el borrador tal como se envió.
        diagrama = {"nombres": form.nombres_regiones[:3], "universo": form.universo_regiones, "exterior_conocido": True,
                    "aviso": None, "panorama": None, "cantidades_url": reverse("calculadora:cardinalidades-conjuntos")}
    if diagrama and diagrama.get("nombres") and form.regiones and form.regiones[0].mascara == 0 and not diagrama["exterior_conocido"]:
        form.fields["venn_region_0"].widget.attrs["placeholder"] = "?"
    _resumir(form)
    return render(request, "calculadora/modules/conjuntos/index.html", {
        "form": form, "resultado": resultado, "guia": _guia(form), "diagrama": diagrama,
        "regiones_aplicadas": regiones_aplicadas,
        "opciones_abiertas": bool(form["venn_nombres"].errors or form["venn_universo"].errors),
        "barra": perfiles_para("relacion-conjuntos")["relacion-conjuntos"]["grupos"],
        "ejemplos": [(clave, titulo) for clave, (titulo, *_resto) in EJEMPLOS.items()],
        "perfiles_teclado": perfiles_para("literal-conjuntos"),
    })


@require_http_methods(['GET', 'POST'])
def cardinalidades_conjuntos(request):
    inicial = {'numero': '2', 'modo': 'regiones', 'expresion': 'A ∪ B'}
    # El diagrama de elementos enlaza aquí con sus cantidades ya contadas: solo enteros, nada más.
    numero = request.GET.get('numero')
    if request.method == 'GET' and numero in ('2', '3'):
        inicial['numero'] = numero
        if numero == '3':
            inicial['expresion'] = 'A ∪ B ∪ C'
        for nombre in [f'region_{m}' for m in range(1, 1 << int(numero))] + ['universo']:
            valor = request.GET.get(nombre, '')
            if valor.isascii() and valor.isdigit() and len(valor) <= 100:
                inicial[nombre] = valor
    form = CardinalidadesForm(request.POST if request.method == 'POST' else None, initial=inicial)
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
