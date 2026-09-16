"""Opciones de «Resolver un sistema»: método y bloques del resultado.

Una sola herramienta y una sola matemática. El método decide el procedimiento
(Gauss, Gauss-Jordan o los dos para compararlos) y los bloques, qué análisis
acompaña a la solución final, que siempre se muestra.
"""

METODOS = (
    ("gauss", "Gauss"),
    ("gauss_jordan", "Gauss-Jordan"),
    ("comparar", "Comparar ambos"),
)
# Gauss-Jordan es el predeterminado de la interfaz web desde su primera versión.
METODO_PREDETERMINADO = "gauss_jordan"
# «Comparar ambos» resuelve la misma entrada con los dos métodos, en este orden.
METODOS_COMPARADOS = ("gauss", "gauss_jordan")

BLOQUES = (
    ("procedimiento", "Procedimiento"),
    ("clasificacion", "Clasificación"),
    ("pivotes", "Columnas pivote"),
    ("sistema-resultante", "Sistema resultante"),
)
BLOQUES_PREDETERMINADOS = tuple(clave for clave, _ in BLOQUES)

# Rutas de P10.1 que hoy son configuraciones de esta misma herramienta.
RUTAS_ANTIGUAS = {
    "gauss": {"metodo": "gauss"},
    "gauss-jordan": {"metodo": "gauss_jordan"},
    "clasificacion": {},
    "columnas-pivote": {},
}


def metodos_a_resolver(metodo: str) -> tuple[str, ...]:
    return METODOS_COMPARADOS if metodo == "comparar" else (metodo,)


def titulo_resultado(metodo: str) -> str:
    if metodo == "comparar":
        return "Gauss y Gauss-Jordan"
    return dict(METODOS)[metodo]
