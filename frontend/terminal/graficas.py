"""Gráficas de funciones con ejes, intervalos y render nativo cuando la terminal lo admite."""

from dataclasses import dataclass
from itertools import groupby
import math
import os
import sys
from threading import Lock

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Static


@dataclass(frozen=True)
class PasoGrafico:
    descripcion: str
    puntos: tuple[tuple[float, float], ...]
    segmento: bool = False


@dataclass(frozen=True)
class MarcaGrafica:
    etiqueta: str
    x: float
    y: float | None = None


@dataclass(frozen=True)
class Curva:
    etiqueta: str
    x: tuple[float, ...]
    y: tuple[float | None, ...]
    pasos: tuple[PasoGrafico, ...] = ()
    marcas: tuple[MarcaGrafica, ...] = ()


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


@dataclass(frozen=True)
class Cruce:
    x: float
    intervalo: tuple[float, float] | None = None


@dataclass(frozen=True)
class VistaGrafica:
    curva: Curva
    escalas: tuple[float, float]
    xlim: tuple[float, float]
    ylim: tuple[float, float]
    cruces: tuple[Cruce, ...]
    activo: PasoGrafico | None
    recorte: bool


_IMAGEN = None
_MEDIDA_CELDA = (10, 20)
_LOCK_AGG = Lock()


def preparar_imagenes():
    """Sondea gráficos solo en emuladores conocidos, antes de ceder el teclado a Textual."""
    global _IMAGEN, _MEDIDA_CELDA
    if not (sys.stdin and sys.stdout and sys.stdin.isatty() and sys.stdout.isatty()):
        return
    termino = os.environ.get("TERM", "")
    programa = os.environ.get("TERM_PROGRAM", "")
    if termino == "dumb":
        return
    kitty_virtual = (termino in {"xterm-kitty", "xterm-ghostty"}
                     or programa.lower() == "ghostty" or os.getenv("KITTY_WINDOW_ID")
                     or os.getenv("GHOSTTY_RESOURCES_DIR"))
    if not (kitty_virtual or termino in {"foot", "foot-extra", "wezterm", "xterm-direct"}
            or programa == "WezTerm" or os.getenv("WT_SESSION") or os.getenv("KONSOLE_VERSION")):
        return
    try:
        from textual_image._terminal import get_cell_size
        from textual_image.renderable import Image, SixelImage, TGPImage
        from textual_image.widget import Image as WidgetImagen

        # Algunos emuladores aceptan TGP pero no sus marcadores virtuales.
        if Image is SixelImage or (Image is TGPImage and kitty_virtual):
            _MEDIDA_CELDA = get_cell_size()
            _IMAGEN = WidgetImagen
    except (ArithmeticError, OSError, UnicodeError):
        return


def _tramos(curva):
    for valido, tramo in groupby(zip(curva.x, curva.y), key=lambda p: p[1] is not None):
        if valido:
            yield tuple(tramo)


def detectar_cruces(curva):
    """Candidatos visuales entre muestras consecutivas del mismo tramo del dominio."""
    cruces = []
    for tramo in _tramos(curva):
        for indice, (x, y) in enumerate(tramo):
            anterior = tramo[indice - 1] if indice else None
            siguiente = tramo[indice + 1] if indice + 1 < len(tramo) else None
            if y == 0:
                if (anterior is None or anterior[1] == 0) and (siguiente is None or siguiente[1] == 0):
                    continue
                intervalo = None
                if anterior and siguiente and anterior[1] != 0 and siguiente[1] != 0 and (
                    (anterior[1] < 0) != (siguiente[1] < 0)
                ):
                    intervalo = (anterior[0], siguiente[0])
                cruces.append(Cruce(x, intervalo))
            elif anterior and anterior[1] != 0 and (anterior[1] < 0) != (y < 0):
                xa, ya = anterior
                escala = max(abs(ya), abs(y))
                peso = abs(ya / escala) / (abs(ya / escala) + abs(y / escala))
                cruces.append(Cruce(xa + (x - xa) * peso, (xa, x)))
    return tuple(cruces)


def preparar_vista(curva, paso):
    activo = curva.pasos[paso] if curva.pasos else None
    puntos = tuple((m.x, m.y) for m in curva.marcas) + (activo.puntos if activo else ())
    x = [*curva.x, *(a for a, _ in puntos)]
    y = sorted(v for v in curva.y if v is not None)
    muestras = y + [b for _, b in puntos if b is not None]
    sx = max(map(abs, x), default=0.) or 1.
    sy = max(map(abs, muestras), default=0.) or 1.
    xlim = (min(x) / sx, max(x) / sx)
    if xlim[0] >= xlim[1]:
        xlim = (xlim[0] - .1, xlim[1] + .1)
    abajo, arriba = min(0., min(muestras, default=0.)) / sy, max(0., max(muestras, default=0.)) / sy
    recorte = False
    if len(y) >= 50 and None in curva.y:
        inferior, superior = min(0., y[len(y) // 40]) / sy, max(0., y[-1 - len(y) // 40]) / sy
        if 0 < (superior - inferior) * 4 < arriba - abajo:
            abajo, arriba = inferior, superior
            recorte = True
    margen = (arriba - abajo) * .075 or .2
    return VistaGrafica(curva, (sx, sy), xlim, (abajo - margen, arriba + margen),
                        detectar_cruces(curva), activo, recorte)


def _numero(valor, decimal, precision=6):
    return f"{valor:.{precision}g}".replace(".", decimal)


def _marcas_eje(limites, escala, cantidad, decimal):
    from matplotlib.ticker import MaxNLocator

    localizador = MaxNLocator(nbins=cantidad)
    if 1e-100 < escala < 1e100:
        candidatos = (v / escala for v in localizador.tick_values(*(lim * escala for lim in limites)))
    else:
        candidatos = localizador.tick_values(*limites)
    valores = [float(v) for v in candidatos
               if limites[0] <= v <= limites[1] and math.isfinite(float(v) * escala)]
    etiquetas = [_numero(v * escala, decimal, 4) for v in valores]
    if len(set(etiquetas)) != len(etiquetas):
        etiquetas = [_numero(v * escala, decimal, 16) for v in valores]
    return valores, etiquetas


def _marcas_puntos(vista):
    sx, sy = vista.escalas
    return [
        (marca.x / sx, marca.y / sy if marca.y is not None else None)
        for marca in vista.curva.marcas
    ]


def pintar_texto(vista, ancho, alto, colores, decimal):
    """Plotext conserva las etiquetas como texto legible en emuladores sin imágenes."""
    import plotext as plot

    if ancho < 25:
        return Text("Amplía el panel para ver la escala de la gráfica.", style=colores["texto"])
    # Plotext usa una figura global. El render de texto se ejecuta en el hilo de la TUI.
    plot.clear_figure()
    plot.limit_size(False, False)
    plot.plot_size(ancho, alto)
    plot.canvas_color(_rgb(colores["fondo"]))
    plot.axes_color(_rgb(colores["fondo"]))
    plot.ticks_color(_rgb(colores["texto"]))
    plot.grid(horizontal=False, vertical=False)
    plot.yaxes(left=True, right=False)
    plot.xaxes(lower=True, upper=False)
    plot.xlabel("x")
    plot.ylabel("f(x)")
    sx, sy = vista.escalas
    plot.xlim(*vista.xlim)
    plot.ylim(*vista.ylim)
    plot.xticks(*_marcas_eje(vista.xlim, sx, min(7, max(3, ancho // 13)), decimal))
    plot.yticks(*_marcas_eje(vista.ylim, sy, max(3, alto // 3), decimal))
    for x, _ in _marcas_puntos(vista):
        plot.vertical_line(x, color=_rgb(colores["guia"]))
    if vista.xlim[0] < 0 < vista.xlim[1]:
        plot.vertical_line(0, color=_rgb(colores["ejes"]))
    plot.horizontal_line(0, color=_rgb(colores["ejes"]))
    for tramo in _tramos(vista.curva):
        plot.plot([p[0] / sx for p in tramo], [p[1] / sy for p in tramo],
                  marker="braille" if len(tramo) > 1 else "•", color=_rgb(colores["curva"]))
    if vista.activo and vista.activo.segmento:
        plot.plot([p[0] / sx for p in vista.activo.puntos], [p[1] / sy for p in vista.activo.puntos],
                  marker="braille", color=_rgb(colores["guia"]))
    puntos = [(c.x / sx, 0.) for c in vista.cruces[:24]]
    puntos += [(x, y) for x, y in _marcas_puntos(vista) if y is not None]
    if vista.activo:
        puntos += [(x / sx, y / sy) for x, y in vista.activo.puntos]
    if puntos:
        plot.scatter(*zip(*puntos), marker="●", color=_rgb(colores["acento"]))
    return Text.from_ansi(plot.build().rstrip("\n"))


def _rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def pintar_imagen(vista, ancho, alto, colores, decimal):
    """Rasteriza la figura con Agg. Textual se ocupa de mostrar sus píxeles."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from PIL import Image

    ancho_px = ancho * _MEDIDA_CELDA[0]
    alto_px = alto * _MEDIDA_CELDA[1]
    dpi = 100
    with _LOCK_AGG:
        figura = Figure(figsize=(ancho_px / dpi, alto_px / dpi), dpi=dpi, facecolor=colores["fondo"])
        lienzo = FigureCanvasAgg(figura)
        margen = min(.23, max(.07, 60 / ancho_px))
        figura.subplots_adjust(left=margen, right=.97, bottom=.2, top=.92)
        grafica = figura.add_subplot(111, facecolor=colores["fondo"])
        grafica.tick_params(colors=colores["texto"], labelsize=9, length=3, pad=3)
        grafica.set_xlabel("x", fontsize=10, color=colores["texto"], loc="right", labelpad=1)
        figura.text(.016, .96, "f(x)", fontsize=10, color=colores["texto"], va="top")
        for borde in grafica.spines.values():
            borde.set_color(colores["rejilla"])
        sx, sy = vista.escalas
        grafica.set_xticks(*_marcas_eje(vista.xlim, sx, min(7, max(3, ancho // 13)), decimal))
        grafica.set_yticks(*_marcas_eje(vista.ylim, sy, max(3, alto // 3), decimal))
        grafica.grid(color=colores["rejilla"], linestyle="--", linewidth=.7)
        grafica.set_axisbelow(True)
        grafica.axhline(0, color=colores["ejes"], lw=1.15, zorder=2.2)
        if vista.xlim[0] <= 0 <= vista.xlim[1]:
            grafica.axvline(0, color=colores["ejes"], lw=1.15, zorder=2.2)
        for marca, (x, y) in zip(vista.curva.marcas, _marcas_puntos(vista)):
            color = colores["acento"] if marca.etiqueta == "Raíz" else colores["guia"]
            grafica.axvline(x, color=color, lw=1., alpha=.8, linestyle=":", zorder=2.3)
            if y is not None:
                grafica.scatter(x, y, s=28, color=color, edgecolors=colores["fondo"], zorder=3.1)
        grafica.plot([x / sx for x in vista.curva.x],
                     [y / sy if y is not None else math.nan for y in vista.curva.y],
                     color=colores["curva"], lw=1.9, zorder=2.5)
        if vista.activo:
            x, y = zip(*vista.activo.puntos)
            grafica.plot([p / sx for p in x], [p / sy for p in y], color=colores["guia"], marker="o",
                         markeredgecolor=colores["fondo"], markersize=4.5, zorder=3.2,
                         linestyle="--" if vista.activo.segmento else "none")
        if vista.cruces:
            grafica.scatter([c.x / sx for c in vista.cruces[:24]], [0.] * min(len(vista.cruces), 24), s=33,
                            color=colores["acento"], edgecolors=colores["fondo"], zorder=3.5)
        grafica.set_xlim(*vista.xlim)
        grafica.set_ylim(*vista.ylim)
        lienzo.draw()
        return Image.frombytes("RGBA", lienzo.get_width_height(), lienzo.buffer_rgba())


def _detalle(vista, paso, decimal, colores):
    texto = Text()
    if vista.curva.marcas:
        for marca in vista.curva.marcas:
            if texto:
                texto.append("   ")
            texto.append(f"{marca.etiqueta} = {_numero(marca.x, decimal, 12)}", style=f"bold {colores['guia']}")
            if marca.y is None:
                texto.append(" · fuera del dominio", style=colores["texto"])
            elif marca.etiqueta != "Raíz":
                texto.append(f" · f = {_numero(marca.y, decimal)}", style=colores["texto"])
        texto.append("\n")
    if vista.activo:
        detalle = vista.activo.descripcion.replace(".", decimal)
        texto.append(f"Iteración {paso + 1}/{len(vista.curva.pasos)}  ·  {detalle}\n", style=colores["guia"])
    if vista.cruces:
        texto.append("Cortes estimados con y = 0", style=f"bold {colores['acento']}")
        for cruce in vista.cruces[:3]:
            texto.append(f"\n  ●  x ≈ {_numero(cruce.x, decimal, 8)}", style=colores["acento"])
            if cruce.intervalo:
                a, b = (_numero(x, decimal, 10) for x in cruce.intervalo)
                if a == b:
                    a, b = (_numero(x, decimal, 17) for x in cruce.intervalo)
                texto.append(f"   [{a}; {b}]", style=colores["texto"])
        if len(vista.cruces) > 3:
            texto.append(f"\n  +{len(vista.cruces) - 3} en esta vista", style=colores["texto"])
        if any(c.intervalo for c in vista.cruces[:3]):
            texto.append("\nLos corchetes indican intervalos aproximados con cambio de signo.",
                         style=colores["texto"])
    else:
        valores = [y for y in vista.curva.y if y is not None]
        if valores and all(y == 0 for y in valores):
            texto.append("Todas las muestras válidas están en y = 0.", style=colores["texto"])
        else:
            texto.append("Sin cortes detectados en la vista.", style=colores["texto"])
    if vista.recorte:
        texto.append("\nEscala vertical recortada cerca de discontinuidades.", style=colores["texto"])
    return texto


class Grafica(Vertical, can_focus=True):
    DEFAULT_CSS = """
    Grafica { height: auto; }
    Grafica > .grafica-titulo, Grafica > .grafica-detalle {
        height: auto;
        text-wrap: wrap;
    }
    Grafica > .grafica-titulo { margin-bottom: 1; }
    Grafica > .grafica-detalle { margin-bottom: 1; }
    Grafica > .grafica-texto { height: auto; text-wrap: nowrap; }
    Grafica > .grafica-imagen { width: 100%; display: none; }
    """
    BINDINGS = [
        Binding("left", "mover(-1)", show=False),
        Binding("right", "mover(1)", show=False),
        Binding("home", "primero", show=False),
        Binding("end", "ultimo", show=False),
        Binding("space", "reproducir", show=False),
    ]

    def __init__(self, curva=None, **kwargs):
        super().__init__(**kwargs)
        self.curva = curva
        self.paso = 0
        self.reproductor = None
        self._vista_actual = None
        self._titulo = Static(markup=False, classes="grafica-titulo")
        self._texto = Static(markup=False, classes="grafica-texto")
        self._detalle = Static(markup=False, classes="grafica-detalle")
        self._imagen = _IMAGEN(classes="grafica-imagen") if _IMAGEN else None

    def compose(self) -> ComposeResult:
        yield self._titulo
        yield self._detalle
        yield self._texto
        if self._imagen is not None:
            yield self._imagen

    def on_mount(self):
        self.display = self.curva is not None
        self.pintar()

    def on_resize(self):
        self.pintar()

    def mostrar(self, curva):
        if self.reproductor:
            self.reproductor.stop()
            self.reproductor = None
        self.curva = curva
        self.display = curva is not None
        self.paso = 0
        self._vista_actual = None
        if curva is None and self._imagen is not None:
            self._imagen.display = False
            self._imagen.image = None
        self.pintar()

    def pintar(self):
        if self.curva is None or not self.is_mounted:
            return
        ancho = self.content_size.width
        if ancho <= 0:
            return
        alto = max(8, min(14, self.app.size.height // 3))
        tema = self.app.current_theme
        decimal = self.app.decimal
        clave = (id(self.curva), ancho, alto, self.paso, tema.name, decimal)
        if self._vista_actual == clave:
            return
        self._vista_actual = clave
        colores = {
            "fondo": tema.surface, "texto": tema.foreground,
            "curva": tema.primary, "guia": tema.secondary, "acento": tema.accent,
            "ejes": "#665975" if not tema.dark else "#9c93b6",
            "rejilla": "#d8d0e8" if not tema.dark else "#34334b",
        }
        vista = preparar_vista(self.curva, self.paso)
        titulo = Text("Gráfica de la función\n", style=f"bold {tema.primary}")
        titulo.append(self.curva.etiqueta, style=tema.foreground)
        self._titulo.update(titulo)
        self._detalle.update(_detalle(vista, self.paso, decimal, colores))
        if self._imagen is not None and ancho >= 40:
            if not self._imagen.display:
                self._texto.update(pintar_texto(vista, ancho, alto, colores, decimal))
            self.renderizar(clave, vista, ancho, alto, colores, decimal)
        else:
            self._texto.display = True
            if self._imagen is not None:
                self._imagen.display = False
            self._texto.update(pintar_texto(vista, ancho, alto, colores, decimal))

    @work(thread=True, exclusive=True)
    def renderizar(self, clave, vista, ancho, alto, colores, decimal):
        try:
            imagen = pintar_imagen(vista, ancho, alto, colores, decimal)
        except (OSError, RuntimeError, ValueError, ArithmeticError):
            imagen = None
        if self.is_mounted:
            self.app.call_from_thread(self._mostrar_imagen, clave, imagen, vista, ancho, alto, colores, decimal)

    def _mostrar_imagen(self, clave, imagen, vista, ancho, alto, colores, decimal):
        if self._vista_actual != clave or not self.is_mounted:
            return
        self._imagen.display = imagen is not None
        self._texto.display = imagen is None
        if imagen is None:
            self._texto.update(pintar_texto(vista, ancho, alto, colores, decimal))
            return
        self._imagen.styles.height = alto
        self._imagen.image = imagen

    def action_mover(self, salto):
        if self.curva and self.curva.pasos:
            self.paso = min(len(self.curva.pasos) - 1, max(0, self.paso + salto))
            self.pintar()

    def action_primero(self):
        self.action_mover(-self.paso)

    def action_ultimo(self):
        if self.curva:
            self.action_mover(len(self.curva.pasos))

    def action_reproducir(self):
        if self.reproductor:
            self.reproductor.stop()
            self.reproductor = None
        elif self.curva and self.curva.pasos:
            if self.paso + 1 == len(self.curva.pasos):
                self.action_primero()
            self.reproductor = self.set_interval(.45, self._siguiente)

    def _siguiente(self):
        self.action_mover(1)
        if self.curva is None or self.paso + 1 == len(self.curva.pasos):
            self.action_reproducir()

    def on_focus(self):
        if self.curva and self.curva.pasos:
            self.app.mostrar_teclas("←→ Iteración · Inicio/Fin · Espacio Reproducir · Tab Cambiar foco")

    def on_blur(self):
        self.app.actualizar_menu()
