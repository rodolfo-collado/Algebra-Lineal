"""Registro central de herramientas: áreas, categorías, herramientas y sus relaciones.

Es la única fuente de verdad de la navegación, el buscador, el inicio, los
breadcrumbs y las herramientas relacionadas. No usa base de datos: son
estructuras inmutables que se declaran una sola vez por herramienta.
"""

from dataclasses import dataclass
from re import split
from typing import Literal
from unicodedata import category, normalize

from django.urls import reverse


Estado = Literal["disponible", "proximamente"]
PALABRAS_VACIAS = ("de", "a", "al", "el", "la", "los", "las", "un", "una",
                   "calcular", "hallar", "metodo", "pasar")
# Espacios Unicode explícitos: Python y JS no asignan exactamente lo mismo a \s.
SEPARADOR_TERMINOS = r"[\t-\r\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+"


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
        caracter for caracter in normalize("NFD", texto) if not category(caracter).startswith("M")
    )
    return " ".join(t for t in split(SEPARADOR_TERMINOS, sin_acentos.lower()) if t)


def terminos_de(texto: str) -> tuple[str, ...]:
    return tuple(t for t in normalizar(texto).split() if t not in PALABRAS_VACIAS)


def datos_buscador() -> dict:
    """Índice, prioridad y palabras vacías del único catálogo, publicados con json_script."""
    return {
        "palabras_vacias": PALABRAS_VACIAS,
        "separador": SEPARADOR_TERMINOS,
        "herramientas": [
            {"id": h.id, "indice": h.indice, "nombre": normalizar(h.nombre),
             "disponible": h.disponible}
            for h in HERRAMIENTAS
        ],
    }


ALGEBRA_LINEAL = Area(
    "algebra-lineal", "Álgebra Lineal",
    "Vectores, matrices, sistemas de ecuaciones y sus aplicaciones.",
)
SISTEMAS_NUMERICOS = Area(
    "sistemas-numericos", "Sistemas numéricos",
    "Representación de números en distintas bases y en numeración romana.",
)
CALCULO = Area("calculo", "Cálculo", "Límites y contenidos posteriores del curso.")
AREAS = (ALGEBRA_LINEAL, SISTEMAS_NUMERICOS, CALCULO)

VECTORES = Categoria(
    "vectores", "Vectores", ALGEBRA_LINEAL,
    "Operaciones con vectores y combinaciones lineales.",
)
MATRICES = Categoria(
    "matrices", "Matrices", ALGEBRA_LINEAL,
    "Operaciones con matrices, sistemas de ecuaciones, reducción por filas, la ecuación matricial Ax = b y la matriz inversa.",
)
BASES_NUMERICAS = Categoria(
    "bases-numericas", "Bases numéricas", SISTEMAS_NUMERICOS,
    "Conversión entre binario, octal, decimal y hexadecimal.",
)
# Aparte de las bases: la numeración romana no es un sistema posicional.
NUMERACION_ROMANA = Categoria(
    "numeracion-romana", "Numeración romana", SISTEMAS_NUMERICOS,
    "Conversión entre números arábigos y romanos.",
)
LIMITES = Categoria("limites", "Límites", CALCULO, "Límites de funciones.")
CATEGORIAS = (VECTORES, MATRICES, BASES_NUMERICAS, NUMERACION_ROMANA, LIMITES)


# Reducción por filas de [A | b]: método a elegir (o comparar los dos) y
# clasificación, columnas pivote y sistema resultante como bloques opcionales.
REDUCCION_FILAS = Herramienta(
    id="reduccion-filas",
    nombre="Reducción por filas",
    categoria=MATRICES,
    descripcion="Resuelve sistemas de ecuaciones con Gauss o Gauss-Jordan, desde el sistema escrito o una matriz aumentada.",
    estado="disponible",
    route_name="calculadora:reduccion-filas",
    palabras_clave=(
        "reducción", "reducción por filas", "sistema de ecuaciones", "sistemas de ecuaciones",
        "resolver sistema", "matriz aumentada", "gauss", "gauss-jordan", "gauss jordan",
        "eliminación gaussiana", "escalonar", "forma escalonada", "forma escalonada reducida",
        "sustitución regresiva", "procedimiento paso a paso", "clasificación",
        "tipo de solución", "consistente", "inconsistente", "solución única",
        "soluciones infinitas", "variables libres", "pivote", "pivotes", "columnas pivote",
        "variables pivote", "reducir", "matriz", "sistema lineal", "sistemas lineales", "ecuaciones lineales",
    ),
    relacionadas=("ecuaciones-matriciales",),
    invitacion="Parte de un sistema escrito o una matriz aumentada y sigue la reducción.",
)

# Única herramienta de la categoría: la operación (suma, resta, escalar o
# combinación lineal) se elige dentro, igual que el método en Reducción por filas.
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
        "conjunto generado", "dimensión", "componentes", "rn", "sumar", "restar", "multiplicar",
    ),
    relacionadas=("ecuaciones-matriciales", "operaciones-matrices"),
    invitacion="Suma o resta vectores y encuentra coeficientes de una combinación lineal.",
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
        "sistemas numéricos", "conversión de bases", "base", "convertir",
    ),
    relacionadas=("conversion-romanos",),
    invitacion="Cambia un número entre binario, octal, decimal y hexadecimal.",
)

CONVERSION_ROMANOS = Herramienta(
    id="conversion-romanos",
    nombre="Conversión de números romanos",
    categoria=NUMERACION_ROMANA,
    descripcion="Convierte entre números arábigos y romanos, del 1 al 3999, con la descomposición paso a paso.",
    estado="disponible",
    route_name="calculadora:conversion-romanos",
    palabras_clave=(
        "romano", "romanos", "números romanos", "numeración romana",
        "arábigo a romano", "romano a arábigo",
        # Solo para el buscador (no se muestran): quien escriba «decimal» también la encuentra.
        "decimal a romano", "romano a decimal", "convertir",
    ),
    relacionadas=("conversion-bases",),
    invitacion="Convierte entre números arábigos y romanos.",
)

# Una sola herramienta para operaciones simples y compuestas (P26.6): A + B, 2A, AB,
# Ax, Aᵀ o A(B + C) - 2D usan el mismo motor de expresiones. Cómo se explican los
# productos se elige dentro. En Ax el vector x es conocido y solo se calcula el
# producto. Absorbió a Expresiones matriciales: sus palabras clave siguen llevando aquí.
OPERACIONES_MATRICES = Herramienta(
    id="operaciones-matrices", nombre="Operaciones con matrices", categoria=MATRICES,
    descripcion="Realiza y combina operaciones con matrices, vectores y escalares paso a paso.",
    estado="disponible", route_name="calculadora:operaciones-matrices",
    palabras_clave=("matriz", "matrices", "suma", "resta", "escalar", "traspuesta",
                    "transpuesta", "aᵀ", "a^t", "filas", "columnas", "rectangular", "fracciones",
                    "multiplicación de matrices", "producto de matrices", "matriz por matriz",
                    "ax", "matriz por vector", "fila por columna", "regla fila-vector",
                    "producto punto", "combinación lineal", "expresión", "expresiones",
                    "expresiones matriciales", "componer", "combinar", "paréntesis",
                    "multiplicación implícita", "igualdad", "2a", "ab", "au",
                    "matriz desconocida", "vector simbólico", "expresión lineal",
                    "multiplicar", "sumar", "restar", "transponer", "trasponer"),
    relacionadas=("ecuaciones-matriciales", "operaciones-vectores", "matriz-inversa"),
    invitacion="Combina operaciones con matrices, vectores y escalares.",
)

# En Resolver Ax = b, x es la incógnita. Se reutilizan los motores de sistemas
# (Gauss, Gauss-Jordan o ambos) sobre la matriz aumentada [A | b].
ECUACIONES_MATRICIALES = Herramienta(
    id="ecuaciones-matriciales", nombre="Resolver Ax = b", categoria=MATRICES,
    descripcion="Si ya tienes A y b, encuentra x en Ax = b mediante reducción por filas.",
    estado="disponible", route_name="calculadora:ecuaciones-matriciales",
    palabras_clave=("ecuación matricial", "ecuaciones matriciales", "ax=b", "ax = b", "resolver ax=b",
                    "matriz aumentada", "sistema equivalente", "vector b", "incógnita x",
                    "combinación lineal", "conjunto generado", "solución única", "soluciones infinitas",
                    "inconsistente", "resolver sistema", "sistema de ecuaciones", "sistemas de ecuaciones",
                    "sistema lineal", "sistemas lineales", "ecuaciones lineales"),
    relacionadas=("reduccion-filas", "operaciones-matrices", "operaciones-vectores"),
    invitacion="Si ya tienes A y b, encuentra x en Ax = b.",
)

# Solo para matrices cuadradas. El método (Gauss-Jordan o la regla 2×2) se elige
# dentro; las palabras clave evitan «gauss» y «pivote», que llevan a Reducción por filas.
MATRIZ_INVERSA = Herramienta(
    id="matriz-inversa",
    nombre="Matriz inversa",
    categoria=MATRICES,
    descripcion="Calcula la inversa de una matriz cuadrada y muestra el procedimiento paso a paso.",
    estado="disponible",
    route_name="calculadora:matriz-inversa",
    palabras_clave=(
        "inversa", "matriz inversa", "inversa de una matriz", "a⁻¹", "a^-1", "invertible",
        "no invertible", "matriz singular", "matriz identidad", "identidad", "matriz cuadrada", "2x2", "2×2", "invertir",
    ),
    relacionadas=("operaciones-matrices", "ecuaciones-matriciales"),
    invitacion="Si necesitas invertir una matriz cuadrada, sigue el procedimiento.",
)

HERRAMIENTAS = (
    OPERACIONES_VECTORES,
    OPERACIONES_MATRICES,
    REDUCCION_FILAS,
    ECUACIONES_MATRICIALES,
    MATRIZ_INVERSA,
    CONVERSION_BASES,
    CONVERSION_ROMANOS,
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
    terminos = terminos_de(consulta)
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
    # Los POST históricos de /sistemas/ usan la misma vista y navegación canónica.
    # Es un alias de ruta, nunca una segunda herramienta en el catálogo.
    if resolver_match.view_name == "calculadora:sistemas":
        return REDUCCION_FILAS
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
