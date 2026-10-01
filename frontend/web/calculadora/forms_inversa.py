"""Entrada cuadrada de la inversa y una única propiedad o aplicación opcional.

La estructura de A determina también B o b cuando la función elegida los
necesita. Aplicar conserva las celdas supervivientes sin efectuar cálculos;
Calcular exige exactamente los campos de esa estructura.
"""

from django import forms

from backend.matriz_inversa import DIRECTO_2X2, GAUSS_JORDAN, METODO_PREDETERMINADO

from .forms_matrices import FormularioCeldas, campo_dimension
from .servicios_inversa import FUNCIONES_ADICIONALES, METODOS


class InversaForm(FormularioCeldas):
    orden = campo_dimension("Filas y columnas")
    metodo = forms.ChoiceField(
        label="Método", choices=METODOS, initial=METODO_PREDETERMINADO, widget=forms.RadioSelect,
        error_messages={"required": "Selecciona un método.", "invalid_choice": "Selecciona un método válido."},
    )
    verificar = forms.BooleanField(
        label="Verificar el resultado", required=False, initial=False,
        help_text="Comprueba que A·A⁻¹ y A⁻¹·A producen la matriz identidad.",
        widget=forms.CheckboxInput(attrs={"aria-describedby": "inverse-verification-help"}),
    )
    funcion_adicional = forms.ChoiceField(
        label="Aplicaciones y propiedades", choices=FUNCIONES_ADICIONALES, initial="ninguna",
        widget=forms.RadioSelect,
        error_messages={
            "required": "Selecciona una función adicional válida.",
            "invalid_choice": "Selecciona una función adicional válida.",
        },
    )
    # Firma que envía «Continuar» cuando un cálculo largo pidió confirmación; la comprueba el servicio.
    confirmacion = forms.CharField(required=False, strip=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound and "funcion_adicional" not in self.data:
            # Un formulario anterior sigue representando el modo principal;
            # también debe aparecer seleccionado al volver a mostrar el POST.
            self.data = self.data.copy()
            self.data["funcion_adicional"] = "ninguna"
        orden = self._valor_seguro("orden")
        self.estructura = {
            "orden": orden, "metodo": self._valor_seguro("metodo"),
            "funcion_adicional": self._valor_seguro("funcion_adicional"),
        }
        self.metodo_2x2_disponible = orden == 2
        # Fuera de 2×2 no existe una decisión de método: un POST sin el campo
        # usa Gauss-Jordan. Un método directo manipulado sigue siendo inválido.
        self.fields["metodo"].required = self.metodo_2x2_disponible and not self.ajustar
        if not self.metodo_2x2_disponible:
            self.estructura["metodo"] = GAUSS_JORDAN
        self.generar_celdas("A", orden, orden)
        funcion = self.estructura["funcion_adicional"]
        if funcion == "producto":
            self.generar_celdas("B", orden, orden)
        elif funcion == "vector":
            self.generar_celdas("b", orden, 1, vector=True)

    @property
    def forma_texto(self):
        orden = self.estructura["orden"]
        return f"A es {orden}×{orden}"

    def clean(self):
        datos = super().clean()
        self.rechazar_campos_repetidos()
        if self.errors:
            return datos

        datos["funcion_adicional"] = datos.get("funcion_adicional") or "ninguna"
        if not self.metodo_2x2_disponible:
            if datos.get("metodo") == DIRECTO_2X2 and not self.ajustar:
                self.add_error("metodo", "El método para matrices 2×2 solo se puede usar cuando A es 2×2.")
                return datos
            datos["metodo"] = GAUSS_JORDAN
        if self.ajustar:
            datos["metodo"] = datos.get("metodo") or GAUSS_JORDAN
            return datos

        if not self.celdas_coinciden():
            self.add_error(None, "Las celdas recibidas no coinciden con el tamaño de A y la función adicional elegida. Pulsa Aplicar para ajustar la estructura.")
            return datos

        self.convertir_numeros(datos, self.nombres_celdas)
        if self.errors:
            return datos

        orden = self.estructura["orden"]
        datos["entrada"] = {
            "a": self.leer_matriz(datos, "A", orden, orden),
            "metodo": datos["metodo"], "verificar": datos["verificar"],
            "funcion_adicional": datos["funcion_adicional"],
        }
        if datos["funcion_adicional"] == "producto":
            datos["entrada"]["b"] = self.leer_matriz(datos, "B", orden, orden)
        elif datos["funcion_adicional"] == "vector":
            datos["entrada"]["vector"] = [fila[0] for fila in self.leer_matriz(datos, "b", orden, 1)]
        return datos

    def iniciales(self):
        """Conserva las celdas que sobreviven a Aplicar; la estructura ya está saneada."""
        iniciales = {nombre: self.data.get(nombre, "") for nombre in self.fields if nombre != "confirmacion"}
        iniciales.update(self.estructura)
        iniciales["verificar"] = self.cleaned_data["verificar"]
        return iniciales
