"""Paso de A de Determinantes a Matriz inversa con un POST efímero.

No hay sesión ni almacenamiento: Determinantes escribe A en campos ocultos y
Matriz inversa la valida con su propio formulario y solo la carga, sin calcular.
"""

from .forms_inversa import InversaForm


def campos_matriz(a):
    """Pares (nombre, valor) del formulario: el orden y cada celda como fracción exacta."""
    return [("orden", str(len(a))), *[
        (f"celda_A_{i}_{j}", str(v)) for i, fila in enumerate(a) for j, v in enumerate(fila)
    ]]


def recibir_matriz(post):
    """Valida A con InversaForm; devuelve el formulario con A cargada o con sus errores."""
    datos = post.copy()
    datos.pop("cargar_matriz", None)
    # Llega sin método: Gauss-Jordan sirve para cualquier tamaño (en 2×2 se puede cambiar después).
    datos["metodo"] = "gauss_jordan"
    form = InversaForm(datos)
    if not form.is_valid():
        return form
    return InversaForm(initial=dict(campos_matriz(form.cleaned_data["entrada"]["a"])))
