from frontend.terminal import consola
from frontend.terminal.opciones import (
    consultar_elemento,
    crear_matriz,
    generador_matriz,
    modificar_elemento,
    mostrar_matriz,
    resolver_gauss_jordan_menu
)

_OPCIONES = (
    "1. Generar matriz",
    "2. Crear matriz",
    "3. Modificar elemento",
    "4. Consultar elemento",
    "5. Ver matriz completa",
    "6. Resolver por Gauss-Jordan",
    "7. Salir"
)


def describir_matriz_activa(matriz):
    if not matriz:
        return "Sin matriz activa."

    return f"Matriz activa de {len(matriz)} x {len(matriz[0])}."


def mostrar_menu(matriz):
    consola.titulo("PRÁCTICA DE MATRICES")
    print()
    for opcion in _OPCIONES:
        print(f"  {opcion}")
    print()
    consola.info(describir_matriz_activa(matriz))
    consola.info("Los índices de filas y columnas empiezan en 1.")


def ejecutar_menu():
    matriz = []
    consola.limpiar_pantalla()

    while True:
        mostrar_menu(matriz)
        opcion = consola.pedir("\nSelecciona una opción: ").strip()

        if opcion == "7":
            break

        consola.limpiar_pantalla()

        match opcion:
            case "1": matriz = generador_matriz()
            case "2": matriz = crear_matriz()
            case "3": modificar_elemento(matriz)
            case "4": consultar_elemento(matriz)
            case "5": mostrar_matriz(matriz)
            case "6": resolver_gauss_jordan_menu(matriz)
            case _: consola.error("Error: Selección inválida.")

        consola.pausar()
        consola.limpiar_pantalla()

    consola.exito("Hasta luego.")
    consola.restablecer()
