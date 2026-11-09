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
    # Notación breve que identifica el área en canales y explorador.
    chip: str = ""

    @property
    def ruta(self) -> str:
        return reverse("calculadora:area", kwargs={"area": self.id})

    @property
    def ancla(self) -> str:
        return self.ruta

    @property
    def disponible(self) -> bool:
        return any(categoria.disponible for categoria in CATEGORIAS if categoria.area == self)


@dataclass(frozen=True)
class Categoria:
    id: str
    nombre: str
    area: Area
    descripcion: str = ""
    chip: str = ""

    @property
    def ancla(self) -> str:
        return f"{self.area.ruta}#{self.id}"

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
    # Dos cosas concretas que permite hacer, para el panel destacado de su área.
    puntos: tuple[str, ...] = ()
    # Un dato breve y cierto que invita a experimentar («Para curiosos»).
    curiosidad: str = ""

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
    "algebra-lineal", "Álgebra lineal",
    "Vectores, matrices, sistemas de ecuaciones y sus aplicaciones.", "Ax = b",
)
SISTEMAS_NUMERICOS = Area(
    "sistemas-numericos", "Sistemas numéricos",
    "Representación de números en distintas bases y en numeración romana.", "1011₂",
)
CALCULO = Area("calculo", "Cálculo", "Límites y contenidos posteriores del curso.", "lím")
CONJUNTOS = Area("conjuntos", "Conjuntos", "Definición de conjuntos, sus operaciones y su cardinalidad.", "A ∩ B")
METODOS_NUMERICOS = Area("metodos-numericos", "Métodos numéricos", "Aproximación de raíces de funciones reales.", "f(c) ≈ 0")
AREAS = (ALGEBRA_LINEAL, SISTEMAS_NUMERICOS, METODOS_NUMERICOS, CONJUNTOS, CALCULO)

VECTORES = Categoria(
    "vectores", "Vectores", ALGEBRA_LINEAL,
    "Operaciones con vectores y combinaciones lineales.", "u + v",
)
MATRICES = Categoria(
    "matrices", "Matrices", ALGEBRA_LINEAL,
    "Operaciones con matrices, sistemas de ecuaciones, reducción por filas, la ecuación matricial Ax = b y la matriz inversa.", "[ A ]",
)
BASES_NUMERICAS = Categoria(
    "bases-numericas", "Bases numéricas", SISTEMAS_NUMERICOS,
    "Conversión entre binario, octal, decimal y hexadecimal.", "A₁₆",
)
# Aparte de las bases: la numeración romana no es un sistema posicional.
NUMERACION_ROMANA = Categoria(
    "numeracion-romana", "Numeración romana", SISTEMAS_NUMERICOS,
    "Conversión entre números arábigos y romanos.", "XII",
)
LIMITES = Categoria("limites", "Límites", CALCULO, "Límites de funciones.", "x → a")
CONJUNTOS_FINITOS = Categoria("conjuntos-finitos", "Conjuntos e intervalos", CONJUNTOS,
                            "Operaciones, relaciones, diagramas de Venn, intervalos y cardinalidad.", "{ a, b }")
RAICES = Categoria("raices", "Raíces de ecuaciones", METODOS_NUMERICOS, "Búsqueda de raíces en un intervalo.", "[a, b]")
CATEGORIAS = (VECTORES, MATRICES, BASES_NUMERICAS, NUMERACION_ROMANA, RAICES, CONJUNTOS_FINITOS, LIMITES)


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
    puntos=('Desde ecuaciones o desde la matriz aumentada', 'Pivotes, variables libres y tipo de solución'),
    curiosidad="Las operaciones elementales no cambian las soluciones: solo reescriben el sistema de una forma más fácil de leer.",
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
    puntos=('Suma, resta y multiplicación por escalar', 'Coeficientes de una combinación lineal'),
    curiosidad="Dos vectores no paralelos del plano generan todo ℝ²: cualquier punto es combinación lineal de ellos.",
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
    puntos=('Varias bases de destino a la vez', 'Divisiones sucesivas o expansión posicional'),
    curiosidad="Cada dígito hexadecimal equivale a cuatro binarios: B₁₆ = 1011₂.",
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
    puntos=('En ambos sentidos, del 1 al 3999', 'Avisa cuando un romano no está bien formado'),
    curiosidad="La numeración romana no tiene símbolo para el cero; por eso la conversión empieza en 1.",
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
    puntos=('Suma, producto, escalares y traspuesta', 'Expresiones con varios operandos'),
    curiosidad="El producto de matrices no es conmutativo: en general AB ≠ BA. Pruébalo con dos matrices 2 × 2.",
)

# En Resolver Ax = b, x es la incógnita. Se reutilizan los motores de sistemas
# (Gauss, Gauss-Jordan o ambos) sobre la matriz aumentada [A | b].
ECUACIONES_MATRICIALES = Herramienta(
    id="ecuaciones-matriciales", nombre="Resolver Ax = b", categoria=MATRICES,
    descripcion="Si ya tienes A y b, encuentra x en Ax = b mediante reducción por filas, LU o Regla de Cramer.",
    estado="disponible", route_name="calculadora:ecuaciones-matriciales",
    palabras_clave=("ecuación matricial", "ecuaciones matriciales", "ax=b", "ax = b", "resolver ax=b",
                    "matriz aumentada", "sistema equivalente", "vector b", "incógnita x",
                    "combinación lineal", "conjunto generado", "solución única", "soluciones infinitas",
                    "inconsistente", "resolver sistema", "sistema de ecuaciones", "sistemas de ecuaciones",
                    "cramer", "regla de cramer",
                    "sistema lineal", "sistemas lineales", "ecuaciones lineales"),
    relacionadas=("reduccion-filas", "operaciones-matrices", "operaciones-vectores"),
    invitacion="Si ya tienes A y b, encuentra x en Ax = b.",
    puntos=('Reducción por filas, LU o Regla de Cramer', 'Detecta si no hay solución o hay infinitas'),
    curiosidad="Ax = b tiene solución exactamente cuando b es combinación lineal de las columnas de A.",
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
    relacionadas=("operaciones-matrices", "ecuaciones-matriciales", "determinantes"),
    invitacion="Si necesitas invertir una matriz cuadrada, sigue el procedimiento.",
    puntos=('Gauss-Jordan sobre [A | I]', 'Regla directa para matrices 2 × 2'),
    curiosidad="Una matriz cuadrada es invertible exactamente cuando su determinante es distinto de cero.",
)

# Cinco métodos con el mismo det(A): fórmula 2×2, Sarrus (3×3), cofactores, LU y
# reducción. Comparte ad − bc con Matriz inversa y lleva A hasta ella cuando det(A) ≠ 0.
# Como Matriz inversa, evita «gauss», «pivote» y «reducción», que llevan a Reducción por filas.
DETERMINANTES = Herramienta(
    id="determinantes",
    nombre="Determinantes",
    categoria=MATRICES,
    descripcion="Calcula el determinante de una matriz cuadrada y muestra el procedimiento paso a paso.",
    estado="disponible",
    route_name="calculadora:determinantes",
    palabras_clave=(
        "determinante", "det", "det(a)", "cofactores", "cofactor", "menores", "laplace",
        "sarrus", "regla de sarrus", "lu", "factorización lu", "matriz triangular",
    ),
    relacionadas=("matriz-inversa", "reduccion-filas"),
    invitacion="Calcula det(A) y comprueba si una matriz cuadrada es invertible.",
    puntos=('Cinco métodos con el procedimiento completo', 'Relación con la inversa y los sistemas'),
    curiosidad="Si intercambias dos filas de A, el determinante cambia de signo.",
)

RELACIONES_CONJUNTOS = Herramienta(
    id="relaciones-conjuntos", nombre="Operaciones con conjuntos", categoria=CONJUNTOS_FINITOS,
    descripcion="Define conjuntos, combínalos y compruébalo en un diagrama de Venn o en la recta real.",
    estado="disponible", route_name="calculadora:relaciones-conjuntos",
    palabras_clave=("unión", "intersección", "diferencia", "complemento", "pertenencia", "no pertenencia", "inclusión",
                    "subconjunto", "inclusión propia", "igualdad", "vacío", "anidados", "potencia", "producto cartesiano",
                    "pares ordenados", "intervalos", "recta real", "venn"),
    relacionadas=("cardinalidad-conjuntos",),
    invitacion="Define conjuntos y combínalos con ∪, ∩, ∖ y ∁.",
    puntos=("Diagrama de Venn con los elementos en su región", "Intervalos exactos en la recta real"),
    curiosidad="{1, {1}} tiene dos elementos: un conjunto puede ser elemento de otro sin que sus elementos se mezclen.",
)

CARDINALIDAD_CONJUNTOS = Herramienta(
    id="cardinalidad-conjuntos", nombre="Cardinalidad e inclusión-exclusión", categoria=CONJUNTOS_FINITOS,
    descripcion="Cuenta elementos por regiones de Venn y descubre por qué funciona la inclusión-exclusión.",
    estado="disponible", route_name="calculadora:cardinalidades-conjuntos",
    palabras_clave=("cardinalidad", "inclusión-exclusión", "inclusión y exclusión", "contar", "regiones", "venn",
                    "problemas de conteo", "encuestas"),
    relacionadas=("relaciones-conjuntos",),
    invitacion="Cuenta cuántos hay en A ∪ B sin contar dos veces.",
    puntos=("Datos por regiones o por intersecciones", "Cada región contada exactamente una vez"),
    curiosidad="En |A ∪ B ∪ C| la región común se suma tres veces, se resta tres y se suma una más: cuenta exactamente una vez.",
)

BISECCION = Herramienta(
    id="biseccion", nombre="Método de bisección", categoria=RAICES,
    descripcion="Aproxima una raíz real y explora cómo se reduce el intervalo en una gráfica interactiva.",
    estado="disponible", route_name="calculadora:biseccion",
    palabras_clave=("bisección", "raíz", "raíces", "función", "intervalo", "punto medio", "gráfica", "bolzano"),
    relacionadas=("regla-falsa",),
    invitacion="Busca una raíz de f(x) mediante bisección.",
    puntos=('Gráfica interactiva del intervalo', 'Tabla de iteraciones paso a paso'),
    curiosidad="Cada iteración reduce el intervalo a la mitad: tras 10 pasos mide menos de una milésima del original.",
)

REGLA_FALSA = Herramienta(
    id="regla-falsa", nombre="Método de regla falsa", categoria=RAICES,
    descripcion="Aproxima una raíz real con rectas secantes y sigue en la gráfica cómo cada corte con el eje x se acerca a ella.",
    estado="disponible", route_name="calculadora:regla-falsa",
    palabras_clave=("regla falsa", "falsa posición", "regula falsi", "interpolación lineal", "secante", "raíz", "raíces",
                    "función", "intervalo", "gráfica", "error absoluto"),
    relacionadas=("biseccion",),
    invitacion="Busca una raíz de f(x) mediante regla falsa.",
    puntos=('Recta secante de cada iteración en la gráfica', 'Error absoluto y motivo de parada explicados'),
    curiosidad="Se llama «falsa» porque una recta sustituye a la curva: su corte con el eje x es una posición falsa de la raíz, que cada paso corrige.",
)

HERRAMIENTAS = (
    OPERACIONES_VECTORES,
    OPERACIONES_MATRICES,
    REDUCCION_FILAS,
    ECUACIONES_MATRICIALES,
    MATRIZ_INVERSA,
    DETERMINANTES,
    CONVERSION_BASES,
    CONVERSION_ROMANOS,
    BISECCION,
    REGLA_FALSA,
    RELACIONES_CONJUNTOS,
    CARDINALIDAD_CONJUNTOS,
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


def area_por_id(id_area: str) -> Area | None:
    return next((area for area in AREAS if area.id == id_area), None)


def hermanas(herramienta: Herramienta) -> tuple[tuple[Categoria, tuple[Herramienta, ...]], ...]:
    """Categorías del área de la herramienta, cada una con sus herramientas disponibles."""
    return tuple(
        (categoria, disponibles)
        for categoria in CATEGORIAS if categoria.area == herramienta.area
        if (disponibles := tuple(h for h in herramientas_de(categoria) if h.disponible))
    )
