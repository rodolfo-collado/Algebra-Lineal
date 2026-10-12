"""Determinantes: presupuesto previo y datos exactos listos para la plantilla.

El backend calcula y devuelve estructuras; aquí solo se escriben las lecturas
de cada método (sin HTML). No se recalcula ninguna entrada.
"""

import json

from django.utils.crypto import constant_time_compare, salted_hmac

from backend.determinantes import calcular_determinante
from backend.determinantes.presupuesto import estimar_determinante
from backend.matrices import contar
from backend.presupuesto_computacional import Categoria, categoria, intervalo_segundos
from backend.seguridad_numerica import dividir_exacto

from .forms_determinantes import METODOS
from .presentacion_numerica import formatear_exacto
from .servicios import adaptar_pasos, formatear_matriz
from .servicios_matrices import _operando, _sumando, desarrollo_ad_menos_bc, subindice
from .servicios_presupuesto import texto_intervalo
from .transferencia_matriz import campos_matriz

_SAL_CONFIRMACION = "pygebra.determinantes.confirmacion"
MENSAJES_ESPERA = {
    Categoria.PESADA: "Este cálculo puede tardar varios segundos porque su procedimiento es largo.",
    Categoria.MUY_PESADA: "Este cálculo puede tardar bastante porque su procedimiento es muy largo.",
}
SIMBOLICA_2X2 = [["a", "b"], ["c", "d"]]
EXPONENTES = str.maketrans("0123456789+", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺")


def firmar_entrada(entrada):
    """Firma canónica de A, el método y la expansión."""
    calculo = {"a": [[str(valor) for valor in fila] for fila in entrada["a"]],
               "metodo": entrada["metodo"], "expansion": entrada["expansion"]}
    return salted_hmac(
        _SAL_CONFIRMACION, json.dumps(calculo, sort_keys=True, separators=(",", ":")), algorithm="sha256",
    ).hexdigest()


def confirmacion_pendiente(entrada, firma=""):
    """None si se puede calcular ya; si no, el aviso que se confirma con «Continuar».

    Cofactores por encima de 6×6 no llega aquí como aviso: el estimador lo rechaza.
    """
    estimacion = estimar_determinante(entrada["a"], entrada["metodo"])
    nivel = categoria(estimacion)
    if nivel < Categoria.PESADA:
        return None
    esperada = firmar_entrada(entrada)
    if constant_time_compare(firma or "", esperada):
        return None
    mensaje = MENSAJES_ESPERA[nivel]
    if entrada["metodo"] == "cofactores":
        mensaje += " Reducción por filas o Factorización LU obtienen el mismo determinante con menos pasos."
    return {"firma": esperada, "mensaje": mensaje, "tiempo": texto_intervalo(*intervalo_segundos(estimacion))}


def _producto(valores):
    return "·".join(_operando(valor) for valor in valores)


def _suma(valores):
    return " + ".join(_sumando(valor) for valor in valores)


def _directo_2x2(calculo):
    return {
        "simbolica": SIMBOLICA_2X2,
        "desarrollo": "det(A) = " + desarrollo_ad_menos_bc(
            calculo["matriz"], calculo["ad"], calculo["bc"], calculo["determinante"]),
    }


def _sarrus(calculo):
    def diagonales(grupo):
        return [
            "".join(f"a{subindice(i + 1, k + 1)}" for i, k in d["posiciones"])
            + f" = {_producto(d['valores'])} = {formatear_exacto(d['producto'])}"
            for d in grupo["diagonales"]
        ]

    positivas, negativas = calculo["positivas"], calculo["negativas"]
    return {
        # Las dos primeras columnas repetidas a la derecha dejan ver las seis diagonales completas.
        "ampliada": formatear_matriz([fila + fila[:2] for fila in calculo["matriz"]]),
        "positivas": diagonales(positivas),
        "negativas": diagonales(negativas),
        "suma_positivas": f"{_suma(d['producto'] for d in positivas['diagonales'])} = {formatear_exacto(positivas['suma'])}",
        "suma_negativas": f"{_suma(d['producto'] for d in negativas['diagonales'])} = {formatear_exacto(negativas['suma'])}",
        "resta": (f"det(A) = {formatear_exacto(positivas['suma'])} − {_sumando(negativas['suma'])} "
                  f"= {formatear_exacto(calculo['determinante'])}"),
    }


def _menor(hijo, nivel, nombre):
    """Cómo se obtuvo el valor de un menor: entrada única, ad − bc o otro desarrollo."""
    if len(hijo["matriz"]) == 1:
        return {"tipo": "1x1"}
    if len(hijo["matriz"]) == 2:
        return {"tipo": "2x2", "desarrollo": desarrollo_ad_menos_bc(
            hijo["matriz"], hijo["ad"], hijo["bc"], hijo["determinante"])}
    return {"tipo": "cofactores", **_cofactores(hijo, nivel, nombre)}


def _eleccion(nodo, eje):
    if not nodo["automatico"]:
        return f"Se desarrolla por {eje}, la que se eligió."
    ceros = sum(t["elemento"] == 0 for t in nodo["terminos"])
    if not ceros:
        return f"Automático usa {eje}: ninguna fila ni columna tiene ceros."
    return (f"Automático elige {eje}: tiene {contar(ceros, 'cero')} y ninguna otra fila o columna "
            "tiene más. Cada cero ahorra calcular un menor.")


def _cofactores(nodo, nivel=4, nombre="det(A)"):
    """Un nivel del desarrollo; los menores de 3×3 o más anidan su propio desarrollo.

    `nivel` es el encabezado del desplegable que explica cada menor (h4…h6).
    Dentro de un menor (`nombre` = Mᵢⱼ) las entradas se llaman mᵢⱼ y sus
    posiciones se cuentan en el propio menor.
    """
    if not nodo["terminos"]:
        return {"terminos": [], "valor": formatear_exacto(nodo["determinante"])}
    letra = "a" if nivel == 4 else "m"
    eje = f"la {nodo['eje']} {nodo['indice']}"
    terminos = []
    for t in nodo["terminos"]:
        pos = subindice(t["fila"], t["columna"])
        exponente = f"{t['fila']}+{t['columna']}".translate(EXPONENTES)
        signo = "+1" if t["signo"] > 0 else "−1"
        termino = {
            "entrada": f"{letra}{pos}", "posicion": pos, "elemento": formatear_exacto(t["elemento"]),
            "menor": formatear_matriz(t["menor"]),
            "signo": f"(−1){exponente} = {signo}",
            "contribucion_valor": t["contribucion"],
        }
        if t["hijo"] is not None:
            termino.update(
                menor_valor=f"M{pos} = {formatear_exacto(t['valor_menor'])}",
                cofactor=f"C{pos} = ({signo})·{_operando(t['valor_menor'])} = {formatear_exacto(t['cofactor'])}",
                contribucion=f"{letra}{pos}·C{pos} = {_operando(t['elemento'])}·{_operando(t['cofactor'])} = {formatear_exacto(t['contribucion'])}",
                titulo_menor=f"Cómo se obtiene M{pos}",
                calculo_menor=_menor(t["hijo"], min(nivel + 1, 6), f"M{pos}"),
            )
        terminos.append(termino)
    return {
        "nivel": nivel, "anidado": nivel > 4, "eje": eje, "eleccion": _eleccion(nodo, eje),
        "formula": f"{nombre} = " + " + ".join(f"{t['entrada']}C{t['posicion']}" for t in terminos),
        "terminos": terminos,
        "suma": f"{nombre} = {_suma(t['contribucion_valor'] for t in terminos)} = {formatear_exacto(nodo['determinante'])}",
    }


def _correcciones(pasos):
    """Solo los pasos que cambian det: intercambios y normalizaciones, con el factor que lo deshace."""
    return [
        f"Paso {numero} ({paso['operacion']}): det quedó multiplicado por "
        f"{_operando(dividir_exacto(1, paso['correccion_determinante']))}; "
        f"se corrige multiplicando por {_operando(paso['correccion_determinante'])}."
        for numero, paso in enumerate(pasos, start=1) if "correccion_determinante" in paso
    ]


def _reduccion(calculo):
    factores = [paso["correccion_determinante"] for paso in calculo["pasos"] if "correccion_determinante" in paso]
    singular = calculo["producto_diagonal"] == 0
    return {
        "pasos": adaptar_pasos(calculo["pasos"]),
        "u": formatear_matriz(calculo["u"]),
        "correcciones": _correcciones(calculo["pasos"]),
        "diagonal": f"det(U) = {_producto(calculo['diagonal'])} = {formatear_exacto(calculo['producto_diagonal'])}",
        "singular": singular,
        "final": None if singular else (
            f"det(A) = det(U)·{_producto(factores)} = {formatear_exacto(calculo['determinante'])}" if factores
            else f"det(A) = det(U) = {formatear_exacto(calculo['determinante'])}"),
    }


def _lu(calculo):
    datos = {"pasos": adaptar_pasos(calculo["pasos"]), "l": formatear_matriz(calculo["l"]),
             "u": formatear_matriz(calculo["u"])}
    if calculo["aplicable"]:
        datos["diagonal"] = (f"det(A) = det(L)·det(U) = 1·{_producto(calculo['diagonal'])} "
                             f"= {formatear_exacto(calculo['determinante'])}")
    else:
        pivote = calculo["pivote_nulo"]
        datos["motivo"] = (
            f"El pivote u{subindice(pivote['fila'], pivote['columna'])} es 0 y debajo hay un número distinto de 0. "
            "Para seguir habría que intercambiar filas, y la factorización LU sin intercambios no lo permite."
        )
    return datos


PRESENTAR = {"directo_2x2": _directo_2x2, "sarrus": _sarrus, "cofactores": _cofactores,
             "lu": _lu, "reduccion": _reduccion}


def calcular_determinante_web(entrada):
    """Calcula la entrada ya validada (y confirmada, si hacía falta) y la deja lista para la plantilla."""
    calculo = calcular_determinante(entrada["a"], entrada["metodo"], entrada["expansion"])
    orden = len(calculo["matriz"])
    datos = {
        "metodo": calculo["metodo"], "titulo_metodo": dict(METODOS)[calculo["metodo"]],
        "forma": f"{orden}×{orden}", "matriz": formatear_matriz(calculo["matriz"]),
        "aplicable": calculo["aplicable"], **PRESENTAR[calculo["metodo"]](calculo),
    }
    if calculo["aplicable"]:
        invertible = calculo["determinante"] != 0
        datos.update(determinante=formatear_exacto(calculo["determinante"]), invertible=invertible,
                     # Solo una A invertible ofrece «Calcular su matriz inversa».
                     transferencia=campos_matriz(calculo["matriz"]) if invertible else None)
    return datos
