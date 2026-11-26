"""Entrada de Jacobi y Gauss-Seidel para sistemas cuadrados.

El sistema llega como ecuaciones (el mismo campo y el mismo parser que Reducción
por filas) o como A y b en celdas; las dos formas terminan en la misma entrada.
"""

from django import forms

from backend.parser_sistemas import analizar_sistema, convertir_a_numero
from backend.sistemas_iterativos import ITERACIONES_MAXIMAS, ITERACIONES_PREDETERMINADAS, METODOS, TOLERANCIA

from .forms import SistemaForm
from .forms_ecuaciones import SistemaMatricialForm
from .servicios_iterativos import COMPARAR_ITERATIVOS


def _plural(cantidad, singular, plural):
    return f"{cantidad} {singular if cantidad == 1 else plural}"


class SistemasIterativosForm(SistemaMatricialForm):
    # Matriz primero en v0.20.1: sin tipo_entrada (POST antiguos, ejemplos) se leen las celdas.
    tipo_entrada = forms.ChoiceField(
        label="Tipo de entrada", choices=(("sistema", "Sistema de ecuaciones"), ("matriz", "Matriz A y vector b")),
        initial="matriz", required=False, widget=forms.RadioSelect,
    )
    sistema = SistemaForm.base_fields["sistema"]
    clean_sistema = SistemaForm.clean_sistema
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
        if self.cleaned_data.get("tipo_entrada") == "sistema" and not self.ajustar:
            return self._clean_ecuaciones(self.cleaned_data)
        datos = super().clean()
        if "entrada" not in datos:
            return datos

        filas, columnas = self.estructura["filas"], self.estructura["columnas"]
        if filas != columnas:
            self.add_error("metodo", "Jacobi y Gauss-Seidel requieren una matriz A cuadrada.")
        datos["entrada"].update(self._opciones_iterativas(datos, columnas))
        return datos

    def _clean_ecuaciones(self, datos):
        """A y b desde el texto, con las reglas y el presupuesto del parser de Gauss."""
        # Las dimensiones de A pertenecen a la entrada escondida: no bloquean el texto.
        for nombre in ("filas", "columnas"):
            self.errors.pop(nombre, None)
        self.rechazar_campos_repetidos()
        if self.errors:
            return datos
        if not datos.get("sistema"):
            self.add_error("sistema", "Ingresa un sistema de ecuaciones.")
            return datos
        try:
            matriz, _ = analizar_sistema(datos["sistema"], limitar_entrada=True)
        except ValueError as error:
            self.add_error("sistema", str(error))
            return datos

        ecuaciones, incognitas = len(matriz), len(matriz[0]) - 1
        if ecuaciones != incognitas:
            self.add_error("sistema", (
                f"El sistema tiene {_plural(ecuaciones, 'ecuación', 'ecuaciones')} y "
                f"{_plural(incognitas, 'incógnita', 'incógnitas')}{f' (x1 a x{incognitas})' if incognitas > 1 else ''}: "
                "Jacobi y Gauss-Seidel requieren tantas ecuaciones como incógnitas."
            ))
            return datos
        datos["entrada"] = {
            "a": [fila[:-1] for fila in matriz], "b": [fila[-1] for fila in matriz], "metodo": datos["metodo"],
            **self._opciones_iterativas(datos, incognitas),
        }
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
