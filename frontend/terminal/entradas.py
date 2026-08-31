from backend.parser_sistemas import construir_matriz_aumentada, convertir_a_numero
from frontend.terminal import consola

_NUMERO_INVALIDO = "Error: Ingrese un número válido."


def pedir_entero_positivo(mensaje, nombre):
    while True:
        try:
            valor = int(consola.pedir(mensaje))
        except ValueError:
            consola.error(_NUMERO_INVALIDO)
            continue

        if valor <= 0:
            consola.error(f"Error: La cantidad de {nombre} debe ser mayor que 0.")
            continue

        return valor


def pedir_numero(mensaje):
    """Acepta enteros, negativos, fracciones y decimales."""
    while True:
        try:
            return convertir_a_numero(consola.pedir(mensaje))
        except ValueError:
            consola.error(_NUMERO_INVALIDO)


def pedir_dimensiones():
    filas = pedir_entero_positivo("\nIngrese la cantidad de filas: ", "filas")
    columnas = pedir_entero_positivo("Ingrese la cantidad de columnas: ", "columnas")

    return filas, columnas


def pedir_indices(matriz):
    while True:
        try:
            fila = int(consola.pedir("\nIngrese el índice de la fila: "))
            if fila <= 0 or fila > len(matriz):
                consola.error("Error: Fila fuera de rango.")
                continue
            columna = int(consola.pedir("Ingrese el índice de la columna: "))
            if columna <= 0 or columna > len(matriz[fila - 1]):
                consola.error("Error: Columna fuera de rango.")
                continue

        except ValueError:
            consola.error(_NUMERO_INVALIDO)
            continue
        break

    return fila, columna


def pedir_elemento_matriz(fila, columna):
    return pedir_numero(f"Ingrese el elemento [{fila},{columna}]: ")


def pedir_nuevo_numero():
    return pedir_numero("\nIngresa el nuevo número: ")


def pedir_texto_sistema():
    return consola.pedir("\nSistema: ")


def pedir_sistema_manual():
    """Pide las dimensiones y los coeficientes, y devuelve la matriz aumentada."""
    variables = pedir_entero_positivo("\nCantidad de variables: ", "variables")
    ecuaciones = pedir_entero_positivo("Cantidad de ecuaciones: ", "ecuaciones")

    coeficientes = []
    terminos_independientes = []
    for numero_ecuacion in range(1, ecuaciones + 1):
        consola.info(f"\nEcuación {numero_ecuacion}")
        coeficientes.append([
            pedir_numero(f"x{variable}: ")
            for variable in range(1, variables + 1)
        ])
        terminos_independientes.append(pedir_numero("Término independiente: "))

    return construir_matriz_aumentada(coeficientes, terminos_independientes)
