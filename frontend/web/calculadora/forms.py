"""Formularios de entrada de la interfaz Django."""

from django import forms

from backend.parser_sistemas import construir_matriz_aumentada, convertir_a_numero


class SistemaForm(forms.Form):
    TIPOS_ENTRADA = (
        ("sistema", "Sistema de ecuaciones"),
        ("matriz", "Matriz aumentada"),
    )
    METODOS = (
        ("gauss", "Gauss"),
        ("gauss_jordan", "Gauss-Jordan"),
    )

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
        initial="gauss_jordan",
        widget=forms.RadioSelect,
    )
    sistema = forms.CharField(
        label="Sistema de ecuaciones",
        required=False,
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
    ecuaciones = forms.IntegerField(
        label="Número de ecuaciones",
        required=False,
        min_value=1,
        error_messages={
            "invalid": "La cantidad de ecuaciones debe ser un número entero.",
            "min_value": "Debe haber al menos una ecuación.",
        },
    )
    variables = forms.IntegerField(
        label="Número de variables",
        required=False,
        min_value=1,
        error_messages={
            "invalid": "La cantidad de variables debe ser un número entero.",
            "min_value": "Debe haber al menos una variable.",
        },
    )

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
