"""Teclado matemático contextual: cada herramienta declara solo las teclas que usa.

La interfaz muestra notación matemática (x₁, −, a⁄b) y la tecla inserta el
texto que entiende el parser (x1, -, /). Solo se registran teclas con una
inserción real; una tecla sin operación detrás no debe existir.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tecla:
    etiqueta: str
    insercion: str
    nombre: str
    # Cuántos caracteres retrocede el cursor tras insertar: «( )» deja el cursor dentro.
    retroceso: int = 0

    def __post_init__(self):
        if not self.etiqueta.strip() or not self.insercion or not self.nombre.strip():
            raise ValueError("Una tecla necesita etiqueta, inserción y nombre accesible.")
        if not 0 <= self.retroceso <= len(self.insercion):
            raise ValueError("El retroceso debe quedar dentro del texto insertado.")


@dataclass(frozen=True)
class GrupoTeclas:
    nombre: str
    teclas: tuple[Tecla, ...]


@dataclass(frozen=True)
class TecladoContextual:
    id: str
    titulo: str
    grupos: tuple[GrupoTeclas, ...]
    ayuda: str = "Inserta en el campo donde está el cursor."

    @property
    def teclas(self) -> tuple[Tecla, ...]:
        return tuple(tecla for grupo in self.grupos for tecla in grupo.teclas)


def variables(cantidad: int) -> tuple[Tecla, ...]:
    """x₁ … xₙ visibles; el parser recibe x1 … xn."""
    subindices = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    return tuple(
        Tecla(f"x{str(indice).translate(subindices)}", f"x{indice}", f"Variable x{indice}")
        for indice in range(1, cantidad + 1)
    )


OPERACIONES = GrupoTeclas("Operaciones", (
    Tecla("+", "+", "Más"),
    Tecla("−", "-", "Menos"),
    Tecla("a⁄b", "/", "Barra de fracción"),
    Tecla("=", "=", "Igual"),
))

TECLADO_SISTEMA = TecladoContextual(
    id="sistema",
    titulo="Teclado matemático",
    grupos=(
        GrupoTeclas("Variables", variables(4)),
        OPERACIONES,
        GrupoTeclas("Ecuaciones", (
            Tecla("; nueva ecuación", ";\n", "Separar la siguiente ecuación"),
        )),
    ),
)

TECLADO_MATRIZ = TecladoContextual(
    id="matriz",
    titulo="Teclado matemático",
    grupos=(
        GrupoTeclas("Valores", (
            Tecla("−", "-", "Menos"),
            Tecla("a⁄b", "/", "Barra de fracción"),
        )),
    ),
    ayuda="Inserta en la celda donde está el cursor.",
)


def _teclado_digitos(id_teclado: str, titulo: str, simbolos: str) -> TecladoContextual:
    """Teclado de solo dígitos válidos para la base de entrada."""
    return TecladoContextual(
        id=id_teclado,
        titulo=titulo,
        grupos=(
            GrupoTeclas("Dígitos", tuple(
                Tecla(simbolo, simbolo, f"Dígito {simbolo}") for simbolo in simbolos
            )),
        ),
        ayuda="Inserta en el campo del número. También puedes escribir con el teclado físico.",
    )


TECLADO_BINARIO = _teclado_digitos("base-2", "Teclado binario", "01")
TECLADO_OCTAL = _teclado_digitos("base-8", "Teclado octal", "01234567")
TECLADO_DECIMAL = _teclado_digitos("base-10", "Teclado decimal", "0123456789")
TECLADO_HEXADECIMAL = _teclado_digitos("base-16", "Teclado hexadecimal", "0123456789ABCDEF")

TECLADOS_BASE = {
    2: TECLADO_BINARIO,
    8: TECLADO_OCTAL,
    10: TECLADO_DECIMAL,
    16: TECLADO_HEXADECIMAL,
}

TECLADOS = {
    teclado.id: teclado
    for teclado in (
        TECLADO_SISTEMA,
        TECLADO_MATRIZ,
        TECLADO_BINARIO,
        TECLADO_OCTAL,
        TECLADO_DECIMAL,
        TECLADO_HEXADECIMAL,
    )
}
