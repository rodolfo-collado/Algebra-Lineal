"""Formulario de la conversión entre números arábigos y romanos."""

from django import forms

from backend.sistemas_numericos import LONGITUD_ROMANA_MAXIMA


class ConversionRomanosForm(forms.Form):
    """La dirección de la conversión y un único número.

    Como en Conversión de bases, el contrato HTTP es estricto: un campo ajeno
    o repetido se rechaza con un mensaje propio. El número se valida en el
    backend al convertir; aquí solo se acota su longitud.
    """

    # Los valores conservan los nombres del backend; la interfaz dice «arábigo».
    DIRECCIONES = (
        ("decimal_a_romano", "Arábigo → romano"),
        ("romano_a_decimal", "Romano → arábigo"),
    )
    CAMPOS_PERMITIDOS = frozenset({"csrfmiddlewaretoken", "direccion", "numero"})

    direccion = forms.ChoiceField(
        label="Dirección",
        choices=DIRECCIONES,
        initial="decimal_a_romano",
        widget=forms.RadioSelect,
        error_messages={
            "required": "Elige la dirección de la conversión.",
            "invalid_choice": "Elige una dirección válida: Arábigo → romano o Romano → arábigo.",
        },
    )
    numero = forms.CharField(
        label="Número",
        required=False,
        max_length=LONGITUD_ROMANA_MAXIMA,
        error_messages={
            "max_length": f"El número no puede tener más de {LONGITUD_ROMANA_MAXIMA} caracteres.",
        },
        widget=forms.TextInput(
            attrs={
                "class": "field-input field-input-numeral",
                "autocomplete": "off",
                "autocapitalize": "characters",
                "spellcheck": "false",
                "aria-describedby": "numero-ayuda",
            }
        ),
    )

    def clean(self):
        datos = super().clean()
        if set(self.data) - self.CAMPOS_PERMITIDOS:
            self.add_error(None, "El envío incluye campos que no forman parte del formulario.")
        if hasattr(self.data, "getlist") and any(len(self.data.getlist(nombre)) > 1 for nombre in self.data):
            self.add_error(None, "Envía un único valor por campo; hay campos repetidos.")
        return datos
