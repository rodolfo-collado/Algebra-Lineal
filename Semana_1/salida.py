from fractions import Fraction


def formatear_numero(numero):
    if isinstance(numero, Fraction):
        if numero.denominator == 1:
            return str(numero.numerator)
        return f"{numero.numerator}/{numero.denominator}"

    return str(numero)


def obtener_lineas_matriz(matriz):
    valores = []

    for fila in matriz:
        valores.append([formatear_numero(numero) for numero in fila])

    anchos = []
    for columna in range(len(valores[0])):
        ancho = max(len(fila[columna]) for fila in valores)
        anchos.append(max(ancho, 3))

    lineas = []
    for fila in valores:
        linea = "[ "
        for indice, numero in enumerate(fila):
            linea += f"{numero:>{anchos[indice]}} "
        linea += "]"
        lineas.append(linea)

    return lineas


def imprimir_matriz(matriz):
    for linea in obtener_lineas_matriz(matriz):
        print(linea)


def imprimir_paso_gauss_jordan(paso):
    matriz_antes = obtener_lineas_matriz(paso["antes"])
    matriz_despues = obtener_lineas_matriz(paso["despues"])
    operacion = f"  {paso['operacion']}  "
    alto = max(len(matriz_antes), len(matriz_despues))
    ancho_antes = max(len(linea) for linea in matriz_antes)
    ancho_operacion = len(operacion)

    for i in range(alto):
        linea_antes = matriz_antes[i] if i < len(matriz_antes) else " " * ancho_antes
        linea_despues = matriz_despues[i] if i < len(matriz_despues) else ""

        if i == alto // 2:
            texto_operacion = operacion
        else:
            texto_operacion = " " * ancho_operacion

        print(f"{linea_antes:<{ancho_antes}}{texto_operacion}{linea_despues}")
