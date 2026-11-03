"""Adapta la evidencia del motor al resultado único de la herramienta web."""

from backend.conjuntos.evaluador import evaluar_relacion
from backend.conjuntos.parser import analizar_relacion


def relacion_web(texto, entorno, *, presupuesto=None):
    relacion = analizar_relacion(texto, presupuesto=presupuesto)
    resultado = evaluar_relacion(relacion, entorno)
    return {"expresion": texto, "respuesta": "Verdadero" if resultado.valor else "Falso",
            "pasos": resultado.pasos, "estimacion": resultado.estimacion}
