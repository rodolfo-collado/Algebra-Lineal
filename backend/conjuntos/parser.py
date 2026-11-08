"""Expresiones de valores y una relación opcional; sin ejecución de código."""

from dataclasses import dataclass

from .literales import Lector, validar_nombre
from backend.operandos import OPERANDOS_MAXIMOS

OPERADORES = (("∈", "Pertenece"), ("∉", "No pertenece"), ("⊆", "Está incluido"),
              ("⊂", "Está incluido propiamente"), ("=", "Es igual"), ("≠", "Es distinto"))


@dataclass(frozen=True)
class Referencia:
    nombre: str


@dataclass(frozen=True)
class Relacion:
    izquierda: object
    operador: str
    derecha: object


@dataclass(frozen=True)
class Operacion:
    operador: str
    operandos: tuple[object, ...]


_SIN_OPERANDO = ("∪", "∩", "∖", "×", ",", ")", "}")


def _operando(lector, profundidad=0):
    if lector.actual().texto in ("potencia", "par"):
        lector.presupuesto.elemento(profundidad)
        operador = lector.tomar().texto
        lector.exigir("(")
        operandos = [_expresion(lector, profundidad + 1)]
        if operador == "par":
            lector.exigir(",")
            operandos.append(_expresion(lector, profundidad + 1))
        lector.exigir(")")
        return Operacion(operador, tuple(operandos))
    if lector.actual().texto == "(":
        lector.presupuesto.elemento(profundidad)
        lector.tomar()
        valor = _expresion(lector, profundidad + 1)
        lector.exigir(")")
        return valor
    if lector.actual().texto in ("∁", "|"):
        lector.presupuesto.elemento(profundidad)
        operador = lector.tomar().texto
        if operador == "|":
            valor = _expresion(lector, profundidad + 1)
            lector.exigir("|")
            return Operacion(operador, (valor,))
        lector.exigir("(")
        valor = _expresion(lector, profundidad + 1)
        lector.exigir(",")
        universo = _expresion(lector, profundidad + 1)
        lector.exigir(")")
        return Operacion(operador, (valor, universo))
    if lector.actual().tipo == "nombre" and lector.actual().texto != 'intervalo':
        lector.presupuesto.elemento(profundidad)
        return Referencia(validar_nombre(lector.tomar().texto))
    # Sin operando (final, operador o cierre), el mensaje de literales confundiría: aquí sí hay nombres.
    if lector.actual().tipo == "fin":
        raise ValueError("Falta un conjunto al final de la expresión; complétala, por ejemplo A ∪ B.")
    if lector.actual().texto in (*_SIN_OPERANDO, *(simbolo for simbolo, _ in OPERADORES)):
        raise ValueError(f"Falta un conjunto antes de «{lector.actual().texto}».")
    return lector.literal(profundidad)


def _expresion(lector, profundidad=0, minimo=0):
    precedencia = {"∪": 1, "∖": 1, "∩": 2, "×": 3}
    izquierda = _operando(lector, profundidad)
    while lector.actual().texto in precedencia and precedencia[lector.actual().texto] >= minimo:
        lector.presupuesto.elemento(profundidad)
        operador = lector.tomar().texto
        derecha = _expresion(lector, profundidad + 1, precedencia[operador] + 1)
        izquierda = Operacion(operador, (izquierda, derecha))
    return izquierda


def analizar_expresion(texto, *, presupuesto=None):
    lector = Lector(texto, presupuesto)
    izquierda = _expresion(lector)
    if lector.actual().tipo == "fin":
        arbol = izquierda
    else:
        arbol = _relacion(lector, izquierda)
    lector.fin()
    # También limita la altura que producen las cadenas asociadas a la izquierda.
    pendientes = [(arbol, 0)]
    while pendientes:
        nodo, profundidad = pendientes.pop()
        if profundidad >= OPERANDOS_MAXIMOS:
            raise ValueError(f"La expresión admite hasta {OPERANDOS_MAXIMOS} niveles de operaciones.")
        hijos = nodo.operandos if isinstance(nodo, Operacion) else (
            (nodo.izquierda, nodo.derecha) if isinstance(nodo, Relacion) else ())
        pendientes.extend((hijo, profundidad + 1) for hijo in hijos)
    return arbol


def _relacion(lector, izquierda):
    operador = lector.tomar().texto
    if operador not in dict(OPERADORES):
        raise ValueError("Escribe una relación con ∈, ∉, ⊆, ⊂, = o ≠ entre dos operandos.")
    derecha = _expresion(lector)
    return Relacion(izquierda, operador, derecha)


def analizar_relacion(texto, *, presupuesto=None):
    arbol = analizar_expresion(texto, presupuesto=presupuesto)
    if not isinstance(arbol, Relacion):
        raise ValueError("Escribe una relación con ∈, ∉, ⊆, ⊂, = o ≠ entre dos operandos.")
    return arbol


def renombrar_referencias(texto, cambios):
    """Renombrado simultáneo por tokens; no toca texto entre comillas ni partes de nombres."""
    lector = Lector(texto)
    reemplazos = []
    literal_intervalo = False
    profundidad = 0
    for token in lector.tokens:
        if token.texto == 'intervalo':
            literal_intervalo = True
        if literal_intervalo:
            if token.texto == '(':
                profundidad += 1
            elif token.texto == ')':
                profundidad -= 1
                if profundidad == 0:
                    literal_intervalo = False
            continue
        if token.tipo == 'nombre' and token.texto in cambios:
            reemplazos.append((token,cambios[token.texto]))
    # Comprobar el tamaño final antes de expandir nombres repetidos.
    lector.presupuesto.longitud(sum(len(nombre) - len(token.texto) for token, nombre in reemplazos))
    partes = []
    posicion = 0
    for token, nombre in reemplazos:
        partes.extend((texto[posicion:token.inicio], nombre))
        posicion = token.fin
    partes.append(texto[posicion:])
    return "".join(partes)
