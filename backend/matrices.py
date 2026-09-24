"""Utilidades generales sobre matrices, independientes de cualquier algoritmo.

Las filas y las columnas son vectores (listas de números exactos), así que aquí
viven también la validación de un vector y el producto punto: la primitiva con
la que se construyen los productos AB y Ax.
"""

import random
from fractions import Fraction

from backend.operandos import ARIDAD_MATRICES, exigir_aridad, nombre_matriz


def generar_matriz(cantidad_filas, cantidad_columnas):
    matriz = []

    # Ciclo para generar la matriz
    for _ in range(cantidad_filas):
        fila = []
        for _ in range(cantidad_columnas):
            fila.append(random.randint(0, 20))
        matriz.append(fila)

    return matriz


def copiar_matriz(matriz):
    copia = []

    for fila in matriz:
        copia.append(fila.copy())

    return copia


def convertir_matriz_a_fracciones(matriz):
    matriz_fracciones = []

    for fila in matriz:
        nueva_fila = []
        for numero in fila:
            nueva_fila.append(Fraction(numero))
        matriz_fracciones.append(nueva_fila)

    return matriz_fracciones


def es_matriz_rectangular(matriz):
    # Una matriz sin filas no tiene forma que comprobar.
    if not isinstance(matriz, (list, tuple)) or not matriz:
        return False
    if any(not isinstance(fila, (list, tuple)) for fila in matriz):
        return False

    cantidad_columnas = len(matriz[0])
    for fila in matriz:
        if len(fila) != cantidad_columnas:
            return False

    return True


def validar_matriz_rectangular(matriz):
    """Devuelve (es_valida, mensaje). Acepta cualquier matriz rectangular no vacia."""
    if not matriz:
        return False, "Error: La matriz está vacía."

    if not es_matriz_rectangular(matriz):
        return False, "Error: La matriz no es rectangular."

    if len(matriz[0]) == 0:
        return False, "Error: La matriz no tiene columnas."

    return True, ""


def formatear_fraccion(numero):
    if numero.denominator == 1:
        return str(numero.numerator)
    return f"{numero.numerator}/{numero.denominator}"


def validar_matriz(matriz):
    """Forma rectangular no vacía y entradas exactas; sin límites de interfaz."""
    valida, mensaje = validar_matriz_rectangular(matriz)
    if not valida:
        return valida, mensaje
    for fila in matriz:
        for valor in fila:
            if isinstance(valor, bool) or not isinstance(valor, (int, Fraction)):
                return False, "Cada entrada de la matriz debe ser un número exacto."
    return True, ""


def _exigir_matriz(matriz):
    valida, mensaje = validar_matriz(matriz)
    if not valida:
        raise ValueError(mensaje)


def validar_vector(vector, nombre=None):
    """Devuelve (es_valido, mensaje). Un vector necesita al menos una componente."""
    sujeto = f"El vector {nombre}" if nombre else "El vector"
    if not isinstance(vector, (list, tuple)):
        return False, f"{sujeto} debe ser una lista de componentes."

    if len(vector) == 0:
        return False, f"{sujeto} no tiene componentes."

    for componente in vector:
        if isinstance(componente, bool) or not isinstance(componente, (int, Fraction)):
            return False, f"{sujeto} tiene una componente que no es un número."

    return True, ""


def _exigir_vector(vector, nombre):
    valido, mensaje = validar_vector(vector, nombre)
    if not valido:
        raise ValueError(mensaje)


def contar(cantidad, singular):
    """«1 fila», «3 columnas»: cuenta con plural para los mensajes de dimensiones."""
    return f"{cantidad} {singular}{'' if cantidad == 1 else 's'}"


def dimensiones(matriz):
    """Dimensiones (filas, columnas) de una matriz válida."""
    _exigir_matriz(matriz)
    return len(matriz), len(matriz[0])


def _operar_entradas(a, b, signo):
    forma_a, forma_b = dimensiones(a), dimensiones(b)
    if forma_a != forma_b:
        raise ValueError(
            "Para sumar o restar, ambas matrices deben tener las mismas dimensiones: "
            f"A es {forma_a[0]}×{forma_a[1]} y B es {forma_b[0]}×{forma_b[1]}."
        )
    return [
        [Fraction(x) + signo * Fraction(y) for x, y in zip(fila_a, fila_b)]
        for fila_a, fila_b in zip(a, b)
    ]


def sumar_matrices(a, b):
    """C[i][j] = A[i][j] + B[i][j], con dimensiones iguales, incluso rectangulares."""
    return _operar_entradas(a, b, 1)


def restar_matrices(a, b):
    """C[i][j] = A[i][j] - B[i][j], sin modificar las entradas."""
    return _operar_entradas(a, b, -1)


def multiplicar_escalar_matriz(escalar, matriz):
    """Multiplica cada entrada por un entero o Fraction."""
    _exigir_matriz(matriz)
    if isinstance(escalar, bool) or not isinstance(escalar, (int, Fraction)):
        raise ValueError("El escalar debe ser un número exacto.")
    return [[Fraction(escalar) * Fraction(valor) for valor in fila] for fila in matriz]


def trasponer_matriz(matriz):
    """Intercambia filas y columnas: una matriz m×n produce una matriz n×m."""
    filas, columnas = dimensiones(matriz)
    return [[Fraction(matriz[i][j]) for i in range(filas)] for j in range(columnas)]


def vector_columna(vector):
    """Escribe un vector de n componentes como matriz n×1."""
    _exigir_vector(vector, "x")
    return [[Fraction(componente)] for componente in vector]


def producto_punto(u, v):
    """u · v = u₁v₁ + u₂v₂ + … + uₙvₙ, con la misma dimensión y aritmética exacta.

    Cada entrada de un producto de matrices es el producto punto de una fila
    de A con una columna de B; esta es la única suma de productos del módulo.
    """
    _exigir_vector(u, "u")
    _exigir_vector(v, "v")
    if len(u) != len(v):
        raise ValueError(
            "El producto punto necesita dos vectores de la misma dimensión: "
            f"u tiene {contar(len(u), 'componente')} y v tiene {contar(len(v), 'componente')}."
        )

    resultado = Fraction(0)
    for componente_u, componente_v in zip(u, v):
        resultado += Fraction(componente_u) * Fraction(componente_v)

    return resultado


def multiplicar_matrices(a, b):
    """C = AB con cᵢⱼ = filaᵢ(A) · columnaⱼ(B); A m×n y B n×p dan C m×p.

    No exige matrices cuadradas ni del mismo tamaño: solo que las columnas de A
    coincidan con las filas de B. No modifica las entradas.
    """
    (_, columnas_a), (filas_b, _) = dimensiones(a), dimensiones(b)
    if columnas_a != filas_b:
        raise ValueError(
            f"No se puede calcular AB: A tiene {contar(columnas_a, 'columna')} y B tiene "
            f"{contar(filas_b, 'fila')}. Para multiplicar matrices, esos valores deben coincidir."
        )
    # Las columnas de B son las filas de su traspuesta.
    columnas_b = trasponer_matriz(b)
    return [[producto_punto(fila, columna) for columna in columnas_b] for fila in a]


def multiplicar_matriz_vector(a, x):
    """Ax: A m×n por un vector x de n componentes; devuelve las m componentes de Ax.

    Es el mismo producto AB con B = [x] escrito como columna n×1: no hay un
    segundo motor. Cambian la validación y la forma de explicarlo.
    """
    _, columnas_a = dimensiones(a)
    _exigir_vector(x, "x")
    if len(x) != columnas_a:
        raise ValueError(
            f"No se puede calcular Ax: A tiene {contar(columnas_a, 'columna')} y x tiene "
            f"{contar(len(x), 'componente')}. Para multiplicar, esos valores deben coincidir."
        )
    return [fila[0] for fila in multiplicar_matrices(a, vector_columna(x))]


def _pasos_producto(a, b, resultado):
    """Los productos aᵢₖbₖⱼ se calculan una vez y se agrupan de dos maneras.

    `pasos[i][j]` explica cada entrada como fila por columna; `columnas[j]`
    explica cada columna del resultado como combinación lineal de las columnas
    de A con los coeficientes de la columna j de B. Son las mismas cantidades,
    así que ambos procedimientos conducen exactamente al mismo resultado.
    """
    filas_a, comunes = dimensiones(a)
    columnas_de_a = trasponer_matriz(a)
    columnas_de_b = trasponer_matriz(b)
    productos = [
        [[Fraction(a[i][k]) * Fraction(b[k][j]) for k in range(comunes)] for j in range(len(columnas_de_b))]
        for i in range(filas_a)
    ]
    pasos = [
        [
            {
                "posicion": (i + 1, j + 1),
                "fila": tuple(Fraction(valor) for valor in a[i]),
                "columna": tuple(columnas_de_b[j]),
                "productos": tuple(productos[i][j]),
                "resultado": resultado[i][j],
            }
            for j in range(len(columnas_de_b))
        ]
        for i in range(filas_a)
    ]
    columnas = [
        {
            "posicion": j + 1,
            "coeficientes": tuple(columnas_de_b[j]),
            "escaladas": tuple(tuple(productos[i][j][k] for i in range(filas_a)) for k in range(comunes)),
            "resultado": tuple(resultado[i][j] for i in range(filas_a)),
        }
        for j in range(len(columnas_de_b))
    ]
    return {
        "pasos": pasos, "columnas": columnas,
        "columnas_a": tuple(tuple(columna) for columna in columnas_de_a),
    }


def resolver_coleccion_matrices(operacion, matrices):
    """Opera una colección; cada etapa del producto reutiliza ambas evidencias."""
    if operacion not in ("suma", "resta", "producto"):
        raise ValueError("Selecciona suma, resta o producto de matrices.")
    matrices = list(matrices)
    exigir_aridad(len(matrices), ARIDAD_MATRICES[operacion])
    # Validar todas antes de calcular evita procedimientos parciales inválidos.
    formas = [dimensiones(matriz) for matriz in matrices]
    for i in range(1, len(matrices)):
        compatibles = formas[i - 1][1] == formas[i][0] if operacion == "producto" else formas[0] == formas[i]
        if not compatibles:
            raise ValueError(
                f"Dimensiones incompatibles entre {nombre_matriz(i - 1) if operacion == 'producto' else 'A'} "
                f"y {nombre_matriz(i)}: "
                + ("las columnas de la anterior deben coincidir con las filas de la siguiente."
                   if operacion == "producto" else "las matrices deben tener las mismas dimensiones.")
            )
    acumulado = matrices[0]
    etapas = []
    for matriz in matrices[1:]:
        calculo = resolver_operacion_matrices(operacion, acumulado, matriz)
        if operacion == "producto":
            etapas.append({"izquierda": acumulado, "derecha": matriz, "calculo": calculo})
        acumulado = calculo["resultado"]
    if operacion == "producto":
        return {**calculo, "etapas": etapas}
    for i, fila in enumerate(calculo["pasos"]):
        for j, paso in enumerate(fila):
            paso["operandos"] = tuple(Fraction(matriz[i][j]) for matriz in matrices)
    return calculo


def resolver_operacion_matrices(operacion, a, b=None, escalar=None, vector=None):
    """Resultado y evidencia estructurada, como datos exactos sin presentación.

    Los índices de los pasos empiezan en 1. En la traspuesta se conserva la
    posición de origen para explicar cómo cada fila pasa a ser una columna. En
    AB y Ax se entregan las dos lecturas equivalentes del mismo producto.
    """
    if operacion in ("producto", "matriz_vector"):
        if operacion == "producto":
            resultado = multiplicar_matrices(a, b)
        else:
            resultado = vector_columna(multiplicar_matriz_vector(a, vector))
            b = vector_columna(vector)
        return {
            "operacion": operacion, "resultado": resultado, **_pasos_producto(a, b, resultado),
            "dimensiones_entrada": dimensiones(a),
            "dimensiones_b": dimensiones(b),
            "dimensiones_resultado": dimensiones(resultado),
        }

    if operacion == "suma":
        resultado = sumar_matrices(a, b)
    elif operacion == "resta":
        resultado = restar_matrices(a, b)
    elif operacion == "escalar":
        resultado = multiplicar_escalar_matriz(escalar, a)
    elif operacion == "traspuesta":
        resultado = trasponer_matriz(a)
    else:
        raise ValueError("Selecciona una operación de matrices válida.")

    pasos = []
    for i, fila in enumerate(resultado):
        pasos_fila = []
        for j, valor in enumerate(fila):
            origen = (j + 1, i + 1) if operacion == "traspuesta" else (i + 1, j + 1)
            if operacion in ("suma", "resta"):
                operandos = (Fraction(a[i][j]), Fraction(b[i][j]))
            elif operacion == "escalar":
                operandos = (Fraction(escalar), Fraction(a[i][j]))
            else:
                operandos = (Fraction(a[j][i]),)
            pasos_fila.append({
                "posicion": (i + 1, j + 1), "origen": origen,
                "operandos": operandos, "resultado": valor,
            })
        pasos.append(pasos_fila)
    return {
        "operacion": operacion, "resultado": resultado, "pasos": pasos,
        "dimensiones_entrada": dimensiones(a),
        "dimensiones_resultado": dimensiones(resultado),
    }
