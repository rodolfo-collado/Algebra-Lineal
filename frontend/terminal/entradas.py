from frontend.terminal import consola

_NUMERO_INVALIDO = "Error: Ingrese un número válido."


def pedir_dimensiones():
    while True:
        try:
            filas = int(consola.pedir("\nIngrese la cantidad de filas: "))
            if filas <= 0:
                consola.error("Error: La cantidad de filas debe ser mayor que 0.")
                continue

            columnas = int(consola.pedir("Ingrese la cantidad de columnas: "))
            if columnas <= 0:
                consola.error("Error: La cantidad de columnas debe ser mayor que 0.")
                continue

        except ValueError:
            consola.error(_NUMERO_INVALIDO)
            continue

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
    while True:
        try:
            valor = int(consola.pedir(f"Ingrese el elemento [{fila},{columna}]: "))
            return valor
        except ValueError:
            consola.error(_NUMERO_INVALIDO)


def pedir_nuevo_numero():
    while True:
        try:
            numero = int(consola.pedir("\nIngresa el nuevo número: "))
            return numero
        except ValueError:
            consola.error(_NUMERO_INVALIDO)
