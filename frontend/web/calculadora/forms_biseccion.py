"""Campos esenciales y ajustes opcionales, con el contrato HTTP habitual."""

from django import forms
from backend.biseccion import PRECISION, MAX_ITERACIONES
from backend.funciones_reales import FuncionReal
from .forms_feedback import FormularioConErrores


EJEMPLO = "x^4 - 5x^3 + 0.5x^2 - 11x + 10"


class BiseccionForm(FormularioConErrores):
    funcion = forms.CharField(label="Función f(x)", max_length=512, initial=EJEMPLO,
                              widget=forms.TextInput(attrs={"class": "field-input", "spellcheck": "false",
                                                            "aria-describedby": "funcion-ayuda"}))
    a = forms.FloatField(label="Extremo a", initial=.55,
                         widget=forms.NumberInput(attrs={"class": "field-input", "step": "any"}))
    b = forms.FloatField(label="Extremo b", initial=1.1,
                         widget=forms.NumberInput(attrs={"class": "field-input", "step": "any"}))
    precision = forms.FloatField(label="Precisión del intervalo", initial=PRECISION, required=False,
                                 max_value=PRECISION,
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
        permitidos = {"csrfmiddlewaretoken", *self.fields}
        if set(self.data) - permitidos:
            self.add_error(None, "El envío incluye campos que no forman parte del formulario.")
        if hasattr(self.data, "getlist") and any(len(self.data.getlist(n)) > 1 for n in self.data):
            self.add_error(None, "Envía un único valor por campo; hay campos repetidos.")
        if datos.get("precision") is None:
            datos["precision"] = PRECISION
        if not 0 < datos["precision"] <= PRECISION:
            self.add_error("precision", "La precisión debe ser positiva y no mayor que 0.0001.")
        if datos.get("max_iteraciones") is None:
            datos["max_iteraciones"] = MAX_ITERACIONES
        if "a" in datos and "b" in datos and datos["a"] >= datos["b"]:
            self.add_error("b", "El extremo b debe ser mayor que a.")
        return datos
