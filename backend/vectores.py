"""Operaciones con vectores de dimension arbitraria y combinacion lineal.

Un vector es una lista de numeros exactos (enteros o `Fraction`); su dimension
`n` es la cantidad de componentes y no se fija de antemano: (1, 2), (1, 2, 3)
o (1, 2, 3, 4, 5) se tratan igual. Este modulo es logica pura: recibe listas
y devuelve listas o diccionarios, o lanza ValueError con un mensaje legible.
No imprime ni conoce ninguna interfaz.

La combinacion lineal no repite ninguna eliminacion: se plantea como sistema
y se resuelve con el Gauss-Jordan del proyecto.
"""

from fractions import Fraction
from backend.operandos import ARIDAD_VECTORES, exigir_aridad

# La validación de un vector vive junto al producto punto, en backend.matrices,
# porque las filas y columnas de una matriz también son vectores.
from backend.matrices import validar_vector
from backend.sistemas import (
    INCONSISTENTE,
    SOLUCION_UNICA,
    ecuaciones_de_matriz,
    resolver_sistema_gauss_jordan,
)

# Los escalares buscados en una combinacion lineal se llaman c1, c2, ..., ck.
NOMBRE_COEFICIENTE = "c"


def dimension(vector):
    return len(vector)


def validar_misma_dimension(vectores, nombres, accion="operar"):
    """Devuelve (es_valida, mensaje) comprobando que todos tengan igual dimension."""
    for vector, nombre in zip(vectores, nombres):
        es_valido, mensaje = validar_vector(vector, nombre)
        if not es_valido:
            return False, mensaje

    dimensiones = {dimension(vector) for vector in vectores}
    if len(dimensiones) > 1:
        detalle = ", ".join(
            f"{nombre} tiene {dimension(vector)}"
            for vector, nombre in zip(vectores, nombres)
        )
        return False, (
            f"No se pueden {accion} vectores de distinta dimensión: {detalle} componentes."
        )

    return True, ""


def _exigir(es_valido, mensaje):
    if not es_valido:
        raise ValueError(mensaje)


def convertir_vector_a_fracciones(vector):
    return [Fraction(componente) for componente in vector]


def operar_vectores(operacion, vectores):
    """Suma o resta una colección, de izquierda a derecha, sin mutarla."""
    if operacion not in ("suma", "resta"):
        raise ValueError("Selecciona suma o resta de vectores.")
    vectores = list(vectores)
    exigir_aridad(len(vectores), ARIDAD_VECTORES[operacion])
    nombres = ["u", "v"] if len(vectores) == 2 else nombres_generadores(len(vectores))
    _exigir(*validar_misma_dimension(vectores, nombres, "sumar" if operacion == "suma" else "restar"))
    resultado = convertir_vector_a_fracciones(vectores[0])
    signo = 1 if operacion == "suma" else -1
    for vector in vectores[1:]:
        resultado = [a + signo * Fraction(b) for a, b in zip(resultado, vector)]
    return resultado


def sumar_vectores(u, v):
    """Suma componente a componente: (u1 + v1, u2 + v2, ..., un + vn).

    Los dos vectores deben tener la misma dimension. El resultado conserva la
    aritmetica exacta: (1/2, 2/3) + (1/2, 1/3) = (1, 1).
    """
    return operar_vectores("suma", [u, v])


def restar_vectores(u, v):
    """Resta componente a componente: u - v = (u1 - v1, u2 - v2, ..., un - vn)."""
    return operar_vectores("resta", [u, v])


def multiplicar_escalar(escalar, v):
    """Multiplica cada componente por el escalar: k(v1, ..., vn) = (k·v1, ..., k·vn)."""
    _exigir(*validar_vector(v))
    if isinstance(escalar, bool) or not isinstance(escalar, (int, Fraction)):
        raise ValueError("El escalar debe ser un número.")

    factor = Fraction(escalar)
    resultado = []
    for componente in v:
        resultado.append(factor * Fraction(componente))

    return resultado


def combinar(coeficientes, generadores):
    """Evalua c1·v1 + c2·v2 + ... + ck·vk con las operaciones de este modulo.

    Sirve para comprobar una combinacion ya calculada: el resultado debe
    coincidir con el vector objetivo.
    """
    if len(coeficientes) != len(generadores):
        raise ValueError("Hace falta un coeficiente por cada vector.")
    if not generadores:
        raise ValueError("Hace falta al menos un vector para combinar.")

    acumulado = multiplicar_escalar(coeficientes[0], generadores[0])
    for coeficiente, vector in zip(coeficientes[1:], generadores[1:]):
        acumulado = sumar_vectores(acumulado, multiplicar_escalar(coeficiente, vector))

    return acumulado


def nombres_generadores(cantidad):
    return [f"v{indice}" for indice in range(1, cantidad + 1)]


def validar_combinacion(generadores, objetivo):
    """Devuelve (es_valida, mensaje) para plantear c1·v1 + ... + ck·vk = b."""
    if not generadores:
        return False, "Hace falta al menos un vector generador para plantear la combinación."

    nombres = nombres_generadores(len(generadores))
    return validar_misma_dimension(
        (*generadores, objetivo), (*nombres, "b"), "combinar"
    )


def matriz_de_combinacion(generadores, objetivo):
    """Escribe c1·v1 + ... + ck·vk = b como la matriz aumentada [v1 v2 ... vk | b].

    La igualdad vectorial es un sistema con una ecuacion por componente: la
    fila i es v1[i]·c1 + v2[i]·c2 + ... + vk[i]·ck = b[i]. Por eso cada vector
    generador ocupa una columna y el objetivo, la columna aumentada.
    """
    _exigir(*validar_combinacion(generadores, objetivo))

    matriz = []
    for indice in range(dimension(objetivo)):
        fila = [Fraction(vector[indice]) for vector in generadores]
        fila.append(Fraction(objetivo[indice]))
        matriz.append(fila)

    return matriz


def evaluar_combinacion_lineal(generadores, objetivo):
    """Decide si `objetivo` es combinacion lineal de `generadores` y con que coeficientes.

    Plantea el sistema [v1 ... vk | b] y lo resuelve con Gauss-Jordan
    (`backend.sistemas`), sin repetir la eliminacion. La clasificacion del
    sistema decide la respuesta:

    - solucion unica: hay exactamente una combinacion y se devuelven sus
      coeficientes;
    - soluciones infinitas: el vector si pertenece al conjunto generado, con
      infinitas combinaciones; se devuelve la solucion general y una
      combinacion concreta (coeficientes libres en cero);
    - inconsistente: no existe ninguna combinacion.
    """
    matriz_aumentada = matriz_de_combinacion(generadores, objetivo)
    cantidad_vectores = len(generadores)
    resultado = resolver_sistema_gauss_jordan(matriz_aumentada, NOMBRE_COEFICIENTE)
    clasificacion = resultado["clasificacion"]

    coeficientes = None
    coeficientes_particulares = None
    verificacion = None
    if clasificacion == SOLUCION_UNICA:
        coeficientes = list(resultado["soluciones"])
        verificacion = combinar(coeficientes, generadores)
    elif clasificacion != INCONSISTENTE:
        # Con los coeficientes libres en cero, la constante de cada expresión
        # es una combinación concreta entre las infinitas posibles.
        coeficientes_particulares = [
            expresion["constante"] for expresion in resultado["expresiones_solucion"]
        ]
        verificacion = combinar(coeficientes_particulares, generadores)

    return {
        "cantidad_vectores": cantidad_vectores,
        "dimension": dimension(objetivo),
        "nombres": nombres_generadores(cantidad_vectores),
        "matriz_aumentada": matriz_aumentada,
        "ecuaciones": ecuaciones_de_matriz(matriz_aumentada, NOMBRE_COEFICIENTE),
        "matriz_reducida": resultado["matriz_reducida"],
        "pasos": resultado["pasos"],
        "columnas_pivote": resultado["columnas_pivote"],
        "clasificacion": clasificacion,
        "es_combinacion": clasificacion != INCONSISTENTE,
        "justificacion": resultado["justificacion"],
        "solucion_general": resultado["solucion_general"],
        "variables_libres": resultado["variables_libres"],
        "coeficientes": coeficientes,
        "coeficientes_particulares": coeficientes_particulares,
        "verificacion": verificacion,
    }
