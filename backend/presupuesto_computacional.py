"""Presupuesto computacional: cuánto trabajo pide una operación válida, sin ejecutarla.

No es un límite. `presupuesto_sistemas` y `operandos` rechazan entradas que la
interfaz no puede representar o que serían peligrosas de leer; esta estimación
describe lo que costará una entrada ya aceptada, para que una interfaz pueda
avisar antes de ejecutar. Un costo alto no convierte una entrada en inválida.

Separa dos trabajos que crecen distinto:

- cálculo: operaciones aritméticas con números exactos;
- procedimiento: valores que los pasos conservan y que luego se presentan. En
  Gauss y Gauss-Jordan cada paso guarda la matriz antes y después, así que un
  motor rápido no garantiza que mostrar el procedimiento sea barato.

Las cantidades son cotas del peor caso denso y no dependen del equipo. El
tiempo sí: se deriva aparte, con referencias calibrables. Estimar no recorre
filas, no ejecuta ningún motor y no convierte números a texto.
"""

from bisect import bisect_right
from dataclasses import dataclass
from enum import IntEnum
from typing import NamedTuple

# Referencias de calibración medidas en el equipo de desarrollo (Windows, Python
# 3.13) con scripts/benchmark_presupuesto.py, incluido su POST completo (--web).
# Ordenan y agrupan costos; no garantizan tiempos en ningún equipo.
REFERENCIA_SEGUNDOS_OPERACION = 1e-6  # una operación con números pequeños
REFERENCIA_SEGUNDOS_CELDA = 9e-5  # conservar, adaptar y mostrar en HTML un valor del procedimiento
REFERENCIA_MARGEN = 3  # el intervalo va de la referencia / 3 a la referencia × 3
# Límites de categoría en segundos de referencia: 1 s ya se nota; 10 s agota la espera.
REFERENCIA_UMBRALES = (1, 3, 10)
# Tamaño de los números: la aritmética crece más que lineal con sus bits
# (1 + (bits / 1000) ** 1.25, ajustado con Gauss-Jordan y AB); el texto que se
# muestra, linealmente (1 + bits / 7000, ajustado con el POST completo).
REFERENCIA_BITS = 1000
REFERENCIA_EXPONENTE = 1.25
REFERENCIA_BITS_TEXTO = 7000


class PerfilNumerico(NamedTuple):
    """Tamaño de las entradas en bits: el mayor numerador y el mayor denominador."""

    bits_numerador: int = 0
    bits_denominador: int = 0


@dataclass(frozen=True)
class Estimacion:
    """Trabajo previsto. `calculo` y `procedimiento` ya incluyen el efecto del tamaño
    de los números (`factor_numerico` es el del cálculo), así que una estimación
    compuesta solo los suma."""

    operacion: str
    dimensiones: tuple[int, ...]
    pasos: int
    calculo: float
    procedimiento: float
    factor_numerico: float = 1.0
    partes: tuple["Estimacion", ...] = ()


class Categoria(IntEnum):
    """Para decidir si avisar antes de ejecutar; los textos visibles los pone la interfaz."""

    NORMAL = 0
    PERCEPTIBLE = 1
    PESADA = 2
    MUY_PESADA = 3


def perfil_numerico(*matrices):
    """Perfil de una o varias matrices (listas de filas) de int o Fraction.

    `bit_length` no depende del tamaño del número: medir es barato incluso con
    valores enormes, y nada se convierte a texto.
    """
    numerador = denominador = 0
    for matriz in matrices:
        for fila in matriz:
            for valor in fila:
                numerador = max(numerador, valor.numerator.bit_length())
                # Un entero (denominador 1) no aporta bits.
                denominador = max(denominador, valor.denominator.bit_length() - 1)
    return PerfilNumerico(numerador, denominador)


def _exigir_dimensiones(*dimensiones):
    if any(type(valor) is not int or valor < 1 for valor in dimensiones):
        raise ValueError("Las dimensiones de una estimación deben ser enteros positivos.")


def _factor_numerico(bits_efectivos):
    """Cuánto más cuesta operar con esos bits que con números pequeños (1 = igual)."""
    return 1 + (bits_efectivos / REFERENCIA_BITS) ** REFERENCIA_EXPONENTE


def _factor_texto(bits_efectivos):
    """Cuánto más cuesta mostrar un valor de ese tamaño: crece con la longitud de su texto."""
    return 1 + bits_efectivos / REFERENCIA_BITS_TEXTO


def _reduccion(operacion, filas, columnas, columnas_pivote, perfil, hacia_arriba):
    if columnas_pivote is None:
        columnas_pivote = columnas
    _exigir_dimensiones(filas, columnas, columnas_pivote)
    if columnas_pivote > columnas:
        raise ValueError("Las columnas con pivote no pueden superar las columnas de la matriz.")

    # Peor caso denso: cada columna admitida tiene pivote distinto de 1 y ninguna
    # entrada que eliminar vale cero. Un intercambio no añade pasos: la fila que
    # baja trae un cero en esa columna y ya no hay que eliminarla.
    pivotes = min(filas, columnas_pivote)
    eliminaciones = pivotes * (filas - 1) - pivotes * (pivotes - 1) // 2
    if hacia_arriba:
        eliminaciones += pivotes * (pivotes - 1) // 2
    pasos = pivotes + eliminaciones
    # Normalizar divide toda la fila; eliminar multiplica y resta en cada columna.
    operaciones = columnas * (pivotes + 2 * eliminaciones)
    # Cada paso registra la matriz antes y después.
    celdas = 2 * filas * columnas * pasos

    # Los racionales crecen con cada eliminación, y al combinar filas se acumulan
    # los denominadores de sus columnas.
    perfil = perfil or PerfilNumerico()
    bits = pivotes * (perfil.bits_numerador + (columnas - 1) * perfil.bits_denominador)
    factor = _factor_numerico(bits)
    return Estimacion(
        operacion, (filas, columnas), pasos, operaciones * factor, celdas * _factor_texto(bits), factor
    )


def estimar_gauss(filas, columnas, *, columnas_pivote=None, perfil=None):
    """Escalonar como `aplicar_gauss`, sin escalonar. Solo elimina hacia abajo."""
    return _reduccion("gauss", filas, columnas, columnas_pivote, perfil, hacia_arriba=False)


def estimar_gauss_jordan(filas, columnas, *, columnas_pivote=None, perfil=None):
    """Reducir como `aplicar_gauss_jordan`: el escalonamiento más la eliminación hacia arriba.

    Sirve igual para [A | b] (columnas_pivote = variables) que para aumentos de
    varias columnas como [A | I] (columnas_pivote = columnas de A).
    """
    return _reduccion("gauss_jordan", filas, columnas, columnas_pivote, perfil, hacia_arriba=True)


# Los mismos identificadores de método que Resolver un sistema y Ax = b.
ESTIMADORES = {"gauss": estimar_gauss, "gauss_jordan": estimar_gauss_jordan}


def estimar_producto(filas, comunes, columnas, *, perfil=None):
    """AB con A filas×comunes y B comunes×columnas, como `resolver_operacion_matrices`.

    El cálculo son los productos y sumas de cada entrada; el procedimiento, la
    evidencia de las dos lecturas del producto (fila por columna y por columnas).
    Ax es el caso de una sola columna.
    """
    _exigir_dimensiones(filas, comunes, columnas)
    entradas = filas * columnas
    operaciones = 2 * entradas * comunes
    # Por entrada: fila, columna, productos y resultado. Por columna: coeficientes,
    # columnas de A escaladas y resultado. Además, las columnas de A.
    celdas = (
        entradas * (3 * comunes + 1)
        + columnas * (comunes * filas + comunes + filas)
        + filas * comunes
    )
    # Cada producto suma los tamaños de sus factores y la suma de una entrada
    # acumula los denominadores de sus términos.
    perfil = perfil or PerfilNumerico()
    bits = 2 * perfil.bits_numerador + comunes * perfil.bits_denominador
    factor = _factor_numerico(bits)
    return Estimacion(
        "producto", (filas, comunes, columnas), entradas,
        operaciones * factor, celdas * _factor_texto(bits), factor,
    )


def combinar_estimaciones(*estimaciones, operacion="compuesta"):
    """Ejecutar varias operaciones seguidas cuesta la suma de sus costos.

    Las partes se conservan para explicar de dónde sale el total; el factor
    numérico del conjunto es el de la parte con números más grandes.
    """
    if not estimaciones:
        raise ValueError("Combina al menos una estimación.")
    return Estimacion(
        operacion,
        (),
        sum(parte.pasos for parte in estimaciones),
        sum(parte.calculo for parte in estimaciones),
        sum(parte.procedimiento for parte in estimaciones),
        max(parte.factor_numerico for parte in estimaciones),
        tuple(estimaciones),
    )


def segundos_referencia(estimacion):
    """Tiempo en el equipo de referencia. Orienta; no es una promesa para otro equipo."""
    return (
        estimacion.calculo * REFERENCIA_SEGUNDOS_OPERACION
        + estimacion.procedimiento * REFERENCIA_SEGUNDOS_CELDA
    )


def intervalo_segundos(estimacion):
    """Un intervalo amplio en vez de un número: el equipo, los valores y los ceros cambian el tiempo real."""
    segundos = segundos_referencia(estimacion)
    return segundos / REFERENCIA_MARGEN, segundos * REFERENCIA_MARGEN


def categoria(estimacion):
    """Normal, perceptible, pesada o muy pesada según los segundos de referencia."""
    return Categoria(bisect_right(REFERENCIA_UMBRALES, segundos_referencia(estimacion)))
