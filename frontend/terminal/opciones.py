from backend.logica_matrices import (
    generar_matriz,
    resolver_gauss_jordan,
    validar_dimensiones_gauss_jordan
)
from frontend.terminal import consola
from frontend.terminal.entradas import (
    pedir_dimensiones,
    pedir_elemento_matriz,
    pedir_indices,
    pedir_nuevo_numero
)
from frontend.terminal.salida import imprimir_matriz, imprimir_paso_gauss_jordan

_AVISO_INDICES = "Los índices de filas y columnas empiezan en 1."


def validar_matriz(matriz):
    if not matriz:
        consola.error("Error: No hay ninguna matriz creada o generada.")
        return False

    return True


def crear_matriz():
    consola.titulo("Creador de matrices")

    filas, columnas = pedir_dimensiones()
    matriz = []

    consola.subtitulo("Elementos de la matriz")
    for i in range(filas):
        fila = []
        consola.info(f"\nFila {i + 1}")
        matriz.append(fila)
        for j in range(columnas):
            valor = pedir_elemento_matriz(i + 1, j + 1)
            fila.append(valor)

    consola.exito("Matriz creada correctamente.")
    print()
    imprimir_matriz(matriz)
    return matriz


def generador_matriz():
    consola.titulo("Generador de matrices")

    filas, columnas = pedir_dimensiones()
    matriz = generar_matriz(filas, columnas)

    consola.exito("Matriz generada correctamente.")
    print()
    imprimir_matriz(matriz)
    return matriz


def modificar_elemento(matriz):
    if not validar_matriz(matriz):
        return

    consola.titulo("Modificador de elementos")
    consola.info(_AVISO_INDICES)
    fila, columna = pedir_indices(matriz)
    numero = pedir_nuevo_numero()

    matriz[fila - 1][columna - 1] = numero
    consola.exito("Elemento modificado correctamente.")
    print()
    imprimir_matriz(matriz)


def consultar_elemento(matriz):
    if not validar_matriz(matriz):
        return

    consola.titulo("Consultor de elementos")
    consola.info(_AVISO_INDICES)
    fila, columna = pedir_indices(matriz)

    numero = matriz[fila - 1][columna - 1]
    consola.exito(f"El elemento en la posición [{fila},{columna}] = {numero}")


def mostrar_matriz(matriz):
    if not validar_matriz(matriz):
        return

    consola.titulo("Matriz")
    print()
    imprimir_matriz(matriz)


def resolver_gauss_jordan_menu(matriz):
    if not validar_matriz(matriz):
        return

    es_valida, mensaje = validar_dimensiones_gauss_jordan(matriz)
    if not es_valida:
        consola.error(mensaje)
        return

    consola.titulo("Método de Gauss-Jordan")
    matriz_reducida, pasos, analisis = resolver_gauss_jordan(matriz)

    if pasos:
        consola.subtitulo("Pasos realizados")
        print()
        for indice, paso in enumerate(pasos):
            consola.info(f"Paso {indice + 1}:")
            imprimir_paso_gauss_jordan(paso)
            print()
    else:
        consola.advertencia("No fue necesario realizar operaciones por filas.")

    consola.subtitulo("Matriz reducida")
    print()
    imprimir_matriz(matriz_reducida)

    consola.subtitulo("Análisis")
    print()
    for linea in analisis:
        print(linea)
