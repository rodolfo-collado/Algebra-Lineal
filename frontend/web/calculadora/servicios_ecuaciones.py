"""Presentación de «Resolver Ax = b»: la ecuación matricial leída como sistema.

No calcula nada: `backend.ecuaciones_matriciales` resuelve [A | b] con los
motores de sistemas y aquí solo se formatean los datos exactos para la
plantilla: el enunciado (Ax = b tiene solución única, infinitas o ninguna), el
vector x, la comprobación A·x = b, la interpretación como combinación lineal de
las columnas de A y la cadena de equivalencias que lleva de Ax = b a [A | b].
El procedimiento de cada método se adapta con `servicios.presentar_resolucion`,
las mismas piezas que usa Reducción por filas.
"""

import json

from django.utils.crypto import constant_time_compare, salted_hmac

from backend.determinantes.presupuesto import estimar_determinante
from backend.ecuaciones_matriciales import MENSAJE_LU_CUADRADA, matrices_de_cramer, resolver_ecuacion_matricial
from backend.matrices import vector_columna
from backend.presupuesto_computacional import (
    ESTIMADORES, Categoria, Estimacion, PerfilNumerico, categoria, combinar_estimaciones,
    estimar_gauss_jordan, estimar_lu, estimar_producto, intervalo_segundos, perfil_numerico,
)
from backend.sistemas import enumerar_variables

from .opciones_ecuaciones import NOMBRE_INCOGNITA, forma_texto, metodos_a_resolver, titulo_resultado
from .forms_determinantes import metodo_disponible, metodo_sugerido
from .presentacion_numerica import formatear_exacto
from .servicios import adaptar_pasos, clave_clasificacion, formatear_matriz, presentar_resolucion
from .servicios_determinantes import presentar_determinante
from .servicios_matrices import _operando, combinacion_columnas, subindice
from .servicios_presupuesto import texto_intervalo

ENUNCIADOS = {
    "no_aplicable": "Factorización LU sin permutaciones no aplicable.",
    "unica": "Ax = b tiene solución única.",
    "infinitas": "Ax = b tiene infinitas soluciones.",
    "inconsistente": "Ax = b no tiene solución.",
}


def incognitas(columnas):
    """x₁, x₂, …, xₙ: una incógnita por columna de A."""
    return [f"{NOMBRE_INCOGNITA}{subindice(indice)}" for indice in range(1, columnas + 1)]


def vector_incognita(columnas):
    """El vector x tal como se dibuja: una columna de incógnitas, sin celdas editables."""
    return [[nombre] for nombre in incognitas(columnas)]


def combinacion_simbolica(columnas):
    """«x₁a₁ + x₂a₂ + … + xₙaₙ»: Ax escrito como combinación lineal de las columnas de A."""
    return " + ".join(f"{nombre}a{subindice(k)}" for k, nombre in enumerate(incognitas(columnas), start=1))


def ecuacion_vectorial(columnas):
    return f"{combinacion_simbolica(columnas)} = b"


def _columna_texto(vector):
    return formatear_matriz(vector_columna(list(vector)))


def _columnas_de_a(calculo):
    return [
        {"nombre": f"a{subindice(k)}", "etiqueta": f"Columna {k} de A", "matriz": _columna_texto(columna)}
        for k, columna in enumerate(calculo["columnas_a"], start=1)
    ]


def _interpretacion(calculo, clave):
    """Lectura de la clasificación como pertenencia de b al conjunto generado por las columnas de A."""
    n = calculo["columnas"]
    columnas = "la columna de A" if n == 1 else "las columnas de A"
    if clave == "unica":
        return {
            "texto": f"b es combinación lineal de {columnas} de una única manera.",
            "igualdad": f"b = {combinacion_columnas(calculo['x'])}",
        }
    if clave == "infinitas":
        libres = enumerar_variables(calculo["variables_libres"])
        return {
            "texto": (
                f"b es combinación lineal de {columnas} de infinitas maneras: cada valor de "
                f"{libres} da una combinación distinta que también produce b."
            ),
            "igualdad": None,
        }
    return {
        "texto": (
            f"b no pertenece al conjunto generado por {columnas}: ninguna combinación "
            f"{combinacion_simbolica(n)} produce b."
        ),
        "igualdad": None,
    }


def _comprobacion(a, calculo):
    """A·x = b con la solución sustituida; el producto lo calcula `multiplicar_matriz_vector`."""
    return {
        "a": formatear_matriz(a),
        "x": _columna_texto(calculo["x"]),
        "producto": _columna_texto(calculo["verificacion"]),
        "b": _columna_texto(calculo["b"]),
        "coincide": calculo["verificacion"] == calculo["b"],
    }


def estimar_ecuacion_web(entrada):
    """Costo previsto de `resolver_ecuacion_web(entrada)`, sin resolver.

    Cada método reduce [A | b] y, con solución única, comprueba A·x = b con un
    producto; antes de resolver no se sabe si la habrá, así que se cuenta
    siempre. Todavía no decide nada: ninguna entrada válida se rechaza por su costo.
    """
    a, b = entrada["a"], entrada["b"]
    filas, columnas = len(a), len(a[0])
    perfil = perfil_numerico(a, [b])
    if entrada["metodo"] == "cramer":
        metodo = entrada.get("metodo_determinante", metodo_sugerido(filas))
        matrices = [a, *matrices_de_cramer(a, b)]
        if not metodo_disponible(metodo, filas):
            raise ValueError("El método de determinante no está disponible para el tamaño de A.")
        partes = [estimar_determinante(matriz, metodo) for matriz in matrices]
        # Además de cada desarrollo: matrices A_i, cocientes, vector y comprobación.
        factor = max(parte.factor_numerico for parte in partes)
        resumen = Estimacion("cramer", (filas, columnas), filas, filas * factor,
                             ((filas + 1) * filas * columnas + 8 * filas) * factor, factor)
        bits_det = filas * (perfil.bits_numerador + columnas * perfil.bits_denominador + filas.bit_length())
        return combinar_estimaciones(*partes, resumen,
                                     estimar_producto(filas, columnas, 1, perfil=PerfilNumerico(2 * bits_det, 2 * bits_det)),
                                     operacion="cramer")
    if entrada["metodo"] == "lu":
        if filas != columnas:
            raise ValueError(MENSAJE_LU_CUADRADA)
        # Los resultados aún no existen: aproximamos su crecimiento, como en Inversa.
        bits_lu = filas * (perfil.bits_numerador + (columnas - 1) * perfil.bits_denominador)
        perfil_lu = PerfilNumerico(bits_lu, bits_lu)
        bits_y = filas * (bits_lu + columnas * bits_lu)
        perfil_y = PerfilNumerico(bits_y, bits_y)
        bits_x = filas * (bits_y + columnas * bits_y)
        return combinar_estimaciones(
            estimar_lu(filas, columnas, perfil=perfil_numerico(a)),
            estimar_gauss_jordan(filas, columnas + 1, columnas_pivote=columnas, perfil=perfil_lu),
            estimar_gauss_jordan(filas, columnas + 1, columnas_pivote=columnas, perfil=perfil_y),
            estimar_producto(filas, columnas, 1, perfil=PerfilNumerico(bits_x, bits_x)),
            operacion="lu",
        )
    comprobacion = estimar_producto(filas, columnas, 1, perfil=perfil)
    partes = []
    for clave in metodos_a_resolver(entrada["metodo"]):
        partes += [ESTIMADORES[clave](filas, columnas + 1, columnas_pivote=columnas, perfil=perfil), comprobacion]
    return combinar_estimaciones(*partes, operacion=entrada["metodo"])


def confirmacion_pendiente(entrada, firma=""):
    """Estima LU o Cramer antes de ejecutar; la firma liga todos los datos del cálculo."""
    if entrada["metodo"] not in ("lu", "cramer"):
        return None
    estimacion = estimar_ecuacion_web(entrada)
    if categoria(estimacion) < Categoria.PESADA:
        return None
    calculo = {
        "a": [[str(valor) for valor in fila] for fila in entrada["a"]],
        "b": [str(valor) for valor in entrada["b"]], "metodo": entrada["metodo"],
    }
    if entrada["metodo"] == "cramer":
        calculo["metodo_determinante"] = entrada.get("metodo_determinante", metodo_sugerido(len(entrada["a"])))
    esperada = salted_hmac(
        f"pygebra.ecuaciones-{entrada['metodo']}.confirmacion",
        json.dumps(calculo, sort_keys=True, separators=(",", ":")), algorithm="sha256",
    ).hexdigest()
    if constant_time_compare(firma or "", esperada):
        return None
    return {
        "firma": esperada, "tiempo": texto_intervalo(*intervalo_segundos(estimacion)),
        "mensaje": (
            f"Cramer prevé {len(entrada['a']) + 1} determinantes y sus procedimientos completos; el cálculo puede tardar."
            if entrada["metodo"] == "cramer" else
            "La factorización y las dos reducciones pueden tardar porque conservan un procedimiento largo."
        ),
        "operacion": "Resolver Ax = b por Regla de Cramer" if entrada["metodo"] == "cramer" else
                     "Resolver Ax = b por LU: A = LU, Ly = b y Ux = y",
    }


def _presentar_lu(calculo):
    factorizacion = calculo["factorizacion"]
    aplicable = factorizacion["aplicable"]
    return {
        "aplicable": aplicable,
        "l": formatear_matriz(factorizacion["l"]) if aplicable else None,
        "u": formatear_matriz(factorizacion["u"]),
        "pasos": adaptar_pasos(factorizacion["pasos"]) if not aplicable else [],
        "mensaje": " ".join(calculo["justificacion"]) if not aplicable else (
            "U es singular: el bloque izquierdo no puede convertirse en I, por lo que "
            "no se obtiene [I | x] ni una solución única. La reducción permite clasificar el sistema."
            if calculo["x"] is None else ""
        ),
        "etapas": [{
            "titulo": "Resolver Ly = b" if etapa["nombre"] == "y" else "Resolver Ux = y",
            "inicial": "[L | b]" if etapa["nombre"] == "y" else "[U | y]",
            "final": f"[I | {etapa['nombre']}]" if etapa["es_identidad"] else "Forma reducida de [U | y]",
            "lectura": (
                f"La última columna contiene {etapa['nombre']}."
                if etapa["es_identidad"] else "El bloque izquierdo no es la identidad."
            ),
            "matriz_inicial": formatear_matriz(etapa["matriz_inicial"]),
            "matriz_final": formatear_matriz(etapa["matriz_final"]),
            "columnas_izquierda": calculo["columnas"], "pasos": adaptar_pasos(etapa["pasos"]),
        } for etapa in calculo["etapas_lu"]],
    }


def _presentar_cramer(calculo):
    evidencia = calculo["cramer"]
    principal = presentar_determinante(evidencia["principal"], nombre="D")
    reemplazos = []
    for etapa in evidencia["reemplazos"]:
        indice = subindice(etapa["columna"])
        nombre = f"D{indice}"
        determinante = presentar_determinante(etapa["calculo"], nombre=nombre)
        reemplazos.append({
            "columna": etapa["columna"], "nombre_matriz": f"A{indice}", "nombre": nombre,
            "titulo": f"Ver cálculo de {nombre}", "determinante": determinante,
            "cociente": (
                f"x{indice} = {nombre}/D = {_operando(etapa['calculo']['determinante'])} / "
                f"{_operando(evidencia['principal']['determinante'])} = {formatear_exacto(etapa['valor'])}"
                if etapa["valor"] is not None else None
            ),
        })
    return {"principal": principal, "reemplazos": reemplazos, "motivo": evidencia["motivo"],
            "mensaje": " ".join(calculo["justificacion"])}


def resolver_ecuacion_web(entrada):
    """Resuelve la entrada ya validada por el formulario y la deja lista para la plantilla."""
    a, b, metodo = entrada["a"], entrada["b"], entrada["metodo"]
    # «Comparar ambos» resuelve la misma ecuación con cada método; la clasificación y el
    # conjunto solución coinciden por construcción y el resultado se muestra una sola vez.
    opciones = {"metodo_determinante": entrada.get("metodo_determinante", metodo_sugerido(len(a)))} if metodo == "cramer" else {}
    calculos = [resolver_ecuacion_matricial(a, b, clave, **opciones) for clave in metodos_a_resolver(metodo)]
    principal = calculos[0]
    clave = clave_clasificacion(principal["clasificacion"]) if principal["clasificacion"] else "no_aplicable"
    filas, columnas = principal["filas"], principal["columnas"]
    unica = principal["x"] is not None

    resultado = {
        "metodo": metodo,
        "titulo_metodo": titulo_resultado(metodo),
        "comparando": len(calculos) > 1,
        "filas": filas,
        "columnas": columnas,
        "forma": forma_texto(filas, columnas),
        "clasificacion": principal["clasificacion"],
        "clasificacion_clave": clave,
        "enunciado": ENUNCIADOS[clave],
        "justificacion": principal["justificacion"],
        "solucion_general": principal["solucion_general"],
        "columnas_pivote": principal["columnas_pivote"],
        "variables_libres": [f"{NOMBRE_INCOGNITA}{indice}" for indice in principal["variables_libres"]],
        "x": _columna_texto(principal["x"]) if unica else None,
        "comprobacion": _comprobacion(a, principal) if unica else None,
        "interpretacion": _interpretacion(principal, clave) if principal["clasificacion"] else None,
        # Cadena de equivalencias: ecuación matricial → vectorial → sistema → [A | b].
        "a": formatear_matriz(a),
        "b": _columna_texto(b),
        "incognitas": vector_incognita(columnas),
        "ecuacion_vectorial": {
            "simbolica": ecuacion_vectorial(columnas),
            "terminos": [
                {"coeficiente": nombre, **columna}
                for nombre, columna in zip(incognitas(columnas), _columnas_de_a(principal))
            ],
        },
        "ecuaciones": principal["ecuaciones"],
        "matriz_aumentada": formatear_matriz(principal["matriz_aumentada"]),
        "metodos": [] if metodo in ("lu", "cramer") else [
            presentar_resolucion(calculo, calculo["metodo"], calculo["matriz_aumentada"]) for calculo in calculos
        ],
    }
    if metodo == "lu":
        resultado["lu"] = _presentar_lu(principal)
    if metodo == "cramer":
        resultado["cramer"] = _presentar_cramer(principal)
        if clave == "no_aplicable":
            resultado["enunciado"] = (
                "Regla de Cramer no aplicable: D = 0." if principal["cramer"]["motivo"] == "determinante_nulo" else
                "No se pudo completar Cramer con el método de determinante elegido."
            )
    return resultado
