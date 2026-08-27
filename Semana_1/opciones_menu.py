from entradas import (
    pedir_dimensiones,
    pedir_elemento_matriz,
    pedir_indices,
    pedir_nuevo_numero
)
from logica_matrices import (
    generar_matriz,
    resolver_gauss_jordan,
    validar_dimensiones_gauss_jordan
)
from salida import imprimir_matriz, imprimir_paso_gauss_jordan


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
            valor = pedir_elemento_matriz(i + 1, j + 1)
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
    numero = pedir_nuevo_numero()

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
    imprimir_matriz(matriz)


def resolver_gauss_jordan_menu(matriz):
    if not validar_matriz(matriz):
        return

    es_valida, mensaje = validar_dimensiones_gauss_jordan(matriz)
    if not es_valida:
        print(f"\n{mensaje}")
        return

    print("\n==== Método de Gauss-Jordan ====")
    matriz_reducida, pasos, analisis = resolver_gauss_jordan(matriz)

    if pasos:
        print("\n==== Pasos realizados ====\n")
        for indice, paso in enumerate(pasos):
            print(f"Paso {indice + 1}:")
            imprimir_paso_gauss_jordan(paso)
            print()
    else:
        print("\nNo fue necesario realizar operaciones por filas.")

    print("==== Matriz reducida ====\n")
    imprimir_matriz(matriz_reducida)

    print("\n==== Análisis ====\n")
    for linea in analisis:
        print(linea)
