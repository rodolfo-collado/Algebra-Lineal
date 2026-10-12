"""Determinante mediante la reducción de Gauss existente y sus correcciones exactas."""

from backend.gauss import aplicar_gauss

from .comun import determinante_desde_reduccion, preparar, producto


def reduccion(a):
    """Triangulariza A con Gauss y corrige sus intercambios y normalizaciones.

    Gauss normaliza cada pivote, así que la diagonal de U solo tiene unos (o un
    cero si A es singular): multiplicarla no basta. Devuelve `u`, `pasos`
    (cada uno con su `correccion_determinante` cuando la hay), `diagonal`,
    `producto_diagonal` y `determinante`.
    """
    a = preparar(a)
    u, pasos, _ = aplicar_gauss(a)
    diagonal = [u[i][i] for i in range(len(a))]
    return {"u": u, "pasos": pasos, "diagonal": diagonal,
            "producto_diagonal": producto(diagonal),
            "determinante": determinante_desde_reduccion(pasos, diagonal)}
