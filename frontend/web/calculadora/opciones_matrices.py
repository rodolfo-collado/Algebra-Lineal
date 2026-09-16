"""Configuración de la herramienta; los límites son de interfaz, no matemáticos."""

DIMENSION_MINIMA = 1
DIMENSION_MAXIMA = 10
DIMENSION_PREDETERMINADA = 2
OPERACION_PREDETERMINADA = "suma"

CONFIGURACION = {
    "suma": {
        "etiqueta": "Suma", "matrices": ("A", "B"), "escalar": False,
        "expresion": "A + B", "simbolo": "+", "formula": "cᵢⱼ = aᵢⱼ + bᵢⱼ",
        "ayuda": "Suma las entradas en la misma posición. A y B comparten filas y columnas.",
    },
    "resta": {
        "etiqueta": "Resta", "matrices": ("A", "B"), "escalar": False,
        "expresion": "A − B", "simbolo": "−", "formula": "cᵢⱼ = aᵢⱼ − bᵢⱼ",
        "ayuda": "Resta las entradas en la misma posición. A y B comparten filas y columnas.",
    },
    "escalar": {
        "etiqueta": "Multiplicación por escalar", "matrices": ("A",), "escalar": True,
        "expresion": "k·A", "simbolo": "·", "formula": "(kA)ᵢⱼ = k · aᵢⱼ",
        "ayuda": "El escalar k multiplica cada entrada de A.",
    },
    "traspuesta": {
        "etiqueta": "Traspuesta", "matrices": ("A",), "escalar": False,
        "expresion": "Aᵀ", "simbolo": "", "formula": "(Aᵀ)ᵢⱼ = Aⱼᵢ",
        "ayuda": "Las filas de A pasan a ser las columnas de Aᵀ.",
    },
}
OPERACIONES = tuple((clave, opcion["etiqueta"]) for clave, opcion in CONFIGURACION.items())
