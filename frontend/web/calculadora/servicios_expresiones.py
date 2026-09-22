"""Presenta la evaluación. La aritmética sigue en el backend."""

from fractions import Fraction

from backend.expresiones_matriciales import Comparacion, Evaluacion, aplanar, evaluar
from backend.matrices import vector_columna

from .presentacion_numerica import formatear_exacto
from .servicios import formatear_matriz
from .servicios_matrices import combinacion_columnas

_SIGNOS = {"resta": "−", "resta_vector": "−", "escalar": "·", "escalar_vector": "·"}


def evaluar_expresion_web(entrada):
    resultado = evaluar(entrada["expresion"], entrada["simbolos"], entrada.get("nodo"))
    if isinstance(resultado, Comparacion):
        return presentar_igualdad(resultado)
    return presentar(resultado)


def presentar_igualdad(comparacion):
    if not comparacion.comparable:
        titulo, veredicto = "No se pueden comparar ambos lados", "incomparable"
    elif comparacion.coincide:
        titulo, veredicto = "Ambos lados coinciden", "coincide"
    else:
        titulo, veredicto = "Los resultados son diferentes", "distinto"
    return {
        "modo": "igualdad",
        "texto": comparacion.texto,
        "titulo": titulo,
        "veredicto": veredicto,
        "mensaje": comparacion.mensaje,
        "coincide": comparacion.coincide,
        "comparable": comparacion.comparable,
        "dimensiones": None if veredicto == "incomparable" else dimensiones(comparacion.izquierda),
        "izquierda": presentar(Evaluacion(comparacion.izquierda)),
        "derecha": presentar(Evaluacion(comparacion.derecha)),
    }


def presentar(evaluacion):
    pasos = aplanar(evaluacion.principal)
    visibles = pasos if len(pasos) == 1 else [paso for paso in pasos if paso.operacion not in ("numero", "simbolo")]
    return {
        "texto": evaluacion.principal.texto,
        "tipo": evaluacion.principal.tipo,
        "parcial": evaluacion.principal.id != "0",
        "dimensiones": dimensiones(evaluacion.principal),
        "igualdad": igualdad(evaluacion.principal),
        "matriz": matriz_de(evaluacion.principal),
        "pasos": [presentar_paso(paso) for paso in visibles],
    }


def presentar_paso(paso):
    return {
        "id": paso.id,
        "texto": paso.texto,
        "operacion": paso.operacion,
        "igualdad": igualdad(paso),
        "matriz": matriz_de(paso),
        "lineas": lineas(paso),
    }


def dimensiones(paso):
    if paso.tipo == "escalar":
        return "escalar"
    if paso.tipo == "vector":
        return f"{paso.filas} componente" + ("" if paso.filas == 1 else "s")
    return f"{paso.filas}×{paso.columnas}"


def igualdad(paso):
    if paso.tipo == "matriz":
        return f"{paso.texto} ="
    return f"{paso.texto} = {texto_valor(paso)}"


def texto_valor(paso):
    if paso.tipo == "escalar":
        return formatear_exacto(paso.resultado)
    return "[" + ", ".join(formatear_exacto(componente) for componente in paso.resultado) + "]"


def matriz_de(paso):
    if paso.tipo == "matriz":
        return formatear_matriz(paso.resultado)
    if paso.tipo == "vector":
        return formatear_matriz(vector_columna(paso.resultado))
    return None


def lineas(paso):
    detalle = paso.detalle or {}
    operacion = detalle.get("operacion")
    if operacion in ("producto", "matriz_vector"):
        return lineas_producto(detalle) + lineas_columnas(detalle)
    pasos = detalle.get("pasos") or ()
    if not pasos:
        return []
    signo = _SIGNOS.get(operacion, "+")
    if isinstance(pasos[0], dict):
        return [linea_operandos(entrada, signo) for entrada in pasos]
    return [linea_operandos(entrada, signo) for fila in pasos for entrada in fila]


def lineas_producto(detalle):
    """Las mismas entradas que ya calculó resolver_operacion_matrices, sin rehacer el producto."""
    resultado = []
    for fila in detalle["pasos"]:
        for paso in fila:
            sustitucion = " + ".join(
                f"{operando(a)}·{operando(b)}" for a, b in zip(paso["fila"], paso["columna"])
            )
            resultado.append(f"{sustitucion} = {formatear_exacto(paso['resultado'])}")
    return resultado


def lineas_columnas(detalle):
    return [
        f"{combinacion_columnas(columna['coeficientes'])} = [{', '.join(formatear_exacto(valor) for valor in columna['resultado'])}]"
        for columna in detalle["columnas"]
    ]


def linea_operandos(paso, signo):
    expresion = f" {signo} ".join(operando(valor) for valor in paso["operandos"])
    return f"{expresion} = {formatear_exacto(paso['resultado'])}"


def operando(numero):
    numero = Fraction(numero)
    texto = formatear_exacto(numero)
    return f"({texto})" if numero < 0 or numero.denominator != 1 else texto
