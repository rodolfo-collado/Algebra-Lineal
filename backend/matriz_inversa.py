"""Matriz inversa: Gauss-Jordan sobre [A | I] y la regla directa de las matrices 2×2.

Son dos métodos distintos, no dos lecturas del mismo cálculo:

- Gauss-Jordan sirve para cualquier matriz cuadrada. Coloca la identidad junto
  a A, reduce [A | I] con el motor de siempre (`aplicar_gauss_jordan`, con los
  pivotes limitados a las columnas de A) y lee el resultado: si el bloque
  izquierdo llegó a la identidad, el derecho es A⁻¹; si no, A no tiene inversa.
  No usa determinantes.
- La regla 2×2 calcula ad − bc y, si no es 0, A⁻¹ = 1/(ad − bc) · [[d, −b], [−c, a]].
  Esa escritura solo existe para matrices 2×2.

Toda la aritmética pasa por las operaciones exactas protegidas de
`backend.seguridad_numerica`. Este módulo es lógica pura: recibe listas de
enteros o Fraction y devuelve diccionarios con Fraction, o lanza ValueError con
un mensaje legible.
"""

from fractions import Fraction

from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import (
    aumentar_matrices, matriz_identidad, resolver_operacion_matrices,
    separar_bloques, validar_matriz, validar_vector, vector_columna,
)
from backend.seguridad_numerica import (
    dividir_exacto, multiplicar_exacto, restar_exacto, validar_matriz_exacta,
    validar_valor_exacto,
)

GAUSS_JORDAN = "gauss_jordan"
DIRECTO_2X2 = "directo_2x2"
METODO_PREDETERMINADO = GAUSS_JORDAN
FUNCIONES_ADICIONALES = ("ninguna", "inversa_inversa", "traspuesta", "producto", "vector")


def validar_matriz_cuadrada(a):
    """Devuelve (es_valida, mensaje): A no vacía, rectangular, con entradas exactas y cuadrada."""
    es_valida, mensaje = validar_matriz(a)
    if not es_valida:
        return False, mensaje
    filas, columnas = len(a), len(a[0])
    if filas != columnas:
        return False, f"Solo una matriz cuadrada puede tener inversa: A es {filas}×{columnas}."
    return True, ""


def _orden(a):
    es_valida, mensaje = validar_matriz_cuadrada(a)
    if not es_valida:
        raise ValueError(mensaje)
    return len(a)


def inversa_gauss_jordan(a):
    """Reduce [A | I] hasta [I | A⁻¹], o hasta ver que la izquierda no llega a I.

    Devuelve `metodo`, `orden` (n), `matriz` (A exacta), `aumentada` ([A | I]),
    los `pasos` y `pivotes` del motor, la matriz `reducida` y sus bloques
    `izquierda` y `derecha`, `invertible` (la izquierda es exactamente I_n) e
    `inversa` (el bloque derecho, o None). Con A cuadrada, llegar a I_n equivale
    a encontrar n pivotes; la comparación exacta es la evidencia que se muestra.
    """
    n = _orden(a)
    identidad = matriz_identidad(n)
    aumentada = aumentar_matrices(a, identidad)
    reducida, pasos, pivotes = aplicar_gauss_jordan(aumentada, columnas_pivote=n)
    izquierda, derecha = separar_bloques(reducida, n)
    invertible = izquierda == identidad
    return {
        "metodo": GAUSS_JORDAN,
        "orden": n,
        "matriz": [fila[:n] for fila in aumentada],
        "aumentada": aumentada,
        "pasos": pasos,
        "pivotes": pivotes,
        "reducida": reducida,
        "izquierda": izquierda,
        "derecha": derecha,
        "invertible": invertible,
        "inversa": derecha if invertible else None,
    }


def inversa_metodo_2x2(a):
    """Regla directa de A = [[a, b], [c, d]]: con ad − bc ≠ 0, A⁻¹ = 1/(ad − bc) · [[d, −b], [−c, a]].

    Devuelve `metodo`, `orden`, `matriz`, las `entradas` a, b, c y d, los
    productos `ad` y `bc`, su diferencia `ad_menos_bc`, la matriz
    `intercambiada` [[d, −b], [−c, a]], el `factor` 1/(ad − bc), `invertible` e
    `inversa`. Con ad − bc = 0 no hay factor ni inversa.
    """
    if _orden(a) != 2:
        raise ValueError("El método para matrices 2×2 solo se aplica a matrices 2×2.")
    validar_matriz_exacta(a)
    (a11, a12), (a21, a22) = ([Fraction(valor) for valor in fila] for fila in a)
    ad = multiplicar_exacto(a11, a22)
    bc = multiplicar_exacto(a12, a21)
    ad_menos_bc = restar_exacto(ad, bc)
    # Cambiar el signo conserva el tamaño del número: no necesita otra validación.
    intercambiada = [[a22, -a12], [-a21, a11]]
    factor = inversa = None
    if ad_menos_bc != 0:
        factor = dividir_exacto(1, ad_menos_bc)
        inversa = [[multiplicar_exacto(factor, valor) for valor in fila] for fila in intercambiada]
    return {
        "metodo": DIRECTO_2X2,
        "orden": 2,
        "matriz": [[a11, a12], [a21, a22]],
        "entradas": {"a": a11, "b": a12, "c": a21, "d": a22},
        "ad": ad,
        "bc": bc,
        "ad_menos_bc": ad_menos_bc,
        "intercambiada": intercambiada,
        "factor": factor,
        "invertible": inversa is not None,
        "inversa": inversa,
    }


METODOS = {GAUSS_JORDAN: inversa_gauss_jordan, DIRECTO_2X2: inversa_metodo_2x2}


def calcular_inversa(a, metodo=METODO_PREDETERMINADO):
    """Calcula la inversa con el método pedido; el 2×2 rechaza cualquier otro tamaño."""
    try:
        calcular = METODOS[metodo]
    except (KeyError, TypeError):
        raise ValueError(
            "Selecciona un método válido: Gauss-Jordan o el método para matrices 2×2."
        ) from None
    return calcular(a)


def verificar_inversa(a, inversa):
    """Comprueba A·A⁻¹ = I y A⁻¹·A = I con la inversa recibida, sin recalcularla.

    A y la candidata a inversa deben ser matrices cuadradas del mismo orden,
    con enteros o Fraction. Ambos productos reutilizan el motor común y sus
    operaciones exactas protegidas. No modifica ninguna entrada.

    Devuelve `identidad`, los productos `a_por_inversa` e `inversa_por_a`,
    las comparaciones exactas `a_por_inversa_es_identidad` e
    `inversa_por_a_es_identidad` y `verificada` (ambas coincidieron). Conserva
    la evidencia del motor en `detalles_a_por_inversa` y
    `detalles_inversa_por_a`, sin exigir que la candidata sea correcta.
    """
    n = _orden(a)
    if _orden(inversa) != n:
        raise ValueError("A y su inversa deben ser matrices cuadradas del mismo orden.")
    identidad = matriz_identidad(n)
    producto_a_inversa = resolver_operacion_matrices("producto", a=a, b=inversa)
    producto_inversa_a = resolver_operacion_matrices("producto", a=inversa, b=a)
    a_por_inversa = producto_a_inversa["resultado"]
    inversa_por_a = producto_inversa_a["resultado"]
    a_por_inversa_es_identidad = a_por_inversa == identidad
    inversa_por_a_es_identidad = inversa_por_a == identidad
    return {
        "identidad": identidad,
        "a_por_inversa": a_por_inversa,
        "inversa_por_a": inversa_por_a,
        "a_por_inversa_es_identidad": a_por_inversa_es_identidad,
        "inversa_por_a_es_identidad": inversa_por_a_es_identidad,
        "verificada": a_por_inversa_es_identidad and inversa_por_a_es_identidad,
        "detalles_a_por_inversa": producto_a_inversa,
        "detalles_inversa_por_a": producto_inversa_a,
    }


def _validar_metodo_adicional(metodo, n):
    if not isinstance(metodo, str) or metodo not in METODOS:
        raise ValueError("Selecciona un método válido: Gauss-Jordan o el método para matrices 2×2.")
    if metodo == DIRECTO_2X2 and n != 2:
        raise ValueError("El método para matrices 2×2 solo se aplica a matrices 2×2.")


def _preparar_funcion(a, inversa, funcion, metodo=METODO_PREDETERMINADO):
    """Valida la A⁻¹ recibida; None indica que el cálculo principal fue singular."""
    n = _orden(a)
    validar_matriz_exacta(a)
    _validar_metodo_adicional(metodo, n)
    if inversa is not None:
        if _orden(inversa) != n:
            raise ValueError("A y su inversa deben ser matrices cuadradas del mismo orden.")
        validar_matriz_exacta(inversa)
    motivo = ""
    if inversa is None:
        motivo = (
            "No se puede usar x = A⁻¹b porque A no tiene inversa."
            if funcion == "vector" else
            "No se puede aplicar esta propiedad porque A no tiene inversa."
        )
    return n, {
        "funcion": funcion, "aplicable": inversa is not None,
        "motivo": motivo, "resultado": None,
    }


def inversa_de_inversa(a, inversa, metodo=METODO_PREDETERMINADO):
    """Invierte únicamente la A⁻¹ recibida y compara su resultado exacto con A.

    Conserva la segunda inversión completa en `calculo_inversa_de_inversa`
    para explicar sus pasos. Una candidata incorrecta no se da por cierta.
    """
    _, datos = _preparar_funcion(a, inversa, "inversa_inversa", metodo)
    if not datos["aplicable"]:
        return datos
    calculo = calcular_inversa(inversa, metodo)
    resultado = calculo["inversa"]
    return {
        **datos,
        "aplicable": calculo["invertible"],
        "motivo": "" if calculo["invertible"] else "La matriz recibida como A⁻¹ no tiene inversa.",
        "resultado": resultado,
        "calculo_inversa_de_inversa": calculo,
        "inversa_de_inversa": resultado,
        "coincide_con_a": resultado == a,
    }


def propiedad_traspuesta(a, inversa, metodo=METODO_PREDETERMINADO):
    """Calcula ambos lados de (Aᵀ)⁻¹ = (A⁻¹)ᵀ con los motores compartidos."""
    _, datos = _preparar_funcion(a, inversa, "traspuesta", metodo)
    if not datos["aplicable"]:
        return datos
    traspuesta_a = resolver_operacion_matrices("traspuesta", a=a)
    calculo_inversa = calcular_inversa(traspuesta_a["resultado"], metodo)
    traspuesta_inversa = resolver_operacion_matrices("traspuesta", a=inversa)
    resultado = calculo_inversa["inversa"]
    return {
        **datos,
        "aplicable": calculo_inversa["invertible"],
        "motivo": "" if calculo_inversa["invertible"] else "Aᵀ no tiene inversa.",
        "resultado": resultado,
        "calculo_traspuesta_a": traspuesta_a,
        "traspuesta_a": traspuesta_a["resultado"],
        "calculo_inversa_traspuesta": calculo_inversa,
        "inversa_traspuesta": resultado,
        "calculo_traspuesta_inversa": traspuesta_inversa,
        "traspuesta_inversa": traspuesta_inversa["resultado"],
        "coinciden": resultado == traspuesta_inversa["resultado"],
    }


def propiedad_producto(a, inversa, b, metodo=METODO_PREDETERMINADO):
    """Calcula (AB)⁻¹ y B⁻¹A⁻¹ sin volver a invertir A.

    B debe ser cuadrada del mismo orden. Si B es singular devuelve una
    condición matemática no aplicable y su inversión, sin productos posteriores.
    """
    n, datos = _preparar_funcion(a, inversa, "producto", metodo)
    if _orden(b) != n:
        raise ValueError("A y B deben ser matrices cuadradas del mismo orden.")
    validar_matriz_exacta(b)
    if not datos["aplicable"]:
        return datos
    calculo_b = calcular_inversa(b, metodo)
    datos.update({
        "calculo_inversa_b": calculo_b, "inversa_b": calculo_b["inversa"],
        "b_invertible": calculo_b["invertible"],
    })
    if not calculo_b["invertible"]:
        datos.update({
            "aplicable": False,
            "motivo": "La propiedad del producto no puede aplicarse porque B no tiene inversa.",
        })
        return datos
    producto_ab = resolver_operacion_matrices("producto", a=a, b=b)
    calculo_ab = calcular_inversa(producto_ab["resultado"], metodo)
    producto_inversas = resolver_operacion_matrices("producto", a=calculo_b["inversa"], b=inversa)
    resultado = calculo_ab["inversa"]
    return {
        **datos,
        "aplicable": calculo_ab["invertible"],
        "motivo": "" if calculo_ab["invertible"] else "AB no tiene inversa.",
        "resultado": resultado,
        "calculo_producto_ab": producto_ab, "producto_ab": producto_ab["resultado"],
        "calculo_inversa_producto": calculo_ab, "inversa_producto": resultado,
        "calculo_producto_inversas": producto_inversas,
        "producto_inversas": producto_inversas["resultado"],
        "coinciden": resultado == producto_inversas["resultado"],
    }


def resolver_por_inversa(a, inversa, b):
    """Obtiene x = A⁻¹b y comprueba Ax = b mediante dos productos matriz-vector.

    Recibe b como lista plana de n componentes. Devuelve `b`, `x` y
    `a_por_x` como columnas n×1 junto con ambas evidencias del motor común.
    No reduce [A | b] ni llama al solver de sistemas.
    """
    n, datos = _preparar_funcion(a, inversa, "vector")
    valido, mensaje = validar_vector(b, "b")
    if not valido:
        raise ValueError(mensaje)
    if len(b) != n:
        raise ValueError(f"El vector b debe tener {n} componentes, una por fila de A.")
    for valor in b:
        validar_valor_exacto(valor)
    if not datos["aplicable"]:
        return datos
    calculo_x = resolver_operacion_matrices("matriz_vector", a=inversa, vector=b)
    x = calculo_x["resultado"]
    calculo_ax = resolver_operacion_matrices("matriz_vector", a=a, vector=[fila[0] for fila in x])
    columna_b = vector_columna(b)
    return {
        **datos, "resultado": x, "b": columna_b, "x": x,
        "a_por_x": calculo_ax["resultado"],
        "calculo_inversa_por_b": calculo_x, "calculo_a_por_x": calculo_ax,
        "coincide_con_b": calculo_ax["resultado"] == columna_b,
    }


def aplicar_funcion_adicional(funcion, a, inversa, metodo=METODO_PREDETERMINADO, b=None, vector=None):
    """Ejecuta una opción del contrato cerrado sobre la inversa ya calculada.

    Los operandos adicionales solo se admiten para su opción: B para producto,
    vector plano para la aplicación Ax = b. Todas las nuevas inversiones usan
    el método recibido. Devuelve `funcion`, `aplicable`, `motivo`, `resultado`
    y la evidencia específica de la opción; no construye presentación.
    """
    if not isinstance(funcion, str) or funcion not in FUNCIONES_ADICIONALES:
        raise ValueError("Selecciona una función adicional válida.")
    if b is not None and funcion != "producto":
        raise ValueError("La matriz B solo se admite para la propiedad del producto.")
    if vector is not None and funcion != "vector":
        raise ValueError("El vector b solo se admite para la aplicación Ax = b.")
    if funcion == "producto":
        if b is None:
            raise ValueError("La propiedad del producto requiere la matriz B.")
        return propiedad_producto(a, inversa, b, metodo)
    if funcion == "vector":
        if vector is None:
            raise ValueError("La aplicación Ax = b requiere el vector b.")
        _validar_metodo_adicional(metodo, _orden(a))
        return resolver_por_inversa(a, inversa, vector)
    funciones = {"inversa_inversa": inversa_de_inversa, "traspuesta": propiedad_traspuesta}
    if funcion in funciones:
        return funciones[funcion](a, inversa, metodo)
    _, datos = _preparar_funcion(a, inversa, funcion, metodo)
    if inversa is not None:
        datos["resultado"] = [[Fraction(valor) for valor in fila] for fila in inversa]
    return datos
