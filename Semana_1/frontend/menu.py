from ..backend.matrices import generar_matriz
from ..backend.parser_sistemas import parsear_sistema
from ..backend.sistemas import resolver_gauss, resolver_gauss_jordan
from .entradas import (
    pedir_dimensiones,
    pedir_indices,
    pedir_matriz,
    pedir_numero,
    pedir_sistema_manual,
    pedir_texto_sistema
)
from .salida import (
    imprimir_matriz,
    imprimir_pasos,
    mostrar_analisis,
    mostrar_soluciones
)
from .terminal import (
    limpiar_consola,
    mostrar_error,
    mostrar_exito,
    mostrar_info,
    mostrar_titulo,
    pausar
)


def validar_matriz(matriz):
    if not matriz:
        mostrar_error("No hay una matriz activa.")
        return False
    return True


def crear_matriz():
    mostrar_titulo("==== Crear matriz ====")
    filas, columnas = pedir_dimensiones()
    return pedir_matriz(filas, columnas)


def generador_matriz():
    mostrar_titulo("==== Generar matriz ====")
    filas, columnas = pedir_dimensiones()
    return generar_matriz(filas, columnas)


def modificar_elemento(matriz):
    if not validar_matriz(matriz):
        return

    mostrar_titulo("==== Modificar elemento ====")
    fila, columna = pedir_indices(matriz)
    matriz[fila - 1][columna - 1] = pedir_numero("Nuevo valor: ")
    mostrar_exito("Elemento modificado correctamente.")


def consultar_elemento(matriz):
    if not validar_matriz(matriz):
        return

    mostrar_titulo("==== Consultar elemento ====")
    fila, columna = pedir_indices(matriz)
    print(f"Valor [{fila},{columna}]: {matriz[fila - 1][columna - 1]}")


def mostrar_matriz(matriz):
    if not validar_matriz(matriz):
        return

    mostrar_titulo("==== Matriz ====")
    imprimir_matriz(matriz)


def menu_sistemas():
    while True:
        limpiar_consola()
        mostrar_titulo("Crear sistema de ecuaciones")
        print("1. Ingresar sistema directamente")
        print("2. Ingresar coeficientes manualmente")
        print("3. Volver")
        opcion = input("\nOpción: ").strip()

        if opcion == "1":
            limpiar_consola()
            mostrar_titulo("==== Ingresar sistema directamente ====")
            print("Ingrese el sistema separando las ecuaciones con ';':\n")
            try:
                matriz = parsear_sistema(pedir_texto_sistema())
            except ValueError as error:
                mostrar_error(str(error))
                pausar()
                return None

            mostrar_exito("Sistema creado correctamente.")
            pausar()
            return matriz

        if opcion == "2":
            limpiar_consola()
            mostrar_titulo("==== Ingresar coeficientes manualmente ====")
            matriz = pedir_sistema_manual()
            mostrar_exito("Sistema creado correctamente.")
            pausar()
            return matriz

        if opcion == "3":
            return None

        mostrar_error("Opción inválida.")
        pausar()


def resolver_gauss_menu(matriz):
    if not validar_matriz(matriz):
        return

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
        mostrar_error(str(error))
        return

    mostrar_titulo("==== Método de Gauss ====")
    imprimir_pasos(pasos)
    mostrar_titulo("==== Matriz escalonada ====")
    imprimir_matriz(matriz_escalonada)
    mostrar_analisis(analisis)

    if pasos_sustitucion:
        mostrar_titulo("\n==== Sustitución regresiva ====")
        for paso in pasos_sustitucion:
            print(paso)
    mostrar_soluciones(soluciones)


def resolver_gauss_jordan_menu(matriz):
    if not validar_matriz(matriz):
        return

    try:
        matriz_reducida, pasos, analisis = resolver_gauss_jordan(matriz)
    except ValueError as error:
        mostrar_error(str(error))
        return

    mostrar_titulo("==== Método de Gauss-Jordan ====")
    imprimir_pasos(pasos)
    mostrar_titulo("==== Matriz reducida ====")
    imprimir_matriz(matriz_reducida)
    mostrar_analisis(analisis)


def mostrar_menu_principal():
    mostrar_titulo("Calculadora de Álgebra Lineal")
    print("\n1. Generar matriz")
    print("2. Crear matriz")
    print("3. Crear sistema de ecuaciones")
    print("4. Modificar elemento")
    print("5. Consultar elemento")
    print("6. Ver matriz")
    print("7. Resolver por Gauss")
    print("8. Resolver por Gauss-Jordan")
    print("9. Salir")


def ejecutar_aplicacion():
    matriz = []
    limpiar_consola()

    while True:
        limpiar_consola()
        mostrar_menu_principal()
        opcion = input("\nOpción: ").strip()

        if opcion == "1":
            limpiar_consola()
            matriz = generador_matriz()
            mostrar_exito("Matriz generada correctamente.")
            pausar()
        elif opcion == "2":
            limpiar_consola()
            matriz = crear_matriz()
            mostrar_exito("Matriz creada correctamente.")
            pausar()
        elif opcion == "3":
            nueva_matriz = menu_sistemas()
            if nueva_matriz is not None:
                matriz = nueva_matriz
        elif opcion == "4":
            limpiar_consola()
            modificar_elemento(matriz)
            pausar()
        elif opcion == "5":
            limpiar_consola()
            consultar_elemento(matriz)
            pausar()
        elif opcion == "6":
            limpiar_consola()
            mostrar_matriz(matriz)
            pausar()
        elif opcion == "7":
            limpiar_consola()
            resolver_gauss_menu(matriz)
            pausar()
        elif opcion == "8":
            limpiar_consola()
            resolver_gauss_jordan_menu(matriz)
            pausar()
        elif opcion == "9":
            mostrar_info("Hasta luego.")
            break
        else:
            mostrar_error("Opción inválida.")
            pausar()
