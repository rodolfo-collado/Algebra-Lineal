lista = [[12, 34, 11], [45, 60, 11], [22, 51, 81]]


def pedir_indices():
    while True:
        try:
            fila = int(input("\nIngrese el índice de la fila: "))
            if fila <= 0 or fila > len(lista):
                print("Error: fila fuera de rango. Intenta de nuevo")
            else: break

        except (ValueError or TypeError):
            print("Error: Ingrese un numero valido.\n")
            continue

    while True:
        try:
            columna = int(input("Ingrese el índice de la columna: "))
            if columna <= 0 or columna > len(lista[0]):
                print("Error: columna fuera de rango. Intente de nuevo.\n")
            else: break

        except (ValueError or TypeError):
            print("\nError: Ingrese un numero valido.")
    return fila, columna



def mostrar_matriz(lista):
    print("\n--- Matriz Completa ---")
    for i in lista:
        print(*i)


while True:

    try:
        print("\n"
              "        \n=== PRÁCTICA DE MATRICES ===\n"
              "        \n"
              "--- opciones (índices empiezan en 1) ---\n"
              "    \n"
              "1. Modificar elemento\n"
              "2. Consultar elemento\n"
              "3. Ver matriz completa\n"
              "4. Salir\n"
              "    ")
        opcion = input("==> ").strip().lower()

        match opcion:
            case "1":
                fila, columna = pedir_indices()
                numero = int(input("Ingresa el nuevo número: "))
                lista[fila - 1][columna - 1] = numero
                print("\nElemento modificado correctamente")
            case "2":
                fila, columna = pedir_indices()
                numero = lista[fila - 1][columna - 1]
                print(f"\nEl elemento en la posición [{fila},{columna}] = {numero}")
            case "3":
                mostrar_matriz(lista)
            case "4":
                break
            case _:
                print("\nError: Selecciona una opcion válida")


    except TypeError:
        print("\nError: Input Inválido. Intente de nuevo.")
        continue