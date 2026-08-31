from frontend.terminal import consola
from frontend.terminal.opciones import (
    consultar_elemento,
    crear_matriz,
    crear_sistema_directo,
    crear_sistema_manual,
    generador_matriz,
    modificar_elemento,
    mostrar_matriz,
    resolver_por_gauss,
    resolver_por_gauss_jordan
)

_OPCIONES = (
    "1. Generar matriz",
    "2. Crear matriz",
    "3. Crear sistema de ecuaciones",
    "4. Modificar elemento",
    "5. Consultar elemento",
    "6. Ver matriz",
    "7. Resolver por Gauss",
    "8. Resolver por Gauss-Jordan",
    "9. Salir"
)

_OPCIONES_SISTEMA = (
    "1. Ingresar sistema directamente",
    "2. Ingresar coeficientes manualmente",
    "3. Volver"
)


def describir_matriz_activa(matriz):
    if not matriz:
        return "Sin matriz activa."

    return f"Matriz activa de {len(matriz)} x {len(matriz[0])}."


def mostrar_opciones(opciones):
    print()
    for opcion in opciones:
        print(f"  {opcion}")
    print()


def mostrar_menu(matriz):
    consola.titulo("PRÁCTICA DE MATRICES")
    mostrar_opciones(_OPCIONES)
    consola.info(describir_matriz_activa(matriz))
    consola.info("Los índices de filas y columnas empiezan en 1.")


def mostrar_submenu_sistemas():
    consola.titulo("Crear sistema de ecuaciones")
    mostrar_opciones(_OPCIONES_SISTEMA)


def crear_sistema():
    """Devuelve la matriz aumentada creada, o None si no se creo ninguna."""
    while True:
        mostrar_submenu_sistemas()
        opcion = consola.pedir("Selecciona una opción: ").strip()

        # Volver deja intacta la matriz activa.
        if opcion == "3":
            return None

        consola.limpiar_pantalla()

        if opcion == "1":
            return crear_sistema_directo()
        if opcion == "2":
            return crear_sistema_manual()

        consola.error("Error: Selección inválida.")
        consola.pausar()
        consola.limpiar_pantalla()


def ejecutar_menu():
    matriz = []
    consola.limpiar_pantalla()

    while True:
        mostrar_menu(matriz)
        opcion = consola.pedir("\nSelecciona una opción: ").strip()

        if opcion == "9":
            break

        consola.limpiar_pantalla()

        match opcion:
            case "1": matriz = generador_matriz()
            case "2": matriz = crear_matriz()
            case "3":
                sistema = crear_sistema()
                # Solo un sistema creado correctamente reemplaza la matriz.
                if sistema is not None:
                    matriz = sistema
            case "4": modificar_elemento(matriz)
            case "5": consultar_elemento(matriz)
            case "6": mostrar_matriz(matriz)
            case "7": resolver_por_gauss(matriz)
            case "8": resolver_por_gauss_jordan(matriz)
            case _: consola.error("Error: Selección inválida.")

        consola.pausar()
        consola.limpiar_pantalla()

    consola.exito("Hasta luego.")
    consola.restablecer()
