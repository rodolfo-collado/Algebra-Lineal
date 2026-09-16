"""Presentación de «Resolver Ax = b»: la ecuación matricial leída como sistema.

No calcula nada: `backend.ecuaciones_matriciales` resuelve [A | b] con los
motores de sistemas y aquí solo se formatean los datos exactos para la
plantilla: el enunciado (Ax = b tiene solución única, infinitas o ninguna), el
vector x, la comprobación A·x = b, la interpretación como combinación lineal de
las columnas de A y la cadena de equivalencias que lleva de Ax = b a [A | b].
El procedimiento de cada método se adapta con `servicios.presentar_resolucion`,
las mismas piezas que usa Resolver un sistema.
"""

from backend.ecuaciones_matriciales import resolver_ecuacion_matricial
from backend.matrices import vector_columna
from backend.sistemas import enumerar_variables

from .opciones_ecuaciones import NOMBRE_INCOGNITA, forma_texto, metodos_a_resolver, titulo_resultado
from .servicios import clave_clasificacion, formatear_matriz, presentar_resolucion
from .servicios_matrices import combinacion_columnas, subindice

ENUNCIADOS = {
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


def resolver_ecuacion_web(entrada):
    """Resuelve la entrada ya validada por el formulario y la deja lista para la plantilla."""
    a, b, metodo = entrada["a"], entrada["b"], entrada["metodo"]
    # «Comparar ambos» resuelve la misma ecuación con cada método; la clasificación y el
    # conjunto solución coinciden por construcción y el resultado se muestra una sola vez.
    calculos = [resolver_ecuacion_matricial(a, b, clave) for clave in metodos_a_resolver(metodo)]
    principal = calculos[0]
    clave = clave_clasificacion(principal["clasificacion"])
    filas, columnas = principal["filas"], principal["columnas"]
    unica = principal["x"] is not None

    return {
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
        "interpretacion": _interpretacion(principal, clave),
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
        "metodos": [
            presentar_resolucion(calculo, calculo["metodo"], calculo["matriz_aumentada"]) for calculo in calculos
        ],
    }
