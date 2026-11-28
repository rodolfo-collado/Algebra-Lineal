"""Cuaderno de resoluciones: consultar, buscar, agrupar en ejercicios, renombrar y eliminar.

Solo lee metadatos y el resumen de cada documento; abrir una resolución es ir a su
herramienta con ?resolucion=<id> (el middleware la repone sin recalcular). Todo funciona
con formularios: resoluciones.js solo añade la barra de selección flotante.
"""

from collections import OrderedDict
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

from django.http import HttpResponseRedirect, QueryDict
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from . import catalogo
from .resoluciones import registro
from .resoluciones.almacen import MAX_NOMBRE, AlmacenFuturo, AlmacenNoDisponible, almacen
from .resoluciones.servicio import NO_DISPONIBLE, url_reabrir


FILTROS = ("q", "herramienta", "desde", "hasta")
# Herramientas desde las que empezar cuando el cuaderno está en blanco: una por área.
SUGERIDAS = ("determinantes", "matriz-inversa", "metodos-cerrados", "relaciones-conjuntos")
HECHOS = {
    "agrupadas": "Reuniste {n} en «{ejercicio}».",
    "sacadas": "Sacaste {n} de su ejercicio; ahora están sueltas.",
    "eliminadas": "Eliminaste {n} del cuaderno.",
    "renombrada": "Cambiaste el nombre de la resolución.",
    "ejercicio_renombrado": "Cambiaste el nombre del ejercicio.",
    "disuelto": "Desagrupaste el ejercicio; sus resoluciones siguen en el cuaderno.",
    "sin_seleccion": "Primero marca al menos una resolución.",
    "sin_nombre": "Escribe un nombre de al menos un carácter.",
}


def _fecha(texto):
    try:
        return datetime.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


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


def _resoluciones(filas):
    """Metadatos listos para la plantilla: fecha, herramienta, enlace y estado legible."""
    esquemas = {ruta: adaptador.esquema for ruta, adaptador in registro.ADAPTADORES.items()}
    for fila in filas:
        herramienta = catalogo.herramienta_por_id(fila["herramienta"])
        fila["fecha"] = _fecha(fila["creado"])
        fila["herramienta_nombre"] = herramienta.nombre if herramienta else fila["herramienta"]
        fila["chip"] = herramienta.categoria.chip if herramienta else ""
        # El nombre por defecto ya empieza por la herramienta o su método: no se repite encima.
        fila["mostrar_herramienta"] = not fila["nombre"].startswith(fila["herramienta_nombre"])
        if fila["estado"] == "ok" and fila["ruta"] not in esquemas:
            fila["estado"] = "sin_herramienta"
        elif fila["estado"] == "ok" and fila["esquema"] != esquemas[fila["ruta"]]:
            fila["estado"] = "antiguo"
        abrible = fila["estado"] in ("ok", "antiguo")
        fila["url"] = url_reabrir(fila["ruta"], fila["id"]) if abrible else None
    return filas


def _coincide(fila, consulta, ejercicio):
    if not consulta:
        return True
    textos = (fila["nombre"], fila.get("resumen") or "", fila["herramienta_nombre"], ejercicio or "")
    return all(any(termino in catalogo.normalizar(texto) for texto in textos) for termino in consulta)


def _filtrar(filas, filtros, nombres_ejercicios):
    consulta = catalogo.normalizar(filtros["q"]).split()
    desde, hasta = _dia(filtros["desde"]), _dia(filtros["hasta"])
    for fila in filas:
        dia = fila["fecha"].date() if fila["fecha"] else None
        if filtros["herramienta"] and fila["herramienta"] != filtros["herramienta"]:
            continue
        if (desde and (dia is None or dia < desde)) or (hasta and (dia is None or dia > hasta)):
            continue
        if _coincide(fila, consulta, nombres_ejercicios.get(fila["ejercicio"])):
            yield fila


def _cuaderno(filtros):
    """Ejercicios (con sus pasos en orden) y resoluciones sueltas agrupadas por día."""
    cuaderno = almacen()
    filas = _resoluciones(cuaderno.listar())
    ejercicios = cuaderno.ejercicios()
    nombres = {e["id"]: e["nombre"] for e in ejercicios}
    totales = {e["id"]: 0 for e in ejercicios}
    for fila in filas:
        if fila["ejercicio"] in totales:
            totales[fila["ejercicio"]] += 1
    visibles = list(_filtrar(filas, filtros, nombres))
    activo = any(filtros.values())

    hojas = []
    for ejercicio in ejercicios:
        pasos = sorted((f for f in visibles if f["ejercicio"] == ejercicio["id"]), key=lambda f: (f["creado"], f["id"]))
        if pasos or not activo:
            fechas = [f["fecha"] for f in pasos if f["fecha"]]
            hojas.append(ejercicio | {"pasos": pasos, "total": totales[ejercicio["id"]],
                                      "ultima": max(fechas) if fechas else _fecha(ejercicio["creado"])})
    # El ejercicio en el que se trabajó más recientemente, primero.
    hojas.sort(key=lambda h: h["ultima"] or datetime.min.replace(tzinfo=timezone.get_current_timezone()), reverse=True)

    hoy = timezone.localdate()
    dias = OrderedDict()
    for fila in visibles:
        if fila["ejercicio"] is None:
            dia = fila["fecha"].date() if fila["fecha"] else None
            dias.setdefault(dia, []).append(fila)
    sueltas = [{"dia": dia, "rotulo": _rotulo_dia(dia, hoy), "resoluciones": grupo} for dia, grupo in dias.items()]

    herramientas = sorted({(f["herramienta"], f["herramienta_nombre"]) for f in filas}, key=lambda h: h[1])
    return {
        "ejercicios": hojas, "sueltas": sueltas, "total": len(filas), "visibles": len(visibles),
        "total_ejercicios": len(ejercicios), "herramientas": herramientas, "filtrando": activo,
        "todos_los_ejercicios": ejercicios, "apartado": cuaderno.apartado,
    }


def _filtros(datos):
    return {clave: datos.get(clave, "").strip()[:MAX_NOMBRE] for clave in FILTROS}


def _volver(filtros, **extra):
    consulta = urlencode({clave: valor for clave, valor in (filtros | extra).items() if valor})
    destino = reverse("calculadora:resoluciones")
    return f"{destino}?{consulta}" if consulta else destino


def _ids(datos):
    ids = []
    for valor in datos.getlist("ids"):
        try:
            ids.append(int(valor))
        except ValueError:
            continue
    return ids


def _entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _cantidad(n):
    return "1 resolución" if n == 1 else f"{n} resoluciones"


def _agrupar(cuaderno, ids, datos):
    """Destino elegido: un ejercicio existente o uno nuevo con el nombre escrito (o «Ejercicio N»)."""
    destino = _entero(datos.get("ejercicio"))
    if destino is None or not cuaderno.existe_ejercicio(destino):
        nombre = " ".join(datos.get("nombre_ejercicio", "").split())
        nombre = nombre or f"Ejercicio {len(cuaderno.ejercicios()) + 1}"
        destino = cuaderno.crear_ejercicio(nombre)
    cuaderno.agrupar(ids, destino)
    return destino, next(e["nombre"] for e in cuaderno.ejercicios() if e["id"] == destino)


def _accion(request, filtros):
    """Aplica la acción del POST; devuelve la respuesta o el contexto de una confirmación."""
    cuaderno, datos = almacen(), request.POST
    accion, ids = datos.get("accion", ""), _ids(datos)
    if accion in ("agrupar", "sacar", "eliminar", "eliminar_confirmado") and not ids:
        return HttpResponseRedirect(_volver(filtros, hecho="sin_seleccion"))
    if accion == "agrupar":
        destino, nombre = _agrupar(cuaderno, ids, datos)
        if datos.get("volver") == "herramienta" and len(ids) == 1:
            ficha = cuaderno.obtener(ids[0], documento=False)
            enlace = ficha and url_reabrir(ficha["ruta"], ficha["id"])
            if enlace:
                return HttpResponseRedirect(enlace)
        return HttpResponseRedirect(
            _volver(filtros, hecho="agrupadas", n=len(ids), ejercicio=nombre) + f"#ejercicio-{destino}")
    if accion == "sacar":
        cuaderno.agrupar(ids, None)
        return HttpResponseRedirect(_volver(filtros, hecho="sacadas", n=len(ids)))
    if accion == "eliminar":
        # Primero se confirma: eliminar no se puede deshacer.
        return {"confirmar": [f for f in cuaderno.listar() if f["id"] in ids]}
    if accion == "eliminar_confirmado":
        cuaderno.eliminar(ids)
        return HttpResponseRedirect(_volver(filtros, hecho="eliminadas", n=len(ids)))
    nombre = " ".join(datos.get("nombre", "").split())
    identificador = _entero(datos.get("id"))
    if accion in ("renombrar", "renombrar_ejercicio") and not nombre:
        return HttpResponseRedirect(_volver(filtros, hecho="sin_nombre"))
    if accion == "renombrar" and identificador is not None:
        cuaderno.renombrar(identificador, nombre)
        return HttpResponseRedirect(_volver(filtros, hecho="renombrada") + f"#resolucion-{identificador}")
    if accion == "renombrar_ejercicio" and identificador is not None:
        cuaderno.renombrar_ejercicio(identificador, nombre)
        return HttpResponseRedirect(_volver(filtros, hecho="ejercicio_renombrado") + f"#ejercicio-{identificador}")
    if accion == "disolver" and identificador is not None:
        cuaderno.disolver_ejercicio(identificador)
        return HttpResponseRedirect(_volver(filtros, hecho="disuelto"))
    return HttpResponseRedirect(_volver(filtros))


def _hecho(datos):
    plantilla = HECHOS.get(datos.get("hecho", ""))
    if plantilla is None:
        return None
    n = _entero(datos.get("n")) or 0
    return plantilla.format(n=_cantidad(n), ejercicio=datos.get("ejercicio", "")[:MAX_NOMBRE])


@require_http_methods(["GET", "POST"])
def resoluciones(request):
    # Los filtros viajan en la URL; en un POST, en un campo oculto con la consulta de la página.
    filtros = _filtros(request.GET if request.method == "GET" else QueryDict(request.POST.get("filtros", "")))
    contexto = {"filtros": filtros, "consulta_filtros": urlencode({k: v for k, v in filtros.items() if v}),
                "hecho": _hecho(request.GET), "max_nombre": MAX_NOMBRE,
                "sugeridas": [h for h in map(catalogo.herramienta_por_id, SUGERIDAS) if h and h.disponible],
                "pagina_resoluciones": True,
                "migas": (catalogo.Miga("Inicio", reverse("calculadora:inicio")), catalogo.Miga("Resoluciones", actual=True))}
    try:
        if request.method == "POST":
            resultado = _accion(request, filtros)
            if not isinstance(resultado, dict):
                return resultado
            contexto.update(resultado)
        contexto.update(_cuaderno(filtros))
    except AlmacenNoDisponible as error:
        contexto["no_disponible"] = str(error) if isinstance(error, AlmacenFuturo) else NO_DISPONIBLE
    return TemplateResponse(request, "calculadora/pages/resoluciones.html", contexto,
                  status=503 if "no_disponible" in contexto else 200)
