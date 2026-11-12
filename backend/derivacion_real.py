"""Derivación de los árboles validados por FuncionReal."""

import ast
import re
from .funciones_reales import _signos, finito

_ELEVADOS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def legible(texto):
    """Exponentes enteros como superíndices: 3 · x^2 − 1 → 3 · x² − 1. Solo presentación."""
    return re.sub(r"\^(?:\((-?\d+)\)|(\d+)(?![.\d]))",
                  lambda m: (m[1] or m[2]).translate(_ELEVADOS), texto)


def _operar(op, a, b):
    cero, uno = ast.Constant(0), ast.Constant(1)
    av = a.value if isinstance(a, ast.Constant) else None
    bv = b.value if isinstance(b, ast.Constant) else None
    if op in (ast.Add, ast.Sub) and bv == 0:
        return a
    if op is ast.Add and av == 0:
        return b
    if op is ast.Mult:
        if av == 0 or bv == 0:
            return cero
        if av == 1:
            return b
        if bv == 1:
            return a
    if op is ast.Div:
        if bv == 1:
            return a
        # d(ln(kx)) = 1/x para k constante distinto de cero.
        if av and isinstance(b, ast.BinOp) and isinstance(b.op, ast.Mult):
            for factor, resto in ((b.left, b.right), (b.right, b.left)):
                if isinstance(factor, ast.Constant) and factor.value == av:
                    return ast.BinOp(uno, ast.Div(), resto)
    if op is ast.Pow and bv in (0, 1):
        return uno if bv == 0 else a
    return ast.BinOp(a, op(), b)


def _llamada(nombre, argumento):
    return ast.Call(ast.Name(nombre, ast.Load()), [argumento], [])


class DerivadaReal:
    def __init__(self, funcion):
        self.funcion = funcion
        self.arbol = self._derivar(funcion.arbol)
        self.texto = (ast.unparse(self.arbol).replace(" ** ", "^").replace(" * ", " · ")
                      .replace("sin(", "sen(").replace("sqrt(", "√(").replace(" - ", " − "))

    def __call__(self, x):
        x = finito(x)
        self.funcion(x)
        return self.funcion._numero(self.arbol, x)

    def _derivar(self, nodo):
        c = ast.Constant
        if isinstance(nodo, ast.Constant):
            return c(0)
        if isinstance(nodo, ast.Name):
            return c(int(nodo.id == "x"))
        if isinstance(nodo, ast.UnaryOp):
            d = self._derivar(nodo.operand)
            if isinstance(nodo.op, ast.UAdd) or isinstance(d, ast.Constant) and d.value == 0:
                return d
            return ast.UnaryOp(ast.USub(), d)
        if isinstance(nodo, ast.Call):
            u = nodo.args[0]
            d = self._derivar(u)
            nombre = nodo.func.id
            if nombre == "sin":
                return _operar(ast.Mult, _llamada("cos", u), d)
            if nombre == "cos":
                return _operar(ast.Mult, ast.UnaryOp(ast.USub(), _llamada("sin", u)), d)
            if nombre == "exp":
                return _operar(ast.Mult, nodo, d)
            if nombre == "abs":
                signos = _signos(u, -float("inf"), float("inf"))
                if -1 not in signos:
                    return d
                if 1 not in signos:
                    return ast.UnaryOp(ast.USub(), d)
                return _operar(ast.Mult, _operar(ast.Div, u, nodo), d)
            if isinstance(d, ast.Constant) and d.value == 0:
                return d
            if nombre == "tan":
                divisor = _operar(ast.Pow, _llamada("cos", u), c(2))
            elif nombre in ("ln", "log"):
                divisor = u
            elif nombre == "log10":
                divisor = _operar(ast.Mult, u, _llamada("ln", c(10)))
            elif nombre == "sqrt":
                divisor = _operar(ast.Mult, c(2), nodo)
            else:
                raise ValueError(f"No se admite la derivación de {nombre}.")
            return _operar(ast.Div, d, divisor)

        a, b = nodo.left, nodo.right
        da = self._derivar(a)
        op = type(nodo.op)
        if op is ast.Pow:
            exponente = self.funcion._numero(b, 0.)
            if exponente == 0:
                return c(0)
            if exponente == 1:
                return da
            n = int(exponente) if exponente.is_integer() and abs(exponente) < 2**53 else exponente
            potencia = _operar(ast.Pow, a, c(n - 1))
            return _operar(ast.Mult, _operar(ast.Mult, c(n), potencia), da)
        db = self._derivar(b)
        if op in (ast.Add, ast.Sub):
            return _operar(op, da, db)
        if op is ast.Mult:
            return _operar(ast.Add, _operar(ast.Mult, da, b), _operar(ast.Mult, a, db))
        if isinstance(db, ast.Constant) and db.value == 0:
            return _operar(ast.Div, da, b)
        numerador = _operar(ast.Sub, _operar(ast.Mult, da, b), _operar(ast.Mult, a, db))
        return _operar(ast.Div, numerador, _operar(ast.Pow, b, c(2)))
