"""Presentación de x1 u + … + xk w = b en Operaciones: ¿es b combinación lineal y con qué coeficientes?

No calcula nada: llama a `backend.vectores` y convierte los valores exactos en textos
listos para la plantilla (vectores como «(1, 2, 3)», el planteamiento, el sistema
equivalente y la conclusión en el lenguaje del ejercicio). Sumas, restas y escalares
con vectores los evalúa el motor de expresiones, como cualquier otra operación.
"""

from fractions import Fraction

from .presentacion_numerica import formatear_exacto
from backend.vectores import NOMBRE_COEFICIENTE, evaluar_combinacion_lineal

from .servicios import adaptar_pasos, clave_clasificacion, formatear_matriz

TITULO_COMBINACION = "Combinación lineal"


def numero(valor):
    return formatear_exacto(Fraction(valor))


def componentes(vector):
    return [numero(valor) for valor in vector]


def texto_vector(vector):
    """(1, 2, 3): la escritura horizontal, que sirve igual en HTML y en texto."""
    return f"({', '.join(componentes(vector))})"


def _entrada(nombre, vector):
    return {"nombre": nombre, "componentes": componentes(vector), "texto": texto_vector(vector)}


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


def planteamiento(generadores, objetivo):
    """x1(1, 0) + x2(0, 1) = (3, 4)."""
    terminos = " + ".join(
        f"{NOMBRE_COEFICIENTE}{indice}{texto_vector(vector)}"
        for indice, vector in enumerate(generadores, start=1)
    )
    return f"{terminos} = {texto_vector(objetivo)}"


def enumerar(nombres):
    if len(nombres) == 1:
        return nombres[0]
    return f"{', '.join(nombres[:-1])} y {nombres[-1]}"


def presentar_combinacion(plan):
    """x1 u + … + xk w = b (de `backend.expresiones_matriciales.combinacion.plantear`) lista para la plantilla."""
    nombres = [nombre for nombre, _ in plan["generadores"]]
    generadores = [valor for _, valor in plan["generadores"]]
    nombre_objetivo, objetivo = plan["objetivo"]
    evaluacion = evaluar_combinacion_lineal(generadores, objetivo)

    incognitas = plan["incognitas"]
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
        conclusion = f"Sí: {nombre_objetivo} es combinación lineal de {lista_nombres}."
        detalle = "Existe una única combinación."
    elif clave == "infinitas":
        conclusion = f"Sí: {nombre_objetivo} es combinación lineal de {lista_nombres}."
        detalle = "Existen infinitas combinaciones posibles."
    else:
        conclusion = f"No: {nombre_objetivo} no es combinación lineal de {lista_nombres}."
        detalle = "El sistema asociado no tiene solución."

    libres = [f"{NOMBRE_COEFICIENTE}{indice}" for indice in evaluacion["variables_libres"]]
    ejemplo = None
    if clave == "infinitas" and libres:
        ceros = " = ".join(libres)
        ejemplo = f"Por ejemplo, con {ceros} = 0:"

    return {
        "modo": "combinacion",
        "operacion": "combinacion",
        "texto": plan["texto"],
        "titulo": TITULO_COMBINACION,
        "dimension": len(objetivo),
        "generadores": [_entrada(nombre, vector) for nombre, vector in zip(nombres, generadores)],
        "objetivo": _entrada(nombre_objetivo, objetivo),
        "nombres_generadores": lista_nombres,
        "incognitas": enumerar(incognitas),
        "planteamiento": planteamiento(generadores, objetivo),
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
