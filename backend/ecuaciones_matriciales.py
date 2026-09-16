"""Ecuaciones matriciales Ax = b: A y b son conocidos y x es la incognita.

Una ecuacion matricial no es una operacion con matrices —en Ax de
`backend.matrices` el vector x ya se conoce y solo se multiplica— sino un
sistema de ecuaciones lineales escrito de otra manera. Estas cuatro formas
son equivalentes y este modulo las conecta:

    Ax = b  <->  x1*a1 + x2*a2 + ... + xn*an = b  <->  sistema lineal  <->  [A | b]

Aqui no hay un segundo solucionador: la matriz aumentada [A | b] se entrega a
`resolver_sistema_gauss` o `resolver_sistema_gauss_jordan` de
`backend.sistemas`, y la clasificacion del sistema decide si Ax = b tiene
solucion unica, infinitas o ninguna, es decir, si b es combinacion lineal de
las columnas de A. A m×n admite m = n, m < n y m > n; x tiene n componentes
y b tiene m. Este modulo es logica pura: recibe listas y devuelve listas o
diccionarios, o lanza ValueError con un mensaje legible.
"""

from fractions import Fraction

from backend.matrices import (
    contar,
    dimensiones,
    multiplicar_matriz_vector,
    trasponer_matriz,
    validar_matriz,
    validar_vector,
)
from backend.sistemas import (
    INCONSISTENTE,
    SOLUCION_UNICA,
    ecuaciones_de_matriz,
    resolver_sistema_gauss,
    resolver_sistema_gauss_jordan,
)

# Los mismos identificadores que Resolver un sistema; Gauss-Jordan es el predeterminado.
METODOS = {
    "gauss": resolver_sistema_gauss,
    "gauss_jordan": resolver_sistema_gauss_jordan,
}
METODO_PREDETERMINADO = "gauss_jordan"


def validar_ecuacion_matricial(a, b):
    """Devuelve (es_valida, mensaje): A es una matriz m×n y b un vector de m componentes."""
    es_valida, mensaje = validar_matriz(a)
    if not es_valida:
        return False, mensaje

    es_valido, mensaje = validar_vector(b, "b")
    if not es_valido:
        return False, mensaje

    filas, _ = dimensiones(a)
    if len(b) != filas:
        return False, (
            f"No se puede plantear Ax = b: A tiene {contar(filas, 'fila')} y b tiene "
            f"{contar(len(b), 'componente')}. Cada fila de A es una ecuación, así que b "
            "necesita una componente por fila."
        )

    return True, ""


def _exigir_ecuacion(a, b):
    es_valida, mensaje = validar_ecuacion_matricial(a, b)
    if not es_valida:
        raise ValueError(mensaje)


def matriz_aumentada_de_ax_b(a, b):
    """Escribe Ax = b como la matriz aumentada [A | b], con una fila por ecuación.

    La fila i es a_i1*x1 + ... + a_in*xn = b_i: los coeficientes de la fila i de
    A seguidos de la componente i de b. Se trabaja con listas y `Fraction`,
    nunca reconstruyendo la matriz desde texto.
    """
    _exigir_ecuacion(a, b)
    return [
        [Fraction(valor) for valor in fila] + [Fraction(componente)]
        for fila, componente in zip(a, b)
    ]


def columnas_de(a):
    """Las columnas a1, a2, ..., an de A como vectores (tuplas exactas)."""
    return tuple(tuple(columna) for columna in trasponer_matriz(a))


def resolver_ecuacion_matricial(a, b, metodo=METODO_PREDETERMINADO):
    """Resuelve Ax = b con el motor de sistemas indicado y lo lee como ecuación matricial.

    Devuelve el resultado completo de `resolver_sistema_gauss` o de
    `resolver_sistema_gauss_jordan` sobre [A | b] —pasos, matriz final,
    clasificación, columnas pivote, variables libres, solución general,
    contradicción y justificación— ampliado con la lectura propia de Ax = b:

    - `filas`, `columnas`: m y n, con x de n componentes y b de m;
    - `matriz_aumentada`: [A | b] exacta, y `ecuaciones`: el sistema
      equivalente con incógnitas x1, ..., xn;
    - `columnas_a`: las columnas de A, para la ecuación vectorial
      x1*a1 + ... + xn*an = b;
    - `x`: el vector solución cuando es única (None en otro caso);
    - `verificacion`: A·x calculado con `multiplicar_matriz_vector`, que debe
      coincidir con b, solo con solución única;
    - `b_en_generado`: si b es combinación lineal de las columnas de A, es
      decir, si el sistema es consistente.

    No se recalcula nada por otro camino: la clasificación del sistema es la
    única fuente de todas esas conclusiones.
    """
    try:
        resolver = METODOS[metodo]
    except (KeyError, TypeError):
        raise ValueError("Selecciona un método de resolución válido: Gauss o Gauss-Jordan.") from None

    matriz_aumentada = matriz_aumentada_de_ax_b(a, b)
    filas, columnas = dimensiones(a)
    resolucion = resolver(matriz_aumentada)

    x = None
    verificacion = None
    if resolucion["clasificacion"] == SOLUCION_UNICA:
        x = list(resolucion["soluciones"])
        verificacion = multiplicar_matriz_vector(a, x)

    return {
        "metodo": metodo,
        "filas": filas,
        "columnas": columnas,
        "matriz_aumentada": matriz_aumentada,
        "ecuaciones": ecuaciones_de_matriz(matriz_aumentada),
        "columnas_a": columnas_de(a),
        "b": [Fraction(componente) for componente in b],
        "x": x,
        "verificacion": verificacion,
        "b_en_generado": resolucion["clasificacion"] != INCONSISTENTE,
        **resolucion,
    }
