"""Interfaz interactiva de PyGebra para terminales de celdas Unicode."""

from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.events import Resize
from textual.theme import Theme
from textual.widgets import Collapsible, DataTable, Input, Static, TextArea

from .adaptador import Tabla, ejecutar, procedimiento
from .dialogos import Campo, DIALOGOS

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
        ancho = max(len(self.tabla.columnas), *(len(f) for f in self.tabla.filas))
        columnas = (*self.tabla.columnas, *("" for _ in range(ancho - len(self.tabla.columnas))))
        self.add_columns(*columnas)
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


class PyGebra(App):
    TITLE = "PyGebra"
    CSS_PATH = "interfaz.tcss"
    BINDINGS = [
        Binding("escape", "cerrar_menu", show=False),
        Binding("ctrl+q", "quit", "Salir"),
        Binding("f2", "enviar_texto", show=False),
        Binding("f3", "paso_anterior", show=False),
        Binding("f4", "repetir", show=False),
        Binding("space", "alternar_casilla", show=False, priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.navegacion = Navegacion()
        self.debugging = False
        self.decimal = "."
        self.comando = None
        self.datos = {}
        self.paso = 0
        self.seleccion = set()
        self.confirmacion = None
        self.ultimo_ejercicio = None
        self.ultimo_resultado = None
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
                yield Static(id="respuestas", markup=False)
                yield Static(id="ayuda", markup=False)
                yield Static(id="menu", markup=False)
                yield EntradaComando(placeholder="Escribe /", id="entrada")
                yield TextArea(id="editor", show_line_numbers=False)
                yield Static(id="aviso", markup=False)
        yield Static(id="teclas", markup=False)

    @property
    def entrada(self):
        return self.query_one("#entrada", EntradaComando)

    def on_mount(self):
        self.adaptar(self.size)
        self.entrada.focus()
        self.actualizar_menu()

    def on_resize(self, event: Resize):
        if self.is_mounted:
            self.adaptar(event.size)

    def adaptar(self, size):
        ancho, alto = size
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
        if self.comando is not None:
            self.actualizar_opciones()
            return
        nav = self.navegacion
        opciones = nav.opciones(self.entrada.value) if self.entrada.value.startswith("/") else ()
        menu = self.query_one("#menu", Static)
        menu.display = self.entrada.value.startswith("/")
        texto = Text()
        inicio = max(0, nav.indice - 5)
        for indice, opcion in enumerate(opciones[inicio:inicio + 6], inicio):
            if indice > inicio:
                texto.append("\n")
            seleccionada = indice == nav.indice
            texto.append(("› " if seleccionada else "  ") + "/" + opcion.id,
                         "bold reverse" if seleccionada else "")
        menu.update(texto if opciones else "Sin coincidencias")
        self.query_one("#migas", Static).update(" › ".join(c.titulo for c in nav.ruta))
        teclas = ("↑↓ Elegir · ← Atrás · → Volver · Enter Abrir" if menu.display
                  else "/ Menú · Tab Cambiar foco · F4 Repetir · Ctrl+Q Salir")
        self.query_one("#teclas", Static).update(teclas)

    @on(Input.Changed, "#entrada")
    def cambio_comando(self, evento):
        if self.comando is None and evento.value != "/":
            self.navegacion.indice = 0
        self.actualizar_menu()

    def action_mover_menu(self, salto):
        if self.comando is not None:
            self.navegacion.mover(self.campo_actual().opciones, salto)
            self.actualizar_opciones()
        elif self.entrada.value.startswith("/"):
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
        self.comando = None
        self.confirmacion = None
        self.navegacion.reiniciar()
        self.query_one("#editor").display = False
        self.query_one("#respuestas", Static).update("")
        self.query_one("#ayuda", Static).update("")
        self.entrada.display = True
        self.entrada.placeholder = "Escribe /"
        self.entrada.focus()
        self.estado("Escribe / para elegir una herramienta.")
        self.avisar("")
        self.entrada.clear()
        self.actualizar_menu()

    @on(Input.Submitted, "#entrada")
    def enviar_comando(self, evento):
        if self.comando is not None:
            self.enviar_respuesta(evento.value)
            return
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
                if self.ultimo_resultado is None:
                    self.query_one("#resultados").focus()
                else:
                    self.ultimo_resultado.query_one("CollapsibleTitle").focus()
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

    def abrir_herramienta(self, comando, datos=None):
        if comando.id not in DIALOGOS:
            self.avisar("Esta herramienta aún se está integrando.")
            return
        self.comando = comando
        self.datos = dict(datos or {})
        self.paso = 0
        self.mostrar_paso()

    def campos(self):
        if self.confirmacion:
            return (Campo("confirmacion", self.confirmacion.mensaje, (
                ("continuar", "Continuar"), ("cancelar", "Volver a los datos"),
            ), "cancelar", self.confirmacion.tiempo),)
        return DIALOGOS[self.comando.id](self.datos)

    def campo_actual(self):
        return self.campos()[self.paso]

    def mostrar_paso(self):
        campos = self.campos()
        campo = campos[self.paso]
        valor = self.datos.get(campo.id, campo.inicial)
        claves = [clave for clave, _ in campo.opciones]
        self.seleccion = set(valor) if campo.multiple else set()
        self.navegacion.indice = claves.index(valor) if valor in claves else 0
        self.query_one("#migas", Static).update(f"Resolver › {self.comando.titulo}")
        respuestas = []
        for previo in campos[:self.paso][-3:]:
            escrito = self.datos.get(previo.id, "")
            etiquetas = dict(previo.opciones)
            texto = (", ".join(etiquetas.get(v, v) for v in escrito) if previo.multiple
                     else etiquetas.get(escrito, escrito))
            resumen = " ".join(texto.split())
            respuestas.append(f"› {previo.titulo} · {resumen[:90]}")
        self.query_one("#respuestas", Static).update("\n".join(respuestas))
        self.estado(f"{campo.titulo}  ·  {self.paso + 1}/{len(campos)}")
        self.query_one("#ayuda", Static).update(campo.ayuda)
        self.entrada.display = not campo.multilinea
        self.entrada.placeholder = "Enter para confirmar" if campo.opciones else "Escribe tu respuesta"
        self.entrada.value = "" if campo.opciones else valor
        self.entrada.cursor_position = len(self.entrada.value)
        editor = self.query_one("#editor", TextArea)
        editor.display = campo.multilinea
        if campo.multilinea:
            editor.load_text(valor)
            editor.focus()
        else:
            self.entrada.focus()
        self.actualizar_opciones()

    def actualizar_opciones(self):
        campo = self.campo_actual()
        menu = self.query_one("#menu", Static)
        menu.display = bool(campo.opciones)
        seleccionada = self.navegacion.indice
        inicio = max(0, seleccionada - 4)
        texto = Text()
        for indice, (clave, etiqueta) in enumerate(campo.opciones[inicio:inicio + 5], inicio):
            if indice > inicio:
                texto.append("\n")
            prefijo = ("[x] " if clave in self.seleccion else "[ ] ") if campo.multiple else ""
            texto.append(("› " if indice == seleccionada else "  ") + prefijo + etiqueta,
                         "bold reverse" if indice == seleccionada else "")
        menu.update(texto)
        teclas = ("F2 Confirmar · Enter Nueva línea" if campo.multilinea else
                  "↑↓ Elegir · Espacio Marcar · Enter Confirmar" if campo.multiple else
                  "↑↓ Elegir · Enter Confirmar" if campo.opciones else "Enter Confirmar")
        self.query_one("#teclas", Static).update(teclas + " · F3 Atrás · Esc Cancelar · Tab Cambiar foco")

    def check_action(self, action, parameters):
        if action == "alternar_casilla":
            return (self.comando is not None and self.entrada.has_focus
                    and self.campo_actual().multiple)
        return super().check_action(action, parameters)

    def action_alternar_casilla(self):
        campo = self.campo_actual()
        clave = campo.opciones[self.navegacion.indice][0]
        self.seleccion.symmetric_difference_update({clave})
        self.actualizar_opciones()

    def action_enviar_texto(self):
        editor = self.query_one("#editor", TextArea)
        if self.comando and editor.has_focus:
            self.enviar_respuesta(editor.text)

    def action_paso_anterior(self):
        if self.comando is None:
            return
        self.avisar("")
        if self.confirmacion:
            self.confirmacion = None
            self.paso = len(self.campos()) - 1
        elif self.paso > 0:
            self.paso -= 1
        self.mostrar_paso()

    def action_repetir(self):
        if self.comando is None and self.ultimo_ejercicio:
            self.abrir_herramienta(*self.ultimo_ejercicio)

    def enviar_respuesta(self, texto):
        campo = self.campo_actual()
        if campo.multiple:
            valor = tuple(clave for clave, _ in campo.opciones if clave in self.seleccion)
        elif campo.opciones:
            valor = campo.opciones[self.navegacion.indice][0]
        else:
            valor = texto.strip()
        self.avisar("")
        if self.confirmacion:
            if valor == "cancelar":
                self.action_paso_anterior()
                return
            firma = self.confirmacion.firma
            self.confirmacion = None
            self.paso = len(self.campos()) - 1
            self.resolver(firma)
            return
        self.datos[campo.id] = valor
        if self.paso + 1 < len(self.campos()):
            self.paso += 1
            self.mostrar_paso()
        else:
            self.resolver()

    def resolver(self, firma=None):
        datos = dict(self.datos)
        if firma is not None:
            datos["confirmacion"] = firma
        try:
            respuesta, archivos = ejecutar(self.comando.id, datos, self.debugging)
        except ValueError as error:
            self.avisar(str(error))
            return
        contexto = respuesta.context_data
        form = contexto["form"]
        if form.errors:
            nombres = [campo.id for campo in self.campos()]
            pasos = [nombres.index(n) for n in form.errors if n in nombres]
            self.paso = min(pasos, default=self.paso)
            self.mostrar_paso()
            self.avisar(" ".join(str(m) for errores in form.errors.values() for m in errores))
            return
        if confirmacion := contexto.get("confirmacion"):
            self.confirmacion = confirmacion
            self.paso = 0
            self.mostrar_paso()
            return
        bloques = procedimiento(respuesta)
        if not bloques:
            self.avisar("Revisa los datos del ejercicio y vuelve a confirmar.")
            return
        self.guardar_ejercicio(bloques, archivos)
        self.action_cerrar_menu()
        self.estado("Ejercicio resuelto · / para otro · F4 para repetir")

    def guardar_ejercicio(self, bloques, archivos):
        self.ultimo_ejercicio = (self.comando, dict(self.datos))
        widgets = []
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
        if archivos:
            enlaces = Text()
            for archivo in archivos:
                if enlaces:
                    enlaces.append("\n")
                enlaces.append(archivo, f"underline link {Path(archivo).as_uri()}")
            widgets.append(Collapsible(Static(enlaces, markup=False), title="Archivos del backend"))
        if self.ultimo_resultado is not None:
            self.ultimo_resultado.collapsed = True
        titulo = self.comando.titulo
        if isinstance(bloques[0], str) and bloques[0] != titulo:
            titulo += " · " + bloques[0][:100]
        ejercicio = Collapsible(*widgets, title=titulo, collapsed=False, classes="ejercicio")
        self.ultimo_resultado = ejercicio
        self.query_one("#vacio").display = False
        self.query_one("#resultados").mount(ejercicio)
        self.call_after_refresh(ejercicio.scroll_visible, top=True)

    def avisar(self, mensaje):
        aviso = self.query_one("#aviso", Static)
        aviso.display = bool(mensaje)
        aviso.update(mensaje)

    def estado(self, mensaje):
        self.query_one("#pregunta", Static).update(mensaje)
