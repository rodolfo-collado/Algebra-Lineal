import random
from fractions import Fraction


def generar_matriz(filas, columnas):
    matriz = []

    for _ in range(filas):
        fila = []
        for _ in range(columnas):
            fila.append(random.randint(0, 20))
        matriz.append(fila)

    return matriz


def copiar_matriz(matriz):
    return [fila.copy() for fila in matriz]


def es_matriz_rectangular(matriz):
    if not matriz or not matriz[0]:
        return False

    cantidad_columnas = len(matriz[0])
    return all(len(fila) == cantidad_columnas for fila in matriz)


def validar_matriz(matriz):
    if not matriz:
        return False, "Error: La matriz no puede estar vacía."

    if not es_matriz_rectangular(matriz):
        return False, "Error: La matriz debe ser rectangular."

    return True, ""


def validar_matriz_sistema(matriz):
    es_valida, mensaje = validar_matriz(matriz)
    if not es_valida:
        return es_valida, mensaje

    if len(matriz[0]) < 2:
        return False, (
            "Error: Un sistema debe tener al menos una incógnita y "
            "un término independiente."
        )

    return True, ""


def validar_dimensiones_gauss_jordan(matriz):
    """Valida únicamente la estructura, sin restringir las dimensiones."""
    return validar_matriz(matriz)


def convertir_matriz_a_fracciones(matriz):
    return [
        [Fraction(numero) for numero in fila]
        for fila in matriz
    ]


def buscar_fila_pivote(matriz, fila_inicio, columna):
    for fila in range(fila_inicio, len(matriz)):
        if matriz[fila][columna] != 0:
            return fila

    return None


def registrar_paso(pasos, matriz_antes, operacion, matriz_despues):
    pasos.append({
        "antes": copiar_matriz(matriz_antes),
        "operacion": operacion,
        "despues": copiar_matriz(matriz_despues)
    })


def formatear_numero_operacion(numero):
    numero = Fraction(numero)
    if numero.denominator == 1:
        return str(numero.numerator)

    return f"{numero.numerator}/{numero.denominator}"


def texto_factor(factor):
    if factor < 0:
        return f"+ ({formatear_numero_operacion(-factor)})"

    return f"- ({formatear_numero_operacion(factor)})"


def _validar_matriz_para_operar(matriz, es_sistema):
    if es_sistema:
        es_valida, mensaje = validar_matriz_sistema(matriz)
    else:
        es_valida, mensaje = validar_matriz(matriz)

    if not es_valida:
        raise ValueError(mensaje)


def aplicar_gauss(matriz, es_sistema=False):
    """Devuelve la forma escalonada, los pasos y las posiciones de pivote.

    Una matriz general puede usar todas sus columnas como columnas de pivote.
    Cuando ``es_sistema`` es verdadero, la última columna se trata como el
    término independiente y no se usa para buscar pivotes.
    """
    _validar_matriz_para_operar(matriz, es_sistema)

    matriz_escalonada = convertir_matriz_a_fracciones(matriz)
    pasos = []
    cantidad_filas = len(matriz_escalonada)
    cantidad_columnas = len(matriz_escalonada[0])
    limite_columnas_pivote = (
        cantidad_columnas - 1 if es_sistema else cantidad_columnas
    )
    fila_pivote = 0
    pivotes = []

    for columna in range(limite_columnas_pivote):
        if fila_pivote >= cantidad_filas:
            break

        fila_encontrada = buscar_fila_pivote(
            matriz_escalonada,
            fila_pivote,
            columna
        )
        if fila_encontrada is None:
            continue

        if fila_encontrada != fila_pivote:
            matriz_antes = copiar_matriz(matriz_escalonada)
            matriz_escalonada[fila_pivote], matriz_escalonada[fila_encontrada] = (
                matriz_escalonada[fila_encontrada],
                matriz_escalonada[fila_pivote]
            )
            operacion = f"F{fila_pivote + 1} <-> F{fila_encontrada + 1}"
            registrar_paso(
                pasos,
                matriz_antes,
                operacion,
                matriz_escalonada
            )

        pivote = matriz_escalonada[fila_pivote][columna]
        if pivote != 1:
            matriz_antes = copiar_matriz(matriz_escalonada)
            matriz_escalonada[fila_pivote] = [
                numero / pivote
                for numero in matriz_escalonada[fila_pivote]
            ]
            factor_pivote = formatear_numero_operacion(Fraction(1, 1) / pivote)
            operacion = (
                f"F{fila_pivote + 1} = ({factor_pivote})"
                f"F{fila_pivote + 1}"
            )
            registrar_paso(
                pasos,
                matriz_antes,
                operacion,
                matriz_escalonada
            )

        for fila in range(fila_pivote + 1, cantidad_filas):
            factor = matriz_escalonada[fila][columna]
            if factor == 0:
                continue

            matriz_antes = copiar_matriz(matriz_escalonada)
            matriz_escalonada[fila] = [
                matriz_escalonada[fila][columna_actual]
                - factor * matriz_escalonada[fila_pivote][columna_actual]
                for columna_actual in range(cantidad_columnas)
            ]
            operacion = (
                f"F{fila + 1} = F{fila + 1} "
                f"{texto_factor(factor)}F{fila_pivote + 1}"
            )
            registrar_paso(
                pasos,
                matriz_antes,
                operacion,
                matriz_escalonada
            )

        pivotes.append((fila_pivote, columna))
        fila_pivote += 1

    return matriz_escalonada, pasos, pivotes


def aplicar_gauss_jordan(matriz, es_sistema=False):
    """Aplica Gauss y después elimina los valores sobre cada pivote."""
    matriz_reducida, pasos, pivotes = aplicar_gauss(
        matriz,
        es_sistema=es_sistema
    )
    cantidad_columnas = len(matriz_reducida[0])

    for fila_pivote, columna in reversed(pivotes):
        for fila in range(fila_pivote - 1, -1, -1):
            factor = matriz_reducida[fila][columna]
            if factor == 0:
                continue

            matriz_antes = copiar_matriz(matriz_reducida)
            matriz_reducida[fila] = [
                matriz_reducida[fila][columna_actual]
                - factor * matriz_reducida[fila_pivote][columna_actual]
                for columna_actual in range(cantidad_columnas)
            ]
            operacion = (
                f"F{fila + 1} = F{fila + 1} "
                f"{texto_factor(factor)}F{fila_pivote + 1}"
            )
            registrar_paso(
                pasos,
                matriz_antes,
                operacion,
                matriz_reducida
            )

    return matriz_reducida, pasos, pivotes


def obtener_rango(matriz, columnas_limite=None):
    """Calcula el rango usando las primeras ``columnas_limite`` columnas."""
    es_valida, mensaje = validar_matriz(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    matriz_trabajo = convertir_matriz_a_fracciones(matriz)
    cantidad_filas = len(matriz_trabajo)
    cantidad_columnas = len(matriz_trabajo[0])

    if columnas_limite is None:
        columnas_limite = cantidad_columnas
    if columnas_limite < 0 or columnas_limite > cantidad_columnas:
        raise ValueError("El límite de columnas no es válido.")

    fila_pivote = 0
    rango = 0

    for columna in range(columnas_limite):
        if fila_pivote >= cantidad_filas:
            break

        fila_encontrada = buscar_fila_pivote(
            matriz_trabajo,
            fila_pivote,
            columna
        )
        if fila_encontrada is None:
            continue

        matriz_trabajo[fila_pivote], matriz_trabajo[fila_encontrada] = (
            matriz_trabajo[fila_encontrada],
            matriz_trabajo[fila_pivote]
        )
        pivote = matriz_trabajo[fila_pivote][columna]

        for fila in range(fila_pivote + 1, cantidad_filas):
            factor = matriz_trabajo[fila][columna] / pivote
            if factor == 0:
                continue

            matriz_trabajo[fila] = [
                matriz_trabajo[fila][columna_actual]
                - factor * matriz_trabajo[fila_pivote][columna_actual]
                for columna_actual in range(cantidad_columnas)
            ]

        rango += 1
        fila_pivote += 1

    return rango


def fila_contradictoria(fila, cantidad_incognitas):
    coeficientes_cero = all(
        fila[columna] == 0
        for columna in range(cantidad_incognitas)
    )
    return coeficientes_cero and fila[cantidad_incognitas] != 0


def obtener_tipo_sistema(matriz):
    """Clasifica un sistema usando los rangos de A y de la matriz aumentada."""
    es_valida, mensaje = validar_matriz_sistema(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    cantidad_incognitas = len(matriz[0]) - 1
    rango_coeficientes = obtener_rango(matriz, cantidad_incognitas)
    rango_aumentada = obtener_rango(matriz)

    if rango_coeficientes != rango_aumentada:
        return "incompatible"

    if rango_coeficientes == cantidad_incognitas:
        return "compatible determinado"

    return "compatible indeterminado"


def analizar_sistema(matriz):
    es_valida, mensaje = validar_matriz_sistema(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    cantidad_incognitas = len(matriz[0]) - 1
    rango_coeficientes = obtener_rango(matriz, cantidad_incognitas)
    rango_aumentada = obtener_rango(matriz)
    tipo_sistema = obtener_tipo_sistema(matriz)

    resultado = [
        f"Rango de la matriz de coeficientes: {rango_coeficientes}.",
        f"Rango de la matriz aumentada: {rango_aumentada}."
    ]

    if tipo_sistema == "incompatible":
        resultado.extend([
            "Sistema incompatible.",
            "Apareció una fila del tipo 0 = k, con k distinto de 0.",
            "No tiene solución."
        ])
    elif tipo_sistema == "compatible determinado":
        resultado.extend([
            "Sistema compatible determinado.",
            "Tiene exactamente una solución."
        ])
    else:
        resultado.extend([
            "Sistema compatible indeterminado.",
            "Tiene infinitas soluciones porque hay menos pivotes que incógnitas."
        ])

    return resultado


def formatear_expresion_sustitucion(fila, columna, soluciones, cantidad_incognitas):
    expresion = formatear_numero_operacion(fila[cantidad_incognitas])

    for indice in range(columna + 1, cantidad_incognitas):
        coeficiente = fila[indice]
        if coeficiente == 0:
            continue

        expresion += (
            f" - ({formatear_numero_operacion(coeficiente)})"
            f"x{indice + 1}"
        )

    return expresion


def sustitucion_regresiva(matriz_escalonada, pivotes, cantidad_incognitas=None):
    """Resuelve por sustitución regresiva una forma escalonada compatible."""
    es_valida, mensaje = validar_matriz(matriz_escalonada)
    if not es_valida:
        raise ValueError(mensaje)

    cantidad_columnas = len(matriz_escalonada[0])
    if cantidad_incognitas is None:
        cantidad_incognitas = cantidad_columnas - 1

    if cantidad_incognitas <= 0 or cantidad_incognitas >= cantidad_columnas:
        raise ValueError("La cantidad de incógnitas no es válida.")

    if len(pivotes) != cantidad_incognitas:
        raise ValueError(
            "La sustitución regresiva requiere un pivote para cada incógnita."
        )

    matriz = convertir_matriz_a_fracciones(matriz_escalonada)
    soluciones = [Fraction(0) for _ in range(cantidad_incognitas)]
    pasos = []

    for fila, columna in reversed(pivotes):
        pivote = matriz[fila][columna]
        if pivote == 0:
            raise ValueError("No se puede dividir entre un pivote cero.")

        expresion = formatear_expresion_sustitucion(
            matriz[fila],
            columna,
            soluciones,
            cantidad_incognitas
        )
        suma_conocida = sum(
            matriz[fila][indice] * soluciones[indice]
            for indice in range(columna + 1, cantidad_incognitas)
        )
        solucion = (
            matriz[fila][cantidad_incognitas] - suma_conocida
        ) / pivote
        soluciones[columna] = solucion
        pasos.append(
            f"Fila {fila + 1}: x{columna + 1} = {expresion} "
            f"= {formatear_numero_operacion(solucion)}"
        )

    return soluciones, pasos


def resolver_gauss(matriz):
    matriz_escalonada, pasos, pivotes = aplicar_gauss(
        matriz,
        es_sistema=True
    )
    analisis = analizar_sistema(matriz_escalonada)
    soluciones = None
    pasos_sustitucion = []

    if obtener_tipo_sistema(matriz_escalonada) == "compatible determinado":
        soluciones, pasos_sustitucion = sustitucion_regresiva(
            matriz_escalonada,
            pivotes,
            len(matriz_escalonada[0]) - 1
        )

    return (
        matriz_escalonada,
        pasos,
        pivotes,
        analisis,
        soluciones,
        pasos_sustitucion
    )


def analizar_resultado_gauss_jordan(
    matriz,
    pivotes=None,
    tipo_matriz=None,
    es_sistema=None
):
    """Compatibilidad con el nombre anterior, sin inferir sistemas por forma."""
    if es_sistema is None:
        es_sistema = tipo_matriz == "aumentada"

    if not es_sistema:
        return [
            "La matriz se redujo sin interpretarla como un sistema de ecuaciones."
        ]

    return analizar_sistema(matriz)


def resolver_gauss_jordan(matriz, es_sistema=False):
    matriz_reducida, pasos, pivotes = aplicar_gauss_jordan(
        matriz,
        es_sistema=es_sistema
    )
    analisis = (
        analizar_sistema(matriz_reducida)
        if es_sistema
        else analizar_resultado_gauss_jordan(matriz_reducida, pivotes)
    )

    return matriz_reducida, pasos, analisis
