"""Adapta la evidencia del motor al resultado único de la herramienta web."""

from backend.conjuntos.evaluador import evaluar_expresion
from backend.conjuntos.modelo import Conjunto, Par, presentar
from backend.conjuntos.parser import analizar_expresion
from backend.conjuntos.presupuesto import Presupuesto
from backend.conjuntos.intervalos import Recta
from backend.conjuntos.regiones import construir_venn
from backend.conjuntos.recta_visual import datos_recta
from backend.conjuntos.literales import Lector
from fractions import Fraction


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
        return {"tipo": "conjunto", "elementos": [_valor_web(e) for e in sorted(valor.elementos, key=presentar)]}
    if isinstance(valor, str):
        return {"tipo": "texto", "valor": valor}
    return {"tipo": "numero", "numerador": str(valor.numerator), "denominador": str(valor.denominator)}


def relacion_web(texto, entorno, *, presupuesto=None, punto='', venn_nombres=(), venn_universo=None):
    presupuesto = presupuesto if presupuesto is not None else Presupuesto()
    presupuesto.texto(','.join(venn_nombres) + (venn_universo or ''))
    expresion = analizar_expresion(texto, presupuesto=presupuesto)
    resultado = evaluar_expresion(expresion, entorno, presupuesto=presupuesto)
    respuesta = ("Verdadero" if resultado.valor else "Falso") if type(resultado.valor) is bool else presentar(resultado.valor)
    datos = {"valor": _valor_web(resultado.valor), "procedimiento": [{
        "operador": paso.operador, "regla": paso.regla,
        "operandos": [_valor_web(valor) for valor in paso.operandos],
        "resultado": _valor_web(paso.resultado), "explicacion": paso.explicacion,
        "testigo": _valor_web(paso.testigo) if paso.testigo is not None else None,
        "pertenece": paso.pertenece, "incluido": paso.incluido, "iguales": paso.iguales,
    } for paso in resultado.procedimiento]}
    if isinstance(resultado.valor,Recta):
        valor_punto = None
        if punto:
            lector = Lector(punto, presupuesto)
            valor_punto = lector.literal()
            lector.fin()
            if not isinstance(valor_punto,Fraction):
                raise ValueError('La consulta de punto requiere un número exacto.')
        datos['recta'] = datos_recta(resultado.valor,valor_punto)
    elif punto:
        raise ValueError('La consulta de punto solo se aplica a resultados de intervalos.')
    regiones = None
    if venn_nombres:
        regiones = construir_venn(venn_nombres,entorno,expresion,universo=venn_universo,presupuesto=presupuesto)
        regiones = [{**r, 'elementos':[_valor_web(e) for e in r['elementos']],
                     'etiquetas':[presentar(e) for e in r['elementos']], 'cantidad':str(len(r['elementos']))} for r in regiones]
        datos['venn'] = {'nombres':venn_nombres, 'regiones':regiones}
    return {"expresion": texto, "respuesta": respuesta, "datos": datos, 'regiones':regiones,
            "pasos": resultado.pasos, "estimacion": resultado.estimacion}
