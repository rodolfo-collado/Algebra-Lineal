"""Política de entrada compartida; cuenta también duplicados antes de construir valores."""

from dataclasses import dataclass

from backend.operandos import CELDAS_MAXIMAS, OPERANDOS_MAXIMOS
from backend.presupuesto_sistemas import LONGITUD_SISTEMA_MAXIMA

VOLUMEN_MAXIMO = CELDAS_MAXIMAS * OPERANDOS_MAXIMOS


@dataclass
class Presupuesto:
    caracteres: int = 0
    entradas: int = 0
    calculo: int = 0
    procedimiento: int = 0

    def reservar(self, *, calculo=0, procedimiento=0):
        if self.calculo + calculo > VOLUMEN_MAXIMO:
            raise ValueError("La expresión supera el presupuesto acumulado de cálculo de conjuntos.")
        if self.procedimiento + procedimiento > VOLUMEN_MAXIMO:
            raise ValueError("La expresión supera el presupuesto acumulado del procedimiento de conjuntos.")
        self.calculo += calculo
        self.procedimiento += procedimiento

    def texto(self, texto):
        self.longitud(len(texto))

    def longitud(self, cantidad):
        self.caracteres += cantidad
        if self.caracteres > LONGITUD_SISTEMA_MAXIMA:
            raise ValueError(f"La entrada completa admite hasta {LONGITUD_SISTEMA_MAXIMA} caracteres.")

    def elemento(self, profundidad):
        self.entradas += 1
        if self.entradas > CELDAS_MAXIMAS:
            raise ValueError(f"La entrada admite hasta {CELDAS_MAXIMAS} elementos y contenedores, contando repetidos.")
        if profundidad >= OPERANDOS_MAXIMOS:
            raise ValueError(f"La entrada admite hasta {OPERANDOS_MAXIMOS} niveles de conjuntos y agrupaciones.")
