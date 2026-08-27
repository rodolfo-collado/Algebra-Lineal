from entradas import (
    pedir_coeficiente,
    pedir_dimensiones,
    pedir_elemento_matriz,
    pedir_indices,
    pedir_nuevo_numero,
    pedir_si_no,
    pedir_termino_independiente
)
from logica_matrices import (
    generar_matriz,
    resolver_gauss,
    resolver_gauss_jordan
)
from salida import imprimir_matriz, imprimir_paso


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
    for indice_fila in range(filas):
        fila = []
        print(f"\nFila {indice_fila + 1}: ")
        for indice_columna in range(columnas):
            valor = pedir_elemento_matriz(
                indice_fila + 1,
                indice_columna + 1
            )
            fila.append(valor)
        matriz.append(fila)

    print("\nMatriz creada correctamente!")
    return matriz


def generador_matriz():
    print("\n==== Generador de matrices ====")

    filas, columnas = pedir_dimensiones()
    matriz = generar_matriz(filas, columnas)

    print("\nMatriz generada correctamente!")
    return matriz


def crear_sistema_ecuaciones():
    print("\n==== Crear sistema de ecuaciones ====")
    print("La primera ecuación define la cantidad de incógnitas.")

    matriz = []
    numero_ecuacion = 1
    coeficientes_primera_ecuacion = []
    numero_incognita = 1

    print(f"\nEcuación {numero_ecuacion}")
    while True:
        coeficientes_primera_ecuacion.append(
            pedir_coeficiente(numero_incognita)
        )
        if not pedir_si_no("¿Añadir otra incógnita?"):
            break
        numero_incognita += 1

    coeficientes_primera_ecuacion.append(
        pedir_termino_independiente(numero_ecuacion)
    )
    matriz.append(coeficientes_primera_ecuacion)

    while pedir_si_no("¿Añadir otra ecuación?"):
        numero_ecuacion += 1
        print(f"\nEcuación {numero_ecuacion}")
        fila = []
        for indice in range(1, numero_incognita + 1):
            fila.append(pedir_coeficiente(indice))
        fila.append(pedir_termino_independiente(numero_ecuacion))
        matriz.append(fila)

    print("\nSistema creado correctamente!")
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


def imprimir_pasos(pasos):
    if pasos:
        print("\n==== Pasos realizados ====\n")
        for indice, paso in enumerate(pasos):
            print(f"Paso {indice + 1}:")
            imprimir_paso(paso)
            print()
    else:
        print("\nNo fue necesario realizar operaciones por filas.")


def resolver_gauss_menu(matriz):
    if not validar_matriz(matriz):
        return

    print("\n==== Método de Gauss ====")
    try:
        (
            matriz_escalonada,
            pasos,
            _pivotes,
            analisis,
            soluciones,
            pasos_sustitucion
        ) = resolver_gauss(matriz)
    except ValueError as error:
        print(f"\n{error}")
        return

    imprimir_pasos(pasos)
    print("==== Matriz escalonada ====\n")
    imprimir_matriz(matriz_escalonada)

    if pasos_sustitucion:
        print("\n==== Sustitución regresiva ====")
        for paso in pasos_sustitucion:
            print(paso)

    if soluciones is not None:
        print("\n==== Soluciones ====")
        for indice, solucion in enumerate(soluciones, start=1):
            print(f"x{indice} = {solucion}")

    print("\n==== Análisis ====")
    for linea in analisis:
        print(linea)


def resolver_gauss_jordan_menu(matriz):
    if not validar_matriz(matriz):
        return

    print("\n==== Método de Gauss-Jordan ====")
    try:
        matriz_reducida, pasos, analisis = resolver_gauss_jordan(
            matriz
        )
    except ValueError as error:
        print(f"\n{error}")
        return

    imprimir_pasos(pasos)
    print("==== Matriz reducida ====\n")
    imprimir_matriz(matriz_reducida)

    print("\n==== Análisis ====")
    for linea in analisis:
        print(linea)
