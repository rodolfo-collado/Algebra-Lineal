"""Opciones de «Operaciones con vectores»: operación, dimensión y cantidad de vectores.

Una sola herramienta para todo el flujo de vectores. La operación decide qué
vectores se piden (v1, v2, …; un escalar y v1; o v1 … vk y el objetivo b) y la
dimensión `n` es libre: el profesor no la fija, así que la elige el usuario.
"""

OPERACIONES = (
    ("suma", "Suma"),
    ("resta", "Resta"),
    ("escalar", "Multiplicación por escalar"),
    ("combinacion", "Combinación lineal"),
)
OPERACION_PREDETERMINADA = "suma"

# Explicación breve por operación, en el lenguaje del ejercicio.
AYUDAS = {
    "suma": "Suma dos o más vectores componente a componente.",
    "resta": "Resta dos o más vectores en el orden indicado, componente a componente.",
    "escalar": "k·v1 multiplica cada componente de v1 por el escalar k.",
    "combinacion": "¿Existen x1, …, xk tales que x1·v1 + … + xk·vk = b?",
}

# La dimensión conserva su límite de interfaz; la cantidad depende de la operación.
DIMENSION_PREDETERMINADA = 3
DIMENSION_MINIMA = 1
DIMENSION_MAXIMA = 10
VECTORES_PREDETERMINADOS = 2
VECTORES_MINIMOS = 1

# Nombres de los vectores de entrada: v1, v2, … en todas las operaciones, así que
# agregar uno nunca renombra los anteriores; k es el escalar y b, el objetivo.
NOMBRE_ESCALAR = "k"
NOMBRE_OBJETIVO = "b"


def nombres_generadores(cantidad: int) -> tuple[str, ...]:
    return tuple(f"v{indice}" for indice in range(1, cantidad + 1))


def nombres_vectores(operacion: str, cantidad: int) -> tuple[str, ...]:
    """Vectores que pide cada operación, en el orden en que se muestran."""
    if operacion == "combinacion":
        return (*nombres_generadores(cantidad), NOMBRE_OBJETIVO)
    if operacion == "escalar":
        return nombres_generadores(1)
    return nombres_generadores(cantidad)


def texto_boton(operacion: str) -> str:
    return "Comprobar" if operacion == "combinacion" else "Calcular"
