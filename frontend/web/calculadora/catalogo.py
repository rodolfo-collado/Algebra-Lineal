"""Registro central de herramientas: áreas, categorías, herramientas y sus relaciones.

Es la única fuente de verdad de la navegación, el buscador, el inicio, los
breadcrumbs y las herramientas relacionadas. No usa base de datos: son
estructuras inmutables que se declaran una sola vez por herramienta.
"""

from dataclasses import dataclass
from typing import Literal
from unicodedata import combining, normalize

from django.urls import reverse


Estado = Literal["disponible", "proximamente"]


@dataclass(frozen=True)
class Area:
    id: str
    nombre: str
    descripcion: str = ""

    @property
    def ancla(self) -> str:
        return f"{reverse('calculadora:inicio')}#{self.id}"

    @property
    def disponible(self) -> bool:
        return any(categoria.disponible for categoria in CATEGORIAS if categoria.area == self)


@dataclass(frozen=True)
class Categoria:
    id: str
    nombre: str
    area: Area
    descripcion: str = ""

    @property
    def ancla(self) -> str:
        return f"{reverse('calculadora:inicio')}#{self.id}"

    @property
    def disponible(self) -> bool:
        return any(herramienta.disponible for herramienta in herramientas_de(self))


@dataclass(frozen=True)
class Herramienta:
    id: str
    nombre: str
    categoria: Categoria
    descripcion: str
    estado: Estado = "proximamente"
    route_name: str | None = None
    ruta_kwargs: tuple[tuple[str, str], ...] = ()
    palabras_clave: tuple[str, ...] = ()
    relacionadas: tuple[str, ...] = ()
    # Frase corta en imperativo para sugerirla desde otra herramienta.
    invitacion: str = ""

    @property
    def disponible(self) -> bool:
        return self.estado == "disponible"

    @property
    def ruta(self) -> str | None:
        if not self.route_name:
            return None
        return reverse(self.route_name, kwargs=dict(self.ruta_kwargs))

    @property
    def area(self) -> Area:
        return self.categoria.area

    @property
    def indice(self) -> str:
        """Texto normalizado que consultan el buscador en Python y el filtro en JS."""
        partes = (
            self.nombre,
            *self.palabras_clave,
            self.categoria.nombre,
            self.area.nombre,
            self.descripcion,
        )
        return normalizar(" ".join(partes))


@dataclass(frozen=True)
class Miga:
    nombre: str
    url: str | None = None
    actual: bool = False


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos y con espacios simples: «Clasificación» ≈ «clasificacion»."""
    sin_acentos = "".join(
        caracter for caracter in normalize("NFD", texto) if not combining(caracter)
    )
    return " ".join(sin_acentos.lower().split())


ALGEBRA_LINEAL = Area(
    "algebra-lineal", "Álgebra Lineal",
    "Sistemas de ecuaciones, vectores y matrices.",
)
SISTEMAS_NUMERICOS = Area(
    "sistemas-numericos", "Sistemas numéricos",
    "Representación de números en distintas bases.",
)
CALCULO = Area("calculo", "Cálculo", "Límites y contenidos posteriores del curso.")
AREAS = (ALGEBRA_LINEAL, SISTEMAS_NUMERICOS, CALCULO)

SISTEMAS_ECUACIONES = Categoria(
    "sistemas-ecuaciones", "Sistemas de ecuaciones", ALGEBRA_LINEAL,
    "Resuelve y analiza sistemas lineales mediante operaciones por filas.",
)
VECTORES = Categoria(
    "vectores", "Vectores", ALGEBRA_LINEAL,
    "Operaciones con vectores y combinaciones lineales.",
)
MATRICES = Categoria(
    "matrices", "Matrices", ALGEBRA_LINEAL,
    "Operaciones entre matrices y ecuaciones matriciales.",
)
BASES_NUMERICAS = Categoria(
    "bases-numericas", "Bases numéricas", SISTEMAS_NUMERICOS,
    "Conversión entre binario, octal, decimal y hexadecimal.",
)
LIMITES = Categoria("limites", "Límites", CALCULO, "Límites de funciones.")
CATEGORIAS = (SISTEMAS_ECUACIONES, VECTORES, MATRICES, BASES_NUMERICAS, LIMITES)


def _herramienta_sistemas(id_, nombre, descripcion, *, palabras_clave, relacionadas, invitacion):
    return Herramienta(
        id=id_,
        nombre=nombre,
        categoria=SISTEMAS_ECUACIONES,
        descripcion=descripcion,
        estado="disponible",
        route_name="calculadora:sistemas-herramienta",
        ruta_kwargs=(("herramienta", id_),),
        palabras_clave=palabras_clave,
        relacionadas=relacionadas,
        invitacion=invitacion,
    )


# Espacio general de la categoría: conserva /sistemas/ con el método a elegir.
SISTEMAS = Herramienta(
    id="sistemas",
    nombre="Resolver un sistema",
    categoria=SISTEMAS_ECUACIONES,
    descripcion=(
        "Elige entre Gauss y Gauss-Jordan y sigue el procedimiento completo, "
        "con la clasificación y las columnas pivote del resultado."
    ),
    estado="disponible",
    route_name="calculadora:sistemas",
    palabras_clave=("resolver sistema", "matriz aumentada", "gauss", "gauss-jordan",
                    "procedimiento paso a paso"),
    # Ya calcula y muestra todo lo que ofrecen las demás herramientas de la
    # categoría: recomendarlas no aportaría nada.
    relacionadas=(),
    invitacion="Resolver el sistema completo",
)
GAUSS = _herramienta_sistemas(
    "gauss", "Método de Gauss",
    "Escalona la matriz aumentada eliminando hacia abajo y resuelve por "
    "sustitución regresiva.",
    palabras_clave=("eliminación gaussiana", "escalonar", "forma escalonada",
                    "sustitución regresiva", "resolver sistema"),
    relacionadas=("gauss-jordan",),
    invitacion="Ver el procedimiento con Gauss",
)
GAUSS_JORDAN = _herramienta_sistemas(
    "gauss-jordan", "Gauss-Jordan",
    "Reduce por completo la matriz aumentada hasta la forma escalonada reducida.",
    palabras_clave=("gauss jordan", "reducción completa", "forma escalonada reducida",
                    "matriz reducida", "resolver sistema"),
    relacionadas=("gauss",),
    invitacion="Ver el procedimiento con Gauss-Jordan",
)
CLASIFICACION = _herramienta_sistemas(
    "clasificacion", "Clasificación de sistemas",
    "Determina si un sistema es consistente de solución única, consistente de "
    "soluciones infinitas o inconsistente.",
    palabras_clave=("tipo de solución", "consistente", "inconsistente",
                    "solución única", "soluciones infinitas", "variables libres"),
    relacionadas=("sistemas",),
    invitacion="Analizar el tipo de solución",
)
COLUMNAS_PIVOTE = _herramienta_sistemas(
    "columnas-pivote", "Columnas pivote",
    "Identifica las columnas pivote de la matriz y las variables que quedan "
    "determinadas por el sistema.",
    palabras_clave=("pivote", "pivotes", "variables pivote", "variables libres"),
    relacionadas=("sistemas",),
    invitacion="Identificar las columnas pivote",
)

HERRAMIENTAS = (
    SISTEMAS,
    GAUSS,
    GAUSS_JORDAN,
    CLASIFICACION,
    COLUMNAS_PIVOTE,
    Herramienta("operaciones-vectores", "Operaciones con vectores", VECTORES,
                "Suma, resta y producto de un vector por un escalar.",
                palabras_clave=("vector", "suma de vectores", "escalar")),
    Herramienta("combinacion-lineal", "Combinación lineal", VECTORES,
                "Expresa un vector como combinación lineal de otros.",
                palabras_clave=("vector", "combinación", "ecuación vectorial")),
    Herramienta("operaciones-matrices", "Operaciones con matrices", MATRICES,
                "Suma, resta y multiplicación de matrices.",
                palabras_clave=("matriz", "suma de matrices", "producto de matrices")),
    Herramienta("ecuaciones-matriciales", "Ecuaciones matriciales", MATRICES,
                "Resuelve ecuaciones cuyas incógnitas son matrices.",
                palabras_clave=("matriz", "ecuación matricial")),
    Herramienta("conversion-bases", "Conversión entre bases", BASES_NUMERICAS,
                "Convierte números entre binario, octal, decimal y hexadecimal.",
                palabras_clave=("binario", "octal", "decimal", "hexadecimal", "base")),
    Herramienta("limites-funciones", "Límites de funciones", LIMITES,
                "Calcula límites de funciones paso a paso.",
                palabras_clave=("límite", "función", "tiende a")),
)

_POR_ID = {herramienta.id: herramienta for herramienta in HERRAMIENTAS}


def herramienta_por_id(id_herramienta: str) -> Herramienta | None:
    return _POR_ID.get(id_herramienta)


def herramientas_de(categoria: Categoria) -> tuple[Herramienta, ...]:
    return tuple(h for h in HERRAMIENTAS if h.categoria == categoria)


def herramientas_disponibles() -> tuple[Herramienta, ...]:
    return tuple(h for h in HERRAMIENTAS if h.disponible)


def arbol() -> tuple[tuple[Area, tuple[tuple[Categoria, tuple[Herramienta, ...]], ...]], ...]:
    """Área → categorías → herramientas, en el orden declarado, incluidas las próximas."""
    return tuple(
        (
            area,
            tuple(
                (categoria, herramientas_de(categoria))
                for categoria in CATEGORIAS
                if categoria.area == area
            ),
        )
        for area in AREAS
    )


def relacionadas_disponibles(herramienta: Herramienta) -> tuple[Herramienta, ...]:
    """Las relaciones usan IDs; solo se presentan destinos ya disponibles."""
    return tuple(
        _POR_ID[id_relacionada]
        for id_relacionada in herramienta.relacionadas
        if _POR_ID[id_relacionada].disponible
    )


def buscar_herramientas(consulta: str, herramientas=HERRAMIENTAS) -> tuple[Herramienta, ...]:
    """Coincidencias reales por nombre, palabras clave, categoría o área.

    Todos los términos deben aparecer. Primero las disponibles y, entre ellas,
    las que coinciden por nombre; después se respeta el orden del registro.
    """
    terminos = normalizar(consulta).split()
    if not terminos:
        return ()

    coincidencias = []
    for herramienta in herramientas:
        indice = herramienta.indice
        if not all(termino in indice for termino in terminos):
            continue
        nombre = normalizar(herramienta.nombre)
        aciertos_nombre = sum(termino in nombre for termino in terminos)
        coincidencias.append((not herramienta.disponible, -aciertos_nombre, herramienta))

    coincidencias.sort(key=lambda entrada: entrada[:2])
    return tuple(herramienta for _, _, herramienta in coincidencias)


def herramienta_por_ruta(resolver_match) -> Herramienta | None:
    """Identifica la herramienta activa a partir de la ruta resuelta por Django."""
    if resolver_match is None:
        return None
    for herramienta in HERRAMIENTAS:
        if herramienta.route_name != resolver_match.view_name:
            continue
        if all(resolver_match.kwargs.get(clave) == valor for clave, valor in herramienta.ruta_kwargs):
            return herramienta
    return None


def migas(herramienta: Herramienta | None) -> tuple[Miga, ...]:
    """Inicio › área › categoría › herramienta; los niveles previos son navegables."""
    if herramienta is None:
        return ()
    categoria = herramienta.categoria
    return (
        Miga("Inicio", reverse("calculadora:inicio")),
        Miga(categoria.area.nombre, categoria.area.ancla),
        Miga(categoria.nombre, categoria.ancla),
        Miga(herramienta.nombre, actual=True),
    )
