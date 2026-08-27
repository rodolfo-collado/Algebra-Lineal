from ..backend.parser_sistemas import convertir_a_numero
from .terminal import mostrar_error


def pedir_entero_positivo(mensaje):
    while True:
        try:
            valor = int(input(mensaje))
            if valor <= 0:
                raise ValueError
            return valor
        except ValueError:
            mostrar_error("Error: Ingrese un número entero mayor que cero.")


def pedir_numero(mensaje):
    while True:
        try:
            return convertir_a_numero(input(mensaje))
        except (ValueError, ZeroDivisionError):
            mostrar_error("Error: Ingrese un número válido.")


def pedir_dimensiones():
    filas = pedir_entero_positivo("Cantidad de filas: ")
    columnas = pedir_entero_positivo("Cantidad de columnas: ")
    return filas, columnas


def pedir_indices(matriz):
    while True:
        try:
            fila = int(input("Índice de la fila: "))
            columna = int(input("Índice de la columna: "))
            if fila <= 0 or fila > len(matriz):
                raise ValueError("fila")
            if columna <= 0 or columna > len(matriz[fila - 1]):
                raise ValueError("columna")
            return fila, columna
        except ValueError:
            mostrar_error("Error: Índice fuera de rango o inválido.")


def pedir_matriz(filas, columnas):
    matriz = []
    for indice_fila in range(filas):
        print(f"\nFila {indice_fila + 1}")
        fila = []
        for indice_columna in range(columnas):
            fila.append(
                pedir_numero(
                    f"Elemento [{indice_fila + 1},{indice_columna + 1}]: "
                )
            )
        matriz.append(fila)
    return matriz


def pedir_sistema_manual():
    variables = pedir_entero_positivo("Cantidad de variables: ")
    ecuaciones = pedir_entero_positivo("Cantidad de ecuaciones: ")
    matriz = []

    for indice_ecuacion in range(ecuaciones):
        print(f"\nEcuación {indice_ecuacion + 1}")
        fila = [
            pedir_numero(f"x{indice_variable}: ")
            for indice_variable in range(1, variables + 1)
        ]
        fila.append(pedir_numero("Término independiente: "))
        matriz.append(fila)

    return matriz


def pedir_texto_sistema():
    return input("> ").strip()
