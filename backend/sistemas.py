"""Interpretacion explicita de una matriz aumentada como sistema de ecuaciones."""

from fractions import Fraction

from backend.expresiones import (
    crear_expresion,
    expresion_de_variable,
    formatear_ecuacion,
    formatear_expresion,
    multiplicar_expresion,
    restar_expresiones
)
from backend.gauss import aplicar_gauss
from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import formatear_fraccion, validar_matriz_rectangular
from backend.operaciones_filas import texto_factor

SOLUCION_UNICA = "Consistente de solución única"
SOLUCIONES_INFINITAS = "Consistente de soluciones infinitas"
INCONSISTENTE = "Inconsistente"

SIN_SOLUCION = "No existe solución."


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


def fila_sin_coeficientes(fila, cantidad_variables):
    return all(fila[columna] == 0 for columna in range(cantidad_variables))


def datos_de_fila(fila, indice, cantidad_variables):
    """Conserva la fila exacta y su indice de usuario, que empieza en uno."""
    return {
        "fila": indice + 1,
        "termino_independiente": Fraction(fila[cantidad_variables]),
        "representacion": [Fraction(valor) for valor in fila]
    }


def fila_inconsistente(matriz_resuelta, cantidad_variables):
    """Primera fila del tipo 0 = k, con k distinto de cero."""
    # Búsqueda de filas contradictorias
    for indice, fila in enumerate(matriz_resuelta):
        if (
            fila_sin_coeficientes(fila, cantidad_variables)
            and fila[cantidad_variables] != 0
        ):
            return datos_de_fila(fila, indice, cantidad_variables)

    return None


def tiene_fila_inconsistente(matriz_resuelta, cantidad_variables):
    return fila_inconsistente(matriz_resuelta, cantidad_variables) is not None


def filas_nulas(matriz_resuelta, cantidad_variables):
    """Filas 0 = 0 que evidencian ecuaciones redundantes."""
    # Identificación de filas redundantes
    return [
        datos_de_fila(fila, indice, cantidad_variables)
        for indice, fila in enumerate(matriz_resuelta)
        if (
            fila_sin_coeficientes(fila, cantidad_variables)
            and fila[cantidad_variables] == 0
        )
    ]


def clasificar_sistema(matriz_resuelta, pivotes, cantidad_variables):
    """Sirve igual para una forma escalonada que para una forma reducida."""
    if tiene_fila_inconsistente(matriz_resuelta, cantidad_variables):
        return INCONSISTENTE

    # Sin un pivote por variable quedan variables sin determinar.
    columnas_pivote = {columna for _, columna in pivotes}
    if len(columnas_pivote) < cantidad_variables:
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


def variables_libres(pivotes, cantidad_variables):
    """Las variables cuya columna no llego a tener pivote."""
    # Identificación de columnas pivote: las demás columnas quedan libres.
    columnas_pivote = {columna for _, columna in pivotes}

    return [
        columna + 1
        for columna in range(cantidad_variables)
        if columna not in columnas_pivote
    ]


def permite_lectura_directa(matriz_resuelta, pivotes, cantidad_variables):
    """Indica si cada fila pivote ya tiene la forma directa xN = C."""
    columnas_pivote = {columna for _, columna in pivotes}
    if columnas_pivote != set(range(cantidad_variables)):
        return False

    for indice_fila, columna_pivote in pivotes:
        fila = matriz_resuelta[indice_fila]
        if fila[columna_pivote] != 1:
            return False

        for columna in range(cantidad_variables):
            if columna != columna_pivote and fila[columna] != 0:
                return False

    return True


def formatear_fila_aumentada(fila, cantidad_variables=None):
    """Escribe una fila aumentada como [0 0 | C], con fracciones exactas."""
    if cantidad_variables is None:
        cantidad_variables = len(fila) - 1

    if len(fila) != cantidad_variables + 1:
        raise ValueError("Error: La fila no coincide con la cantidad de variables.")

    coeficientes = " ".join(
        formatear_fraccion(Fraction(fila[columna]))
        for columna in range(cantidad_variables)
    )
    termino = formatear_fraccion(Fraction(fila[cantidad_variables]))
    return f"[{coeficientes} | {termino}]"


def enumerar_variables(indices):
    nombres = [f"x{indice}" for indice in indices]
    if len(nombres) == 1:
        return nombres[0]

    return f"{', '.join(nombres[:-1])} y {nombres[-1]}"


def agregar_parrafo(lineas, texto):
    if lineas:
        lineas.append("")
    lineas.append(texto)


def construir_justificacion(
    clasificacion, contradiccion, redundantes, libres, cantidad_variables
):
    """Construye una explicación breve desde evidencia estructurada."""
    lineas = []

    if clasificacion == INCONSISTENTE:
        fila = contradiccion["fila"]
        representacion = formatear_fila_aumentada(
            contradiccion["representacion"], cantidad_variables
        )
        termino = formatear_fraccion(contradiccion["termino_independiente"])
        agregar_parrafo(
            lineas,
            f"En la fila {fila} se obtiene {representacion}, "
            f"que equivale a 0 = {termino}."
        )
        agregar_parrafo(
            lineas,
            "Como esta igualdad es imposible, el sistema es inconsistente "
            "y no tiene solución."
        )
        return lineas

    if clasificacion != SOLUCIONES_INFINITAS:
        return lineas

    for redundante in redundantes:
        representacion = formatear_fila_aumentada(
            redundante["representacion"], cantidad_variables
        )
        agregar_parrafo(
            lineas,
            f"En la fila {redundante['fila']} se obtiene {representacion}, "
            "por lo que esa ecuación no agrega una nueva condición."
        )

    nombres = enumerar_variables(libres)
    if len(libres) == 1:
        texto_libres = (
            f"La variable {nombres} no tiene pivote, por lo que es libre."
        )
    else:
        texto_libres = (
            f"Las variables {nombres} no tienen pivote, por lo que son libres."
        )
    agregar_parrafo(lineas, texto_libres)

    return lineas


def solucion_general(matriz_resuelta, pivotes, cantidad_variables):
    """Expresa cada variable pivote en funcion unicamente de las libres.

    Devuelve una expresion lineal por variable, de x1 a xn, en ese orden. Cada
    variable libre queda representada por si misma. Sirve igual para una forma
    escalonada que para una forma reducida.
    """
    expresiones = {
        variable: expresion_de_variable(variable)
        for variable in range(1, cantidad_variables + 1)
    }

    # Sustitución regresiva simbólica: los pivotes se recorren de abajo hacia
    # arriba, así que al despejar uno los de su derecha ya están despejados.
    for fila, columna in reversed(pivotes):
        valores = matriz_resuelta[fila]
        despejada = crear_expresion(valores[cantidad_variables])

        # Sustitución de las variables ya despejadas.
        for siguiente in range(columna + 1, cantidad_variables):
            coeficiente = valores[siguiente]
            if coeficiente == 0:
                continue

            despejada = restar_expresiones(
                despejada,
                multiplicar_expresion(expresiones[siguiente + 1], coeficiente)
            )

        expresiones[columna + 1] = multiplicar_expresion(
            despejada, Fraction(1, 1) / valores[columna]
        )

    return [expresiones[variable] for variable in range(1, cantidad_variables + 1)]


def formatear_solucion_general(expresiones, libres):
    """Una linea por variable, en orden, marcando cuales quedaron libres."""
    sin_pivote = set(libres)
    lineas = []

    for variable, expresion in enumerate(expresiones, start=1):
        if variable in sin_pivote:
            lineas.append(f"x{variable} es libre")
        else:
            lineas.append(f"x{variable} = {formatear_expresion(expresion)}")

    return lineas


def interpretar_resultado(matriz_resuelta, pivotes, cantidad_variables):
    """Lee una matriz ya resuelta: ecuaciones, clasificacion y solucion.

    La comparten Gauss y Gauss-Jordan. Cada uno le pasa su propia matriz, de
    modo que el sistema resultante puede diferir aunque la solucion coincida.
    """
    clasificacion = clasificar_sistema(
        matriz_resuelta, pivotes, cantidad_variables
    )
    ecuaciones = ecuaciones_de_matriz(matriz_resuelta)
    contradiccion = fila_inconsistente(matriz_resuelta, cantidad_variables)
    redundantes = filas_nulas(matriz_resuelta, cantidad_variables)

    # Una contradicción anula el conjunto solución aunque falten pivotes: sin
    # solución no hay nada que declarar libre.
    if clasificacion == INCONSISTENTE:
        return {
            "clasificacion": clasificacion,
            "ecuaciones_resultantes": ecuaciones,
            "solucion_general": [],
            "soluciones": [],
            "fila_inconsistente": contradiccion,
            "filas_nulas": redundantes,
            "variables_libres": [],
            "solucion_directa": False,
            "justificacion": construir_justificacion(
                clasificacion, contradiccion, redundantes, [], cantidad_variables
            )
        }

    expresiones = solucion_general(matriz_resuelta, pivotes, cantidad_variables)
    libres = variables_libres(pivotes, cantidad_variables)

    # Sin variables libres cada expresión ya es su valor constante.
    soluciones = []
    if clasificacion == SOLUCION_UNICA:
        soluciones = [expresion["constante"] for expresion in expresiones]

    return {
        "clasificacion": clasificacion,
        "ecuaciones_resultantes": ecuaciones,
        "solucion_general": formatear_solucion_general(expresiones, libres),
        "soluciones": soluciones,
        "fila_inconsistente": None,
        "filas_nulas": redundantes,
        "variables_libres": libres,
        "solucion_directa": (
            clasificacion == SOLUCION_UNICA
            and permite_lectura_directa(
                matriz_resuelta, pivotes, cantidad_variables
            )
        ),
        "justificacion": construir_justificacion(
            clasificacion, None, redundantes, libres, cantidad_variables
        )
    }


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
    escalonada, los pasos de eliminacion, los pasos de la sustitucion y la
    interpretacion del resultado.
    """
    es_valida, mensaje = validar_matriz_aumentada(matriz_aumentada)
    if not es_valida:
        raise ValueError(mensaje)

    # Los pivotes solo se buscan en las columnas de coeficientes.
    cantidad_variables = contar_variables(matriz_aumentada)
    matriz_escalonada, pasos, pivotes = aplicar_gauss(
        matriz_aumentada, cantidad_variables
    )
    interpretacion = interpretar_resultado(
        matriz_escalonada, pivotes, cantidad_variables
    )

    # La sustitución numérica paso a paso solo se muestra con solución única;
    # el conjunto solución sale siempre del mismo modelo general.
    pasos_sustitucion = []
    if interpretacion["clasificacion"] == SOLUCION_UNICA:
        _, pasos_sustitucion = sustitucion_regresiva(
            matriz_escalonada, pivotes, cantidad_variables
        )

    return {
        "matriz_escalonada": matriz_escalonada,
        "pasos": pasos,
        "pasos_sustitucion": pasos_sustitucion,
        **interpretacion
    }


def resolver_sistema_gauss_jordan(matriz_aumentada):
    """Reduce el sistema y lee el resultado de la forma reducida.

    Toma la ultima columna como terminos independientes. Devuelve la matriz
    reducida, los pasos y la interpretacion del resultado.
    """
    es_valida, mensaje = validar_matriz_aumentada(matriz_aumentada)
    if not es_valida:
        raise ValueError(mensaje)

    # Los pivotes solo se buscan en las columnas de coeficientes.
    cantidad_variables = contar_variables(matriz_aumentada)
    matriz_reducida, pasos, pivotes = aplicar_gauss_jordan(
        matriz_aumentada, cantidad_variables
    )

    return {
        "matriz_reducida": matriz_reducida,
        "pasos": pasos,
        **interpretar_resultado(matriz_reducida, pivotes, cantidad_variables)
    }
