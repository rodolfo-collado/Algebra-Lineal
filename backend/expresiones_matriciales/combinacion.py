"""x1 u + x2 v = b: los coeficientes de una combinación lineal escritos como una igualdad.

No es un motor nuevo. El parser de expresiones lee la igualdad (con x1, x2, … como
nombres además de los operandos) y `backend.vectores` plantea [u v … | b] y lo resuelve
con el Gauss-Jordan del proyecto, como hacía la antigua Operaciones con vectores.
Una expresión sin incógnitas x1, x2, … no pasa por aquí: se evalúa como siempre.
"""

import re

from backend.expresiones_matriciales.lexer import tokenizar
from backend.expresiones_matriciales.nodos import Igualdad, Producto, Simbolo, Suma
from backend.expresiones_matriciales.parser import analizar_entrada, segmentar
from backend.vectores import validar_misma_dimension

_INCOGNITA = re.compile(r"(x[1-9]\d*)(.*)\Z")
FORMA = ("Para hallar coeficientes escribe una igualdad como x1 u + x2 v = b: cada incógnita x1, x2, … "
         "multiplica a un vector definido, los términos se suman y el otro lado es un vector definido.")


def incognitas(texto, definidos):
    """Incógnitas x1, x2, … que aparecen en la expresión sin ser operandos, en orden de aparición."""
    try:
        tokens = tokenizar(texto)
    except ValueError:
        return []
    encontradas = []
    for token in tokens:
        if token.tipo != "nombre" or token.valor in definidos:
            continue
        coincidencia = _INCOGNITA.match(token.valor)
        # «x1u» también vale: x1 seguido de operandos definidos, como cualquier producto implícito.
        if coincidencia and (not coincidencia[2] or segmentar(coincidencia[2], definidos)):
            if coincidencia[1] not in encontradas:
                encontradas.append(coincidencia[1])
    return encontradas


def _terminos(nodo, incognitas_validas, definidos):
    """[(incógnita, vector), …] si el nodo es x1 u + x2 v + …; None si tiene otra forma."""
    if isinstance(nodo, Suma):
        izquierda = _terminos(nodo.izquierda, incognitas_validas, definidos)
        derecha = _terminos(nodo.derecha, incognitas_validas, definidos)
        return None if izquierda is None or derecha is None else izquierda + derecha
    if (isinstance(nodo, Producto) and isinstance(nodo.izquierda, Simbolo) and isinstance(nodo.derecha, Simbolo)
            and nodo.izquierda.nombre in incognitas_validas and nodo.derecha.nombre in definidos):
        return [(nodo.izquierda.nombre, nodo.derecha.nombre)]
    return None


def plantear(texto, simbolos):
    """Generadores y objetivo de x1 u + … + xk w = b, o None si la expresión no usa incógnitas.

    `simbolos` es el mismo diccionario que recibe `evaluar`. Lanza ValueError con un mensaje
    concreto si hay incógnitas pero la igualdad no tiene la forma de una combinación lineal.
    """
    definidos = set(simbolos)
    halladas = incognitas(texto, definidos)
    if not halladas:
        return None
    arbol = analizar_entrada(texto, definidos | set(halladas))
    if not isinstance(arbol, Igualdad):
        raise ValueError(f"{', '.join(halladas)} no {'es un operando definido' if len(halladas) == 1 else 'son operandos definidos'}. {FORMA}")
    for lado, otro in ((arbol.izquierda, arbol.derecha), (arbol.derecha, arbol.izquierda)):
        terminos = _terminos(lado, set(halladas), definidos)
        if terminos is not None and isinstance(otro, Simbolo) and otro.nombre in definidos:
            break
    else:
        raise ValueError(FORMA)
    nombres = [incognita for incognita, _ in terminos]
    esperadas = [f"x{indice}" for indice in range(1, len(terminos) + 1)]
    if nombres != esperadas:
        raise ValueError(f"Numera los coeficientes en orden, uno por término: {' + '.join(f'{x} {v}' for x, (_, v) in zip(esperadas, terminos))} = {otro.nombre}.")
    for nombre in (*(vector for _, vector in terminos), otro.nombre):
        tipo = simbolos[nombre]["tipo"]
        if tipo != "vector":
            nombre_tipo = {"matriz": "una matriz", "escalar": "un escalar"}.get(tipo, "un operando simbólico")
            raise ValueError(f"En una combinación lineal {nombre} debe ser un vector con valores; es {nombre_tipo}.")
    generadores = [(vector, simbolos[vector]["valor"]) for _, vector in terminos]
    objetivo = (otro.nombre, simbolos[otro.nombre]["valor"])
    valida, mensaje = validar_misma_dimension(
        [valor for _, valor in (*generadores, objetivo)], [nombre for nombre, _ in (*generadores, objetivo)], "combinar")
    if not valida:
        raise ValueError(mensaje)
    return {"incognitas": nombres, "generadores": generadores, "objetivo": objetivo, "texto": arbol.texto}
