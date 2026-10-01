"""Reglas numéricas de tipos y dimensiones, compartidas por evaluación y presupuesto.

Solo inspeccionan metadatos: no hacen aritmética ni construyen matrices.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Forma:
    tipo: str
    filas: int | None = None
    columnas: int | None = None


def describir(valor, texto):
    if valor.tipo == "matriz":
        return f"{texto} es {valor.filas}×{valor.columnas}"
    if valor.tipo == "matriz_desconocida":
        return f"{texto} es la matriz desconocida {valor.filas}×{valor.columnas}"
    if valor.tipo == "vector":
        sufijo = "" if valor.filas == 1 else "s"
        return f"{texto} es un vector de {valor.filas} componente{sufijo}"
    if valor.tipo == "vector_simbolico":
        return f"{texto} es un vector simbólico de {valor.filas} componentes"
    if valor.tipo == "vector_lineal":
        sufijo = "" if valor.filas == 1 else "s"
        return f"{texto} es un vector lineal de {valor.filas} componente{sufijo}"
    if valor.tipo == "aplicacion":
        return f"{texto} es el producto de una matriz desconocida"
    return f"{texto} es un escalar"


def rechazar(texto, izq, der, izq_texto, der_texto, porque):
    raise ValueError(
        f"No se puede calcular {texto}: {describir(izq, izq_texto)} y {describir(der, der_texto)}. {porque}"
    )


def inferir_suma(texto, izq, der, izq_texto, der_texto):
    if izq.tipo != der.tipo or izq.tipo not in ("matriz", "vector", "escalar"):
        rechazar(texto, izq, der, izq_texto, der_texto,
                 "Solo se pueden sumar o restar matrices con matrices, vectores con vectores o escalares con escalares.")
    if izq.tipo == "matriz" and (izq.filas, izq.columnas) != (der.filas, der.columnas):
        rechazar(texto, izq, der, izq_texto, der_texto,
                 "Para sumar o restar, ambas matrices deben tener las mismas dimensiones.")
    if izq.tipo == "vector" and izq.filas != der.filas:
        rechazar(texto, izq, der, izq_texto, der_texto,
                 "Para sumar o restar vectores, ambos deben tener la misma dimensión.")
    return Forma(izq.tipo, izq.filas, izq.columnas)


def inferir_traspuesta(texto, operando, operando_texto):
    if operando.tipo != "matriz":
        sugerencia = (
            f" Para escribir {operando_texto} como fila, defínelo como una matriz de 1×{operando.filas}."
            if operando.tipo == "vector" else ""
        )
        raise ValueError(
            f"No se puede calcular {texto}: {describir(operando, operando_texto)}. "
            f"La traspuesta se aplica a matrices con entradas conocidas.{sugerencia}"
        )
    return Forma("matriz", operando.columnas, operando.filas)


def inferir_producto(texto, izq, der, izq_texto, der_texto):
    par = (izq.tipo, der.tipo)
    if izq.tipo == "escalar" or der.tipo == "escalar":
        otro = der if izq.tipo == "escalar" else izq
        if otro.tipo in ("escalar", "matriz", "vector"):
            return Forma(otro.tipo, otro.filas, otro.columnas)
    if par == ("matriz", "matriz"):
        if izq.columnas != der.filas:
            rechazar(texto, izq, der, izq_texto, der_texto,
                     "Para multiplicar matrices, las columnas de la primera deben coincidir con las filas de la segunda.")
        return Forma("matriz", izq.filas, der.columnas)
    if par == ("matriz", "vector"):
        if izq.columnas != der.filas:
            rechazar(texto, izq, der, izq_texto, der_texto,
                     "Para multiplicar una matriz por un vector, las columnas de la matriz deben coincidir con las componentes del vector.")
        return Forma("vector", izq.filas)
    motivos = {
        ("vector", "vector"): "El producto de dos vectores no está definido aquí; el producto punto no se infiere.",
        ("vector", "matriz"): "El producto de un vector por una matriz no está definido en esta herramienta.",
    }
    rechazar(texto, izq, der, izq_texto, der_texto,
             motivos.get(par, "Esa combinación de tipos no tiene producto en esta herramienta."))
