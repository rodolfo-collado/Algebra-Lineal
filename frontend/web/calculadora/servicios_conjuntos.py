"""Adapta la evidencia del motor al resultado único de la herramienta web."""

from backend.conjuntos.evaluador import evaluar_expresion
from backend.conjuntos.modelo import Conjunto, Par, presentar
from backend.conjuntos.parser import analizar_expresion
from backend.conjuntos.presupuesto import Presupuesto


def _valor_web(valor):
    if isinstance(valor, Par):
        return {"tipo": "par", "primero": _valor_web(valor.primero), "segundo": _valor_web(valor.segundo)}
    if type(valor) is bool:
        return {"tipo": "booleano", "valor": valor}
    if isinstance(valor, Conjunto):
        return {"tipo": "conjunto", "elementos": [_valor_web(e) for e in sorted(valor.elementos, key=presentar)]}
    if isinstance(valor, str):
        return {"tipo": "texto", "valor": valor}
    return {"tipo": "numero", "numerador": str(valor.numerator), "denominador": str(valor.denominator)}


def relacion_web(texto, entorno, *, presupuesto=None):
    presupuesto = presupuesto if presupuesto is not None else Presupuesto()
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
    return {"expresion": texto, "respuesta": respuesta, "datos": datos,
            "pasos": resultado.pasos, "estimacion": resultado.estimacion}
