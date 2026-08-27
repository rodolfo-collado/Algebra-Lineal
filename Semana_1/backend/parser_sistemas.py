import re
from fractions import Fraction


PATRON_TERMINO = re.compile(
    r"([+-])((?:\d+(?:/\d+)?|\d*\.\d+)?)x([1-9]\d*)"
)


def convertir_a_numero(texto):
    """Convierte enteros, decimales y fracciones a valores exactos."""
    numero = Fraction(texto.strip().replace(" ", ""))
    if numero.denominator == 1:
        return numero.numerator

    return numero


def _convertir_fraccion_a_numero(numero):
    if numero.denominator == 1:
        return numero.numerator

    return numero


def _separar_terminos(expresion):
    if expresion[0] not in "+-":
        expresion = "+" + expresion

    terminos = re.findall(r"[+-][^+-]+", expresion)
    if not terminos or "".join(terminos) != expresion:
        raise ValueError(
            "cada término debe tener la forma xN o coeficiente xN"
        )

    return terminos


def parsear_ecuacion(ecuacion):
    partes = ecuacion.strip().split("=")
    if len(partes) != 2:
        raise ValueError("cada ecuación debe tener un único signo '='")

    lado_izquierdo = partes[0].strip()
    lado_derecho = partes[1].strip()
    if not lado_izquierdo or not lado_derecho:
        raise ValueError("la ecuación debe tener dos lados no vacíos")

    try:
        termino_independiente = convertir_a_numero(lado_derecho)
    except (ValueError, ZeroDivisionError):
        raise ValueError("el término independiente debe ser numérico") from None

    expresion = re.sub(r"\s+", "", lado_izquierdo)
    coeficientes = {}
    for termino in _separar_terminos(expresion):
        coincidencia = PATRON_TERMINO.fullmatch(termino)
        if coincidencia is None:
            raise ValueError(
                "solo se permiten variables x1, x2, ... con coeficientes numéricos"
            )

        signo, texto_coeficiente, texto_indice = coincidencia.groups()
        indice = int(texto_indice)
        try:
            coeficiente = (
                Fraction(1)
                if texto_coeficiente == ""
                else Fraction(texto_coeficiente)
            )
        except (ValueError, ZeroDivisionError):
            raise ValueError("el coeficiente debe ser numérico") from None

        if signo == "-":
            coeficiente *= -1

        coeficientes[indice] = coeficientes.get(indice, Fraction(0)) + coeficiente

    if not coeficientes:
        raise ValueError("la ecuación debe contener al menos una variable")

    return coeficientes, Fraction(termino_independiente)


def parsear_sistema(texto):
    """Convierte texto de ecuaciones en una matriz aumentada."""
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("el sistema no puede estar vacío")

    ecuaciones = [ecuacion.strip() for ecuacion in texto.split(";")]
    if any(not ecuacion for ecuacion in ecuaciones):
        raise ValueError("separación de ecuaciones inválida")

    try:
        ecuaciones_parseadas = [
            parsear_ecuacion(ecuacion)
            for ecuacion in ecuaciones
        ]
    except ValueError as error:
        raise ValueError(f"Formato de sistema inválido: {error}") from None

    mayor_indice = max(
        indice
        for coeficientes, _ in ecuaciones_parseadas
        for indice in coeficientes
    )
    matriz = []

    for coeficientes, termino_independiente in ecuaciones_parseadas:
        fila = [Fraction(0) for _ in range(mayor_indice)]
        for indice, coeficiente in coeficientes.items():
            fila[indice - 1] = coeficiente
        fila.append(termino_independiente)
        matriz.append([
            _convertir_fraccion_a_numero(numero)
            for numero in fila
        ])

    return matriz
