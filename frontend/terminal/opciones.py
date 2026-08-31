from backend.matrices import generar_matriz
from backend.parser_sistemas import SEPARADOR_ECUACIONES, parsear_sistema
from backend.sistemas import (
    resolver_sistema_gauss,
    resolver_sistema_gauss_jordan,
    validar_matriz_aumentada
)
from frontend.terminal import consola
from frontend.terminal.entradas import (
    pedir_dimensiones,
    pedir_elemento_matriz,
    pedir_indices,
    pedir_nuevo_numero,
    pedir_sistema_manual,
    pedir_texto_sistema
)
from frontend.terminal.salida import (
    formatear_numero,
    imprimir_matriz,
    imprimir_paso
)

_AVISO_INDICES = "Los índices de filas y columnas empiezan en 1."
_AVISO_COLUMNA_FINAL = (
    "La última columna se interpreta como los términos independientes."
)
_EJEMPLO_SISTEMA = "x1 - 3x2 - 5x3 = 0; x2 + x3 = 3"


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


def crear_sistema_directo():
    """Devuelve la matriz aumentada, o None si el texto no se pudo interpretar."""
    consola.titulo("Sistema escrito directamente")
    consola.info(f"Separa las ecuaciones con '{SEPARADOR_ECUACIONES}'.")
    consola.info(f"Ejemplo: {_EJEMPLO_SISTEMA}")

    try:
        matriz = parsear_sistema(pedir_texto_sistema())
    except ValueError as error:
        # Un texto inválido no reemplaza la matriz activa.
        consola.error(str(error))
        return None

    consola.exito("Sistema creado correctamente.")
    print()
    imprimir_matriz(matriz)
    return matriz


def crear_sistema_manual():
    consola.titulo("Sistema por coeficientes")

    matriz = pedir_sistema_manual()

    consola.exito("Sistema creado correctamente.")
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
    consola.exito(
        f"El elemento en la posición [{fila},{columna}] = "
        f"{formatear_numero(numero)}"
    )


def mostrar_matriz(matriz):
    if not validar_matriz(matriz):
        return

    consola.titulo("Matriz")
    print()
    imprimir_matriz(matriz)


def mostrar_pasos(pasos):
    if not pasos:
        consola.advertencia("No fue necesario realizar operaciones por filas.")
        return

    consola.subtitulo("Pasos realizados")
    print()
    for indice, paso in enumerate(pasos):
        consola.info(f"Paso {indice + 1}:")
        imprimir_paso(paso)
        print()


def mostrar_matriz_resultante(titulo, matriz):
    consola.subtitulo(titulo)
    print()
    imprimir_matriz(matriz)


def mostrar_sustitucion(pasos):
    consola.subtitulo("Sustitución regresiva")
    print()
    for paso in pasos:
        valor = formatear_numero(paso["valor"])
        if paso["expresion"] == valor:
            print(f"x{paso['variable']} = {valor}")
        else:
            print(f"x{paso['variable']} = {paso['expresion']} = {valor}")


def mostrar_resultado(clasificacion, soluciones):
    consola.subtitulo("Resultado")
    print()
    print(clasificacion)
    for indice, solucion in enumerate(soluciones):
        print(f"x{indice + 1} = {formatear_numero(solucion)}")


def validar_como_sistema(matriz):
    """La matriz activa solo se interpreta como sistema al pedir un método."""
    if not validar_matriz(matriz):
        return False

    es_valida, mensaje = validar_matriz_aumentada(matriz)
    if not es_valida:
        consola.error(mensaje)
        return False

    return True


def resolver_por_gauss(matriz):
    if not validar_como_sistema(matriz):
        return

    consola.titulo("Resolución por Gauss")
    consola.info(_AVISO_COLUMNA_FINAL)
    resultado = resolver_sistema_gauss(matriz)

    mostrar_pasos(resultado["pasos"])
    mostrar_matriz_resultante("Matriz escalonada", resultado["matriz_escalonada"])
    if resultado["pasos_sustitucion"]:
        mostrar_sustitucion(resultado["pasos_sustitucion"])
    mostrar_resultado(resultado["clasificacion"], resultado["soluciones"])


def resolver_por_gauss_jordan(matriz):
    if not validar_como_sistema(matriz):
        return

    consola.titulo("Resolución por Gauss-Jordan")
    consola.info(_AVISO_COLUMNA_FINAL)
    resultado = resolver_sistema_gauss_jordan(matriz)

    mostrar_pasos(resultado["pasos"])
    mostrar_matriz_resultante("Matriz reducida", resultado["matriz_reducida"])
    mostrar_resultado(resultado["clasificacion"], resultado["soluciones"])
