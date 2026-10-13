"""Entrada de Determinantes: A cuadrada, el método y, para Cofactores, la fila o columna.

La disponibilidad de cada método depende solo del tamaño de A: la fórmula
directa existe para 2×2, Sarrus para 3×3 y Cofactores hasta 6×6. Aplicar
conserva las celdas supervivientes; Calcular exige exactamente esa estructura.
"""

from django import forms

from backend.determinantes import ORDEN_EXIGIDO, ORDEN_MAXIMO_COFACTORES

from .forms_matrices import FormularioCeldas, campo_dimension
from .opciones_matrices import DIMENSION_MAXIMA, DIMENSION_MINIMA

METODOS = (
    ("directo_2x2", "Fórmula directa 2×2"),
    ("sarrus", "Regla de Sarrus"),
    ("cofactores", "Cofactores"),
    ("lu", "Factorización LU"),
    ("reduccion", "Reducción por filas"),
)


def metodo_disponible(metodo, orden):
    if metodo not in dict(METODOS):
        return False
    if metodo in ORDEN_EXIGIDO:
        return ORDEN_EXIGIDO[metodo] == orden
    return metodo != "cofactores" or orden <= ORDEN_MAXIMO_COFACTORES


def metodo_sugerido(orden):
    """Valor inicial por tamaño, independiente de la recomendación para los valores de A."""
    for metodo, exigido in ORDEN_EXIGIDO.items():
        if exigido == orden:
            return metodo
    return "cofactores" if orden <= ORDEN_MAXIMO_COFACTORES else "reduccion"


def opciones_expansion(orden):
    return [("auto", "Automático"), *((f"fila_{i}", f"Fila {i}") for i in range(1, orden + 1)),
            *((f"columna_{j}", f"Columna {j}") for j in range(1, orden + 1))]


class RadiosPorTamano(forms.RadioSelect):
    """Desactiva (y la plantilla oculta) los métodos que no existen para el tamaño de A."""

    orden = None

    def create_option(self, *args, **kwargs):
        opcion = super().create_option(*args, **kwargs)
        metodo = opcion["value"]
        opcion["attrs"]["data-sugerido"] = ",".join(
            str(n) for n in range(DIMENSION_MINIMA, DIMENSION_MAXIMA + 1) if metodo_sugerido(n) == metodo
        )
        if metodo in ORDEN_EXIGIDO:
            opcion["attrs"]["data-orden"] = ORDEN_EXIGIDO[metodo]
        elif metodo == "cofactores":
            opcion["attrs"]["data-orden-maximo"] = ORDEN_MAXIMO_COFACTORES
        if not metodo_disponible(metodo, self.orden):
            opcion["attrs"]["disabled"] = True
        return opcion


class DeterminantesForm(FormularioCeldas):
    orden = campo_dimension("Filas y columnas")
    metodo = forms.ChoiceField(
        label="Método", choices=METODOS, widget=RadiosPorTamano,
        error_messages={"required": "Selecciona un método.", "invalid_choice": "Selecciona un método válido."},
    )
    expansion = forms.ChoiceField(
        label="Desarrollar por", required=False,
        widget=forms.Select(attrs={"class": "field-select", "aria-describedby": "expansion-help"}),
        error_messages={"invalid_choice": "Selecciona una fila o columna existente."},
    )
    # Firma que envía «Continuar» cuando un cálculo largo pidió confirmación; la comprueba el servicio.
    confirmacion = forms.CharField(required=False, strip=False)
    eleccion = forms.CharField(required=False, strip=False, widget=forms.HiddenInput)

    def __init__(self, *args, elegir=False, **kwargs):
        super().__init__(*args, **kwargs)
        orden = self._valor_seguro("orden")
        self.fields["metodo"].required = elegir
        self.fields["metodo"].choices = [(m, titulo) for m, titulo in METODOS if metodo_disponible(m, orden)]
        self.fields["expansion"].choices = opciones_expansion(orden)
        self.fields["metodo"].widget.orden = orden
        if self.is_bound and not elegir:
            # Una A nueva se analiza antes de aceptar una elección de método.
            self.data = self.data.copy()
            self.data["metodo"] = ""
            self.data["expansion"] = "auto"
        self.estructura = {"orden": orden, "metodo": self._valor_seguro("metodo")}
        self.generar_celdas("A", orden, orden)

    @property
    def forma_texto(self):
        orden = self.estructura["orden"]
        return f"A es {orden}×{orden}"

    def clean(self):
        datos = super().clean()
        self.rechazar_campos_repetidos()
        if self.ajustar or self.errors.get("orden") or self.non_field_errors():
            return datos
        orden = self.estructura["orden"]
        if not self.celdas_coinciden():
            self.grupo_error = "determinant-matrix"
            self.add_error(None, "Las celdas recibidas no coinciden con el tamaño de A. Pulsa Aplicar para ajustar la estructura.")
            return datos
        self.convertir_numeros(datos, self.nombres_celdas)
        if not any(nombre in self.errors for nombre in self.nombres_celdas):
            metodo = datos.get("metodo", "")
            datos["entrada"] = {
                "a": self.leer_matriz(datos, "A", orden, orden), "metodo": metodo,
                "expansion": (datos.get("expansion") or "auto") if metodo == "cofactores" else "auto",
            }
        return datos

    def iniciales(self):
        """Conserva las celdas que sobreviven a Aplicar; método y expansión ya están saneados."""
        iniciales = {nombre: self.data.get(nombre, "") for nombre in self.fields if nombre not in ("confirmacion", "eleccion")}
        iniciales.update(self.estructura)
        iniciales["expansion"] = self.data.get("expansion") or "auto"
        return iniciales
