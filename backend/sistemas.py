"""Interpretacion explicita de una matriz aumentada como sistema de ecuaciones."""

from fractions import Fraction

from backend.expresiones import crear_expresion, formatear_ecuacion
from backend.gauss import aplicar_gauss
from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import formatear_fraccion, validar_matriz_rectangular
from backend.operaciones_filas import texto_factor

SOLUCION_UNICA = "Consistente de solución única"
SOLUCIONES_INFINITAS = "Consistente de soluciones infinitas"
INCONSISTENTE = "Inconsistente"


def contar_variables(matriz_aumentada):
    return len(matriz_aumentada[0]) - 1


def validar_matriz_aumentada(matriz_aumentada):
    """Devuelve (es_valida, mensaje). Hacen falta coeficientes y una columna final."""
    es_valida, mensaje = validar_matriz_rectangular(matriz_aumentada)
    if not es_valida:
        return False, mensaje

    if contar_variables(matriz_aumentada) < 1:
        return False, (
            "Error: Una matriz aumentada necesita al menos una columna de "
            "coeficientes y una de términos independientes."
        )

    return True, ""


def tiene_fila_inconsistente(matriz_resuelta, cantidad_variables):
    # Fila del tipo 0 = k, con k distinto de 0
    for fila in matriz_resuelta:
        coeficientes_en_cero = True
        for columna in range(cantidad_variables):
            if fila[columna] != 0:
                coeficientes_en_cero = False
                break

        if coeficientes_en_cero and fila[cantidad_variables] != 0:
            return True

    return False


def clasificar_sistema(matriz_resuelta, pivotes, cantidad_variables):
    """Sirve igual para una forma escalonada que para una forma reducida."""
    if tiene_fila_inconsistente(matriz_resuelta, cantidad_variables):
        return INCONSISTENTE

    # Sin un pivote por variable quedan variables sin determinar.
    if len(pivotes) < cantidad_variables:
        return SOLUCIONES_INFINITAS

    return SOLUCION_UNICA


def ecuaciones_de_matriz(matriz_aumentada):
    """Traduce cada fila de la matriz aumentada a su ecuacion equivalente.

    Las filas nulas y las contradictorias tambien se traducen, porque son
    parte del sistema resultante: 0 = 0 y 0 = 3 se leen igual que el resto.
    """
    es_valida, mensaje = validar_matriz_aumentada(matriz_aumentada)
    if not es_valida:
        raise ValueError(mensaje)

    cantidad_variables = contar_variables(matriz_aumentada)
    ecuaciones = []

    for fila in matriz_aumentada:
        # Conversión de la fila a ecuación: la última columna es el término
        # independiente y el resto son los coeficientes de x1, x2, ...
        izquierda = crear_expresion(
            0,
            {columna + 1: fila[columna] for columna in range(cantidad_variables)}
        )
        ecuaciones.append(formatear_ecuacion(izquierda, fila[cantidad_variables]))

    return ecuaciones


def obtener_soluciones(matriz_reducida, pivotes, cantidad_variables):
    """Solo tiene sentido cuando cada variable tiene su pivote."""
    soluciones = [Fraction(0) for _ in range(cantidad_variables)]

    for fila, columna in pivotes:
        soluciones[columna] = matriz_reducida[fila][cantidad_variables]

    return soluciones


def texto_sustitucion(fila, columna, cantidad_variables, soluciones):
    """Expresion de la variable en funcion de las que ya se conocen."""
    texto = formatear_fraccion(fila[cantidad_variables])

    for indice in range(columna + 1, cantidad_variables):
        coeficiente = fila[indice]
        if coeficiente == 0:
            continue

        valor = formatear_fraccion(soluciones[indice])
        texto += f" {texto_factor(coeficiente)}({valor})"

    pivote = fila[columna]
    if pivote != 1:
        texto = f"({texto}) / {formatear_fraccion(pivote)}"

    return texto


def sustitucion_regresiva(matriz_escalonada, pivotes, cantidad_variables=None):
    """Despeja las variables de abajo hacia arriba sobre una matriz escalonada.

    Devuelve (soluciones, pasos). Exige un pivote por variable: sin eso el
    sistema no tiene solucion unica y no hay nada que despejar.
    """
    es_valida, mensaje = validar_matriz_aumentada(matriz_escalonada)
    if not es_valida:
        raise ValueError(mensaje)

    if cantidad_variables is None:
        cantidad_variables = contar_variables(matriz_escalonada)

    if len(pivotes) != cantidad_variables:
        raise ValueError(
            "Error: La sustitución regresiva necesita un pivote por cada variable."
        )

    soluciones = [Fraction(0) for _ in range(cantidad_variables)]
    pasos = []

    # Sustitución regresiva: los pivotes se recorren de abajo hacia arriba.
    for fila, columna in reversed(pivotes):
        fila_actual = matriz_escalonada[fila]
        expresion = texto_sustitucion(
            fila_actual, columna, cantidad_variables, soluciones
        )

        acumulado = Fraction(0)
        for indice in range(columna + 1, cantidad_variables):
            acumulado += fila_actual[indice] * soluciones[indice]

        soluciones[columna] = (
            fila_actual[cantidad_variables] - acumulado
        ) / fila_actual[columna]
        pasos.append({
            "variable": columna + 1,
            "expresion": expresion,
            "valor": soluciones[columna]
        })

    return soluciones, pasos


def resolver_sistema_gauss(matriz_aumentada):
    """Escalona el sistema y despeja las variables por sustitucion regresiva.

    Toma la ultima columna como terminos independientes. Devuelve la matriz
    escalonada, los pasos de eliminacion, los pasos de la sustitucion, la
    clasificacion y las soluciones (vacias si no hay solucion unica).
    """
    es_valida, mensaje = validar_matriz_aumentada(matriz_aumentada)
    if not es_valida:
        raise ValueError(mensaje)

    # Los pivotes solo se buscan en las columnas de coeficientes.
    cantidad_variables = contar_variables(matriz_aumentada)
    matriz_escalonada, pasos, pivotes = aplicar_gauss(
        matriz_aumentada, cantidad_variables
    )
    clasificacion = clasificar_sistema(
        matriz_escalonada, pivotes, cantidad_variables
    )

    soluciones = []
    pasos_sustitucion = []
    # Sin solución única no se sustituye: no se inventan valores libres.
    if clasificacion == SOLUCION_UNICA:
        soluciones, pasos_sustitucion = sustitucion_regresiva(
            matriz_escalonada, pivotes, cantidad_variables
        )

    return {
        "matriz_escalonada": matriz_escalonada,
        "pasos": pasos,
        "pasos_sustitucion": pasos_sustitucion,
        "clasificacion": clasificacion,
        "soluciones": soluciones
    }


def resolver_sistema_gauss_jordan(matriz_aumentada):
    """Reduce el sistema y lee las soluciones de la forma reducida.

    Toma la ultima columna como terminos independientes. Devuelve la matriz
    reducida, los pasos, la clasificacion y las soluciones (vacias si no hay
    solucion unica).
    """
    es_valida, mensaje = validar_matriz_aumentada(matriz_aumentada)
    if not es_valida:
        raise ValueError(mensaje)

    # Los pivotes solo se buscan en las columnas de coeficientes.
    cantidad_variables = contar_variables(matriz_aumentada)
    matriz_reducida, pasos, pivotes = aplicar_gauss_jordan(
        matriz_aumentada, cantidad_variables
    )
    clasificacion = clasificar_sistema(matriz_reducida, pivotes, cantidad_variables)

    soluciones = []
    if clasificacion == SOLUCION_UNICA:
        soluciones = obtener_soluciones(matriz_reducida, pivotes, cantidad_variables)

    return {
        "matriz_reducida": matriz_reducida,
        "pasos": pasos,
        "clasificacion": clasificacion,
        "soluciones": soluciones
    }
