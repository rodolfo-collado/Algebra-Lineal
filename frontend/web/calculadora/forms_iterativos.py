"""Entrada de Jacobi y Gauss-Seidel para sistemas cuadrados."""

from django import forms

from backend.parser_sistemas import convertir_a_numero
from backend.sistemas_iterativos import ITERACIONES_MAXIMAS, ITERACIONES_PREDETERMINADAS, METODOS, TOLERANCIA

from .forms_ecuaciones import SistemaMatricialForm
from .servicios_iterativos import COMPARAR_ITERATIVOS


class SistemasIterativosForm(SistemaMatricialForm):
    metodo = forms.ChoiceField(
        label="Método", choices=(*METODOS, (COMPARAR_ITERATIVOS, "Comparar ambos")),
        initial="jacobi", widget=forms.RadioSelect,
        error_messages={"required": "Selecciona un método.", "invalid_choice": "Selecciona un método válido."},
    )
    inicial_iterativo = forms.CharField(
        label="Vector inicial", required=False, max_length=2100,
        widget=forms.TextInput(attrs={"class": "field-input", "aria-describedby": "ayuda-inicial-iterativo"}),
    )
    tolerancia_iterativa = forms.CharField(
        label="Tolerancia", required=False, initial=str(float(TOLERANCIA)), max_length=210,
        widget=forms.TextInput(attrs={"class": "field-input", "inputmode": "decimal"}),
    )
    max_iteraciones = forms.CharField(
        label="Máximo de iteraciones", required=False, initial=ITERACIONES_PREDETERMINADAS, max_length=12,
        widget=forms.NumberInput(attrs={
            "class": "field-input", "min": "1", "max": str(ITERACIONES_MAXIMAS), "inputmode": "numeric",
        }),
    )

    def clean(self):
        datos = super().clean()
        if "entrada" not in datos:
            return datos

        filas, columnas = self.estructura["filas"], self.estructura["columnas"]
        if filas != columnas:
            self.add_error("metodo", "Jacobi y Gauss-Seidel requieren una matriz A cuadrada.")
        datos["entrada"].update(self._opciones_iterativas(datos, columnas))
        return datos

    def _opciones_iterativas(self, datos, orden):
        inicial = datos["inicial_iterativo"].split()
        if inicial and len(inicial) != orden:
            self.add_error("inicial_iterativo", f"Escribe {orden} componentes separadas por espacios.")
        elif inicial:
            try:
                inicial = [convertir_a_numero(valor, limitar_entrada=True) for valor in inicial]
            except ValueError as error:
                self.add_error("inicial_iterativo", str(error))

        tolerancia = TOLERANCIA
        if datos["tolerancia_iterativa"]:
            try:
                tolerancia = convertir_a_numero(datos["tolerancia_iterativa"], limitar_entrada=True)
                if tolerancia <= 0:
                    raise ValueError("La tolerancia debe ser positiva.")
            except ValueError as error:
                self.add_error("tolerancia_iterativa", str(error))

        limite = ITERACIONES_PREDETERMINADAS
        if datos["max_iteraciones"]:
            try:
                limite = int(datos["max_iteraciones"])
                if not 1 <= limite <= ITERACIONES_MAXIMAS:
                    raise ValueError
            except ValueError:
                self.add_error("max_iteraciones", f"Escribe un entero de 1 a {ITERACIONES_MAXIMAS}.")

        return {"inicial": inicial or None, "tolerancia": tolerancia, "max_iteraciones": limite}
