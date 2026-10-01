"""Tokens de una expresión matricial. No decide multiplicaciones implícitas.

Los literales numéricos son los del resto del proyecto (enteros, fracciones
`1/2` y decimales exactos). El signo menos es un token propio: el parser
distingue el unario del binario. `/` solo es válido dentro de una fracción.
`=` es una relación entre dos expresiones, no un operador aritmético.
`ᵀ` y `^T` son el mismo token de traspuesta; `^` no forma potencias.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    tipo: str
    valor: str
    inicio: int
    fin: int


_OPERADORES = {"+": "mas", "-": "menos", "*": "por", "(": "izq", ")": "der"}
TRASPUESTA = "ᵀ"


def _exponente(texto, i):
    """Mensaje para un `^` que no forma `^T`: el exponente no se interpreta."""
    if texto[i + 1:].lstrip().startswith("-1"):
        return (
            "^-1 no se interpreta como inversa: ^ solo admite T, la traspuesta (A^T o Aᵀ). "
            "La inversa se calcula en la herramienta Matriz inversa."
        )
    return "^ solo indica la traspuesta, como A^T o Aᵀ. Esta herramienta no calcula potencias."


def tokenizar(texto):
    """Devuelve los tokens y un token `fin`. Lanza ValueError si hay un carácter ajeno."""
    tokens = []
    i = 0
    n = len(texto)
    while i < n:
        if texto[i].isspace():
            i += 1
            continue
        if texto[i].isdigit():
            inicio = i
            i += 1
            while i < n and texto[i].isdigit():
                i += 1
            if i < n and texto[i] == "." and i + 1 < n and texto[i + 1].isdigit():
                i += 2
                while i < n and texto[i].isdigit():
                    i += 1
            elif i < n and texto[i] == "/" and i + 1 < n and texto[i + 1].isdigit():
                i += 2
                while i < n and texto[i].isdigit():
                    i += 1
            tokens.append(Token("numero", texto[inicio:i], inicio, i))
            continue
        # ᵀ es una letra modificadora para isalpha(): se separa antes de leer nombres.
        if texto[i] == TRASPUESTA:
            tokens.append(Token("traspuesta", TRASPUESTA, i, i + 1))
            i += 1
            continue
        if texto[i] == "^":
            if texto[i + 1:i + 2] != "T":
                raise ValueError(_exponente(texto, i))
            tokens.append(Token("traspuesta", "^T", i, i + 2))
            i += 2
            continue
        if texto[i].isalpha():
            inicio = i
            i += 1
            while i < n and texto[i].isalnum() and texto[i] != TRASPUESTA:
                i += 1
            tokens.append(Token("nombre", texto[inicio:i], inicio, i))
            continue
        if texto[i] == "/":
            raise ValueError("Escribe las fracciones sin espacios, como 1/2. La división no es una operación de esta expresión.")
        if texto[i] in "=<>!":
            par = texto[i:i + 2]
            if par in {"==", "!=", "<=", ">="}:
                raise ValueError(f"El operador {par} no forma parte de esta sintaxis. Para comparar dos expresiones usa un solo =.")
            if texto[i] == "=":
                tokens.append(Token("igual", "=", i, i + 1))
                i += 1
                continue
            raise ValueError(f"El operador {texto[i]} no forma parte de esta sintaxis. Para comparar dos expresiones usa un solo =.")
        tipo = _OPERADORES.get(texto[i])
        if tipo is None:
            raise ValueError(f"«{texto[i]}» no forma parte de la sintaxis de una expresión matricial.")
        tokens.append(Token(tipo, texto[i], i, i + 1))
        i += 1
    tokens.append(Token("fin", "", n, n))
    return tokens
