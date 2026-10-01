"""Presentación de «Matriz inversa»: estimar, confirmar si hace falta y formatear.

No calcula: `backend.matriz_inversa` resuelve con Gauss-Jordan sobre [A | I] o
con la regla 2×2, y aquí se adaptan sus datos exactos a la plantilla. Antes de
ejecutar Gauss-Jordan se estima su costo con `presupuesto_computacional`: una
estimación pesada no calcula hasta que el usuario confirma con «Continuar».
"""

from django.utils.crypto import constant_time_compare, salted_hmac

from backend.matriz_inversa import DIRECTO_2X2, GAUSS_JORDAN, calcular_inversa
from backend.presupuesto_computacional import (
    Categoria, categoria, estimar_gauss_jordan, intervalo_segundos, perfil_numerico,
)

from .presentacion_numerica import formatear_exacto
from .servicios import adaptar_pasos, formatear_matriz
from .servicios_bases import enumerar
from .servicios_matrices import _operando, _sumando
from .servicios_presupuesto import texto_intervalo

METODOS = ((GAUSS_JORDAN, "Gauss-Jordan"), (DIRECTO_2X2, "Método para matrices 2×2"))

# La regla general con letras; los valores concretos llegan del backend.
SIMBOLICA = [["a", "b"], ["c", "d"]]
SIMBOLICA_INTERCAMBIADA = [["d", "−b"], ["−c", "a"]]

# Por qué A no tiene inversa, según el método: lo que el usuario acaba de ver en el procedimiento.
NO_INVERTIBLE = {
    GAUSS_JORDAN: "Con Gauss-Jordan, el lado izquierdo no pudo convertirse en la matriz identidad: A es una matriz no invertible.",
    DIRECTO_2X2: "Como ad − bc = 0, A es una matriz no invertible.",
}

MENSAJES_ESPERA = {
    Categoria.PESADA: "Esta operación puede tardar varios segundos porque la matriz requiere un procedimiento largo.",
    Categoria.MUY_PESADA: "Esta operación puede tardar bastante porque la matriz requiere un procedimiento muy largo.",
}
_SAL_CONFIRMACION = "pygebra.matriz-inversa.confirmacion"


def estimar_inversa_web(entrada):
    """Costo previsto de Gauss-Jordan sobre [A | I], sin calcular; None con la regla 2×2.

    La regla 2×2 hace unas pocas operaciones y nunca pide confirmación.
    """
    if entrada["metodo"] != GAUSS_JORDAN:
        return None
    orden = len(entrada["a"])
    return estimar_gauss_jordan(orden, 2 * orden, columnas_pivote=orden, perfil=perfil_numerico(entrada["a"]))


def firmar_entrada(entrada):
    """Firma de esta matriz exacta y este método: una confirmación no sirve para otra entrada."""
    valores = ";".join(",".join(str(valor) for valor in fila) for fila in entrada["a"])
    return salted_hmac(_SAL_CONFIRMACION, f"{entrada['metodo']}|{valores}", algorithm="sha256").hexdigest()


def confirmacion_pendiente(entrada, firma=""):
    """None si se puede calcular ya; si no, el aviso que se confirma con «Continuar».

    Solo una estimación pesada o muy pesada pide confirmación. «Continuar»
    devuelve la firma de esta misma entrada, así que al volver con ella se
    calcula sin preguntar otra vez; con otra matriz se vuelve a estimar.
    """
    estimacion = estimar_inversa_web(entrada)
    if estimacion is None:
        return None
    nivel = categoria(estimacion)
    if nivel < Categoria.PESADA:
        return None
    esperada = firmar_entrada(entrada)
    if constant_time_compare(firma or "", esperada):
        return None
    return {
        "firma": esperada,
        "mensaje": MENSAJES_ESPERA[nivel],
        "tiempo": texto_intervalo(*intervalo_segundos(estimacion)),
    }


def _gauss_jordan(calculo):
    """[A | I], las operaciones por filas del motor y la lectura de la matriz final."""
    nulas = [indice for indice, fila in enumerate(calculo["izquierda"], start=1) if not any(fila)]
    if calculo["invertible"]:
        lectura = "El lado izquierdo ya es la matriz identidad: la matriz final es [I | B]. El bloque derecho B es la inversa de A."
    else:
        filas = f"La fila {nulas[0]} del lado izquierdo quedó" if len(nulas) == 1 else f"Las filas {enumerar(map(str, nulas))} del lado izquierdo quedaron"
        lectura = f"{filas} con solo ceros: ninguna operación por filas puede convertir ese lado en la matriz identidad."
    return {
        "columnas_izquierda": calculo["orden"],
        "aumentada": formatear_matriz(calculo["aumentada"]),
        "pasos": adaptar_pasos(calculo["pasos"]),
        "final": formatear_matriz(calculo["reducida"]),
        "lectura": lectura,
    }


def _metodo_2x2(calculo):
    """La regla con letras, ad − bc con los números de A, el intercambio y el factor."""
    entradas = calculo["entradas"]
    a, b, c, d = (entradas[nombre] for nombre in "abcd")
    diferencia = formatear_exacto(calculo["ad_menos_bc"])
    datos = {
        "simbolica": SIMBOLICA,
        "simbolica_intercambiada": SIMBOLICA_INTERCAMBIADA,
        "matriz": formatear_matriz(calculo["matriz"]),
        "entradas": enumerar(f"{nombre} = {formatear_exacto(valor)}" for nombre, valor in entradas.items()),
        "ad_menos_bc": (
            f"ad − bc = {_operando(a)}·{_operando(d)} − {_operando(b)}·{_operando(c)} "
            f"= {formatear_exacto(calculo['ad'])} − {_sumando(calculo['bc'])} = {diferencia}"
        ),
        "diferencia": diferencia,
        "intercambiada": formatear_matriz(calculo["intercambiada"]),
    }
    if calculo["invertible"]:
        factor = calculo["factor"]
        datos |= {
            "factor": f"1/(ad − bc) = 1/({diferencia}) = {formatear_exacto(factor)}",
            "factor_operando": _operando(factor),
            "desarrollo": [[f"{_operando(factor)}·{_operando(valor)}" for valor in fila] for fila in calculo["intercambiada"]],
        }
    return datos


def calcular_inversa_web(entrada):
    """Calcula la entrada ya validada (y confirmada, si hacía falta) y la deja lista para la plantilla."""
    calculo = calcular_inversa(entrada["a"], entrada["metodo"])
    orden = calculo["orden"]
    presentar = _gauss_jordan if calculo["metodo"] == GAUSS_JORDAN else _metodo_2x2
    return {
        "metodo": calculo["metodo"],
        "titulo_metodo": dict(METODOS)[calculo["metodo"]],
        "forma": f"{orden}×{orden}",
        "invertible": calculo["invertible"],
        "inversa": formatear_matriz(calculo["inversa"]) if calculo["invertible"] else None,
        "explicacion": None if calculo["invertible"] else NO_INVERTIBLE[calculo["metodo"]],
        **presentar(calculo),
    }
