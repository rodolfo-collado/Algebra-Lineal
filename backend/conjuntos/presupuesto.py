"""Política de entrada compartida; cuenta también duplicados antes de construir valores."""

from dataclasses import dataclass

from backend.operandos import CELDAS_MAXIMAS, OPERANDOS_MAXIMOS
from backend.presupuesto_sistemas import LONGITUD_SISTEMA_MAXIMA


@dataclass
class Presupuesto:
    caracteres: int = 0
    entradas: int = 0

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
