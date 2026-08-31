import random
from fractions import Fraction


def generar_matriz(filas, columnas):
    matriz = []

    for i in range(filas):
        matriz.append([])
        for j in range(columnas):
            num = random.randint(0, 20)
            matriz[i].append(num)

    return matriz


def copiar_matriz(matriz):
    copia = []

    for fila in matriz:
        copia.append(fila.copy())

    return copia


def convertir_matriz_a_fracciones(matriz):
    matriz_fracciones = []

    for fila in matriz:
        nueva_fila = []
        for numero in fila:
            nueva_fila.append(Fraction(numero))
        matriz_fracciones.append(nueva_fila)

    return matriz_fracciones


def es_matriz_rectangular(matriz):
    columnas = len(matriz[0])

    for fila in matriz:
        if len(fila) != columnas:
            return False

    return True


def obtener_tipo_gauss_jordan(matriz):
    filas = len(matriz)
    columnas = len(matriz[0])

    if filas == columnas:
        return "cuadrada"

    if columnas == filas + 1:
        return "aumentada"

    return None


def validar_dimensiones_gauss_jordan(matriz):
    if not es_matriz_rectangular(matriz):
        return False, "Error: La matriz no es rectangular."

    tipo_matriz = obtener_tipo_gauss_jordan(matriz)
    if tipo_matriz is None:
        filas = len(matriz)
        columnas = len(matriz[0])
        return False, (
            f"Error: La matriz es de {filas}x{columnas}. "
            "Para Gauss-Jordan use matrices nxn o nx(n+1)."
        )

    return True, tipo_matriz


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
    if numero.denominator == 1:
        return str(numero.numerator)
    return f"{numero.numerator}/{numero.denominator}"


def texto_factor(factor):
    if factor < 0:
        return f"+ ({formatear_numero_operacion(-factor)})"

    return f"- ({formatear_numero_operacion(factor)})"


def aplicar_gauss_jordan(matriz):
    es_valida, mensaje = validar_dimensiones_gauss_jordan(matriz)
    if not es_valida:
        raise ValueError(mensaje)

    matriz_reducida = convertir_matriz_a_fracciones(matriz)
    pasos = []
    filas = len(matriz_reducida)
    columnas = len(matriz_reducida[0])
    tipo_matriz = obtener_tipo_gauss_jordan(matriz_reducida)
    columnas_pivote = columnas - 1 if tipo_matriz == "aumentada" else columnas
    fila_pivote = 0
    pivotes = []

    for columna in range(columnas_pivote):
        if fila_pivote >= filas:
            break

        fila_encontrada = buscar_fila_pivote(matriz_reducida, fila_pivote, columna)
        if fila_encontrada is None:
            continue

        if fila_encontrada != fila_pivote:
            matriz_antes = copiar_matriz(matriz_reducida)
            matriz_reducida[fila_pivote], matriz_reducida[fila_encontrada] = (
                matriz_reducida[fila_encontrada],
                matriz_reducida[fila_pivote]
            )
            operacion = f"F{fila_pivote + 1} <-> F{fila_encontrada + 1}"
            registrar_paso(pasos, matriz_antes, operacion, matriz_reducida)

        pivote = matriz_reducida[fila_pivote][columna]
        if pivote != 1:
            matriz_antes = copiar_matriz(matriz_reducida)
            matriz_reducida[fila_pivote] = [
                numero / pivote for numero in matriz_reducida[fila_pivote]
            ]
            factor_pivote = formatear_numero_operacion(Fraction(1, 1) / pivote)
            operacion = f"F{fila_pivote + 1} = ({factor_pivote})F{fila_pivote + 1}"
            registrar_paso(pasos, matriz_antes, operacion, matriz_reducida)

        for fila in range(fila_pivote + 1, filas):
            factor = matriz_reducida[fila][columna]
            if factor == 0:
                continue

            matriz_antes = copiar_matriz(matriz_reducida)
            matriz_reducida[fila] = [
                matriz_reducida[fila][columna_actual]
                - factor * matriz_reducida[fila_pivote][columna_actual]
                for columna_actual in range(columnas)
            ]
            operacion = (
                f"F{fila + 1} = F{fila + 1} "
                f"{texto_factor(factor)}F{fila_pivote + 1}"
            )
            registrar_paso(pasos, matriz_antes, operacion, matriz_reducida)

        pivotes.append((fila_pivote, columna))
        fila_pivote += 1

    for fila_pivote, columna in reversed(pivotes):
        for fila in range(fila_pivote - 1, -1, -1):
            factor = matriz_reducida[fila][columna]
            if factor == 0:
                continue

            matriz_antes = copiar_matriz(matriz_reducida)
            matriz_reducida[fila] = [
                matriz_reducida[fila][columna_actual]
                - factor * matriz_reducida[fila_pivote][columna_actual]
                for columna_actual in range(columnas)
            ]
            operacion = (
                f"F{fila + 1} = F{fila + 1} "
                f"{texto_factor(factor)}F{fila_pivote + 1}"
            )
            registrar_paso(pasos, matriz_antes, operacion, matriz_reducida)

    return matriz_reducida, pasos, pivotes, tipo_matriz


def obtener_rango(matriz, columnas_limite):
    rango = 0

    for fila in matriz:
        for columna in range(columnas_limite):
            if fila[columna] != 0:
                rango += 1
                break

    return rango


def analizar_resultado_gauss_jordan(matriz, pivotes, tipo_matriz):
    filas = len(matriz)
    columnas = len(matriz[0])

    if tipo_matriz == "cuadrada":
        rango = obtener_rango(matriz, columnas)
        if rango == filas:
            return ["La matriz cuadrada es invertible y se redujo a la identidad."]

        return [
            "La matriz cuadrada es singular.",
            "No se consiguieron pivotes en todas las columnas.",
            "Si se interpreta como sistema homogéneo, tiene infinitas soluciones."
        ]

    columnas_coeficientes = columnas - 1
    rango_coeficientes = obtener_rango(matriz, columnas_coeficientes)

    for fila in matriz:
        coeficientes_en_cero = True
        for columna in range(columnas_coeficientes):
            if fila[columna] != 0:
                coeficientes_en_cero = False
                break

        if coeficientes_en_cero and fila[-1] != 0:
            return [
                "Sistema incompatible.",
                "Apareció una fila del tipo 0 = k, con k distinto de 0.",
                "No tiene solución."
            ]

    if rango_coeficientes < columnas_coeficientes:
        return [
            "Sistema compatible indeterminado.",
            "Tiene infinitas soluciones porque no hay pivote para cada variable."
        ]

    soluciones = [Fraction(0) for _ in range(columnas_coeficientes)]
    for fila, columna in pivotes:
        if columna < columnas_coeficientes:
            soluciones[columna] = matriz[fila][-1]

    resultado = ["Sistema compatible determinado.", "Solución única:"]
    for indice, solucion in enumerate(soluciones):
        resultado.append(f"x{indice + 1} = {formatear_numero_operacion(solucion)}")

    return resultado


def resolver_gauss_jordan(matriz):
    matriz_reducida, pasos, pivotes, tipo_matriz = aplicar_gauss_jordan(matriz)
    analisis = analizar_resultado_gauss_jordan(matriz_reducida, pivotes, tipo_matriz)

    return matriz_reducida, pasos, analisis
