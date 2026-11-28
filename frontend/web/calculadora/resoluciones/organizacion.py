"""Proyectos del cuaderno listos para mostrar: árbol, progreso, mapa y borrador del documento.

Solo lee el almacén (metadatos y resúmenes, nunca documentos enteros). La futura exportación a
PDF recorrerá el mismo árbol con ``solo_incluidos=True`` y leerá cada documento por su id.
"""

from datetime import datetime

from .. import catalogo
from . import registro
from .almacen import AlmacenNoDisponible, almacen


def fecha(texto):
    try:
        return datetime.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


def etiqueta(ejercicio):
    """«Ejercicio 12 · Inversa de A», «Ejercicio 12» o el título solo."""
    numero, titulo = ejercicio.get("numero"), ejercicio.get("nombre") or ""
    if numero:
        return f"Ejercicio {numero} · {titulo}" if titulo else f"Ejercicio {numero}"
    return titulo or "Ejercicio sin título"


def corta(ejercicio):
    """Lo mínimo para un control estrecho: «Ej. 12» o el título."""
    return f"Ej. {ejercicio['numero']}" if ejercicio.get("numero") else (ejercicio.get("nombre") or "Ejercicio")


def preparar_resoluciones(filas):
    """Metadatos de cada resolución listos para la plantilla: fecha, herramienta, enlace y estado."""
    from .servicio import url_reabrir

    esquemas = {ruta: adaptador.esquema for ruta, adaptador in registro.ADAPTADORES.items()}
    for fila in filas:
        herramienta = catalogo.herramienta_por_id(fila["herramienta"])
        fila["fecha"] = fecha(fila["creado"])
        fila["herramienta_nombre"] = herramienta.nombre if herramienta else fila["herramienta"]
        fila["chip"] = herramienta.categoria.chip if herramienta else ""
        # El nombre por defecto ya empieza por la herramienta o su método: no se repite encima.
        fila["mostrar_herramienta"] = not fila["nombre"].startswith(fila["herramienta_nombre"])
        if fila["estado"] == "ok" and fila["ruta"] not in esquemas:
            fila["estado"] = "sin_herramienta"
        elif fila["estado"] == "ok" and fila["esquema"] != esquemas[fila["ruta"]]:
            fila["estado"] = "antiguo"
        fila["url"] = url_reabrir(fila["ruta"], fila["id"]) if fila["estado"] in ("ok", "antiguo") else None
    return filas


def arbol(proyecto, ejercicios, secciones, resoluciones, solo_incluidos=False):
    """Secciones (la primera, sin sección) con sus ejercicios y las resoluciones de cada uno, en orden."""
    por_ejercicio = {}
    for fila in sorted(resoluciones, key=lambda r: (r["posicion"], r["id"])):
        por_ejercicio.setdefault(fila["ejercicio"], []).append(fila)
    grupos = [{"seccion": None, "ejercicios": []}] + [{"seccion": s, "ejercicios": []} for s in secciones]
    indice = {s["id"]: grupo for s, grupo in zip(secciones, grupos[1:])}
    for ejercicio in ejercicios:
        propias = por_ejercicio.get(ejercicio["id"], [])
        ejercicio = ejercicio | {
            "etiqueta": etiqueta(ejercicio), "corta": corta(ejercicio),
            "resoluciones": [r for r in propias if r["incluir"]] if solo_incluidos else propias,
            "resuelto": bool(propias),
        }
        grupo = indice.get(ejercicio["seccion"], grupos[0])
        if solo_incluidos and not (ejercicio["incluir"] and (grupo["seccion"] is None or grupo["seccion"]["incluir"])):
            continue
        grupo["ejercicios"].append(ejercicio)
    secciones_visibles = grupos[1:]
    for posicion, grupo in enumerate(secciones_visibles):
        grupo["primera"], grupo["ultima"] = posicion == 0, posicion == len(secciones_visibles) - 1
    return [g for g in grupos if g["seccion"] is not None or g["ejercicios"]]


def progreso(ejercicios, objetivo):
    resueltos = sum(1 for e in ejercicios if e["resuelto"])
    total = max(objetivo or 0, len(ejercicios))
    return {"resueltos": resueltos, "total": total, "creados": len(ejercicios), "objetivo": objetivo,
            "porcentaje": round(100 * resueltos / total) if total else 0,
            "pendientes_por_crear": max((objetivo or 0) - len(ejercicios), 0)}


def borrador(grupos):
    """Lo que entraría hoy en el documento: secciones, ejercicios y resoluciones incluidos."""
    ejercicios = [e for g in grupos if g["seccion"] is None or g["seccion"]["incluir"] for e in g["ejercicios"]
                  if e["incluir"]]
    return {"ejercicios": len(ejercicios),
            "resoluciones": sum(1 for e in ejercicios for r in e["resoluciones"] if r["incluir"]),
            "sin_resolver": sum(1 for e in ejercicios if not e["resuelto"])}


def destinos(ejercicios, proyectos):
    """Ejercicios a los que llevar una resolución, agrupados: independientes y luego cada proyecto."""
    grupos = [("Ejercicios independientes", [e for e in ejercicios if e["proyecto"] is None])]
    grupos += [(p["nombre"], [e for e in ejercicios if e["proyecto"] == p["id"]]) for p in proyectos]
    for _, opciones in grupos:
        for ejercicio in opciones:
            ejercicio.setdefault("etiqueta", etiqueta(ejercicio))
    return [(nombre, opciones) for nombre, opciones in grupos if opciones]


def activo():
    """El proyecto y el ejercicio activos, con los ejercicios del proyecto para cambiar de uno a otro."""
    try:
        trabajo = almacen().trabajo_activo()
    except AlmacenNoDisponible:
        return None
    if trabajo is None:
        return None
    proyecto, ejercicios, ejercicio = trabajo
    for opcion in ejercicios:
        opcion["etiqueta"], opcion["corta"] = etiqueta(opcion), corta(opcion)
    return {"proyecto": proyecto, "ejercicios": ejercicios, "ejercicio": ejercicio}
