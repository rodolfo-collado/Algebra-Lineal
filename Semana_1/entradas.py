from fractions import Fraction


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
            if fila <= 0 or fila > len(matriz):
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

    return fila, columna


def convertir_a_numero(texto):
    """Acepta enteros y fracciones sin perder exactitud."""
    numero = Fraction(texto.strip())
    if numero.denominator == 1:
        return numero.numerator

    return numero


def pedir_elemento_matriz(fila, columna):
    while True:
        try:
            return convertir_a_numero(
                input(f"Ingrese el elemento [{fila},{columna}]: ")
            )
        except (ValueError, ZeroDivisionError):
            print("Error: Ingrese un número válido.\n")


def pedir_nuevo_numero():
    while True:
        try:
            return convertir_a_numero(input("\nIngresa el nuevo número: "))
        except (ValueError, ZeroDivisionError):
            print("Error: Número inválido.")


def pedir_coeficiente(numero_incognita):
    while True:
        try:
            return convertir_a_numero(
                input(f"Coeficiente de x{numero_incognita}: ")
            )
        except (ValueError, ZeroDivisionError):
            print("Error: Ingrese un número válido.\n")


def pedir_termino_independiente(numero_ecuacion):
    while True:
        try:
            return convertir_a_numero(
                input(
                    f"Término independiente de la ecuación "
                    f"{numero_ecuacion}: "
                )
            )
        except (ValueError, ZeroDivisionError):
            print("Error: Ingrese un número válido.\n")


def pedir_si_no(mensaje):
    while True:
        respuesta = input(f"{mensaje} (s/n): ").strip().lower()
        if respuesta in ("s", "n"):
            return respuesta == "s"

        print("Error: Responda con 's' o 'n'.")
