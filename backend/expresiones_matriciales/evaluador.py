"""Evalúa un AST de abajo hacia arriba con las operaciones ya existentes.

No hay otra suma ni otro producto: cada nodo llama a `backend.matrices` o
`backend.vectores`. El identificador de un nodo es su ruta en el árbol
(`0`, `0.1`, `0.1.0`), estable para pedir una subexpresión.

Una igualdad evalúa los dos AST y compara esos valores exactos. No resuelve
incógnitas: eso sigue en `backend.ecuaciones_matriciales`.
"""

import re
from dataclasses import dataclass
from fractions import Fraction

from backend.matrices import resolver_operacion_matrices, validar_matriz, validar_vector
from backend.vectores import multiplicar_escalar, restar_vectores, sumar_vectores

from backend.expresiones_matriciales.nodos import Igualdad, Negacion, Numero, Producto, Resta, Simbolo, Suma
from backend.expresiones_matriciales.parser import analizar_entrada, nombre_valido

_RUTA_LADO = re.compile(r"^(izq|der):(\d+(?:\.\d+)*)$")

_SUMA = {
    ("matriz", "matriz"): "suma",
    ("vector", "vector"): "suma_vector",
    ("escalar", "escalar"): "suma_escalar",
}
_RESTA = {
    ("matriz", "matriz"): "resta",
    ("vector", "vector"): "resta_vector",
    ("escalar", "escalar"): "resta_escalar",
}


@dataclass(frozen=True)
class Valor:
    tipo: str
    valor: object
    filas: int | None = None
    columnas: int | None = None


@dataclass(frozen=True)
class Paso:
    id: str
    texto: str
    operacion: str
    tipo: str
    filas: int | None
    columnas: int | None
    resultado: object
    hijos: tuple
    detalle: dict | None
    inicio: int
    fin: int


@dataclass(frozen=True)
class Evaluacion:
    principal: Paso

    def por_id(self):
        return {paso.id: paso for paso in aplanar(self.principal)}


@dataclass(frozen=True)
class Comparacion:
    """Resultado de evaluar los dos lados. `coincide` solo existe si son comparables."""

    texto: str
    izquierda: Paso
    derecha: Paso
    coincide: bool | None
    comparable: bool
    mensaje: str
    tipo: str | None
    filas: int | None
    columnas: int | None


def aplanar(paso):
    """Hijos primero: el orden en que se calculó la expresión."""
    pasos = []
    for hijo in paso.hijos:
        pasos.extend(aplanar(hijo))
    pasos.append(paso)
    return pasos


def localizar(nodo, buscado, ruta="0"):
    if ruta == buscado:
        return nodo
    for indice, hijo in enumerate(nodo.hijos()):
        hallado = localizar(hijo, buscado, f"{ruta}.{indice}")
        if hallado is not None:
            return hallado
    return None


def preparar_simbolo(nombre, definicion):
    """Normaliza un símbolo definido a un valor exacto."""
    if not nombre_valido(nombre):
        raise ValueError(f"«{nombre}» no es un nombre de símbolo. Usa una letra seguida de letras o dígitos, como A, u o k.")
    tipo = definicion.get("tipo") if isinstance(definicion, dict) else None
    valor = definicion.get("valor") if isinstance(definicion, dict) else None
    if tipo == "escalar":
        if isinstance(valor, bool) or not isinstance(valor, (int, Fraction)):
            raise ValueError(f"El escalar {nombre} debe ser un número exacto.")
        return Valor("escalar", Fraction(valor))
    if tipo == "vector":
        valido, mensaje = validar_vector(valor, nombre)
        if not valido:
            raise ValueError(mensaje)
        componentes = [Fraction(componente) for componente in valor]
        return Valor("vector", componentes, len(componentes), None)
    if tipo == "matriz":
        valida, mensaje = validar_matriz(valor)
        if not valida:
            raise ValueError(mensaje)
        matriz = [[Fraction(entrada) for entrada in fila] for fila in valor]
        return Valor("matriz", matriz, len(matriz), len(matriz[0]))
    raise ValueError(f"El símbolo {nombre} necesita un tipo: matriz, vector o escalar.")


def evaluar(texto, simbolos, nodo=None):
    """Evalúa una expresión o compara los dos lados de una igualdad.

    `nodo` pide una subexpresión. En una igualdad la ruta lleva el lado:
    `izq:0.1` o `der:0`. El signo `=` no se evalúa como operación.
    """
    entorno = {}
    for nombre, definicion in simbolos.items():
        if nombre in entorno:
            raise ValueError(f"El símbolo {nombre} está repetido.")
        entorno[nombre] = preparar_simbolo(nombre, definicion)
    entrada = analizar_entrada(texto, entorno)
    if isinstance(entrada, Igualdad):
        if nodo:
            return Evaluacion(_parcial(entrada, entorno, nodo))
        izquierda = _lado(entrada.izquierda, entorno, "izq", "izquierdo")
        derecha = _lado(entrada.derecha, entorno, "der", "derecho")
        return _comparar(entrada.texto, izquierda, derecha)
    if nodo:
        elegido = localizar(entrada, nodo)
        if elegido is None:
            raise ValueError(f"No existe la subexpresión «{nodo}» en esta expresión.")
        return Evaluacion(_evaluar(elegido, entorno, nodo))
    return Evaluacion(_evaluar(entrada, entorno, "0"))


def _lado(nodo, entorno, prefijo, nombre):
    try:
        return _evaluar(nodo, entorno, f"{prefijo}:0")
    except ValueError as error:
        raise ValueError(f"En el lado {nombre}: {error}") from None


def _parcial(igualdad, entorno, nodo):
    coincidencia = _RUTA_LADO.fullmatch(nodo) if isinstance(nodo, str) else None
    if coincidencia is None:
        raise ValueError(f"No existe la subexpresión «{nodo}» en esta expresión.")
    prefijo, ruta = coincidencia.group(1), coincidencia.group(2)
    arbol = igualdad.izquierda if prefijo == "izq" else igualdad.derecha
    elegido = localizar(arbol, ruta)
    if elegido is None:
        raise ValueError(f"No existe la subexpresión «{nodo}» en esta expresión.")
    try:
        return _evaluar(elegido, entorno, nodo)
    except ValueError as error:
        nombre = "izquierdo" if prefijo == "izq" else "derecho"
        raise ValueError(f"En el lado {nombre}: {error}") from None


def _comparar(texto, izquierda, derecha):
    izq, der = _valor(izquierda), _valor(derecha)
    comparable = _comparables(izq, der)
    coincide = izq.valor == der.valor if comparable else None
    return Comparacion(
        texto, izquierda, derecha, coincide, comparable,
        _mensaje(izq, der, coincide, comparable),
        izq.tipo if comparable else None,
        izq.filas if comparable else None,
        izq.columnas if comparable else None,
    )


def _comparables(izq, der):
    if izq.tipo != der.tipo:
        return False
    if izq.tipo == "vector":
        return izq.filas == der.filas
    if izq.tipo == "matriz":
        return (izq.filas, izq.columnas) == (der.filas, der.columnas)
    return True


def _clase(valor):
    if valor.tipo == "matriz":
        return f"una matriz {valor.filas}×{valor.columnas}"
    if valor.tipo == "vector":
        sufijo = "" if valor.filas == 1 else "s"
        return f"un vector de {valor.filas} componente{sufijo}"
    return "un escalar"


def _texto_resultado(valor):
    if valor.tipo == "escalar":
        return str(Fraction(valor.valor))
    if valor.tipo == "vector":
        return "[" + ", ".join(str(Fraction(componente)) for componente in valor.valor) + "]"
    return None


def _mensaje(izq, der, coincide, comparable):
    if not comparable:
        return (
            "No se pueden comparar ambos lados: "
            f"el lado izquierdo es {_clase(izq)} y el lado derecho es {_clase(der)}."
        )
    if coincide:
        texto = _texto_resultado(izq)
        if texto is None:
            return "Ambos lados producen la misma matriz para los valores dados."
        return f"Ambos lados producen {texto} para los valores dados."
    return "Los resultados son diferentes para los valores dados."


def _evaluar(nodo, entorno, ruta):
    hijos = tuple(_evaluar(hijo, entorno, f"{ruta}.{indice}") for indice, hijo in enumerate(nodo.hijos()))
    if isinstance(nodo, Numero):
        valor = Valor("escalar", nodo.valor)
        detalle = None
    elif isinstance(nodo, Simbolo):
        valor = entorno[nodo.nombre]
        detalle = None
    elif isinstance(nodo, Negacion):
        valor, detalle = _negar(hijos[0])
    elif isinstance(nodo, Suma):
        valor, detalle = _operar(nodo.texto, _valor(hijos[0]), _valor(hijos[1]), nodo.izquierda.texto, nodo.derecha.texto, _SUMA, True)
    elif isinstance(nodo, Resta):
        valor, detalle = _operar(nodo.texto, _valor(hijos[0]), _valor(hijos[1]), nodo.izquierda.texto, nodo.derecha.texto, _RESTA, False)
    elif isinstance(nodo, Producto):
        valor, detalle = _multiplicar(nodo.texto, _valor(hijos[0]), _valor(hijos[1]), nodo.izquierda.texto, nodo.derecha.texto)
    else:
        raise TypeError(type(nodo).__name__)
    return Paso(
        ruta, nodo.texto, nodo.operacion, valor.tipo, valor.filas, valor.columnas,
        valor.valor, hijos, detalle, nodo.inicio, nodo.fin,
    )


def _valor(paso):
    return Valor(paso.tipo, paso.resultado, paso.filas, paso.columnas)


def _negar(paso):
    return _multiplicar(f"(-1)·{paso.texto}", Valor("escalar", Fraction(-1)), _valor(paso), "-1", paso.texto)


def describir(valor, texto):
    if valor.tipo == "matriz":
        return f"{texto} es {valor.filas}×{valor.columnas}"
    if valor.tipo == "vector":
        sufijo = "" if valor.filas == 1 else "s"
        return f"{texto} es un vector de {valor.filas} componente{sufijo}"
    return f"{texto} es un escalar"


def _no(texto, izq, der, izq_texto, der_texto, porque):
    raise ValueError(
        f"No se puede calcular {texto}: {describir(izq, izq_texto)} y {describir(der, der_texto)}. {porque}"
    )


def _operar(texto, izq, der, izq_texto, der_texto, tabla, es_suma):
    clave = tabla.get((izq.tipo, der.tipo))
    if clave is None:
        _no(
            texto, izq, der, izq_texto, der_texto,
            "Solo se pueden sumar o restar matrices con matrices, vectores con vectores o escalares con escalares.",
        )
    if clave in ("suma", "resta"):
        if (izq.filas, izq.columnas) != (der.filas, der.columnas):
            _no(texto, izq, der, izq_texto, der_texto, "Para sumar o restar, ambas matrices deben tener las mismas dimensiones.")
        detalle = resolver_operacion_matrices("suma" if es_suma else "resta", izq.valor, der.valor)
        return Valor("matriz", detalle["resultado"], izq.filas, izq.columnas), detalle
    if clave in ("suma_vector", "resta_vector"):
        if izq.filas != der.filas:
            _no(texto, izq, der, izq_texto, der_texto, "Para sumar o restar vectores, ambos deben tener la misma dimensión.")
        resultado = (sumar_vectores if es_suma else restar_vectores)(izq.valor, der.valor)
        return Valor("vector", resultado, len(resultado), None), _detalle_vector(clave, izq.valor, der.valor, resultado)
    resultado = izq.valor + der.valor if es_suma else izq.valor - der.valor
    return Valor("escalar", resultado), None


def _multiplicar(texto, izq, der, izq_texto, der_texto):
    par = (izq.tipo, der.tipo)
    if par == ("escalar", "escalar"):
        return Valor("escalar", izq.valor * der.valor), None
    if par == ("escalar", "vector"):
        resultado = multiplicar_escalar(izq.valor, der.valor)
        return Valor("vector", resultado, len(resultado), None), _detalle_escalar_vector(izq.valor, der.valor, resultado)
    if par == ("vector", "escalar"):
        resultado = multiplicar_escalar(der.valor, izq.valor)
        return Valor("vector", resultado, len(resultado), None), _detalle_escalar_vector(der.valor, izq.valor, resultado)
    if par in (("escalar", "matriz"), ("matriz", "escalar")):
        escalar = izq if izq.tipo == "escalar" else der
        matriz = der if izq.tipo == "escalar" else izq
        detalle = resolver_operacion_matrices("escalar", matriz.valor, escalar=escalar.valor)
        return Valor("matriz", detalle["resultado"], matriz.filas, matriz.columnas), detalle
    if par == ("matriz", "matriz"):
        if izq.columnas != der.filas:
            _no(
                texto, izq, der, izq_texto, der_texto,
                "Para multiplicar matrices, las columnas de la primera deben coincidir con las filas de la segunda.",
            )
        detalle = resolver_operacion_matrices("producto", izq.valor, der.valor)
        filas, columnas = detalle["dimensiones_resultado"]
        return Valor("matriz", detalle["resultado"], filas, columnas), detalle
    if par == ("matriz", "vector"):
        if izq.columnas != der.filas:
            _no(
                texto, izq, der, izq_texto, der_texto,
                "Para multiplicar una matriz por un vector, las columnas de la matriz deben coincidir con las componentes del vector.",
            )
        detalle = resolver_operacion_matrices("matriz_vector", izq.valor, vector=der.valor)
        resultado = [fila[0] for fila in detalle["resultado"]]
        return Valor("vector", resultado, len(resultado), None), detalle
    motivos = {
        ("vector", "vector"): "El producto de dos vectores no está definido aquí; el producto punto no se infiere.",
        ("vector", "matriz"): "El producto de un vector por una matriz no está definido en esta herramienta.",
    }
    _no(texto, izq, der, izq_texto, der_texto, motivos.get(par, "Esa combinación de tipos no tiene producto en esta herramienta."))


def _detalle_vector(operacion, izq, der, resultado):
    return {
        "operacion": operacion,
        "pasos": tuple(
            {"operandos": (Fraction(a), Fraction(b)), "resultado": Fraction(r)}
            for a, b, r in zip(izq, der, resultado)
        ),
    }


def _detalle_escalar_vector(escalar, vector, resultado):
    return {
        "operacion": "escalar_vector",
        "pasos": tuple(
            {"operandos": (Fraction(escalar), Fraction(componente)), "resultado": Fraction(obtenido)}
            for componente, obtenido in zip(vector, resultado)
        ),
    }
