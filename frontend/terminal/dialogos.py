"""Preguntas de terminal y su correspondencia con los controles compartidos."""

from dataclasses import dataclass

from django import forms

from frontend.web.calculadora.forms import ConversionBasesForm
from frontend.web.calculadora.forms_romanos import ConversionRomanosForm


class ErrorEntrada(ValueError):
    def __init__(self, campo, mensaje):
        super().__init__(mensaje)
        self.campo = campo


@dataclass(frozen=True)
class Campo:
    id: str
    titulo: str
    opciones: tuple[tuple[str, str], ...] = ()
    inicial: str | tuple[str, ...] = ""
    ayuda: str = ""
    multiple: bool = False
    multilinea: bool = False


def campo(form, nombre, *, ayuda=None, omitir=(), inicial=None):
    control = form.fields[nombre]
    valor = form.initial.get(nombre, control.initial) if inicial is None else inicial
    opciones = ()
    multiple = isinstance(control, forms.MultipleChoiceField)
    if isinstance(control, forms.ChoiceField):
        opciones = tuple((str(clave), str(etiqueta)) for clave, etiqueta in control.choices if str(clave) not in omitir)
    elif isinstance(control, forms.BooleanField):
        opciones = (("si", "Activar"), ("", "Desactivar"))
        valor = "si" if valor else ""
    defecto = (tuple(str(v) for v in (valor or ())) if multiple
               else "" if valor is None else str(valor))
    return Campo(
        nombre, str(control.label or nombre), opciones, defecto,
        str(control.help_text or "") if ayuda is None else ayuda,
        multiple, isinstance(control.widget, forms.Textarea),
    )


def _bases(datos):
    form = ConversionBasesForm()
    origen = datos.get("base_origen", "10")
    inicial = ("10",) if origen == "2" else ("2",)
    return (
        campo(form, "base_origen"),
        campo(form, "numero", ayuda="Puedes incluir un signo - para los negativos."),
        campo(form, "bases_destino", omitir=(origen,), inicial=inicial),
    )


def _romanos(datos):
    form = ConversionRomanosForm()
    ayuda = "Escribe un entero de 1 a 3999." if datos.get("direccion") == "decimal_a_romano" else "Ejemplo: XLII."
    return campo(form, "direccion"), campo(form, "numero", ayuda=ayuda)


DIALOGOS = {
    "conversion-bases": _bases,
    "conversion-romanos": _romanos,
}
