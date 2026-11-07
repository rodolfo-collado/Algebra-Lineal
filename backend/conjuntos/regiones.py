"""Regiones disjuntas de Venn y selección mediante el evaluador compartido."""

from fractions import Fraction

from .evaluador import evaluar_expresion
from .modelo import Conjunto, presentar, peso
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


def construir_venn(nombres, entorno, arbol, *, universo=None, presupuesto=None):
    presupuesto = presupuesto if presupuesto is not None else Presupuesto()
    if len(nombres) not in (2,3) or len(set(nombres)) != len(nombres):
        raise ValueError('Selecciona dos o tres nombres distintos para Venn.')
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
    for e in sorted(elementos, key=presentar):
        mascara = 0
        for i,conjunto in enumerate(conjuntos):
            if e in conjunto.elementos:
                mascara |= 1 << i
        regiones[mascara].append(e)
    return tuple({'mascara': m, 'pertenece': tuple(bool(m & (1 << i)) for i in range(len(nombres))),
                  'elementos': tuple(valores), 'seleccionada': m in seleccionadas,
                  'exterior_conocido': bool(universo) or m != 0}
                 for m,valores in enumerate(regiones))
