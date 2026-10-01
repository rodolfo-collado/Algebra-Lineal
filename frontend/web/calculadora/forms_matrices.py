"""Entrada visual de matrices y validación del contrato HTTP de su estructura.

La comparten Operaciones con matrices, Resolver Ax = b y Matriz inversa.
"""

from django import forms

from backend.parser_sistemas import convertir_a_numero

from .opciones_matrices import DIMENSION_MAXIMA, DIMENSION_MINIMA, DIMENSION_PREDETERMINADA


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
                    datos[nombre] = convertir_a_numero(texto, limitar_entrada=True)
                except ValueError as error:
                    self.add_error(nombre, str(error))

    @staticmethod
    def leer_matriz(datos, nombre, alto, ancho):
        return [[datos[f"celda_{nombre}_{i}_{j}"] for j in range(ancho)] for i in range(alto)]
