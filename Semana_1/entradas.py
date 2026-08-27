import re
from fractions import Fraction


PATRON_TERMINO = re.compile(
    r"([+-])((?:\d+(?:/\d+)?|\d*\.\d+)?)x([1-9]\d*)"
)


def pedir_dimensiones():
    while True:
        try:
            filas = int(input("\nIngrese la cantidad de filas: "))
            if filas <= 0:
                print("Error: Cantidad de filas negativa.")
                continue

            columnas = int(input("Ingrese la cantidad de columnas: "))
            if columnas <= 0:
                print("Error: Cantidad de columnas negativa.")
                continue

        except ValueError:
            print("Error: Ingrese un numero valido.")
            continue

        return filas, columnas


def pedir_indices(matriz):
    while True:
        try:
            fila = int(input("\nIngrese el índice de la fila: "))
            if fila <= 0 or fila > len(matriz):
                print("Error: Fila fuera de rango.")
                continue

            columna = int(input("Ingrese el índice de la columna: "))
            if columna <= 0 or columna > len(matriz[fila - 1]):
                print("Error: Columna fuera de rango.")
                continue

        except ValueError:
            print("Error: Ingrese un número válido.")
            continue
        break

    return fila, columna


def convertir_a_numero(texto):
    """Acepta enteros, decimales y fracciones sin perder exactitud."""
    numero = Fraction(texto.strip())
    if numero.denominator == 1:
        return numero.numerator

    return numero


def _convertir_fraccion_a_numero(numero):
    if numero.denominator == 1:
        return numero.numerator

    return numero


def pedir_elemento_matriz(fila, columna):
    while True:
        try:
            return convertir_a_numero(
                input(f"Ingrese el elemento [{fila},{columna}]: ")
            )
        except (ValueError, ZeroDivisionError):
            print("Error: Ingrese un número válido.\n")


def pedir_nuevo_numero():
    while True:
        try:
            return convertir_a_numero(input("\nIngresa el nuevo número: "))
        except (ValueError, ZeroDivisionError):
            print("Error: Número inválido.")


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
    ecuacion = ecuacion.strip()
    partes = ecuacion.split("=")
    if len(partes) != 2:
        raise ValueError("cada ecuación debe tener un único signo '='")

    lado_izquierdo = partes[0].strip()
    lado_derecho = partes[1].strip()
    if not lado_izquierdo or not lado_derecho:
        raise ValueError("la ecuación debe tener dos lados no vacíos")

    try:
        termino_independiente = Fraction(lado_derecho.replace(" ", ""))
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
        coeficiente = (
            Fraction(1)
            if texto_coeficiente == ""
            else Fraction(texto_coeficiente)
        )
        if signo == "-":
            coeficiente *= -1

        coeficientes[indice] = coeficientes.get(indice, Fraction(0)) + coeficiente

    if not coeficientes:
        raise ValueError("la ecuación debe contener al menos una variable")

    return coeficientes, termino_independiente


def parsear_sistema(texto):
    """Convierte texto de ecuaciones en una matriz aumentada."""
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("el sistema no puede estar vacío")

    ecuaciones = [ecuacion.strip() for ecuacion in texto.split(";")]
    if any(not ecuacion for ecuacion in ecuaciones):
        raise ValueError("separación de ecuaciones inválida")

    ecuaciones_parseadas = []
    try:
        for ecuacion in ecuaciones:
            ecuaciones_parseadas.append(parsear_ecuacion(ecuacion))
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
