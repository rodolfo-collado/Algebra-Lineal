"""Jacobi y Gauss-Seidel con los despejes de Ax = b en el orden de entrada."""

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from numbers import Rational, Real
from sys import float_info

from backend.presupuesto_sistemas import validar_dimensiones

METODOS = (("jacobi", "Jacobi"), ("gauss_seidel", "Gauss-Seidel"))
TOLERANCIA = Fraction(1, 10_000)
ITERACIONES_PREDETERMINADAS = 100
ITERACIONES_MAXIMAS = 500


@dataclass(frozen=True)
class Termino:
    columna: int
    coeficiente: float
    usa_nuevo: bool


@dataclass(frozen=True)
class Despeje:
    independiente: float
    diagonal: float
    terminos: tuple[Termino, ...]


@dataclass(frozen=True)
class Iteracion:
    k: int
    x: tuple[float, ...]
    cambio: float | None
    residuo: tuple[Fraction, ...]
    norma_residuo: Fraction


@dataclass(frozen=True)
class ResultadoIterativo:
    metodo: str
    estado: str
    tolerancia: Fraction
    limite: int
    filas_no_dominantes: tuple[int, ...]
    despejes: tuple[Despeje, ...]
    iteraciones: tuple[Iteracion, ...]

    @property
    def final(self):
        return self.iteraciones[-1]


def _finito(valor, mensaje):
    if isinstance(valor, bool) or not isinstance(valor, Real):
        raise ValueError(mensaje)
    try:
        numero = float(valor)
    except OverflowError:
        raise ValueError(mensaje) from None
    if not isfinite(numero) or (numero == 0 and valor != 0):
        raise ValueError(mensaje)
    return numero


def _vector(valores, n):
    if not isinstance(valores, Sequence) or len(valores) != n:
        raise ValueError(f"El vector debe tener {n} componentes.")
    return tuple(_finito(valor, "A, b y x inicial deben contener números finitos representables.")
                 for valor in valores)


def _exacto(valor):
    return Fraction(valor) if isinstance(valor, Rational) else Fraction(float(valor))


def _registrar(k, a, b, x, cambio=None):
    # Se comprueba el vector realmente obtenido contra los coeficientes ingresados.
    x_exacto = tuple(Fraction(xi) for xi in x)
    residuo = tuple(bi - sum(aij * xj for aij, xj in zip(fila, x_exacto))
                    for fila, bi in zip(a, b))
    norma = max(abs(ri) for ri in residuo)
    if norma > float_info.max:
        return None
    return Iteracion(k, tuple(x), cambio, residuo, norma)


def resolver_iterativo(a, b, metodo, *, inicial=None, tolerancia=TOLERANCIA,
                       max_iteraciones=ITERACIONES_PREDETERMINADAS):
    """Resuelve con aritmética de máquina y conserva fila inicial y aproximaciones finitas."""
    if metodo not in ("jacobi", "gauss_seidel"):
        raise ValueError("Elige Jacobi o Gauss-Seidel.")
    if not isinstance(a, Sequence) or not a:
        raise ValueError("Ingresa una matriz A cuadrada.")
    n = len(a)
    validar_dimensiones(n, n)
    if any(not isinstance(fila, Sequence) or len(fila) != n for fila in a):
        raise ValueError("Jacobi y Gauss-Seidel requieren una matriz A cuadrada.")
    if type(max_iteraciones) is not int or not 1 <= max_iteraciones <= ITERACIONES_MAXIMAS:
        raise ValueError(f"Indica entre 1 y {ITERACIONES_MAXIMAS} iteraciones.")
    mensaje_tolerancia = "La tolerancia debe ser un número finito y positivo."
    if _finito(tolerancia, mensaje_tolerancia) <= 0:
        raise ValueError(mensaje_tolerancia)
    tolerancia = _exacto(tolerancia)

    a_numerica = tuple(_vector(fila, n) for fila in a)
    b_numerico = _vector(b, n)
    a_exacta = tuple(tuple(_exacto(valor) for valor in fila) for fila in a)
    b_exacto = tuple(_exacto(valor) for valor in b)
    anterior = (0.0,) * n if inicial is None else _vector(inicial, n)
    despejes = []
    filas_no_dominantes = []
    for i, (fila, exacta) in enumerate(zip(a_numerica, a_exacta)):
        diagonal = fila[i]
        if diagonal == 0:
            raise ValueError(
                f"El coeficiente diagonal de la fila {i + 1} es cero. "
                "Revisa el orden de las ecuaciones."
            )
        terminos = tuple(Termino(j, coef, metodo == "gauss_seidel" and j < i)
                         for j, coef in enumerate(fila) if j != i and coef != 0)
        despejes.append(Despeje(b_numerico[i], diagonal, terminos))
        if abs(exacta[i]) <= sum(abs(exacta[t.columna]) for t in terminos):
            filas_no_dominantes.append(i + 1)

    primera = _registrar(0, a_exacta, b_exacto, anterior)
    if primera is None:
        raise ValueError("El residuo inicial supera el rango numérico. Revisa A, b y el vector inicial.")
    iteraciones = [primera]
    estado = "limite"
    for k in range(1, max_iteraciones + 1):
        nuevo = [0.0] * n
        for i, despeje in enumerate(despejes):
            if metodo == "jacobi":
                suma = sum(t.coeficiente * anterior[t.columna] for t in despeje.terminos)
                nuevo[i] = (despeje.independiente - suma) / despeje.diagonal
            else:
                suma_nueva = sum(t.coeficiente * nuevo[t.columna] for t in despeje.terminos if t.usa_nuevo)
                suma_anterior = sum(t.coeficiente * anterior[t.columna] for t in despeje.terminos if not t.usa_nuevo)
                nuevo[i] = (despeje.independiente - suma_nueva - suma_anterior) / despeje.diagonal

        cambio = max(abs(nuevo[i] - anterior[i]) for i in range(n))
        fila = (_registrar(k, a_exacta, b_exacto, nuevo, cambio)
                if all(map(isfinite, (*nuevo, cambio))) else None)
        if fila is None:
            estado = "rango"
            break
        iteraciones.append(fila)
        if cambio < tolerancia and fila.norma_residuo < tolerancia:
            estado = "convergio"
            break
        anterior = fila.x

    return ResultadoIterativo(metodo, estado, tolerancia, max_iteraciones,
                              tuple(filas_no_dominantes), tuple(despejes), tuple(iteraciones))
