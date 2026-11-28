"""Interfaz interactiva de PyGebra para terminales de celdas Unicode."""

import re
import sqlite3

from rich.cells import cell_len
from rich.style import Style
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.color import Color
from textual.containers import Container, VerticalScroll
from textual.events import DescendantFocus, Resize
from textual.theme import Theme
from textual.widgets import Collapsible, Input, Static, TextArea
from textual.widgets._collapsible import CollapsibleTitle

from backend.operandos import OPERANDOS_MAXIMOS
from frontend.web.calculadora.opciones_matrices import datos_operacion_vectorial
from frontend.web.calculadora.teclados import (
    PERFIL_EXPRESION, PERFIL_FUNCION_REAL, PERFIL_LINEAL, PERFIL_LITERAL_CONJUNTOS,
    PERFIL_NUMERICO, PERFIL_REGIONES_CONJUNTOS, PERFIL_RELACION_CONJUNTOS, PERFIL_SISTEMA,
)

from .adaptador import Linea, Tabla, ejecutar, procedimiento, trazar_backend
from .algebra import DIALOGOS_ALGEBRA, campo_de_error, combinacion_vectores_maxima, preparar_algebra
from .conjuntos import (
    DIALOGOS_CONJUNTOS, GraficaConjuntos, cardinalidad, preparar_conjuntos, relaciones,
    representacion, resolver_conjuntos,
)
from .componentes import ArchivosBackend, EntradaComando, Ficha, MenuOpciones, Paleta, TablaInteractiva
from .dialogos import Campo, DIALOGOS, ErrorEntrada

from .graficas import Grafica
from .marca import logotipo
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


class PyGebra(App):
    TITLE = "PyGebra"
    CSS_PATH = "interfaz.tcss"
    BINDINGS = [
        Binding("escape", "cerrar_menu", show=False),
        Binding("ctrl+q", "quit", "Salir"),
        Binding("f2", "enviar_texto", show=False),
        Binding("f3", "paso_anterior", show=False),
        Binding("f4", "repetir", show=False),
        Binding("f6", "simbolos", show=False, priority=True),
        Binding("f7", "cambiar_panel", show=False, priority=True),
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
        self._borrador = ""
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
                yield Static("Historial", id="titulo-historial", classes="titulo")
                yield Static("Los ejercicios resueltos aparecerán aquí.", id="vacio", markup=False)
            with Container(id="chat"):
                yield Static(id="migas", markup=False)
                yield Static(id="espacio-chat")
                with VerticalScroll(id="conversacion", can_focus=False):
                    yield Static(id="respuestas", markup=False, classes="vacio")
                    yield Static(id="paso", markup=False, classes="vacio")
                    yield Static("Escribe / para elegir una herramienta.", id="pregunta", markup=False)
                    yield Static(id="ayuda", markup=False, classes="vacio")
                with Container(id="redaccion"):
                    yield MenuOpciones(id="menu", markup=False)
                    yield Static(id="detalle-menu", markup=False, classes="vacio")
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
            if self.historial.omitidos:
                n = self.historial.omitidos
                self.notify("1 ejercicio del historial no se pudo leer y se omitió." if n == 1 else
                            f"{n} ejercicios del historial no se pudieron leer y se omitieron.", severity="warning")
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
        pantalla = self.query_one("#cuerpo").screen
        pantalla.set_class(ancho >= 96 and ancho >= 2.65 * alto, "ancha")
        if pantalla.has_class("ancha"):
            pantalla.remove_class("lectura")
        pantalla.set_class(alto < 32, "corta")
        pantalla.set_class(alto < 23, "muy-corta")
        self.query_one("#marca", Static).update(logotipo(ancho, alto, claro=self.theme == "pygebra-claro"))
        self.call_after_refresh(self.actualizar_menu)

    def _lista_opciones(self, opciones, seleccion, *, comandos=False):
        """Mantiene la selección visible al recorrer listas más altas que el chat."""
        menu = self.query_one("#menu", Static)
        ancho = max(1, menu.content_size.width or (
            self.size.width // 3 - 10 if self.screen.has_class("ancha") else self.size.width - 9
        ))
        maximo = 6 if self.screen.has_class("ancha") else 4 if self.size.height >= 32 else 3
        inicio = min(max(0, seleccion - maximo + 1), max(0, len(opciones) - maximo))
        tema = self.current_theme
        fondo_activo = Color.parse(tema.background).blend(Color.parse(tema.secondary), 0.20).hex
        activa = Style(bgcolor=fondo_activo)
        ancho_comando = max((1 + cell_len(opcion.id) for opcion in opciones), default=0) if comandos else 0
        ancho_descripcion = ancho - ancho_comando - 6  # Marcador y separación entre columnas.
        en_columnas = comandos and ancho_descripcion >= 15
        texto = Text()
        for indice, opcion in enumerate(opciones[inicio:inicio + maximo], inicio):
            if indice > inicio:
                texto.append("\n")
            elegida = indice == seleccion
            if comandos:
                etiqueta = "/" + opcion.id
            else:
                clave, etiqueta = opcion
                if self.campo_actual().multiple:
                    etiqueta = ("✓  " if clave in self.seleccion else "○  ") + etiqueta
            linea = Text.assemble(("▌  ", tema.secondary) if elegida else "   ")
            linea.append(etiqueta, tema.primary if comandos else None)
            if en_columnas:
                linea.pad_right(ancho_comando - cell_len(etiqueta) + 3)
                descripcion = Text(opcion.descripcion_corta or opcion.titulo, style="dim")
                descripcion.truncate(ancho_descripcion, overflow="ellipsis")
                linea.append_text(descripcion)
            linea.truncate(ancho, overflow="ellipsis")
            if elegida:
                linea.pad_right(ancho - linea.cell_len)
                linea.stylize(activa)
            texto.append(linea)
        return texto, en_columnas

    def _ruta_chat(self, ruta):
        tema = self.current_theme
        linea = Text()
        for indice, parte in enumerate(ruta):
            if indice:
                linea.append("  ›  ", tema.primary)
            linea.append(parte, f"bold {tema.secondary}" if indice == len(ruta) - 1 else "")
        self.query_one("#migas", Static).update(linea)

    def actualizar_menu(self):
        if self.comando is not None:
            self.actualizar_opciones()
            return
        nav = self.navegacion
        opciones = nav.opciones(self.entrada.value) if self.entrada.value.startswith("/") else ()
        menu = self.query_one("#menu", Static)
        menu.display = self.entrada.value.startswith("/")
        self.query_one("#pregunta").display = not menu.display
        lista, en_columnas = self._lista_opciones(opciones, nav.indice, comandos=True)
        menu.update(lista or "Sin coincidencias")
        descripcion = opciones[nav.indice].titulo if not en_columnas and nav.indice < len(opciones) else ""
        self.detalle_chat("#detalle-menu", descripcion)
        ruta = ("Chat",) if len(nav.ruta) == 1 else ("Chat", *(c.titulo for c in nav.ruta[1:]))
        self._ruta_chat(ruta)
        if not self.entrada.has_focus:
            return
        if menu.display:
            teclas = ["Enter Abrir"] if opciones else []
            if len(opciones) > 1:
                teclas.append("↑↓ Elegir")
            if len(nav.ruta) > 1:
                teclas.append("← Atrás")
            if nav.ruta[-1].id in nav.ultimo:
                teclas.append("→ Volver")
            self.mostrar_teclas(" · ".join((*teclas, "Esc Cerrar")))
        else:
            repetir = " · F4 Repetir" if self.ultimo_ejercicio and self.ultimo_ejercicio.comando in HERRAMIENTAS else ""
            self.mostrar_teclas(f"/ Menú{repetir} · Ctrl+Q Salir")

    @on(Input.Changed, "#entrada")
    def cambio_comando(self, evento):
        if self.comando is None:
            if evento.value != "/":
                self.navegacion.indice = 0
            self.actualizar_menu()
        elif evento.value == self.entrada.value:
            self._cambio_borrador(evento.value, multilinea=False)

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
        self.screen.remove_class("lectura")
        self._calculo += 1
        self._resolviendo = False
        self._invalidar_previsualizacion()
        self.query_one("#grafica-viva", Grafica).mostrar(None)
        self.query_one("#diagrama-vivo", GraficaConjuntos).mostrar(None)
        self.comando = None
        self.confirmacion = None
        self.navegacion.reiniciar()
        self.query_one("#editor").display = False
        self.detalle_chat("#respuestas", "")
        self.detalle_chat("#paso", "")
        self.detalle_chat("#ayuda", "")
        self.detalle_chat("#detalle-menu", "")
        self.entrada.display = True
        self.entrada.placeholder = "Escribe /"
        self.entrada.focus()
        self.estado("Escribe / para elegir una herramienta.")
        self._aviso_formato("")
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
        self._borrador = "" if campo.opciones else valor
        self._aviso_formato("")
        claves = [clave for clave, _ in campo.opciones]
        self.seleccion = set(valor) if campo.multiple else set()
        self.navegacion.indice = claves.index(valor) if valor in claves else 0
        self._ruta_chat(("Resolver", self.comando.titulo))
        anteriores = campos[:self.paso][-3:]
        respuestas = Text()
        for previo in anteriores:
            escrito = self.datos.get(previo.id, "")
            etiquetas = dict(previo.opciones)
            texto = (", ".join(etiquetas.get(v, v) for v in escrito) if previo.multiple
                     else etiquetas.get(escrito, escrito))
            resumen = " ".join(texto.split())
            if not resumen:
                continue
            if respuestas:
                respuestas.append("\n\n" if self.screen.has_class("ancha") else "\n")
            respuestas.append("✓  ", self.current_theme.accent)
            respuestas.append(previo.titulo + "   ", "dim")
            respuestas.append(resumen[:90], f"bold {self.current_theme.primary}")
        self.detalle_chat("#respuestas", respuestas)
        self.detalle_chat("#paso", f"Paso {self.paso + 1} de {len(campos)}")
        self.query_one("#pregunta").display = True
        self.estado(campo.titulo)
        self.detalle_chat("#ayuda", campo.ayuda)
        self.call_after_refresh(self.query_one("#conversacion", VerticalScroll).scroll_end, animate=False)
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
        if self._validar_borrador() and self.comando.id in _VISUALES:
            self.programar_grafica()

    def _invalidar_previsualizacion(self):
        self._revision_grafica += 1
        if self._reloj_grafica is not None:
            self._reloj_grafica.stop()
            self._reloj_grafica = None

    def programar_grafica(self):
        self._invalidar_previsualizacion()
        revision = self._revision_grafica
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
    def cambio_multilinea(self, evento):
        self._cambio_borrador(evento.text_area.text, multilinea=True)

    def _cambio_borrador(self, texto, *, multilinea):
        if self.comando is None or self._resolviendo or texto == self._borrador:
            return
        campo = self.campo_actual()
        if campo.opciones or campo.multilinea != multilinea:
            return
        self._borrador = texto
        if not self._validar_borrador():
            return
        if (self.comando.id in DIALOGOS_RAICES and campo.id in _CAMPOS_VISTA
                or self.comando.id in DIALOGOS_CONJUNTOS and campo.id in {"expresion", "punto"}):
            self.programar_grafica()

    def _validar_borrador(self):
        texto = self._borrador.strip()
        if texto:
            try:
                self.campo_actual().validar(texto, self.decimal)
            except ErrorEntrada as error:
                self._aviso_formato(str(error))
                return False
        self._aviso_formato("")
        return True

    def _aviso_formato(self, mensaje):
        self.query_one("#redaccion").set_class(bool(mensaje), "formato-invalido")
        if mensaje:
            self._invalidar_previsualizacion()
        self.avisar(mensaje)
        if mensaje:
            self.call_after_refresh(self.query_one("#aviso").scroll_visible, animate=False)

    def mostrar_teclas(self, texto):
        if "F7 " not in texto:
            texto = "F7 Panel · " + texto
        leyenda = Text()
        for tramo in texto.split(" · "):
            if leyenda:
                leyenda.append("   ·   ", "dim")
            tecla, _, significado = tramo.partition(" ")
            leyenda.append(f"[{tecla}]", f"bold {self.current_theme.primary}")
            leyenda.append(f" {significado}" if significado else "")
        self.query_one("#teclas", Static).update(leyenda)

    def on_descendant_focus(self, evento: DescendantFocus):
        foco = evento.widget
        if foco is not self.focused:
            return
        resultados = self.query_one("#resultados")
        if foco is resultados or resultados in foco.ancestors:
            self._teclas_resultados(foco)
        elif isinstance(foco, (EntradaComando, TextArea)):
            self.actualizar_menu()

    @on(Collapsible.Expanded)
    @on(Collapsible.Collapsed)
    def _actualizar_teclas_ficha(self, evento):
        foco = self.focused
        if isinstance(foco, CollapsibleTitle) and foco.parent is evento.collapsible:
            self._teclas_resultados(foco)

    def _teclas_resultados(self, foco):
        if isinstance(foco, CollapsibleTitle):
            accion = "Abrir" if foco.collapsed else "Plegar"
            teclas = f"Enter {accion} · Tab Cambiar foco"
        elif isinstance(foco, TablaInteractiva):
            teclas = "Ctrl+C Celda · Ctrl+R Fila · Ctrl+T Tabla · Tab Cambiar foco"
        elif isinstance(foco, ArchivosBackend):
            teclas = "↑↓ Elegir archivo · Enter Mostrar carpeta · Ctrl+C Copiar ruta"
        else:
            teclas = "↑↓ Desplazar · RePág/AvPág Página"
        self.mostrar_teclas(f"F7 Chat · {teclas}")

    def action_cambiar_panel(self):
        resultados = self.query_one("#resultados", VerticalScroll)
        foco = self.focused
        if foco is resultados or (foco is not None and resultados in foco.ancestors):
            self.screen.remove_class("lectura")
            entrada = self.entrada if self.entrada.display else self.query_one("#editor", TextArea)
            entrada.focus()
            self.actualizar_menu()
        else:
            self.screen.set_class(not self.screen.has_class("ancha"), "lectura")
            resultados.focus(scroll_visible=False)

    def actualizar_opciones(self):
        campo = self.campo_actual()
        menu = self.query_one("#menu", Static)
        menu.display = bool(campo.opciones)
        lista, _ = self._lista_opciones(campo.opciones, self.navegacion.indice)
        menu.update(lista)
        self.detalle_chat("#detalle-menu", "")
        if not isinstance(self.focused, (EntradaComando, TextArea)):
            return
        teclas = ("F2 Confirmar · Enter Nueva línea" if campo.multilinea else
                  "↑↓ Elegir · Espacio Marcar · Enter Confirmar" if campo.multiple else
                  "↑↓ Elegir · Enter Confirmar" if campo.opciones else "Enter Confirmar")
        if not campo.opciones:
            teclas += " · F6 Símbolos"
        self.mostrar_teclas(teclas + " · F3 Atrás · Esc Cancelar")

    def check_action(self, action, parameters):
        if action == "cambiar_panel":
            return not isinstance(self.screen, Paleta)
        if action == "simbolos":
            return (self.comando is not None and not self._resolviendo and not self.campo_actual().opciones
                    and isinstance(self.focused, (EntradaComando, TextArea)))
        if action == "alternar_casilla":
            return (self.comando is not None and self.entrada.has_focus
                    and self.campo_actual().multiple)
        return super().check_action(action, parameters)

    def action_simbolos(self):
        campo = self.campo_actual()
        herramienta = self.comando.id
        if campo.id == "sistema":
            perfil = PERFIL_SISTEMA
        elif herramienta in DIALOGOS_RAICES and campo.id == "funcion":
            perfil = PERFIL_FUNCION_REAL
        elif herramienta == "relaciones-conjuntos":
            perfil = PERFIL_RELACION_CONJUNTOS if campo.id == "expresion" else PERFIL_LITERAL_CONJUNTOS
        elif herramienta == "cardinalidad-conjuntos" and campo.id == "expresion":
            perfil = PERFIL_REGIONES_CONJUNTOS
        elif herramienta == "operaciones-matrices" and campo.id == "expresion":
            perfil = PERFIL_EXPRESION
        elif campo.id.startswith("@operando_") and self.datos.get("tipo_" + campo.id.split("_")[1]) == "vector_lineal":
            perfil = PERFIL_LINEAL
        else:
            perfil = PERFIL_NUMERICO
        entrada = self.focused

        def insertar(respuesta):
            if respuesta is None:
                return
            texto, retroceso = respuesta
            if isinstance(entrada, TextArea):
                inicio, fin = sorted(entrada.selection)
                edicion = entrada.replace(texto, inicio, fin, maintain_selection_offset=False)
                if retroceso:
                    fila, columna = edicion.end_location
                    entrada.move_cursor((fila, columna - retroceso))
            else:
                inicio, fin = sorted(entrada.selection)
                entrada.replace(texto, inicio, fin)
                entrada.cursor_position -= retroceso

        self.push_screen(Paleta(perfil), insertar)

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
        try:
            valor = campo.validar(valor, self.decimal)
        except ErrorEntrada as error:
            self._aviso_formato(str(error))
            return
        self._aviso_formato("")
        if self.confirmacion:
            if valor == "cancelar":
                self.action_paso_anterior()
                return
            firma = self.confirmacion["firma"]
            self.confirmacion = None
            self.paso = len(self.campos()) - 1
            self.resolver(firma)
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
        self._invalidar_previsualizacion()
        self.estado("Calculando…")
        self.procesar(self._calculo, self.comando.id, self.datos_activos(), self.decimal, self.debugging, firma)

    @work(thread=True, group="calculo")
    def procesar(self, version, herramienta, datos, decimal, depurar, firma):
        try:
            ruta = herramienta
            entrada = datos
            if herramienta in DIALOGOS_ALGEBRA:
                entrada = preparar_algebra(herramienta, datos, decimal)
            elif herramienta in DIALOGOS_RAICES:
                entrada = preparar_raices(datos, decimal)
            if herramienta == "operaciones-vectores":
                if entrada["operacion"] == "combinacion" and int(entrada["vectores"]) == OPERANDOS_MAXIMOS:
                    bloques, archivos = trazar_backend(lambda: combinacion_vectores_maxima(entrada), depurar)
                    if decimal == ",":
                        bloques = tuple(self._con_coma(b) for b in bloques)
                    self.call_from_thread(self.recibir_calculo, version, bloques=bloques, archivos=archivos)
                    return
                entrada = datos_operacion_vectorial(entrada)
                ruta = "operaciones-matrices"
            if firma is not None:
                entrada["confirmacion"] = firma
            if herramienta in DIALOGOS_CONJUNTOS:
                entrada = preparar_conjuntos(herramienta, datos, decimal)
                respuesta, archivos = resolver_conjuntos(herramienta, entrada, depurar,
                                                        azar=datos.get("@modo") == "azar")
            else:
                respuesta, archivos = ejecutar(ruta, entrada, depurar)
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
        aviso = self.aviso_matematico(contexto.get("resultado"))
        self.call_from_thread(self.recibir_calculo, version, bloques=bloques, archivos=archivos,
                              grafica=grafica, aviso=aviso)

    @staticmethod
    def aviso_matematico(resultado):
        if not isinstance(resultado, dict):
            return ""
        if resultado.get("clasificacion") in ("no_aplicable", "sin_convergencia"):
            return resultado.get("mensaje", "")
        if resultado.get("aplicable") is False:
            return resultado.get("motivo", "")
        if resultado.get("invertible") is False and "explicacion" in resultado:
            return resultado["explicacion"]
        return ""

    def recibir_calculo(self, version, mensaje="", nombres=(), *,
                       confirmacion=None, bloques=(), archivos=(), grafica=None, aviso=""):
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
            self.estado("Ejercicio guardado · / para otro · F4 para repetir")
            self.avisar(aviso)
        else:
            self.revisar("Revisa los datos del ejercicio y vuelve a confirmar.", ())

    @staticmethod
    def _con_coma(bloque):
        sustituir = lambda texto: re.sub(r"(?<=[0-9])\.(?=[0-9])", ",", texto)
        if isinstance(bloque, Tabla):
            return Tabla(bloque.titulo, bloque.columnas,
                         tuple(tuple(map(sustituir, f)) for f in bloque.filas))
        return Linea(sustituir(bloque), bloque.estilo) if isinstance(bloque, Linea) else sustituir(bloque)

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

    def detalle_chat(self, selector, texto):
        widget = self.query_one(selector, Static)
        widget.set_class(not texto, "vacio")
        widget.update(texto)

    def avisar(self, mensaje):
        aviso = self.query_one("#aviso", Static)
        aviso.display = bool(mensaje)
        aviso.update(Text.assemble(("!  ", "bold"), mensaje) if mensaje else "")

    def estado(self, mensaje):
        self.query_one("#pregunta", Static).update(mensaje)
