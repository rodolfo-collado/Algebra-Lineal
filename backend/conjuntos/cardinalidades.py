"""Inversión manual de intersecciones y principio de inclusión-exclusión."""

from .parser import analizar_expresion
from .presupuesto import Presupuesto
from .regiones import seleccionar_regiones


def resolver_cardinalidades(nombres, datos, *, modo='regiones', universo=None, expresion='A ∪ B', presupuesto=None):
    presupuesto = presupuesto if presupuesto is not None else Presupuesto()
    n = len(nombres)
    if n not in (2,3) or len(set(nombres)) != n or 'U' in nombres:
        raise ValueError('Usa dos o tres nombres distintos de U.')
    cantidad = 1 << n
    if modo not in ('regiones','intersecciones') or set(datos) != set(range(1,cantidad)):
        raise ValueError('Indica todas las regiones o intersecciones de dos o tres conjuntos.')
    valores = (*datos.values(), *((universo,) if universo is not None else ()))
    if any(type(v) is not int or v < 0 or v >= 10**100 for v in valores):
        raise ValueError('Las cardinalidades deben ser enteros no negativos de hasta 100 cifras.')
    presupuesto.reservar(calculo=cantidad * cantidad, procedimiento=cantidad * cantidad)
    regiones = {}
    pasos = []
    def etiqueta(m):
        return ' ∩ '.join(n if m & (1 << i) else f'{n}ᶜ' for i,n in enumerate(nombres))
    for m in sorted(datos, key=lambda m: (-m.bit_count(),m)):
        descontar = tuple(k for k in regiones if k & m == m) if modo == 'intersecciones' else ()
        valor = datos[m]
        for k in descontar:
            valor -= regiones[k]
        if valor < 0:
            raise ValueError(f'Datos incoherentes: la región exclusiva {m} tendría cardinalidad negativa.')
        regiones[m] = valor
        pasos.append({'regla': 'region_exclusiva', 'mascara': m, 'etiqueta':etiqueta(m),
                      'inicial': datos[m], 'restar': descontar,
                      'sustraendos':tuple({'etiqueta':etiqueta(k),'cantidad':regiones[k]} for k in descontar), 'resultado': valor})
    total = 0
    for valor in regiones.values():
        total += valor
    if universo is not None and universo < total:
        raise ValueError('El universo no puede ser menor que la unión de los conjuntos.')
    regiones[0] = None if universo is None else universo - total
    intersecciones = {}
    terminos = []
    union = 0
    for m in range(1,cantidad):
        valor = 0
        for k in range(1,cantidad):
            if k & m == m:
                valor += regiones[k]
        intersecciones[m] = valor
        signo = 1 if m.bit_count() % 2 else -1
        union += signo * valor
        terminos.append({'mascara': m, 'etiqueta':' ∩ '.join(n for i,n in enumerate(nombres) if m & (1 << i)), 'signo': signo, 'valor': valor})
    pasos.append({'regla': 'inclusion_exclusion', 'terminos': tuple(terminos), 'resultado': union})
    arbol = analizar_expresion(expresion, presupuesto=presupuesto)
    seleccionadas = seleccionar_regiones(arbol, nombres, 'U' if universo is not None else None, presupuesto)
    resultado = 0
    for m in seleccionadas:
        if regiones[m] is None:
            raise ValueError('Se necesita la cardinalidad del universo para contar la región exterior.')
        resultado += regiones[m]
    pasos.append({'regla': 'suma_regiones', 'regiones': seleccionadas,
                  'etiquetas':tuple(etiqueta(m) for m in seleccionadas), 'resultado': resultado})
    return {'regiones': regiones, 'intersecciones': intersecciones, 'union': union,
            'seleccionadas': seleccionadas, 'resultado': resultado, 'pasos': tuple(pasos)}
