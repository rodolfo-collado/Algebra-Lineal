"""Contexto de navegación derivado del registro central y de la ruta activa."""

from . import catalogo


def navegacion(request):
    """Sidebar, breadcrumbs y relacionadas sin que cada vista los arme a mano."""
    herramienta = catalogo.herramienta_por_ruta(getattr(request, "resolver_match", None))
    return {
        "arbol_navegacion": catalogo.arbol(),
        "herramienta_actual": herramienta,
        "categoria_actual": herramienta.categoria if herramienta else None,
        "migas": catalogo.migas(herramienta),
        "herramientas_relacionadas": (
            catalogo.relacionadas_disponibles(herramienta) if herramienta else ()
        ),
    }
