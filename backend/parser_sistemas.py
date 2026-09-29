"""Conversion de sistemas escritos como texto en matrices aumentadas.

Este modulo es logica pura: recibe texto y devuelve una matriz, o lanza
ValueError. No imprime, no pide datos y no conoce ninguna interfaz.

Cada ecuacion pasa por tres etapas: se parsea cada miembro en terminos (lo
unico propio de esta sintaxis), se representa como expresion lineal y se
normaliza la igualdad (backend.expresiones). Por eso x1 + x2 = 6, x1 - 6 = -x2,
6 = x1 + x2 y x2 = 6 - x1 producen la misma fila [1, 1 | 6].
"""

import re
from fractions import Fraction

from backend.expresiones import (
    crear_expresion,
    expresion_desde_terminos,
    formatear_ecuacion,
    normalizar_igualdad,
)
from backend.presupuesto_sistemas import (
    validar_dimensiones,
    validar_literal_numerico,
    validar_longitud_sistema,
    validar_valor_agrupado,
)

SEPARADOR_ECUACIONES = ";"

_PREFIJO_ERROR = "Formato de sistema inválido"

# Un literal es un entero, una fraccion o un decimal. Un termino es un signo y
# un literal, o un signo, un coeficiente opcional y una variable xN con N desde 1.
_LITERAL = r"\d+(?:/\d+)?|\d*\.\d+"
_TERMINO = re.compile(rf"([+-])({_LITERAL})?x([1-9]\d*)")
_CONSTANTE = re.compile(rf"[+-](?:{_LITERAL})")
_TERMINOS_CON_SIGNO = re.compile(r"[+-][^+-]+")
_ESPACIOS = re.compile(r"\s+")
_SALTO_DE_LINEA = re.compile(r"\r?\n")
_VARIABLE = re.compile(r"x\d+")
_FUNCION = re.compile(r"[A-Za-z]{2,}(?=\()")


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
        raise ValueError("cada + o - debe ir seguido de un número o de una variable xN")

    return terminos


def _validar_termino(termino):
    """Presupuesto web: ningun literal del termino llega a Fraction o int si es caro."""
    validar_literal_numerico(termino)
    coeficiente, variable, indice = termino[1:].partition("x")
    if variable:
        validar_literal_numerico(coeficiente)
        validar_literal_numerico(indice)


def _explicar_termino(termino):
    """Por que un termino no es un numero, xN ni un coeficiente seguido de xN."""
    cuerpo = termino[1:]
    funcion = _FUNCION.search(cuerpo)
    if funcion:
        return (
            f"{funcion.group()}(…) no forma parte de una ecuación lineal, "
            "que solo admite números y variables xN"
        )
    base, potencia, _ = cuerpo.partition("^")
    if potencia:
        if _VARIABLE.search(base):
            return "la ecuación deja de ser lineal porque eleva una variable a una potencia"
        return "las potencias no forman parte de esta sintaxis"
    if len(_VARIABLE.findall(cuerpo)) > 1:
        return "la ecuación deja de ser lineal porque multiplica dos variables"
    if re.search(r"/\(?x", cuerpo):
        return "la ecuación deja de ser lineal porque divide por una variable"
    if re.search(r"x\d+/", cuerpo):
        return "escribe la fracción antes de la variable, como 1/2x1"
    if "*" in cuerpo:
        return "escribe el coeficiente junto a la variable, sin *, como 2x1"
    if "(" in cuerpo or ")" in cuerpo:
        return "escribe cada término sin paréntesis, como 2x1 + 2x2"
    if "x" in cuerpo:
        return "solo se admiten variables x1, x2, ... con coeficientes numéricos"
    return f"«{cuerpo}» no es un número ni una variable xN"


def _leer_termino(termino):
    """(indice, coeficiente) de un termino con signo; el indice es None en un numero."""
    variable = _TERMINO.fullmatch(termino)
    if variable is None:
        if not _CONSTANTE.fullmatch(termino):
            raise ValueError(_explicar_termino(termino))
        try:
            return None, Fraction(termino)
        except ZeroDivisionError:
            raise ValueError("un número no puede tener denominador cero") from None

    signo, texto_coeficiente, texto_indice = variable.groups()
    coeficiente = Fraction(1)
    if texto_coeficiente is not None:
        try:
            coeficiente = Fraction(texto_coeficiente)
        except ZeroDivisionError:
            raise ValueError("un coeficiente no puede tener denominador cero") from None

    if signo == "-":
        coeficiente = -coeficiente

    return int(texto_indice), coeficiente


def _leer_miembro(miembro, *, limitar_entrada=False):
    """Terminos (indice, coeficiente) de un lado de la ecuacion, en el orden escrito.

    Con limitar_entrada, cada literal pasa por el presupuesto antes de convertirse.
    """
    compacto = _ESPACIOS.sub("", miembro)
    if "x" not in compacto:
        # Un lado que es un solo número conserva el contrato de siempre del
        # término independiente: 5., 1_000 y, en consola, 1e2.
        if limitar_entrada:
            validar_literal_numerico(compacto)
        try:
            return [(None, Fraction(compacto))]
        except (ValueError, ZeroDivisionError):
            pass

    terminos = _separar_terminos(compacto)
    if limitar_entrada:
        for termino in terminos:
            _validar_termino(termino)

    return [_leer_termino(termino) for termino in terminos]


def _leer_ecuacion(ecuacion, *, limitar_entrada=False):
    """(coeficientes, termino independiente, ya estaba en forma estandar).

    Parsear cada lado, representarlo y normalizar la igualdad. Una variable
    escrita que se cancela conserva su columna con coeficiente 0.
    """
    lados = ecuacion.split("=")
    if len(lados) != 2:
        raise ValueError("cada ecuación debe contener un único signo '='")

    if not lados[0].strip() or not lados[1].strip():
        raise ValueError("cada ecuación necesita términos a ambos lados del '='")

    izquierda = _leer_miembro(lados[0], limitar_entrada=limitar_entrada)
    derecha = _leer_miembro(lados[1], limitar_entrada=limitar_entrada)
    escritas = sorted({indice for indice, _ in izquierda + derecha if indice is not None})
    if not escritas:
        raise ValueError("cada ecuación necesita al menos una variable xN")

    expresion, termino_independiente = normalizar_igualdad(
        expresion_desde_terminos(izquierda), expresion_desde_terminos(derecha)
    )
    coeficientes = {
        indice: expresion["coeficientes"].get(indice, Fraction(0)) for indice in escritas
    }
    if limitar_entrada:
        for valor in (*coeficientes.values(), termino_independiente):
            validar_valor_agrupado(valor)
    # Solo variables a la izquierda y un número a la derecha: nada que reescribir.
    estandar = (
        all(indice is not None for indice, _ in izquierda)
        and len(derecha) == 1
        and derecha[0][0] is None
    )

    return coeficientes, termino_independiente, estandar


def parsear_ecuacion(ecuacion, *, limitar_entrada=False):
    """Devuelve ({indice: coeficiente}, termino independiente) de una ecuacion.

    Los terminos pueden estar en ambos lados: x1 - 6 = -x2 da ({1: 1, 2: 1}, 6).
    """
    coeficientes, termino_independiente, _ = _leer_ecuacion(
        ecuacion, limitar_entrada=limitar_entrada
    )
    return coeficientes, termino_independiente


def _separar_lineas(tramo):
    """Las ecuaciones de un tramo entre ';': una por línea, sin las líneas vacías.

    Un salto de línea separa solo si la ecuación en curso ya tiene su '=' y la
    línea siguiente trae el suyo. Si no, la ecuación sigue en esa línea, como
    hasta ahora: 'x1 + x2' y '= 6' en dos líneas siguen siendo una ecuación.
    """
    ecuaciones = []
    lineas, con_igual = [], False
    for linea in _SALTO_DE_LINEA.split(tramo):
        if not linea.strip():
            continue
        if con_igual and "=" in linea:
            ecuaciones.append("\n".join(lineas))
            lineas, con_igual = [], False
        lineas.append(linea)
        con_igual = con_igual or "=" in linea
    ecuaciones.append("\n".join(lineas))
    return [ecuacion.strip() for ecuacion in ecuaciones]


def _leer_sistema(texto, limitar_entrada):
    """Las ecuaciones escritas, su lectura y la matriz aumentada que producen.

    Las ecuaciones se separan con ';' o con saltos de línea (\\n o \\r\\n) y la
    cantidad de variables la marca el mayor indice que aparece en todo el sistema.
    La entrada web activa el presupuesto antes de dividir texto, reservar filas
    o convertir literales. Los consumidores de consola conservan su contrato.
    """
    if limitar_entrada and isinstance(texto, str):
        validar_longitud_sistema(texto)
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError(f"{_PREFIJO_ERROR}: el sistema no puede estar vacío.")

    if limitar_entrada:
        validar_dimensiones(texto.count(SEPARADOR_ECUACIONES) + 1, 1)

    # Separación de las ecuaciones: ';' y, dentro de cada tramo, los saltos de línea.
    tramos = [parte.strip() for parte in texto.split(SEPARADOR_ECUACIONES)]
    if any(not tramo for tramo in tramos):
        raise ValueError(
            f"{_PREFIJO_ERROR}: las ecuaciones se separan con un único ';' y "
            "ninguna puede quedar vacía."
        )
    ecuaciones = [ecuacion for tramo in tramos for ecuacion in _separar_lineas(tramo)]
    if limitar_entrada:
        # También cuentan las ecuaciones que solo separa un salto de línea.
        validar_dimensiones(len(ecuaciones), 1)

    try:
        analizadas = [
            _leer_ecuacion(ecuacion, limitar_entrada=limitar_entrada)
            for ecuacion in ecuaciones
        ]
    except ValueError as error:
        raise ValueError(f"{_PREFIJO_ERROR}: {str(error).rstrip('.')}.") from None

    # Conversión a matriz aumentada: las variables ausentes valen cero.
    cantidad_variables = max(max(coeficientes) for coeficientes, _, _ in analizadas)
    if limitar_entrada:
        validar_dimensiones(len(analizadas), cantidad_variables)
    matriz = []
    for coeficientes, termino_independiente, _ in analizadas:
        fila = [0] * cantidad_variables
        for indice, coeficiente in coeficientes.items():
            fila[indice - 1] = _simplificar(coeficiente)
        fila.append(_simplificar(termino_independiente))
        matriz.append(fila)

    return ecuaciones, analizadas, matriz


def analizar_sistema(texto, *, limitar_entrada=False):
    """Devuelve (matriz aumentada, ecuaciones reescritas) de un sistema escrito.

    Cada reescrita es un dict con su numero, el texto original y su forma
    estandar, para que una interfaz explique el paso. Las ecuaciones que ya
    tenian solo variables a la izquierda y un numero a la derecha no aparecen.
    """
    ecuaciones, analizadas, matriz = _leer_sistema(texto, limitar_entrada)
    reescritas = [
        {
            "numero": numero,
            "original": " ".join(ecuacion.split()),
            "estandar": formatear_ecuacion(crear_expresion(0, coeficientes), termino_independiente),
        }
        for numero, (ecuacion, (coeficientes, termino_independiente, estandar)) in enumerate(
            zip(ecuaciones, analizadas), start=1
        )
        if not estandar
    ]
    return matriz, reescritas


def parsear_sistema(texto, *, limitar_entrada=False):
    """Convierte un sistema escrito como texto en su matriz aumentada.

    Solo la matriz: el backend matematico no necesita saber como se escribio
    cada ecuacion (analizar_sistema da tambien las reescritas).
    """
    _, _, matriz = _leer_sistema(texto, limitar_entrada)
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
