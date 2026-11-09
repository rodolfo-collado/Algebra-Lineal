"""Editor de definiciones; no calcula relaciones ni mantiene un segundo modelo."""

from django import forms

from backend.conjuntos.literales import analizar_definicion, analizar_literal, validar_nombre
from backend.conjuntos.modelo import Conjunto, orden, presentar
from backend.conjuntos.parser import renombrar_referencias
from backend.conjuntos.presupuesto import Presupuesto
from backend.operandos import OPERANDOS_MAXIMOS
from backend.presupuesto_sistemas import LONGITUD_SISTEMA_MAXIMA
from .forms_feedback import FormularioConErrores
from .servicios_conjuntos import describir_region

# Ejemplos opcionales: el editor empieza vacío y cada uno muestra una idea distinta.
EJEMPLOS = {
    "relaciones": ("Pertenencia e inclusión", [("A", "{1, 2}"), ("B", "{2, {1, 2}}")], "A ∈ B", {}),
    "venn": ("Tres conjuntos y Venn",
             [("U", "{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}"), ("A", "{1, 2, 3, 4, 5}"), ("B", "{4, 5, 6, 7}"), ("C", "{2, 5, 7, 9}")],
             "(A ∪ B) ∖ C", {"venn_universo": "U"}),
    "anidados": ("Conjuntos anidados", [("S", "{1, {1}, {{1}}}")], "|S|", {}),
    "generacion": ("Potencia y producto", [("A", "{1, 2, 3}"), ("B", '{"x", "y"}')], "potencia(A)", {}),
    "intervalos": ("Intervalos", [("I", "intervalo(0, 5, cerrado, abierto)"), ("J", "intervalo(2, 8, abierto, cerrado)")],
                   "I ∖ J", {}),
}

# Guía de operaciones: plantillas con los nombres definidos ({a}, {b}, {u}) y un elemento ({x}).
GUIA = (
    ("Operaciones", (
        ("union", "Unión", "{a} ∪ {b}", "Los elementos que están en al menos uno."),
        ("interseccion", "Intersección", "{a} ∩ {b}", "Los elementos comunes."),
        ("diferencia", "Diferencia", "{a} ∖ {b}", "Los del primero que no están en el segundo."),
        ("complemento", "Complemento", "∁({a}, {u})", "Lo que falta para completar el universo, que siempre se escribe."),
        ("cardinalidad", "Cardinalidad", "|{a}|", "Cuántos elementos distintos tiene."),
        ("potencia", "Conjunto potencia", "potencia({a})", "Todos sus subconjuntos, incluido ∅."),
        ("producto", "Producto cartesiano", "{a} × {b}", "Todos los pares ordenados."),
    )),
    ("Relaciones", (
        ("pertenencia", "Pertenencia", "{x} ∈ {a}", "¿Es uno de sus elementos? También ∉."),
        ("inclusion", "Inclusión", "{a} ⊆ {b}", "¿Cada elemento del primero está en el segundo? ⊂ además exige que sean distintos."),
        ("igualdad", "Igualdad", "{a} = {b}", "¿Tienen los mismos elementos? También ≠."),
    )),
    ("Intervalos", (
        ("intervalo", "Intervalo", "intervalo(0, 1, cerrado, abierto)", "Es [0, 1). Usa -inf o inf para no acotar."),
        ("intervalos", "Operar intervalos", "intervalo(-inf, 2, abierto, cerrado) ∖ intervalo(0, 1, abierto, abierto)",
         "∪, ∩, ∖ y ∁ también operan regiones de la recta."),
    )),
)
PLANTILLAS = {clave: plantilla for _, filas in GUIA for clave, _, plantilla, _ in filas}


def elegir_nombres(nombres):
    """Nombres para la guía: dos conjuntos (si U existe, se reserva como universo)."""
    otros = [n for n in nombres if n != "U"] or list(nombres)
    a = otros[0] if otros else "A"
    # Con un solo conjunto, el segundo operando es un literal: «S ∪ {1}» y no «S ∪ S».
    b = otros[1] if len(otros) > 1 else ("B" if not otros else "{1}")
    u = "U" if "U" in nombres and "U" not in (a, b) else (f"{a} ∪ {b}" if a != b else a)
    return a, b, u


def rellenar(plantilla, nombres, elemento="1"):
    """Escribe una plantilla de la guía con los nombres disponibles; sin nombres usa A y B."""
    a, b, u = elegir_nombres(nombres)
    return plantilla.replace("{a}", a).replace("{b}", b).replace("{u}", u).replace("{x}", elemento)


def campo_texto(etiqueta, *, multilinea=False, **attrs):
    widget = forms.Textarea if multilinea else forms.TextInput
    return forms.CharField(label=etiqueta, required=False, max_length=LONGITUD_SISTEMA_MAXIMA,
                           widget=widget(attrs={"class": "field-input field-input-code", "spellcheck": "false",
                                                "autocomplete": "off", **attrs}))


class ConjuntosForm(FormularioConErrores):
    # Se escribe junto a la recta del resultado, fuera del <form>: `form` lo asocia igualmente.
    punto = campo_texto("Punto x", placeholder="1/2", inputmode="decimal", form="conjuntos-form")
    venn_nombres = campo_texto("Conjuntos del diagrama", placeholder="Automático: los de la expresión")
    venn_universo = campo_texto("Universo", placeholder="Ninguno")
    cantidad = forms.IntegerField(min_value=0, max_value=OPERANDOS_MAXIMOS, widget=forms.HiddenInput)
    expresion = campo_texto("Expresión", multilinea=True, rows=2, placeholder="A ∪ B")
    definicion = campo_texto("Nuevo conjunto", placeholder="T = {1, 2, {3, 4}}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bloques = []
        try:
            cantidad = int(self.data.get("cantidad", 0)) if self.is_bound else self.initial.get("cantidad", 0)
        except (ValueError, TypeError):
            cantidad = 0
        cantidad = max(0, min(cantidad, OPERANDOS_MAXIMOS))
        for i in range(cantidad):
            self.fields[f"nombre_{i}"] = campo_texto("Nombre", **{"data-campo": "nombre", "aria-describedby": "nombres-ayuda"})
            self.fields[f"contenido_{i}"] = campo_texto("Elementos", multilinea=True, rows=1, **{"aria-describedby": "conjuntos-ayuda"})
            self.fields[f"anterior_{i}"] = forms.CharField(required=False, widget=forms.HiddenInput,
                                                         max_length=LONGITUD_SISTEMA_MAXIMA)
            self.bloques.append({"indice": i, "nombre": self[f"nombre_{i}"],
                                 "contenido": self[f"contenido_{i}"], "anterior": self[f"anterior_{i}"]})

    def clean(self):
        datos = super().clean()
        permitidos = set(self.fields) | {"csrfmiddlewaretoken", "accion", "eliminar", "plantilla"}
        if set(self.data) - permitidos:
            self.add_error(None, "El envío contiene campos ajenos al formulario.")
        if hasattr(self.data, "getlist") and any(len(self.data.getlist(n)) != 1 for n in self.data):
            self.add_error(None, "Envía un único valor por campo; hay campos repetidos.")
        self.accion = "usar" if "plantilla" in self.data else self.data.get("accion", "calcular")
        if self.accion not in {"calcular", "guardar", "agregar", "usar"}:
            self.add_error(None, "Acción desconocida.")
        if self.accion == "usar" and self.data.get("plantilla") not in PLANTILLAS:
            self.add_error(None, "Esa operación no está en la guía.")
        eliminar = self.data.get("eliminar")
        if eliminar is not None and eliminar not in {str(b["indice"]) for b in self.bloques}:
            self.add_error(None, "No existe el conjunto que intentas eliminar.")
        self.filas = []
        self.entorno = {}
        self.presupuesto = Presupuesto()
        cambios = {}
        if self.errors:
            return datos
        for bloque in self.bloques:
            i = bloque["indice"]
            if str(i) == eliminar:
                continue
            nombre = datos[f"nombre_{i}"]
            contenido = datos[f"contenido_{i}"]
            self.filas.append((nombre, contenido))
            try:
                validar_nombre(nombre)
                if nombre in self.entorno:
                    raise ValueError(f"El nombre «{nombre}» ya está definido. Usa nombres únicos.")
                self.presupuesto.texto(nombre)
            except ValueError as error:
                self.add_error(f"nombre_{i}", str(error))
                continue
            try:
                self.entorno[nombre] = analizar_literal(contenido, presupuesto=self.presupuesto)
            except ValueError as error:
                self.add_error(f"contenido_{i}", str(error))
            anterior = datos[f"anterior_{i}"]
            if anterior and anterior != nombre:
                cambios[anterior] = nombre
        expresion = datos.get("expresion", "")
        if self.accion == "usar":
            nombres = list(self.entorno)
            primero = self.entorno.get(elegir_nombres(nombres)[0])
            elemento = (presentar(min(primero.elementos, key=orden))
                        if isinstance(primero, Conjunto) and primero.elementos else "1")
            expresion = rellenar(PLANTILLAS[self.data["plantilla"]], nombres, elemento)
        elif cambios and expresion:
            try:
                expresion = renombrar_referencias(expresion, cambios)
            except ValueError as error:
                self.add_error("expresion", str(error))
        self.expresion = expresion
        if self.accion == "agregar":
            try:
                if len(self.filas) >= OPERANDOS_MAXIMOS:
                    raise ValueError(f"El editor admite hasta {OPERANDOS_MAXIMOS} conjuntos.")
                nombre, valor = analizar_definicion(datos.get("definicion", ""), presupuesto=self.presupuesto)
                if nombre in self.entorno:
                    raise ValueError(f"El nombre «{nombre}» ya está definido.")
                self.filas.append((nombre, presentar(valor)))
            except ValueError as error:
                self.add_error("definicion", str(error))
        return datos


def inicial_editor(filas=(), expresion="", **extra):
    inicial = {"cantidad": len(filas), "expresion": expresion, **extra}
    for i, (nombre, contenido) in enumerate(filas):
        inicial.update({f"nombre_{i}": nombre, f"contenido_{i}": contenido, f"anterior_{i}": nombre})
    return inicial


def inicial_ejemplo(clave):
    """Datos iniciales de un ejemplo de la lista, o del editor vacío si la clave no existe."""
    if clave not in EJEMPLOS:
        return inicial_editor()
    _, filas, expresion, extra = EJEMPLOS[clave]
    return inicial_editor(filas, expresion, **extra)


class CardinalidadesForm(FormularioConErrores):
    numero = forms.ChoiceField(label='Conjuntos', choices=(('2', 'Dos: A y B'), ('3', 'Tres: A, B y C')),
                               widget=forms.RadioSelect)
    modo = forms.ChoiceField(label='Datos que conoces',
                             choices=(('regiones', 'Regiones separadas'), ('intersecciones', 'Conjuntos e intersecciones')),
                             widget=forms.RadioSelect)
    universo = forms.IntegerField(label='Universo |U| (opcional)', required=False, min_value=0, max_value=10**100-1)
    expresion = campo_texto('¿Qué quieres contar?', placeholder='A ∪ B')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        numero = self.data.get('numero', '2') if self.is_bound else self.initial.get('numero', '2')
        self.nombres = tuple('ABC'[:3 if numero == '3' else 2])
        self.regiones = []
        self.modo_actual = modo = self.data.get('modo', 'regiones') if self.is_bound else self.initial.get('modo', 'regiones')
        n = len(self.nombres)
        for m in range(1, 1 << n):
            dentro = [x for i, x in enumerate(self.nombres) if m & (1 << i)]
            if modo == 'intersecciones':
                etiqueta = '|' + ' ∩ '.join(dentro) + '|'
                cubre = [k for k in range(1, 1 << n) if k & m == m]
                descripcion = 'Todos los de ' + (dentro[0] if len(dentro) == 1 else ', '.join(dentro[:-1]) + ' y ' + dentro[-1])
            else:
                etiqueta = ' ∩ '.join(x if m & (1 << i) else f'{x}ᶜ' for i, x in enumerate(self.nombres))
                cubre = [m]
                descripcion = describir_region(m, self.nombres)
            self.fields[f'region_{m}'] = forms.IntegerField(label=etiqueta, min_value=0, max_value=10**100-1, required=False)
            campo = self[f'region_{m}']
            # Regiones que cubre el dato: el icono las sombrea; no es un cálculo del resultado.
            campo.cubre = ' '.join(map(str, cubre))
            campo.mascara = m
            campo.descripcion = descripcion
            self.regiones.append(campo)
        # Atajos de lo que suele preguntarse; solo escriben la expresión, no calculan.
        self.atajos = (('A ∪ B', 'A ∩ B', 'A ∖ B', '(A ∖ B) ∪ (B ∖ A)', '∁(A ∪ B, U)') if n == 2 else
                       ('A ∪ B ∪ C', 'A ∩ B ∩ C', '(A ∩ B) ∖ C', 'A ∖ (B ∪ C)', '∁(A ∪ B ∪ C, U)'))
        for campo in self.fields.values():
            if not isinstance(campo.widget, forms.RadioSelect):
                campo.widget.attrs['class'] = 'field-input'
        for nombre in [f'region_{m}' for m in range(1, 1 << n)] + ['universo']:
            self.fields[nombre].widget.attrs.update({'inputmode': 'numeric', 'class': 'field-input cardinalidad-campo'})

    def clean(self):
        datos = super().clean()
        permitidos = set(self.fields) | {'csrfmiddlewaretoken', 'accion'}
        if self.data.get('accion') == 'ajustar':
            permitidos.update(f'region_{m}' for m in range(1, 8))
        if set(self.data) - permitidos:
            self.add_error(None, 'El envío contiene campos ajenos al formulario.')
        if hasattr(self.data, 'getlist') and any(len(self.data.getlist(n)) != 1 for n in self.data):
            self.add_error(None, 'Envía un único valor por campo; hay campos repetidos.')
        accion = self.data.get('accion', 'calcular')
        if accion not in ('calcular', 'ajustar'):
            self.add_error(None, 'Acción desconocida.')
        if accion == 'calcular':
            for m in range(1, 1 << len(self.nombres)):
                nombre = f'region_{m}'
                if datos.get(nombre) is None and nombre not in self.errors:
                    self.add_error(nombre, 'Indica esta cardinalidad, incluso si es cero.')
        return datos
