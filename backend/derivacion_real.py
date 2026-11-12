"""Derivación de los árboles validados por FuncionReal."""

import ast
from decimal import Decimal
from .funciones_reales import _signos, finito

_ELEVADOS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")

_SUMA, _PRODUCTO, _POTENCIA, _ATOMO = 1, 2, 3, 4
_NOMBRES = {"sin": "sen", "log10": "log₁₀"}


def _numero(valor):
    """Decimal llano, sin exponente ni «.0»: 2.0 → 2, 1e-05 → 0.00001."""
    if type(valor) is int:
        return str(valor)
    texto = format(Decimal(repr(float(valor))), "f")
    return texto[:-2] if texto.endswith(".0") else texto


def _constante(nodo):
    """Valor de una constante numérica, con signo unario incluido, o None."""
    signo = 1
    while isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.USub):
        signo, nodo = -signo, nodo.operand
    return signo * nodo.value if isinstance(nodo, ast.Constant) else None


def _factores(nodo, salida):
    """Aplana un producto: signo, coeficientes y factores literales (a·b = b·a solo para leer)."""
    if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Mult):
        _factores(nodo.left, salida)
        _factores(nodo.right, salida)
    elif isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.USub) and _constante(nodo) is None:
        salida.append(-1)
        _factores(nodo.operand, salida)
    else:
        salida.append(_constante(nodo) if _constante(nodo) is not None else nodo)
    return salida


def _natural(nodo):
    """(texto, precedencia) en notación de clase: 3x² − 1, 1/x + 2x − cos(x), |x|, √x."""
    if isinstance(nodo, ast.Constant):
        return ("−" if nodo.value < 0 else "") + _numero(abs(nodo.value)), _ATOMO if nodo.value >= 0 else _PRODUCTO
    if isinstance(nodo, ast.Name):
        return {"pi": "π"}.get(nodo.id, nodo.id), _ATOMO
    if isinstance(nodo, ast.Call):
        u, p = _natural(nodo.args[0])
        nombre = nodo.func.id
        if nombre == "abs":
            return f"|{u}|", _ATOMO
        if nombre == "sqrt":
            return (f"√{u}" if p == _ATOMO and "(" not in u else f"√({u})"), _ATOMO
        return f"{_NOMBRES.get(nombre, nombre)}({u})", _ATOMO
    if isinstance(nodo, ast.UnaryOp):
        u, p = _natural(nodo.operand)
        if isinstance(nodo.op, ast.UAdd):
            return u, p
        return "−" + (f"({u})" if p == _SUMA or u.startswith("−") else u), _PRODUCTO
    op = type(nodo.op)
    if op is ast.Pow:
        base, p = _natural(nodo.left)
        base = base if p == _ATOMO and not base.startswith("−") else f"({base})"
        n = _constante(nodo.right)
        if n is not None and float(n).is_integer():
            return base + _numero(n).translate(_ELEVADOS), _POTENCIA
        exponente, p = _natural(nodo.right)
        return f"{base}^{exponente if p == _ATOMO else f'({exponente})'}", _POTENCIA
    if op is ast.Mult:
        factores = _factores(nodo, [])
        coeficiente, literales = 1, []
        for f in factores:
            if isinstance(f, ast.AST):
                literales.append(f)
            else:
                coeficiente *= f
        signo = "−" if coeficiente < 0 else ""
        coeficiente = abs(coeficiente)
        # x y sus potencias antes que las funciones (2x · cos(x)); los cocientes, delante.
        literales.sort(key=lambda f: 1 if isinstance(f, ast.Name) or isinstance(f, ast.BinOp) and isinstance(
            f.op, ast.Pow) and isinstance(f.left, ast.Name) else 0 if isinstance(f, ast.BinOp) else 2)
        textos = [t if p > _PRODUCTO else f"({t})" for t, p in map(_natural, literales)]
        if not textos:
            return signo + _numero(coeficiente), _ATOMO if not signo else _PRODUCTO
        # π y e se pegan a lo que sigue (2πx, e²x); entre otros factores, un punto.
        bases = [f.left if isinstance(f, ast.BinOp) and isinstance(f.op, ast.Pow) else f for f in literales]
        cuerpo = textos[0]
        for anterior, actual, texto in zip(bases, bases[1:], textos[1:]):
            pegado = isinstance(anterior, ast.Name) and anterior.id != "x" and isinstance(actual, ast.Name)
            cuerpo += ("" if pegado else " · ") + texto
        if coeficiente != 1:
            # Coeficiente pegado a su factor (3x², 2(x + 1)); entre dos números, un punto.
            cuerpo = _numero(coeficiente) + ("" if cuerpo[0].isalpha() or cuerpo[0] in "π√|(" else " · ") + cuerpo
        return signo + cuerpo, _PRODUCTO
    izquierda, pi = _natural(nodo.left)
    derecha, pd = _natural(nodo.right)
    if op is ast.Div:
        if pi < _PRODUCTO or isinstance(nodo.left, ast.BinOp) and isinstance(nodo.left.op, ast.Div):
            izquierda = f"({izquierda})"
        if pd <= _PRODUCTO:
            derecha = f"({derecha})"
        return f"{izquierda}/{derecha}", _PRODUCTO
    if op is ast.Sub and pd == _SUMA:
        derecha = f"({derecha})"
    # a + (−b) se lee a − b; a − (−b), a + b.
    if derecha.startswith("−"):
        return f"{izquierda} {'+' if op is ast.Sub else '−'} {derecha[1:]}", _SUMA
    return f"{izquierda} {'+' if op is ast.Add else '−'} {derecha}", _SUMA


def natural(arbol):
    """Notación matemática de lectura para un árbol validado; no se usa para calcular."""
    return _natural(arbol)[0]


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
        self.texto = natural(self.arbol)

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
