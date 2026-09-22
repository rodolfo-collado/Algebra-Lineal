"""Presentación estructurada de conversiones de base para la interfaz web."""

from collections.abc import Iterable

from backend.sistemas_numericos import (
    NOMBRES_BASE,
    SUBINDICES_BASE,
    ConversionDesdeDecimal,
    ConversionHaciaDecimal,
    convertir_a_varias_bases,
    escribir_decimal_exacto,
)


def notacion(digitos: str, base: int) -> str:
    """Número con subíndice tipográfico de la base (p. ej. 1101₂)."""
    return f"{digitos}{SUBINDICES_BASE[base]}"


def enumerar(nombres: Iterable[str]) -> str:
    """«binario», «binario y octal» o «binario, decimal y hexadecimal»."""
    nombres = list(nombres)
    if len(nombres) <= 1:
        return "".join(nombres)
    return f"{', '.join(nombres[:-1])} y {nombres[-1]}"


def titulo_direccion(base_origen: int, base_destino: int) -> str:
    return f"{NOMBRES_BASE[base_origen].capitalize()} → {NOMBRES_BASE[base_destino]}"


def titulo_conversion(base_origen: int, bases_destino: Iterable[int]) -> str:
    """«Octal → binario, decimal y hexadecimal»: el origen y todos los destinos pedidos."""
    destinos = enumerar(NOMBRES_BASE[base] for base in bases_destino)
    return f"{NOMBRES_BASE[base_origen].capitalize()} → {destinos}"


def _etapa_expansion(conversion: ConversionHaciaDecimal) -> dict:
    entera, punto, fraccionaria = conversion.texto_normalizado.partition(".")
    significativo = (entera.lstrip("0") or "0") + punto + fraccionaria
    return {
        "tipo": "expansion",
        "titulo": titulo_direccion(conversion.base_origen, 10),
        "base_entrada": conversion.base_origen,
        "origen": notacion(significativo, conversion.base_origen),
        "destino": notacion(escribir_decimal_exacto(conversion.resultado), 10),
        "pasos": conversion.pasos,
        "suma_parcial": " + ".join(escribir_decimal_exacto(paso.contribucion) for paso in conversion.pasos),
        "sustituciones_hex": tuple(paso for paso in conversion.pasos if paso.valor >= 10),
    }


def _etapa_division(conversion: ConversionDesdeDecimal) -> dict:
    destino = notacion(conversion.resultado, conversion.base_destino)
    entero = notacion(conversion.parte_entera, conversion.base_destino)
    multiplicaciones = tuple(
        {
            "operacion": (
                f"{escribir_decimal_exacto(paso.fraccion_inicial)} × {paso.base} = "
                f"{escribir_decimal_exacto(paso.producto)}"
            ),
            "digito": (
                f"{paso.digito} → {paso.simbolo_digito}"
                if paso.digito >= 10 else paso.simbolo_digito
            ),
            "restante": escribir_decimal_exacto(paso.fraccion_restante),
        }
        for paso in conversion.multiplicaciones
    )
    periodo = ""
    if conversion.inicio_periodo is not None:
        repetida = conversion.multiplicaciones[conversion.inicio_periodo].fraccion_inicial
        periodo = (
            f"La fracción restante {escribir_decimal_exacto(repetida)} se repite: "
            f"el período {conversion.parte_periodica} comienza en el dígito fraccionario "
            f"{conversion.inicio_periodo + 1}. Los paréntesis indican los dígitos que se repiten."
        )
    return {
        "tipo": "division",
        "titulo": titulo_direccion(10, conversion.base_destino),
        "base_salida": conversion.base_destino,
        "origen": notacion(escribir_decimal_exacto(conversion.valor_decimal), 10),
        "destino": destino,
        "pasos": conversion.pasos,
        "multiplicaciones": multiplicaciones,
        "mostrar_divisiones": bool(conversion.pasos) or not multiplicaciones,
        "periodo": periodo,
        "lectura_fraccion": f"Los dígitos se leen de arriba hacia abajo: {destino}.",
        "lectura_residuos": (
            f"Los residuos se leen de abajo hacia arriba: {entero}."
            if conversion.pasos
            else f"El cero en cualquier base se escribe {destino}."
        ),
    }


def convertir_entrada(*, numero: str, base_origen: int, bases_destino: Iterable[int]) -> dict:
    """Ejecuta la conversión y arma un diccionario listo para la plantilla.

    No genera HTML: solo datos (resultados, etapas con sus pasos, notaciones y
    textos de lectura). Cada etapa aparece una sola vez: si el origen no es
    decimal, la expansión posicional es la etapa compartida y va primero;
    después hay divisiones y multiplicaciones por cada destino no decimal,
    todas desde el mismo valor intermedio. Si se pidió decimal, su resultado es
    ese valor y no genera una etapa propia.
    """
    conversion = convertir_a_varias_bases(numero, base_origen, bases_destino)
    compartida = _etapa_expansion(conversion.hacia_decimal) if conversion.hacia_decimal else None
    divisiones = tuple(
        _etapa_division(destino.desde_decimal)
        for destino in conversion.destinos
        if destino.desde_decimal
    )
    decimal = notacion(escribir_decimal_exacto(conversion.valor_decimal), 10)
    origen = compartida["origen"] if compartida else decimal

    # El origen va aparte y una sola vez; cada resultado solo aporta su escritura y su base.
    resultados = tuple(
        {
            "base": destino.base_destino,
            "nombre": NOMBRES_BASE[destino.base_destino],
            "destino": notacion(destino.resultado, destino.base_destino),
            **({"periodo": destino.desde_decimal.parte_periodica}
               if destino.desde_decimal and destino.desde_decimal.parte_periodica else {}),
        }
        for destino in conversion.destinos
    )

    return {
        "titulo": titulo_conversion(base_origen, conversion.bases_destino),
        "origen": origen,
        "base_origen": base_origen,
        "bases_destino": conversion.bases_destino,
        "resultados": resultados,
        "etapas": ((compartida,) if compartida else ()) + divisiones,
        # Solo cuando la expansión alimenta divisiones: el decimal por el que pasa todo
        # y las escrituras que salen de él (una rama por destino no decimal).
        "intermedio": decimal if compartida and divisiones else None,
        "ramas": tuple(etapa["destino"] for etapa in divisiones) if compartida else (),
        "decimal_pedido": 10 in conversion.bases_destino,
        "tiene_fraccion": conversion.valor_decimal % 1 != 0,
    }
