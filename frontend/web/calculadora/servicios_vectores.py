"""Presentación de las operaciones con vectores para la interfaz web.

No calcula nada: llama a `backend.vectores` y convierte los valores exactos
en textos listos para la plantilla (vectores como «(1, 2, 3)», el desarrollo
componente a componente y, en la combinación lineal, el planteamiento, el
sistema equivalente y la conclusión en el lenguaje del ejercicio).
"""

from fractions import Fraction

from .presentacion_numerica import formatear_exacto
from backend.vectores import (
    NOMBRE_COEFICIENTE,
    evaluar_combinacion_lineal,
    multiplicar_escalar,
    restar_vectores,
    sumar_vectores,
)

from .opciones_vectores import NOMBRE_ESCALAR, NOMBRE_OBJETIVO, etiqueta_operacion
from .servicios import adaptar_pasos, clave_clasificacion, formatear_matriz

TITULOS = {
    "suma": "Suma de vectores",
    "resta": "Resta de vectores",
    "escalar": "Multiplicación de un vector por un escalar",
    "combinacion": "Combinación lineal",
}


def numero(valor):
    return formatear_exacto(Fraction(valor))


def componentes(vector):
    return [numero(valor) for valor in vector]


def texto_vector(vector):
    """(1, 2, 3): la escritura horizontal, que sirve igual en HTML y en texto."""
    return f"({', '.join(componentes(vector))})"


def _con_parentesis(valor, tambien_fracciones=False):
    """Un operando negativo (o fraccionario, si se pide) se encierra para no confundir signos."""
    fraccion = Fraction(valor)
    texto = formatear_exacto(fraccion)
    if fraccion < 0 or (tambien_fracciones and fraccion.denominator != 1):
        return f"({texto})"
    return texto


def desarrollo_suma(u, v):
    return [f"{numero(a)} + {_con_parentesis(b)}" for a, b in zip(u, v)]


def desarrollo_resta(u, v):
    return [f"{numero(a)} - {_con_parentesis(b)}" for a, b in zip(u, v)]


def desarrollo_escalar(escalar, u):
    factor = _con_parentesis(escalar, tambien_fracciones=True)
    return [f"{factor}·{_con_parentesis(a, tambien_fracciones=True)}" for a in u]


def _entrada(nombre, vector):
    return {"nombre": nombre, "componentes": componentes(vector), "texto": texto_vector(vector)}


def _operacion_componente_a_componente(entrada):
    operacion = entrada["operacion"]
    vectores = entrada["vectores"]

    if operacion == "escalar":
        u = vectores["u"]
        escalar = entrada["escalar"]
        resultado = multiplicar_escalar(escalar, u)
        desarrollo = desarrollo_escalar(escalar, u)
        expresion = f"{NOMBRE_ESCALAR}·u"
        sustitucion = f"{_con_parentesis(escalar, tambien_fracciones=True)}·{texto_vector(u)}"
    else:
        u, v = vectores["u"], vectores["v"]
        if operacion == "suma":
            resultado = sumar_vectores(u, v)
            desarrollo = desarrollo_suma(u, v)
            expresion = "u + v"
        else:
            resultado = restar_vectores(u, v)
            desarrollo = desarrollo_resta(u, v)
            expresion = "u − v"
        sustitucion = f"{texto_vector(u)} {expresion[2]} {texto_vector(v)}"

    return {
        "operacion": operacion,
        "etiqueta": etiqueta_operacion(operacion),
        "titulo": TITULOS[operacion],
        "dimension": entrada["dimension"],
        "expresion": expresion,
        # «u + v = (1, 2, 3) + (4, 5, 6) = (1 + 4, 2 + 5, 3 + 6) = (5, 7, 9)», una igualdad por línea.
        "sustitucion": sustitucion,
        "desarrollo": f"({', '.join(desarrollo)})",
        "resultado": componentes(resultado),
        "resultado_texto": texto_vector(resultado),
    }


def termino_combinacion(coeficiente, vector_texto, primero):
    """Escribe c·v dentro de una suma: 3(1, 0), - 2(0, 1), + 1/2(1, 1)."""
    fraccion = Fraction(coeficiente)
    magnitud = formatear_exacto(abs(fraccion))
    factor = "" if magnitud == "1" else magnitud
    if primero:
        signo = "-" if fraccion < 0 else ""
        return f"{signo}{factor}{vector_texto}"
    signo = "-" if fraccion < 0 else "+"
    return f" {signo} {factor}{vector_texto}"


def igualdad_combinacion(coeficientes, generadores, objetivo):
    """(3, 4) = 3(1, 0) + 4(0, 1): el objetivo escrito como la combinación hallada."""
    terminos = "".join(
        termino_combinacion(coeficiente, texto_vector(vector), indice == 0)
        for indice, (coeficiente, vector) in enumerate(zip(coeficientes, generadores))
    )
    return f"{texto_vector(objetivo)} = {terminos}"


def planteamiento(nombres, generadores, objetivo):
    """c1(1, 0) + c2(0, 1) = (3, 4)."""
    terminos = " + ".join(
        f"{NOMBRE_COEFICIENTE}{indice}{texto_vector(vector)}"
        for indice, vector in enumerate(generadores, start=1)
    )
    return f"{terminos} = {texto_vector(objetivo)}"


def enumerar(nombres):
    if len(nombres) == 1:
        return nombres[0]
    return f"{', '.join(nombres[:-1])} y {nombres[-1]}"


def _combinacion_lineal(entrada):
    nombres = [nombre for nombre in entrada["nombres"] if nombre != NOMBRE_OBJETIVO]
    generadores = [entrada["vectores"][nombre] for nombre in nombres]
    objetivo = entrada["vectores"][NOMBRE_OBJETIVO]
    evaluacion = evaluar_combinacion_lineal(generadores, objetivo)

    incognitas = [f"{NOMBRE_COEFICIENTE}{indice}" for indice in range(1, len(nombres) + 1)]
    clave = clave_clasificacion(evaluacion["clasificacion"])
    lista_nombres = enumerar(nombres)

    coeficientes = None
    igualdad = None
    if evaluacion["coeficientes"] is not None:
        coeficientes = [
            (incognita, numero(valor))
            for incognita, valor in zip(incognitas, evaluacion["coeficientes"])
        ]
        igualdad = igualdad_combinacion(evaluacion["coeficientes"], generadores, objetivo)
    elif evaluacion["coeficientes_particulares"] is not None:
        igualdad = igualdad_combinacion(
            evaluacion["coeficientes_particulares"], generadores, objetivo
        )

    if clave == "unica":
        conclusion = f"Sí: {NOMBRE_OBJETIVO} es combinación lineal de {lista_nombres}."
        detalle = "Existe una única combinación."
    elif clave == "infinitas":
        conclusion = f"Sí: {NOMBRE_OBJETIVO} es combinación lineal de {lista_nombres}."
        detalle = "Existen infinitas combinaciones posibles."
    else:
        conclusion = f"No: {NOMBRE_OBJETIVO} no es combinación lineal de {lista_nombres}."
        detalle = "El sistema asociado no tiene solución."

    libres = [f"{NOMBRE_COEFICIENTE}{indice}" for indice in evaluacion["variables_libres"]]
    ejemplo = None
    if clave == "infinitas" and libres:
        ceros = " = ".join(libres)
        ejemplo = f"Por ejemplo, con {ceros} = 0:"

    return {
        "operacion": "combinacion",
        "etiqueta": etiqueta_operacion("combinacion"),
        "titulo": TITULOS["combinacion"],
        "dimension": entrada["dimension"],
        "generadores": [_entrada(nombre, vector) for nombre, vector in zip(nombres, generadores)],
        "objetivo": _entrada(NOMBRE_OBJETIVO, objetivo),
        "nombres_generadores": lista_nombres,
        "incognitas": enumerar(incognitas),
        "planteamiento": planteamiento(nombres, generadores, objetivo),
        "ecuaciones": evaluacion["ecuaciones"],
        "matriz_aumentada": formatear_matriz(evaluacion["matriz_aumentada"]),
        "pasos": adaptar_pasos(evaluacion["pasos"]),
        "matriz_reducida": formatear_matriz(evaluacion["matriz_reducida"]),
        "columnas_pivote": evaluacion["columnas_pivote"],
        "clasificacion": evaluacion["clasificacion"],
        "clasificacion_clave": clave,
        "es_combinacion": evaluacion["es_combinacion"],
        "conclusion": conclusion,
        "detalle": detalle,
        "justificacion": evaluacion["justificacion"],
        "solucion_general": evaluacion["solucion_general"],
        "coeficientes": coeficientes,
        "ejemplo": ejemplo,
        "igualdad": igualdad,
    }


def operar_vectores(entrada):
    """Resuelve la entrada ya validada por el formulario y la deja lista para la plantilla."""
    if entrada["operacion"] == "combinacion":
        return _combinacion_lineal(entrada)
    return _operacion_componente_a_componente(entrada)
