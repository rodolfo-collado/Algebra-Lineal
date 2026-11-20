"""Interfaz interactiva de PyGebra para terminales de celdas Unicode."""

import os
from pathlib import Path
import re
import sqlite3
import subprocess

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.events import Resize
from textual.theme import Theme
from textual.widgets import Collapsible, DataTable, Input, OptionList, Static, TextArea

from .adaptador import Tabla, ejecutar, procedimiento
from .algebra import DIALOGOS_ALGEBRA, campo_de_error, preparar_algebra, validar_cantidad_matricial
from .conjuntos import (
    DIALOGOS_CONJUNTOS, GraficaConjuntos, cardinalidad, preparar_conjuntos, relaciones,
    representacion, resolver_conjuntos,
)
from .dialogos import Campo, DIALOGOS, ErrorEntrada

from .graficas import Grafica
from .historial import Ejercicio, Historial
from .navegacion import HERRAMIENTAS, Navegacion
from .raices import DIALOGOS_RAICES, _CAMPOS_VISTA, curva, mensaje_previsualizacion, preparar_raices


_DIALOGOS = {
    **DIALOGOS, **DIALOGOS_ALGEBRA, **DIALOGOS_RAICES,
    "relaciones-conjuntos": relaciones,
    "cardinalidad-conjuntos": cardinalidad,
}
_VISUALES = set(DIALOGOS_RAICES) | DIALOGOS_CONJUNTOS
_ERRORES_DISCO = (OSError, ValueError, KeyError, sqlite3.Error)
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

    def __init__(self, historial=None):
        super().__init__()
        self.historial = historial if historial is not None else Historial()
        self.navegacion = Navegacion()
        self.debugging = False
        self.decimal = "."
        self.comando = None
        self._campos = ()
        self.datos = {}
        self.paso = 0
        self.seleccion = set()
        self.confirmacion = None
        self.ultimo_ejercicio = None
        self.ultimo_resultado = None
        self._reloj_grafica = None
        self._revision_grafica = 0
        self._calculo = 0
        self._resolviendo = False
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
                yield Grafica(id="grafica-viva")
                yield GraficaConjuntos(id="diagrama-vivo")
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

    async def on_mount(self):
        try:
            historico, ajustes = self.historial.abrir()
        except _ERRORES_DISCO:
            self.notify("El historial local no se pudo leer.", severity="warning")
        else:
            self.theme = "pygebra-claro" if ajustes.get("tema") == "pygebra-claro" else "pygebra"
            self.decimal = "," if ajustes.get("decimal") == "," else "."
            self.screen.set_class(ajustes.get("densidad") == "holgada", "holgada")
            self.debugging = ajustes.get("debugging") == "si"
            if historico:
                fichas = [Ficha(e) for e in historico]
                await self.query_one("#resultados").mount(*fichas)
                self.ultimo_resultado = fichas[-1]
                self.ultimo_ejercicio = historico[-1]
                self.query_one("#vacio").display = False
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
        self.screen.set_class(alto < 27, "corta")
        marca = Text(justify="center")
        colores = (_COLORES if self.theme == "pygebra" else
                   ("#69458a", "#615182", "#395d8c", "#00606e", "#166756", "#22664a", "#205e38"))
        if alto < 24 or ancho < 51:
            for letra, color in zip("PYGEBRA", colores):
                marca.append(letra, f"bold {color}")
        else:
            for indice, linea in enumerate(_BLOQUES):
                if indice:
                    marca.append("\n")
                for columna, caracter in enumerate(linea):
                    marca.append(caracter, colores[min(6, columna * 7 // len(linea))])
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
        if self.comando is None:
            if evento.value != "/":
                self.navegacion.indice = 0
            self.actualizar_menu()
        elif self.comando.id in DIALOGOS_RAICES and self.campo_actual().id in _CAMPOS_VISTA:
            self.programar_grafica()
        elif self.comando.id in DIALOGOS_CONJUNTOS and self.campo_actual().id in {"expresion", "punto"}:
            self.programar_grafica()

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
        self._calculo += 1
        self._resolviendo = False
        self._revision_grafica += 1
        self.query_one("#grafica-viva", Grafica).mostrar(None)
        self.query_one("#diagrama-vivo", GraficaConjuntos).mostrar(None)
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
                self.guardar_preferencia("debugging", "si" if self.debugging else "")
                self.estado(f"Depuración {'activada' if self.debugging else 'desactivada'}.")
            case "tema":
                self.theme = "pygebra-claro" if self.theme == "pygebra" else "pygebra"
                self.guardar_preferencia("tema", self.theme)
                self.adaptar(self.size)
                for grafica in self.query("Grafica, GraficaConjuntos"):
                    grafica.pintar()
            case "convencion-decimal":
                self.decimal = "," if self.decimal == "." else "."
                self.guardar_preferencia("decimal", self.decimal)
                self.estado(f"Separador decimal seleccionado: {self.decimal}")
                for grafica in self.query("Grafica, GraficaConjuntos"):
                    grafica.pintar()
            case "densidad":
                espacio = self.screen.toggle_class("holgada").has_class("holgada")
                self.guardar_preferencia("densidad", "holgada" if espacio else "compacta")
                self.estado("Espaciado holgado." if espacio else "Espaciado compacto.")
            case _:
                self.abrir_herramienta(comando)

    def guardar_preferencia(self, clave, valor):
        try:
            self.historial.preferencia(clave, valor)
        except _ERRORES_DISCO:
            self.notify("El ajuste solo se aplicó a esta sesión.", severity="warning")

    def abrir_herramienta(self, comando, datos=None):
        self.comando = comando
        self.datos = dict(datos or {})
        self.recalcular_campos()
        self.paso = 0
        self.mostrar_paso()

    def campos(self):
        if self.confirmacion:
            return (Campo("confirmacion", self.confirmacion["mensaje"], (
                ("continuar", "Continuar"), ("cancelar", "Volver a los datos"),
            ), "cancelar", self.confirmacion.get("tiempo", "")),)
        return self._campos

    def recalcular_campos(self):
        self._campos = _DIALOGOS[self.comando.id](self.datos)

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
        if self.comando.id in _VISUALES:
            self.programar_grafica()

    def programar_grafica(self):
        self._revision_grafica += 1
        revision = self._revision_grafica
        if self._reloj_grafica is not None:
            self._reloj_grafica.stop()
        herramienta = self.comando.id
        datos = self.datos_activos()
        clave = self.campo_actual().id
        if clave in _CAMPOS_VISTA | {"punto", "expresion"} and not self.campo_actual().opciones:
            dato = self.query_one("#editor", TextArea).text if self.campo_actual().multilinea else self.entrada.value
            datos[clave] = dato
        if herramienta in DIALOGOS_CONJUNTOS and (not datos.get("expresion") or datos.get("@modo") == "azar"):
            return
        decimal = self.decimal
        self._reloj_grafica = self.set_timer(.15, lambda: self.calcular_previsualizacion(
            revision, herramienta, datos, decimal,
        ))

    @work(thread=True, exclusive=True)
    def calcular_previsualizacion(self, revision, herramienta, datos, decimal):
        es_raiz = herramienta in DIALOGOS_RAICES
        aviso = ""
        try:
            if es_raiz:
                vista = curva(herramienta, preparar_raices(datos, decimal))
            else:
                entrada = preparar_conjuntos(herramienta, datos, decimal)
                respuesta, _ = resolver_conjuntos(herramienta, entrada, False)
                form = respuesta.context_data["form"]
                aviso = " ".join(str(m) for errores in form.errors.values() for m in errores)
                vista = representacion(respuesta.context_data) if not aviso else None
        except (ValueError, ArithmeticError) as error:
            vista = None
            aviso = mensaje_previsualizacion(error, datos.get("funcion", "")) if es_raiz else str(error)
        self.call_from_thread(self.aplicar_previsualizacion, revision, vista, aviso)

    def aplicar_previsualizacion(self, revision, vista, aviso):
        if revision != self._revision_grafica or self.comando is None:
            return
        if self.comando.id in DIALOGOS_RAICES:
            grafica = self.query_one("#grafica-viva", Grafica)
            anterior = grafica.curva
        else:
            grafica = self.query_one("#diagrama-vivo", GraficaConjuntos)
            anterior = grafica.vista
        if vista is not None:
            grafica.mostrar(vista)
            if anterior is None:
                self.query_one("#resultados", VerticalScroll).scroll_home(animate=False)
        if self.campo_actual().id in _CAMPOS_VISTA | {"punto", "expresion"}:
            self.avisar(aviso + (" Se conserva la última gráfica válida." if aviso and anterior else ""))

    @on(TextArea.Changed, "#editor")
    def cambio_multilinea(self):
        if (self.comando and self.comando.id in DIALOGOS_CONJUNTOS
                and self.campo_actual().id == "expresion"):
            self.programar_grafica()

    def mostrar_teclas(self, texto):
        self.query_one("#teclas", Static).update(texto)

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
        if self.comando is None or self._resolviendo:
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
            ultimo = self.ultimo_ejercicio
            if ultimo.comando in HERRAMIENTAS:
                self.abrir_herramienta(HERRAMIENTAS[ultimo.comando], ultimo.datos)

    def enviar_respuesta(self, texto):
        if self._resolviendo:
            return
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
            firma = self.confirmacion["firma"]
            self.confirmacion = None
            self.paso = len(self.campos()) - 1
            self.resolver(firma)
            return
        if self.comando.id == "operaciones-matrices" and campo.id == "cantidad":
            try:
                valor = validar_cantidad_matricial(valor)
            except ErrorEntrada as error:
                self.avisar(str(error))
                return
        if campo.id in {"@plantilla", "@ejemplo"} and self.datos.get(campo.id) != valor:
            self.datos.pop("expresion", None)
        self.datos[campo.id] = valor
        self.recalcular_campos()
        if self.paso + 1 < len(self.campos()):
            self.paso += 1
            self.mostrar_paso()
        else:
            self.resolver()

    def revisar(self, mensaje, nombres):
        ids = [campo.id for campo in self.campos()]
        pasos = [ids.index(n) for n in nombres if n in ids]
        self.paso = min(pasos, default=self.paso)
        self.mostrar_paso()
        self.avisar(mensaje)

    def datos_activos(self):
        return {c.id: self.datos[c.id] for c in self.campos() if c.id in self.datos}

    def resolver(self, firma=None):
        self._calculo += 1
        self._resolviendo = True
        self._revision_grafica += 1
        self.estado("Calculando…")
        self.procesar(self._calculo, self.comando.id, self.datos_activos(), self.decimal, self.debugging, firma)

    @work(thread=True, group="calculo")
    def procesar(self, version, herramienta, datos, decimal, depurar, firma):
        try:
            entrada = datos
            if herramienta in DIALOGOS_ALGEBRA:
                entrada = preparar_algebra(herramienta, datos, decimal)
            elif herramienta in DIALOGOS_RAICES:
                entrada = preparar_raices(datos, decimal)
            if firma is not None:
                entrada["confirmacion"] = firma
            if herramienta in DIALOGOS_CONJUNTOS:
                entrada = preparar_conjuntos(herramienta, datos, decimal)
                respuesta, archivos = resolver_conjuntos(herramienta, entrada, depurar,
                                                        azar=datos.get("@modo") == "azar")
            else:
                respuesta, archivos = ejecutar(herramienta, entrada, depurar)
        except ErrorEntrada as error:
            self.call_from_thread(self.recibir_calculo, version, str(error), (error.campo,))
            return
        except (ValueError, ArithmeticError) as error:
            self.call_from_thread(self.recibir_calculo, version, str(error))
            return

        contexto = respuesta.context_data
        form = contexto["form"]
        if form.errors:
            mensaje = " ".join(str(m) for errores in form.errors.values() for m in errores)
            nombres = tuple("@definiciones" if n.startswith(("nombre_", "contenido_")) and herramienta == "relaciones-conjuntos"
                            else campo_de_error(n) for n in form.errors)
            self.call_from_thread(self.recibir_calculo, version, mensaje, nombres)
            return
        if confirmacion := contexto.get("confirmacion"):
            self.call_from_thread(self.recibir_calculo, version, confirmacion=confirmacion)
            return

        bloques = procedimiento(respuesta)
        grafica = None
        if herramienta in DIALOGOS_RAICES:
            try:
                grafica = curva(herramienta, entrada, contexto["resultado"])
            except (ValueError, ArithmeticError):
                pass
        elif herramienta in DIALOGOS_CONJUNTOS:
            grafica = representacion(contexto)
            if herramienta == "relaciones-conjuntos" and (contexto.get("diagrama") or {}).get("panorama"):
                bloques += procedimiento(respuesta, "panorama-titulo")
        if decimal == ",":
            bloques = tuple(self._con_coma(b) for b in bloques)
        self.call_from_thread(self.recibir_calculo, version, bloques=bloques, archivos=archivos, grafica=grafica)

    def recibir_calculo(self, version, mensaje="", nombres=(), *, confirmacion=None, bloques=(), archivos=(), grafica=None):
        if version != self._calculo or self.comando is None:
            return
        self._resolviendo = False
        if mensaje:
            self.revisar(mensaje, nombres)
        elif confirmacion:
            self.confirmacion = confirmacion
            self.paso = 0
            self.mostrar_paso()
        elif bloques:
            self.guardar_ejercicio(bloques, archivos, grafica)
            self.action_cerrar_menu()
            self.estado("Ejercicio resuelto · / para otro · F4 para repetir")
        else:
            self.revisar("Revisa los datos del ejercicio y vuelve a confirmar.", ())

    @staticmethod
    def _con_coma(bloque):
        sustituir = lambda texto: re.sub(r"(?<=[0-9])\.(?=[0-9])", ",", texto)
        if isinstance(bloque, Tabla):
            return Tabla(bloque.titulo, bloque.columnas,
                         tuple(tuple(map(sustituir, f)) for f in bloque.filas))
        return sustituir(bloque)

    def guardar_ejercicio(self, bloques, archivos, grafica):
        datos = self.datos_activos()
        entrada = next((datos[k] for k in ("funcion", "expresion", "sistema", "numero", "@A", "@matriz")
                        if datos.get(k)), "")
        resumen = " ".join(entrada.split())
        if not resumen:
            resumen = next((b for b in bloques if isinstance(b, str) and b != self.comando.titulo), "")
        titulo = " · ".join(t for t in (self.comando.titulo, resumen[:75]) if t)
        registro = Ejercicio(self.comando.id, titulo, datos, bloques, archivos, grafica)
        self.ultimo_ejercicio = registro
        try:
            self.historial.agregar(registro)
        except _ERRORES_DISCO:
            self.notify("El ejercicio solo quedó guardado en esta sesión.", severity="warning")
        if self.ultimo_resultado is not None:
            self.ultimo_resultado.collapsed = True
        ejercicio = Ficha(registro, collapsed=False)
        self.ultimo_resultado = ejercicio
        self.query_one("#vacio").display = False
        self.query_one("#resultados").mount(ejercicio)
        self.call_after_refresh(ejercicio.cargar)
        self.call_after_refresh(ejercicio.scroll_visible, top=True)

    def avisar(self, mensaje):
        aviso = self.query_one("#aviso", Static)
        aviso.display = bool(mensaje)
        aviso.update(mensaje)

    def estado(self, mensaje):
        self.query_one("#pregunta", Static).update(mensaje)
