"""Interfaz interactiva de PyGebra para terminales de celdas Unicode."""

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.events import Resize
from textual.theme import Theme
from textual.widgets import Input, Static

from .navegacion import Navegacion


_BLOQUES = (
    "████  █   █  ████  █████  ████   ████    ███ ",
    "█   █  █ █   █      █      █   █  █   █  █   █",
    "████    █    █ ███  ████   ████   ████   █████",
    "█       █    █   █  █      █   █  █  █   █   █",
    "█       █    █████  █████  ████   █   █  █   █",
)
_COLORES = ("#c9a6f4", "#bcaef1", "#a9c5ef", "#8edfec", "#92ded9", "#9ee2c3", "#ace6a5")


class EntradaComando(Input):
    BINDINGS = [
        Binding("up", "app.mover_menu(-1)", show=False),
        Binding("down", "app.mover_menu(1)", show=False),
    ]

    def action_cursor_left(self, select=False):
        if self.value == "/" and not select:
            self.app.volver_menu()
        else:
            super().action_cursor_left(select)

    def action_cursor_right(self, select=False):
        if self.value == "/" and not select:
            self.app.avanzar_menu()
        else:
            super().action_cursor_right(select)


class PyGebra(App):
    TITLE = "PyGebra"
    CSS_PATH = "interfaz.tcss"
    BINDINGS = [
        Binding("escape", "cerrar_menu", show=False),
        Binding("ctrl+q", "quit", "Salir"),
    ]

    def __init__(self):
        super().__init__()
        self.navegacion = Navegacion()
        self.debugging = False
        self.decimal = "."
        self.register_theme(Theme(
            name="pygebra", primary="#8edfec", secondary="#c9a6f4", accent="#ace6a5",
            foreground="#d8d6ed", background="#12121c", surface="#181824",
            panel="#212132", error="#f492b1",
        ))
        self.register_theme(Theme(
            name="pygebra-claro", primary="#00606e", secondary="#624184", accent="#205e38",
            foreground="#292439", background="#f7f4fc", surface="#ede7f6",
            panel="#ded5ed", error="#961d4a", dark=False,
        ))
        self.theme = "pygebra"

    def compose(self) -> ComposeResult:
        yield Static(id="marca", markup=False)
        with Container(id="cuerpo"):
            with VerticalScroll(id="resultados", can_focus=True):
                yield Static("Historial", classes="titulo")
                yield Static("Los ejercicios resueltos aparecerán aquí.", id="vacio", markup=False)
            with Container(id="chat"):
                yield Static(id="migas", markup=False)
                yield Static("Escribe / para elegir una herramienta.", id="pregunta", markup=False)
                yield Static(id="menu", markup=False)
                yield EntradaComando(placeholder="Escribe /", id="entrada")
                yield Static(id="aviso", markup=False)
        yield Static(id="teclas", markup=False)

    @property
    def entrada(self):
        return self.query_one("#entrada", EntradaComando)

    def on_mount(self):
        self.adaptar()
        self.entrada.focus()
        self.actualizar_menu()

    def on_resize(self, event: Resize):
        if self.is_mounted:
            self.adaptar()

    def adaptar(self):
        ancho, alto = self.size
        self.screen.set_class(ancho >= 96 and ancho >= 2.65 * alto, "ancha")
        self.screen.set_class(alto < 24 or ancho < 51, "marca-breve")
        marca = Text(justify="center")
        if alto < 24 or ancho < 51:
            for letra, color in zip("PYGEBRA", _COLORES):
                marca.append(letra, f"bold {color}")
        else:
            for indice, linea in enumerate(_BLOQUES):
                if indice:
                    marca.append("\n")
                for columna, caracter in enumerate(linea):
                    marca.append(caracter, _COLORES[min(6, columna * 7 // len(linea))])
        self.query_one("#marca", Static).update(marca)

    def actualizar_menu(self):
        nav = self.navegacion
        opciones = nav.opciones(self.entrada.value) if self.entrada.value.startswith("/") else ()
        menu = self.query_one("#menu", Static)
        menu.display = self.entrada.value.startswith("/")
        texto = Text()
        for indice, opcion in enumerate(opciones):
            if indice:
                texto.append("\n")
            seleccionada = indice == nav.indice
            texto.append(("› " if seleccionada else "  ") + "/" + opcion.id,
                         "bold reverse" if seleccionada else "")
        menu.update(texto if opciones else "Sin coincidencias")
        self.query_one("#migas", Static).update(" › ".join(c.titulo for c in nav.ruta))
        teclas = ("↑↓ Elegir · ← Atrás · → Volver · Enter Abrir" if menu.display
                  else "/ Menú · Tab Cambiar foco · Ctrl+Q Salir")
        self.query_one("#teclas", Static).update(teclas)

    @on(Input.Changed, "#entrada")
    def cambio_comando(self, evento):
        if evento.value != "/":
            self.navegacion.indice = 0
        self.actualizar_menu()

    def action_mover_menu(self, salto):
        if self.entrada.value.startswith("/"):
            self.navegacion.mover(self.navegacion.opciones(self.entrada.value), salto)
            self.actualizar_menu()

    def volver_menu(self):
        self.navegacion.salir()
        self.actualizar_menu()

    def avanzar_menu(self):
        nav = self.navegacion
        opciones = nav.opciones("/")
        previo = nav.ultimo.get(nav.ruta[-1].id)
        comando = next((c for c in opciones if c.id == previo and c.hijos), None)
        if comando is not None:
            nav.entrar(comando)
            self.actualizar_menu()

    def action_cerrar_menu(self):
        self.navegacion.reiniciar()
        self.entrada.clear()
        self.actualizar_menu()

    @on(Input.Submitted, "#entrada")
    def enviar_comando(self, evento):
        if not evento.value.startswith("/"):
            self.avisar("Escribe / para abrir el menú.")
            return
        nav = self.navegacion
        opciones = nav.opciones(evento.value)
        if not opciones:
            return
        comando = opciones[nav.indice]
        self.avisar("")
        if comando.hijos:
            nav.entrar(comando)
            self.entrada.value = "/"
            self.entrada.cursor_position = 1
            self.actualizar_menu()
        else:
            self.action_cerrar_menu()
            self.ejecutar_comando(comando)

    def ejecutar_comando(self, comando):
        match comando.id:
            case "historial":
                self.query_one("#resultados").focus()
            case "debugging":
                self.debugging = not self.debugging
                self.estado(f"Depuración {'activada' if self.debugging else 'desactivada'}.")
            case "tema":
                self.theme = "pygebra-claro" if self.theme == "pygebra" else "pygebra"
            case "convencion-decimal":
                self.decimal = "," if self.decimal == "." else "."
                self.estado(f"Separador decimal seleccionado: {self.decimal}")
            case "densidad":
                espacio = self.screen.toggle_class("holgada").has_class("holgada")
                self.estado("Espaciado holgado." if espacio else "Espaciado compacto.")
            case _:
                self.abrir_herramienta(comando)

    def abrir_herramienta(self, comando):
        self.estado(comando.titulo)

    def avisar(self, mensaje):
        aviso = self.query_one("#aviso", Static)
        aviso.display = bool(mensaje)
        aviso.update(mensaje)

    def estado(self, mensaje):
        self.query_one("#pregunta", Static).update(mensaje)
