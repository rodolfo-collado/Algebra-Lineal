"""Formularios de entrada de la interfaz Django."""

import re

from django import forms

from backend.parser_sistemas import construir_matriz_aumentada, convertir_a_numero

from .opciones_sistemas import BLOQUES, BLOQUES_PREDETERMINADOS, METODO_PREDETERMINADO, METODOS
from .opciones_vectores import (
    DIMENSION_MAXIMA,
    DIMENSION_MINIMA,
    DIMENSION_PREDETERMINADA,
    NOMBRE_OBJETIVO,
    OPERACION_PREDETERMINADA,
    OPERACIONES,
    VECTORES_MAXIMOS,
    VECTORES_MINIMOS,
    VECTORES_PREDETERMINADOS,
    nombres_vectores,
)


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

        return self.valores_matriz_desde(self.data, ecuaciones, variables)

    @staticmethod
    def valores_matriz_desde(datos, ecuaciones, variables):
        """Las celdas matriz_i_j de un envío o de una consulta, como filas de texto."""
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
        if consulta.get("sistema", "").strip():
            inicial["sistema"] = consulta["sistema"]
        for campo in ("ecuaciones", "variables"):
            valor = consulta.get(campo, "")
            if valor.isdigit() and int(valor) >= 1:
                inicial[campo] = int(valor)
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


class ConversionBasesForm(forms.Form):
    """Un número, su base de origen y las bases a las que convertirlo.

    Los destinos son casillas: una, varias o todas las demás bases, nunca la de
    origen y al menos una. El orden de los destinos es siempre el de las casillas,
    aunque un POST manipulado los envíe desordenados o repetidos.
    """

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
    bases_destino = forms.TypedMultipleChoiceField(
        label="Convertir a",
        choices=BASES,
        coerce=int,
        initial=[2],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def clean_numero(self):
        return self.cleaned_data.get("numero", "")

    def clean_bases_destino(self):
        elegidas = set(self.cleaned_data.get("bases_destino") or ())
        return [base for base, _ in self.BASES if base in elegidas]

    def clean(self):
        datos = super().clean()
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


class VectoresForm(forms.Form):
    """Operación, dimensión y componentes de los vectores, como celdas `nombre_i`.

    Las componentes viajan como campos sueltos (u_0, u_1, …, v1_0, …, b_0, …)
    generados según la dimensión y la cantidad de vectores. El servidor
    reconstruye la estructura esperada y la compara con lo recibido, así que un
    POST manipulado (celdas de más, de menos o con otros nombres) se rechaza.
    """

    OPERACIONES = OPERACIONES
    _CELDA = re.compile(r"^(u|v|b|v[1-9]\d*)_(\d+)$")

    operacion = forms.ChoiceField(
        label="Operación",
        choices=OPERACIONES,
        initial=OPERACION_PREDETERMINADA,
        widget=forms.RadioSelect,
        error_messages={
            "required": "Selecciona una operación.",
            "invalid_choice": "Selecciona una operación válida.",
        },
    )
    dimension = forms.IntegerField(
        label="Dimensión",
        initial=DIMENSION_PREDETERMINADA,
        min_value=DIMENSION_MINIMA,
        max_value=DIMENSION_MAXIMA,
        widget=forms.NumberInput(
            attrs={
                "class": "field-input",
                "min": str(DIMENSION_MINIMA),
                "max": str(DIMENSION_MAXIMA),
                "inputmode": "numeric",
            }
        ),
        error_messages={
            "required": "Indica la dimensión de los vectores.",
            "invalid": "La dimensión debe ser un número entero.",
            "min_value": "Un vector necesita al menos una componente.",
            "max_value": f"La dimensión máxima admitida es {DIMENSION_MAXIMA}.",
        },
    )
    vectores = forms.IntegerField(
        label="Número de vectores",
        required=False,
        initial=VECTORES_PREDETERMINADOS,
        min_value=VECTORES_MINIMOS,
        max_value=VECTORES_MAXIMOS,
        widget=forms.NumberInput(
            attrs={
                "class": "field-input",
                "min": str(VECTORES_MINIMOS),
                "max": str(VECTORES_MAXIMOS),
                "inputmode": "numeric",
            }
        ),
        error_messages={
            "invalid": "La cantidad de vectores debe ser un número entero.",
            "min_value": "Hace falta al menos un vector generador.",
            "max_value": f"Se admiten como máximo {VECTORES_MAXIMOS} vectores generadores.",
        },
    )
    escalar = forms.CharField(
        label="Escalar",
        required=False,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": "matrix-input scalar-input",
                "autocomplete": "off",
                "spellcheck": "false",
                "inputmode": "text",
                "aria-label": "Escalar k",
            }
        ),
    )

    @classmethod
    def iniciales_desde(cls, datos):
        """Valores iniciales a partir de un POST que solo pide reajustar la estructura.

        Sirve al botón «Aplicar» sin JavaScript: se conserva lo escrito, sin
        validar ni calcular todavía.
        """
        iniciales = {
            "operacion": datos.get("operacion", OPERACION_PREDETERMINADA),
            "dimension": datos.get("dimension", DIMENSION_PREDETERMINADA),
            "vectores": datos.get("vectores", VECTORES_PREDETERMINADOS),
            "escalar": datos.get("escalar", ""),
            "valores": {
                nombre: valor
                for nombre, valor in datos.items()
                if cls._CELDA.match(nombre)
            },
        }
        return iniciales

    def _valor_actual(self, campo, predeterminado):
        if self.is_bound:
            return self.data.get(campo, predeterminado)
        return self.initial.get(campo, self.fields[campo].initial if campo in self.fields else predeterminado)

    @staticmethod
    def _entero(valor, predeterminado, minimo, maximo):
        try:
            numero = int(str(valor).strip())
        except (TypeError, ValueError):
            return predeterminado
        return min(max(numero, minimo), maximo)

    def estructura(self):
        """Operación, dimensión y filas de vectores (con lo escrito) para pintar la entrada.

        No depende de que el formulario sea válido: tras un error la cuadrícula
        conserva lo ingresado, y en un GET muestra la estructura inicial.
        """
        operacion = self._valor_actual("operacion", OPERACION_PREDETERMINADA)
        if operacion not in dict(OPERACIONES):
            operacion = OPERACION_PREDETERMINADA
        dimension = self._entero(
            self._valor_actual("dimension", DIMENSION_PREDETERMINADA),
            DIMENSION_PREDETERMINADA, DIMENSION_MINIMA, DIMENSION_MAXIMA,
        )
        cantidad = self._entero(
            self._valor_actual("vectores", VECTORES_PREDETERMINADOS),
            VECTORES_PREDETERMINADOS, VECTORES_MINIMOS, VECTORES_MAXIMOS,
        )
        valores = self.data if self.is_bound else self.initial.get("valores", {})

        filas = []
        for nombre in nombres_vectores(operacion, cantidad):
            filas.append({
                "nombre": nombre,
                "objetivo": nombre == NOMBRE_OBJETIVO,
                "componentes": [
                    {"campo": f"{nombre}_{indice}", "indice": indice + 1,
                     "valor": valores.get(f"{nombre}_{indice}", "")}
                    for indice in range(dimension)
                ],
            })

        return {
            "operacion": operacion,
            "dimension": dimension,
            "vectores": cantidad,
            "escalar": self._valor_actual("escalar", "") or "",
            "filas": filas,
        }

    def valores_ingresados(self):
        """Componentes recibidas por nombre de campo, para que JavaScript las conserve."""
        if not self.is_bound:
            return dict(self.initial.get("valores", {}))
        return {
            nombre: valor
            for nombre, valor in self.data.items()
            if self._CELDA.match(nombre)
        }

    @staticmethod
    def _etiqueta(nombre, indice):
        return f"la componente {indice + 1} de {nombre}"

    def clean(self):
        datos = super().clean()
        operacion = datos.get("operacion")
        dimension = datos.get("dimension")
        if operacion is None or dimension is None:
            return datos

        cantidad = datos.get("vectores")
        if operacion == "combinacion":
            if self.errors.get("vectores"):
                return datos
            if cantidad is None:
                self.add_error("vectores", "Indica cuántos vectores generadores hay.")
                return datos
        else:
            cantidad = 0

        nombres = nombres_vectores(operacion, cantidad)
        esperados = {f"{nombre}_{indice}" for nombre in nombres for indice in range(dimension)}
        recibidos = {nombre for nombre in self.data if self._CELDA.match(nombre)}
        if recibidos != esperados:
            self.add_error(
                None,
                "La cantidad de componentes no coincide con la dimensión y los vectores indicados.",
            )
            return datos

        vectores = {}
        errores = []
        for nombre in nombres:
            componentes = []
            for indice in range(dimension):
                texto = self.data.get(f"{nombre}_{indice}", "")
                if not isinstance(texto, str) or not texto.strip():
                    errores.append(f"Falta {self._etiqueta(nombre, indice)}.")
                    continue
                try:
                    componentes.append(convertir_a_numero(texto))
                except ValueError as error:
                    errores.append(f"En {self._etiqueta(nombre, indice)}: {error}")
            vectores[nombre] = componentes

        escalar = None
        if operacion == "escalar":
            texto = datos.get("escalar") or ""
            if not texto:
                self.add_error("escalar", "Ingresa el escalar k.")
            else:
                try:
                    escalar = convertir_a_numero(texto)
                except ValueError as error:
                    self.add_error("escalar", f"El escalar: {error}")

        if errores:
            for error in errores:
                self.add_error(None, error)
            return datos
        if self.errors:
            return datos

        datos["entrada"] = {
            "operacion": operacion,
            "dimension": dimension,
            "nombres": nombres,
            "vectores": vectores,
            "escalar": escalar,
        }
        return datos
