"""Independencia de vectores a partir de la solución de Aα = 0."""

from fractions import Fraction

from backend.matrices import validar_vector
from backend.presupuesto_sistemas import validar_dimensiones
from backend.sistemas import ecuaciones_de_matriz, resolver_sistema_gauss_jordan
from backend.vectores import combinar, matriz_de_combinacion, nombres_generadores

NOMBRE_COEFICIENTE = "α"


def analizar_independencia_lineal(vectores):
    """Devuelve entradas, reducción y una relación exacta si hay dependencia.

    Las columnas y variables se numeran desde uno. Para construir un testigo
    se fija en uno la primera variable libre y en cero las demás. Las
    expresiones del sistema ya están despejadas en función de esas variables.
    """
    if not vectores:
        raise ValueError("Ingresa al menos un vector para analizar su independencia.")

    valido, mensaje = validar_vector(vectores[0], "v1")
    if not valido:
        raise ValueError(mensaje)
    dimension = len(vectores[0])
    validar_dimensiones(dimension, len(vectores))
    cero = [Fraction(0)] * dimension
    aumentada = matriz_de_combinacion(vectores, cero)
    matriz = [fila[:-1] for fila in aumentada]
    sistema = resolver_sistema_gauss_jordan(aumentada, NOMBRE_COEFICIENTE)
    libres = sistema["variables_libres"]
    relacion = None

    if libres:
        elegida = libres[0]
        coeficientes = [
            expresion["coeficientes"].get(elegida, Fraction(0))
            for expresion in sistema["expresiones_solucion"]
        ]
        verificacion = combinar(coeficientes, vectores)
        relacion = {
            "asignacion_libres": {variable: int(variable == elegida) for variable in libres},
            "coeficientes": coeficientes,
            "vector_despejado": elegida,
            "combinacion": {
                indice: -coeficiente
                for indice, coeficiente in enumerate(coeficientes, 1)
                if indice != elegida and coeficiente
            },
            "verificacion": verificacion,
            "verificada": verificacion == cero,
        }

    return {
        "vectores": [list(columna) for columna in zip(*matriz)],
        "dimension": dimension,
        "nombres": nombres_generadores(len(vectores)),
        "matriz": matriz,
        "matriz_aumentada": aumentada,
        "ecuaciones": ecuaciones_de_matriz(aumentada, NOMBRE_COEFICIENTE),
        "rango": len(sistema["columnas_pivote"]),
        "es_independiente": not libres,
        "sistema": sistema,
        "relacion": relacion,
    }
