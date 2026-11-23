"""Traduce el AST de FuncionReal a SymPy y conserva sus restricciones reales."""

import ast
from dataclasses import dataclass
from decimal import Decimal
import math

import sympy as sp
from sympy.core.relational import Relational
from sympy.solvers.inequalities import solve_poly_inequality

from .funciones_reales import FuncionReal

_X = sp.Symbol("x", real=True)
_CONSTANTES = {"x": _X, "pi": sp.pi, "e": sp.E}
_FUNCIONES = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "exp": sp.exp,
    "ln": sp.log, "log": sp.log, "sqrt": sp.sqrt, "abs": sp.Abs,
}
_BINARIAS = {ast.Add: sp.Add, ast.Mult: sp.Mul}
_RELACIONES = {"!=": sp.Ne, ">": sp.Gt, ">=": sp.Ge}
_EXPONENTE_MAXIMO = 1024
_GRADO_CANCELACION = 4
_GRADO_DOMINIO = 2
_BITS_CANCELACION = 2048


@dataclass(frozen=True)
class RestriccionDominio:
    condicion: Relational
    conjunto: sp.Set | None


@dataclass(frozen=True)
class DominioReal:
    conjunto: sp.Set | None
    restricciones: tuple[RestriccionDominio, ...]
    removibles: sp.Set


@dataclass(frozen=True)
class FuncionSimbolica:
    texto_original: str
    variable: sp.Symbol
    expresion: sp.Expr
    dominio: DominioReal


def _cota_racional(expr):
    """Cota de grado y tamaño antes de permitir una expansión racional."""
    if isinstance(expr, sp.Rational):
        return 0, max(int(expr.p).bit_length(), int(expr.q).bit_length())
    if expr == _X:
        return 1, 1
    if expr.func is sp.Pow and isinstance(expr.exp, sp.Integer):
        cota = _cota_racional(expr.base)
        if cota is not None:
            n = abs(int(expr.exp))
            return cota[0] * n, cota[1] * n + 1
    elif expr.func in (sp.Add, sp.Mul):
        cotas = [_cota_racional(arg) for arg in expr.args]
        if all(cota is not None for cota in cotas):
            grado = sum(cota[0] for cota in cotas)
            bits = sum(cota[1] for cota in cotas) + len(cotas)
            return grado, bits
    return None


def _cancelar_acotado(expr):
    cota = _cota_racional(expr)
    if cota is not None and cota[0] <= _GRADO_CANCELACION and cota[1] <= _BITS_CANCELACION:
        resultado = sp.cancel(expr, _X)
        if _cota_racional(resultado) is not None:
            return resultado
    return None


def _resolver_restriccion(expr, relacion):
    if relacion == "!=" and expr.func is sp.cos:
        argumento = _cancelar_acotado(expr.args[0])
        if argumento is not None:
            num, den = sp.fraction(argumento)
            if isinstance(den, sp.Rational):
                polinomio = sp.Poly(num, _X, domain=sp.QQ)
                if polinomio.degree() <= 1:
                    pendiente, origen = (polinomio.nth(i) / den for i in (1, 0))
                    if pendiente:
                        k = sp.Dummy("k", integer=True)
                        polos = sp.ImageSet(sp.Lambda(k, (sp.pi * (k + sp.S.Half) - origen) / pendiente),
                                            sp.S.Integers)
                        return sp.Complement(sp.S.Reals, polos, evaluate=False)
                    # Un argumento racional constante nunca coincide con pi/2 + k*pi.
                    return sp.S.Reals
        return None

    racional = _cancelar_acotado(expr)
    if racional is None:
        return None
    num, den = sp.fraction(racional)
    if relacion != "!=" and not isinstance(den, sp.Rational):
        # shortcut: las desigualdades racionales requieren partir por el signo del denominador.
        return None
    expresion = num if relacion == "!=" else num / den
    polinomio = sp.Poly(expresion, _X, domain=sp.QQ)
    if polinomio.degree() > _GRADO_DOMINIO:
        return None
    # La visita ya registró el dominio del denominador antes de comprobar num != 0.
    return sp.Union(*solve_poly_inequality(polinomio, relacion))


def _dominio(restricciones, racional):
    resueltas = [r.conjunto for r in restricciones if r.conjunto is not None]
    periodicos = [s for s in resueltas if isinstance(s, sp.Complement)]
    conjunto = sp.Intersection(sp.S.Reals, *(s for s in resueltas if s not in periodicos))
    if periodicos and conjunto != sp.S.EmptySet:
        # Conservar el conjunto exacto sin activar un solver para intersecciones periódicas.
        conjuntos = periodicos if conjunto == sp.S.Reals else [conjunto, *periodicos]
        conjunto = sp.Intersection(*conjuntos, evaluate=False)
    if conjunto != sp.S.EmptySet and any(r.conjunto is None for r in restricciones):
        conjunto = None

    removibles = sp.S.EmptySet
    if racional is not None and conjunto is not None:
        excluidos = sp.S.Reals - conjunto
        if isinstance(excluidos, sp.FiniteSet):
            _, den = sp.fraction(racional)
            removibles = sp.FiniteSet(*(x for x in excluidos if den.subs(_X, x).is_zero is False))
    return DominioReal(conjunto, tuple(restricciones), removibles)


def _literal(funcion, nodo):
    if type(nodo.value) is int:
        return sp.Integer(nodo.value)
    if nodo.value == 0:
        return sp.S.Zero
    # El literal finito validado permite recuperar el decimal sin redondeo binario.
    decimal = Decimal(ast.get_source_segment(funcion.expresion, nodo))
    return sp.Rational(*decimal.as_integer_ratio())


def _exponente(funcion, nodo, simbolico):
    try:
        valor = funcion._numero(nodo, 0.)
    except (ArithmeticError, ValueError) as error:
        raise ValueError("El exponente debe poder evaluarse como constante real finita.") from error
    if abs(valor) > _EXPONENTE_MAXIMO:
        raise ValueError(f"El exponente simbólico admite magnitud de hasta {_EXPONENTE_MAXIMO}.")

    if valor.is_integer():
        return sp.Integer(int(valor))
    exacto = _cancelar_acotado(simbolico)
    if isinstance(exacto, sp.Rational) and exacto.q != 1 and (exacto > 0) == (valor > 0):
        if abs(float(exacto) - valor) <= math.ulp(valor):
            return exacto
    if simbolico in (sp.pi, -sp.pi, sp.E, -sp.E):
        return simbolico
    # Conserva el comportamiento real de FuncionReal para exponentes fuera del cálculo racional.
    return sp.Rational(*valor.as_integer_ratio())


def adaptar_funcion(texto: str) -> FuncionSimbolica:
    """Valida texto con FuncionReal antes de construir objetos de SymPy."""
    funcion = FuncionReal(texto)
    restricciones = []

    def restringir(expr, relacion):
        condicion = _RELACIONES[relacion](expr, sp.S.Zero, evaluate=False)
        restricciones.append(RestriccionDominio(condicion, _resolver_restriccion(expr, relacion)))

    def traducir(nodo):
        if isinstance(nodo, ast.Constant):
            return _literal(funcion, nodo)
        if isinstance(nodo, ast.Name):
            return _CONSTANTES[nodo.id]
        if isinstance(nodo, ast.UnaryOp):
            operando = traducir(nodo.operand)
            if isinstance(nodo.op, ast.USub):
                return sp.Mul(-1, operando, evaluate=False)
            if isinstance(nodo.op, ast.UAdd):
                return operando
        if isinstance(nodo, ast.Call):
            nombre = nodo.func.id
            argumento = traducir(nodo.args[0])
            if nombre in ("ln", "log", "log10"):
                restringir(argumento, ">")
            elif nombre == "sqrt":
                restringir(argumento, ">=")
            elif nombre == "tan":
                restringir(sp.cos(argumento, evaluate=False), "!=")
            if nombre == "log10":
                return sp.Mul(sp.log(argumento, evaluate=False), 1 / sp.log(10), evaluate=False)
            return _FUNCIONES[nombre](argumento, evaluate=False)

        if not isinstance(nodo, ast.BinOp):
            raise ValueError("El nodo no tiene traducción simbólica admitida.")
        a, b = traducir(nodo.left), traducir(nodo.right)
        if isinstance(nodo.op, ast.Pow):
            exponente = _exponente(funcion, nodo.right, b)
            if exponente == 0:
                return sp.S.One
            if exponente == 1:
                return a
            if isinstance(exponente, sp.Integer):
                if exponente < 0:
                    restringir(a, "!=")
            else:
                restringir(a, ">" if exponente < 0 else ">=")
            return sp.Pow(a, exponente, evaluate=False)
        if isinstance(nodo.op, ast.Div):
            restringir(b, "!=")
            return sp.Mul(a, sp.Pow(b, -1, evaluate=False), evaluate=False)
        if isinstance(nodo.op, ast.Sub):
            return sp.Add(a, sp.Mul(-1, b, evaluate=False), evaluate=False)
        operacion = _BINARIAS.get(type(nodo.op))
        if operacion is None:
            raise ValueError("La operación no tiene traducción simbólica admitida.")
        return operacion(a, b, evaluate=False)

    expresion = traducir(funcion.arbol)
    racional = _cancelar_acotado(expresion)
    dominio = _dominio(restricciones, racional)
    if racional is not None and dominio.conjunto != sp.S.EmptySet:
        expresion = racional
    return FuncionSimbolica(texto, _X, expresion, dominio)
