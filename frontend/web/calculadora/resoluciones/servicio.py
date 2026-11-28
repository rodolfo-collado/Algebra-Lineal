"""Guardar una resolución recién calculada y prepararla para volver a abrirla.

Las dos funciones públicas reciben el contexto que la vista de la herramienta ya armó;
no calculan nada. Un fallo del cuaderno nunca impide mostrar el resultado.
"""

import logging
from datetime import datetime

from django.http import QueryDict
from django.urls import NoReverseMatch, reverse

from .. import catalogo
from . import contrato, registro
from .almacen import AlmacenFuturo, AlmacenNoDisponible, CuadernoLleno, ahora, almacen


LOG = logging.getLogger(__name__)
NO_DISPONIBLE = "El cuaderno no está disponible en este momento; este resultado no se guardó. Tus resoluciones anteriores siguen a salvo."


def url_reabrir(ruta, identificador):
    try:
        return f"{reverse(f'calculadora:{ruta}')}?resolucion={identificador}#resultado"
    except NoReverseMatch:
        return None


def nombre_por_defecto(herramienta, entrada):
    """«Herramienta · lo que se escribió»: la función, la expresión, el número o el tamaño."""
    def valor(clave):
        return " ".join((entrada.get(clave) or [""])[0].split())

    detalle = ""
    if valor("funcion"):
        detalle = f"f(x) = {valor('funcion')}"
    elif valor("expresion"):
        detalle = valor("expresion")
    elif valor("sistema") and valor("tipo_entrada") != "matriz":
        detalle = valor("sistema")
    elif valor("numero"):
        detalle = valor("numero")
    elif valor("orden"):
        detalle = f"{valor('orden')}×{valor('orden')}"
    else:
        filas, columnas = (valor("filas"), valor("columnas")) if valor("filas") else (valor("ecuaciones"), valor("variables"))
        if filas and columnas:
            detalle = f"{filas}×{columnas}"
    nombre = f"{herramienta} · {detalle}" if detalle else herramienta
    return nombre if len(nombre) <= 80 else nombre[:79] + "…"


def _aviso(identificador, estado, **extra):
    """Lo que necesita el aviso de la página: la ficha y los ejercicios para agrupar."""
    datos = {"estado": estado, "id": identificador, **extra}
    try:
        cuaderno = almacen()
        ficha = cuaderno.obtener(identificador, documento=False) if identificador else None
        ejercicios = cuaderno.ejercicios()
    except AlmacenNoDisponible:
        return datos
    if ficha:
        try:
            fecha = datetime.fromisoformat(ficha["creado"])
        except ValueError:
            fecha = None
        datos.update(nombre=ficha["nombre"], creado=ficha["creado"], fecha=fecha, ejercicio=next(
            (e for e in ejercicios if e["id"] == ficha["ejercicio"]), None))
    datos["ejercicios"] = ejercicios
    return datos


def guardar(request, adaptador, contexto):
    """Guarda la resolución válida de un POST; devuelve el aviso o None si no hubo resultado."""
    if not adaptador.es_valida(contexto):
        return None
    herramienta = catalogo.herramienta_por_ruta(request.resolver_match)
    ruta = registro.ruta_canonica(request.resolver_match)
    entrada = contrato.entrada_de(request.POST)
    nombre = nombre_por_defecto(adaptador.nombre or herramienta.nombre, entrada)
    try:
        doc = contrato.documento(
            herramienta=herramienta.id, nombre_herramienta=herramienta.nombre, ruta=ruta, esquema=adaptador.esquema,
            entrada=entrada, resultado={clave: contexto.get(clave) for clave in adaptador.claves},
            creado=ahora(), resumen=adaptador.resumir(contexto), grafica=adaptador.graficar(contexto),
        )
        identificador, nueva = almacen().guardar(
            huella=contrato.huella(herramienta.id, adaptador.esquema, entrada, adaptador.ignorar),
            ruta=ruta, herramienta=herramienta.id, nombre=nombre, documento=contrato.serializar(doc),
        )
    except contrato.NoCodificable:
        LOG.exception("La resolución de %s no se pudo codificar.", ruta)
        return {"estado": "no_guardada", "motivo": "Esta resolución todavía no se puede guardar en el cuaderno."}
    except CuadernoLleno as error:
        return {"estado": "no_guardada", "motivo": str(error)}
    except AlmacenNoDisponible as error:
        LOG.warning("El cuaderno no estaba disponible al guardar: %s", error)
        return {"estado": "no_guardada", "motivo": NO_DISPONIBLE}
    return _aviso(identificador, "guardada" if nueva else "existente", url=url_reabrir(ruta, identificador))


def abrir(valor, resolver_match):
    """Lee la resolución pedida en ?resolucion=… sin decidir todavía cómo mostrarla."""
    try:
        identificador = int(valor)
        encontrado = almacen().obtener(identificador)
    except ValueError:
        return {"estado": "inexistente"}
    except AlmacenNoDisponible as error:
        return {"estado": "no_disponible", "motivo": str(error) if isinstance(error, AlmacenFuturo) else NO_DISPONIBLE}
    if encontrado is None:
        return {"estado": "inexistente"}
    ficha, texto = encontrado
    abierta = {"id": identificador, "ficha": ficha}
    ruta = registro.ruta_canonica(resolver_match)
    if ficha["ruta"] != ruta:
        return abierta | {"estado": "otra_ruta", "url": url_reabrir(ficha["ruta"], identificador)}
    try:
        doc = contrato.leer(texto)
    except contrato.DocumentoFuturo:
        return abierta | {"estado": "futuro"}
    except contrato.DocumentoInvalido:
        return abierta | {"estado": "danado"}
    datos = QueryDict(mutable=True)
    for clave, valores in doc["entrada"].items():
        datos.setlist(clave, valores)
    abierta.update(datos=datos, documento=doc)
    if doc["herramienta"]["esquema"] != registro.ADAPTADORES[ruta].esquema:
        return abierta | {"estado": "antiguo"}
    try:
        abierta["resultado"] = contrato.decodificar(doc["resultado"])
    except (ValueError, TypeError, ZeroDivisionError, ArithmeticError):
        return abierta | {"estado": "danado"}
    return abierta | {"estado": "abierta"}


def reabrir(abierta, adaptador, contexto):
    """Sustituye en el contexto de la vista (GET, sin cálculo) el formulario y el resultado guardados."""
    datos = abierta.get("datos")
    if datos is not None:
        try:
            contexto["form"] = adaptador.formulario(contexto["form"], datos)
        except (KeyError, TypeError, ValueError):
            LOG.warning("No se pudo reconstruir el formulario de la resolución %s.", abierta.get("id"), exc_info=True)
    if abierta["estado"] == "abierta":
        contexto.update(abierta["resultado"])
    if "ficha" not in abierta:
        return {"estado": abierta["estado"], "motivo": abierta.get("motivo")}
    return _aviso(abierta["id"], abierta["estado"], url=abierta.get("url"), motivo=abierta.get("motivo"))

