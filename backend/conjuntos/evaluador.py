"""Evalúa valores y produce evidencia matemática; la interfaz decide cómo mostrarla."""

from dataclasses import dataclass
from fractions import Fraction

from backend.presupuesto_computacional import Estimacion
from .modelo import Conjunto, presentar, peso
from .generacion import generar
from .parser import Operacion, Referencia, Relacion
from .presupuesto import Presupuesto


@dataclass(frozen=True)
class Paso:
    operador: str
    operandos: tuple[object, ...]
    resultado: object
    regla: str
    explicacion: str
    testigo: object = None
    pertenece: bool | None = None
    incluido: bool | None = None
    iguales: bool | None = None


@dataclass(frozen=True)
class Resultado:
    valor: bool | Fraction | str | Conjunto
    pasos: tuple[str, ...]
    estimacion: Estimacion
    procedimiento: tuple[Paso, ...] = ()


_peso = peso


def evaluar_expresion(expresion, entorno, *, presupuesto=None):
    presupuesto = presupuesto if presupuesto is not None else Presupuesto()
    calculo_inicial, procedimiento_inicial = presupuesto.calculo, presupuesto.procedimiento
    procedimiento = []
    pasos = []

    def resolver(operando):
        if isinstance(operando, Referencia):
            if operando.nombre not in entorno:
                raise ValueError(f"No existe el conjunto «{operando.nombre}». Defínelo o revisa su nombre.")
            return entorno[operando.nombre]
        if isinstance(operando, Relacion):
            a, b = resolver(operando.izquierda), resolver(operando.derecha)
            presupuesto.reservar(calculo=_peso(a) + _peso(b), procedimiento=_peso(a) + _peso(b) + 1)
            valor, textos, evidencia = _comparar(a, operando.operador, b)
            pasos.extend(textos)
            procedimiento.append(evidencia)
            return valor
        if isinstance(operando, Operacion):
            operandos = tuple(resolver(hijo) for hijo in operando.operandos)
            if operando.operador in ('par', 'potencia', '×'):
                valor, regla, texto = generar(operando.operador, operandos, presupuesto)
                evidencia = Paso(operando.operador, operandos, valor, regla, texto)
                procedimiento.append(evidencia)
                pasos.append(texto)
                return valor
            if any(not isinstance(valor, Conjunto) for valor in operandos):
                raise ValueError("Las operaciones ∪, ∩, ∖, ∁ y |…| requieren conjuntos finitos.")
            peso = sum(_peso(valor) for valor in operandos)
            # Reserva antes de construir el resultado o formatear la evidencia.
            presupuesto.reservar(calculo=2 * peso, procedimiento=2 * peso + 1)
            evidencia = _operar(operando.operador, operandos)
            procedimiento.append(evidencia)
            pasos.append(evidencia.explicacion)
            return evidencia.resultado
        return operando

    valor = resolver(expresion)
    if not procedimiento:
        presupuesto.reservar(procedimiento=_peso(valor))
    estimacion = Estimacion("relacion_conjuntos" if isinstance(expresion, Relacion) else "operacion_conjuntos",
                            (), len(pasos), presupuesto.calculo - calculo_inicial,
                            presupuesto.procedimiento - procedimiento_inicial)
    return Resultado(valor, tuple(pasos), estimacion, tuple(procedimiento))


def evaluar_relacion(relacion, entorno, *, presupuesto=None):
    if not isinstance(relacion, Relacion):
        raise ValueError("Se esperaba una relación entre dos operandos.")
    return evaluar_expresion(relacion, entorno, presupuesto=presupuesto)


def _operar(operador, operandos):
    a = operandos[0]
    if operador == "|":
        cantidad = 0
        for _ in a.elementos:
            cantidad += 1
        return Paso(operador, operandos, Fraction(cantidad), "cardinalidad",
                    f"Contamos una vez cada elemento completo de {presentar(a)}: {cantidad}. Los conjuntos anidados cuentan como un elemento y las repeticiones no cuentan de nuevo.")
    b = operandos[1]
    if operador == "∁":
        for elemento in a.elementos:
            if elemento not in b.elementos:
                raise ValueError(f"El complemento exige que el conjunto esté incluido en el universo explícito; {presentar(elemento)} no pertenece a ese universo.")
    elementos = set()
    if operador == "∪":
        for conjunto in operandos:
            for elemento in conjunto.elementos:
                elementos.add(elemento)
        regla = "union"
        texto = "Tomamos los elementos que pertenecen al menos a uno de los conjuntos, sin repetirlos."
    elif operador == "∩":
        for elemento in a.elementos:
            if elemento in b.elementos:
                elementos.add(elemento)
        regla = "interseccion"
        texto = "Conservamos los elementos completos que pertenecen a ambos conjuntos."
    elif operador in ("∖", "∁"):
        origen, excluir = (b, a) if operador == "∁" else (a, b)
        for elemento in origen.elementos:
            if elemento not in excluir.elementos:
                elementos.add(elemento)
        regla = "complemento" if operador == "∁" else "diferencia"
        texto = ("Comprobamos la inclusión en el universo explícito y tomamos sus elementos que no pertenecen al conjunto."
                 if operador == "∁" else "Tomamos los elementos del conjunto izquierdo que no pertenecen al derecho; el orden de los operandos importa.")
    else:
        raise ValueError("Operación no implementada.")
    valor = Conjunto(frozenset(elementos))
    expresion = f"∁({presentar(a)}, {presentar(b)})" if operador == "∁" else f"{presentar(a)} {operador} {presentar(b)}"
    return Paso(operador, operandos, valor, regla, f"{expresion} = {presentar(valor)}. {texto}",
                incluido=True if operador == "∁" else None)


def _comparar(a, operador, b):
    pasos = [f"Comparamos {presentar(a)} {operador} {presentar(b)}."]
    pertenece = incluido = iguales = falta = None
    if operador in ("∈", "∉"):
        if not isinstance(b, Conjunto):
            raise ValueError("A la derecha de ∈ o ∉ debe haber un conjunto.")
        pertenece = a in b.elementos
        valor = pertenece if operador == "∈" else not pertenece
        pasos.append(f"{presentar(a)} {'aparece' if pertenece else 'no aparece'} como un elemento completo del conjunto derecho. No se descomponen los conjuntos anidados.")
        regla = "pertenencia"
    elif operador in ("⊆", "⊂"):
        if not isinstance(a, Conjunto) or not isinstance(b, Conjunto):
            raise ValueError("La inclusión requiere un conjunto a cada lado; un elemento individual no es un conjunto.")
        falta = next((e for e in a.elementos if e not in b.elementos), None)
        incluido = falta is None
        iguales = a == b
        valor = incluido and (not iguales if operador == "⊂" else True)
        pasos.append(f"El elemento {presentar(falta)} del conjunto izquierdo no pertenece al derecho." if not incluido else
                     "Cada elemento del conjunto izquierdo pertenece al derecho." if a.elementos else
                     "El conjunto vacío está incluido en todo conjunto: no tiene elementos que incumplan la inclusión.")
        if operador == "⊂":
            pasos.append("La inclusión propia exige además conjuntos distintos. " + ("Ambos son iguales." if a == b else "Los conjuntos son distintos."))
        regla = "inclusion_propia" if operador == "⊂" else "inclusion"
    elif operador in ("=", "≠"):
        if type(a) is not type(b):
            raise ValueError("La igualdad requiere operandos del mismo tipo: conjuntos, números o textos.")
        iguales = a == b
        valor = iguales if operador == "=" else not iguales
        pasos.append("Los conjuntos son iguales cuando tienen exactamente los mismos elementos; el orden y las repeticiones no cuentan." if isinstance(a, Conjunto) else
                     "Comparamos los valores de los dos elementos del mismo tipo.")
        pasos.append("Los operandos coinciden." if a == b else "Los operandos son distintos.")
        regla = "igualdad" if operador == "=" else "desigualdad"
    else:
        raise ValueError("Relación no implementada.")
    return valor, pasos, Paso(operador, (a, b), valor, regla, " ".join(pasos),
                              falta, pertenece, incluido, iguales)
