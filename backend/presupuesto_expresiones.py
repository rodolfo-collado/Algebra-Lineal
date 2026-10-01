"""Productos numéricos de un AST, sin evaluar ni construir resultados intermedios.

El perfil de cada subárbol reúne los valores exactos conocidos que participan
en él, incluidos los escalares literales. No predice valores intermedios ni
cancelaciones. La calibración y la composición pertenecen a P26.2.
"""

from dataclasses import dataclass

from backend.expresiones_matriciales.evaluador import _RUTA_LADO, localizar, preparar_simbolo
from backend.expresiones_matriciales.formas import Forma, inferir_producto, inferir_suma, inferir_traspuesta
from backend.expresiones_matriciales.nodos import Igualdad, Negacion, Numero, Producto, Simbolo, Suma, Resta, Traspuesta, nodos
from backend.expresiones_matriciales.parser import analizar_entrada
from backend.presupuesto_computacional import Estimacion, PerfilNumerico, combinar_estimaciones, estimar_producto, perfil_numerico


@dataclass(frozen=True)
class Analisis:
    formas: tuple[Forma, ...] = ()
    productos: tuple[Estimacion, ...] = ()
    total: Estimacion | None = None
    simbolica: bool = False


def _perfil_union(*perfiles):
    return PerfilNumerico(
        max(perfil.bits_numerador for perfil in perfiles),
        max(perfil.bits_denominador for perfil in perfiles),
    )


def _arboles(entrada, nodo):
    if isinstance(entrada, Igualdad):
        if not nodo:
            return ((entrada.izquierda, "izquierdo"), (entrada.derecha, "derecho"))
        coincidencia = _RUTA_LADO.fullmatch(nodo) if isinstance(nodo, str) else None
        if coincidencia:
            prefijo, ruta = coincidencia.groups()
            arbol = entrada.izquierda if prefijo == "izq" else entrada.derecha
            elegido = localizar(arbol, ruta)
            if elegido is not None:
                return ((elegido, "izquierdo" if prefijo == "izq" else "derecho"),)
    else:
        elegido = localizar(entrada, nodo) if nodo else entrada
        if elegido is not None:
            return ((elegido, None),)
    raise ValueError(f"No existe la subexpresión «{nodo}» en esta expresión.")


def analizar_presupuesto(texto, simbolos, nodo=None):
    """Valida formas numéricas y suma cada producto ejecutado en orden de hijos a padre.

    En una igualdad se recorren ambos lados, salvo que se pida una parte. Si
    los árboles seleccionados usan símbolos del flujo simbólico actual, se
    delegan íntegramente al evaluador: este presupuesto no representa ese flujo.
    """
    entorno = {nombre: preparar_simbolo(nombre, definicion) for nombre, definicion in simbolos.items()}
    seleccion = _arboles(analizar_entrada(texto, entorno), nodo)
    if any(isinstance(hoja, Simbolo) and entorno[hoja.nombre].tipo not in ("matriz", "vector", "escalar")
           for arbol, _ in seleccion for hoja in nodos(arbol)):
        return Analisis(simbolica=True)
    perfiles = {}
    for arbol, _ in seleccion:
        for hoja in nodos(arbol):
            if isinstance(hoja, Simbolo) and hoja.nombre not in perfiles:
                valor = entorno[hoja.nombre]
                matriz = valor.valor if valor.tipo == "matriz" else [valor.valor] if valor.tipo == "vector" else [[valor.valor]]
                perfiles[hoja.nombre] = perfil_numerico(matriz)
    productos = []

    def recorrer(actual):
        if isinstance(actual, Numero):
            return Forma("escalar"), perfil_numerico([[actual.valor]])
        if isinstance(actual, Simbolo):
            valor = entorno[actual.nombre]
            return Forma(valor.tipo, valor.filas, valor.columnas), perfiles[actual.nombre]
        hijos = [recorrer(hijo) for hijo in actual.hijos()]
        perfil = _perfil_union(*(perfil for _, perfil in hijos))
        izq = hijos[0][0]
        if isinstance(actual, Negacion):
            return izq, perfil
        if isinstance(actual, Traspuesta):
            return inferir_traspuesta(actual.texto, izq, actual.operando.texto), perfil
        der = hijos[1][0]
        argumentos = (actual.texto, izq, der, actual.izquierda.texto, actual.derecha.texto)
        if isinstance(actual, (Suma, Resta)):
            return inferir_suma(*argumentos), perfil
        if isinstance(actual, Producto):
            forma = inferir_producto(*argumentos)
            if izq.tipo == "matriz" and der.tipo in ("matriz", "vector"):
                productos.append(estimar_producto(izq.filas, izq.columnas, der.columnas or 1, perfil=perfil))
            return forma, perfil
        raise TypeError(type(actual).__name__)

    formas = []
    for arbol, lado in seleccion:
        try:
            formas.append(recorrer(arbol)[0])
        except ValueError as error:
            if lado:
                raise ValueError(f"En el lado {lado}: {error}") from None
            raise
    total = combinar_estimaciones(*productos, operacion="expresion_matricial") if productos else None
    return Analisis(tuple(formas), tuple(productos), total)
