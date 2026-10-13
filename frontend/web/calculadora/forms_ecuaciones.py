"""Entrada de «Resolver Ax = b»: A y b editables, x como incógnita.

El contrato HTTP deriva todo de las dimensiones de A: b debe llegar con
exactamente m componentes y x no viaja en el POST porque es lo que se busca.
Comparte con Operaciones con matrices las celdas, el parser y las comprobaciones
de estructura (`FormularioCeldas`), pero es un formulario aparte: la ecuación
matricial no es una operación más.
"""

from django import forms

from backend.ecuaciones_matriciales import MENSAJE_CRAMER_CUADRADA, MENSAJE_LU_CUADRADA
from .forms_determinantes import METODOS as METODOS_DETERMINANTES, RadiosPorTamano, metodo_disponible, metodo_sugerido
from .forms_matrices import FormularioCeldas, campo_dimension
from .opciones_ecuaciones import ENTRADAS, METODO_PREDETERMINADO, METODOS, forma_texto
from .servicios_ecuaciones import vector_incognita


class RadiosEcuacion(forms.RadioSelect):
    cuadrada = True

    def create_option(self, *args, **kwargs):
        opcion = super().create_option(*args, **kwargs)
        if opcion["value"] == "cramer" and not self.cuadrada:
            opcion["attrs"]["disabled"] = True
        return opcion


class EcuacionMatricialForm(FormularioCeldas):
    filas = campo_dimension("Filas de A")
    columnas = campo_dimension("Columnas de A")
    metodo = forms.ChoiceField(
        label="Método", choices=METODOS, initial=METODO_PREDETERMINADO, widget=RadiosEcuacion,
        error_messages={"required": "Selecciona un método.", "invalid_choice": "Selecciona un método válido."},
    )
    metodo_determinante = forms.ChoiceField(
        label="Método para los determinantes", choices=METODOS_DETERMINANTES,
        required=False, widget=RadiosPorTamano,
        error_messages={"invalid_choice": "Selecciona un método válido para los determinantes."},
    )
    confirmacion = forms.CharField(required=False, strip=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La estructura vigente decide qué celdas existen: A es m×n, b es m×1 y x muestra n incógnitas.
        self.estructura = {nombre: self._valor_seguro(nombre) for nombre in ("filas", "columnas", "metodo")}
        orden = self.estructura["filas"]
        cuadrada = orden == self.estructura["columnas"]
        self.fields["metodo"].widget.cuadrada = cuadrada
        self.fields["metodo_determinante"].widget.orden = orden
        self.fields["metodo_determinante"].initial = metodo_sugerido(orden)
        if self.is_bound:
            self.data = self.data.copy()
            if self.ajustar and not cuadrada and self.estructura["metodo"] == "cramer":
                # Como ecuaciones.js: Aplicar a una A rectangular no deja Cramer marcado y desactivado.
                self.data["metodo"] = self.estructura["metodo"] = METODO_PREDETERMINADO
            elegido = self.data.get("metodo_determinante")
            if not elegido or (self.ajustar and not metodo_disponible(elegido, orden)):
                self.data["metodo_determinante"] = metodo_sugerido(orden)
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
            self.grupo_error = "equation-entry"
            self.add_error(None, "Las celdas recibidas no coinciden con las dimensiones de A y de b. Pulsa Aplicar para ajustar la estructura.")
            return datos

        self.convertir_numeros(datos, self.nombres_celdas)
        if self.errors:
            return datos

        matriz, vector = ENTRADAS
        filas, columnas = self.estructura["filas"], self.estructura["columnas"]
        if datos["metodo"] == "lu" and filas != columnas:
            self.add_error("metodo", MENSAJE_LU_CUADRADA)
            return datos
        if datos["metodo"] == "cramer":
            if filas != columnas:
                self.add_error("metodo", MENSAJE_CRAMER_CUADRADA)
                return datos
            if not metodo_disponible(datos["metodo_determinante"], filas):
                self.add_error("metodo_determinante", "El método de determinante no está disponible para el tamaño de A. Elige otro método.")
                return datos
        datos["entrada"] = {
            "a": self.leer_matriz(datos, matriz, filas, columnas),
            # b se entrega como lista de componentes, no como matriz m×1.
            "b": [fila[0] for fila in self.leer_matriz(datos, vector, filas, 1)],
            "metodo": datos["metodo"],
        }
        if datos["metodo"] == "cramer":
            datos["entrada"]["metodo_determinante"] = datos["metodo_determinante"]
        return datos

    def iniciales(self):
        """Conserva las celdas que sobreviven a Aplicar; la estructura ya está saneada."""
        iniciales = {nombre: self.data.get(nombre, "") for nombre in self.fields if nombre != "confirmacion"}
        iniciales.update(self.estructura)
        return iniciales
