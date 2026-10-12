"""Regla de Sarrus: tres diagonales que suman y tres que restan."""

from fractions import Fraction

from backend.seguridad_numerica import restar_exacto, sumar_exacto

from .comun import preparar, producto


def sarrus(a):
    """Devuelve las diagonales `positivas` y `negativas` (posiciones, valores, producto) y su resta."""
    a = preparar(a)
    # Sarrus solo se aplica a matrices 3×3.
    if len(a) != 3:
        raise ValueError("La regla de Sarrus solo se aplica a matrices 3×3.")
    grupos = []
    # 1: diagonales ↘ (a₁₁a₂₂a₃₃, …); −1: diagonales ↙ (a₁₃a₂₂a₃₁, …). El módulo 3 repite columnas.
    for direccion in (1, -1):
        diagonales, suma = [], Fraction(0)
        for j in range(3):
            posiciones = [(i, (j + direccion * i) % 3) for i in range(3)]
            valores = [a[i][k] for i, k in posiciones]
            valor = producto(valores)
            suma = sumar_exacto(suma, valor)
            diagonales.append({"posiciones": posiciones, "valores": valores, "producto": valor})
        grupos.append({"diagonales": diagonales, "suma": suma})
    return {"positivas": grupos[0], "negativas": grupos[1],
            "determinante": restar_exacto(grupos[0]["suma"], grupos[1]["suma"])}
