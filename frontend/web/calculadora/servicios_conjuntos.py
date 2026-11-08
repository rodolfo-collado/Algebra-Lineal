"""Adapta la evidencia del motor al resultado único de la herramienta web.

Todo lo que se muestra sale de valores y hechos que el motor ya calculó: aquí solo se
escriben textos, se marcan elementos comparando con los valores del motor y se ordena
la presentación. Ningún gráfico ni script vuelve a operar conjuntos."""

from fractions import Fraction

from backend.conjuntos.cardinalidades import resolver_cardinalidades
from backend.conjuntos.evaluador import evaluar_expresion
from backend.conjuntos.intervalos import Recta
from backend.conjuntos.literales import Lector
from backend.conjuntos.modelo import Conjunto, Par, orden, presentar
from backend.conjuntos.parser import Operacion, Referencia, Relacion, analizar_expresion
from backend.conjuntos.presupuesto import Presupuesto
from backend.conjuntos.recta_visual import datos_recta, notacion_recta
from backend.conjuntos.regiones import construir_venn, detectar_venn

# Por encima de estos tamaños el paso muestra su fórmula, sin desglosar elemento a elemento.
CHIPS_MAXIMOS = 40
SUBCONJUNTOS_MAXIMOS = 64
PRODUCTO_MAXIMO = 10

# Título y regla de cada paso; None usa la explicación del motor (lleva sus recuentos).
REGLAS = {
    'union': ('Unión', 'Reunimos los elementos de ambos conjuntos; los comunes se escriben una sola vez.'),
    'interseccion': ('Intersección', 'Conservamos solo los elementos que están en los dos conjuntos.'),
    'diferencia': ('Diferencia', 'Quitamos del primer conjunto los elementos que también están en el segundo; el orden importa.'),
    'complemento': ('Complemento', 'Partimos del universo y quitamos los elementos del conjunto.'),
    'cardinalidad': ('Cardinalidad', None),
    'par_ordenado': ('Par ordenado', 'El primer y el segundo lugar se conservan: par(a, b) y par(b, a) son distintos si a ≠ b.'),
    'potencia': ('Conjunto potencia', None),
    'producto_cartesiano': ('Producto cartesiano', None),
    'pertenencia': ('Pertenencia', 'Buscamos el valor como un elemento completo; no se miran los elementos de los conjuntos anidados.'),
    'inclusion': ('Inclusión', 'Comprobamos que cada elemento del primer conjunto esté en el segundo.'),
    'inclusion_propia': ('Inclusión propia', 'Además de la inclusión, los conjuntos deben ser distintos.'),
    'igualdad': ('Igualdad', 'Dos conjuntos son iguales si tienen los mismos elementos, sin importar orden ni repeticiones.'),
    'desigualdad': ('Desigualdad', 'Son distintos si algún elemento está en uno y no en el otro.'),
    'union_intervalos': ('Unión de intervalos', 'Reunimos los tramos; dos tramos que se tocan solo se fusionan si el punto de contacto está incluido.'),
    'interseccion_intervalos': ('Intersección de intervalos', 'Conservamos la parte común; en cada frontera manda el extremo más restrictivo.'),
    'diferencia_intervalos': ('Diferencia de intervalos', 'Quitamos del primero lo que cubre el segundo; un extremo quitado cambia de cerrado a abierto y al revés.'),
    'complemento_intervalos': ('Complemento en la recta', 'Partimos del universo y quitamos la región; las fronteras invierten su cierre.'),
    'pertenencia_intervalo': ('Pertenencia a un intervalo', 'Comprobamos las desigualdades de cada tramo y si sus extremos admiten la igualdad.'),
    'relacion_intervalos': ('Relación entre intervalos', 'Comparamos los tramos canónicos y sus cierres.'),
}
MARCAS = {
    'queda': 'queda en el resultado', 'sale': 'se descarta', 'comun': 'está en ambos: se escribe una vez',
    'coincide': 'es el valor buscado', 'esta': 'está en el otro conjunto', 'falta': 'no está en el otro conjunto',
}
INTERVALOS = ('union_intervalos', 'interseccion_intervalos', 'diferencia_intervalos', 'complemento_intervalos',
              'pertenencia_intervalo', 'relacion_intervalos')


def _valor_web(valor):
    if isinstance(valor, Recta):
        return {'tipo':'recta', 'intervalos':[{'inferior':None if i.inferior is None else _valor_web(i.inferior),
                'superior':None if i.superior is None else _valor_web(i.superior),
                'cerrado_inferior':i.cerrado_inferior, 'cerrado_superior':i.cerrado_superior} for i in valor.intervalos]}
    if isinstance(valor, Par):
        return {"tipo": "par", "primero": _valor_web(valor.primero), "segundo": _valor_web(valor.segundo)}
    if type(valor) is bool:
        return {"tipo": "booleano", "valor": valor}
    if isinstance(valor, Conjunto):
        return {"tipo": "conjunto", "elementos": [_valor_web(e) for e in sorted(valor.elementos, key=orden)]}
    if isinstance(valor, str):
        return {"tipo": "texto", "valor": valor}
    return {"tipo": "numero", "numerador": str(valor.numerator), "denominador": str(valor.denominator)}


def texto_valor(valor):
    """Presentación de lectura: los intervalos con su notación habitual."""
    if type(valor) is bool:
        return "Verdadero" if valor else "Falso"
    return notacion_recta(valor) if isinstance(valor, Recta) else presentar(valor)


def _texto_nodo(nodo, exterior=True):
    """Texto de una subexpresión con los nombres que escribió el usuario."""
    if isinstance(nodo, Referencia):
        return nodo.nombre
    if isinstance(nodo, Relacion):
        return f"{_texto_nodo(nodo.izquierda)} {nodo.operador} {_texto_nodo(nodo.derecha)}"
    if isinstance(nodo, Operacion):
        if nodo.operador == '|':
            return f"|{_texto_nodo(nodo.operandos[0])}|"
        if nodo.operador in ('∁', 'potencia', 'par'):
            return f"{nodo.operador}({', '.join(_texto_nodo(h) for h in nodo.operandos)})"
        texto = f" {nodo.operador} ".join(_texto_nodo(h, False) for h in nodo.operandos)
        return texto if exterior else f"({texto})"
    return texto_valor(nodo)


def _nodos_en_orden(arbol):
    """Operaciones y relaciones en el mismo orden en que el evaluador registra sus pasos."""
    nodos = []

    def recorrer(nodo):
        if isinstance(nodo, Relacion):
            recorrer(nodo.izquierda)
            recorrer(nodo.derecha)
            nodos.append(nodo)
        elif isinstance(nodo, Operacion):
            for hijo in nodo.operandos:
                recorrer(hijo)
            nodos.append(nodo)

    recorrer(arbol)
    return nodos


def _chips(conjunto, marca=None, numerar=False):
    elementos = sorted(conjunto.elementos, key=orden)
    return {'elementos': [{'texto': presentar(e), 'marca': marca(e) if marca else None,
                           'aviso': MARCAS.get(marca(e)) if marca else None,
                           'indice': i + 1 if numerar else None}
                          for i, e in enumerate(elementos[:CHIPS_MAXIMOS])],
            'resto': max(0, len(elementos) - CHIPS_MAXIMOS)}


def _grupos(paso, etiquetas):
    """Elementos de los operandos marcados con lo que les ocurre, según los valores del motor."""
    ops, res = paso.operandos, paso.resultado
    if not ops or not isinstance(ops[0], Conjunto) and paso.regla != 'pertenencia':
        return []
    a = ops[0]
    b = ops[1] if len(ops) > 1 and isinstance(ops[1], Conjunto) else None
    regla = paso.regla
    en_res = (lambda e: 'queda' if e in res.elementos else 'sale') if isinstance(res, Conjunto) else None
    grupos = []
    if regla == 'union' and b is not None:
        grupos = [(0, _chips(a, lambda e: 'comun' if e in b.elementos else 'queda')),
                  (1, _chips(b, lambda e: 'comun' if e in a.elementos else 'queda'))]
    elif regla in ('interseccion', 'diferencia') and b is not None:
        grupos = [(0, _chips(a, en_res)), (1, _chips(b, en_res if regla == 'interseccion' else None))]
    elif regla == 'complemento' and b is not None:
        grupos = [(0, _chips(a)), (1, _chips(b, en_res))]
    elif regla == 'cardinalidad':
        grupos = [(0, _chips(a, numerar=True))]
    elif regla == 'pertenencia' and b is not None:
        grupos = [(1, _chips(b, lambda e: 'coincide' if e == a else None))]
    elif regla in ('inclusion', 'inclusion_propia', 'igualdad', 'desigualdad') and b is not None:
        simetrica = regla in ('igualdad', 'desigualdad')
        grupos = [(0, _chips(a, lambda e: 'esta' if e in b.elementos else 'falta')),
                  (1, _chips(b, (lambda e: 'esta' if e in a.elementos else 'falta') if simetrica else None))]
    return [{'etiqueta': etiquetas[i] if i < len(etiquetas) else texto_valor(ops[i]), **g} for i, g in grupos]


def _conclusion(paso, etiquetas, expresion):
    """Frase final de una relación, a partir de los hechos booleanos del motor."""
    a, b = (list(etiquetas) + [None, None])[:2]
    regla, x = paso.regla, texto_valor(paso.operandos[0])
    if regla in ('pertenencia', 'pertenencia_intervalo'):
        hecho = f"{x} es un elemento de {b}." if paso.pertenece else f"{x} no es un elemento de {b}."
    elif paso.operador in ('⊆', '⊂') and paso.incluido is not None:
        if paso.incluido:
            hecho = f"Todo elemento de {a} está en {b}." if a != '∅' else "El vacío está incluido en cualquier conjunto."
            if paso.operador == '⊂':
                hecho += " Pero son iguales." if paso.iguales else " Además, son distintos."
        elif paso.testigo is not None:
            hecho = f"{presentar(paso.testigo)} está en {a} pero no en {b}."
        else:
            hecho = f"Una parte de {a} queda fuera de {b}."
    elif paso.iguales is not None:
        if any(isinstance(v, (Conjunto, Recta)) for v in paso.operandos):
            hecho = "Tienen exactamente los mismos elementos." if paso.iguales else "No tienen los mismos elementos."
        else:
            hecho = "Los dos valores coinciden." if paso.iguales else "Los dos valores son distintos."
    else:
        return None
    return f"{hecho} Por eso, {expresion} es {texto_valor(paso.resultado).lower()}."


def _formula(paso, nodo):
    valores = [texto_valor(v) for v in paso.operandos]
    igual = f" = {texto_valor(paso.resultado)}"
    if paso.operador == '|':
        return f"|{valores[0]}|{igual}"
    if paso.operador in ('∁', 'potencia', 'par'):
        return f"{paso.operador}({', '.join(valores)})" + ('' if paso.operador == 'par' else igual)
    if type(paso.resultado) is bool:
        return f"{valores[0]} {paso.operador} {valores[1]}"
    return f"{valores[0]} {paso.operador} {valores[1]}{igual}"


def _paso_vista(numero, paso, nodo):
    titulo, frase = REGLAS.get(paso.regla, (paso.regla, None))
    etiquetas = []
    if isinstance(nodo, Relacion):
        etiquetas = [_texto_nodo(nodo.izquierda), _texto_nodo(nodo.derecha)]
    elif isinstance(nodo, Operacion):
        etiquetas = [_texto_nodo(h) for h in nodo.operandos]
    formula = _formula(paso, nodo)
    expresion = _texto_nodo(nodo) if nodo is not None else None
    vista = {'numero': numero, 'titulo': titulo, 'regla': paso.regla,
             # La expresión con nombres solo se añade si dice algo distinto de la fórmula.
             'expresion': expresion if expresion and not formula.startswith(expresion) else None,
             'formula': formula, 'frase': frase or paso.explicacion,
             'grupos': _grupos(paso, etiquetas), 'conclusion': None}
    if type(paso.resultado) is bool:
        vista['conclusion'] = _conclusion(paso, etiquetas or [texto_valor(v) for v in paso.operandos], expresion or formula)
    if paso.regla == 'potencia' and len(paso.resultado.elementos) <= SUBCONJUNTOS_MAXIMOS:
        tamanos = {}
        for s in sorted(paso.resultado.elementos, key=orden):
            tamanos.setdefault(len(s.elementos), []).append(presentar(s))
        vista['subconjuntos'] = [{'tamano': t, 'elementos': tamanos[t]} for t in sorted(tamanos)]
    if paso.regla == 'producto_cartesiano':
        a, b = paso.operandos
        if 0 < len(a.elementos) <= PRODUCTO_MAXIMO and 0 < len(b.elementos) <= PRODUCTO_MAXIMO:
            filas, columnas = sorted(a.elementos, key=orden), sorted(b.elementos, key=orden)
            vista['tabla'] = {'columnas': [presentar(y) for y in columnas],
                              'filas': [{'cabecera': presentar(x), 'celdas': [presentar(Par(x, y)) for y in columnas]} for x in filas]}
    return vista


def describir_region(mascara, nombres):
    """Lectura en palabras de una región de Venn: «Solo en A», «En A y B, fuera de C»."""
    dentro = [n for i, n in enumerate(nombres) if mascara & (1 << i)]
    fuera = [n for i, n in enumerate(nombres) if not mascara & (1 << i)]

    def lista(nombres):
        return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]
    if not dentro:
        return f"Fuera de {lista(fuera)}"
    if not fuera:
        return f"En {lista(dentro)}"
    if len(dentro) == 1:
        return f"Solo en {dentro[0]}"
    return f"En {lista(dentro)}, fuera de {lista(fuera)}"


def notacion_region(mascara, nombres):
    return ' ∩ '.join(n if mascara & (1 << i) else f'{n}ᶜ' for i, n in enumerate(nombres))


def _leer_punto(punto, presupuesto):
    try:
        lector = Lector(punto, presupuesto)
        valor = lector.literal()
        lector.fin()
    except ValueError:
        valor = None
    if not isinstance(valor, Fraction):
        raise ValueError('Escribe un número exacto, por ejemplo 1/2 o 0.25.')
    return valor


def _venn(expresion, entorno, nombres, universo, presupuesto):
    """Regiones para el diagrama: las pedidas o, si no se pidieron, las que usa la expresión."""
    if not nombres:
        detectado = detectar_venn(expresion, entorno)
        if detectado is None:
            return None, None
        universo = universo or detectado[1]
        nombres = tuple(n for n in detectado[0] if n != universo)
        try:
            regiones = construir_venn(nombres, entorno, expresion, universo=universo, presupuesto=presupuesto)
        except ValueError as error:
            return None, f"No se dibuja el diagrama: {error}"
    else:
        regiones = construir_venn(nombres, entorno, expresion, universo=universo, presupuesto=presupuesto)
    regiones = [{**r, 'elementos': [_valor_web(e) for e in r['elementos']],
                 'etiqueta': notacion_region(r['mascara'], nombres),
                 'descripcion': describir_region(r['mascara'], nombres),
                 'etiquetas': [presentar(e) for e in r['elementos']],
                 'cantidad': str(len(r['elementos'])) if r['exterior_conocido'] else None} for r in regiones]
    return {'nombres': nombres, 'universo': universo, 'regiones': regiones}, None


def _recta(resultado, nodos, punto):
    """Datos de la recta: el resultado y los operandos de su última operación, alineados."""
    if not resultado.procedimiento:
        return datos_recta(resultado.valor, punto) if isinstance(resultado.valor, Recta) else None
    ultimo, nodo = resultado.procedimiento[-1], nodos[-1]
    filas = ()
    if ultimo.regla in INTERVALOS:
        hijos = (nodo.izquierda, nodo.derecha) if isinstance(nodo, Relacion) else (nodo.operandos if nodo else ())
        etiquetas = [_texto_nodo(h) for h in hijos] or [texto_valor(v) for v in ultimo.operandos]
        filas = tuple((e, v if isinstance(v, Recta) else Recta()) for e, v in zip(etiquetas, ultimo.operandos)
                      if isinstance(v, Recta) or (isinstance(v, Conjunto) and not v.elementos))
    if isinstance(resultado.valor, Recta):
        return datos_recta(resultado.valor, punto, filas)
    if ultimo.regla == 'pertenencia_intervalo':
        # x ∈ I: el intervalo y el punto que consulta la propia expresión.
        return {**datos_recta(ultimo.operandos[1], ultimo.operandos[0]), 'relacion': True}
    if ultimo.regla == 'relacion_intervalos' and filas:
        return {**datos_recta(Recta(), None, filas), 'tramos': (), 'notacion': None, 'relacion': True}
    return None


def relacion_web(texto, entorno, *, presupuesto=None, punto='', venn_nombres=(), venn_universo=None):
    presupuesto = presupuesto if presupuesto is not None else Presupuesto()
    presupuesto.texto(','.join(venn_nombres) + (venn_universo or ''))
    expresion = analizar_expresion(texto, presupuesto=presupuesto)
    resultado = evaluar_expresion(expresion, entorno, presupuesto=presupuesto)
    nodos = _nodos_en_orden(expresion)
    if len(nodos) != len(resultado.procedimiento):
        nodos = [None] * len(resultado.procedimiento)
    datos = {"valor": _valor_web(resultado.valor), "procedimiento": [{
        "operador": paso.operador, "regla": paso.regla,
        "operandos": [_valor_web(valor) for valor in paso.operandos],
        "resultado": _valor_web(paso.resultado), "explicacion": paso.explicacion,
        "testigo": _valor_web(paso.testigo) if paso.testigo is not None else None,
        "pertenece": paso.pertenece, "incluido": paso.incluido, "iguales": paso.iguales,
    } for paso in resultado.procedimiento]}
    error_punto = valor_punto = None
    # Un punto que quedó escrito de una recta anterior no se aplica a otros resultados.
    if punto and isinstance(resultado.valor, Recta):
        try:
            valor_punto = _leer_punto(punto, presupuesto)
        except ValueError as error:
            error_punto = str(error)
    recta = _recta(resultado, nodos, valor_punto)
    if recta is not None:
        datos['recta'] = recta
    venn, venn_aviso = _venn(expresion, entorno, venn_nombres, venn_universo, presupuesto)
    if venn is not None:
        datos['venn'] = venn
    pasos = [_paso_vista(i + 1, paso, nodo) for i, (paso, nodo) in enumerate(zip(resultado.procedimiento, nodos))]
    valor = resultado.valor
    usadas = {e['marca'] for p in pasos for g in p['grupos'] for e in g['elementos'] if e['marca']}
    return {"expresion": texto, "respuesta": texto_valor(valor), "datos": datos,
            'regiones': venn['regiones'] if venn else None, 'venn': venn, 'venn_aviso': venn_aviso,
            'pasos_vista': pasos, 'error_punto': error_punto, 'tipo': datos['valor']['tipo'],
            'leyenda': [(marca, aviso) for marca, aviso in MARCAS.items() if marca in usadas],
            'cantidad': len(valor.elementos) if isinstance(valor, Conjunto) else None,
            'motivo': pasos[-1]['conclusion'] if pasos and type(valor) is bool else None,
            "pasos": resultado.pasos, "estimacion": resultado.estimacion}


def resumen_definiciones(entorno):
    """Lectura de cada conjunto definido: sus elementos completos y cuántos son."""
    resumen = {}
    for nombre, valor in entorno.items():
        if isinstance(valor, Conjunto):
            elementos = sorted(valor.elementos, key=orden)
            resumen[nombre] = {'cantidad': len(elementos), 'elementos': [presentar(e) for e in elementos[:CHIPS_MAXIMOS]],
                               'resto': max(0, len(elementos) - CHIPS_MAXIMOS)}
        elif isinstance(valor, Recta):
            resumen[nombre] = {'cantidad': None, 'notacion': notacion_recta(valor)}
    return resumen


def cardinalidades_web(nombres, datos, *, modo, universo, expresion):
    """Resultado, regiones con su lectura y la evidencia de inclusión-exclusión, en cadenas exactas."""
    r = resolver_cardinalidades(nombres, datos, modo=modo, universo=universo, expresion=expresion)
    regiones = [{'mascara': m, 'cantidad': None if v is None else str(v), 'seleccionada': m in r['seleccionadas'],
                 'etiqueta': notacion_region(m, nombres), 'descripcion': describir_region(m, nombres),
                 'pertenece': tuple(bool(m & (1 << i)) for i in range(len(nombres))), 'etiquetas': [],
                 'exterior_conocido': v is not None} for m, v in sorted(r['regiones'].items())]
    por_mascara = {reg['mascara']: reg for reg in regiones}
    pasos = []
    for p in r['pasos']:
        vista = {k: v for k, v in p.items() if k != 'restar'}
        vista['resultado'] = str(p['resultado'])
        if 'inicial' in p:
            vista['inicial'] = str(p['inicial'])
            vista['descripcion'] = describir_region(p['mascara'], nombres)
        if 'sustraendos' in p:
            vista['sustraendos'] = [{**s, 'cantidad': str(s['cantidad'])} for s in p['sustraendos']]
        if 'terminos' in p:
            vista['terminos'] = [{**t, 'valor': str(t['valor']), 'cubre': list(t['cubre']),
                                  'desglose': [por_mascara[k]['cantidad'] for k in t['cubre']]} for t in p['terminos']]
            vista['veces'] = {str(k): v for k, v in p['veces'].items()}
            vista['tabla'] = [{'mascara': k, 'descripcion': por_mascara[k]['descripcion'], 'etiqueta': por_mascara[k]['etiqueta'],
                               'celdas': [('+1' if t['signo'] > 0 else '−1') if k in t['cubre'] else '' for t in p['terminos']],
                               'veces': str(v)} for k, v in p['veces'].items()]
        if p['regla'] == 'suma_regiones':
            vista['regiones'] = list(p['regiones'])
            vista['sumandos'] = [{'mascara': m, 'cantidad': por_mascara[m]['cantidad'],
                                  'descripcion': por_mascara[m]['descripcion'], 'etiqueta': por_mascara[m]['etiqueta']}
                                 for m in p['regiones']]
        pasos.append(vista)
    return {**r, 'filas': regiones, 'pasos_vista': pasos, 'expresion': expresion, 'modo': modo, 'datos': {
        'venn': {'nombres': nombres, 'regiones': regiones, 'cantidades': True},
        'resultado': str(r['resultado']), 'union': str(r['union']), 'pasos': pasos}}
