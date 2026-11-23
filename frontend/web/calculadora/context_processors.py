"""Contexto de navegación derivado del registro central y de la ruta activa."""

from functools import lru_cache

from django.conf import settings

from actualizador import versiones

from . import catalogo, preferencias


@lru_cache(maxsize=1)
def _version():
    """Versión instalada: no cambia mientras la app corre (actualizar exige reiniciarla)."""
    try:
        return versiones.version_instalada()
    except (OSError, KeyError, ValueError):
        return ""


def navegacion(request):
    """Sidebar, breadcrumbs y relacionadas sin que cada vista los arme a mano."""
    ruta = getattr(request, "resolver_match", None)
    herramienta = catalogo.herramienta_por_ruta(ruta)
    pagina = getattr(ruta, "url_name", None)
    area_actual_id = (
        herramienta.categoria.area.id if herramienta
        else ruta.kwargs.get("area") if pagina == "area" else None
    )
    # Posición del enlace activo en la navegación por áreas (Inicio es 0): la muesca de BelugaCalc.
    navegables = [area.id for area in catalogo.AREAS if area.disponible]
    indice_area = 0 if pagina == "inicio" else (
        navegables.index(area_actual_id) + 1 if area_actual_id in navegables else None
    )
    hermanas = catalogo.hermanas(herramienta) if herramienta else ()
    return {
        # Solo hay a dónde moverse si el área tiene más de una herramienta disponible.
        "herramientas_hermanas": hermanas if sum(len(h) for _, h in hermanas) > 1 else (),
        "arbol_navegacion": catalogo.arbol(),
        "datos_buscador": catalogo.datos_buscador(),
        "herramienta_actual": herramienta,
        "categoria_actual": herramienta.categoria if herramienta else None,
        # Navegación por áreas de los temas homenaje: Inicio, la página de un área o su herramienta.
        "en_inicio": pagina == "inicio",
        "area_actual_id": area_actual_id,
        "indice_area": indice_area,
        "migas": catalogo.migas(herramienta),
        "version_pygebra": _version(),
        "herramientas_relacionadas": (
            catalogo.relacionadas_disponibles(herramienta) if herramienta else ()
        ),
    }


def escritorio(request):
    """Señal de la app de escritorio y sus preferencias guardadas; nada en la web."""
    if not settings.DESKTOP_MODE:
        return {}
    return {"escritorio": True, "preferencias_guardadas": preferencias.leer()}
