"""Contexto de navegación derivado del registro central y de la ruta activa."""

from django.conf import settings

from . import catalogo, preferencias


def navegacion(request):
    """Sidebar, breadcrumbs y relacionadas sin que cada vista los arme a mano."""
    herramienta = catalogo.herramienta_por_ruta(getattr(request, "resolver_match", None))
    hermanas = catalogo.hermanas(herramienta) if herramienta else ()
    return {
        # Solo hay a dónde moverse si el área tiene más de una herramienta disponible.
        "herramientas_hermanas": hermanas if sum(len(h) for _, h in hermanas) > 1 else (),
        "arbol_navegacion": catalogo.arbol(),
        "datos_buscador": catalogo.datos_buscador(),
        "herramienta_actual": herramienta,
        "categoria_actual": herramienta.categoria if herramienta else None,
        "migas": catalogo.migas(herramienta),
        "herramientas_relacionadas": (
            catalogo.relacionadas_disponibles(herramienta) if herramienta else ()
        ),
    }


def escritorio(request):
    """Señal de la app de escritorio y sus preferencias guardadas; nada en la web."""
    if not settings.DESKTOP_MODE:
        return {}
    return {"escritorio": True, "preferencias_guardadas": preferencias.leer()}
