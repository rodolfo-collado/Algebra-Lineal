"""Presentación estructurada de conversiones de base para la interfaz web."""

from backend.sistemas_numericos import (
    NOMBRES_BASE,
    SUBINDICES_BASE,
    ConversionDesdeDecimal,
    ConversionHaciaDecimal,
    convertir,
)


def notacion(digitos: str, base: int) -> str:
    """Número con subíndice tipográfico de la base (p. ej. 1101₂)."""
    return f"{digitos}{SUBINDICES_BASE[base]}"


def titulo_direccion(base_origen: int, base_destino: int) -> str:
    return f"{NOMBRES_BASE[base_origen].capitalize()} → {NOMBRES_BASE[base_destino]}"


def _etapa_expansion(conversion: ConversionHaciaDecimal) -> dict:
    significativo = conversion.texto_normalizado.lstrip("0") or "0"
    return {
        "tipo": "expansion",
        "titulo": titulo_direccion(conversion.base_origen, 10),
        "base_entrada": conversion.base_origen,
        "origen": notacion(significativo, conversion.base_origen),
        "destino": notacion(str(conversion.resultado), 10),
        "pasos": conversion.pasos,
        "suma_parcial": " + ".join(str(paso.contribucion) for paso in conversion.pasos),
        "sustituciones_hex": tuple(paso for paso in conversion.pasos if paso.valor >= 10),
    }


def _etapa_division(conversion: ConversionDesdeDecimal) -> dict:
    destino = notacion(conversion.resultado, conversion.base_destino)
    return {
        "tipo": "division",
        "titulo": titulo_direccion(10, conversion.base_destino),
        "base_salida": conversion.base_destino,
        "origen": notacion(str(conversion.valor_decimal), 10),
        "destino": destino,
        "pasos": conversion.pasos,
        "lectura_residuos": (
            f"Los residuos se leen de abajo hacia arriba: {destino}."
            if conversion.pasos
            else f"El cero en cualquier base se escribe {destino}."
        ),
    }


def convertir_entrada(*, numero: str, base_origen: int, base_destino: int) -> dict:
    """Ejecuta la conversión y arma un diccionario listo para la plantilla.

    No genera HTML: solo datos (etapas con sus pasos, notaciones y textos de
    lectura). Con decimal en un extremo hay una etapa; si ninguna base es
    decimal, la expansión posicional y las divisiones sucesivas se encadenan
    y el valor decimal intermedio queda a la vista.
    """
    conversion = convertir(numero, base_origen, base_destino)
    etapas = []
    if conversion.hacia_decimal:
        etapas.append(_etapa_expansion(conversion.hacia_decimal))
    if conversion.desde_decimal:
        etapas.append(_etapa_division(conversion.desde_decimal))

    origen = etapas[0]["origen"]
    destino = notacion(conversion.resultado, base_destino)
    return {
        "titulo": titulo_direccion(base_origen, base_destino),
        "origen": origen,
        "destino": destino,
        "igualdad": f"{origen} = {destino}",
        "base_origen": base_origen,
        "base_destino": base_destino,
        "etapas": tuple(etapas),
        # Solo con dos etapas: el decimal por el que pasa la conversión.
        "intermedio": notacion(str(conversion.valor_decimal), 10) if len(etapas) == 2 else None,
    }
