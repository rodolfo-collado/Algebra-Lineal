"""Formas lineales exactas y la matriz que las produce.

Una forma es una constante más un coeficiente `Fraction` por variable.
Solo se admiten suma, resta, negación y producto por un escalar numérico.
`Ax = b` con A desconocida se resuelve comparando coeficientes, no con Gauss.
Hallar x cuando A y b son numéricos sigue en `backend.ecuaciones_matriciales`.

ponytail: una sola matriz desconocida por un vector simbólico. AX = B,
varias incógnitas y productos de variables quedan fuera de este módulo.
"""

import re
from dataclasses import dataclass
from fractions import Fraction

from backend.expresiones_matriciales.lexer import tokenizar
from backend.expresiones_matriciales.nodos import Negacion, Numero, Producto, Resta, Simbolo, Suma
from backend.expresiones_matriciales.parser import analizar

NO_LINEAL = "La expresión deja de ser lineal porque multiplica dos cantidades simbólicas."
_DIVISION = "La expresión deja de ser lineal porque divide por una cantidad simbólica."
_POTENCIA = "La expresión deja de ser lineal porque eleva una cantidad simbólica a una potencia."
_DIVISION_SIMBOLICA = re.compile(r"/\s*[A-Za-z(]")


@dataclass(frozen=True)
class FormaLineal:
    constante: Fraction
    coeficientes: tuple[tuple[str, Fraction], ...]

    def coeficiente(self, variable):
        for nombre, valor in self.coeficientes:
            if nombre == variable:
                return valor
        return Fraction(0)

    def __eq__(self, otro):
        if not isinstance(otro, FormaLineal):
            return NotImplemented
        return self.constante == otro.constante and dict(self.coeficientes) == dict(otro.coeficientes)


@dataclass(frozen=True)
class VectorLineal:
    componentes: tuple[FormaLineal, ...]
    variables: tuple[str, ...] = ()


@dataclass(frozen=True)
class VectorSimbolico:
    nombre: str
    variables: tuple[str, ...]


@dataclass(frozen=True)
class MatrizDesconocida:
    nombre: str
    filas: int
    columnas: int


@dataclass(frozen=True)
class Aplicacion:
    """Producto todavía no resuelto: una matriz desconocida por un vector simbólico."""

    matriz: MatrizDesconocida
    vector: VectorSimbolico


@dataclass(frozen=True)
class Determinacion:
    matriz: MatrizDesconocida
    vector: VectorSimbolico
    etiqueta: str
    componentes: tuple[FormaLineal, ...]
    columnas: tuple[tuple[Fraction, ...], ...]
    resultado: tuple[tuple[Fraction, ...], ...]
    verificacion: tuple[FormaLineal, ...]
    texto: str = ""

    @property
    def nombres_columnas(self):
        base = self.matriz.nombre.lower()
        return tuple(f"{base}{indice}" for indice in range(1, len(self.vector.variables) + 1))

    @property
    def verificada(self):
        return self.componentes == self.verificacion


def forma(constante=0, coeficientes=None):
    """Descarta coeficientes nulos. El orden de las claves es el de primera aparición."""
    terminos = {}
    for variable, coeficiente in (coeficientes or {}).items():
        valor = Fraction(coeficiente)
        if valor != 0:
            terminos[variable] = valor
    return FormaLineal(Fraction(constante), tuple(terminos.items()))


def sumar(izquierda, derecha):
    coeficientes = dict(izquierda.coeficientes)
    for variable, valor in derecha.coeficientes:
        coeficientes[variable] = coeficientes.get(variable, Fraction(0)) + valor
    return forma(izquierda.constante + derecha.constante, coeficientes)


def escalar(factor, expresion):
    factor = Fraction(factor)
    return forma(
        expresion.constante * factor,
        {variable: valor * factor for variable, valor in expresion.coeficientes},
    )


def negar(expresion):
    return escalar(-1, expresion)


def restar(minuendo, sustraendo):
    return sumar(minuendo, negar(sustraendo))


def enumerar(nombres):
    nombres = tuple(nombres)
    if len(nombres) <= 1:
        return nombres[0] if nombres else ""
    if len(nombres) == 2:
        return f"{nombres[0]} y {nombres[1]}"
    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def texto_forma(expresion, orden=()):
    """Escribe la forma en el orden declarado y omite coeficientes nulos."""
    terminos = []
    vistos = set()
    for nombre in orden:
        vistos.add(nombre)
        coeficiente = expresion.coeficiente(nombre)
        if coeficiente != 0:
            terminos.append((nombre, coeficiente))
    for nombre, coeficiente in expresion.coeficientes:
        if nombre not in vistos:
            terminos.append((nombre, coeficiente))
    if not terminos:
        return str(Fraction(expresion.constante))
    texto = "".join(
        _termino(coeficiente, nombre, indice == 0)
        for indice, (nombre, coeficiente) in enumerate(terminos)
    )
    if expresion.constante != 0:
        constante = Fraction(expresion.constante)
        texto += f" - {abs(constante)}" if constante < 0 else f" + {constante}"
    return texto


def _termino(coeficiente, nombre, primero):
    negativo = coeficiente < 0
    magnitud = -coeficiente if negativo else coeficiente
    cuerpo = nombre if magnitud == 1 else f"{magnitud}{nombre}"
    if primero:
        return f"-{cuerpo}" if negativo else cuerpo
    return f" - {cuerpo}" if negativo else f" + {cuerpo}"


def analizar_lineal(texto):
    """Normaliza una componente. Reutiliza el lexer y el parser; el resultado es una forma."""
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("Escribe una expresión lineal.")
    if "^" in texto:
        raise ValueError(_POTENCIA)
    if _DIVISION_SIMBOLICA.search(texto):
        raise ValueError(_DIVISION)
    try:
        tokens = tokenizar(texto)
    except ValueError as error:
        raise ValueError(str(error)) from None
    nombres = {token.valor for token in tokens if token.tipo == "nombre"}
    return _normalizar(analizar(texto, nombres))


def _normalizar(nodo):
    if isinstance(nodo, Numero):
        return forma(nodo.valor)
    if isinstance(nodo, Simbolo):
        return forma(0, {nodo.nombre: 1})
    if isinstance(nodo, Negacion):
        return negar(_normalizar(nodo.operando))
    if isinstance(nodo, Suma):
        return sumar(_normalizar(nodo.izquierda), _normalizar(nodo.derecha))
    if isinstance(nodo, Resta):
        return restar(_normalizar(nodo.izquierda), _normalizar(nodo.derecha))
    if isinstance(nodo, Producto):
        izquierda = _normalizar(nodo.izquierda)
        derecha = _normalizar(nodo.derecha)
        if not izquierda.coeficientes:
            return escalar(izquierda.constante, derecha)
        if not derecha.coeficientes:
            return escalar(derecha.constante, izquierda)
        raise ValueError(NO_LINEAL)
    raise TypeError(type(nodo).__name__)


def coef_vector(vector, variable):
    """Coeficiente de `variable` en cada componente. La ausente vale 0."""
    componentes = vector.componentes if isinstance(vector, VectorLineal) else vector
    return tuple(componente.coeficiente(variable) for componente in componentes)


def variables_simbolicas(nombre, cantidad):
    return tuple(f"{nombre}{indice}" for indice in range(1, cantidad + 1))


def exigir_columnas(matriz, vector):
    if matriz.columnas != len(vector.variables):
        raise ValueError(
            f"{matriz.nombre} es {matriz.filas}×{matriz.columnas} y necesita un vector de "
            f"{matriz.columnas} componentes, pero {vector.nombre} tiene {len(vector.variables)}."
        )


def determinar(matriz, vector, lado, etiqueta="el otro lado", ubicacion="derecho"):
    """Columnas de A: el coeficiente de cada variable de x, en ese orden."""
    if not isinstance(lado, VectorLineal):
        lado = VectorLineal(tuple(lado))
    exigir_columnas(matriz, vector)
    if matriz.filas != len(lado.componentes):
        raise ValueError(
            f"{matriz.nombre}{vector.nombre} tiene {matriz.filas} componentes pero {etiqueta} tiene {len(lado.componentes)}."
        )
    permitidas = set(vector.variables)
    ajenas = []
    for componente in lado.componentes:
        for nombre, _coeficiente in componente.coeficientes:
            if nombre not in permitidas and nombre not in ajenas:
                ajenas.append(nombre)
    if ajenas:
        raise ValueError(
            f"El lado {ubicacion} contiene {enumerar(ajenas)}, pero {vector.nombre} está formado únicamente por {enumerar(vector.variables)}."
        )
    for indice, componente in enumerate(lado.componentes, 1):
        if componente.constante != 0:
            raise ValueError(
                f"La componente {indice} es {texto_forma(componente, vector.variables)}. "
                f"{matriz.nombre}{vector.nombre} siempre es una combinación lineal de las componentes de {vector.nombre} "
                "y no genera un término constante independiente."
            )
    columnas = tuple(coef_vector(lado, variable) for variable in vector.variables)
    resultado = tuple(
        tuple(columna[fila] for columna in columnas)
        for fila in range(matriz.filas)
    )
    verificacion = _aplicar(resultado, vector.variables)
    return Determinacion(matriz, vector, etiqueta, lado.componentes, columnas, resultado, verificacion)


def _aplicar(filas, variables):
    return tuple(
        forma(0, {variable: coeficiente for variable, coeficiente in zip(variables, fila)})
        for fila in filas
    )


def matriz_por_simbolico(filas, vector):
    """Producto de una matriz numérica por un vector simbólico, componente a componente."""
    return VectorLineal(_aplicar(filas, vector.variables), vector.variables)
