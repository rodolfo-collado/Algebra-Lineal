"""Controles de entrada, historial y tablas de PyGebra."""

from itertools import groupby
import os
from pathlib import Path
import re
import subprocess

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Collapsible, DataTable, Input, OptionList, Static

from .adaptador import Linea, Tabla
from .conjuntos import DIALOGOS_CONJUNTOS, GraficaConjuntos
from .graficas import Grafica


class EntradaComando(Input):
    BINDINGS = [
        Binding("up", "app.mover_menu(-1)", show=False),
        Binding("down", "app.mover_menu(1)", show=False),
    ]

    def check_consume_key(self, key, character):
        if key == "space" and self.app.check_action("alternar_casilla", ()):
            return False
        return super().check_consume_key(key, character)

    def action_cursor_left(self, select=False):
        if self.app.comando is None and self.value.startswith("/") and not select:
            self.app.volver_menu()
        else:
            super().action_cursor_left(select)

    def action_cursor_right(self, select=False):
        if self.app.comando is None and self.value.startswith("/") and not select:
            self.app.avanzar_menu()
        else:
            super().action_cursor_right(select)


class TablaInteractiva(DataTable):
    DEFAULT_CSS = """
    TablaInteractiva {
        width: auto;
        min-width: 20;
        max-width: 100%;
        height: auto;
        max-height: 15;
        border: round $primary 45%;
        margin-bottom: 1;
        background: $background;
        scrollbar-size: 1 1;

        & > .datatable--header {
            background: $primary 15%;
            color: $primary;
            text-style: bold;
        }
        & > .datatable--even-row { background: $surface; }
        & > .datatable--odd-row { background: $background; }
        &:focus { border: round $primary; }
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "copiar('celda')", show=False),
        Binding("ctrl+r", "copiar('fila')", show=False),
        Binding("ctrl+t", "copiar('tabla')", show=False),
    ]

    def __init__(self, tabla):
        super().__init__(show_header=bool(tabla.columnas), show_cursor=False, zebra_stripes=True)
        self.tabla = tabla

    def on_mount(self):
        ancho = max(len(self.tabla.columnas), max(map(len, self.tabla.filas)))
        columnas = (*self.tabla.columnas, *("" for _ in range(ancho - len(self.tabla.columnas))))
        # Los encabezados e identificadores pueden contener corchetes matemáticos.
        self.add_columns(*map(Text, columnas))
        for fila in self.tabla.filas:
            valores = [Text(valor, justify="right" if re.fullmatch(r"[-−+]?\d[\d.,/]*(?:e[+-]?\d+)?", valor) else "left")
                       for valor in fila]
            self.add_row(*valores, *("" for _ in range(ancho - len(fila))))

    def action_copiar(self, alcance):
        fila, columna = self.cursor_coordinate
        valores = self.tabla.filas
        if alcance == "tabla":
            texto = "\n".join("\t".join(f) for f in valores)
        elif alcance == "fila":
            texto = "\t".join(valores[fila])
        else:
            texto = valores[fila][columna] if columna < len(valores[fila]) else ""
        self.app.copy_to_clipboard(texto)
        self.app.notify("Copiado")

    def on_focus(self):
        self.show_cursor = True
        self.app.query_one("#teclas", Static).update(
            "Ctrl+C Celda · Ctrl+R Fila · Ctrl+T Tabla · Tab Cambiar foco"
        )

    def on_blur(self):
        self.show_cursor = False
        self.app.actualizar_menu()


class ArchivosBackend(OptionList):
    BINDINGS = [Binding("ctrl+c", "copiar_ruta", show=False)]

    def __init__(self, archivos):
        super().__init__(*(
            Text(archivo, style=f"underline link {Path(archivo).as_uri()}") for archivo in archivos
        ), markup=False)
        self.archivos = archivos

    def action_copiar_ruta(self):
        if self.highlighted is not None:
            self.app.copy_to_clipboard(self.archivos[self.highlighted])
            self.app.notify("Ruta copiada")

    @on(OptionList.OptionSelected)
    def mostrar_archivo(self, evento):
        ruta = Path(self.archivos[evento.option_index])
        try:
            if os.name == "nt":
                subprocess.Popen(["explorer", "/select,", str(ruta)])
            else:
                subprocess.Popen(["xdg-open", str(ruta.parent)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            self.app.notify("Usa Ctrl+C para copiar la ruta.")

    def on_focus(self):
        self.app.mostrar_teclas("↑↓ Elegir archivo · Enter Mostrar carpeta · Ctrl+C Copiar ruta")

    def on_blur(self):
        self.app.actualizar_menu()


class Ficha(Collapsible):
    DEFAULT_CSS = """
    Ficha.ejercicio {
        background: $background;
        padding: 0;
        border: round $secondary 36%;
        margin-bottom: 1;

        &:focus-within { border: round $secondary 65%; background-tint: $foreground 0%; }
        & > CollapsibleTitle {
            width: 1fr;
            padding: 1 2;
            color: $secondary;
            background: $surface;
            text-style: bold;
        }
        &.-collapsed > CollapsibleTitle { padding: 0 2; }
        & > CollapsibleTitle:focus { color: $background; background: $secondary; }
        & > Contents { padding: 1 2 0 2; }

        .bloque { height: auto; width: 1fr; margin-bottom: 1; }
        .bloque-titulo { color: $secondary; text-style: bold; }
        .bloque-seccion {
            color: $primary;
            background: $primary 11%;
            border-left: thick $primary;
            padding: 0 1;
            margin-top: 1;
            text-style: bold;
        }
        .bloque-paso { color: $secondary; text-style: bold; }
        .bloque-nota { color: $foreground 82%; text-style: italic; }
        .bloque-formula { color: $primary; padding-left: 1; }
        .bloque-resultado {
            color: $accent;
            background: $accent 13%;
            border-left: thick $accent;
            padding: 0 1;
            margin-top: 1;
            text-style: bold;
        }
        .bloque-valor, .bloque-exito { color: $accent; text-style: bold; }
        .bloque-aviso {
            color: $warning;
            background: $warning 12%;
            border-left: thick $warning;
            padding: 0 1;
            text-style: bold;
        }
        .bloque-leyenda { color: $primary; margin-bottom: 0; }
        .bloque-grafica { margin: 0 0 1 0; }
        .bloque-archivos { background: $surface; border-top: hkey $secondary 40%; margin-bottom: 1; }
    }
    .holgada Ficha.ejercicio .bloque-seccion, .holgada Ficha.ejercicio .bloque-resultado { margin-top: 2; }
    .corta Ficha.ejercicio > CollapsibleTitle { padding: 0 1; }
    .corta Ficha.ejercicio > Contents { padding: 1 1 0 1; }
    """

    def __init__(self, registro, **kwargs):
        self.registro = registro
        self.cargada = False
        super().__init__(title=registro.titulo, classes="ejercicio", **kwargs)

    async def cargar(self):
        if self.cargada:
            return
        self.cargada = True
        widgets = []
        bloques = tuple(b if isinstance(b, (Linea, Tabla)) else Linea.legada(b) for b in self.registro.bloques)
        grafica = self.registro.grafica
        if grafica is not None:
            if self.registro.comando in DIALOGOS_CONJUNTOS:
                if bloques and isinstance(bloques[0], Linea) and bloques[0].estilo == "titulo":
                    widgets.extend(self._presentar(bloques[:1]))
                    bloques = bloques[1:]
                widgets.append(GraficaConjuntos(grafica, classes="bloque-grafica"))
            else:
                bloques = self._resumen_grafica(bloques, widgets)
                widgets.append(Grafica(grafica, classes="bloque-grafica"))
        widgets.extend(self._presentar(bloques))
        if self.registro.archivos:
            widgets.append(Collapsible(ArchivosBackend(self.registro.archivos), title="Archivos del backend",
                                       classes="bloque-archivos"))
        await self.query_one("Contents").mount(*widgets)

    @staticmethod
    def _presentar(bloques):
        anterior = None
        for estilo, grupo in groupby(bloques, key=lambda b: b.estilo if isinstance(b, Linea) else None):
            if estilo is None:
                for tabla in grupo:
                    if tabla.titulo and tabla.titulo != anterior:
                        yield Static(tabla.titulo, classes="bloque bloque-leyenda", markup=False)
                    yield TablaInteractiva(tabla)
                    anterior = None
            else:
                lineas = list(grupo)
                separador = "\n\n" if estilo == "texto" else "\n"
                yield Static(separador.join(lineas), classes=f"bloque bloque-{estilo}", markup=False)
                anterior = lineas[-1]

    def _resumen_grafica(self, bloques, widgets):
        estilos = {"titulo", "exito", "aviso", "valor", "nota"}
        fin = 0
        for bloque in bloques:
            if not isinstance(bloque, Linea) or bloque.estilo not in estilos:
                break
            fin += 1
        resumen = bloques[:fin]
        # Los registros previos guardaban el veredicto y su valor como dos textos sin estilos.
        if fin == 1 and len(bloques) > 1 and isinstance(bloques[1], Linea) and bloques[1].estilo == "texto":
            estilo = "aviso" if bloques[0].estilo == "aviso" else "valor"
            resumen = (*resumen, Linea(bloques[1], estilo))
            fin = 2
        widgets.extend(self._presentar(resumen))
        return bloques[fin:]

    @on(Collapsible.Expanded)
    async def cargar_al_abrir(self, evento):
        if evento.collapsible is self:
            await self.cargar()


class Paleta(ModalScreen):
    """Inserta la misma notación del teclado contextual de PyGebra web."""

    BINDINGS = [Binding("escape", "dismiss", show=False)]

    def __init__(self, perfil):
        super().__init__()
        self.teclas = perfil.teclas

    def compose(self) -> ComposeResult:
        with Container(id="paleta"):
            yield Static("Símbolos matemáticos", classes="titulo")
            yield OptionList(*(Text(f"{t.etiqueta}  {t.nombre}") for t in self.teclas), markup=False)
            yield Static("↑↓ Elegir · Enter Insertar · Esc Volver", markup=False)

    def on_mount(self):
        self.query_one(OptionList).focus()

    @on(OptionList.OptionSelected)
    def insertar(self, evento):
        tecla = self.teclas[evento.option_index]
        self.dismiss(("^", 0) if tecla.exponente_entero else (tecla.insercion, tecla.retroceso))
