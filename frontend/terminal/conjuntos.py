"""Entrada y visualización local de conjuntos, regiones e intervalos."""

from dataclasses import dataclass
import math

from rich.text import Text
from textual.widgets import Static

from frontend.web.calculadora.forms_conjuntos import (
    CardinalidadesForm, ConjuntosForm, EJEMPLOS, GUIA, PLANTILLAS, inicial_editor, rellenar,
)

from .adaptador import ejecutar
from .dialogos import Campo, ErrorEntrada, campo
from .graficas import Lienzo


DIALOGOS_CONJUNTOS = {"relaciones-conjuntos", "cardinalidad-conjuntos"}
_RUTAS = {"cardinalidad-conjuntos": "cardinalidades-conjuntos"}
_GEOMETRIA = {
    2: ((124, 120, 80), (196, 120, 80)),
    3: ((130, 94, 70), (190, 94, 70), (160, 148, 70)),
}
_MODO = Campo("@modo", "¿Cómo quieres introducir los conjuntos?", (
    ("definiciones", "Escribir definiciones"),
    ("regiones", "Editar los elementos de cada región"),
    ("azar", "Generar regiones al azar"),
    ("ejemplo", "Cargar un ejemplo"),
), "definiciones")
_PLANTILLA = Campo("@plantilla", "¿Qué quieres calcular?", (
    ("personalizada", "Escribir una expresión"),
    *((clave, titulo) for _, filas in GUIA for clave, titulo, _, _ in filas),
), "personalizada")
_AYUDA_EXPRESION = "Ejemplos: A ∪ B, A ∩ B, A ∖ B, 2 ∈ A, potencia(A), ∁(A, U)."


def _definiciones(texto):
    filas = []
    for numero, linea in enumerate(texto.splitlines(), 1):
        if not linea.strip():
            continue
        nombre, sep, literal = map(str.strip, linea.partition("="))
        if not sep or not nombre or not literal:
            raise ErrorEntrada("@definiciones", f"Línea {numero}: escribe nombre = valor, como A = {{1, 2}}.")
        filas.append((nombre, literal))
    return filas


def _opciones_regiones(datos):
    return {
        "cantidad": 0,
        "venn_nombres": datos.get("venn_nombres") or "A, B",
        "venn_universo": datos.get("venn_universo", ""),
    }


def relaciones(datos):
    form = ConjuntosForm()
    modo = datos.get("@modo", "definiciones")
    campos = [_MODO]
    nombres = []
    if modo == "definiciones":
        campos.append(Campo("@definiciones", "Definiciones", ayuda=(
            "Una definición por línea. Ejemplos: A = {1, 2}; I = intervalo(0, 2, cerrado, abierto). "
            "Deja vacío para operar con literales en la expresión."
        ), multilinea=True))
        try:
            nombres = [n for n, _ in _definiciones(datos.get("@definiciones", ""))]
        except ErrorEntrada:
            pass
    elif modo == "ejemplo":
        campos.append(Campo("@ejemplo", "Ejemplo", tuple((k, v[0]) for k, v in EJEMPLOS.items()), "venn"))
        nombres = [n for n, _ in EJEMPLOS[datos.get("@ejemplo", "venn")][1]]
    campos.extend((
        campo(form, "venn_nombres", ayuda="Para Venn, escribe dos o tres nombres separados por comas. Vacío: automático."),
        campo(form, "venn_universo", ayuda="Nombre del universo, si lo necesitas."),
    ))
    if modo in {"regiones", "azar"}:
        opciones = _opciones_regiones(datos)
        nombres = [n.strip() for n in opciones["venn_nombres"].split(",")]
        if modo == "regiones":
            regiones = ConjuntosForm({**opciones, "accion": "editar_regiones"}).regiones
            campos.extend(campo(r.form, r.name, ayuda="Ejemplo: 1, 2, \"rojo\". Vacío: ∅.") for r in regiones)
    campos.append(_PLANTILLA)
    plantilla = datos.get("@plantilla", "personalizada")
    inicial = ""
    if plantilla in PLANTILLAS:
        inicial = rellenar(PLANTILLAS[plantilla], nombres)
    elif modo == "ejemplo":
        inicial = EJEMPLOS[datos.get("@ejemplo", "venn")][2]
    elif modo in {"regiones", "azar"}:
        inicial = " ∪ ".join(nombres)
    campos.extend((
        campo(form, "expresion", inicial=inicial, ayuda=_AYUDA_EXPRESION),
        campo(form, "punto", ayuda="Opcional, para consultar pertenencia a un intervalo. Ejemplo: 1/2."),
    ))
    return tuple(campos)


def cardinalidad(datos):
    form = CardinalidadesForm(initial=datos)
    return (
        campo(form, "numero", inicial="2"),
        campo(form, "modo", inicial="regiones"),
        *(campo(form, region.name, ayuda=region.descripcion) for region in form.regiones),
        campo(form, "universo"),
        campo(form, "expresion", inicial=form.atajos[0],
              ayuda="Ejemplos: " + " · ".join(form.atajos[:3])),
    )


def preparar_conjuntos(herramienta, datos, decimal):
    web = {k: v for k, v in datos.items() if not k.startswith("@")}
    if herramienta == "cardinalidad-conjuntos":
        return web
    modo = datos.get("@modo", "definiciones")
    if modo in {"regiones", "azar"}:
        opciones = _opciones_regiones(datos)
        web.update(opciones)
        web["base_nombres"] = opciones["venn_nombres"]
        web["base_universo"] = opciones["venn_universo"]
        if modo == "regiones":
            web["venn_fuente"] = "regiones"
    else:
        filas = (_definiciones(datos.get("@definiciones", "")) if modo == "definiciones" else
                 EJEMPLOS[datos.get("@ejemplo", "venn")][1])
        web.update(inicial_editor(filas, web.get("expresion", "")))
    if decimal == "," and web.get("punto"):
        web["punto"] = web["punto"].replace(",", ".")
    return web


def resolver_conjuntos(herramienta, datos, depurar, *, azar=False):
    ruta = _RUTAS.get(herramienta, herramienta)
    archivos_azar = ()
    if azar:
        borrador, archivos_azar = ejecutar(ruta, {**datos, "accion": "azar_regiones"}, depurar)
        if borrador.context_data["form"].errors:
            return borrador, archivos_azar
        inicial = borrador.context_data["form"].initial
        datos = {k: v for k, v in inicial.items() if k in borrador.context_data["form"].fields}
    respuesta, archivos = ejecutar(ruta, datos, depurar)
    return respuesta, tuple(dict.fromkeys((*archivos_azar, *archivos)))


@dataclass(frozen=True)
class RepresentacionConjuntos:
    venn: dict | None = None
    recta: dict | None = None


def representacion(contexto):
    resultado = contexto.get("resultado")
    if not resultado:
        return None
    datos = resultado["datos"]
    venn = datos.get("venn") or resultado.get("venn")
    recta = datos.get("recta")
    return RepresentacionConjuntos(venn, recta) if venn or recta else None


def _venn(datos, ancho, paleta):
    nombres = datos["nombres"]
    geometria = _GEOMETRIA.get(len(nombres))
    if not geometria:
        return Text()
    lienzo = Lienzo(min(ancho, 54), 8)
    seleccion = {r["mascara"] for r in datos["regiones"] if r["seleccionada"]}
    if not datos.get("resalta", True):
        seleccion.clear()
    for y in range(lienzo.alto):
        for x in range(lienzo.ancho):
            px = 320 * x / (lienzo.ancho - 1)
            py = 240 * y / (lienzo.alto - 1)
            distancias = [math.hypot(px - cx, py - cy) - radio for cx, cy, radio in geometria]
            mascara = sum(1 << i for i, d in enumerate(distancias) if d <= 0)
            if min(map(abs, distancias)) < 4.5:
                lienzo.punto(x, y, 2)
            elif mascara in seleccion and (x + 2 * y) % 5 == 0:
                lienzo.punto(x, y, 1)
    texto = Text("Diagrama de Venn · " + " / ".join(nombres) + "\n", style=paleta[2])
    texto.append_text(lienzo.texto(paleta))
    for i, r in enumerate(datos["regiones"]):
        etiqueta = r["etiqueta"]
        contenido = (r["cantidad"] or "?" if datos.get("cantidades") else
                     ", ".join(r["etiquetas"]) or ("∅" if r["exterior_conocido"] else "?"))
        if i:
            texto.append("\n")
        texto.append(f"{'●' if r['mascara'] in seleccion else '○'} {etiqueta}   {contenido}",
                     paleta[1] if r["mascara"] in seleccion else "")
    return texto


def _recta(datos, ancho, paleta):
    texto = Text("Recta real", style=paleta[2])
    filas = list(datos["filas"])
    if datos["notacion"]:
        filas.append({"etiqueta": "Resultado", **datos})
    for fila in filas:
        caracteres = ["┄"] * ancho
        for tramo in fila["tramos"]:
            x1, x2 = (round(tramo[k] * (ancho - 1) / 100) for k in ("x1", "x2"))
            for i in range(x1, x2 + 1):
                caracteres[i] = "━"
            caracteres[x1] = "←" if tramo["inferior"] is None else "●" if tramo["cerrado_inferior"] else "○"
            caracteres[x2] = "→" if tramo["superior"] is None else "●" if tramo["cerrado_superior"] else "○"
        if datos["x_punto"] is not None and (fila["etiqueta"] == "Resultado" or datos.get("relacion")):
            caracteres[round(datos["x_punto"] * (ancho - 1) / 100)] = "◆"
        texto.append(f"\n{fila['etiqueta']}  {fila['notacion']}\n")
        texto.append("".join(caracteres), paleta[1])
    if datos["punto"] is not None:
        signo = "∈" if datos["pertenece"] else "∉"
        texto.append(f"\n◆ {datos['punto']} {signo} {datos['notacion']}", paleta[1])
    return texto


class GraficaConjuntos(Static):
    def __init__(self, vista=None, **kwargs):
        super().__init__(markup=False, **kwargs)
        self.vista = vista

    def on_mount(self):
        self.mostrar(self.vista)

    def on_resize(self):
        self.pintar()

    def mostrar(self, vista):
        self.vista = vista
        self.display = vista is not None
        self.pintar()

    def pintar(self):
        if self.vista is None or not self.is_mounted:
            return
        tema = self.app.current_theme
        paleta = ("", tema.accent, tema.primary)
        ancho = max(2, self.content_size.width)
        if self.vista.venn:
            self.update(_venn(self.vista.venn, ancho, paleta))
        elif self.vista.recta:
            self.update(_recta(self.vista.recta, ancho, paleta))
