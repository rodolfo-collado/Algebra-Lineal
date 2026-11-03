"""Expresiones reales acotadas: interpretación AST, sin ejecutar código del usuario."""

import ast
from decimal import Decimal
import math
import operator


FUNCIONES = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "exp": math.exp,
             "log": math.log, "ln": math.log, "log10": math.log10,
             "sqrt": math.sqrt, "abs": abs}
CONSTANTES = {"pi": math.pi, "e": math.e}
OPERACIONES = {ast.Add: operator.add, ast.Sub: operator.sub,
               ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: math.pow}


def finito(valor):
    valor = float(valor)
    if not math.isfinite(valor):
        raise ValueError("La evaluación produjo un valor no finito.")
    return valor


def acotar(inferior, superior):
    # Redondeo hacia fuera para no excluir valores por aritmética de máquina.
    return (finito(math.nextafter(inferior, -math.inf)),
            finito(math.nextafter(superior, math.inf)))


class FuncionReal:
    def __init__(self, texto):
        if not isinstance(texto, str) or not texto.strip() or len(texto) > 512:
            raise ValueError("Escribe una función de x de hasta 512 caracteres.")
        self.texto = texto.strip()
        try:
            self.expresion = self.texto.replace("^", "**")
            self.arbol = ast.parse(self.expresion, mode="eval").body
            if len(list(ast.walk(self.arbol))) > 160:
                raise ValueError("La función tiene demasiadas operaciones.")
            self._validar(self.arbol, 0)
        except (SyntaxError, RecursionError, ArithmeticError) as error:
            raise ValueError("Función no válida. Usa x, números, *, /, ^ y funciones admitidas.") from error
        self.clave = ast.dump(self.arbol)

    def _validar(self, nodo, nivel):
        if nivel > 24:
            raise ValueError("La función tiene demasiados niveles de paréntesis u operaciones.")
        if isinstance(nodo, ast.Constant) and type(nodo.value) in (int, float):
            finito(nodo.value)
            if type(nodo.value) is float and nodo.value == 0 and Decimal(ast.get_source_segment(self.expresion, nodo)) != 0:
                raise ValueError("Subdesbordamiento: una constante se redondeó a cero.")
        elif isinstance(nodo, ast.Name) and nodo.id in {"x", *CONSTANTES}:
            return
        elif isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.UAdd, ast.USub)):
            self._validar(nodo.operand, nivel + 1)
        elif isinstance(nodo, ast.BinOp) and type(nodo.op) in OPERACIONES:
            self._validar(nodo.left, nivel + 1)
            self._validar(nodo.right, nivel + 1)
            if isinstance(nodo.op, ast.Pow) and any(isinstance(n, ast.Name) and n.id == "x"
                                                   for n in ast.walk(nodo.right)):
                raise ValueError("El exponente debe ser constante; no puede depender de x.")
        elif (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
              and nodo.func.id in FUNCIONES and len(nodo.args) == 1 and not nodo.keywords):
            self._validar(nodo.args[0], nivel + 1)
        else:
            raise ValueError("Sintaxis no admitida. Usa solo x, números y funciones matemáticas permitidas.")

    def _numero(self, nodo, x):
        if isinstance(nodo, ast.Constant):
            return float(nodo.value)
        if isinstance(nodo, ast.Name):
            return x if nodo.id == "x" else CONSTANTES[nodo.id]
        if isinstance(nodo, ast.UnaryOp):
            valor = self._numero(nodo.operand, x)
            return -valor if isinstance(nodo.op, ast.USub) else valor
        if isinstance(nodo, ast.Call):
            valor = finito(FUNCIONES[nodo.func.id](self._numero(nodo.args[0], x)))
            if nodo.func.id == "exp" and valor == 0:
                raise ValueError("Subdesbordamiento: exp(x) se redondeó a cero.")
            return valor
        a, b = self._numero(nodo.left, x), self._numero(nodo.right, x)
        valor = finito(OPERACIONES[type(nodo.op)](a, b))
        if valor == 0 and a != 0 and ((isinstance(nodo.op, (ast.Mult, ast.Div)) and b != 0)
                                    or isinstance(nodo.op, ast.Pow)):
            raise ValueError("Subdesbordamiento: el resultado se redondeó a cero.")
        return valor

    def __call__(self, x):
        try:
            return self._numero(self.arbol, finito(x))
        except (ArithmeticError, ValueError) as error:
            raise ValueError(f"No se puede evaluar f({x:g}): {error}") from error

    def rango(self, a, b):
        """Envolvente conservadora; falla si no puede certificar dominio y continuidad."""
        try:
            return self._rango(self.arbol, (a, b))
        except (ArithmeticError, ValueError) as error:
            raise ValueError("No se pudo verificar dominio y continuidad en todo [a,b]. "
                             "Prueba un intervalo menor o una expresión equivalente. " + str(error)) from error

    def _rango(self, nodo, intervalo):
        if isinstance(nodo, ast.Constant):
            return (float(nodo.value),) * 2
        if isinstance(nodo, ast.Name):
            return intervalo if nodo.id == "x" else (CONSTANTES[nodo.id],) * 2
        if isinstance(nodo, ast.UnaryOp):
            a, b = self._rango(nodo.operand, intervalo)
            return (-b, -a) if isinstance(nodo.op, ast.USub) else (a, b)
        if isinstance(nodo, ast.Call):
            a, b = self._rango(nodo.args[0], intervalo)
            nombre = nodo.func.id
            if nombre in ("sin", "cos"):
                return -1., 1.
            if nombre == "abs":
                return (0. if a <= 0 <= b else min(abs(a), abs(b)), max(abs(a), abs(b)))
            if nombre == "tan":
                primera = math.ceil(math.nextafter((a - math.pi/2)/math.pi, -math.inf))
                ultima = math.floor(math.nextafter((b - math.pi/2)/math.pi, math.inf))
                if primera <= ultima:
                    raise ValueError("tan(x) cruza una asíntota.")
            if nombre in ("log", "ln", "log10") and a <= 0:
                raise ValueError("El argumento del logaritmo debe ser positivo.")
            if nombre == "sqrt" and a < 0:
                raise ValueError("El argumento de sqrt debe ser no negativo.")
            valores = [FUNCIONES[nombre](a), FUNCIONES[nombre](b)]
            if nombre == "exp" and min(valores) == 0:
                raise ValueError("Subdesbordamiento de exp.")
            return acotar(min(valores), max(valores))
        a, b = self._rango(nodo.left, intervalo)
        if isinstance(nodo.op, ast.Pow):
            n = self._numero(nodo.right, 0.)
            if (a < 0 and not n.is_integer()) or (a <= 0 <= b and n < 0):
                raise ValueError("Potencia fuera del dominio real o con división por cero.")
            valores = [math.pow(a, n), math.pow(b, n)]
            if a <= 0 <= b and n > 0:
                valores.append(0.)
        else:
            c, d = self._rango(nodo.right, intervalo)
            if isinstance(nodo.op, ast.Add):
                return acotar(a + c, b + d)
            if isinstance(nodo.op, ast.Sub):
                return acotar(a - d, b - c)
            if isinstance(nodo.op, ast.Div) and c <= 0 <= d:
                raise ValueError("El denominador puede ser cero.")
            op = OPERACIONES[type(nodo.op)]
            valores = [op(u, v) for u in (a, b) for v in (c, d)]
        return acotar(min(valores), max(valores))
