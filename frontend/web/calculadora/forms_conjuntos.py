"""Editor de definiciones; no calcula relaciones ni mantiene un segundo modelo."""

from django import forms

from backend.conjuntos.literales import analizar_definicion, analizar_literal, validar_nombre
from backend.conjuntos.modelo import presentar
from backend.conjuntos.parser import OPERADORES, renombrar_referencias
from backend.conjuntos.presupuesto import Presupuesto
from backend.operandos import OPERANDOS_MAXIMOS
from backend.presupuesto_sistemas import LONGITUD_SISTEMA_MAXIMA
from .forms_feedback import FormularioConErrores

INICIALES = [("A", "{1, 2}"), ("B", "{2, {1, 2}}")]


def campo_texto(etiqueta, *, multilinea=False, **attrs):
    widget = forms.Textarea if multilinea else forms.TextInput
    return forms.CharField(label=etiqueta, required=False, max_length=LONGITUD_SISTEMA_MAXIMA,
                           widget=widget(attrs={"class": "field-input field-input-code", "spellcheck": "false",
                                                "autocomplete": "off", **attrs}))


class ConjuntosForm(FormularioConErrores):
    cantidad = forms.IntegerField(min_value=0, max_value=OPERANDOS_MAXIMOS, widget=forms.HiddenInput)
    expresion = campo_texto("Expresión", multilinea=True, rows=2, placeholder="A ∈ B")
    definicion = campo_texto("Nueva definición", placeholder="S = {1, 2, {3, 4}, 5}")
    izquierdo = campo_texto("Operando izquierdo", placeholder="2, A o {2}", list="nombres-conjuntos")
    operador = forms.ChoiceField(label="Relación", choices=[(op, f"{op} — {nombre}") for op, nombre in OPERADORES], required=False,
                                widget=forms.Select(attrs={"class": "field-input"}),
                                error_messages={"invalid_choice": "Selecciona una relación válida."})
    derecho = campo_texto("Operando derecho", placeholder="A o {1, 2}", list="nombres-conjuntos")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bloques = []
        try:
            cantidad = int(self.data.get("cantidad", 0)) if self.is_bound else self.initial.get("cantidad", 2)
        except (ValueError, TypeError):
            cantidad = 0
        cantidad = max(0, min(cantidad, OPERANDOS_MAXIMOS))
        for i in range(cantidad):
            self.fields[f"nombre_{i}"] = campo_texto("Nombre", **{"data-campo": "nombre", "aria-describedby": "nombres-ayuda"})
            self.fields[f"contenido_{i}"] = campo_texto("Contenido", multilinea=True, rows=2, **{"aria-describedby": "conjuntos-ayuda"})
            self.fields[f"anterior_{i}"] = forms.CharField(required=False, widget=forms.HiddenInput,
                                                         max_length=LONGITUD_SISTEMA_MAXIMA)
            self.bloques.append({"indice": i, "nombre": self[f"nombre_{i}"],
                                 "contenido": self[f"contenido_{i}"], "anterior": self[f"anterior_{i}"]})

    def clean(self):
        datos = super().clean()
        permitidos = set(self.fields) | {"csrfmiddlewaretoken", "accion", "eliminar"}
        if set(self.data) - permitidos:
            self.add_error(None, "El envío contiene campos ajenos al formulario.")
        if hasattr(self.data, "getlist") and any(len(self.data.getlist(n)) != 1 for n in self.data):
            self.add_error(None, "Envía un único valor por campo; hay campos repetidos.")
        self.accion = self.data.get("accion", "calcular")
        if self.accion not in {"calcular", "guardar", "agregar", "construir"}:
            self.add_error(None, "Acción desconocida.")
        eliminar = self.data.get("eliminar")
        if eliminar is not None and eliminar not in {str(b["indice"]) for b in self.bloques}:
            self.add_error(None, "No existe el conjunto que intentas eliminar.")
        self.filas = []
        self.entorno = {}
        self.presupuesto = Presupuesto()
        cambios = {}
        if self.errors:
            return datos
        for bloque in self.bloques:
            i = bloque["indice"]
            if str(i) == eliminar:
                continue
            nombre = datos[f"nombre_{i}"]
            contenido = datos[f"contenido_{i}"]
            self.filas.append((nombre, contenido))
            try:
                validar_nombre(nombre)
                if nombre in self.entorno:
                    raise ValueError(f"El nombre «{nombre}» ya está definido. Usa nombres únicos.")
                self.presupuesto.texto(nombre)
            except ValueError as error:
                self.add_error(f"nombre_{i}", str(error))
                continue
            try:
                self.entorno[nombre] = analizar_literal(contenido, presupuesto=self.presupuesto)
            except ValueError as error:
                self.add_error(f"contenido_{i}", str(error))
            anterior = datos[f"anterior_{i}"]
            if anterior and anterior != nombre:
                cambios[anterior] = nombre
        expresion = datos.get("expresion", "")
        if self.accion == "construir":
            expresion = f'{datos.get("izquierdo", "")} {datos.get("operador", "")} {datos.get("derecho", "")}'
        elif cambios and expresion:
            try:
                expresion = renombrar_referencias(expresion, cambios)
            except ValueError as error:
                self.add_error("expresion", str(error))
        self.expresion = expresion
        if self.accion == "agregar":
            try:
                if len(self.filas) >= OPERANDOS_MAXIMOS:
                    raise ValueError(f"El editor admite hasta {OPERANDOS_MAXIMOS} conjuntos.")
                nombre, valor = analizar_definicion(datos.get("definicion", ""), presupuesto=self.presupuesto)
                if nombre in self.entorno:
                    raise ValueError(f"El nombre «{nombre}» ya está definido.")
                self.filas.append((nombre, presentar(valor)))
            except ValueError as error:
                self.add_error("definicion", str(error))
        return datos


def inicial_editor(filas=INICIALES, expresion="A ∈ B", **extra):
    inicial = {"cantidad": len(filas), "expresion": expresion, "izquierdo": "A", "operador": "∈", "derecho": "B", **extra}
    for i, (nombre, contenido) in enumerate(filas):
        inicial.update({f"nombre_{i}": nombre, f"contenido_{i}": contenido, f"anterior_{i}": nombre})
    return inicial
