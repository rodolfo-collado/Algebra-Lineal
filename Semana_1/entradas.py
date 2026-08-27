def pedir_dimensiones():

    while True:
        try:
            filas = int(input("\nIngrese la cantidad de filas: "))
            if filas <= 0:
                print("Error: Cantidad de filas negativa.")
                continue

            columnas = int(input("Ingrese la cantidad de columnas: "))
            if columnas <= 0:
                print("Error: Cantidad de columnas negativa.")
                continue

        except ValueError:
            print("Error: Ingrese un numero valido.")
            continue

        return filas, columnas


def pedir_indices(matriz):
    while True:
        try:
            fila = int(input("\nIngrese el índice de la fila: "))
            if fila <=0 or fila > len(matriz):
                print("Error: Fila fuera de rango.")
                continue
            columna = int(input("Ingrese el índice de la columna: "))
            if columna <= 0 or columna > len(matriz[fila - 1]):
                print("Error: Columna fuera de rango.")
                continue

        except ValueError:
            print("Error: Ingrese un número válido.")
            continue
        break

    return fila,columna


def pedir_elemento_matriz(fila, columna):
    while True:
        try:
            valor = int(input(f"Ingrese el elemento [{fila},{columna}]: "))
            return valor
        except ValueError:
            print("Error: Input inválido.\n")


def pedir_nuevo_numero():
    while True:
        try:
            numero = int(input("\nIngresa el nuevo número: "))
            return numero
        except ValueError:
            print("Error: Número inválido.")
