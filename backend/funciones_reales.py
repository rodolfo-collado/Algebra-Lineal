"""Expresiones reales acotadas: interpretación AST, sin ejecutar código del usuario."""

import ast
from decimal import Decimal
from io import StringIO
import math
import operator
import re
import tokenize


FUNCIONES = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "exp": math.exp,
             "log": math.log, "ln": math.log, "log10": math.log10,
             "sqrt": math.sqrt, "abs": abs}
CONSTANTES = {"pi": math.pi, "e": math.e}
OPERACIONES = {ast.Add: operator.add, ast.Sub: operator.sub,
               ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: math.pow}
SUPERINDICES = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")


def normalizar_potencias(texto):
    def entero(coincidencia):
        exponente = coincidencia[0].translate(SUPERINDICES)
        if not re.fullmatch(r"[+-]?[0-9]+", exponente):
            raise ValueError("El superíndice debe ser un exponente entero, con signo opcional al inicio.")
        signo = exponente[0] if exponente[0] in "+-" else ""
        exponente = signo + (exponente.lstrip("+-").lstrip("0") or "0")
        return f"**({exponente})"
    return re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+", entero, texto.replace("^", "**"))


def finito(valor):
    valor = float(valor)
    if not math.isfinite(valor):
        raise ValueError("La evaluación produjo un valor no finito.")
    return valor


def acotar(inferior, superior):
    # Redondeo hacia fuera para no excluir valores por aritmética de máquina.
    # Las operaciones verificadas conservan el cero exacto como cota.
    return (finito(math.nextafter(inferior, -math.inf)) if inferior else 0.,
            finito(math.nextafter(superior, math.inf)) if superior else 0.)


def depende_de_x(nodo):
    return any(isinstance(n, ast.Name) and n.id == "x" for n in ast.walk(nodo))


def explicitar_productos(texto):
    """Insertar * entre factores reconocidos sin separar nombres ni números."""
    salida = []
    anterior = None
    valores = {"x", *CONSTANTES}
    for actual in tokenize.generate_tokens(StringIO(texto).readline):
        tipo, token = actual.type, actual.string
        if tipo == tokenize.NAME and token == "sen":
            token = "sin"
        if tipo == tokenize.COMMENT:
            raise ValueError("No se admiten comentarios en la función.")
        if anterior is not None:
            previo = anterior.string
            if anterior.type == tokenize.NUMBER and token in {"e", "E"} and anterior.end == actual.start:
                raise ValueError("Completa el exponente científico o escribe *e para multiplicar por e.")
            fin = anterior.type == tokenize.NUMBER or previo in valores or previo == ")"
            inicio = token in valores or token in FUNCIONES or token in {"(", "tanx"} or tipo == tokenize.NUMBER
            if fin and inicio and not (anterior.type == tipo == tokenize.NUMBER):
                salida.append((tokenize.OP, "*"))
        if tipo == tokenize.NAME and token == "tanx":
            salida.extend(((tokenize.NAME, "tan"), (tokenize.OP, "("), (tokenize.NAME, "x"), (tokenize.OP, ")")))
            anterior = actual._replace(type=tokenize.OP, string=")")
        else:
            salida.append((tipo, token))
            anterior = actual
    return tokenize.untokenize(salida)


def _signos(nodo, a, b):
    """Signos posibles por reglas exactas para un subconjunto de expresiones reales."""
    if isinstance(nodo, ast.Constant):
        return {(nodo.value > 0) - (nodo.value < 0)}
    if isinstance(nodo, ast.Name):
        if nodo.id != "x":
            return {1}
        return {signo for signo, posible in ((-1, a < 0), (0, a <= 0 <= b), (1, b > 0)) if posible}
    if isinstance(nodo, ast.UnaryOp):
        signos = _signos(nodo.operand, a, b)
        return {-s for s in signos} if isinstance(nodo.op, ast.USub) else signos
    if isinstance(nodo, ast.Call) and nodo.func.id == "exp":
        return {1}
    if isinstance(nodo, ast.BinOp):
        op = nodo.op
        if isinstance(op, ast.Pow):
            base = _signos(nodo.left, a, b)
            if base == {1}:
                return {1}
            if isinstance(nodo.right, ast.Constant):
                n = nodo.right.value
                if type(n) is int and n > 0 and n % 2 == 0:
                    return {abs(s) for s in base}
        if isinstance(op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            izq, der = _signos(nodo.left, a, b), _signos(nodo.right, a, b)
            if isinstance(op, ast.Mult):
                return {s * t for s in izq for t in der}
            if isinstance(op, ast.Div):
                return {s * t for s in izq for t in der if t != 0}
            if isinstance(op, ast.Sub):
                der = {-s for s in der}
            if not (-1 in izq and 1 in der or 1 in izq and -1 in der):
                return {(s + t > 0) - (s + t < 0) for s in izq for t in der}
    return {-1, 0, 1}


def _polo_tangente(x):
    # Comparamos con los múltiplos de π/2 mientras la precisión distinga los polos.
    if abs(x) >= math.pi * 2**51:
        return False
    n = round((x - math.pi / 2) / math.pi)
    return x == (n + .5) * math.pi


def _llamar(nombre, x):
    if nombre == "tan" and _polo_tangente(x):
        raise ValueError("La tangente tiene una discontinuidad y no está definida en un polo.")
    if nombre == "sqrt" and x < 0:
        raise ValueError("La raíz cuadrada real solo admite cantidades mayores o iguales que cero.")
    if nombre in ("log", "ln", "log10") and x <= 0:
        raise ValueError("El logaritmo solo admite cantidades mayores que cero.")
    valor = finito(FUNCIONES[nombre](x))
    if nombre == "exp" and valor == 0:
        raise ValueError("Subdesbordamiento: la exponencial se redondeó a cero.")
    return valor


def _operacion(op, a, b):
    if op is ast.Div and b == 0:
        raise ValueError("No se puede dividir entre cero. El denominador se anula en este punto.")
    valor = OPERACIONES[op](a, b)
    if math.isinf(valor):
        raise OverflowError
    if valor == 0 and a != 0 and (op is ast.Pow or op in (ast.Mult, ast.Div) and b != 0):
        raise ValueError("Subdesbordamiento: el resultado se redondeó a cero.")
    return finito(valor)


def _potencia(nodo, base, exponente):
    if base < 0 and not exponente.is_integer():
        raise ValueError("Potencia fuera del dominio real: una base negativa exige un exponente entero.")
    if base == 0 and exponente < 0:
        raise ValueError("Potencia fuera del dominio real: una base cero no admite un exponente negativo.")
    if base == exponente == 0 and depende_de_x(nodo.right):
        raise ValueError("Potencia fuera del dominio real: una base cero exige un exponente variable positivo.")
    if isinstance(nodo.left, ast.Name) and nodo.left.id == "e":
        return _llamar("exp", exponente)
    return _operacion(ast.Pow, base, exponente)


class FuncionReal:
    def __init__(self, texto):
        if not isinstance(texto, str) or not texto.strip() or len(texto) > 512:
            raise ValueError("Escribe una función de x de hasta 512 caracteres.")
        self.texto = texto.strip()
        try:
            self.expresion = explicitar_productos(normalizar_potencias(self.texto).replace("√", " sqrt").replace("π", " pi ").strip())
            self.arbol = ast.parse(self.expresion, mode="eval").body
            if len(list(ast.walk(self.arbol))) > 160:
                raise ValueError("La función tiene demasiadas operaciones.")
            self._validar(self.arbol, 0)
        except (SyntaxError, RecursionError, ArithmeticError, tokenize.TokenError) as error:
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
            return _llamar(nodo.func.id, self._numero(nodo.args[0], x))
        a, b = self._numero(nodo.left, x), self._numero(nodo.right, x)
        return _potencia(nodo, a, b) if isinstance(nodo.op, ast.Pow) else _operacion(type(nodo.op), a, b)

    def evaluar_arbol(self, nodo, x, nombre="f"):
        x = finito(x)
        try:
            return self._numero(nodo, x)
        except OverflowError as error:
            raise ValueError(f"No se puede evaluar {nombre}({x:g}): desbordamiento del rango numérico.") from error
        except ValueError as error:
            raise ValueError(f"No se puede evaluar {nombre}({x:g}): {error}") from error

    def __call__(self, x):
        return self.evaluar_arbol(self.arbol, x)

    def signo_estricto(self, a, b):
        """Probar que cero queda excluido por los signos, dado un dominio válido."""
        return _signos(self.arbol, a, b) in ({-1}, {1})

    def excluye_cero(self):
        """Excluir un cero en todo el dominio mediante las reglas de signos."""
        return 0 not in _signos(self.arbol, -math.inf, math.inf)

    def rango(self, a, b):
        """Envolvente conservadora; falla si no puede certificar dominio y continuidad."""
        try:
            a, b = finito(a), finito(b)
            if a > b:
                raise ValueError("El extremo a debe ser menor o igual que b.")
            return self._rango(self.arbol, (a, b))
        except OverflowError as error:
            raise ValueError("No podemos aplicar el método en este intervalo. Desbordamiento del rango numérico.") from error
        except ValueError as error:
            raise ValueError("No podemos aplicar el método en este intervalo. " + str(error)) from error

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
                if primera <= ultima or _polo_tangente(a) or _polo_tangente(b):
                    raise ValueError("La tangente no está definida cuando su coseno vale cero. El argumento puede alcanzar uno de esos puntos dentro del intervalo. Elige extremos donde la tangente permanezca definida y continua.")
            if nombre in ("log", "ln", "log10") and a <= 0:
                directo = isinstance(nodo.args[0], ast.Name) and nodo.args[0].id == "x"
                raise ValueError("El logaritmo solo admite cantidades mayores que cero. " +
                                 ("Tu intervalo incluye x iguales o menores que cero. Elige a > 0 y b > a."
                                  if directo else "No pudimos asegurar que la cantidad dentro del logaritmo sea positiva en todo el intervalo. Elige extremos donde se cumpla esa condición."))
            if nombre == "sqrt" and a < 0:
                directo = isinstance(nodo.args[0], ast.Name) and nodo.args[0].id == "x"
                raise ValueError("La raíz cuadrada real √ solo admite cantidades mayores o iguales que cero. " +
                                 ("Tu intervalo incluye valores negativos de x. Para √(x), elige a ≥ 0 y b > a."
                                  if directo else "No pudimos descartar cantidades negativas dentro de la raíz en este intervalo. Elige extremos donde su contenido sea no negativo en todo el intervalo."))
            valores = [_llamar(nombre, a), _llamar(nombre, b)]
            return acotar(min(valores), max(valores))
        a, b = self._rango(nodo.left, intervalo)
        op = type(nodo.op)
        if op is ast.Pow:
            variable = depende_de_x(nodo.right)
            if variable:
                c, d = self._rango(nodo.right, intervalo)
            else:
                c = d = self._numero(nodo.right, 0.)
            if a < 0 and (c != d or not c.is_integer()):
                raise ValueError("No se pudo certificar el dominio real de la potencia en todo el intervalo. "
                                 "Si la base puede ser negativa, se necesita un exponente entero que permanezca fijo.")
            if a <= 0 <= b and (c < 0 or c == 0 and variable):
                raise ValueError("No se pudo certificar el dominio real de la potencia en todo el intervalo. "
                                 "Si la base puede ser cero, el exponente variable debe permanecer positivo "
                                 "y el exponente constante no puede ser negativo.")
            # Para base positiva, log(base^exponente) es bilineal en log(base) y exponente.
            exponentes = (c,) if c == d else (c, d)
            valores = [_potencia(nodo, u, v) for u in (a, b) for v in exponentes]
            if a <= 0 <= b and c > 0:
                valores.append(0.)
        else:
            c, d = self._rango(nodo.right, intervalo)
            if op is ast.Add:
                return acotar(_operacion(op, a, c), _operacion(op, b, d))
            if op is ast.Sub:
                return acotar(_operacion(op, a, d), _operacion(op, b, c))
            if op is ast.Div and c <= 0 <= d:
                raise ValueError("No se puede dividir entre cero. No pudimos descartar un denominador cero dentro de este intervalo. Elige extremos donde el denominador no se anule; cambiar de signo a través de un hueco no garantiza una raíz.")
            valores = [_operacion(op, u, v) for u in (a, b) for v in (c, d)]
        return acotar(min(valores), max(valores))
