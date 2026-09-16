"""Entrada visual de matrices y validación del contrato HTTP de su estructura."""

from django import forms

from backend.parser_sistemas import convertir_a_numero

from .opciones_matrices import (
    CONFIGURACION, DIMENSION_MAXIMA, DIMENSION_MINIMA, DIMENSION_PREDETERMINADA,
    OPERACIONES, OPERACION_PREDETERMINADA,
)


def campo_dimension(etiqueta):
    return forms.IntegerField(
        label=etiqueta, initial=DIMENSION_PREDETERMINADA,
        min_value=DIMENSION_MINIMA, max_value=DIMENSION_MAXIMA,
        widget=forms.NumberInput(attrs={"class": "field-input", "inputmode": "numeric"}),
        error_messages={
            "required": f"Indica el número de {etiqueta.lower()}.",
            "invalid": f"El número de {etiqueta.lower()} debe ser entero.",
            "min_value": f"El número de {etiqueta.lower()} debe ser al menos {DIMENSION_MINIMA}.",
            "max_value": f"La interfaz admite hasta {DIMENSION_MAXIMA} {etiqueta.lower()}.",
        },
    )


def campo_numero(etiqueta):
    # Se valida con el parser común al calcular; Aplicar conserva incluso un
    # número a medio escribir, sin tratar de calcularlo todavía.
    return forms.CharField(
        label=etiqueta, required=False,
        widget=forms.TextInput(attrs={
            "class": "matrix-input", "autocomplete": "off",
            "spellcheck": "false", "inputmode": "text",
        }),
    )


class MatricesForm(forms.Form):
    operacion = forms.ChoiceField(
        label="Operación", choices=OPERACIONES, initial=OPERACION_PREDETERMINADA,
        widget=forms.RadioSelect,
        error_messages={"required": "Selecciona una operación.",
                        "invalid_choice": "Selecciona una operación válida."},
    )
    filas = campo_dimension("Filas")
    columnas = campo_dimension("Columnas")

    def __init__(self, *args, ajustar=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.ajustar = ajustar
        # Solo la representación usa valores seguros de respaldo. La validación
        # mantiene el POST original y rechaza dimensiones u operaciones inválidas.
        estructura = {}
        for nombre in ("operacion", "filas", "columnas"):
            campo = self.fields[nombre]
            valor = self.data.get(nombre) if self.is_bound else self.initial.get(nombre, campo.initial)
            try:
                estructura[nombre] = campo.clean(valor)
            except forms.ValidationError:
                estructura[nombre] = campo.initial
        self.estructura = estructura
        self.configuracion = CONFIGURACION[estructura["operacion"]]
        self.nombres_celdas = []
        self.matrices = []
        if self.configuracion["escalar"]:
            self.fields["escalar"] = campo_numero("Escalar k")
        for nombre in self.configuracion["matrices"]:
            filas = []
            for i in range(estructura["filas"]):
                fila = []
                for j in range(estructura["columnas"]):
                    clave = f"celda_{nombre}_{i}_{j}"
                    self.nombres_celdas.append(clave)
                    self.fields[clave] = campo_numero(f"Matriz {nombre}, fila {i + 1}, columna {j + 1}")
                    fila.append(self[clave])
                filas.append(fila)
            self.matrices.append({"nombre": nombre, "filas": filas})

    def clean(self):
        datos = super().clean()
        if hasattr(self.data, "getlist") and any(len(self.data.getlist(k)) != 1 for k in self.data):
            self.add_error(None, "Envía un único valor por campo; hay campos repetidos.")
        if self.errors or self.ajustar:
            return datos

        esperados = set(self.nombres_celdas)
        recibidos = {k for k in self.data if k.startswith("celda_")}
        permitidos = set(self.fields) | {"csrfmiddlewaretoken", "ajustar"}
        if recibidos != esperados or set(self.data) - permitidos:
            self.add_error(None, "Las celdas recibidas no coinciden con las matrices, filas y columnas indicadas. Pulsa Aplicar para ajustar la estructura.")
            return datos

        numericos = [*self.nombres_celdas]
        if self.configuracion["escalar"]:
            numericos.append("escalar")
        for nombre in numericos:
            texto = datos.get(nombre, "")
            if not texto:
                self.add_error(nombre, f"Completa {self.fields[nombre].label.lower()}.")
            else:
                try:
                    datos[nombre] = convertir_a_numero(texto)
                except ValueError as error:
                    self.add_error(nombre, str(error))
        if self.errors:
            return datos

        datos["entrada"] = {
            "operacion": datos["operacion"], "escalar": datos.get("escalar"),
            "matrices": {
                nombre: [
                    [datos[f"celda_{nombre}_{i}_{j}"] for j in range(datos["columnas"])]
                    for i in range(datos["filas"])
                ] for nombre in self.configuracion["matrices"]
            },
        }
        return datos

    def iniciales(self):
        """Conserva las celdas que sobreviven a Aplicar, sin arrastrar campos ajenos."""
        return {nombre: self.data.get(nombre, "") for nombre in self.fields}
