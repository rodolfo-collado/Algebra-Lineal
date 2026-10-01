"""Entrada de «Matriz inversa»: una matriz cuadrada A y el método.

A es n×n, así que la estructura es un solo número (filas y columnas). Comparte
con las demás herramientas de matrices las celdas, el parser y el contrato HTTP
estricto de `FormularioCeldas`. El método para matrices 2×2 solo está
disponible cuando n = 2: sin esa dimensión su radio se dibuja desactivado y el
servidor rechaza un envío manipulado.
"""

from django import forms

from backend.matriz_inversa import DIRECTO_2X2, GAUSS_JORDAN, METODO_PREDETERMINADO

from .forms_matrices import FormularioCeldas, campo_dimension
from .servicios_inversa import METODOS


class RadioConInactivas(forms.RadioSelect):
    """RadioSelect que desactiva opciones concretas: una opción desactivada no viaja en el POST."""

    inactivas = frozenset()

    def create_option(self, name, value, *args, **kwargs):
        opcion = super().create_option(name, value, *args, **kwargs)
        if value in self.inactivas:
            opcion["attrs"]["disabled"] = True
        return opcion


class InversaForm(FormularioCeldas):
    orden = campo_dimension("Filas y columnas")
    metodo = forms.ChoiceField(
        label="Método", choices=METODOS, initial=METODO_PREDETERMINADO, widget=RadioConInactivas,
        error_messages={"required": "Selecciona un método.", "invalid_choice": "Selecciona un método válido."},
    )
    verificar = forms.BooleanField(
        label="Verificar el resultado", required=False, initial=False,
        help_text="Comprueba que A·A⁻¹ y A⁻¹·A producen la matriz identidad.",
        widget=forms.CheckboxInput(attrs={"aria-describedby": "inverse-verification-help"}),
    )
    # Firma que envía «Continuar» cuando un cálculo largo pidió confirmación; la comprueba el servicio.
    confirmacion = forms.CharField(required=False, strip=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orden = self._valor_seguro("orden")
        self.estructura = {"orden": orden, "metodo": self._valor_seguro("metodo")}
        self.metodo_2x2_disponible = orden == 2
        if not self.metodo_2x2_disponible:
            self.fields["metodo"].widget.inactivas = frozenset({DIRECTO_2X2})
            # Al pasar a otro tamaño con Aplicar se vuelve al método general.
            if self.estructura["metodo"] == DIRECTO_2X2:
                self.estructura["metodo"] = GAUSS_JORDAN
        self.generar_celdas("A", orden, orden)

    @property
    def forma_texto(self):
        orden = self.estructura["orden"]
        return f"A es {orden}×{orden}"

    def clean(self):
        datos = super().clean()
        self.rechazar_campos_repetidos()
        if self.errors or self.ajustar:
            return datos

        if not self.celdas_coinciden():
            self.add_error(None, "Las celdas recibidas no coinciden con el tamaño de A. Pulsa Aplicar para ajustar la estructura.")
            return datos
        if datos["metodo"] == DIRECTO_2X2 and not self.metodo_2x2_disponible:
            self.add_error("metodo", "El método para matrices 2×2 solo se puede usar cuando A es 2×2.")
            return datos

        self.convertir_numeros(datos, self.nombres_celdas)
        if self.errors:
            return datos

        orden = self.estructura["orden"]
        datos["entrada"] = {
            "a": self.leer_matriz(datos, "A", orden, orden),
            "metodo": datos["metodo"], "verificar": datos["verificar"],
        }
        return datos

    def iniciales(self):
        """Conserva las celdas que sobreviven a Aplicar; la estructura ya está saneada."""
        iniciales = {nombre: self.data.get(nombre, "") for nombre in self.fields if nombre != "confirmacion"}
        iniciales.update(self.estructura)
        iniciales["verificar"] = self.cleaned_data["verificar"]
        return iniciales
