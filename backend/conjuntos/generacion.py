"""Generación manual; reserva el árbol expandido completo antes de enumerarlo."""

from .modelo import Conjunto, Par, peso


def generar(operador, operandos, presupuesto):
    a = operandos[0]
    if operador == 'par':
        valor = Par(*operandos)
        presupuesto.reservar(calculo=peso(valor), procedimiento=2 * peso(valor))
        return valor, 'par_ordenado', 'El orden y las dos posiciones del par se conservan.'
    if any(not isinstance(v, Conjunto) for v in operandos):
        raise ValueError('Potencia y producto cartesiano requieren conjuntos finitos.')
    if operador == 'potencia':
        cantidad = 1
        # Cortar antes de construir potencias o colecciones de tamaño excesivo.
        for _ in a.elementos:
            cantidad *= 2
            if cantidad > 45000:
                raise ValueError('El conjunto potencia supera el presupuesto de generación.')
        volumen = 1 + cantidad + (cantidad // 2) * (peso(a) - 1)
        presupuesto.reservar(calculo=volumen, procedimiento=2 * volumen + peso(a))
        subconjuntos = [Conjunto()]
        for elemento in a.elementos:
            nuevos = []
            for subconjunto in subconjuntos:
                elementos = list(subconjunto.elementos)
                elementos.append(elemento)
                nuevos.append(Conjunto(frozenset(elementos)))
            subconjuntos.extend(nuevos)
        return Conjunto(frozenset(subconjuntos)), 'potencia', f'Cada elemento puede incluirse o excluirse: 2^{len(a.elementos)} = {cantidad} subconjuntos, incluido el vacío.'
    b = operandos[1]
    volumen = 1 + len(a.elementos) * len(b.elementos) + len(b.elementos) * (peso(a) - 1) + len(a.elementos) * (peso(b) - 1)
    presupuesto.reservar(calculo=volumen, procedimiento=2 * volumen + peso(a) + peso(b))
    pares = []
    for primero in a.elementos:
        for segundo in b.elementos:
            pares.append(Par(primero, segundo))
    return Conjunto(frozenset(pares)), 'producto_cartesiano', f'Por cada elemento izquierdo recorremos los derechos: {len(a.elementos)} × {len(b.elementos)} = {len(pares)} pares ordenados.'
