"""Controles de entrada, historial y tablas de PyGebra."""

import os
from pathlib import Path
import subprocess

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Collapsible, DataTable, Input, OptionList, Static

from .adaptador import Tabla
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
    BINDINGS = [
        Binding("ctrl+c", "copiar('celda')", show=False),
        Binding("ctrl+r", "copiar('fila')", show=False),
        Binding("ctrl+t", "copiar('tabla')", show=False),
    ]

    def __init__(self, tabla):
        super().__init__(show_header=bool(tabla.columnas), zebra_stripes=True)
        self.tabla = tabla

    def on_mount(self):
        ancho = max(len(self.tabla.columnas), max(map(len, self.tabla.filas)))
        columnas = (*self.tabla.columnas, *("" for _ in range(ancho - len(self.tabla.columnas))))
        # Los encabezados e identificadores pueden contener corchetes matemáticos.
        self.add_columns(*map(Text, columnas))
        for fila in self.tabla.filas:
            self.add_row(*map(Text, fila), *("" for _ in range(ancho - len(fila))))
        self.styles.height = min(10, len(self.tabla.filas) + bool(self.tabla.columnas) + 1)
        self.border_title = self.tabla.titulo

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
        self.app.query_one("#teclas", Static).update(
            "Ctrl+C Celda · Ctrl+R Fila · Ctrl+T Tabla · Tab Cambiar foco"
        )

    def on_blur(self):
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
    def __init__(self, registro, **kwargs):
        self.registro = registro
        self.cargada = False
        super().__init__(title=registro.titulo, classes="ejercicio", **kwargs)

    async def cargar(self):
        if self.cargada:
            return
        self.cargada = True
        widgets = []
        bloques = self.registro.bloques
        grafica = self.registro.grafica
        if grafica is not None:
            if self.registro.comando in DIALOGOS_CONJUNTOS:
                widgets.append(GraficaConjuntos(grafica))
            else:
                if len(bloques) >= 2 and all(isinstance(b, str) for b in bloques[:2]):
                    widgets.append(Static("\n".join(bloques[:2]), classes="veredicto", markup=False))
                    bloques = bloques[2:]
                widgets.append(Grafica(grafica))
        lineas = []
        for bloque in bloques:
            if isinstance(bloque, Tabla):
                if lineas:
                    widgets.append(Static("\n".join(lineas), markup=False))
                    lineas.clear()
                if bloque.titulo:
                    widgets.append(Static(bloque.titulo, classes="etiqueta", markup=False))
                widgets.append(TablaInteractiva(bloque))
            else:
                lineas.append(bloque)
        if lineas:
            widgets.append(Static("\n".join(lineas), markup=False))
        if self.registro.archivos:
            widgets.append(Collapsible(ArchivosBackend(self.registro.archivos), title="Archivos del backend"))
        await self.query_one("Contents").mount(*widgets)

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
