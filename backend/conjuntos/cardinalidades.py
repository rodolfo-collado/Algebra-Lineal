"""Inversión manual de intersecciones y principio de inclusión-exclusión."""

from .parser import analizar_expresion
from .presupuesto import Presupuesto
from .regiones import UniversoInvalido, seleccionar_regiones


class CardinalidadesIncoherentes(ValueError):
    """Las intersecciones indicadas producen una región con cantidad negativa."""


def inclusion_exclusion(nombres, regiones):
    """Cada intersección suma las regiones que contienen todos sus conjuntos."""
    mascaras = range(1, 1 << len(nombres))
    terminos = []
    for mascara in sorted(mascaras, key=lambda m: (m.bit_count(), m)):
        # Cada bit es un conjunto: una región forma parte de la intersección si tiene todos sus bits.
        cubre = tuple(region for region in mascaras if region & mascara == mascara)
        terminos.append({
            'mascara': mascara,
            'etiqueta': ' ∩ '.join(nombre for i, nombre in enumerate(nombres) if mascara & (1 << i)),
            'signo': 1 if mascara.bit_count() % 2 else -1,
            'valor': sum(regiones[region] for region in cubre),
            'cubre': cubre,
        })
    # La suma de los signos que alcanzan cada región explica por qué se cuenta una vez.
    veces = {region: sum(t['signo'] for t in terminos if region in t['cubre']) for region in mascaras}
    union = sum(t['signo'] * t['valor'] for t in terminos)
    return {'regla': 'inclusion_exclusion', 'terminos': tuple(terminos), 'veces': veces, 'resultado': union}


def resolver_cardinalidades(nombres, datos, *, modo='regiones', universo=None, expresion='A ∪ B', presupuesto=None):
    """Obtiene las regiones exclusivas de dos o tres conjuntos y cuenta los elementos de `expresion`.

    Cada conjunto es un bit: `nombres[i]` corresponde a `1 << i` y una máscara `m` reúne los
    conjuntos cuyos bits están encendidos. En el modo 'regiones', `datos[m]` es la región
    exclusiva `m`: los elementos que están en esos conjuntos y en ningún otro. En el modo
    'intersecciones', `datos[m]` es el cardinal de la intersección de esos conjuntos.
    `datos` lleva una entrada por cada máscara de 1 a 2ⁿ − 1, con enteros no negativos.

    La máscara 0 es la región exterior, fuera de todos los conjuntos: vale universo − |unión|
    o None si no se indica universo. Devuelve `regiones`, `intersecciones`, `union`,
    `seleccionadas`, `resultado` y los `pasos` que muestra la plantilla. Lanza ValueError ante
    datos mal formados, CardinalidadesIncoherentes si una región quedaría negativa y
    UniversoInvalido si el universo es menor que la unión o la expresión lo necesita y falta.
    """
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
    # Primero las máscaras con más conjuntos. Si una región k ya obtenida contiene todos los bits
    # de m (k & m == m), sus elementos están en la intersección m y se descuentan para dejar la
    # región exclusiva. Con tres conjuntos, AB exclusiva = |A ∩ B| − ABC.
    for m in sorted(datos, key=lambda m: (-m.bit_count(),m)):
        descontar = tuple(k for k in regiones if k & m == m) if modo == 'intersecciones' else ()
        valor = datos[m]
        for k in descontar:
            valor -= regiones[k]
        if valor < 0:
            raise CardinalidadesIncoherentes(f'Datos incoherentes: la región {etiqueta(m)} tendría {str(valor).replace('-', '−')} elementos. Una intersección no puede superar a los conjuntos que la contienen; revisa esos datos.')
        regiones[m] = valor
        pasos.append({'regla': 'region_exclusiva', 'mascara': m, 'etiqueta':etiqueta(m),
                      'inicial': datos[m], 'restar': descontar,
                      'sustraendos':tuple({'etiqueta':etiqueta(k),'cantidad':regiones[k]} for k in descontar), 'resultado': valor})
    total = 0
    for valor in regiones.values():
        total += valor
    if universo is not None and universo < total:
        raise UniversoInvalido('El universo no puede ser menor que la unión de los conjuntos.')
    # Región exterior (máscara 0): sin universo no se puede contar.
    regiones[0] = None if universo is None else universo - total
    inclusion = inclusion_exclusion(nombres, regiones)
    intersecciones = {t['mascara']: t['valor'] for t in inclusion['terminos']}
    pasos.append(inclusion)
    arbol = analizar_expresion(expresion, presupuesto=presupuesto)
    seleccionadas = seleccionar_regiones(arbol, nombres, 'U' if universo is not None else None, presupuesto)
    resultado = 0
    for m in seleccionadas:
        if regiones[m] is None:
            raise UniversoInvalido('Se necesita la cardinalidad del universo para contar la región exterior.')
        resultado += regiones[m]
    pasos.append({'regla': 'suma_regiones', 'regiones': seleccionadas,
                  'etiquetas':tuple(etiqueta(m) for m in seleccionadas), 'resultado': resultado})
    return {'regiones': regiones, 'intersecciones': intersecciones, 'union': inclusion['resultado'],
            'seleccionadas': seleccionadas, 'resultado': resultado, 'pasos': tuple(pasos)}
