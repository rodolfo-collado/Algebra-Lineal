"""Gráficas Unicode que se ajustan al panel y a los datos visibles."""

from dataclasses import dataclass
import math

from rich.text import Text
from textual.binding import Binding
from textual.widgets import Static


@dataclass(frozen=True)
class PasoGrafico:
    descripcion: str
    puntos: tuple[tuple[float, float], ...]
    segmento: bool = False


@dataclass(frozen=True)
class Curva:
    etiqueta: str
    x: tuple[float, ...]
    y: tuple[float | None, ...]
    pasos: tuple[PasoGrafico, ...] = ()


class Lienzo:
    _bits = ((1, 2, 4, 64), (8, 16, 32, 128))

    def __init__(self, columnas, filas):
        self.ancho = columnas * 2
        self.alto = filas * 4
        self.lineas = [[0] * columnas for _ in range(filas)]
        self.colores = [[0] * columnas for _ in range(filas)]

    def punto(self, x, y, color):
        if 0 <= x < self.ancho and 0 <= y < self.alto:
            self.lineas[y // 4][x // 2] |= self._bits[x % 2][y % 4]
            self.colores[y // 4][x // 2] = max(color, self.colores[y // 4][x // 2])

    def linea(self, a, b, color):
        dx, dy = b[0] - a[0], b[1] - a[1]
        longitud = max(abs(dx), abs(dy), 1)
        for i in range(longitud + 1):
            self.punto(a[0] + round(dx * i / longitud), a[1] + round(dy * i / longitud), color)

    def texto(self, paleta):
        resultado = Text()
        for celdas, colores in zip(self.lineas, self.colores):
            for bits, color in zip(celdas, colores):
                resultado.append(chr(0x2800 + bits) if bits else " ", paleta[color])
            resultado.append("\n")
        return resultado


def _normalizar(valores):
    escala = max(abs(v) for v in valores) or 1
    lo, hi = min(valores) / escala, max(valores) / escala
    if lo == hi:
        lo, hi = lo - .15, hi + .15
    return lo, hi, escala


def pintar_curva(curva, ancho, alto, paso, paleta, decimal):
    lienzo = Lienzo(ancho, alto)
    activo = curva.pasos[paso] if curva.pasos else None
    puntos = activo.puntos if activo else ()
    validas = [v for v in curva.y if v is not None]
    x0, x1, escala_x = _normalizar([*curva.x, *(x for x, _ in puntos)])
    y0, y1, escala_y = _normalizar([0., *validas, *(y for _, y in puntos)])

    def mapa(x, y):
        return (round((x / escala_x - x0) / (x1 - x0) * (lienzo.ancho - 1)),
                round((y1 - y / escala_y) / (y1 - y0) * (lienzo.alto - 1)))

    eje_x, eje_y = mapa(0., 0.)
    lienzo.linea((0, eje_y), (lienzo.ancho - 1, eje_y), 1)
    if 0 <= eje_x < lienzo.ancho:
        lienzo.linea((eje_x, 0), (eje_x, lienzo.alto - 1), 1)

    anterior = None
    for x, y in zip(curva.x, curva.y):
        if y is None:
            anterior = None
            continue
        punto = mapa(x, y)
        if anterior is not None and abs(punto[1] - anterior[1]) < lienzo.alto // 2:
            lienzo.linea(anterior, punto, 2)
        else:
            lienzo.punto(*punto, 2)
        anterior = punto

    if activo and activo.segmento:
        for a, b in zip(puntos, puntos[1:]):
            lienzo.linea(mapa(*a), mapa(*b), 3)
    for x, y in puntos:
        px, py = mapa(x, y)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            lienzo.punto(px + dx, py + dy, 4)

    rango = f"x [{x0 * escala_x:.4g}, {x1 * escala_x:.4g}]   y [{y0 * escala_y:.4g}, {y1 * escala_y:.4g}]"
    texto = Text(f"{curva.etiqueta}\n", style=paleta[2])
    texto.append_text(lienzo.texto(paleta))
    texto.append(rango.replace(".", decimal), paleta[1])
    if activo:
        texto.append(f"\n{paso + 1}/{len(curva.pasos)} · {activo.descripcion.replace('.', decimal)}", paleta[4])
    return texto


class Grafica(Static, can_focus=True):
    BINDINGS = [
        Binding("left", "mover(-1)", show=False),
        Binding("right", "mover(1)", show=False),
        Binding("home", "primero", show=False),
        Binding("end", "ultimo", show=False),
        Binding("space", "reproducir", show=False),
    ]

    def __init__(self, curva=None, **kwargs):
        super().__init__(markup=False, **kwargs)
        self.curva = curva
        self.paso = 0
        self.reproductor = None

    def on_mount(self):
        self.display = self.curva is not None
        self.pintar()

    def on_resize(self):
        self.pintar()

    def mostrar(self, curva):
        self.curva = curva
        self.display = curva is not None
        self.paso = 0
        self.pintar()

    def pintar(self):
        if self.curva is None or not self.is_mounted:
            return
        dimensiones = self.app.size
        ancho = max(1, self.content_size.width)
        claro = self.app.theme == "pygebra-claro"
        paleta = ("", "#786d8b" if claro else "#8f88aa", self.app.current_theme.primary,
                  self.app.current_theme.secondary, self.app.current_theme.accent)
        self.update(pintar_curva(self.curva, ancho, max(3, min(9, dimensiones.height // 5)),
                                 self.paso, paleta, self.app.decimal))

    def action_mover(self, salto):
        if self.curva.pasos:
            self.paso = min(len(self.curva.pasos) - 1, max(0, self.paso + salto))
            self.pintar()

    def action_primero(self):
        self.action_mover(-self.paso)

    def action_ultimo(self):
        self.action_mover(len(self.curva.pasos))

    def action_reproducir(self):
        if self.reproductor:
            self.reproductor.stop()
            self.reproductor = None
        elif self.curva.pasos:
            if self.paso + 1 == len(self.curva.pasos):
                self.action_primero()
            self.reproductor = self.set_interval(.45, self._siguiente)

    def _siguiente(self):
        self.action_mover(1)
        if self.paso + 1 == len(self.curva.pasos):
            self.action_reproducir()

    def on_focus(self):
        if self.curva and self.curva.pasos:
            self.app.mostrar_teclas("←→ Iteración · Inicio/Fin · Espacio Reproducir · Tab Cambiar foco")

    def on_blur(self):
        self.app.actualizar_menu()
