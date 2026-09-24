"""Contratos de aridad compartidos por cálculo y formularios."""

ARIDAD_VECTORES = {"suma": (2, None), "resta": (2, None), "escalar": (1, 1), "combinacion": (1, None)}
ARIDAD_MATRICES = {
    "suma": (2, None), "resta": (2, None), "producto": (2, None),
    "escalar": (1, 1), "traspuesta": (1, 1), "matriz_vector": (2, 2),
}


def exigir_aridad(cantidad, aridad):
    minimo, maximo = aridad
    if cantidad < minimo or (maximo is not None and cantidad > maximo):
        if minimo == maximo:
            raise ValueError(f"La operación requiere exactamente {minimo} {'operando' if minimo == 1 else 'operandos'}.")
        raise ValueError(f"La operación requiere al menos {minimo} operandos.")


def nombre_matriz(indice):
    """A … Z, AA …: nombres estables sin limitar la cantidad de matrices."""
    nombre = ""
    indice += 1
    while indice:
        indice, resto = divmod(indice - 1, 26)
        nombre = chr(65 + resto) + nombre
    return nombre
