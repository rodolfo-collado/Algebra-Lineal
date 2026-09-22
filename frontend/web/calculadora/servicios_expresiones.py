"""Presenta la evaluación. La aritmética sigue en el backend."""

from fractions import Fraction

from backend.expresiones_matriciales import Comparacion, Determinacion, Evaluacion, aplanar, evaluar
from backend.expresiones_matriciales.lineal import enumerar, texto_forma
from backend.matrices import vector_columna

from .presentacion_numerica import formatear_exacto
from .servicios import formatear_matriz
from .servicios_matrices import combinacion_columnas

_SIGNOS = {"resta": "−", "resta_vector": "−", "escalar": "·", "escalar_vector": "·"}


def evaluar_expresion_web(entrada):
    resultado = evaluar(entrada["expresion"], entrada["simbolos"], entrada.get("nodo"))
    if isinstance(resultado, Determinacion):
        return presentar_determinacion(resultado)
    if isinstance(resultado, Comparacion):
        return presentar_igualdad(resultado)
    return presentar(resultado)


def presentar_determinacion(determinacion):
    variables = determinacion.vector.variables
    nombres = determinacion.nombres_columnas
    producto = f"{determinacion.matriz.nombre}{determinacion.vector.nombre}"
    return {
        "modo": "determinacion",
        "texto": determinacion.texto,
        "nombre": determinacion.matriz.nombre,
        "vector": determinacion.vector.nombre,
        "producto": producto,
        "etiqueta": determinacion.etiqueta,
        "filas": determinacion.matriz.filas,
        "columnas": determinacion.matriz.columnas,
        "variables": variables,
        "variables_texto": enumerar(variables),
        "matriz": formatear_matriz(determinacion.resultado),
        "coeficientes": [[formatear_exacto(coeficiente) for coeficiente in columna] for columna in determinacion.columnas],
        "verificada": determinacion.verificada,
        "por_columnas": f"{determinacion.matriz.nombre} = [{' '.join(nombres)}]",
        "desarrollo": producto + " = " + " + ".join(f"{variable} {nombre}" for variable, nombre in zip(variables, nombres)),
        "agrupacion": determinacion.etiqueta + " = " + " + ".join(
            f"{variable} {_columna(columna)}" for variable, columna in zip(variables, determinacion.columnas)
        ),
        "comparaciones": [
            f"{nombre} = {_columna(columna)}" for nombre, columna in zip(nombres, determinacion.columnas)
        ],
        "comprobacion": [
            f"componente {indice}: {texto_forma(obtenida, variables)} {'coincide' if obtenida == esperada else 'no coincide'}"
            for indice, (obtenida, esperada) in enumerate(zip(determinacion.verificacion, determinacion.componentes), 1)
        ],
    }


def _columna(coeficientes):
    return "[" + ", ".join(formatear_exacto(coeficiente) for coeficiente in coeficientes) + "]^T"


def presentar_igualdad(comparacion):
    if not comparacion.comparable:
        titulo, veredicto = "No se pueden comparar ambos lados", "incomparable"
    elif comparacion.alcance == "simbolica" and comparacion.coincide:
        titulo, veredicto = "Misma expresión lineal", "coincide"
    elif comparacion.alcance == "simbolica":
        titulo, veredicto = "No es la misma expresión lineal", "distinto"
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
        "alcance": comparacion.alcance,
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
    if paso.tipo == "vector_lineal":
        return f"vector lineal de {paso.filas} componente" + ("" if paso.filas == 1 else "s")
    if paso.tipo == "vector_simbolico":
        return f"vector simbólico de {paso.filas} componente" + ("" if paso.filas == 1 else "s")
    if paso.tipo == "matriz_desconocida":
        return f"matriz desconocida {paso.filas}×{paso.columnas}"
    if paso.tipo == "aplicacion":
        return f"{paso.filas} componentes simbólicos"
    if paso.tipo == "vector":
        return f"{paso.filas} componente" + ("" if paso.filas == 1 else "s")
    return f"{paso.filas}×{paso.columnas}"


def igualdad(paso):
    if paso.tipo == "matriz":
        return f"{paso.texto} ="
    if paso.tipo == "aplicacion":
        return f"{paso.texto} queda por determinar"
    return f"{paso.texto} = {texto_valor(paso)}"


def texto_valor(paso):
    if paso.tipo == "escalar":
        return formatear_exacto(paso.resultado)
    if paso.tipo == "vector_lineal":
        orden = paso.resultado.variables
        return "[" + ", ".join(texto_forma(componente, orden) for componente in paso.resultado.componentes) + "]"
    if paso.tipo == "vector_simbolico":
        return "[" + ", ".join(paso.resultado.variables) + "]"
    if paso.tipo == "matriz_desconocida":
        return f"matriz desconocida {paso.filas}×{paso.columnas}"
    if paso.tipo == "aplicacion":
        return f"{paso.resultado.matriz.nombre}{paso.resultado.vector.nombre}"
    return "[" + ", ".join(formatear_exacto(componente) for componente in paso.resultado) + "]"


def matriz_de(paso):
    if paso.tipo == "matriz":
        return formatear_matriz(paso.resultado)
    if paso.tipo == "vector":
        return formatear_matriz(vector_columna(paso.resultado))
    if paso.tipo == "vector_lineal":
        orden = paso.resultado.variables
        return [[texto_forma(componente, orden)] for componente in paso.resultado.componentes]
    if paso.tipo == "vector_simbolico":
        return [[variable] for variable in paso.resultado.variables]
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
