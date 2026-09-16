"""Entrada de «Resolver Ax = b»: A y b editables, x como incógnita.

El contrato HTTP deriva todo de las dimensiones de A: b debe llegar con
exactamente m componentes y x no viaja en el POST porque es lo que se busca.
Comparte con Operaciones con matrices las celdas, el parser y las comprobaciones
de estructura (`FormularioCeldas`), pero es un formulario aparte: la ecuación
matricial no es una operación más.
"""

from django import forms

from .forms_matrices import FormularioCeldas, campo_dimension
from .opciones_ecuaciones import ENTRADAS, METODO_PREDETERMINADO, METODOS, forma_texto
from .servicios_ecuaciones import vector_incognita


class EcuacionMatricialForm(FormularioCeldas):
    filas = campo_dimension("Filas de A")
    columnas = campo_dimension("Columnas de A")
    metodo = forms.ChoiceField(
        label="Método", choices=METODOS, initial=METODO_PREDETERMINADO, widget=forms.RadioSelect,
        error_messages={"required": "Selecciona un método.", "invalid_choice": "Selecciona un método válido."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La estructura vigente decide qué celdas existen: A es m×n, b es m×1 y x muestra n incógnitas.
        self.estructura = {nombre: self._valor_seguro(nombre) for nombre in ("filas", "columnas", "metodo")}
        matriz, vector = ENTRADAS
        self.generar_celdas(matriz, self.estructura["filas"], self.estructura["columnas"])
        self.generar_celdas(vector, self.estructura["filas"], 1, vector=True)
        self.incognitas = vector_incognita(self.estructura["columnas"])

    @property
    def forma_texto(self):
        """«A (3×2) · x (2) = b (3)», con las dimensiones vigentes."""
        return forma_texto(self.estructura["filas"], self.estructura["columnas"])

    def clean(self):
        datos = super().clean()
        self.rechazar_campos_repetidos()
        if self.errors or self.ajustar:
            return datos

        if not self.celdas_coinciden():
            self.add_error(None, "Las celdas recibidas no coinciden con las dimensiones de A y de b. Pulsa Aplicar para ajustar la estructura.")
            return datos

        self.convertir_numeros(datos, self.nombres_celdas)
        if self.errors:
            return datos

        matriz, vector = ENTRADAS
        filas, columnas = self.estructura["filas"], self.estructura["columnas"]
        datos["entrada"] = {
            "a": self.leer_matriz(datos, matriz, filas, columnas),
            # b se entrega como lista de componentes, no como matriz m×1.
            "b": [fila[0] for fila in self.leer_matriz(datos, vector, filas, 1)],
            "metodo": datos["metodo"],
        }
        return datos

    def iniciales(self):
        """Conserva las celdas que sobreviven a Aplicar; la estructura ya está saneada."""
        iniciales = {nombre: self.data.get(nombre, "") for nombre in self.fields}
        iniciales.update(self.estructura)
        return iniciales
