"""Presentación de la conversión entre decimal y romano para la interfaz web."""

from backend.sistemas_numericos import decimal_a_romano, romano_a_decimal


def como_se_forma(partes) -> str:
    """«50 + 10» cuando las partes suman y «1000 − 100» para un par que resta."""
    if len(partes) > 1:
        return " + ".join(str(parte.valor) for parte in partes)
    resta = partes[0].resta
    return f"{resta[0]} − {resta[1]}" if resta else ""


def convertir_romanos(*, direccion: str, numero: str) -> dict:
    """Ejecuta la conversión y arma un diccionario listo para la plantilla.

    No genera HTML: el origen, el resultado, una fila por grupo decimal o por
    símbolo leído y las igualdades del procedimiento como texto.
    """
    if direccion == "decimal_a_romano":
        conversion = decimal_a_romano(numero)
        grupos = conversion.grupos
        return {
            "direccion": direccion,
            "titulo": "Decimal → romano",
            "origen": str(conversion.valor),
            "resultado": conversion.resultado,
            "nombre_resultado": "Romano",
            # 1963 = 1000 + 900 + 60 + 3; con un solo grupo la igualdad no aporta nada.
            "descomposicion": " + ".join(str(grupo.valor) for grupo in grupos) if len(grupos) > 1 else "",
            "filas": tuple(
                {"valor": grupo.valor, "simbolos": grupo.simbolos, "detalle": como_se_forma(grupo.partes)}
                for grupo in grupos
            ),
        }

    conversion = romano_a_decimal(numero)
    lecturas = conversion.lecturas
    return {
        "direccion": direccion,
        "titulo": "Romano → decimal",
        "origen": conversion.texto_normalizado,
        "resultado": str(conversion.resultado),
        "nombre_resultado": "Decimal",
        "suma": " + ".join(str(lectura.valor) for lectura in lecturas) if len(lecturas) > 1 else "",
        "filas": tuple(
            {"valor": lectura.valor, "simbolos": lectura.simbolos, "detalle": como_se_forma((lectura,))}
            for lectura in lecturas
        ),
    }
