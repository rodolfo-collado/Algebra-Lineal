"""Contrato persistente de una resolución: el documento JSON que se guarda y se reabre.

Un documento describe una resolución sin depender del DOM ni de recalcular:

    {"contrato": "pygebra.resolucion", "version": 1, "app": "0.20.3",
     "creado": "2026-11-28T10:32:00-06:00",
     "herramienta": {"id": "matriz-inversa", "nombre": "Matriz inversa",
                     "ruta": "matriz-inversa", "esquema": 1},
     "entrada": {"orden": ["2"], "celda_A_0_0": ["1"], ...},
     "resultado": {"resultado": {...}},
     "resumen": "det(A) = −2", "grafica": null}

- ``entrada``: los campos tal como se enviaron (listas, como un QueryDict).
- ``resultado``: los datos de presentación exactos que la herramienta calculó, por clave.
  Racionales como cadenas «p/q» o con la etiqueta ``$fraccion``; floats con todas sus cifras.
- ``grafica``: muestras de la gráfica cuando la página las pide aparte (raíces).
- ``esquema``: versión de la forma de ``resultado`` en esa herramienta. Si la herramienta
  cambia esa forma, sube su esquema y los documentos anteriores dejan de reabrirse como
  si fueran actuales: se muestran sus datos y se ofrece calcular de nuevo.

Las etiquetas ``$…`` conservan los tipos que JSON no tiene; ``decodificar`` los restaura.
"""

import dataclasses
import hashlib
import json
import math
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from functools import lru_cache

from actualizador import versiones


CONTRATO = "pygebra.resolucion"
VERSION = 1
# Campos que no describen la matemática: token, firmas de confirmación y botones de acción.
CAMPOS_TECNICOS = frozenset({"csrfmiddlewaretoken", "confirmacion", "eleccion", "accion", "ajustar"})


class NoCodificable(TypeError):
    """El contexto trae un valor que el contrato no sabe guardar (p. ej. un objeto del AST)."""


@lru_cache(maxsize=1)
def version_app():
    try:
        return versiones.version_instalada()
    except (OSError, KeyError, ValueError):
        return ""


def codificar(valor):
    """Convierte datos de presentación en JSON puro, sin perder precisión ni tipos útiles."""
    if valor is None or isinstance(valor, (bool, int, str)):
        # Las enumeraciones de texto (ClasificacionRaices) se guardan por su valor.
        return valor.value if isinstance(valor, Enum) else valor
    if isinstance(valor, float):
        return valor if math.isfinite(valor) else {"$real": repr(valor)}
    if isinstance(valor, Fraction):
        return {"$fraccion": str(valor)}
    if isinstance(valor, Decimal):
        return {"$decimal": str(valor)}
    if isinstance(valor, Enum):
        return codificar(valor.value)
    if isinstance(valor, (list, tuple)):
        return [codificar(v) for v in valor]
    if isinstance(valor, (set, frozenset)):
        # Orden estable: la misma resolución produce el mismo documento.
        return {"$conjunto": sorted((codificar(v) for v in valor), key=_orden)}
    if dataclasses.is_dataclass(valor) and not isinstance(valor, type):
        # Las plantillas leen sus campos por nombre; un dict basta para presentarlos.
        return {campo.name: codificar(getattr(valor, campo.name)) for campo in dataclasses.fields(valor)}
    if isinstance(valor, dict):
        if all(isinstance(clave, str) for clave in valor):
            if any(clave.startswith("$") for clave in valor):
                return {"$dict": [[clave, codificar(v)] for clave, v in valor.items()]}
            return {clave: codificar(v) for clave, v in valor.items()}
        return {"$dict": [[codificar(clave), codificar(v)] for clave, v in valor.items()]}
    raise NoCodificable(f"No se puede guardar un valor de tipo {type(valor).__name__}.")


def _orden(valor):
    return json.dumps(valor, sort_keys=True, ensure_ascii=False)


def decodificar(valor):
    if isinstance(valor, list):
        return [decodificar(v) for v in valor]
    if not isinstance(valor, dict):
        return valor
    if len(valor) == 1:
        (etiqueta, contenido), = valor.items()
        if etiqueta == "$fraccion":
            return Fraction(contenido)
        if etiqueta == "$decimal":
            return Decimal(contenido)
        if etiqueta == "$real":
            return float(contenido)
        if etiqueta == "$conjunto":
            return frozenset(_congelar(decodificar(v)) for v in contenido)
        if etiqueta == "$dict":
            return {_congelar(decodificar(clave)): decodificar(v) for clave, v in contenido}
    return {clave: decodificar(v) for clave, v in valor.items()}


def _congelar(valor):
    """Las listas decodificadas no son hashables; dentro de un conjunto o como clave vuelven a tupla."""
    return tuple(_congelar(v) for v in valor) if isinstance(valor, list) else valor


def entrada_de(datos):
    """Los campos enviados, como dict de listas (el formato de un QueryDict), sin el token CSRF."""
    return {clave: [str(v) for v in datos.getlist(clave)] for clave in datos if clave != "csrfmiddlewaretoken"}


def huella(herramienta, esquema, entrada, ignorar=frozenset()):
    """Identidad matemática de una resolución: herramienta, esquema y entrada relevante.

    Recargar o volver atrás reenvía la misma entrada y produce la misma huella. Las firmas,
    el token y los controles de presentación (``ignorar``) no cuentan; los espacios en los
    extremos de cada valor tampoco. Un esquema nuevo produce otra huella: nunca se reutiliza
    un documento que esta versión ya no sabe mostrar.
    """
    relevante = {
        clave: [valor.strip() for valor in valores]
        for clave, valores in entrada.items()
        if clave not in CAMPOS_TECNICOS and clave not in ignorar
    }
    texto = json.dumps([herramienta, esquema, relevante], sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def documento(*, herramienta, nombre_herramienta, ruta, esquema, entrada, resultado, creado, resumen="", grafica=None):
    """Arma el documento del contrato; ``codificar`` rechaza lo que no pueda guardarse."""
    return {
        "contrato": CONTRATO, "version": VERSION, "app": version_app(), "creado": creado,
        "herramienta": {"id": herramienta, "nombre": nombre_herramienta, "ruta": ruta, "esquema": esquema},
        "entrada": entrada, "resultado": codificar(resultado), "resumen": resumen, "grafica": codificar(grafica),
    }


def serializar(doc):
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


class DocumentoInvalido(ValueError):
    """El texto guardado no es un documento de este contrato (dañado o ajeno)."""


class DocumentoFuturo(ValueError):
    """Lo creó una versión más reciente de PyGebra: se conserva intacto y no se interpreta."""


def leer(texto):
    """Documento validado en su estructura; el resultado sigue codificado hasta usarlo."""
    try:
        doc = json.loads(texto)
    except (TypeError, ValueError) as error:
        raise DocumentoInvalido("El registro no es JSON válido.") from error
    if not isinstance(doc, dict) or doc.get("contrato") != CONTRATO or not isinstance(doc.get("version"), int):
        raise DocumentoInvalido("El registro no es una resolución de PyGebra.")
    if doc["version"] > VERSION:
        raise DocumentoFuturo("La resolución se guardó con una versión más reciente de PyGebra.")
    herramienta = doc.get("herramienta")
    if (not isinstance(herramienta, dict) or not isinstance(herramienta.get("ruta"), str)
            or not isinstance(herramienta.get("esquema"), int) or not isinstance(doc.get("entrada"), dict)
            or not isinstance(doc.get("resultado"), dict)):
        raise DocumentoInvalido("Al registro le faltan datos de la resolución.")
    if not all(isinstance(v, list) and all(isinstance(x, str) for x in v) for v in doc["entrada"].values()):
        raise DocumentoInvalido("La entrada guardada no tiene el formato esperado.")
    return doc
