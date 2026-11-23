"""Logotipo de terminal dibujado en cuartos de celda y dos contornos desplazados."""

from dataclasses import dataclass
from functools import lru_cache

from rich.text import Text


# Siluetas sobre una cuadrícula de 12 × 18. Los puntos conservan las
# contraformas de los caracteres y los chaflanes de sus esquinas.
_GLIFOS = (
    (  # P
        ("##########..", 1),
        ("############", 2),
        ("###......###", 5),
        ("############", 2),
        ("##########..", 1),
        ("###.........", 7),
    ),
    (  # Y
        ("###......###", 4),
        (".###....###.", 2),
        ("..###..###..", 2),
        ("...######...", 2),
        ("....####....", 8),
    ),
    (  # G
        ("..##########", 1),
        ("############", 2),
        ("###.........", 5),
        ("###...######", 3),
        ("###......###", 4),
        ("############", 2),
        ("..########..", 1),
    ),
    (  # E
        ("############", 3),
        ("###.........", 4),
        ("##########..", 3),
        ("###.........", 5),
        ("############", 3),
    ),
    (  # B
        ("##########..", 1),
        ("############", 2),
        ("###......###", 4),
        ("###########.", 3),
        ("###......###", 5),
        ("############", 2),
        ("##########..", 1),
    ),
    (  # R
        ("##########..", 1),
        ("############", 2),
        ("###......###", 5),
        ("############", 2),
        ("##########..", 1),
        ("###....###..", 2),
        ("###......###", 5),
    ),
    (  # A
        ("..########..", 2),
        ("############", 2),
        ("###......###", 5),
        ("############", 3),
        ("###......###", 6),
    ),
)
_PASTEL = ("#c8a9f6", "#b5b8f3", "#a0c9ef", "#8cd9ec", "#90deda", "#98e0c6", "#a1e2ae")
_CLARO = ("#69458a", "#5d508e", "#3d5d88", "#006779", "#146f67", "#237051", "#256a3c")


@dataclass(frozen=True)
class Escala:
    ancho: int
    alto: int
    desplazamientos: tuple[tuple[int, int], ...]
    separacion: int

    @property
    def columnas(self):
        ancho_glifo = self.ancho + max(x for x, _ in self.desplazamientos)
        ancho_marca = len(_GLIFOS) * ancho_glifo + (len(_GLIFOS) - 1) * self.separacion
        return (ancho_marca + 1) // 2

    @property
    def filas(self):
        alto_glifo = self.alto + max(y for _, y in self.desplazamientos)
        return (alto_glifo + 1) // 2


_COMPACTA = Escala(6, 5, ((1, 1), (1, 0)), 1)


def _mezclar(color, fondo, proporcion):
    canales = (round(int(fondo[i:i + 2], 16) * (1 - proporcion) + int(color[i:i + 2], 16) * proporcion)
               for i in (1, 3, 5))
    return "#" + "".join(f"{canal:02x}" for canal in canales)


def _remuestrear(glifo, ancho, alto):
    originales = [linea for linea, repeticion in glifo for _ in range(repeticion)]
    return {
        (x, y)
        for y in range(alto)
        for x in range(ancho)
        if originales[(2 * y + 1) * len(originales) // (2 * alto)]
                     [(2 * x + 1) * len(originales[0]) // (2 * ancho)] == "#"
    }


def _contraformas(cuerpo, ancho, alto):
    """Vacíos cerrados por el cuerpo del glifo."""
    libres = {(x, y) for x in range(ancho) for y in range(alto)} - cuerpo
    abiertos = {
        (x, y) for x, y in libres
        if x in (0, ancho - 1) or y in (0, alto - 1)
    }
    pendientes = list(abiertos)
    while pendientes:
        x, y = pendientes.pop()
        vecinas = {(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)}
        nuevos = (libres & vecinas) - abiertos
        abiertos.update(nuevos)
        pendientes.extend(nuevos)
    return libres - abiertos


def _contorno(cuerpo):
    return {
        (x, y) for x, y in cuerpo
        if any((x + dx, y + dy) not in cuerpo for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    }


# Bits separados para los píxeles superior izquierdo, superior derecho,
# inferior izquierdo e inferior derecho de la celda de terminal.
_CUADRANTES = " ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█"


def _celda(tintas):
    mascara = sum(1 << i for i, tinta in enumerate(tintas) if tinta is not None)
    if not mascara:
        return " ", None

    capa, estilo = max(tinta for tinta in tintas if tinta is not None)
    if mascara == 15:
        _, fondo = min(tintas)
        frente = sum(1 << i for i, tinta in enumerate(tintas) if tinta == (capa, estilo))
        return _CUADRANTES[frente], f"{estilo} on {fondo}"
    return _CUADRANTES[mascara], estilo


@lru_cache(maxsize=8)
def _dibujar(escala, claro):
    colores = _CLARO if claro else _PASTEL
    fondo = "#f7f4fc" if claro else "#12121c"
    paso = escala.ancho + max(x for x, _ in escala.desplazamientos) + escala.separacion
    pixeles = {}
    for indice, (glifo, color) in enumerate(zip(_GLIFOS, colores)):
        origen = indice * paso
        cuerpo = _remuestrear(glifo, escala.ancho, escala.alto)
        borde = _contorno(cuerpo)
        for capa, ((dx, dy), contraste) in enumerate(zip(escala.desplazamientos, (0.60, 0.86))):
            tinta = (capa, _mezclar(color, fondo, contraste))
            pixeles.update({(x + origen + dx, y + dy): tinta for x, y in borde})
        if escala.ancho < 19:
            for x, y in _contraformas(cuerpo, escala.ancho, escala.alto):
                pixeles.pop((x + origen, y), None)
        pixeles.update({(x + origen, y): (2, color) for x, y in cuerpo})

    izquierda = min(x for x, _ in pixeles) // 2
    derecha = max(x for x, _ in pixeles) // 2
    marca = Text(no_wrap=True, overflow="crop", end="")
    for fila in range(escala.filas):
        if fila:
            marca.append("\n")
        for columna in range(izquierda, derecha + 1):
            tintas = [pixeles.get((columna * 2 + dx, fila * 2 + dy))
                      for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))]
            caracter, estilo = _celda(tintas)
            marca.append(caracter, estilo)
    return marca


def logotipo(ancho, alto, *, claro=False):
    """Devuelve la marca compacta para el encabezado de la terminal."""
    if ancho >= _COMPACTA.columnas + 6 and alto >= 23:
        return _dibujar(_COMPACTA, claro).copy()

    marca = Text(overflow="crop", no_wrap=True, end="")
    for letra, color in zip("PYGEBRA", _CLARO if claro else _PASTEL):
        marca.append(letra, f"bold {color}")
    return marca
