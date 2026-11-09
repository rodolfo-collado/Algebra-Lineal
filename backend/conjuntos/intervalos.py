"""Uniones canónicas de intervalos exactos; None significa el infinito del extremo."""

from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class Intervalo:
    inferior: Fraction | None
    superior: Fraction | None
    cerrado_inferior: bool = False
    cerrado_superior: bool = False

    def __post_init__(self):
        if any(x is not None and not isinstance(x, Fraction) for x in (self.inferior, self.superior)):
            raise ValueError('Los extremos deben ser números exactos o infinitos.')
        if type(self.cerrado_inferior) is not bool or type(self.cerrado_superior) is not bool:
            raise ValueError('Indica abierto o cerrado para cada extremo.')
        if (self.inferior is None and self.cerrado_inferior) or (self.superior is None and self.cerrado_superior):
            raise ValueError('Los extremos infinitos siempre son abiertos.')
        if self.inferior is not None and self.superior is not None and self.inferior > self.superior:
            raise ValueError('El extremo inferior no puede superar al superior.')

    @property
    def vacio(self):
        return self.inferior is not None and self.inferior == self.superior and not (self.cerrado_inferior and self.cerrado_superior)


def _inicio(i):
    return (i.inferior is not None, i.inferior or Fraction(0), not i.cerrado_inferior)


@dataclass(frozen=True)
class Recta:
    intervalos: tuple[Intervalo, ...] = ()

    def __post_init__(self):
        tramos = tuple(self.intervalos)
        if any(not isinstance(i, Intervalo) for i in tramos):
            raise ValueError('Una región real contiene intervalos.')
        resultado = []
        for i in sorted((i for i in tramos if not i.vacio), key=_inicio):
            if resultado:
                a = resultado[-1]
                se_unen = a.superior is None or i.inferior is None or i.inferior < a.superior or (i.inferior == a.superior and (a.cerrado_superior or i.cerrado_inferior))
                if se_unen:
                    if a.superior is None or (i.superior is not None and a.superior > i.superior):
                        continue
                    cerrado = a.cerrado_superior or i.cerrado_superior if a.superior == i.superior else i.cerrado_superior
                    resultado[-1] = Intervalo(a.inferior, i.superior, a.cerrado_inferior, cerrado)
                    continue
            resultado.append(i)
        object.__setattr__(self, 'intervalos', tuple(resultado))


def interseccion(a, b):
    if a.inferior is None or (b.inferior is not None and b.inferior > a.inferior):
        inferior, ci = b.inferior, b.cerrado_inferior
    elif a.inferior == b.inferior:
        inferior, ci = a.inferior, a.cerrado_inferior and b.cerrado_inferior
    else:
        inferior, ci = a.inferior, a.cerrado_inferior
    if a.superior is None or (b.superior is not None and b.superior < a.superior):
        superior, cs = b.superior, b.cerrado_superior
    elif a.superior == b.superior:
        superior, cs = a.superior, a.cerrado_superior and b.cerrado_superior
    else:
        superior, cs = a.superior, a.cerrado_superior
    if inferior is not None and superior is not None and inferior > superior:
        return None
    i = Intervalo(inferior, superior, ci, cs)
    return None if i.vacio else i


def operar_rectas(operador, a, b):
    if operador == '∪':
        return Recta(a.intervalos + b.intervalos)
    if operador == '∩':
        tramos = []
        for izquierdo in a.intervalos:
            for derecho in b.intervalos:
                i = interseccion(izquierdo, derecho)
                if i is not None:
                    tramos.append(i)
        return Recta(tuple(tramos))
    if operador == '∖':
        tramos = list(a.intervalos)
        for excluir in b.intervalos:
            nuevos = []
            for original in tramos:
                comun = interseccion(original, excluir)
                if comun is None:
                    nuevos.append(original)
                    continue
                if comun.inferior is not None:
                    nuevos.append(Intervalo(original.inferior, comun.inferior, original.cerrado_inferior, not comun.cerrado_inferior))
                if comun.superior is not None:
                    nuevos.append(Intervalo(comun.superior, original.superior, not comun.cerrado_superior, original.cerrado_superior))
            tramos = [i for i in nuevos if not i.vacio]
        return Recta(tuple(tramos))
    raise ValueError('Operación de intervalos no implementada.')


def contiene(recta, valor):
    if not isinstance(valor, Fraction):
        raise ValueError('La pertenencia a un intervalo requiere un número exacto.')
    for i in recta.intervalos:
        if (i.inferior is None or valor > i.inferior or (valor == i.inferior and i.cerrado_inferior)) and (i.superior is None or valor < i.superior or (valor == i.superior and i.cerrado_superior)):
            return True
    return False


def literal_recta(recta):
    def literal(i):
        return f"intervalo({i.inferior if i.inferior is not None else '-inf'}, {i.superior if i.superior is not None else 'inf'}, {'cerrado' if i.cerrado_inferior else 'abierto'}, {'cerrado' if i.cerrado_superior else 'abierto'})"
    return ' ∪ '.join(literal(i) for i in recta.intervalos) or 'intervalo(0, 0, abierto, abierto)'
