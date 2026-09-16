"""Formularios de entrada de la interfaz Django."""

from django import forms

from backend.parser_sistemas import construir_matriz_aumentada, convertir_a_numero

from .opciones_sistemas import BLOQUES, BLOQUES_PREDETERMINADOS, METODO_PREDETERMINADO, METODOS


class SistemaForm(forms.Form):
    TIPOS_ENTRADA = (
        ("sistema", "Sistema de ecuaciones"),
        ("matriz", "Matriz aumentada"),
    )
    METODOS = METODOS

    tipo_entrada = forms.ChoiceField(
        label="Tipo de entrada",
        choices=TIPOS_ENTRADA,
        initial="sistema",
        required=False,
        widget=forms.RadioSelect,
    )
    metodo = forms.ChoiceField(
        label="Método",
        choices=METODOS,
        initial=METODO_PREDETERMINADO,
        widget=forms.RadioSelect,
    )
    mostrar = forms.MultipleChoiceField(
        label="Mostrar",
        choices=BLOQUES,
        initial=list(BLOQUES_PREDETERMINADOS),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    # Un navegador omite las casillas desmarcadas: este marcador distingue
    # «no quiero ningún bloque» de un envío que no incluye la sección Mostrar.
    mostrar_definido = forms.BooleanField(required=False, widget=forms.HiddenInput)
    sistema = forms.CharField(
        label="Sistema de ecuaciones",
        required=False,
        strip=True,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "class": "field-input field-input-code",
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
    ecuaciones = forms.IntegerField(
        label="Número de ecuaciones",
        required=False,
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "field-input",
                "min": "1",
                "inputmode": "numeric",
            }
        ),
        error_messages={
            "invalid": "La cantidad de ecuaciones debe ser un número entero.",
            "min_value": "Debe haber al menos una ecuación.",
        },
    )
    variables = forms.IntegerField(
        label="Número de variables",
        required=False,
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "field-input",
                "min": "1",
                "inputmode": "numeric",
            }
        ),
        error_messages={
            "invalid": "La cantidad de variables debe ser un número entero.",
            "min_value": "Debe haber al menos una variable.",
        },
    )

    def clean_mostrar(self):
        seleccion = self.cleaned_data.get("mostrar") or []
        if not seleccion and not self.data.get("mostrar_definido"):
            # Clientes que no envían la sección (rutas antiguas, scripts): lo de siempre.
            return list(BLOQUES_PREDETERMINADOS)
        return seleccion

    def clean(self):
        datos = super().clean()
        tipo_entrada = datos.get("tipo_entrada")

        if tipo_entrada in (None, "", "sistema"):
            # Mantiene compatibles los POST del flujo textual de P6.
            datos["tipo_entrada"] = "sistema"
            if not datos.get("sistema"):
                self.add_error("sistema", "Ingresa un sistema de ecuaciones.")
            return datos

        if tipo_entrada != "matriz":
            return datos

        ecuaciones = datos.get("ecuaciones")
        variables = datos.get("variables")
        if ecuaciones is None:
            self.add_error(
                "ecuaciones", "Indica el número de ecuaciones."
            )
        if variables is None:
            self.add_error("variables", "Indica el número de variables.")

        if self.errors.get("ecuaciones") or self.errors.get("variables"):
            return datos

        nombres_esperados = {
            f"matriz_{fila}_{columna}"
            for fila in range(ecuaciones)
            for columna in range(variables + 1)
        }
        nombres_recibidos = {
            nombre
            for nombre in self.data
            if nombre.startswith("matriz_")
        }
        if nombres_recibidos != nombres_esperados:
            self.add_error(
                None,
                "La cantidad de celdas no coincide con las dimensiones indicadas.",
            )
            return datos

        filas = []
        errores = []
        for fila in range(ecuaciones):
            valores = []
            for columna in range(variables + 1):
                nombre = f"matriz_{fila}_{columna}"
                texto = self.data.get(nombre, "")
                etiqueta = self._etiqueta_celda(fila, columna, variables)
                if not isinstance(texto, str) or not texto.strip():
                    errores.append(f"La celda {etiqueta} no puede estar vacía.")
                    continue

                try:
                    valores.append(convertir_a_numero(texto))
                except ValueError as error:
                    errores.append(f"La celda {etiqueta}: {error}")

            filas.append(valores)

        if errores:
            for error in errores:
                self.add_error(None, error)
            return datos

        datos["matriz_aumentada"] = construir_matriz_aumentada(
            [fila[:-1] for fila in filas],
            [fila[-1] for fila in filas],
        )
        return datos

    @staticmethod
    def _etiqueta_celda(fila, columna, variables):
        if columna == variables:
            return f"fila {fila + 1}, término independiente"

        return f"fila {fila + 1}, x{columna + 1}"

    def valores_matriz_ingresados(self):
        """Conserva valores de la cuadrícula para repoblarla tras un error."""
        datos_limpios = getattr(self, "cleaned_data", {})
        ecuaciones = datos_limpios.get("ecuaciones")
        variables = datos_limpios.get("variables")
        if ecuaciones is None or variables is None:
            return []

        return [
            [
                self.data.get(f"matriz_{fila}_{columna}", "")
                for columna in range(variables + 1)
            ]
            for fila in range(ecuaciones)
        ]


class ConversionBasesForm(forms.Form):
    """Un número, su base de origen y la base de destino; las bases deben diferir."""

    BASES = (
        (2, "Binario"),
        (8, "Octal"),
        (10, "Decimal"),
        (16, "Hexadecimal"),
    )

    numero = forms.CharField(
        label="Número",
        required=False,
        strip=False,
        widget=forms.TextInput(
            attrs={
                "class": "field-input field-input-numeral",
                "autocomplete": "off",
                "spellcheck": "false",
                "inputmode": "text",
            }
        ),
    )
    base_origen = forms.TypedChoiceField(
        label="Base de origen",
        choices=BASES,
        coerce=int,
        initial=10,
        widget=forms.Select(attrs={"class": "field-select"}),
    )
    base_destino = forms.TypedChoiceField(
        label="Base de destino",
        choices=BASES,
        coerce=int,
        initial=2,
        widget=forms.Select(attrs={"class": "field-select"}),
    )

    def clean_numero(self):
        return self.cleaned_data.get("numero", "")

    def clean(self):
        datos = super().clean()
        if datos.get("base_origen") and datos.get("base_origen") == datos.get("base_destino"):
            self.add_error(
                "base_destino",
                "La base de origen y la base de destino deben ser distintas.",
            )
        return datos
