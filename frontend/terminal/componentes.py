"""Controles de entrada, historial y tablas de PyGebra."""

from itertools import groupby
import os
from pathlib import Path
import re
import subprocess

from rich.cells import cell_len
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.content import Content
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


class MenuOpciones(Static):
    def on_resize(self):
        self.app.actualizar_menu()


class TablaInteractiva(DataTable):
    DEFAULT_CSS = """
    TablaInteractiva {
        width: auto;
        max-width: 100%;
        height: auto;
        max-height: 15;
        margin-bottom: 1;
        background: $background;
        scrollbar-size: 1 1;

        & > .datatable--header {
            background: $panel;
            color: $primary;
            text-style: bold;
        }
        & > .datatable--even-row { background: $surface; }
        & > .datatable--odd-row { background: $background; }
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

    def on_blur(self):
        self.show_cursor = False


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


class Ficha(Collapsible):
    DEFAULT_CSS = """
    Ficha.ejercicio {
        background: $background;
        padding: 0;
        border: none;

        &:focus-within { background-tint: $foreground 0%; }
        & > CollapsibleTitle {
            width: 1fr;
            height: 1;
            padding: 0 1;
            border-left: vkey $background;
            color: $foreground;
            background: $surface;
            text-style: bold;
            text-wrap: nowrap;
            text-overflow: ellipsis;
        }
        &.-collapsed > CollapsibleTitle { background: transparent; text-style: none; }
        & > CollapsibleTitle:focus {
            color: $foreground;
            border-left: vkey $secondary;
            background: $secondary 20%;
        }
        & > Contents { padding: 1 2; }

        .bloque { height: auto; width: 1fr; margin-bottom: 1; }
        .bloque-titulo { color: $secondary; text-style: bold; }
        .bloque-seccion {
            color: $primary;
            border-bottom: solid $panel;
            text-style: bold;
        }
        .bloque-paso { color: $secondary; text-style: bold; }
        .bloque-nota { color: $foreground 82%; text-style: italic; }
        .bloque-formula { color: $primary; padding-left: 1; }
        .bloque-resultado {
            width: auto;
            max-width: 100%;
            color: $accent;
            background: $accent 13%;
            padding: 0 1;
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
        .bloque-archivos { background: $background; border: none; padding: 0; margin-top: 1; }
    }
    .holgada Ficha.ejercicio .bloque-seccion, .holgada Ficha.ejercicio .bloque-resultado { margin-top: 1; }
    .corta Ficha.ejercicio > Contents { padding: 1; }
    """

    def __init__(self, registro, **kwargs):
        self.registro = registro
        self.cargada = False
        super().__init__(title=registro.titulo, classes="ejercicio", **kwargs)

    def on_resize(self):
        titulo = self.query_one("CollapsibleTitle")
        ancho = self.size.width - titulo.styles.gutter.width - 2  # Flecha y espacio.
        nombre, _, entrada = self.title.partition(" · ")
        if not entrada or ancho < 19:
            titulo.label = Content(self.title)
            return

        linea = Text(nombre)
        resumen = Text(entrada)
        limite_entrada = max(ancho - linea.cell_len - 2, ancho // 3)
        resumen.truncate(limite_entrada, overflow="ellipsis")
        linea.truncate(ancho - resumen.cell_len - 2, overflow="ellipsis")
        linea.pad_right(ancho - linea.cell_len - resumen.cell_len)
        titulo.label = Content.assemble(linea.plain, (resumen.plain, "$primary"))

    @staticmethod
    def _resumen_romano(bloques):
        """Reúne el origen y el valor de los registros de conversión en una línea."""
        corte = next((i for i, bloque in enumerate(bloques[:-2]) if bloque == "Resultado"), None)
        if corte is None:
            return bloques
        origen, destino = bloques[corte + 1:corte + 3]
        if not isinstance(origen, Linea) or not isinstance(destino, Linea):
            return bloques
        numeral = r"(?:[0-9]+|[IVXLCDM]+)"
        valor = re.fullmatch(rf"= ({numeral})(?: Romano| Arábigo)?", destino)
        if not re.fullmatch(numeral, origen) or valor is None:
            return bloques

        igualdad = f"{origen} = {valor[1]}"
        inicio = next((i for i, bloque in enumerate(bloques[:corte])
                       if isinstance(bloque, Linea) and bloque.estilo == "seccion"), corte)
        procedimiento = bloques[inicio:corte] + bloques[corte + 3:]
        explicacion = "Las partes se escriben una tras otra, de mayor a menor"
        return (
            *bloques[:inicio], Linea(f"Resultado   {igualdad}", "resultado"),
            *(Linea(explicacion + ".", "nota") if bloque == explicacion + ":" else bloque
              for bloque in procedimiento if bloque != igualdad),
        )

    async def cargar(self):
        if self.cargada:
            return
        self.cargada = True
        widgets = []
        bloques = tuple(b if isinstance(b, (Linea, Tabla)) else Linea.legada(b) for b in self.registro.bloques)
        if self.registro.comando == "conversion-romanos":
            bloques = self._resumen_romano(bloques)
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
