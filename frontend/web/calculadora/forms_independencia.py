"""Cuadrículas de vectores con el presupuesto de un sistema aumentado."""

import re

from django.core.exceptions import ValidationError

from backend.presupuesto_sistemas import (
    CELDAS_MAXIMAS,
    ECUACIONES_MAXIMAS,
    VARIABLES_MAXIMAS,
    dimensiones_admitidas,
    validar_dimensiones,
)
from backend.vectores import nombres_generadores

from .forms_matrices import FormularioCeldas, campo_dimension

_CELDA = re.compile(r"celda_v([1-9][0-9]?)_([0-9]{1,2})_0")


class IndependenciaForm(FormularioCeldas):
    dimension = campo_dimension("Componentes por vector", maximo=ECUACIONES_MAXIMAS)
    cantidad = campo_dimension("Cantidad de vectores", maximo=VARIABLES_MAXIMAS)
    celdas_maximas = CELDAS_MAXIMAS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dimension = self._valor_seguro("dimension")
        cantidad = self._valor_seguro("cantidad")
        if not dimensiones_admitidas(dimension, cantidad):
            dimension, cantidad = self._estructura_recibida()
        self.estructura = {"dimension": dimension, "cantidad": cantidad}
        for nombre in nombres_generadores(cantidad):
            self.generar_celdas(nombre, dimension, 1, vector=True)

    def _estructura_recibida(self):
        """Recobra la cuadrícula anterior al intentar un tamaño fuera del presupuesto."""
        celdas = [celda.groups() for nombre in self.data if (celda := _CELDA.fullmatch(nombre))]
        if celdas:
            dimension = max(int(fila) for _, fila in celdas) + 1
            cantidad = max(int(vector) for vector, _ in celdas)
            if dimensiones_admitidas(dimension, cantidad):
                return dimension, cantidad
        return self.fields["dimension"].initial, self.fields["cantidad"].initial

    def clean(self):
        datos = super().clean()
        self.rechazar_campos_repetidos()
        if self.errors:
            return datos
        try:
            validar_dimensiones(datos["dimension"], datos["cantidad"])
        except ValueError as error:
            self.grupo_error = "vector-entry"
            raise ValidationError(str(error)) from error

        if self.ajustar:
            return datos
        if not self.celdas_coinciden():
            self.grupo_error = "vector-entry"
            self.add_error(None, "Las celdas no coinciden con la cantidad de vectores o sus componentes. Pulsa Aplicar para ajustar la entrada.")
            return datos

        self.convertir_numeros(datos, self.nombres_celdas)
        if not self.errors:
            datos["vectores"] = [
                [fila[0] for fila in self.leer_matriz(datos, matriz["nombre"], datos["dimension"], 1)]
                for matriz in self.matrices
            ]
        return datos

    def iniciales(self):
        return {**{nombre: self.data.get(nombre, "") for nombre in self.nombres_celdas}, **self.estructura}
