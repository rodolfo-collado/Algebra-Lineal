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
    "Operaciones con matrices rectangulares, los productos AB y Ax, y la ecuación matricial Ax = b.",
)
BASES_NUMERICAS = Categoria(
    "bases-numericas", "Bases numéricas", SISTEMAS_NUMERICOS,
    "Conversión entre binario, octal, decimal y hexadecimal.",
)
LIMITES = Categoria("limites", "Límites", CALCULO, "Límites de funciones.")
CATEGORIAS = (SISTEMAS_ECUACIONES, VECTORES, MATRICES, BASES_NUMERICAS, LIMITES)


# Única herramienta de la categoría: método a elegir (o comparar los dos) y
# clasificación, columnas pivote y sistema resultante como bloques opcionales.
SISTEMAS = Herramienta(
    id="sistemas",
    nombre="Resolver un sistema",
    categoria=SISTEMAS_ECUACIONES,
    descripcion="Resuelve un sistema y explora sus pasos con Gauss o Gauss-Jordan.",
    estado="disponible",
    route_name="calculadora:sistemas",
    palabras_clave=(
        "resolver sistema", "matriz aumentada", "gauss", "gauss-jordan", "gauss jordan",
        "eliminación gaussiana", "escalonar", "forma escalonada", "forma escalonada reducida",
        "sustitución regresiva", "procedimiento paso a paso", "clasificación",
        "tipo de solución", "consistente", "inconsistente", "solución única",
        "soluciones infinitas", "variables libres", "pivote", "pivotes", "columnas pivote",
        "variables pivote",
    ),
    relacionadas=("ecuaciones-matriciales",),
    invitacion="Resolver el sistema completo",
)

# Única herramienta de la categoría: la operación (suma, resta, escalar o
# combinación lineal) se elige dentro, igual que el método en Resolver un sistema.
OPERACIONES_VECTORES = Herramienta(
    id="operaciones-vectores",
    nombre="Operaciones con vectores",
    categoria=VECTORES,
    descripcion="Opera con vectores o encuentra los coeficientes de una combinación lineal.",
    estado="disponible",
    route_name="calculadora:operaciones-vectores",
    palabras_clave=(
        "vector", "vectores", "suma de vectores", "resta de vectores", "escalar",
        "multiplicación por escalar", "producto por escalar", "combinación lineal",
        "combinacion lineal", "coeficientes", "ecuación vectorial", "span", "generado",
        "conjunto generado", "dimensión", "componentes", "rn",
    ),
    relacionadas=("ecuaciones-matriciales", "expresiones-matriciales"),
    invitacion="Operar con vectores",
)

CONVERSION_BASES = Herramienta(
    id="conversion-bases",
    nombre="Conversión de bases",
    categoria=BASES_NUMERICAS,
    descripcion=(
        "Convierte un número entre binario, octal, decimal y hexadecimal, a una o varias "
        "bases a la vez, con el procedimiento de divisiones sucesivas o expansión posicional."
    ),
    estado="disponible",
    route_name="calculadora:conversion-bases",
    palabras_clave=(
        "binario", "decimal", "octal", "hexadecimal", "bases", "conversión",
        "sistemas numéricos", "conversión de bases", "base",
    ),
    relacionadas=(),
    invitacion="Convertir entre bases numéricas",
)

# La operación (suma, resta, escalar, traspuesta, AB o Ax) y, en los productos,
# el método del procedimiento se eligen dentro, igual que el método en Resolver
# un sistema. En Ax el vector x es conocido y solo se calcula el producto.
OPERACIONES_MATRICES = Herramienta(
    id="operaciones-matrices", nombre="Operaciones con matrices", categoria=MATRICES,
    descripcion="Opera con matrices, calcula AB o Ax y sigue el desarrollo paso a paso.",
    estado="disponible", route_name="calculadora:operaciones-matrices",
    palabras_clave=("matriz", "matrices", "suma", "resta", "escalar", "traspuesta",
                    "transpuesta", "filas", "columnas", "rectangular", "fracciones",
                    "multiplicación de matrices", "producto de matrices", "matriz por matriz",
                    "ax", "matriz por vector", "fila por columna", "regla fila-vector",
                    "producto punto", "combinación lineal"),
    relacionadas=("ecuaciones-matriciales", "expresiones-matriciales"),
    invitacion="Operar con matrices",
)

# Segunda herramienta de Matrices: aquí x es la incógnita. Ax = b es un sistema
# escrito de otra manera, así que se resuelve con los motores de Resolver un
# sistema (Gauss, Gauss-Jordan o ambos) sobre la matriz aumentada [A | b].
ECUACIONES_MATRICIALES = Herramienta(
    id="ecuaciones-matriciales", nombre="Resolver Ax = b", categoria=MATRICES,
    descripcion="Encuentra x y conecta la ecuación matricial Ax = b con su sistema lineal.",
    estado="disponible", route_name="calculadora:ecuaciones-matriciales",
    palabras_clave=("ecuación matricial", "ecuaciones matriciales", "ax=b", "ax = b", "resolver ax=b",
                    "matriz aumentada", "sistema equivalente", "vector b", "incógnita x",
                    "combinación lineal", "conjunto generado", "solución única", "soluciones infinitas",
                    "inconsistente"),
    relacionadas=("sistemas", "operaciones-matrices", "operaciones-vectores", "expresiones-matriciales"),
    invitacion="Resolver una ecuación matricial",
)

EXPRESIONES_MATRICIALES = Herramienta(
    id="expresiones-matriciales",
    nombre="Expresiones matriciales",
    categoria=MATRICES,
    descripcion="Evalúa sumas, restas y productos de matrices, vectores y escalares; compara dos expresiones o determina una matriz desconocida cuando Ax = b es lineal.",
    estado="disponible",
    route_name="calculadora:expresiones-matriciales",
    palabras_clave=(
        "expresión", "expresiones matriciales", "componer", "paréntesis",
        "multiplicación implícita", "igualdad", "2a", "ab", "au",
        "matriz desconocida", "vector simbólico", "expresión lineal",
    ),
    relacionadas=("operaciones-matrices", "ecuaciones-matriciales", "operaciones-vectores"),
    invitacion="Evaluar una expresión matricial",
)

HERRAMIENTAS = (
    SISTEMAS,
    OPERACIONES_VECTORES,
    OPERACIONES_MATRICES,
    EXPRESIONES_MATRICIALES,
    ECUACIONES_MATRICIALES,
    CONVERSION_BASES,
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
