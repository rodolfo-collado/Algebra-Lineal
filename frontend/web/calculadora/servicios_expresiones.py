"""Presenta la evaluación de Operaciones con matrices. La aritmética sigue en el backend.

Cada paso del árbol muestra su propio procedimiento: suma, resta, escalar y
traspuesta entrada por entrada; AB y Ax con la lectura elegida (fila por
columna, por columnas o ambas). El último paso no repite su resultado: ese
valor es el resultado de la página y se muestra una sola vez, al final.
"""

from fractions import Fraction

from backend.expresiones_matriciales import Comparacion, Determinacion, Evaluacion, aplanar, evaluar
from backend.expresiones_matriciales.lineal import enumerar, texto_forma
from backend.matrices import vector_columna

from .opciones_matrices import METODO_PREDETERMINADO
from .presentacion_numerica import formatear_exacto
from .servicios import formatear_matriz
from .servicios_matrices import operando, presentar_por_entrada, presentar_producto

_SIGNOS = {"resta_vector": "−", "escalar_vector": "·"}
# Al yuxtaponerlos o nombrarlos dentro de otra operación necesitan paréntesis: (A + B)c₁.
_AGRUPAR = frozenset({"suma", "resta", "negacion"})


def evaluar_expresion_web(entrada):
    metodo = entrada.get("metodo") or METODO_PREDETERMINADO
    resultado = evaluar(entrada["expresion"], entrada["simbolos"], entrada.get("nodo"))
    if isinstance(resultado, Determinacion):
        return presentar_determinacion(resultado)
    if isinstance(resultado, Comparacion):
        return presentar_igualdad(resultado, metodo)
    return presentar(resultado, metodo)


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


def presentar_igualdad(comparacion, metodo=METODO_PREDETERMINADO):
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
        # Cada lado es un árbol propio: sus productos nunca se llaman cᵢⱼ.
        "izquierda": presentar(Evaluacion(comparacion.izquierda), metodo, raiz=False),
        "derecha": presentar(Evaluacion(comparacion.derecha), metodo, raiz=False),
    }


def presentar(evaluacion, metodo=METODO_PREDETERMINADO, raiz=True):
    """Los pasos en el orden en que se calcularon (hijos primero); el último es el resultado."""
    principal = evaluacion.principal
    pasos = [paso for paso in aplanar(principal) if paso.operacion not in ("numero", "simbolo")]
    return {
        "texto": principal.texto,
        "tipo": principal.tipo,
        "parcial": principal.id != "0",
        "dimensiones": dimensiones(principal),
        "igualdad": igualdad(principal),
        "matriz": matriz_de(principal),
        # El último paso es lo que se pidió calcular: no repite su valor ni ofrece recalcularse.
        # En una igualdad, cada lado sí puede pedirse solo.
        "pasos": [
            presentar_paso(paso, metodo, final=paso is principal, simple=raiz and paso is principal,
                           recalcular=not (raiz and paso is principal))
            for paso in pasos
        ],
    }


def presentar_paso(paso, metodo=METODO_PREDETERMINADO, final=False, simple=False, recalcular=True):
    return {
        "id": paso.id,
        "texto": paso.texto,
        "operacion": paso.operacion,
        "dimensiones": dimensiones(paso),
        "igualdad": igualdad(paso),
        "matriz": matriz_de(paso),
        "final": final,
        "recalcular": recalcular,
        "matricial": procedimiento_matricial(paso, metodo, simple),
        "lineas": lineas(paso),
    }


def _operando(paso):
    return operando(paso.texto, paso.resultado, simbolo=paso.operacion == "simbolo", agrupar=paso.operacion in _AGRUPAR)


def procedimiento_matricial(paso, metodo=METODO_PREDETERMINADO, simple=False):
    """El procedimiento de Operaciones con matrices para un paso con matrices; None si no lo tiene.

    `simple` solo vale para dos símbolos operados: es el caso del módulo anterior
    (AB, A + B) y conserva sus nombres cᵢⱼ y sus fórmulas completas.
    """
    detalle = paso.detalle or {}
    operacion = detalle.get("operacion")
    simple = simple and all(hijo.operacion == "simbolo" for hijo in paso.hijos)
    if operacion in ("producto", "matriz_vector"):
        izquierda, derecha = paso.hijos
        return presentar_producto(detalle, metodo, _operando(izquierda), _operando(derecha), paso.texto, simple)
    if operacion in ("suma", "resta"):
        return presentar_por_entrada(detalle, paso.texto, [_operando(hijo) for hijo in paso.hijos], simple=simple)
    if operacion == "traspuesta":
        return presentar_por_entrada(detalle, paso.texto, [_operando(paso.hijos[0])])
    if operacion == "escalar":
        # kA, Ak o -A (la negación multiplica por -1): el factor es el hijo escalar.
        matriz = next(hijo for hijo in paso.hijos if hijo.tipo == "matriz")
        escalar = next((hijo for hijo in paso.hijos if hijo.tipo == "escalar"), None)
        factor = _operando(escalar) if escalar else operando("-1", Fraction(-1), agrupar=True)
        return presentar_por_entrada(detalle, paso.texto, [_operando(matriz)], factor=factor)
    return None


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
    """Vectores y escalar por vector: una línea por componente. Las matrices usan su procedimiento."""
    detalle = paso.detalle or {}
    operacion = detalle.get("operacion")
    if operacion not in ("suma_vector", "resta_vector", "escalar_vector"):
        return []
    signo = _SIGNOS.get(operacion, "+")
    return [linea_operandos(entrada, signo) for entrada in detalle["pasos"]]


def linea_operandos(paso, signo):
    expresion = f" {signo} ".join(operando_texto(valor) for valor in paso["operandos"])
    return f"{expresion} = {formatear_exacto(paso['resultado'])}"


def operando_texto(numero):
    numero = Fraction(numero)
    texto = formatear_exacto(numero)
    return f"({texto})" if numero < 0 or numero.denominator != 1 else texto
