import random

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


def generar_matriz(filas, columnas):
    matriz = []

    for i in range(filas):
        matriz.append([])
        for j in range(columnas):
            num = random.randint(0, 20)
            matriz[i].append(num)

    return matriz


def validar_matriz(matriz):
    if not matriz:
        print("\nError: No hay matrices generadas o creadas.")
        return False

    return True


def crear_matriz():
    print("\n==== Creador de matrices ====")

    filas, columnas = pedir_dimensiones()
    matriz = []

    print("\n==== Elementos de la matriz: ====")
    for i in range(filas):
        fila = []
        print(f"\nFila {i + 1}: ")
        matriz.append(fila)
        for j in range(columnas):
            while True:
                try:
                    valor = int(input(f"Ingrese el elemento [{i + 1},{j + 1}]: "))
                    break
                except ValueError:
                    print("Error: Input inválido.\n")

            fila.append(valor)
    print("\nMatriz creada correctamente!")
    return matriz

def generador_matriz():
    print("\n==== Generador de matrices ====")

    filas, columnas = pedir_dimensiones()
    matriz = generar_matriz(filas, columnas)

    print("\nMatriz generada correctamente!")
    return matriz


def modificar_elemento(matriz):
    if not validar_matriz(matriz):
        return

    print("\n==== Modificador de elementos ====")
    fila, columna = pedir_indices(matriz)

    while True:
        try:
            numero = int(input("\nIngresa el nuevo número: "))
            break
        except ValueError:
            print("Error: Número inválido.")

    matriz[fila - 1][columna - 1] = numero
    print("\nElemento modificado correctamente!")


def consultar_elemento(matriz):
    if not validar_matriz(matriz):
        return

    print("\n==== Consultor de elementos ====")
    fila, columna = pedir_indices(matriz)

    numero = matriz[fila - 1][columna - 1]
    print(f"\nEl elemento en la posición [{fila},{columna}] = {numero}\n")


def mostrar_matriz(matriz):
    if not validar_matriz(matriz):
        return
    print("\n===== Matriz =====\n")
    for fila in matriz:
        print("[", end=" ")
        for numero in fila:
            print(f"{numero:3}", end=" ")
        print("]")