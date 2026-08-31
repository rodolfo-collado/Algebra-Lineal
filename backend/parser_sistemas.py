"""Conversion de sistemas escritos como texto en matrices aumentadas.

Este modulo es logica pura: recibe texto y devuelve una matriz, o lanza
ValueError. No imprime, no pide datos y no conoce ninguna interfaz.
"""

import re
from fractions import Fraction

SEPARADOR_ECUACIONES = ";"

_PREFIJO_ERROR = "Formato de sistema inválido"

# Un termino es un signo, un coeficiente opcional (entero, fraccion o decimal)
# y una variable xN cuyo indice empieza en 1.
_TERMINO = re.compile(r"([+-])(\d+(?:/\d+)?|\d*\.\d+)?x([1-9]\d*)")
_TERMINOS_CON_SIGNO = re.compile(r"[+-][^+-]+")
_ESPACIOS = re.compile(r"\s+")


def _simplificar(numero):
    # Un racional con denominador 1 se guarda como entero, igual que el resto
    # del proyecto.
    if numero.denominator == 1:
        return numero.numerator

    return numero


def convertir_a_numero(texto):
    """Convierte enteros, negativos, fracciones y decimales a un valor exacto."""
    try:
        numero = Fraction(_ESPACIOS.sub("", texto))
    except (ValueError, ZeroDivisionError):
        raise ValueError(f"'{texto.strip()}' no es un número válido.") from None

    return _simplificar(numero)


def _separar_terminos(expresion):
    # Separación de los términos: cada uno arrastra su propio signo.
    if expresion[0] not in "+-":
        expresion = "+" + expresion

    terminos = _TERMINOS_CON_SIGNO.findall(expresion)
    if not terminos or "".join(terminos) != expresion:
        raise ValueError("cada término debe escribirse como xN o coeficiente xN")

    return terminos


def _leer_termino(termino):
    """Devuelve (indice de la variable, coeficiente) de un termino con signo."""
    coincidencia = _TERMINO.fullmatch(termino)
    if coincidencia is None:
        raise ValueError(
            "solo se admiten variables x1, x2, ... con coeficientes numéricos"
        )

    signo, texto_coeficiente, texto_indice = coincidencia.groups()
    try:
        coeficiente = (
            Fraction(1) if texto_coeficiente is None else Fraction(texto_coeficiente)
        )
    except ZeroDivisionError:
        raise ValueError("un coeficiente no puede tener denominador cero") from None

    if signo == "-":
        coeficiente = -coeficiente

    return int(texto_indice), coeficiente


def parsear_ecuacion(ecuacion):
    """Devuelve ({indice: coeficiente}, termino independiente) de una ecuacion."""
    lados = ecuacion.split("=")
    if len(lados) != 2:
        raise ValueError("cada ecuación debe contener un único signo '='")

    izquierda = _ESPACIOS.sub("", lados[0])
    derecha = lados[1].strip()
    if not izquierda or not derecha:
        raise ValueError("cada ecuación necesita términos a ambos lados del '='")

    try:
        termino_independiente = convertir_a_numero(derecha)
    except ValueError:
        raise ValueError("el término independiente debe ser un número") from None

    coeficientes = {}
    for termino in _separar_terminos(izquierda):
        indice, coeficiente = _leer_termino(termino)
        # Una variable repetida suma sus coeficientes.
        coeficientes[indice] = coeficientes.get(indice, Fraction(0)) + coeficiente

    return coeficientes, termino_independiente


def parsear_sistema(texto):
    """Convierte un sistema escrito como texto en su matriz aumentada.

    Las ecuaciones se separan con ';' y la cantidad de variables la marca el
    mayor indice que aparece en todo el sistema.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError(f"{_PREFIJO_ERROR}: el sistema no puede estar vacío.")

    # Separación de las ecuaciones
    ecuaciones = [parte.strip() for parte in texto.split(SEPARADOR_ECUACIONES)]
    if any(not ecuacion for ecuacion in ecuaciones):
        raise ValueError(
            f"{_PREFIJO_ERROR}: las ecuaciones se separan con un único ';' y "
            "ninguna puede quedar vacía."
        )

    try:
        analizadas = [parsear_ecuacion(ecuacion) for ecuacion in ecuaciones]
    except ValueError as error:
        raise ValueError(f"{_PREFIJO_ERROR}: {error}.") from None

    # Conversión a matriz aumentada: las variables ausentes valen cero.
    cantidad_variables = max(max(coeficientes) for coeficientes, _ in analizadas)
    matriz = []
    for coeficientes, termino_independiente in analizadas:
        fila = [0] * cantidad_variables
        for indice, coeficiente in coeficientes.items():
            fila[indice - 1] = _simplificar(coeficiente)
        fila.append(termino_independiente)
        matriz.append(fila)

    return matriz


def construir_matriz_aumentada(coeficientes, terminos_independientes):
    """Une los coeficientes de cada ecuacion con su termino independiente.

    Produce la misma estructura que `parsear_sistema`, para que el ingreso
    manual y el textual sean intercambiables.
    """
    if not coeficientes:
        raise ValueError("Un sistema necesita al menos una ecuación.")

    if len(coeficientes) != len(terminos_independientes):
        raise ValueError("Cada ecuación necesita un término independiente.")

    matriz = []
    for fila, termino_independiente in zip(coeficientes, terminos_independientes):
        if not fila:
            raise ValueError("Cada ecuación necesita al menos una variable.")
        matriz.append(list(fila) + [termino_independiente])

    return matriz
