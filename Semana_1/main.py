from opciones_menu import (
    consultar_elemento,
    crear_matriz,
    crear_sistema_ecuaciones,
    generador_matriz,
    modificar_elemento,
    mostrar_matriz,
    resolver_gauss_jordan_menu,
    resolver_gauss_menu
)


matriz = []

while True:
    print(
        "\n"
        "-----------------------------------------"
        "        \n==== PRÁCTICA DE MATRICES ====\n"
        "        \n--- opciones (índices empiezan en 1) ---\n"
        "    \n"
        "1. Generar matriz\n"
        "2. Crear matriz\n"
        "3. Crear sistema de ecuaciones\n"
        "4. Modificar elemento\n"
        "5. Consultar elemento\n"
        "6. Ver matriz completa\n"
        "7. Resolver por Gauss\n"
        "8. Resolver por Gauss-Jordan\n"
        "9. Salir\n"
        "    "
    )
    opcion = input("==> ").strip()

    match opcion:
        case "1":
            matriz = generador_matriz()
        case "2":
            matriz = crear_matriz()
        case "3":
            matriz = crear_sistema_ecuaciones()
        case "4":
            modificar_elemento(matriz)
        case "5":
            consultar_elemento(matriz)
        case "6":
            mostrar_matriz(matriz)
        case "7":
            resolver_gauss_menu(matriz)
        case "8":
            resolver_gauss_jordan_menu(matriz)
        case "9":
            break
        case _:
            print("\nError: Selección inválida.")
