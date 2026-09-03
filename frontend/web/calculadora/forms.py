"""Formularios de entrada de la interfaz Django."""

from django import forms


class SistemaForm(forms.Form):
    METODOS = (
        ("gauss", "Gauss"),
        ("gauss_jordan", "Gauss-Jordan"),
    )

    metodo = forms.ChoiceField(
        label="Método",
        choices=METODOS,
        initial="gauss_jordan",
        widget=forms.RadioSelect,
    )
    sistema = forms.CharField(
        label="Sistema de ecuaciones",
        strip=True,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "placeholder": (
                    "x1+2x2-x3=4;\n"
                    "2x1-x2+3x3=7;\n"
                    "x1+x2+x3=6"
                ),
                "spellcheck": "false",
            }
        ),
        error_messages={"required": "Ingresa un sistema de ecuaciones."},
    )
