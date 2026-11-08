"""Regiones disjuntas de Venn y selección mediante el evaluador compartido."""

from fractions import Fraction

from .evaluador import evaluar_expresion
from .modelo import Conjunto, orden, peso
from .parser import Operacion, Referencia
from .presupuesto import Presupuesto


def seleccionar_regiones(arbol, nombres, universo, presupuesto):
    pendientes = [arbol]
    while pendientes:
        nodo = pendientes.pop()
        if isinstance(nodo, Referencia):
            if nodo.nombre not in (*nombres, universo):
                raise ValueError('La expresión de regiones solo puede usar los conjuntos seleccionados y su universo.')
        elif isinstance(nodo, Operacion) and nodo.operador in ('∪','∩','∖','∁'):
            pendientes.extend(nodo.operandos)
        elif not (isinstance(nodo, Conjunto) and not nodo.elementos):
            raise ValueError('Para resaltar regiones usa unión, intersección, diferencia o complemento entre los nombres seleccionados.')
    cantidad = 1 << len(nombres)
    entorno = {nombre: Conjunto(frozenset(Fraction(m) for m in range(cantidad) if m & (1 << i))) for i,nombre in enumerate(nombres)}
    if universo:
        entorno[universo] = Conjunto(frozenset(Fraction(m) for m in range(cantidad)))
    resultado = evaluar_expresion(arbol, entorno, presupuesto=presupuesto).valor
    return tuple(m for m in range(cantidad) if Fraction(m) in resultado.elementos)


def detectar_venn(arbol, entorno):
    """Nombres (en orden de aparición) y universo de una expresión de regiones, o None.

    Solo reconoce lo que seleccionar_regiones acepta; el universo es el segundo argumento
    de ∁ cuando es un nombre. Así el diagrama aparece sin pedir datos extra."""
    nombres, universos = [], set()

    def recorrer(nodo):
        if isinstance(nodo, Referencia):
            if nodo.nombre not in nombres:
                nombres.append(nodo.nombre)
            return True
        if isinstance(nodo, Operacion) and nodo.operador in ('∪', '∩', '∖', '∁'):
            if nodo.operador == '∁' and isinstance(nodo.operandos[1], Referencia):
                universos.add(nodo.operandos[1].nombre)
            return all(recorrer(hijo) for hijo in nodo.operandos)
        return isinstance(nodo, Conjunto) and not nodo.elementos

    if not recorrer(arbol):
        return None
    universo = next(iter(universos)) if len(universos) == 1 else None
    if universo:
        nombres.remove(universo)
    if not 1 <= len(nombres) <= 3 or (len(nombres) == 1 and not universo):
        return None
    if any(not isinstance(entorno.get(n), Conjunto) for n in (*nombres, *((universo,) if universo else ()))):
        return None
    return tuple(nombres), universo


def construir_venn(nombres, entorno, arbol, *, universo=None, presupuesto=None):
    presupuesto = presupuesto if presupuesto is not None else Presupuesto()
    if len(nombres) not in (1,2,3) or len(set(nombres)) != len(nombres) or (len(nombres) == 1 and not universo):
        raise ValueError('Selecciona dos o tres nombres distintos para Venn (uno basta si indicas el universo).')
    if universo in nombres:
        raise ValueError('El universo debe tener un nombre distinto de los conjuntos.')
    if any(n not in entorno or not isinstance(entorno[n], Conjunto) for n in (*nombres, *((universo,) if universo else ()))):
        raise ValueError('Venn requiere conjuntos finitos definidos, incluido el universo si se indica.')
    conjuntos = tuple(entorno[n] for n in nombres)
    volumen = sum(peso(c) for c in conjuntos)
    if universo:
        u = entorno[universo]
        volumen += peso(u)
    presupuesto.reservar(calculo=4 * volumen, procedimiento=2 * volumen)
    elementos = set()
    for conjunto in conjuntos:
        for e in conjunto.elementos:
            if universo and e not in u.elementos:
                raise ValueError('Todos los conjuntos de Venn deben estar incluidos en el universo.')
            elementos.add(e)
    if universo:
        elementos = u.elementos
    seleccionadas = seleccionar_regiones(arbol, nombres, universo, presupuesto)
    regiones = [[] for _ in range(1 << len(nombres))]
    for e in sorted(elementos, key=orden):
        mascara = 0
        for i,conjunto in enumerate(conjuntos):
            if e in conjunto.elementos:
                mascara |= 1 << i
        regiones[mascara].append(e)
    return tuple({'mascara': m, 'pertenece': tuple(bool(m & (1 << i)) for i in range(len(nombres))),
                  'elementos': tuple(valores), 'seleccionada': m in seleccionadas,
                  'exterior_conocido': bool(universo) or m != 0}
                 for m,valores in enumerate(regiones))
