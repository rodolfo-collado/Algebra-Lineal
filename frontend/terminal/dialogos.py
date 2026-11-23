"""Preguntas de terminal y su correspondencia con los controles compartidos."""

from collections.abc import Callable
from dataclasses import dataclass

from django import forms

from backend.sistemas_numericos import normalizar_numero
from frontend.web.calculadora.forms import ConversionBasesForm
from frontend.web.calculadora.forms_romanos import ConversionRomanosForm
from frontend.web.calculadora.servicios_romanos import convertir_romanos


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
    verificar: Callable[[str | tuple[str, ...], str], str | None] | None = None

    def validar(self, valor, decimal):
        if self.verificar is None:
            return valor
        try:
            normalizado = self.verificar(valor, decimal)
        except ErrorEntrada:
            raise
        except (forms.ValidationError, ValueError) as error:
            mensaje = error.messages[0] if isinstance(error, forms.ValidationError) else str(error)
            raise ErrorEntrada(self.id, mensaje) from error
        return valor if normalizado is None else normalizado


def campo(form, nombre, *, ayuda=None, omitir=(), inicial=None, verificar=None):
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

    def validar_con_control(texto, decimal):
        if isinstance(control, forms.FloatField) and decimal == ",":
            texto = texto.replace(",", ".")
        limpio = control.clean(texto)
        if verificar is not None:
            verificar(limpio, decimal)
        if type(limpio) is int:
            return str(limpio)

    return Campo(
        nombre, str(control.label or nombre), opciones, defecto,
        str(control.help_text or "") if ayuda is None else ayuda,
        multiple, isinstance(control.widget, forms.Textarea),
        validar_con_control if not opciones or verificar is not None else None,
    )


def _bases(datos):
    form = ConversionBasesForm()
    origen = datos.get("base_origen", "10")
    inicial = ("10",) if origen == "2" else ("2",)

    def destinos_validos(destinos, _decimal):
        if not destinos:
            raise ValueError("Elige al menos una base de destino.")

    return (
        campo(form, "base_origen"),
        campo(form, "numero", ayuda="Puedes incluir un signo - para los negativos.",
              verificar=lambda numero, _: normalizar_numero(numero, int(origen))),
        campo(form, "bases_destino", omitir=(origen,), inicial=inicial, verificar=destinos_validos),
    )


def _romanos(datos):
    form = ConversionRomanosForm()
    direccion = datos.get("direccion", "decimal_a_romano")
    ayuda = "Escribe un entero de 1 a 3999." if direccion == "decimal_a_romano" else "Ejemplo: XLII."
    return campo(form, "direccion"), campo(form, "numero", ayuda=ayuda,
                                          verificar=lambda numero, _: convertir_romanos(direccion=direccion, numero=numero))


DIALOGOS = {
    "conversion-bases": _bases,
    "conversion-romanos": _romanos,
}
