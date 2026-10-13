"""Compara el trabajo de los procedimientos, sin calcular det(A) ni sus pasos.

Los costes son unidades de utilidad didáctica, no tiempos ni presupuestos.
Se prefieren los métodos de clase; reducción es la alternativa con intercambios
o el atajo cuando A ya es triangular superior.
"""

from backend.seguridad_numerica import dividir_exacto, multiplicar_exacto, restar_exacto

from .cofactores import ORDEN_MAXIMO_COFACTORES, elegir_expansion, menor
from .comun import preparar


def _costo_cofactores(a):
    """Cuenta sumas, productos y celdas de los menores que se desarrollan.

    Se reproduce la elección automática en cada menor. Los términos nulos
    solo cuentan su suma; sus menores no se calculan ni se muestran.
    """
    n = len(a)
    if n == 1:
        return 0
    eje, indice = elegir_expansion(a)
    costo = n  # El motor suma todos los términos, incluidos los nulos.
    for k in range(n):
        i, j = (indice, k) if eje == "fila" else (k, indice)
        if a[i][j]:
            m = menor(a, i, j)
            hijo = 0 if n == 2 else 3 if n == 3 else _costo_cofactores(m)
            costo += 2 + (n - 1) ** 2 + hijo
    return costo


def _analizar_lu(a):
    """Comprueba los pivotes del procedimiento sin construir L ni historiales.

    Se saltan columnas nulas sin avanzar la fila, igual que factorizar_lu.
    El coste incluye los cocientes de L, los reemplazos en U y su repetición
    sobre L para verificar L→I, además del producto final de la diagonal.
    """
    u = [fila[:] for fila in a]
    n, fila_pivote, costo = len(a), 0, len(a)
    try:
        for columna in range(n):
            pivote = u[fila_pivote][columna]
            if pivote == 0:
                if any(u[i][columna] for i in range(fila_pivote + 1, n)):
                    return {"aplicable": False, "costo": None,
                            "pivote_nulo": {"fila": fila_pivote + 1, "columna": columna + 1}}
                continue
            costo += n - fila_pivote
            for i in range(fila_pivote + 1, n):
                if u[i][columna]:
                    factor = dividir_exacto(u[i][columna], pivote)
                    u[i] = [restar_exacto(x, multiplicar_exacto(factor, y))
                            for x, y in zip(u[i], u[fila_pivote])]
                    costo += 4 * n
            fila_pivote += 1
        return {"aplicable": True, "costo": costo, "pivote_nulo": None}
    except ValueError:
        # Un límite numérico no demuestra que LU necesite intercambiar filas.
        return {"aplicable": None, "costo": None, "pivote_nulo": None}


def analizar_matriz_para_determinante(a):
    """Devuelve método recomendado, código de razón y datos comprobables.

    A debe ser cuadrada y exacta, con los mismos límites que el cálculo.
    No se modifica A, no se ejecuta ningún motor de determinantes y no se
    genera un resultado matemático. El servicio web traduce la razón a texto.
    """
    a = preparar(a)
    n = len(a)
    eje, indice = elegir_expansion(a)
    linea = a[indice] if eje == "fila" else [fila[indice] for fila in a]
    expansion = {"eje": eje, "indice": indice + 1, "ceros": sum(v == 0 for v in linea)}
    costos = {}
    datos_lu = None
    if n == 1:
        metodo, razon = "cofactores", "unico_elemento"
    elif n == 2:
        metodo, razon = "directo_2x2", "formula_directa"
    elif (all(a[i][j] == 0 for i in range(n) for j in range(i))
          and all(a[i][i] != 0 for i in range(n - 1))):
        # Un cero anterior al último pivote puede desplazar la fila al saltar columnas.
        metodo, razon = "reduccion", "triangular_superior"
    else:
        if n <= ORDEN_MAXIMO_COFACTORES:
            costos["cofactores"] = _costo_cofactores(a)
        if n == 3:
            # Sarrus multiplica 18 factores, suma 6 productos y resta las sumas.
            costos["sarrus"] = 25
            metodo = min(costos, key=costos.get)
            razon = "expansion_favorable" if metodo == "cofactores" else "sarrus"
        else:
            datos_lu = _analizar_lu(a)
            costos["lu"] = datos_lu["costo"]
            # Cota: una división y 2n operaciones por reemplazo, más la diagonal.
            costos["reduccion"] = n + n * (n - 1) // 2 * (1 + 2 * n)
            alternativa = "lu" if datos_lu["aplicable"] is True else "reduccion"
            if "cofactores" in costos and costos["cofactores"] <= costos[alternativa]:
                metodo, razon = "cofactores", "expansion_favorable"
            else:
                metodo = alternativa
                razon = ("lu_sin_intercambios" if metodo == "lu" else
                         "lu_necesita_intercambio" if datos_lu["aplicable"] is False else "lu_no_verificada")
    return {"metodo_recomendado": metodo, "razon": razon, "expansion": expansion,
            "costos": costos, "lu": datos_lu}
