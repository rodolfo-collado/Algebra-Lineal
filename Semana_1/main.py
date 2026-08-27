from opciones_menu import (
    consultar_elemento,
    crear_matriz,
    generador_matriz,
    modificar_elemento,
    mostrar_matriz,
    resolver_gauss_jordan_menu
)

matriz = []
while True:
    print("\n"
          "-----------------------------------------"
          "        \n==== PRÁCTICA DE MATRICES ====\n"
          "        \n"
          "--- opciones (índices empiezan en 1) ---\n"
          "    \n"
          "1. Generar matriz\n"
          "2. Crear matriz\n"
          "3. Modificar elemento\n"
          "4. Consultar elemento\n"
          "5. Ver matriz completa\n"
          "6. Resolver por Gauss-Jordan\n"
          "7. Salir\n"
          "    ")
    opcion = input("==> ").strip()

    match opcion:
        case "1": matriz = generador_matriz()
        case "2": matriz = crear_matriz()
        case "3": modificar_elemento(matriz)
        case "4": consultar_elemento(matriz)
        case "5": mostrar_matriz(matriz)
        case "6": resolver_gauss_jordan_menu(matriz)
        case "7": break
        case _: print("\nError: Selección inválida.")
