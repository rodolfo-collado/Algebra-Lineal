"""Presentación compartida de errores; conserva la validación de cada formulario."""

from django import forms
from django.forms.boundfield import BoundField
from django.forms.utils import ErrorList


class CampoConErrores(BoundField):
    def build_widget_attrs(self, attrs, widget=None):
        widget = widget or self.field.widget
        attrs = super().build_widget_attrs(attrs, widget)
        if self.errors and not widget.is_hidden:
            ids = dict.fromkeys((widget.attrs.get("aria-describedby", "") + " " +
                                 attrs.get("aria-describedby", "")).split())
            ids[f"{self.auto_id}_error"] = None
            attrs["aria-describedby"] = " ".join(ids)
        return attrs


class ErroresFormulario(ErrorList):
    template_name = "calculadora/components/errores_campo.html"


class FormularioConErrores(forms.Form):
    bound_field_class = CampoConErrores

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("error_class", ErroresFormulario)
        # Las etiquetas no llevan «:» automático; el texto de cada una decide su puntuación.
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
