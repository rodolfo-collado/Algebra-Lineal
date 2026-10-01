"""Contratos de aridad compartidos por cálculo y formularios."""

ARIDAD_VECTORES = {"suma": (2, None), "resta": (2, None), "escalar": (1, 1), "combinacion": (1, None)}
ARIDAD_MATRICES = {
    "suma": (2, None), "resta": (2, None), "producto": (2, None),
    "escalar": (1, 1), "traspuesta": (1, 1), "matriz_vector": (2, 2),
}

# Presupuesto de entrada de la interfaz, no un límite matemático: el cálculo acepta
# colecciones de cualquier tamaño, pero los formularios crean un campo por celda a
# partir de la cantidad que envía el navegador y la acotan antes de construirlos.
# 50 operandos con 900 celdas, más sus controles de estructura, caben en los 1000
# campos por envío que admite Django (DATA_UPLOAD_MAX_NUMBER_FIELDS): lo que la
# interfaz dibuja siempre se puede enviar.
OPERANDOS_MAXIMOS = 50
CELDAS_MAXIMAS = 900
# Un formulario de símbolos (Operaciones con matrices) envía además el nombre, el
# tipo y las dimensiones de cada símbolo: hasta 4 campos por matriz. Estructura y
# celdas no superan este tope, que deja margen para los controles fijos (csrf,
# expresión, cantidad, presentación y el botón pulsado) dentro de los 1000 campos
# de Django. Con 50 matrices, 200 campos son de estructura: caben 790 celdas.
CAMPOS_MAXIMOS = 990


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
