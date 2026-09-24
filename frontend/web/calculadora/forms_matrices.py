"""Entrada visual de matrices y validación del contrato HTTP de su estructura."""

from django import forms

from backend.parser_sistemas import convertir_a_numero

from .opciones_matrices import (
    CAMPOS_DIMENSION, CONFIGURACION, DIMENSION_MAXIMA, DIMENSION_MINIMA, DIMENSION_PREDETERMINADA,
    METODO_PREDETERMINADO, OPERACIONES, OPERACION_PREDETERMINADA, es_vector,
    configuracion_operandos,
)


def _minuscula_inicial(texto):
    return texto[:1].lower() + texto[1:]


def campo_dimension(etiqueta, requerido=True):
    nombre = _minuscula_inicial(etiqueta)
    return forms.IntegerField(
        label=etiqueta, initial=DIMENSION_PREDETERMINADA, required=requerido,
        min_value=DIMENSION_MINIMA, max_value=DIMENSION_MAXIMA,
        widget=forms.NumberInput(attrs={"class": "field-input", "inputmode": "numeric"}),
        error_messages={
            "required": f"Indica el número de {nombre}.",
            "invalid": f"El número de {nombre} debe ser entero.",
            "min_value": f"El número de {nombre} debe ser al menos {DIMENSION_MINIMA}.",
            "max_value": f"La interfaz admite hasta {DIMENSION_MAXIMA} {nombre}.",
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


def etiqueta_celda(nombre, vector, i, j):
    if vector:
        return f"Vector {nombre}, componente {i + 1}"
    return f"Matriz {nombre}, fila {i + 1}, columna {j + 1}"


class FormularioCeldas(forms.Form):
    """Base de las herramientas que capturan matrices o vectores columna como celdas `celda_<nombre>_<i>_<j>`.

    Los campos se generan según la estructura vigente (filas, columnas) y el
    contrato HTTP es estricto: el servidor reconstruye el conjunto exacto de
    celdas que espera y rechaza celdas de más, de menos, campos desconocidos o
    repetidos. La aritmética la resuelve el parser común del proyecto.
    """

    def __init__(self, *args, ajustar=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.ajustar = ajustar
        self.nombres_celdas = []
        self.matrices = []

    def _valor_seguro(self, nombre):
        # Solo la representación usa valores seguros de respaldo. La validación
        # mantiene el POST original y rechaza estructuras, operaciones o métodos inválidos.
        campo = self.fields[nombre]
        valor = self.data.get(nombre) if self.is_bound else self.initial.get(nombre, campo.initial)
        try:
            limpio = campo.clean(valor)
        except forms.ValidationError:
            return campo.initial
        return campo.initial if limpio in (None, "") else limpio

    def generar_celdas(self, nombre, alto, ancho, vector=False):
        """Crea los campos de una matriz alto×ancho (o de un vector columna) y la describe para la plantilla."""
        filas = []
        for i in range(alto):
            fila = []
            for j in range(ancho):
                clave = f"celda_{nombre}_{i}_{j}"
                self.nombres_celdas.append(clave)
                self.fields[clave] = campo_numero(etiqueta_celda(nombre, vector, i, j))
                fila.append(self[clave])
            filas.append(fila)
        entrada = {"nombre": nombre, "filas": filas, "vector": vector}
        self.matrices.append(entrada)
        return entrada

    def rechazar_campos_repetidos(self):
        if hasattr(self.data, "getlist") and any(len(self.data.getlist(k)) != 1 for k in self.data):
            self.add_error(None, "Envía un único valor por campo; hay campos repetidos.")

    def celdas_coinciden(self):
        """Exactamente las celdas esperadas y ningún campo ajeno al formulario."""
        esperados = set(self.nombres_celdas)
        recibidos = {k for k in self.data if k.startswith("celda_")}
        permitidos = set(self.fields) | {"csrfmiddlewaretoken", "ajustar"}
        return recibidos == esperados and not (set(self.data) - permitidos)

    def convertir_numeros(self, datos, nombres):
        """Reemplaza el texto de cada campo por su valor exacto, o asocia el error a la celda."""
        for nombre in nombres:
            texto = datos.get(nombre, "")
            if not texto:
                self.add_error(nombre, f"Completa {self.fields[nombre].label.lower()}.")
            else:
                try:
                    datos[nombre] = convertir_a_numero(texto)
                except ValueError as error:
                    self.add_error(nombre, str(error))

    @staticmethod
    def leer_matriz(datos, nombre, alto, ancho):
        return [[datos[f"celda_{nombre}_{i}_{j}"] for j in range(ancho)] for i in range(alto)]


class MatricesForm(FormularioCeldas):
    cantidad = forms.IntegerField(
        label="Cantidad de matrices", initial=2, min_value=2, required=False, widget=forms.HiddenInput,
        error_messages={"invalid": "La cantidad de matrices debe ser un número entero.",
                        "min_value": "La operación requiere al menos 2 operandos."},
    )
    operacion = forms.ChoiceField(
        label="Operación", choices=OPERACIONES, initial=OPERACION_PREDETERMINADA,
        widget=forms.RadioSelect,
        error_messages={"required": "Selecciona una operación.",
                        "invalid_choice": "Selecciona una operación válida."},
    )
    filas = campo_dimension("Filas")
    columnas = campo_dimension("Columnas")
    # Solo AB la usa y solo Ax y AB tienen método. Cuando la operación no los
    # necesita quedan deshabilitados (no viajan en el POST) y ocultos; cuando
    # los necesita, clean() exige que lleguen. No son obligatorios a nivel de
    # campo para que Aplicar sin JavaScript pueda crearlos con su valor inicial.
    columnas_b = campo_dimension("Columnas de B", requerido=False)
    metodo = forms.ChoiceField(
        label="Método", required=False, initial=METODO_PREDETERMINADO, widget=forms.RadioSelect,
        error_messages={"invalid_choice": "Selecciona un método válido."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estructura = {"operacion": self._valor_seguro("operacion")}
        base = CONFIGURACION[estructura["operacion"]]
        self.fields["cantidad"].disabled = base["aridad"][1] is not None
        estructura["cantidad"] = self._valor_seguro("cantidad") if not self.fields["cantidad"].disabled else 2
        self.configuracion = configuracion_operandos(estructura["operacion"], estructura["cantidad"])
        self.dimensiones_adicionales = []
        for nombre, etiqueta in self.configuracion["dimensiones"]:
            if nombre not in self.fields:
                self.fields[nombre] = campo_dimension(etiqueta)
                estructura[nombre] = self._valor_seguro(nombre)
                self.dimensiones_adicionales.append(self[nombre])
        etiquetas = dict(self.configuracion["dimensiones"])
        for nombre in CAMPOS_DIMENSION:
            campo = self.fields[nombre]
            campo.disabled = nombre not in etiquetas
            campo.label = etiquetas.get(nombre, campo.label)
            estructura[nombre] = campo.initial if campo.disabled else self._valor_seguro(nombre)
        metodo = self.fields["metodo"]
        metodo.disabled = not self.configuracion["metodos"]
        metodo.choices = self.configuracion["metodos"] or CONFIGURACION["producto"]["metodos"]
        estructura["metodo"] = metodo.initial if metodo.disabled else self._valor_seguro("metodo")
        self.estructura = estructura

        if self.configuracion["escalar"]:
            self.fields["escalar"] = campo_numero("Escalar k")
        for nombre in self.configuracion["matrices"]:
            self.generar_celdas(nombre, *self.forma(nombre), vector=es_vector(self.configuracion, nombre))

    def forma(self, nombre):
        """(filas, columnas) de una matriz de entrada según la estructura vigente."""
        campo_filas, campo_columnas = self.configuracion["formas"][nombre]
        return self.estructura[campo_filas], self.estructura[campo_columnas] if campo_columnas else 1

    @property
    def forma_texto(self):
        """«A: 2×3 · B: 3×4 → AB: 2×4.», con las dimensiones vigentes."""
        if self.estructura["operacion"] == "producto" and self.estructura["cantidad"] > 2:
            return " · ".join(f"{nombre}: {'×'.join(map(str, self.forma(nombre)))}" for nombre in self.configuracion["matrices"])
        return self.configuracion["forma_texto"].format(
            m=self.estructura["filas"], n=self.estructura["columnas"], p=self.estructura["columnas_b"],
        )

    def clean(self):
        datos = super().clean()
        self.rechazar_campos_repetidos()
        if self.errors or self.ajustar:
            return datos

        # Un control deshabilitado no viaja desde el navegador; si llega en el envío
        # de cálculo, el POST fue manipulado. Aplicar sí lo tolera: al cambiar de
        # operación aún puede enviarse la estructura anterior.
        ajenos = [
            _minuscula_inicial(self.fields[nombre].label or nombre) for nombre in ("columnas_b", "metodo", "cantidad")
            if self.fields[nombre].disabled and nombre in self.data
        ]
        if ajenos:
            self.add_error(None, f"Se recibieron campos que no corresponden a la operación seleccionada: {', '.join(ajenos)}. Pulsa Aplicar para ajustar la estructura.")
            return datos

        columnas_b = self.fields["columnas_b"]
        if not columnas_b.disabled and datos.get("columnas_b") is None:
            self.add_error("columnas_b", columnas_b.error_messages["required"])
        if self.configuracion["metodos"] and not datos.get("metodo"):
            self.add_error("metodo", "Selecciona un método.")
        if self.errors:
            return datos

        if not self.celdas_coinciden():
            self.add_error(None, "Las celdas recibidas no coinciden con las matrices, filas y columnas indicadas. Pulsa Aplicar para ajustar la estructura.")
            return datos

        numericos = [*self.nombres_celdas]
        if self.configuracion["escalar"]:
            numericos.append("escalar")
        self.convertir_numeros(datos, numericos)
        if self.errors:
            return datos

        entrada = {
            "operacion": datos["operacion"], "escalar": datos.get("escalar"),
            "metodo": datos["metodo"] if self.configuracion["metodos"] else None,
            "matrices": {},
        }
        for nombre in self.configuracion["matrices"]:
            valores = self.leer_matriz(datos, nombre, *self.forma(nombre))
            if es_vector(self.configuracion, nombre):
                # El vector se entrega como lista de componentes, no como matriz n×1.
                entrada["vector"] = [fila[0] for fila in valores]
            else:
                entrada["matrices"][nombre] = valores
        datos["entrada"] = entrada
        return datos

    def iniciales(self):
        """Conserva las celdas que sobreviven a Aplicar, sin arrastrar campos ajenos."""
        iniciales = {nombre: self.data.get(nombre, "") for nombre in self.fields}
        # Sin JavaScript, un control recién habilitado aún no viajó en el POST:
        # la estructura efectiva ya le asignó su valor inicial.
        iniciales.update(self.estructura)
        return iniciales
