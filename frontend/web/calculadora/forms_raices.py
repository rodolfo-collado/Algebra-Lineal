"""Función, intervalo y ajustes que comparten los métodos cerrados de raíces."""

from django import forms
from backend.metodos_cerrados import MAX_ITERACIONES, TOLERANCIA
from backend.funciones_reales import FuncionReal
from .forms_feedback import FormularioConErrores


class RaicesForm(FormularioConErrores):
    # Cada método nombra qué mide su tolerancia; el campo HTTP se llama igual en todos.
    magnitud, etiqueta = "tolerancia", "Tolerancia"

    def __init__(self, *args, explorar=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.explorar = explorar
        self.fields["precision"].label = self.etiqueta
        if explorar:
            self.fields["a"].required = self.fields["b"].required = False

    funcion = forms.CharField(label="Función f(x)", max_length=512,
                              widget=forms.TextInput(attrs={"class": "field-input", "spellcheck": "false",
                                                            "aria-describedby": "funcion-ayuda"}))
    a = forms.FloatField(label="Extremo a",
                         widget=forms.NumberInput(attrs={"class": "field-input", "step": "any"}))
    b = forms.FloatField(label="Extremo b",
                         widget=forms.NumberInput(attrs={"class": "field-input", "step": "any"}))
    precision = forms.FloatField(initial=TOLERANCIA, required=False, max_value=TOLERANCIA,
                                 widget=forms.NumberInput(attrs={"class": "field-input", "step": "any",
                                                                 "aria-describedby": "precision-ayuda"}))
    max_iteraciones = forms.IntegerField(label="Máximo de iteraciones", initial=MAX_ITERACIONES,
                                         min_value=1, max_value=1000, required=False,
                                         widget=forms.NumberInput(attrs={"class": "field-input"}))

    def clean_funcion(self):
        texto = self.cleaned_data["funcion"]
        try:
            self.funcion_real = FuncionReal(texto)
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error
        return texto

    def clean(self):
        datos = super().clean()
        if self.explorar:
            for nombre, valor in (("a", -10.), ("b", 10.)):
                if datos.get(nombre) is None:
                    datos[nombre] = valor
        permitidos = {"csrfmiddlewaretoken", *self.fields}
        if set(self.data) - permitidos:
            self.add_error(None, "El envío incluye campos que no forman parte del formulario.")
        if hasattr(self.data, "getlist") and any(len(self.data.getlist(n)) > 1 for n in self.data):
            self.add_error(None, "Envía un único valor por campo; hay campos repetidos.")
        if datos.get("precision") is None:
            datos["precision"] = TOLERANCIA
        if not 0 < datos["precision"] <= TOLERANCIA:
            self.add_error("precision", f"La {self.magnitud} debe ser positiva y no mayor que 0.0001.")
        if datos.get("max_iteraciones") is None:
            datos["max_iteraciones"] = MAX_ITERACIONES
        if "a" in datos and "b" in datos and datos["a"] >= datos["b"]:
            self.add_error("b", "El extremo b debe ser mayor que a.")
        return datos


class BiseccionForm(RaicesForm):
    magnitud, etiqueta = "precisión", "Precisión del intervalo"


class ReglaFalsaForm(RaicesForm):
    magnitud, etiqueta = "tolerancia", "Tolerancia del error absoluto"


class NewtonRaphsonForm(RaicesForm):
    a = b = None
    etiqueta = "Tolerancia del cambio y del residuo"
    x0 = forms.FloatField(label="Aproximación inicial x₀",
        widget=forms.NumberInput(attrs={"class": "field-input", "step": "any"}))
