"""Navegación de comandos y catálogo compartido con PyGebra web."""

from dataclasses import dataclass

from frontend.web.calculadora.catalogo import AREAS, herramientas_disponibles, normalizar


@dataclass(frozen=True)
class Comando:
    id: str
    titulo: str
    hijos: tuple["Comando", ...] = ()


def _herramientas(area):
    for herramienta in herramientas_disponibles():
        if herramienta.area != area:
            continue
        if herramienta.id == "metodos-abiertos":
            yield Comando("newton-raphson", "Newton-Raphson")
            yield Comando("secante", "Secante")
        else:
            yield Comando(herramienta.id, herramienta.nombre)


RAIZ = Comando("", "PyGebra", (
    Comando("resolver", "Resolver un ejercicio", tuple(
        Comando(area.id, area.nombre, tuple(_herramientas(area)))
        for area in AREAS if area.disponible
    )),
    Comando("historial", "Ir a los ejercicios"),
    Comando("ajustes", "Preferencias", (
        Comando("tema", "Alternar entre tema oscuro y claro"),
        Comando("convencion-decimal", "Alternar entre punto y coma decimal"),
        Comando("densidad", "Alternar el espaciado del procedimiento"),
    )),
    Comando("debugging", "Activar o desactivar la traza del backend"),
))


HERRAMIENTAS = {opcion.id: opcion for area in RAIZ.hijos[0].hijos for opcion in area.hijos}


class Navegacion:
    def __init__(self):
        self.ruta = [RAIZ]
        self.ultimo = {}
        self.indice = 0

    def opciones(self, consulta):
        consulta = normalizar(consulta.lstrip("/"))
        return tuple(
            comando for comando in self.ruta[-1].hijos
            if consulta in normalizar(comando.id) or consulta in normalizar(comando.titulo)
        )

    def mover(self, opciones, salto):
        if opciones:
            self.indice = (self.indice + salto) % len(opciones)

    def entrar(self, comando):
        self.ultimo[self.ruta[-1].id] = comando.id
        self.ruta.append(comando)
        self.indice = 0

    def salir(self):
        if len(self.ruta) > 1:
            anterior = self.ruta.pop()
            self.indice = self.ruta[-1].hijos.index(anterior)

    def reiniciar(self):
        self.ruta = [RAIZ]
        self.indice = 0
