"""Opciones de «Operaciones con vectores»: operación, dimensión y cantidad de vectores.

Una sola herramienta para todo el flujo de vectores. La operación decide qué
vectores se piden (u y v; un escalar y u; o v1 … vk y el objetivo b) y la
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
    "suma": "u + v se calcula componente a componente.",
    "resta": "u − v se calcula componente a componente.",
    "escalar": "k·u multiplica cada componente de u por el escalar k.",
    "combinacion": "¿Existen c1, …, ck tales que c1·v1 + … + ck·vk = b?",
}

# Límites razonables para una calculadora de aula: la dimensión no está
# fijada, pero la interfaz debe seguir siendo legible.
DIMENSION_PREDETERMINADA = 3
DIMENSION_MINIMA = 1
DIMENSION_MAXIMA = 10
VECTORES_PREDETERMINADOS = 2
VECTORES_MINIMOS = 1
VECTORES_MAXIMOS = 6

# Nombres de los vectores de entrada según la operación.
NOMBRE_ESCALAR = "k"
NOMBRE_OBJETIVO = "b"
VECTORES_BINARIOS = ("u", "v")
VECTOR_ESCALAR = ("u",)


def nombres_generadores(cantidad: int) -> tuple[str, ...]:
    return tuple(f"v{indice}" for indice in range(1, cantidad + 1))


def nombres_vectores(operacion: str, cantidad: int) -> tuple[str, ...]:
    """Vectores que pide cada operación, en el orden en que se muestran."""
    if operacion == "combinacion":
        return (*nombres_generadores(cantidad), NOMBRE_OBJETIVO)
    if operacion == "escalar":
        return VECTOR_ESCALAR
    return VECTORES_BINARIOS


def etiqueta_operacion(operacion: str) -> str:
    return dict(OPERACIONES)[operacion]


def texto_boton(operacion: str) -> str:
    return "Comprobar" if operacion == "combinacion" else "Calcular"
