"""Factorización exacta A = LU sin intercambios de filas.

Es independiente de Determinantes: devuelve L, U y los pasos para que otra
herramienta (por ejemplo, resolver Ax = b) pueda reutilizarlos.
"""

from fractions import Fraction

from backend.matrices import copiar_matriz, matriz_identidad, validar_matriz
from backend.operaciones_filas import reemplazar_fila
from backend.seguridad_numerica import dividir_exacto, validar_matriz_exacta


def factorizar_lu(a):
    """Devuelve `aplicable`, `l`, `u` y `pasos` de A = LU, sin modificar A.

    A puede ser m×n: L es m×m y U es m×n. Las columnas nulas se saltan sin
    avanzar la fila pivote. Si se necesitaría un intercambio, `aplicable` es
    False y `pivote_nulo` indica su posición (fila y columna, desde 1).

    Cada `etapa` conserva U antes de eliminar, el pivote, las entradas y sus
    cocientes (incluido pivote/pivote = 1), las posiciones de L y los reemplazos.
    La columna de L corresponde a la fila pivote, aunque U salte columnas.
    `verificacion` aplica los mismos reemplazos a L y conserva solo su estado
    final y la comparación exacta con I, sin otro historial de matrices.
    """
    valida, mensaje = validar_matriz(a)
    if not valida:
        raise ValueError(mensaje)
    validar_matriz_exacta(a)
    m, n = len(a), len(a[0])
    u = [[Fraction(valor) for valor in fila] for fila in a]
    l, pasos, etapas = matriz_identidad(m), [], []
    fila_pivote = 0
    for columna_pivote in range(n):
        if fila_pivote == m:
            break
        if u[fila_pivote][columna_pivote] == 0:
            if any(u[i][columna_pivote] for i in range(fila_pivote + 1, m)):
                # Un pivote cero detiene LU porque este método no intercambia filas.
                return {"aplicable": False, "l": l, "u": u, "pasos": pasos,
                        "etapas": etapas, "verificacion": None,
                        "pivote_nulo": {"fila": fila_pivote + 1, "columna": columna_pivote + 1}}
            # Columna ya nula bajo el pivote: no hay nada que eliminar.
            continue
        pivote = u[fila_pivote][columna_pivote]
        etapa = {"u_antes": copiar_matriz(u), "fila_pivote": fila_pivote + 1,
                 "columna_pivote": columna_pivote + 1, "pivote": pivote,
                 "columna_l": fila_pivote + 1, "entradas": [], "operaciones": []}
        # Se toman todos los cocientes antes de modificar la columna de U.
        for i in range(fila_pivote, m):
            entrada = u[i][columna_pivote]
            cociente = dividir_exacto(entrada, pivote)
            l[i][fila_pivote] = cociente
            etapa["entradas"].append({"fila": i + 1, "entrada": entrada,
                                      "cociente": cociente, "posicion_l": (i + 1, fila_pivote + 1)})
        for entrada in etapa["entradas"][1:]:
            if entrada["cociente"]:
                i = entrada["fila"] - 1
                reemplazar_fila(u, pasos, i, fila_pivote, entrada["cociente"])
                etapa["operaciones"].append({"fila": i + 1, "fila_pivote": fila_pivote + 1,
                                             "factor": entrada["cociente"],
                                             "operacion": pasos[-1]["operacion"]})
        etapas.append(etapa)
        fila_pivote += 1

    l_reducida, transitorio = copiar_matriz(l), []
    for etapa in etapas:
        for operacion in etapa["operaciones"]:
            reemplazar_fila(l_reducida, transitorio, operacion["fila"] - 1,
                            operacion["fila_pivote"] - 1, operacion["factor"])
            transitorio.clear()  # Solo se conserva la verificación final, no otro procedimiento.
    verificacion = {"l_reducida": l_reducida, "es_identidad": l_reducida == matriz_identidad(m),
                    "reemplazos": len(pasos)}
    return {"aplicable": True, "l": l, "u": u, "pasos": pasos, "etapas": etapas,
            "verificacion": verificacion, "pivote_nulo": None}
