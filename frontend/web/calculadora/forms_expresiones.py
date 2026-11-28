"""Símbolos, expresión y presentación de Operaciones con matrices. El cálculo vive en el backend.

Presupuesto común (P26.6), comprobado antes de crear un campo por celda:
- estructura: hasta OPERANDOS_MAXIMOS símbolos, CELDAS_MAXIMAS celdas y
  CAMPOS_MAXIMOS campos entre estructura y celdas, dentro del límite de Django;
- expresión: hasta OPERANDOS_MAXIMOS operandos, OPERANDOS_MAXIMOS - 1 operaciones y
  CELDAS_MAXIMAS entradas, contando cada aparición de un símbolo, para que repetirlo
  (o encadenar signos y traspuestas) no eluda los topes.
"""

from django import forms

from backend.expresiones_matriciales.combinacion import incognitas
from backend.expresiones_matriciales.lineal import analizar_lineal
from backend.expresiones_matriciales.nodos import Simbolo, nodos
from backend.expresiones_matriciales.parser import analizar_entrada, nombre_valido
from backend.operandos import CAMPOS_MAXIMOS, CELDAS_MAXIMAS, OPERANDOS_MAXIMOS, nombre_matriz

from .forms_matrices import FormularioCeldas, campo_dimension, campo_numero
from .opciones_matrices import (
    AYUDA_METODOS, DIMENSION_MAXIMA, DIMENSION_MINIMA, DIMENSION_PREDETERMINADA, METODO_PREDETERMINADO, METODOS,
)

SIMBOLOS_INICIALES = 2
LONGITUD_COMPONENTE_MAXIMA = 200
LONGITUD_EXPRESION_MAXIMA = 400
# 990 campos de operandos + 5 expresiones + csrf, cantidad, método, firma y nodo.
EXPRESIONES_MAXIMAS = 5
NOMBRES_EXPRESIONES = ("expresion", *(f"expresion_{i}" for i in range(1, EXPRESIONES_MAXIMAS)))
# Los tipos simbólicos siguen disponibles, agrupados aparte para no competir con los valores.
TIPOS = (
    ("Con valores", (("matriz", "Matriz"), ("vector", "Vector"), ("escalar", "Escalar"))),
    ("Simbólicos", (
        ("matriz_desconocida", "Matriz desconocida"),
        ("vector_simbolico", "Vector simbólico"),
        ("vector_lineal", "Vector lineal"),
    )),
)
_TIPOS_VALIDOS = {clave for _, grupo in TIPOS for clave, _ in grupo}
_SIN_CELDAS = frozenset({"matriz_desconocida", "vector_simbolico"})
_CON_COLUMNAS = frozenset({"matriz", "matriz_desconocida"})
_COMPONENTES = frozenset({"vector", "vector_simbolico", "vector_lineal"})


def campo_lineal(etiqueta):
    return forms.CharField(
        label=etiqueta, required=False, max_length=LONGITUD_COMPONENTE_MAXIMA,
        widget=forms.TextInput(attrs={
            "class": "matrix-input matrix-input-lineal", "autocomplete": "off",
            "spellcheck": "false", "placeholder": "3x1 - 2x2",
        }),
        error_messages={"max_length": "Cada componente admite hasta 200 caracteres."},
    )


_UNIDADES = {"Filas": "una fila", "Componentes": "una componente", "Columnas": "una columna"}


def rotulos_dimension(etiqueta, simbolo):
    """«Quitar una fila de A» y «Agregar una fila a A»: los mismos textos que escribe expresiones.js."""
    unidad = _UNIDADES[etiqueta]
    return f"Quitar {unidad} de {simbolo}", f"Agregar {unidad} a {simbolo}"


def forma(tipo, filas, columnas):
    """(alto, ancho) de las celdas que el símbolo dibuja."""
    if tipo in _SIN_CELDAS:
        return 0, 0
    if tipo == "escalar":
        return 1, 1
    if tipo in ("vector", "vector_lineal"):
        return filas, 1
    return filas, columnas


def tamano(tipo, filas, columnas):
    """Entradas que el símbolo aporta a una operación, también si son simbólicas."""
    if tipo == "escalar":
        return 1
    return filas * columnas if tipo in _CON_COLUMNAS else filas


def campos_estructura(tipo):
    """Nombre y tipo, más filas o componentes, más columnas: lo que envía cada símbolo además de sus celdas."""
    return 2 + (tipo != "escalar") + (tipo in _CON_COLUMNAS)


def nombre_libre(usados):
    """A … Z y después A1 … Z1, A2 …: nombres válidos que no se leen como un producto implícito."""
    sufijo = 0
    while True:
        for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            nombre = letra + (str(sufijo) if sufijo else "")
            if nombre not in usados:
                return nombre
        sufijo += 1


def presupuesto_estructura(estructuras):
    """Mensaje si los símbolos (tipo, filas, columnas) no caben en el formulario; None si caben."""
    celdas = sum(alto * ancho for alto, ancho in (forma(*estructura) for estructura in estructuras))
    campos = celdas + sum(campos_estructura(tipo) for tipo, _, _ in estructuras)
    if celdas > CELDAS_MAXIMAS:
        return (f"Los {len(estructuras)} operandos suman {celdas} celdas y la interfaz admite hasta "
                f"{CELDAS_MAXIMAS}: quita operandos o reduce sus dimensiones.")
    if campos > CAMPOS_MAXIMOS:
        return (f"Los {len(estructuras)} operandos ocupan {campos} campos del formulario (nombre, tipo, dimensiones "
                f"y celdas) y la interfaz admite hasta {CAMPOS_MAXIMOS}: quita operandos o reduce sus dimensiones.")
    return None


def medir_expresion(arbol, tamanos):
    todos = nodos(arbol)
    hojas = [nodo for nodo in todos if not nodo.hijos()]
    # En x1 u + x2 v = b, cada xᵢ marca un coeficiente a hallar y su producto se
    # resuelve como parte del sistema, que conserva su propia estimación.
    coeficientes = sum(isinstance(hoja, Simbolo) and hoja.nombre not in tamanos for hoja in hojas)
    entradas = sum(tamanos.get(hoja.nombre, 0) if isinstance(hoja, Simbolo) else 1 for hoja in hojas)
    return len(hojas) - coeficientes, len(todos) - len(hojas) - coeficientes, entradas


def presupuesto_expresion(uso):
    """Como una operación de hasta 50 operandos del módulo anterior: AAAA usa cuatro veces A.

    Los operandos son las apariciones de símbolos y números, con todas sus entradas;
    las operaciones (49 para 50 operandos) acotan también las cadenas de signos y traspuestas.
    """
    operandos, operaciones, entradas = uso
    if operandos > OPERANDOS_MAXIMOS:
        return (f"La expresión tiene {operandos} operandos y la interfaz admite hasta {OPERANDOS_MAXIMOS}: "
                "cada aparición de un operando o de un número cuenta.")
    if operaciones > OPERANDOS_MAXIMOS - 1:
        return (f"La expresión tiene {operaciones} operaciones y la interfaz admite hasta {OPERANDOS_MAXIMOS - 1}: "
                "cada suma, resta, producto, signo menos o traspuesta cuenta.")
    if entradas > CELDAS_MAXIMAS:
        return (f"Los operandos de la expresión suman {entradas} entradas y la interfaz admite hasta {CELDAS_MAXIMAS}: "
                "cada aparición de un operando cuenta todas sus entradas.")
    return None


class ExpresionMatricialForm(FormularioCeldas):
    """Un símbolo por bloque. Calcular exige las celdas de esa estructura; Aplicar, agregar y eliminar no."""

    longitud_lineal_maxima = LONGITUD_COMPONENTE_MAXIMA

    confirmacion = forms.CharField(required=False, strip=False, widget=forms.HiddenInput)

    expresion = forms.CharField(
        label="Expresión", required=False,
        widget=forms.Textarea(attrs={
            "class": "field-input field-input-code", "rows": 2, "spellcheck": "false",
            "placeholder": "A + B", "maxlength": LONGITUD_EXPRESION_MAXIMA,
        }),
    )
    cantidad = forms.IntegerField(
        min_value=0, max_value=OPERANDOS_MAXIMOS, initial=SIMBOLOS_INICIALES,
        # expresiones.js lee los topes de este mismo control.
        widget=forms.HiddenInput(attrs={
            "data-operandos-maximos": OPERANDOS_MAXIMOS, "data-celdas-maximas": CELDAS_MAXIMAS,
            "data-campos-maximos": CAMPOS_MAXIMOS,
        }),
        error_messages={
            "required": "Indica cuántos operandos hay.",
            "invalid": "La cantidad de operandos debe ser un entero.",
            "min_value": "La cantidad de operandos no puede ser negativa.",
            "max_value": f"La interfaz admite hasta {OPERANDOS_MAXIMOS} operandos.",
        },
    )
    # Solo presentación: el producto se calcula una vez y cambia cómo se explica.
    metodo = forms.ChoiceField(
        label="Cómo mostrar los productos", choices=METODOS, initial=METODO_PREDETERMINADO, required=False,
        widget=forms.RadioSelect, help_text=AYUDA_METODOS,
        error_messages={"invalid_choice": "Selecciona una forma válida de mostrar los productos."},
    )

    def __init__(self, *args, accion=None, **kwargs):
        self.accion = accion
        super().__init__(*args, **kwargs)
        self.nombres_lineales = []
        self.bloques = []
        self.expresiones_maximas = EXPRESIONES_MAXIMAS
        self.expresiones = [self["expresion"]]
        origen = self.data if self.is_bound else self.initial
        for nombre in NOMBRES_EXPRESIONES[1:]:
            if nombre not in origen:
                break
            self.fields[nombre] = forms.CharField(required=False, widget=forms.Textarea(
                attrs=self.fields["expresion"].widget.attrs.copy(),
            ))
            self.expresiones.append(self[nombre])
        estructuras = [self._estructura(indice) for indice in range(self._cantidad())]
        # Presupuesto antes de crear un campo por celda. Si no cabe, se dibujan los mismos
        # símbolos con las dimensiones iniciales (a lo sumo 50 de 2×2) y clean() lo rechaza.
        self.error_presupuesto = presupuesto_estructura(estructuras)
        if self.error_presupuesto:
            self.grupo_error = "symbol-list"
            estructuras = [(tipo, DIMENSION_PREDETERMINADA, DIMENSION_PREDETERMINADA) for tipo, _, _ in estructuras]
        for indice, estructura in enumerate(estructuras):
            self._bloque(indice, *estructura)

    @property
    def opciones_abiertas(self):
        """La presentación de productos se despliega sola cuando no es la predeterminada."""
        return (self["metodo"].value() or METODO_PREDETERMINADO) != METODO_PREDETERMINADO

    def _publicado(self, nombre, defecto):
        if self.is_bound:
            return self.data.get(nombre, defecto)
        return self.initial.get(nombre, defecto)

    def _cantidad(self):
        crudo = self._publicado("cantidad", SIMBOLOS_INICIALES)
        try:
            valor = int(crudo)
        except (TypeError, ValueError):
            return 0
        if not 0 <= valor <= OPERANDOS_MAXIMOS:
            return 0
        return valor

    def _entero(self, nombre, defecto):
        try:
            valor = int(self._publicado(nombre, defecto))
        except (TypeError, ValueError):
            return defecto
        if not DIMENSION_MINIMA <= valor <= DIMENSION_MAXIMA:
            return defecto
        return valor

    def _estructura(self, indice):
        tipo = self._publicado(f"tipo_{indice}", "matriz")
        if tipo not in _TIPOS_VALIDOS:
            tipo = "matriz"
        return (
            tipo,
            self._entero(f"filas_{indice}", DIMENSION_PREDETERMINADA),
            self._entero(f"columnas_{indice}", DIMENSION_PREDETERMINADA),
        )

    def _bloque(self, indice, tipo, filas, columnas):
        self.fields[f"nombre_{indice}"] = forms.CharField(
            label=f"Nombre del operando {indice + 1}", max_length=12,
            initial=self.initial.get(f"nombre_{indice}", nombre_matriz(indice)),
            widget=forms.TextInput(attrs={
                "class": "field-input symbol-field-name", "autocomplete": "off",
                "spellcheck": "false", "maxlength": "12", "data-campo": "nombre",
            }),
            error_messages={"required": "Indica el nombre del operando."},
        )
        self.fields[f"tipo_{indice}"] = forms.ChoiceField(
            label=f"Tipo del operando {indice + 1}", choices=TIPOS,
            initial=self.initial.get(f"tipo_{indice}", "matriz"),
            widget=forms.Select(attrs={"class": "field-input symbol-field-type", "data-campo": "tipo"}),
            error_messages={"invalid_choice": "El tipo debe ser matriz, vector o escalar, matriz desconocida, vector simbólico o vector lineal."},
        )
        simbolo = self._simbolo(indice)
        bloque = {
            "indice": indice, "tipo": tipo, "filas": filas, "columnas": columnas,
            "nombre": self[f"nombre_{indice}"], "tipo_campo": self[f"tipo_{indice}"],
            "filas_campo": None, "columnas_campo": None, "celdas": [],
            "nota": self._nota(tipo, indice, filas),
            "celdas_visibles": tipo not in _SIN_CELDAS,
            # Nombres accesibles que dicen a qué símbolo pertenece cada control;
            # expresiones.js los actualiza al renombrar.
            "simbolo": simbolo,
        }
        if tipo != "escalar":
            etiqueta = "Componentes" if tipo in _COMPONENTES else "Filas"
            self.fields[f"filas_{indice}"] = campo_dimension(etiqueta)
            self.fields[f"filas_{indice}"].initial = filas
            self.fields[f"filas_{indice}"].widget.attrs["data-campo"] = "filas"
            bloque["filas_campo"] = self[f"filas_{indice}"]
            bloque["quitar_filas"], bloque["agregar_filas"] = rotulos_dimension(etiqueta, simbolo)
        if tipo in _CON_COLUMNAS:
            self.fields[f"columnas_{indice}"] = campo_dimension("Columnas")
            self.fields[f"columnas_{indice}"].initial = columnas
            self.fields[f"columnas_{indice}"].widget.attrs["data-campo"] = "columnas"
            bloque["columnas_campo"] = self[f"columnas_{indice}"]
            bloque["quitar_columnas"], bloque["agregar_columnas"] = rotulos_dimension("Columnas", simbolo)
        alto, ancho = forma(tipo, filas, columnas)
        for fila in range(alto):
            celdas = []
            for columna in range(ancho):
                clave = f"celda_{indice}_{fila}_{columna}"
                etiqueta = self._etiqueta(tipo, indice, fila, columna)
                if tipo == "vector_lineal":
                    self.nombres_lineales.append(clave)
                    self.fields[clave] = campo_lineal(etiqueta)
                else:
                    self.nombres_celdas.append(clave)
                    self.fields[clave] = campo_numero(etiqueta)
                self.fields[clave].widget.attrs.update({
                    "data-campo": "celda", "data-fila": str(fila), "data-columna": str(columna),
                })
                celdas.append(self[clave])
            bloque["celdas"].append(celdas)
        self.bloques.append(bloque)

    def _nota(self, tipo, indice, filas):
        if tipo == "matriz_desconocida":
            return "Matriz desconocida: indica filas y columnas. Las entradas no se escriben; se determinan al comparar coeficientes."
        if tipo == "vector_lineal":
            return "Cada componente es una expresión lineal, como 3x1 - 2x2."
        if tipo != "vector_simbolico":
            return ""
        nombre = str(self._publicado(f"nombre_{indice}", "") or "").strip()
        if not nombre_valido(nombre):
            return "Indica el nombre. Sus componentes serán independientes: nombre1, nombre2, …"
        return "Componentes independientes: " + ", ".join(f"{nombre}{numero}" for numero in range(1, filas + 1)) + "."

    def _simbolo(self, indice):
        """El nombre con que se presenta el símbolo (o su número, si todavía no tiene)."""
        nombre = str(self._publicado(f"nombre_{indice}", "") or "").strip()
        if not nombre and f"nombre_{indice}" in self.fields:
            nombre = str(self.fields[f"nombre_{indice}"].initial or "").strip()
        return nombre or str(indice + 1)

    def _etiqueta(self, tipo, indice, fila, columna):
        nombre = self._simbolo(indice)
        if tipo == "escalar":
            return f"Valor del escalar {nombre}"
        if tipo == "vector_lineal":
            return f"Vector lineal {nombre}, componente {fila + 1}"
        if tipo == "vector":
            return f"Vector {nombre}, componente {fila + 1}"
        return f"Matriz {nombre}, fila {fila + 1}, columna {columna + 1}"

    def clean(self):
        """Valida por fases; la primera fase con errores detiene las siguientes.

        1. Campos del formulario y presupuesto de la estructura.
        2. Nombre y dimensiones de cada operando.
        3. Acciones del editor (Aplicar, agregar, eliminar): devuelven `estado`,
           el formulario que se vuelve a dibujar, sin exigir celdas ni expresión.
        4. Calcular: valida los valores compartidos y prepara cada expresión.
        """
        datos = super().clean()
        self.rechazar_campos_repetidos()
        if self.error_presupuesto:
            # También con Aplicar: una estructura que no cabe no se acepta ni para redibujar.
            self.add_error(None, self.error_presupuesto)
        if self.errors:
            return datos
        simbolos = self._simbolos_declarados(datos)
        if self.errors:
            return datos
        if self.accion == "eliminar" and not self._indice_eliminar(len(simbolos)):
            self.add_error(None, "No se puede eliminar ese operando.")
            return datos
        if not self._contrato(simbolos):
            self.grupo_error = "symbol-list"
            self.add_error(None, "Las celdas recibidas no coinciden con los operandos indicados. Pulsa Aplicar para ajustar la estructura.")
            return datos
        if self.accion == "agregar":
            impedimento = self._impedimento_para_agregar(simbolos)
            if impedimento:
                self.add_error(None, impedimento)
                return datos
        if self.accion:
            if self.accion == "agregar_expresion" and len(self.expresiones) == EXPRESIONES_MAXIMAS:
                self.add_error(None, f"La interfaz admite hasta {EXPRESIONES_MAXIMAS} expresiones.")
                return datos
            if self.accion == "eliminar_expresion" and not (
                len(self.expresiones) > 1 and self._indice_eliminar(len(self.expresiones), self.accion)
            ):
                self.add_error(None, "No se puede eliminar esa expresión.")
                return datos
            datos["estado"] = self._estado(simbolos, datos.get("metodo"))
            return datos
        if len(self.expresiones) == 1 and not datos["expresion"]:
            self.add_error("expresion", "Escribe una expresión.")
            return datos
        self.convertir_numeros(datos, self.nombres_celdas)
        self._validar_componentes_lineales(datos)
        if self.errors:
            return datos
        datos["entradas"] = self._entradas(datos, simbolos)
        if len(self.expresiones) == 1 and datos["entradas"] and not self.errors:
            datos["entrada"] = datos["entradas"][0]["entrada"]
        return datos

    def _simbolos_declarados(self, datos):
        """Nombre, tipo y dimensiones de cada bloque, sin sus celdas.

        Asocia cada error a su campo. Un nombre inválido deja fuera ese bloque;
        una dimensión vacía se registra como 1 para que la lista siga completa
        (`clean` se detiene igualmente por el error).
        """
        simbolos = []
        vistos = set()
        for bloque in self.bloques:
            indice = bloque["indice"]
            nombre = (datos.get(f"nombre_{indice}") or "").strip()
            tipo = datos.get(f"tipo_{indice}")
            if not nombre_valido(nombre):
                self.add_error(f"nombre_{indice}", "Usa una letra seguida de letras o dígitos, como A, u o k.")
                continue
            if nombre in vistos:
                self.add_error(f"nombre_{indice}", f"El operando {nombre} está repetido.")
            vistos.add(nombre)
            # Un escalar no envía filas; solo las matrices envían columnas.
            filas = datos.get(f"filas_{indice}") if tipo != "escalar" else 1
            columnas = datos.get(f"columnas_{indice}") if tipo in _CON_COLUMNAS else 1
            if tipo != "escalar" and filas is None:
                self.add_error(f"filas_{indice}", "Indica esa dimensión.")
            if tipo in _CON_COLUMNAS and columnas is None:
                self.add_error(f"columnas_{indice}", "Indica el número de columnas.")
            simbolos.append({
                "indice": indice, "nombre": nombre, "tipo": tipo,
                "filas": filas or 1, "columnas": columnas or 1,
            })
        return simbolos

    def _impedimento_para_agregar(self, simbolos):
        """Por qué no cabe otro operando (una matriz 2×2 nueva), o None si cabe."""
        if len(simbolos) >= OPERANDOS_MAXIMOS:
            return f"No se puede agregar otro operando: la interfaz admite hasta {OPERANDOS_MAXIMOS}."
        otra = presupuesto_estructura([
            *((s["tipo"], s["filas"], s["columnas"]) for s in simbolos),
            ("matriz", DIMENSION_PREDETERMINADA, DIMENSION_PREDETERMINADA),
        ])
        if otra:
            return f"No se puede agregar otro operando: una matriz 2×2 más no cabe. {otra}"
        return None

    def _validar_componentes_lineales(self, datos):
        """Cada componente de un vector lineal debe ser una expresión lineal; se conserva como texto."""
        for clave in self.nombres_lineales:
            texto = (datos.get(clave) or "").strip()
            if not texto:
                self.add_error(clave, "Escribe la expresión lineal de esta componente.")
                continue
            try:
                analizar_lineal(texto)
            except ValueError as error:
                self.add_error(clave, str(error))
            else:
                datos[clave] = texto

    def _entradas(self, datos, simbolos):
        nodo = (self.data.get("nodo") or "").strip()
        indice_nodo = 0
        if nodo and len(self.expresiones) > 1:
            indice, separador, nodo = nodo.partition("|")
            indices = {str(i): i for i in range(len(self.expresiones))}
            if not separador or not nodo or indice not in indices:
                self.add_error(None, "La subexpresión no corresponde a ninguna expresión del formulario.")
                return []
            indice_nodo = indices[indice]
        tamanos = {s["nombre"]: tamano(s["tipo"], s["filas"], s["columnas"]) for s in simbolos}
        operandos = self._operandos_para_calcular(datos, simbolos)
        metodo = datos.get("metodo") or METODO_PREDETERMINADO
        filas = []
        for indice, campo in enumerate(self.expresiones):
            texto = datos[campo.name]
            uso = (0, 0, 0)
            error = None
            if not texto:
                error = "Escribe una expresión."
            elif len(texto) > LONGITUD_EXPRESION_MAXIMA:
                error = f"La expresión admite hasta {LONGITUD_EXPRESION_MAXIMA} caracteres."
            else:
                # Los coeficientes de una combinación lineal cuentan como hojas.
                nombres = set(tamanos)
                if "=" in texto:
                    nombres.update(incognitas(texto, nombres))
                try:
                    uso = medir_expresion(analizar_entrada(texto, nombres), tamanos)
                except ValueError:
                    # El servicio conserva los diagnósticos del analizador y de las igualdades.
                    pass
                error = presupuesto_expresion(uso)
            if error:
                self.add_error(campo.name, error)
            filas.append({
                "campo": campo.name, "indice": indice, "uso": uso, "error": error,
                "entrada": {"expresion": texto, "simbolos": operandos, "metodo": metodo,
                            "nodo": (nodo or None) if indice == indice_nodo else None},
            })
        return filas

    @staticmethod
    def _operandos_para_calcular(datos, simbolos):
        """{nombre: definición} como la recibe el evaluador, con los valores ya validados.

        Las matrices desconocidas y los vectores simbólicos solo llevan su forma;
        el escalar es una celda, los vectores una lista de componentes (números
        exactos o, en el vector lineal, texto) y la matriz una lista de filas.
        """
        operandos = {}
        for simbolo in simbolos:
            indice, tipo, filas = simbolo["indice"], simbolo["tipo"], simbolo["filas"]
            if tipo == "matriz_desconocida":
                operandos[simbolo["nombre"]] = {"tipo": tipo, "filas": filas, "columnas": simbolo["columnas"]}
                continue
            if tipo == "vector_simbolico":
                operandos[simbolo["nombre"]] = {"tipo": tipo, "filas": filas}
                continue
            if tipo == "escalar":
                valor = datos[f"celda_{indice}_0_0"]
            elif tipo in ("vector", "vector_lineal"):
                valor = [datos[f"celda_{indice}_{fila}_0"] for fila in range(filas)]
            else:
                valor = [
                    [datos[f"celda_{indice}_{fila}_{columna}"] for columna in range(simbolo["columnas"])]
                    for fila in range(filas)
                ]
            operandos[simbolo["nombre"]] = {"tipo": tipo, "valor": valor}
        return operandos

    def _indice_eliminar(self, cantidad, campo="eliminar"):
        try:
            indice = int(self.data.get(campo))
        except (TypeError, ValueError):
            return False
        return 0 <= indice < cantidad

    def _contrato(self, simbolos):
        recibidos = set(self.data)
        if self.accion:
            conocidos = set(self.fields) | {"csrfmiddlewaretoken", self.accion, "nodo"}
            return all(
                nombre in conocidos or nombre.startswith(("celda_", "filas_", "columnas_"))
                for nombre in recibidos
            )
        opcionales = {"nodo", "csrfmiddlewaretoken", "metodo", "confirmacion"}
        esperados = {"cantidad", *(campo.name for campo in self.expresiones)} | opcionales
        for simbolo in simbolos:
            indice, tipo = simbolo["indice"], simbolo["tipo"]
            esperados.update((f"nombre_{indice}", f"tipo_{indice}"))
            if tipo != "escalar":
                esperados.add(f"filas_{indice}")
            if tipo in _CON_COLUMNAS:
                esperados.add(f"columnas_{indice}")
            alto, ancho = forma(tipo, simbolo["filas"], simbolo["columnas"])
            esperados.update(f"celda_{indice}_{fila}_{columna}" for fila in range(alto) for columna in range(ancho))
        return esperados - opcionales <= recibidos <= esperados

    def _estado(self, simbolos, metodo):
        lista = []
        for simbolo in simbolos:
            indice, tipo = simbolo["indice"], simbolo["tipo"]
            alto, ancho = forma(tipo, simbolo["filas"], simbolo["columnas"])
            lista.append({
                **simbolo,
                "celdas": {
                    (fila, columna): self.data.get(f"celda_{indice}_{fila}_{columna}", "")
                    for fila in range(alto) for columna in range(ancho)
                },
            })
        if self.accion == "eliminar":
            lista.pop(int(self.data.get("eliminar")))
        if self.accion == "agregar":
            lista.append({
                "nombre": nombre_libre({simbolo["nombre"] for simbolo in lista}), "tipo": "matriz", "filas": 2, "columnas": 2,
                "celdas": {(fila, columna): "" for fila in range(2) for columna in range(2)},
            })
        expresiones = [self.data.get(campo.name, "") for campo in self.expresiones]
        if self.accion == "eliminar_expresion":
            expresiones.pop(int(self.data["eliminar_expresion"]))
        if self.accion == "agregar_expresion":
            expresiones.append("")
        plano = {"cantidad": len(lista), "metodo": metodo or METODO_PREDETERMINADO}
        plano.update(zip(NOMBRES_EXPRESIONES, expresiones))
        for indice, simbolo in enumerate(lista):
            plano[f"nombre_{indice}"] = simbolo["nombre"]
            plano[f"tipo_{indice}"] = simbolo["tipo"]
            if simbolo["tipo"] != "escalar":
                plano[f"filas_{indice}"] = simbolo["filas"]
            if simbolo["tipo"] in _CON_COLUMNAS:
                plano[f"columnas_{indice}"] = simbolo["columnas"]
            for (fila, columna), texto in simbolo["celdas"].items():
                plano[f"celda_{indice}_{fila}_{columna}"] = texto
        return plano
