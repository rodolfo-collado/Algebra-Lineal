"""Desarrollo por cofactores: menores, signos y contribuciones exactas."""

from fractions import Fraction

from backend.seguridad_numerica import multiplicar_exacto, sumar_exacto

from .comun import directo_2x2, preparar

# El árbol de menores crece como n!: más allá de 6×6 conviene LU o reducción.
ORDEN_MAXIMO_COFACTORES = 6
MENSAJE_ORDEN_MAXIMO = (
    f"Cofactores admite hasta {ORDEN_MAXIMO_COFACTORES}×{ORDEN_MAXIMO_COFACTORES}: su número de "
    "menores crece de forma factorial. Usa Factorización LU o Reducción por filas."
)


def menor(a, fila, columna):
    """Quita una fila y una columna (índices desde 0) y devuelve la matriz restante."""
    return [[v for j, v in enumerate(f) if j != columna]
            for i, f in enumerate(a) if i != fila]


def _ceros(a, eje, indice):
    linea = a[indice] if eje == "fila" else [fila[indice] for fila in a]
    return sum(valor == 0 for valor in linea)


def elegir_expansion(a, expansion="auto"):
    """Devuelve (eje, índice desde 0) para "auto", "fila_i" o "columna_j" (i, j desde 1)."""
    n = len(a)
    opciones = [("fila", i) for i in range(n)] + [("columna", j) for j in range(n)]
    if expansion == "auto":
        # Más ceros = menos menores. En empate, max() conserva la primera fila y luego la primera columna.
        return max(opciones, key=lambda opcion: _ceros(a, *opcion))
    for eje, indice in opciones:
        if expansion == f"{eje}_{indice + 1}":
            return eje, indice
    raise ValueError("Selecciona una fila o columna existente para desarrollar por cofactores.")


def _determinante_menor(m):
    """Evidencia del menor: 1×1 directo, 2×2 con ad − bc y los mayores por cofactores automáticos."""
    if len(m) == 1:
        return {"matriz": m, "determinante": m[0][0]}
    if len(m) == 2:
        # Reutiliza el determinante 2×2 usado también por Matriz inversa.
        return {"matriz": m, **directo_2x2(m)}
    return _desarrollar(m, "auto")


def _desarrollar(a, expansion):
    eje, indice = elegir_expansion(a, expansion)
    total = Fraction(0)
    terminos = []
    for k in range(len(a)):
        i, j = (indice, k) if eje == "fila" else (k, indice)
        submatriz = menor(a, i, j)
        # El signo del cofactor sigue el tablero + − + …: (−1)^(i + j), igual con índices desde 0 o 1.
        signo = (-1) ** (i + j)
        termino = {"fila": i + 1, "columna": j + 1, "elemento": a[i][j], "menor": submatriz,
                   "signo": signo, "hijo": None, "valor_menor": None, "cofactor": None,
                   "contribucion": Fraction(0)}
        if a[i][j] != 0:
            # Un elemento cero anula su contribución: no se calcula su menor.
            hijo = _determinante_menor(submatriz)
            cofactor = multiplicar_exacto(signo, hijo["determinante"])
            termino.update(hijo=hijo, valor_menor=hijo["determinante"], cofactor=cofactor,
                           contribucion=multiplicar_exacto(a[i][j], cofactor))
        total = sumar_exacto(total, termino["contribucion"])
        terminos.append(termino)
    return {"matriz": a, "eje": eje, "indice": indice + 1, "automatico": expansion == "auto",
            "terminos": terminos, "determinante": total}


def cofactores(a, expansion="auto"):
    """det(A) = Σ aᵢⱼ·Cᵢⱼ por la fila o columna elegida, con Cᵢⱼ = (−1)^(i+j)·Mᵢⱼ.

    Devuelve `eje`, `indice` (desde 1), `automatico`, `terminos` y
    `determinante`. Cada término guarda su `menor`, `signo`, `valor_menor`,
    `cofactor`, `contribucion` y la evidencia `hijo` de cómo se obtuvo el menor.
    """
    a = preparar(a)
    if len(a) > ORDEN_MAXIMO_COFACTORES:
        raise ValueError(MENSAJE_ORDEN_MAXIMO)
    if len(a) == 1:
        elegir_expansion(a, expansion)
        return {"matriz": a, "eje": None, "indice": None, "automatico": expansion == "auto",
                "terminos": [], "determinante": a[0][0]}
    return _desarrollar(a, expansion)
