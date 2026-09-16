"""Adapta datos exactos a textos; toda la matemática se delega al backend."""

from fractions import Fraction

from backend.matrices import formatear_fraccion, resolver_operacion_matrices

from .opciones_matrices import CONFIGURACION
from .servicios import formatear_matriz


def _operando(numero):
    texto = formatear_fraccion(numero)
    return f"({texto})" if numero < 0 or numero.denominator != 1 else texto


def operar_matrices(entrada):
    operacion = entrada["operacion"]
    matrices = entrada["matrices"]
    calculo = resolver_operacion_matrices(
        operacion, matrices["A"], matrices.get("B"), entrada.get("escalar"),
    )
    opcion = CONFIGURACION[operacion]
    desarrollo = []
    for fila in calculo["pasos"]:
        desarrollo.append([
            (f"a[{paso['origen'][0]}, {paso['origen'][1]}]" if operacion == "traspuesta"
             else f" {opcion['simbolo']} ".join(_operando(n) for n in paso["operandos"]))
            for paso in fila
        ])
    return {
        **opcion, "operacion": operacion,
        "entradas": [{"nombre": nombre, "matriz": formatear_matriz(matrices[nombre])}
                     for nombre in opcion["matrices"]],
        "factor": _operando(Fraction(entrada["escalar"])) if opcion["escalar"] else None,
        "matriz": formatear_matriz(calculo["resultado"]), "desarrollo": desarrollo,
        "dimensiones_entrada": "×".join(map(str, calculo["dimensiones_entrada"])),
        "dimensiones_resultado": "×".join(map(str, calculo["dimensiones_resultado"])),
        "traslados": [", ".join(fila) for fila in formatear_matriz(matrices["A"])]
                     if operacion == "traspuesta" else [],
    }
