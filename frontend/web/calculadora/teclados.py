"""Teclado matemático contextual: perfiles declarativos para un único componente.

La interfaz muestra notación matemática (x₁, −, a⁄b) y la tecla inserta el
texto que entiende el parser (x1, -, /). Solo se registran teclas con una
inserción real; una tecla sin operación detrás no debe existir.

Una herramienta no compone teclados: declara en su plantilla el perfil de cada
contenedor de campos (`data-perfil="sistema"`) y publica con `perfiles_para`
solo los perfiles que usa. `teclado.js` muestra las teclas del perfil del
campo activo.
"""

import re
from dataclasses import asdict, dataclass

from backend.sistemas_numericos import BASES_SOPORTADAS, simbolo_de_valor


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

    def __post_init__(self):
        if not self.nombre.strip() or not self.teclas:
            raise ValueError("Un grupo necesita nombre y al menos una tecla.")


@dataclass(frozen=True)
class Perfil:
    """Conjunto de grupos que ve el usuario cuando el cursor está en un campo."""

    id: str
    grupos: tuple[GrupoTeclas, ...]
    ayuda: str = "Inserta en el campo donde está el cursor."

    def __post_init__(self):
        # El id viaja en data-perfil y como clave del JSON: un slug simple.
        if not re.fullmatch(r"[a-z0-9-]+", self.id) or not self.grupos:
            raise ValueError("Un perfil necesita un id en minúsculas y al menos un grupo.")
        for atributo in ("etiqueta", "insercion"):
            valores = [getattr(tecla, atributo) for tecla in self.teclas]
            if len(set(valores)) != len(valores):
                raise ValueError(f"El perfil {self.id} repite una {atributo}.")

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


def digitos(base: int) -> str:
    """Símbolos válidos en la base, con la misma tabla que usa la conversión."""
    return "".join(simbolo_de_valor(valor) for valor in range(base))


MENOS = Tecla("−", "-", "Menos")
FRACCION = Tecla("a⁄b", "/", "Barra de fracción")

# Grupos reutilizables: un perfil se compone eligiendo grupos, no copiando teclas.
VARIABLES = GrupoTeclas("Variables", variables(4))
OPERACIONES = GrupoTeclas("Operaciones", (Tecla("+", "+", "Más"), MENOS, FRACCION, Tecla("=", "=", "Igual")))
ECUACIONES = GrupoTeclas("Ecuaciones", (Tecla("; nueva ecuación", ";\n", "Separar la siguiente ecuación"),))
VALORES = GrupoTeclas("Valores", (MENOS, FRACCION))


def grupo_digitos(base: int) -> GrupoTeclas:
    return GrupoTeclas("Dígitos", tuple(Tecla(simbolo, simbolo, f"Dígito {simbolo}") for simbolo in digitos(base)))


PERFIL_SISTEMA = Perfil("sistema", (VARIABLES, OPERACIONES, ECUACIONES))
PERFIL_NUMERICO = Perfil("numerico", (VALORES,), ayuda="Inserta en la celda donde está el cursor.")
PERFILES_BASE = {
    base: Perfil(
        f"base-{base}",
        (grupo_digitos(base),),
        ayuda="Inserta en el campo del número. También puedes escribir con el teclado físico.",
    )
    for base in sorted(BASES_SOPORTADAS)
}

PERFILES = {perfil.id: perfil for perfil in (PERFIL_SISTEMA, PERFIL_NUMERICO, *PERFILES_BASE.values())}


def perfiles_para(*ids: str) -> dict[str, dict]:
    """Lo que una pantalla publica con json_script: solo los perfiles que declara."""
    return {
        id_: {
            "id": PERFILES[id_].id,
            "ayuda": PERFILES[id_].ayuda,
            "grupos": [
                {"nombre": grupo.nombre, "teclas": [asdict(tecla) for tecla in grupo.teclas]}
                for grupo in PERFILES[id_].grupos
            ],
        }
        for id_ in ids
    }
