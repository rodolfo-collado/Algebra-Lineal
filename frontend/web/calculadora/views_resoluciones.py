"""Cuaderno de resoluciones: proyectos, ejercicios y resoluciones; buscar, ordenar y elegir qué exportar.

Solo lee metadatos y el resumen de cada documento; abrir una resolución es ir a su herramienta
con ?resolucion=<id> (el middleware la repone sin recalcular). Todo funciona con formularios:
resoluciones.js añade el recuento de la selección, marcar un grupo y la barra flotante.

Las acciones llegan por POST a cualquiera de las dos páginas y vuelven (PRG) a ``volver`` si es
una ruta local, o a la página que corresponda, con un mensaje breve en ``?hecho=``.
"""

from collections import OrderedDict
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

from django.http import Http404, HttpResponseRedirect, QueryDict
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from . import catalogo
from .resoluciones import organizacion
from .resoluciones.almacen import MAX_NOMBRE, AlmacenFuturo, AlmacenNoDisponible, almacen
from .resoluciones.servicio import NO_DISPONIBLE, url_reabrir


FILTROS = ("q", "herramienta", "desde", "hasta")
VISTAS = ("todos", "pendientes", "resueltos")
MAX_EJERCICIOS_DE_UNA_VEZ = 200
MAX_ENUNCIADO = 2000
# Herramientas desde las que empezar cuando el cuaderno está en blanco: una por área.
SUGERIDAS = ("determinantes", "matriz-inversa", "metodos-cerrados", "relaciones-conjuntos")
HECHOS = {
    "agrupadas": "Llevaste {n} a «{ejercicio}».",
    "sacadas": "Sacaste {n} de su ejercicio; ahora están sueltas.",
    "eliminadas": "Eliminaste {n} del cuaderno.",
    "renombrada": "Cambiaste el nombre de la resolución.",
    "ejercicio_renombrado": "Guardaste los cambios del ejercicio.",
    "disuelto": "Desagrupaste el ejercicio; sus resoluciones siguen en el cuaderno.",
    "proyecto_creado": "Creaste el proyecto. Ahora es tu proyecto activo.",
    "proyecto_editado": "Guardaste los cambios del proyecto.",
    "proyecto_eliminado": "Eliminaste el proyecto; sus ejercicios y resoluciones siguen en el cuaderno.",
    "activado": "Ahora trabajas en «{ejercicio}».",
    "desactivado": "Ya no hay un proyecto activo.",
    "ejercicio_creado": "Creaste «{ejercicio}».",
    "ejercicios_creados": "Creaste {e} nuevos.",
    "ordenados": "Ordenaste los ejercicios por número.",
    "seccion_creada": "Creaste la sección «{ejercicio}».",
    "seccion_eliminada": "Quitaste la sección; sus ejercicios siguen en el proyecto.",
    "quitado": "El ejercicio salió del proyecto; ahora es independiente.",
    "sin_seleccion": "Primero marca al menos una resolución.",
    "sin_nombre": "Escribe un nombre de al menos un carácter.",
    "rango_invalido": "Escribe un rango de números enteros, como del 1 al 64 (hasta 200 de una vez).",
}


def _dia(texto):
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def _rotulo_dia(dia, hoy):
    if dia == hoy:
        return "Hoy"
    if dia == hoy - timedelta(days=1):
        return "Ayer"
    return None


def _entero(valor, minimo=None):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    return numero if minimo is None or numero >= minimo else None


def _texto(valor, maximo=MAX_NOMBRE):
    return " ".join((valor or "").split())[:maximo]


def _cantidad(n):
    return "1 resolución" if n == 1 else f"{n} resoluciones"


# ---- Filtros y búsqueda ----

def _filtros(datos):
    return {clave: datos.get(clave, "").strip()[:MAX_NOMBRE] for clave in FILTROS}


def _coincide(fila, consulta, contexto):
    if not consulta:
        return True
    textos = (fila["nombre"], fila.get("resumen") or "", fila["herramienta_nombre"], *contexto)
    return all(any(termino in catalogo.normalizar(texto) for texto in textos) for termino in consulta)


def _filtrar(filas, filtros, contexto_de):
    consulta = catalogo.normalizar(filtros["q"]).split()
    desde, hasta = _dia(filtros["desde"]), _dia(filtros["hasta"])
    for fila in filas:
        dia = fila["fecha"].date() if fila["fecha"] else None
        if filtros["herramienta"] and fila["herramienta"] != filtros["herramienta"]:
            continue
        if (desde and (dia is None or dia < desde)) or (hasta and (dia is None or dia > hasta)):
            continue
        if _coincide(fila, consulta, contexto_de(fila)):
            yield fila


# ---- Páginas ----

def _cuaderno(filtros):
    """Proyectos, ejercicios independientes y resoluciones sueltas; con filtros, la lista de coincidencias."""
    cuaderno = almacen()
    filas = organizacion.preparar_resoluciones(cuaderno.listar())
    ejercicios = cuaderno.ejercicios()
    proyectos = cuaderno.proyectos()
    nombres_proyecto = {p["id"]: p["nombre"] for p in proyectos}
    por_id = {e["id"]: e for e in ejercicios}
    for ejercicio in ejercicios:
        ejercicio["etiqueta"] = organizacion.etiqueta(ejercicio)
        ejercicio["proyecto_nombre"] = nombres_proyecto.get(ejercicio["proyecto"])

    def ubicacion(fila):
        ejercicio = por_id.get(fila["ejercicio"])
        return (ejercicio["etiqueta"], ejercicio["proyecto_nombre"] or "") if ejercicio else ()

    activo = any(filtros.values())
    contexto = {"total": len(filas), "filtrando": activo, "apartado": cuaderno.apartado,
                "herramientas": sorted({(f["herramienta"], f["herramienta_nombre"]) for f in filas}, key=lambda h: h[1]),
                "destinos": organizacion.destinos(ejercicios, proyectos), "proyectos": proyectos,
                "total_ejercicios": len(ejercicios)}
    for fila in filas:
        ejercicio = por_id.get(fila["ejercicio"])
        fila["ubicacion"] = ejercicio and (f"{ejercicio['proyecto_nombre']} › {ejercicio['etiqueta']}"
                                           if ejercicio["proyecto_nombre"] else ejercicio["etiqueta"])
    if activo:
        coincidencias = list(_filtrar(filas, filtros, ubicacion))
        consulta = catalogo.normalizar(filtros["q"]).split()
        return contexto | {"coincidencias": coincidencias, "visibles": len(coincidencias), "proyectos": [
            p for p in proyectos if consulta and all(t in catalogo.normalizar(p["nombre"]) for t in consulta)]}

    pasos = {}
    for fila in sorted(filas, key=lambda f: (f["posicion"], f["id"])):
        pasos.setdefault(fila["ejercicio"], []).append(fila)
    independientes = []
    for ejercicio in ejercicios:
        if ejercicio["proyecto"] is None:
            propias = pasos.get(ejercicio["id"], [])
            fechas = [f["fecha"] for f in propias if f["fecha"]]
            independientes.append(ejercicio | {"pasos": propias, "total": len(propias),
                                               "ultima": max(fechas) if fechas else organizacion.fecha(ejercicio["creado"])})
    independientes.sort(key=lambda h: h["ultima"] or datetime.min.replace(tzinfo=timezone.get_current_timezone()),
                        reverse=True)
    hoy = timezone.localdate()
    dias = OrderedDict()
    for fila in filas:
        if fila["ejercicio"] is None:
            dias.setdefault(fila["fecha"].date() if fila["fecha"] else None, []).append(fila)
    activo_id, _ = cuaderno.activo()
    for proyecto in proyectos:
        proyecto["progreso"] = organizacion.progreso(
            [{"resuelto": i < proyecto["resueltos"]} for i in range(proyecto["ejercicios"])], proyecto["objetivo"])
        proyecto["activo"] = proyecto["id"] == activo_id
        proyecto["fecha"] = organizacion.fecha(proyecto["ultima"])
    return contexto | {
        "ejercicios": independientes, "visibles": len(filas),
        "sueltas": [{"dia": d, "rotulo": _rotulo_dia(d, hoy), "resoluciones": g} for d, g in dias.items()],
    }


def _base(request, filtros):
    return {"filtros": filtros, "consulta_filtros": urlencode({k: v for k, v in filtros.items() if v}),
            "hecho": _hecho(request.GET), "max_nombre": MAX_NOMBRE, "pagina_resoluciones": True,
            "volver": request.get_full_path(), "pagina": request.path}


@require_http_methods(["GET", "POST"])
def resoluciones(request):
    # Los filtros viajan en la URL; en un POST, en un campo oculto con la consulta de la página.
    filtros = _filtros(request.GET if request.method == "GET" else QueryDict(request.POST.get("filtros", "")))
    contexto = _base(request, filtros) | {
        "sugeridas": [h for h in map(catalogo.herramienta_por_id, SUGERIDAS) if h and h.disponible],
        "migas": (catalogo.Miga("Inicio", reverse("calculadora:inicio")), catalogo.Miga("Resoluciones", actual=True)),
    }
    return _responder(request, contexto, "calculadora/pages/resoluciones.html", lambda: _cuaderno(filtros))


def _proyecto(identificador, vista):
    cuaderno = almacen()
    proyecto = next((p for p in cuaderno.proyectos() if p["id"] == identificador), None)
    if proyecto is None:
        raise Http404("No existe ese proyecto.")
    ejercicios = cuaderno.ejercicios(identificador)
    secciones = cuaderno.secciones(identificador)
    ids = {e["id"] for e in ejercicios}
    filas = organizacion.preparar_resoluciones([f for f in cuaderno.listar() if f["ejercicio"] in ids])
    grupos = organizacion.arbol(proyecto, ejercicios, secciones, filas)
    todos = [e for g in grupos for e in g["ejercicios"]]
    activo_proyecto, activo_ejercicio = cuaderno.activo()
    progreso = organizacion.progreso(todos, proyecto["objetivo"])
    # El mapa sigue el orden del documento; las casillas que faltan hasta el objetivo, al final.
    mapa = [{"id": e["id"], "corta": e["numero"] or "·", "etiqueta": e["etiqueta"], "incluir": e["incluir"],
             "estado": "resuelto" if e["resuelto"] else "pendiente"} for e in todos]
    if vista != "todos":
        for grupo in grupos:
            grupo["ejercicios"] = [e for e in grupo["ejercicios"] if e["resuelto"] == (vista == "resueltos")]
    return {
        "proyecto": proyecto | {"activo": activo_proyecto == identificador}, "grupos": grupos,
        "secciones": secciones, "progreso": progreso, "mapa": mapa, "vista": vista,
        "huecos": range(progreso["pendientes_por_crear"]),
        "vistas": (("todos", "Todos"), ("pendientes", "Pendientes"), ("resueltos", "Con resolución")),
        "borrador": organizacion.borrador(organizacion.arbol(proyecto, ejercicios, secciones, filas)),
        "indice": organizacion.arbol(proyecto, ejercicios, secciones, filas, solo_incluidos=True),
        "ejercicio_activo": activo_ejercicio if activo_proyecto == identificador else None,
        "ejercicios_proyecto": todos, "proyectos": cuaderno.proyectos(), "total": len(filas),
        "destinos": organizacion.destinos(cuaderno.ejercicios(), cuaderno.proyectos()),
        "visibles": sum(len(e["resoluciones"]) for g in grupos for e in g["ejercicios"]),
    }


@require_http_methods(["GET", "POST"])
def proyecto(request, identificador):
    vista = request.GET.get("ver") if request.GET.get("ver") in VISTAS else "todos"
    contexto = _base(request, _filtros({})) | {"vista": vista}
    respuesta = _responder(request, contexto, "calculadora/pages/proyecto.html", lambda: _proyecto(identificador, vista))
    if isinstance(respuesta, TemplateResponse) and "proyecto" in respuesta.context_data:
        nombre = respuesta.context_data["proyecto"]["nombre"]
        respuesta.context_data["migas"] = (
            catalogo.Miga("Inicio", reverse("calculadora:inicio")),
            catalogo.Miga("Resoluciones", reverse("calculadora:resoluciones")), catalogo.Miga(nombre, actual=True))
    return respuesta


def _responder(request, contexto, plantilla, cargar):
    try:
        if request.method == "POST":
            resultado = _accion(request)
            if not isinstance(resultado, dict):
                return resultado
            contexto.update(resultado)
        contexto.update(cargar())
    except AlmacenNoDisponible as error:
        contexto["no_disponible"] = str(error) if isinstance(error, AlmacenFuturo) else NO_DISPONIBLE
    return TemplateResponse(request, plantilla, contexto, status=503 if "no_disponible" in contexto else 200)


# ---- Acciones ----

def _destino(request, por_defecto, **hecho):
    """Vuelve a la página de origen si es local; si no, a la que corresponda. Con el mensaje en ?hecho=."""
    volver = request.POST.get("volver", "")
    seguro = volver.startswith("/") and not volver.startswith("//") and url_has_allowed_host_and_scheme(
        volver, allowed_hosts={request.get_host()})
    destino, _, ancla = (volver if seguro else por_defecto).partition("#")
    if hecho:
        consulta = QueryDict(destino.partition("?")[2], mutable=True)
        for clave in ("hecho", "n", "ejercicio", "e"):
            consulta.pop(clave, None)
        consulta.update({clave: str(valor) for clave, valor in hecho.items()})
        destino = f"{destino.partition('?')[0]}?{consulta.urlencode()}"
    return HttpResponseRedirect(f"{destino}#{ancla}" if ancla else destino)


def _cuaderno_url(filtros):
    consulta = urlencode({k: v for k, v in filtros.items() if v})
    destino = reverse("calculadora:resoluciones")
    return f"{destino}?{consulta}" if consulta else destino


def _proyecto_url(identificador, ancla=""):
    return reverse("calculadora:proyecto", args=[identificador]) + (f"#{ancla}" if ancla else "")


def _ids(datos):
    return [i for i in (_entero(v) for v in datos.getlist("ids")) if i is not None]


def _ejercicio_destino(cuaderno, datos):
    """Ejercicio elegido o uno nuevo (en el proyecto indicado, si lo hay), con su número y título."""
    destino = _entero(datos.get("ejercicio"))
    if destino is not None and cuaderno.existe_ejercicio(destino):
        return destino
    proyecto = _entero(datos.get("proyecto"))
    numero = _texto(datos.get("numero"), 20) or None
    nombre = _texto(datos.get("nombre_ejercicio"))
    if not nombre and not numero:
        nombre = f"Ejercicio {len(cuaderno.ejercicios(proyecto if proyecto else None)) + 1}"
    return cuaderno.crear_ejercicio(nombre, proyecto=proyecto, numero=numero)


def _nombre_de(cuaderno, ejercicio):
    return next((organizacion.etiqueta(e) for e in cuaderno.ejercicios() if e["id"] == ejercicio), "")


def _accion(request):
    """Aplica la acción del POST; devuelve la respuesta o el contexto de una confirmación."""
    cuaderno, datos = almacen(), request.POST
    filtros = _filtros(QueryDict(datos.get("filtros", "")))
    accion, ids = datos.get("accion", ""), _ids(datos)
    identificador = _entero(datos.get("id"))
    proyecto = _entero(datos.get("proyecto"))
    volver_cuaderno = _cuaderno_url(filtros)
    # Botones compactos de una sola acción: op = «mover:tabla:id:±1» o «incluir:tabla:id:0|1».
    if datos.get("op"):
        partes = datos["op"].split(":")
        if len(partes) == 4 and partes[0] in ("mover", "incluir") and _entero(partes[2]) is not None:
            tabla, objetivo, valor = partes[1], int(partes[2]), _entero(partes[3])
            if tabla in ("ejercicios", "resoluciones", "secciones") and valor is not None:
                if partes[0] == "mover":
                    cuaderno.mover(tabla, objetivo, -1 if valor < 0 else 1)
                else:
                    cuaderno.incluir(tabla, [objetivo], valor)
                return _destino(request, volver_cuaderno)
        return _destino(request, volver_cuaderno)

    if accion in ("agrupar", "sacar", "eliminar", "eliminar_confirmado") and not ids:
        return _destino(request, volver_cuaderno, hecho="sin_seleccion")
    if accion == "agrupar":
        destino = _ejercicio_destino(cuaderno, datos)
        cuaderno.agrupar(ids, destino)
        if datos.get("volver_a") == "herramienta" and len(ids) == 1:
            ficha = cuaderno.obtener(ids[0], documento=False)
            enlace = ficha and url_reabrir(ficha["ruta"], ficha["id"])
            if enlace:
                return HttpResponseRedirect(enlace)
        return _destino(request, volver_cuaderno, hecho="agrupadas", n=len(ids), ejercicio=_nombre_de(cuaderno, destino))
    if accion == "sacar":
        cuaderno.agrupar(ids, None)
        return _destino(request, volver_cuaderno, hecho="sacadas", n=len(ids))
    if accion == "eliminar":
        # Primero se confirma: eliminar no se puede deshacer.
        return {"confirmar": [f for f in cuaderno.listar() if f["id"] in ids]}
    if accion == "eliminar_confirmado":
        cuaderno.eliminar(ids)
        return _destino(request, volver_cuaderno, hecho="eliminadas", n=len(ids))

    nombre = _texto(datos.get("nombre"))
    if accion == "renombrar" and identificador is not None:
        if not nombre:
            return _destino(request, volver_cuaderno, hecho="sin_nombre")
        cuaderno.renombrar(identificador, nombre)
        return _destino(request, volver_cuaderno, hecho="renombrada")
    if accion in ("renombrar_ejercicio", "editar_ejercicio") and identificador is not None:
        numero = _texto(datos.get("numero"), 20) or None
        if not nombre and not numero:
            return _destino(request, volver_cuaderno, hecho="sin_nombre")
        enunciado = (datos.get("enunciado") or "").strip()[:MAX_ENUNCIADO] or None
        anterior = next((e for e in cuaderno.ejercicios() if e["id"] == identificador), None)
        if anterior is None:
            return _destino(request, volver_cuaderno)
        cuaderno.editar_ejercicio(identificador, nombre=nombre, numero=numero if "numero" in datos else anterior["numero"],
                                  enunciado=enunciado if "enunciado" in datos else anterior["enunciado"])
        ubicacion = datos.get("ubicacion")
        if ubicacion:
            _ubicar(cuaderno, identificador, ubicacion, anterior)
        return _destino(request, volver_cuaderno, hecho="ejercicio_renombrado")
    if accion == "disolver" and identificador is not None:
        cuaderno.disolver_ejercicio(identificador)
        return _destino(request, volver_cuaderno, hecho="disuelto")
    if accion == "quitar_ejercicio" and identificador is not None:
        cuaderno.ubicar_ejercicios([identificador], None)
        return _destino(request, volver_cuaderno, hecho="quitado")

    # Proyectos
    if accion == "crear_proyecto":
        if not nombre:
            return _destino(request, volver_cuaderno, hecho="sin_nombre")
        nuevo = cuaderno.crear_proyecto(nombre, _entero(datos.get("objetivo"), 1))
        cuaderno.activar(nuevo)
        return HttpResponseRedirect(_proyecto_url(nuevo) + "?hecho=proyecto_creado")
    if accion == "editar_proyecto" and proyecto is not None:
        if not nombre:
            return _destino(request, _proyecto_url(proyecto), hecho="sin_nombre")
        cuaderno.editar_proyecto(proyecto, nombre, _entero(datos.get("objetivo"), 1))
        return _destino(request, _proyecto_url(proyecto), hecho="proyecto_editado")
    if accion == "eliminar_proyecto" and proyecto is not None:
        return {"confirmar_proyecto": next((p for p in cuaderno.proyectos() if p["id"] == proyecto), None)}
    if accion == "eliminar_proyecto_confirmado" and proyecto is not None:
        cuaderno.eliminar_proyecto(proyecto)
        return HttpResponseRedirect(reverse("calculadora:resoluciones") + "?hecho=proyecto_eliminado")
    if accion == "activar" and proyecto is not None:
        ejercicio = _entero(datos.get("ejercicio"))
        cuaderno.activar(proyecto, ejercicio)
        etiqueta = _nombre_de(cuaderno, ejercicio) if ejercicio else next(
            (p["nombre"] for p in cuaderno.proyectos() if p["id"] == proyecto), "")
        return _destino(request, _proyecto_url(proyecto), hecho="activado", ejercicio=etiqueta)
    if accion == "desactivar":
        cuaderno.activar(None)
        return _destino(request, volver_cuaderno, hecho="desactivado")

    # Ejercicios y secciones de un proyecto
    if accion == "crear_ejercicio":
        numero = _texto(datos.get("numero"), 20) or None
        if not nombre and not numero:
            return _destino(request, _proyecto_url(proyecto) if proyecto else volver_cuaderno, hecho="sin_nombre")
        enunciado = (datos.get("enunciado") or "").strip()[:MAX_ENUNCIADO] or None
        seccion = _entero(datos.get("seccion"))
        nuevo = cuaderno.crear_ejercicio(nombre, proyecto=proyecto, seccion=seccion, numero=numero, enunciado=enunciado)
        if proyecto is not None and datos.get("activar"):
            cuaderno.activar(proyecto, nuevo)
        etiqueta = organizacion.etiqueta({"numero": numero, "nombre": nombre})
        return _destino(request, _proyecto_url(proyecto, f"ejercicio-{nuevo}") if proyecto else volver_cuaderno,
                        hecho="ejercicio_creado", ejercicio=etiqueta)
    if accion == "crear_ejercicios" and proyecto is not None:
        desde, hasta = _entero(datos.get("desde"), 0), _entero(datos.get("hasta"), 0)
        if desde is None or hasta is None or not 0 <= hasta - desde < MAX_EJERCICIOS_DE_UNA_VEZ:
            return _destino(request, _proyecto_url(proyecto), hecho="rango_invalido")
        creados = cuaderno.crear_ejercicios(proyecto, [str(n) for n in range(desde, hasta + 1)], _entero(datos.get("seccion")))
        return _destino(request, _proyecto_url(proyecto), hecho="ejercicios_creados",
                        e=f"{creados} ejercicio{'s' if creados != 1 else ''}")
    if accion == "ordenar" and proyecto is not None:
        cuaderno.ordenar_por_numero(proyecto)
        return _destino(request, _proyecto_url(proyecto), hecho="ordenados")
    if accion == "crear_seccion" and proyecto is not None:
        if not nombre:
            return _destino(request, _proyecto_url(proyecto), hecho="sin_nombre")
        nueva = cuaderno.crear_seccion(proyecto, nombre)
        return _destino(request, _proyecto_url(proyecto, f"seccion-{nueva}"), hecho="seccion_creada", ejercicio=nombre)
    if accion == "editar_seccion" and identificador is not None and nombre:
        cuaderno.editar_seccion(identificador, nombre)
        return _destino(request, volver_cuaderno)
    if accion == "eliminar_seccion" and identificador is not None:
        cuaderno.eliminar_seccion(identificador)
        return _destino(request, volver_cuaderno, hecho="seccion_eliminada")
    return _destino(request, volver_cuaderno)


def _ubicar(cuaderno, ejercicio, ubicacion, anterior):
    """«s:<id>» sección del proyecto, «s:» sin sección, «p:<id>» otro proyecto, «independiente»."""
    tipo, _, valor = ubicacion.partition(":")
    if tipo == "independiente":
        if anterior["proyecto"] is not None:
            cuaderno.ubicar_ejercicios([ejercicio], None)
    elif tipo == "s" and anterior["proyecto"] is not None:
        seccion = _entero(valor)
        validas = {s["id"] for s in cuaderno.secciones(anterior["proyecto"])}
        seccion = seccion if seccion in validas else None
        if seccion != anterior["seccion"]:
            cuaderno.ubicar_ejercicios([ejercicio], anterior["proyecto"], seccion)
    elif tipo == "p" and _entero(valor) is not None and _entero(valor) != anterior["proyecto"]:
        if any(p["id"] == int(valor) for p in cuaderno.proyectos()):
            cuaderno.ubicar_ejercicios([ejercicio], int(valor))


def _hecho(datos):
    plantilla = HECHOS.get(datos.get("hecho", ""))
    if plantilla is None:
        return None
    n = _entero(datos.get("n")) or 0
    return plantilla.format(n=_cantidad(n), ejercicio=datos.get("ejercicio", "")[:MAX_NOMBRE],
                            e=datos.get("e", "")[:40])
