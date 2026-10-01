"""Expresiones lineales exactas: una constante mas coeficientes por variable.

Las variables se numeran como x1, x2, ... igual que en el resto del proyecto,
incluidos los coeficientes buscados en una combinacion lineal. Al formatear se
puede elegir otra letra; la aritmetica no cambia. Esta se hace siempre sobre
`Fraction`; el texto se genera solo al final, nunca durante el calculo.

Tambien es la representacion comun de los parsers de ecuaciones lineales:
cada parser lee su propia sintaxis y entrega terminos; `expresion_desde_terminos`
los representa y `normalizar_igualdad` pasa una igualdad a la forma estandar.
"""

from fractions import Fraction

from backend.matrices import formatear_fraccion
from backend.seguridad_numerica import multiplicar_exacto, restar_exacto, sumar_exacto

NOMBRE_VARIABLE = "x"


def crear_expresion(constante=0, coeficientes=None):
    """Construye una expresion lineal descartando los coeficientes en cero."""
    terminos = {}
    for variable, coeficiente in (coeficientes or {}).items():
        valor = Fraction(coeficiente)
        if valor != 0:
            terminos[variable] = valor

    return {"constante": Fraction(constante), "coeficientes": terminos}


def expresion_de_variable(variable):
    """La variable escrita como ella misma: es cuanto se sabe de una libre."""
    return crear_expresion(0, {variable: 1})


def multiplicar_expresion(expresion, factor):
    factor = Fraction(factor)
    coeficientes = {
        variable: multiplicar_exacto(coeficiente, factor)
        for variable, coeficiente in expresion["coeficientes"].items()
    }

    return crear_expresion(multiplicar_exacto(expresion["constante"], factor), coeficientes)


def restar_expresiones(minuendo, sustraendo):
    coeficientes = dict(minuendo["coeficientes"])
    for variable, coeficiente in sustraendo["coeficientes"].items():
        coeficientes[variable] = (
            restar_exacto(coeficientes.get(variable, Fraction(0)), coeficiente)
        )

    return crear_expresion(
        restar_exacto(minuendo["constante"], sustraendo["constante"]), coeficientes
    )


def expresion_desde_terminos(terminos):
    """Suma terminos (variable, coeficiente) agrupando los semejantes.

    La variable None marca un termino constante: 2x1 + 3 - x1 son los
    terminos (1, 2), (None, 3) y (1, -1), y la expresion x1 + 3.
    """
    constante = Fraction(0)
    coeficientes = {}
    for variable, coeficiente in terminos:
        if variable is None:
            constante = sumar_exacto(constante, coeficiente)
        else:
            coeficientes[variable] = sumar_exacto(coeficientes.get(variable, Fraction(0)), coeficiente)

    return crear_expresion(constante, coeficientes)


def normalizar_igualdad(izquierda, derecha):
    """Escribe izquierda = derecha como a1x1 + ... + anxn = b.

    Devuelve (expresion sin constante, b). Un termino que cruza el signo
    igual cambia de signo, asi que basta restar los dos lados. Si solo el
    derecho tiene variables, antes se leen al reves (a = b equivale a b = a)
    para no cambiar signos sin necesidad: 6 = x1 + x2 da x1 + x2 = 6.
    """
    if derecha["coeficientes"] and not izquierda["coeficientes"]:
        izquierda, derecha = derecha, izquierda

    diferencia = restar_expresiones(izquierda, derecha)
    return crear_expresion(0, diferencia["coeficientes"]), -diferencia["constante"]


def formatear_termino(coeficiente, variable, nombre=NOMBRE_VARIABLE):
    """Escribe un termino como x1, -x1, 2x1 o 1/2x1."""
    # Los coeficientes 1 y -1 no se escriben delante de la variable.
    if coeficiente == 1:
        return f"{nombre}{variable}"

    if coeficiente == -1:
        return f"-{nombre}{variable}"

    return f"{formatear_fraccion(Fraction(coeficiente))}{nombre}{variable}"


def formatear_expresion(expresion, nombre=NOMBRE_VARIABLE):
    """Escribe la constante y despues las variables en orden ascendente."""
    constante = expresion["constante"]
    coeficientes = expresion["coeficientes"]
    if not coeficientes:
        return formatear_fraccion(constante)

    # La constante cero se omite mientras quede algún término con variable.
    texto = "" if constante == 0 else formatear_fraccion(constante)

    for variable in sorted(coeficientes):
        coeficiente = coeficientes[variable]
        if not texto:
            texto = formatear_termino(coeficiente, variable, nombre)
            continue

        # A partir del segundo término el signo se separa del coeficiente.
        signo = "-" if coeficiente < 0 else "+"
        texto += f" {signo} {formatear_termino(abs(coeficiente), variable, nombre)}"

    return texto


def formatear_ecuacion(expresion, termino_independiente, nombre=NOMBRE_VARIABLE):
    """Escribe 'expresion = termino', incluidos los casos como 0 = 3."""
    izquierda = formatear_expresion(expresion, nombre)
    derecha = formatear_fraccion(Fraction(termino_independiente))

    return f"{izquierda} = {derecha}"
