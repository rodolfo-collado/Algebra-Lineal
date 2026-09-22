"""Parser recursivo del subconjunto de expresiones que PyGebra evalúa.

Precedencia: paréntesis, menos unario, multiplicación (implícita o `*`),
suma y resta asociativas por la izquierda. La multiplicación implícita
solo parte un identificador en símbolos que de verdad están definidos.
Si hay más de una lectura, se rechaza: no se adivina.
"""

import re
from dataclasses import replace
from fractions import Fraction

from backend.parser_sistemas import convertir_a_numero

from backend.expresiones_matriciales.lexer import tokenizar
from backend.expresiones_matriciales.nodos import Negacion, Numero, Producto, Resta, Simbolo, Suma

_NOMBRE = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")
_INICIA_FACTOR = frozenset({"numero", "nombre", "izq"})


def nombre_valido(nombre):
    return bool(_NOMBRE.fullmatch(nombre or ""))


def segmentar(fragmento, nombres):
    """Lecturas del fragmento como símbolos definidos, como máximo dos.

    Dos bastan para saber si la lectura es única o hay que pedir `*`.
    ponytail: no enumera una tercera lectura; el mensaje igual pide escribir `*`.
    """
    nombres = tuple(nombres)
    n = len(fragmento)
    formas = [[] for _ in range(n + 1)]
    formas[n] = [[]]
    for i in range(n - 1, -1, -1):
        for nombre in nombres:
            if not fragmento.startswith(nombre, i):
                continue
            for cola in formas[i + len(nombre)]:
                formas[i].append([nombre, *cola])
                if len(formas[i]) == 2:
                    break
            if len(formas[i]) == 2:
                break
    return formas[0]


def _lectura(partes):
    if len(partes) == 1:
        return f"el símbolo {partes[0]}"
    return "*".join(partes)


def mensaje_ambiguo(fragmento, formas):
    lecturas = " o ".join(_lectura(forma) for forma in formas)
    return f"«{fragmento}» admite más de una lectura: {lecturas}. Escribe * para indicar la multiplicación."


def mensaje_desconocido(fragmento, nombres):
    """Señala el primer tramo que no es un símbolo definido."""
    nombres = sorted(nombres, key=len, reverse=True)
    i = 0
    while i < len(fragmento):
        coincidencia = next((nombre for nombre in nombres if fragmento.startswith(nombre, i)), None)
        if coincidencia:
            i += len(coincidencia)
            continue
        j = i + 1
        while j < len(fragmento) and not any(fragmento.startswith(nombre, j) for nombre in nombres):
            j += 1
        tramo = fragmento[i:j]
        if nombre_valido(tramo):
            return f"El símbolo {tramo} no está definido."
        return f"No se reconoce «{fragmento}» con los símbolos definidos."
    return f"El símbolo {fragmento} no está definido."


class Parser:
    def __init__(self, texto, nombres):
        self.texto = texto
        self.nombres = {nombre for nombre in nombres if nombre_valido(nombre)}
        self.tokens = tokenizar(texto)
        self.indice = 0
        self.abiertos = 0

    @property
    def actual(self):
        return self.tokens[self.indice]

    def avanzar(self):
        token = self.actual
        self.indice += 1
        return token

    def parsear(self):
        if not self.texto.strip():
            raise ValueError("Escribe una expresión.")
        nodo = self._expresion()
        if self.actual.tipo != "fin":
            if self.actual.tipo == "der":
                raise ValueError("Hay un paréntesis de cierre de más.")
            raise ValueError(f"«{self.actual.valor}» sobra al final de la expresión.")
        return nodo

    def _expresion(self):
        izq = self._termino()
        while self.actual.tipo in ("mas", "menos"):
            op = self.avanzar().tipo
            der = self._termino()
            clase = Suma if op == "mas" else Resta
            izq = clase(self._trozo(izq.inicio, der.fin), izq.inicio, der.fin, izq, der)
        return izq

    def _termino(self):
        izq = self._factor()
        while self.actual.tipo == "por" or self.actual.tipo in _INICIA_FACTOR:
            if self.actual.tipo == "por":
                self.avanzar()
            der = self._factor()
            izq = Producto(self._trozo(izq.inicio, der.fin), izq.inicio, der.fin, izq, der)
        return izq

    def _factor(self):
        if self.actual.tipo == "menos":
            inicio = self.avanzar().inicio
            operando = self._factor()
            return Negacion(self._trozo(inicio, operando.fin), inicio, operando.fin, operando)
        if self.actual.tipo == "por":
            raise ValueError("Falta un operando antes de «*».")
        if self.actual.tipo in ("mas", "menos"):
            raise ValueError(f"Falta un operando antes de «{self.actual.valor}».")
        return self._primario()

    def _primario(self):
        token = self.actual
        if token.tipo == "numero":
            self.avanzar()
            try:
                valor = Fraction(convertir_a_numero(token.valor))
            except ValueError as error:
                raise ValueError(str(error)) from None
            return Numero(token.valor, token.inicio, token.fin, valor)
        if token.tipo == "nombre":
            self.avanzar()
            return self._simbolos(token)
        if token.tipo == "izq":
            inicio = self.avanzar().inicio
            self.abiertos += 1
            if self.actual.tipo == "der":
                raise ValueError("Falta una expresión dentro de los paréntesis.")
            nodo = self._expresion()
            if self.actual.tipo != "der":
                raise ValueError("Falta el paréntesis de cierre.")
            fin = self.avanzar().fin
            self.abiertos -= 1
            return replace(nodo, inicio=inicio, fin=fin)
        if token.tipo == "fin":
            if self.abiertos:
                raise ValueError("Falta el paréntesis de cierre.")
            raise ValueError("La expresión está incompleta.")
        if token.tipo == "der":
            raise ValueError("Hay un paréntesis de cierre sin apertura.")
        raise ValueError(f"«{token.valor}» está donde se esperaba un número, un símbolo o un paréntesis.")

    def _simbolos(self, token):
        formas = segmentar(token.valor, self.nombres)
        if not formas:
            raise ValueError(mensaje_desconocido(token.valor, self.nombres))
        if len(formas) > 1:
            raise ValueError(mensaje_ambiguo(token.valor, formas))
        cursor = token.inicio
        nodo = None
        for nombre in formas[0]:
            fin = cursor + len(nombre)
            pieza = Simbolo(nombre, cursor, fin, nombre)
            nodo = pieza if nodo is None else Producto(self._trozo(nodo.inicio, fin), nodo.inicio, fin, nodo, pieza)
            cursor = fin
        return nodo

    def _trozo(self, inicio, fin):
        return self.texto[inicio:fin].strip()


def analizar(texto, nombres):
    """Convierte texto en AST usando solo los símbolos definidos."""
    return Parser(texto, nombres).parsear()
