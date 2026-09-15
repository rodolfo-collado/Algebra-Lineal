"""Presentación estructurada de conversiones de base para la interfaz web."""

from backend.sistemas_numericos import (
    NOMBRES_BASE,
    SUBINDICES_BASE,
    base_a_decimal,
    decimal_a_base,
    parsear_decimal,
)


def notacion(digitos: str, base: int) -> str:
    """Número con subíndice tipográfico de la base (p. ej. 1101₂)."""
    return f"{digitos}{SUBINDICES_BASE[base]}"


def convertir_entrada(*, modo: str, base: int, numero: str) -> dict:
    """Ejecuta la conversión y arma un diccionario listo para la plantilla.

    No genera HTML: solo datos (pasos, notaciones, textos de lectura).
    """
    if modo == "desde_decimal":
        valor = parsear_decimal(numero)
        conversion = decimal_a_base(valor, base)
        origen = notacion(str(valor), 10)
        destino = notacion(conversion.resultado, base)
        return {
            "modo": modo,
            "titulo": f"Decimal → {NOMBRES_BASE[base]}",
            "origen": origen,
            "destino": destino,
            "igualdad": f"{origen} = {destino}",
            "base_entrada": 10,
            "base_salida": base,
            "nombre_base_salida": NOMBRES_BASE[base],
            "pasos_division": conversion.pasos,
            "pasos_expansion": (),
            "lectura_residuos": (
                f"Los residuos se leen de abajo hacia arriba: {destino}."
                if conversion.pasos
                else f"El cero en cualquier base se escribe {destino}."
            ),
            "sustituciones_hex": tuple(
                paso for paso in conversion.pasos if paso.residuo >= 10
            ),
        }

    if modo == "hacia_decimal":
        conversion = base_a_decimal(numero, base)
        # Presentación con el texto normalizado (A–F mayúsculas).
        significativo = conversion.texto_normalizado.lstrip("0") or "0"
        origen = notacion(significativo, base)
        destino = notacion(str(conversion.resultado), 10)
        return {
            "modo": modo,
            "titulo": f"{NOMBRES_BASE[base].capitalize()} → decimal",
            "origen": origen,
            "destino": destino,
            "igualdad": f"{origen} = {destino}",
            "base_entrada": base,
            "base_salida": 10,
            "nombre_base_entrada": NOMBRES_BASE[base],
            "pasos_division": (),
            "pasos_expansion": conversion.pasos,
            "suma_parcial": " + ".join(
                str(paso.contribucion) for paso in conversion.pasos
            ),
            "sustituciones_hex": tuple(
                paso for paso in conversion.pasos if paso.valor >= 10
            ),
        }

    raise ValueError("Elige si conviertes desde decimal o hacia decimal.")
