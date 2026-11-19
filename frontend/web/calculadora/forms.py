"""Formularios de entrada de la interfaz Django."""

from django import forms

from .forms_feedback import FormularioConErrores
from .forms_matrices import campo_numero

from backend.parser_sistemas import construir_matriz_aumentada, convertir_a_numero
from backend.presupuesto_sistemas import (
    ECUACIONES_MAXIMAS,
    VARIABLES_MAXIMAS,
    LONGITUD_SISTEMA_MAXIMA,
    dimensiones_admitidas,
    validar_dimensiones,
    validar_longitud_sistema,
)
from backend.seguridad_numerica import validar_literal_numerico

from .opciones_sistemas import BLOQUES, BLOQUES_PREDETERMINADOS, METODO_PREDETERMINADO, METODOS


class SistemaForm(FormularioConErrores):
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
    # El tipo de entrada ya se llama «Sistema de ecuaciones»: el campo nombra lo que se escribe.
    sistema = forms.CharField(
        label="Ecuaciones",
        required=False,
        max_length=LONGITUD_SISTEMA_MAXIMA,
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
                "aria-describedby": "sistema-ayuda",
            }
        ),
        error_messages={"required": "Ingresa un sistema de ecuaciones."},
    )
    ecuaciones = forms.IntegerField(
        label="Número de ecuaciones",
        initial=3,
        required=False,
        min_value=1,
        max_value=ECUACIONES_MAXIMAS,
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
            "max_value": f"Se admiten hasta {ECUACIONES_MAXIMAS} ecuaciones.",
        },
    )
    variables = forms.IntegerField(
        label="Número de variables",
        initial=3,
        required=False,
        min_value=1,
        max_value=VARIABLES_MAXIMAS,
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
            "max_value": f"Se admiten hasta {VARIABLES_MAXIMAS} variables.",
        },
    )

    def clean_sistema(self):
        # También cuenta los espacios descartados por CharField(strip=True).
        try:
            validar_longitud_sistema(self.data.get("sistema") or "")
        except ValueError as error:
            raise forms.ValidationError(str(error)) from error
        return self.cleaned_data.get("sistema", "")

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
            if not datos.get("sistema") and "sistema" not in self.errors:
                self.add_error("sistema", "Ingresa un sistema de ecuaciones.")
            return datos

        if tipo_entrada != "matriz":
            return datos

        ecuaciones = datos.get("ecuaciones")
        variables = datos.get("variables")
        if ecuaciones is None and "ecuaciones" not in self.errors:
            self.add_error(
                "ecuaciones", "Indica el número de ecuaciones."
            )
        if variables is None and "variables" not in self.errors:
            self.add_error("variables", "Indica el número de variables.")

        if self.errors.get("ecuaciones") or self.errors.get("variables"):
            return datos

        try:
            validar_dimensiones(ecuaciones, variables)
        except ValueError as error:
            self.add_error("variables", str(error))
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
            self.grupo_error = "matrix-grid"
            self.add_error(
                None,
                "La cantidad de celdas no coincide con las dimensiones indicadas.",
            )
            return datos

        filas = []
        for fila in range(ecuaciones):
            valores = []
            for columna in range(variables + 1):
                nombre = f"matriz_{fila}_{columna}"
                texto = self.data.get(nombre, "")
                etiqueta = self._etiqueta_celda(fila, columna, variables)
                if not isinstance(texto, str) or not texto.strip():
                    self.fields[nombre] = campo_numero(etiqueta)
                    self.add_error(nombre, f"La celda {etiqueta} no puede estar vacía.")
                    continue

                try:
                    validar_literal_numerico(texto)
                    valores.append(convertir_a_numero(texto))
                except ValueError as error:
                    self.fields[nombre] = campo_numero(etiqueta)
                    self.add_error(nombre, f"La celda {etiqueta}: {error}")

            filas.append(valores)

        if self.errors:
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
        if not dimensiones_admitidas(ecuaciones, variables):
            return []

        return self.valores_matriz_desde(self.data, ecuaciones, variables)

    @property
    def errores_celdas(self):
        return [self[nombre] for nombre in self.errors if nombre.startswith("matriz_")]

    @staticmethod
    def valores_matriz_desde(datos, ecuaciones, variables):
        """Las celdas matriz_i_j de un envío o de una consulta, como filas de texto."""
        if not dimensiones_admitidas(ecuaciones, variables):
            return []
        return [
            [datos.get(f"matriz_{fila}_{columna}", "") for columna in range(variables + 1)]
            for fila in range(ecuaciones)
        ]

    @classmethod
    def inicial_desde(cls, consulta):
        """Valores iniciales que llegan por GET (rutas antiguas y «También puedes explorar»).

        Solo preparan el formulario con el método, la entrada y los bloques; nada
        se resuelve hasta que el usuario pulsa Resolver. Se ignora lo que no sea válido.
        """
        inicial = {}
        if consulta.get("metodo") in dict(METODOS):
            inicial["metodo"] = consulta["metodo"]
        if consulta.get("tipo_entrada") in dict(cls.TIPOS_ENTRADA):
            inicial["tipo_entrada"] = consulta["tipo_entrada"]
        if 0 < len(consulta.get("sistema", "")) <= LONGITUD_SISTEMA_MAXIMA and consulta["sistema"].strip():
            inicial["sistema"] = consulta["sistema"]
        for campo in ("ecuaciones", "variables"):
            try:
                valor = cls.base_fields[campo].clean(consulta.get(campo))
            except forms.ValidationError:
                continue
            if valor is not None:
                inicial[campo] = valor
        if "ecuaciones" in inicial and "variables" in inicial:
            if not dimensiones_admitidas(inicial["ecuaciones"], inicial["variables"]):
                inicial.pop("ecuaciones")
                inicial.pop("variables")
        if consulta.get("mostrar_definido"):
            elegidos = consulta.getlist("mostrar")
            inicial["mostrar"] = [clave for clave, _ in BLOQUES if clave in elegidos]
        return inicial

    def pares_de_entrada(self):
        """La entrada validada como pares de consulta, para volver a proponerla por GET."""
        datos = self.cleaned_data
        if datos.get("tipo_entrada") != "matriz":
            return [("tipo_entrada", "sistema"), ("sistema", datos.get("sistema", ""))]

        pares = [
            ("tipo_entrada", "matriz"),
            ("ecuaciones", datos["ecuaciones"]),
            ("variables", datos["variables"]),
        ]
        for fila, valores in enumerate(self.valores_matriz_ingresados()):
            for columna, valor in enumerate(valores):
                pares.append((f"matriz_{fila}_{columna}", valor))
        return pares

    def bloques_elegidos(self):
        """Los bloques marcados ahora (enviados o iniciales), sin depender de la validación."""
        if not self.is_bound:
            return list(self.initial.get("mostrar", BLOQUES_PREDETERMINADOS))
        if not self.data.get("mostrar_definido"):
            return list(BLOQUES_PREDETERMINADOS)
        elegidos = self.data.getlist("mostrar")
        return [clave for clave, _ in BLOQUES if clave in elegidos]


class ConversionBasesForm(FormularioConErrores):
    """Un número, su base de origen y las bases a las que convertirlo.

    Los destinos son casillas: una, varias o todas las demás bases, nunca la de
    origen y al menos una. El contrato HTTP es estricto: `bases_destino` es el
    único campo que viaja repetido (una vez por casilla marcada); un valor
    duplicado dentro de esa lista, cualquier otro campo repetido o un campo ajeno
    al formulario se rechazan. El orden de los destinos es siempre el de las
    casillas, aunque un POST manipulado los envíe desordenados.
    """

    BASES = (
        (2, "Binario"),
        (8, "Octal"),
        (10, "Decimal"),
        (16, "Hexadecimal"),
    )
    CAMPOS_PERMITIDOS = frozenset({"csrfmiddlewaretoken", "numero", "base_origen", "bases_destino"})
    # Tope generoso para un ejercicio (128 dígitos binarios o hexadecimales): evita que
    # una entrada enorme cueste segundos de cálculo o desborde la conversión a texto.
    LONGITUD_MAXIMA = 128

    numero = forms.CharField(
        label="Número",
        required=False,
        strip=False,
        max_length=LONGITUD_MAXIMA,
        error_messages={
            "max_length": f"El número no puede tener más de {LONGITUD_MAXIMA} caracteres.",
        },
        widget=forms.TextInput(
            attrs={
                "class": "field-input field-input-numeral",
                "autocomplete": "off",
                "spellcheck": "false",
                "inputmode": "text",
                "aria-describedby": "numero-ayuda numero-aviso",
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
    bases_destino = forms.TypedMultipleChoiceField(
        label="Convertir a",
        choices=BASES,
        coerce=int,
        initial=[2],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"aria-describedby": "destinos-ayuda destinos-aviso"}),
    )

    def clean_numero(self):
        return self.cleaned_data.get("numero", "")

    def clean_bases_destino(self):
        elegidas = self.cleaned_data.get("bases_destino") or []
        if len(set(elegidas)) != len(elegidas):
            raise forms.ValidationError("Las bases de destino no deben repetirse.")
        return [base for base, _ in self.BASES if base in elegidas]

    def rechazar_envio_manipulado(self):
        """Ningún campo ajeno y un solo valor por campo, salvo las casillas de destino."""
        if not hasattr(self.data, "getlist"):
            return
        if set(self.data) - self.CAMPOS_PERMITIDOS:
            self.add_error(None, "El envío incluye campos que no forman parte del formulario.")
        if any(len(self.data.getlist(nombre)) > 1 for nombre in self.data if nombre != "bases_destino"):
            self.add_error(None, "Envía un único valor por campo; hay campos repetidos.")

    def clean(self):
        datos = super().clean()
        self.rechazar_envio_manipulado()
        destinos = datos.get("bases_destino")
        if destinos is None:
            return datos
        if datos.get("base_origen") in destinos:
            self.add_error(
                "bases_destino",
                "La base de origen y la base de destino deben ser distintas.",
            )
        elif not destinos:
            self.add_error("bases_destino", "Elige al menos una base de destino.")
        return datos
