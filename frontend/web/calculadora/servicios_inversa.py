"""Inversa y una aplicación: presupuesto previo y presentación de datos exactos.

Los motores compartidos hacen la matemática. Se estima el cálculo completo
sin ejecutar matrices intermedias y una sola firma confirma toda la entrada.
"""

import json

from django.utils.crypto import constant_time_compare, salted_hmac

from backend.matriz_inversa import (
    DIRECTO_2X2, GAUSS_JORDAN, aplicar_funcion_adicional, calcular_inversa, verificar_inversa,
)
from backend.presupuesto_computacional import (
    Categoria, Estimacion, PerfilNumerico, categoria, combinar_estimaciones,
    estimar_gauss_jordan, estimar_producto, intervalo_segundos, perfil_numerico,
)

from .presentacion_numerica import formatear_exacto
from .servicios import adaptar_pasos, formatear_matriz
from .servicios_bases import enumerar
from .servicios_matrices import _operando, _sumando, subindice
from .servicios_presupuesto import texto_intervalo

METODOS = ((GAUSS_JORDAN, "Gauss-Jordan"), (DIRECTO_2X2, "Método para matrices 2×2"))
FUNCIONES_ADICIONALES = (
    ("ninguna", "Sin operación adicional"),
    ("inversa_inversa", "Invertir nuevamente"),
    ("traspuesta", "Traspuesta"),
    ("producto", "Producto con otra matriz"),
    ("vector", "Aplicar a un vector"),
)
# Qué calcula o comprueba cada opción, antes de elegirla (una línea, junto a su radio).
AYUDAS_FUNCIONES = {
    "ninguna": "Solo calcula A⁻¹.",
    "inversa_inversa": "Comprueba (A⁻¹)⁻¹ = A.",
    "traspuesta": "Comprueba (Aᵀ)⁻¹ = (A⁻¹)ᵀ.",
    "producto": "Comprueba (AB)⁻¹ = B⁻¹A⁻¹.",
    "vector": "Calcula x = A⁻¹b y comprueba Ax = b.",
}

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
    """Costo total, incluida la verificación, antes de ejecutar ningún motor.

    Las inversiones iniciales usan los perfiles de A/B. Para resultados aún
    desconocidos se aproxima el crecimiento con n·(bits_num+(2n−1)·bits_den),
    conservando ese tamaño en numerador y denominador. AB usa el perfil de sus
    entradas ampliado por las sumas y productos. Son aproximaciones, no valores
    de matrices ejecutadas. Las traspuestas solo reordenan n² entradas.

    La regla directa usa una cota pequeña de 14 operaciones y 24 celdas por
    inversión; no se modela como reducción por filas. P26.2 suma estas partes
    usando las mismas referencias, categorías y calibración.
    """
    orden = len(entrada["a"])
    perfil_a = perfil_numerico(entrada["a"])
    funcion = entrada.get("funcion_adicional", "ninguna")

    def invertir(perfil):
        if entrada["metodo"] == DIRECTO_2X2:
            return Estimacion("inversa_2x2", (2, 2), 4, 14, 24)
        return estimar_gauss_jordan(orden, 2 * orden, columnas_pivote=orden, perfil=perfil)

    def perfil_inversa(perfil):
        bits = orden * (perfil.bits_numerador + (2 * orden - 1) * perfil.bits_denominador)
        return PerfilNumerico(bits, bits)

    partes = [invertir(perfil_a)]
    perfil_intermedio = perfil_inversa(perfil_a)
    if funcion == "inversa_inversa":
        partes.append(invertir(perfil_intermedio))
    elif funcion == "traspuesta":
        partes.append(invertir(perfil_a))
        partes.append(Estimacion("traspuestas", (orden, orden), 0, 0, 2 * orden * orden))
    elif funcion == "producto":
        perfil_b = perfil_numerico(entrada["b"])
        conjunto = perfil_numerico(entrada["a"], entrada["b"])
        bits_ab = 2 * conjunto.bits_numerador + orden * conjunto.bits_denominador
        perfil_ab = PerfilNumerico(bits_ab, bits_ab)
        perfil_inversas = PerfilNumerico(
            max(perfil_intermedio.bits_numerador, perfil_inversa(perfil_b).bits_numerador),
            max(perfil_intermedio.bits_denominador, perfil_inversa(perfil_b).bits_denominador),
        )
        partes.extend((invertir(perfil_b), estimar_producto(orden, orden, orden, perfil=conjunto),
                       invertir(perfil_ab), estimar_producto(orden, orden, orden, perfil=perfil_inversas)))
    elif funcion == "vector":
        perfil_vector = perfil_numerico([entrada["vector"]])
        perfil_producto = PerfilNumerico(
            max(perfil_intermedio.bits_numerador, perfil_vector.bits_numerador),
            max(perfil_intermedio.bits_denominador, perfil_vector.bits_denominador),
        )
        bits_x = 2 * perfil_producto.bits_numerador + orden * perfil_producto.bits_denominador
        perfil_comprobacion = PerfilNumerico(
            max(perfil_a.bits_numerador, bits_x), max(perfil_a.bits_denominador, bits_x),
        )
        partes.extend((estimar_producto(orden, orden, 1, perfil=perfil_producto),
                       estimar_producto(orden, orden, 1, perfil=perfil_comprobacion)))
    if entrada.get("verificar", False):
        partes.extend(estimar_producto(orden, orden, orden, perfil=perfil_intermedio) for _ in range(2))
    return partes[0] if len(partes) == 1 else combinar_estimaciones(*partes, operacion="inversa_y_aplicacion")


def firmar_entrada(entrada):
    """Firma canónica de TODO el cálculo: A, método, verificar, función y B/b."""
    def matriz(valores):
        return [[str(valor) for valor in fila] for fila in valores]

    calculo = {
        "a": matriz(entrada["a"]), "metodo": entrada["metodo"],
        "verificar": bool(entrada.get("verificar", False)),
        "funcion_adicional": entrada.get("funcion_adicional", "ninguna"),
        "b": matriz(entrada["b"]) if entrada.get("b") is not None else None,
        "vector": [str(valor) for valor in entrada["vector"]] if entrada.get("vector") is not None else None,
    }
    return salted_hmac(
        _SAL_CONFIRMACION, json.dumps(calculo, sort_keys=True, separators=(",", ":")), algorithm="sha256",
    ).hexdigest()


def confirmacion_pendiente(entrada, firma=""):
    """None si se puede calcular ya; si no, el aviso que se confirma con «Continuar».

    Solo una estimación pesada o muy pesada pide confirmación. «Continuar»
    devuelve la firma de esta misma entrada, así que al volver con ella se
    calcula sin preguntar otra vez; con otra matriz se vuelve a estimar.
    """
    estimacion = estimar_inversa_web(entrada)
    # Todos los trabajos 2×2 directos tienen tamaño mínimo; la cota se conserva
    # pero no se pide un aviso para unas pocas operaciones exactas protegidas.
    if entrada["metodo"] == DIRECTO_2X2:
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


def _gauss_jordan(calculo, nombre="A"):
    """[A | I], las operaciones por filas del motor y la lectura de la matriz final."""
    nulas = [indice for indice, fila in enumerate(calculo["izquierda"], start=1) if not any(fila)]
    if calculo["invertible"]:
        inversa_nombre = f"({nombre})⁻¹" if nombre in ("A⁻¹", "Aᵀ", "AB") else f"{nombre}⁻¹"
        lectura = f"El lado izquierdo ya es la matriz identidad: la matriz final es [I | {inversa_nombre}]. El bloque derecho es la inversa de {nombre}."
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


def _presentar_inversion(calculo, nombre):
    """Los pasos ya registrados de una inversión adicional, sin recalcularla."""
    presentar = _gauss_jordan(calculo, nombre) if calculo["metodo"] == GAUSS_JORDAN else _metodo_2x2(calculo)
    return {
        "metodo": calculo["metodo"], "nombre": nombre, "invertible": calculo["invertible"],
        "inversa": formatear_matriz(calculo["inversa"]) if calculo["invertible"] else None,
        **presentar,
    }


def _presentar_adicional(calculo):
    """Matrices comparadas, datos de aplicación y pasos de las nuevas inversiones."""
    datos = {clave: valor for clave, valor in calculo.items() if not clave.startswith("calculo_")}
    matrices = (
        "resultado", "inversa_de_inversa", "traspuesta_a", "inversa_traspuesta", "traspuesta_inversa",
        "inversa_b", "producto_ab", "inversa_producto", "producto_inversas", "b", "x", "a_por_x",
    )
    for clave in matrices:
        if datos.get(clave) is not None:
            datos[clave] = formatear_matriz(datos[clave])
    inversiones = {
        "calculo_inversa_de_inversa": ("pasos_inversa_de_inversa", "A⁻¹"),
        "calculo_inversa_traspuesta": ("pasos_inversa_traspuesta", "Aᵀ"),
        "calculo_inversa_b": ("pasos_inversa_b", "B"),
        "calculo_inversa_producto": ("pasos_inversa_producto", "AB"),
    }
    for clave, (destino, nombre) in inversiones.items():
        if calculo.get(clave) is not None:
            datos[destino] = _presentar_inversion(calculo[clave], nombre)
    for clave, destino, expresion in (
        ("calculo_inversa_por_b", "desarrollo_vector", "A⁻¹b"),
        ("calculo_a_por_x", "desarrollo_comprobacion", "Ax"),
    ):
        if calculo.get(clave) is not None:
            datos[destino] = [
                f"({expresion}){subindice(paso['posicion'][0])} = "
                + " + ".join(f"{_operando(a)}·{_operando(b)}" for a, b in zip(paso["fila"], paso["columna"]))
                + f" = {formatear_exacto(paso['resultado'])}"
                for fila in calculo[clave]["pasos"] for paso in fila
            ]
    return datos


def calcular_inversa_web(entrada):
    """Calcula la entrada ya validada (y confirmada, si hacía falta) y la deja lista para la plantilla."""
    calculo = calcular_inversa(entrada["a"], entrada["metodo"])
    verificar_solicitado = entrada.get("verificar", False)
    verificacion = None
    if verificar_solicitado and calculo["invertible"]:
        comprobacion = verificar_inversa(entrada["a"], calculo["inversa"])
        verificacion = {
            clave: formatear_matriz(comprobacion[clave])
            for clave in ("identidad", "a_por_inversa", "inversa_por_a")
        }
        verificacion.update({
            clave: comprobacion[clave]
            for clave in ("a_por_inversa_es_identidad", "inversa_por_a_es_identidad", "verificada")
        })
    orden = calculo["orden"]
    funcion = entrada.get("funcion_adicional", "ninguna")
    adicional = _presentar_adicional(aplicar_funcion_adicional(
        funcion, entrada["a"], calculo["inversa"], metodo=entrada["metodo"],
        b=entrada.get("b"), vector=entrada.get("vector"),
    ))
    expresiones = {
        "ninguna": ("A⁻¹", "Matriz inversa de A"),
        "inversa_inversa": ("(A⁻¹)⁻¹ = A", "Inversa de la inversa de A"),
        "traspuesta": ("(Aᵀ)⁻¹ = (A⁻¹)ᵀ", "Inversa de la traspuesta de A"),
        "producto": ("(AB)⁻¹ = B⁻¹A⁻¹", "Inversa del producto AB"),
        "vector": ("x = A⁻¹b", "Vector solución mediante la inversa"),
    }
    expresion, etiqueta = expresiones[funcion]
    comparacion = "coincide_con_a" if funcion == "inversa_inversa" else "coinciden"
    if funcion in ("inversa_inversa", "traspuesta", "producto") and adicional.get(comparacion) is False:
        expresion = expresion.replace(" = ", " ≠ ")
    presentar = _gauss_jordan if calculo["metodo"] == GAUSS_JORDAN else _metodo_2x2
    return {
        "metodo": calculo["metodo"],
        "titulo_metodo": dict(METODOS)[calculo["metodo"]],
        "forma": f"{orden}×{orden}",
        "invertible": calculo["invertible"],
        "verificar_solicitado": verificar_solicitado,
        "verificacion": verificacion,
        "funcion_adicional": funcion, "adicional": adicional,
        "titulo": "Inversa de A" if funcion == "ninguna" else dict(FUNCIONES_ADICIONALES)[funcion],
        "expresion_final": expresion, "etiqueta_final": etiqueta,
        "inversa": formatear_matriz(calculo["inversa"]) if calculo["invertible"] else None,
        "explicacion": None if calculo["invertible"] else NO_INVERTIBLE[calculo["metodo"]],
        **presentar(calculo),
    }
