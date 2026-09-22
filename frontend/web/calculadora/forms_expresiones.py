"""Símbolos y expresión de la herramienta. El cálculo vive en el backend."""

from django import forms

from backend.expresiones_matriciales.lineal import analizar_lineal
from backend.expresiones_matriciales.parser import nombre_valido

from .forms_matrices import FormularioCeldas, campo_dimension, campo_numero
from .opciones_matrices import DIMENSION_MAXIMA, DIMENSION_MINIMA

MAX_SIMBOLOS = 8
TIPOS = (
    ("matriz", "Matriz"),
    ("vector", "Vector"),
    ("escalar", "Escalar"),
    ("matriz_desconocida", "Matriz desconocida"),
    ("vector_simbolico", "Vector simbólico"),
    ("vector_lineal", "Vector lineal"),
)
_TIPOS_VALIDOS = {clave for clave, _ in TIPOS}
_SIN_CELDAS = frozenset({"matriz_desconocida", "vector_simbolico"})
_CON_COLUMNAS = frozenset({"matriz", "matriz_desconocida"})
_COMPONENTES = frozenset({"vector", "vector_simbolico", "vector_lineal"})


def campo_lineal(etiqueta):
    return forms.CharField(
        label=etiqueta, required=False, max_length=200,
        widget=forms.TextInput(attrs={
            "class": "matrix-input matrix-input-lineal", "autocomplete": "off",
            "spellcheck": "false", "placeholder": "3x1 - 2x2",
        }),
        error_messages={"max_length": "Cada componente admite hasta 200 caracteres."},
    )


class ExpresionMatricialForm(FormularioCeldas):
    """Un símbolo por bloque. Calcular exige las celdas de esa estructura; Aplicar, agregar y eliminar no."""

    expresion = forms.CharField(
        label="Expresión", required=False, max_length=400,
        widget=forms.Textarea(attrs={
            "class": "field-input field-input-code", "rows": 2, "spellcheck": "false",
            "placeholder": "A(u + v) = Au + Av",
        }),
        error_messages={"max_length": "La expresión admite hasta 400 caracteres."},
    )
    cantidad = forms.IntegerField(
        min_value=0, max_value=MAX_SIMBOLOS, initial=1, widget=forms.HiddenInput,
        error_messages={
            "required": "Indica cuántos símbolos hay.",
            "invalid": "La cantidad de símbolos debe ser un entero.",
            "min_value": "La cantidad de símbolos no puede ser negativa.",
            "max_value": f"La interfaz admite hasta {MAX_SIMBOLOS} símbolos.",
        },
    )

    def __init__(self, *args, accion=None, **kwargs):
        self.accion = accion
        super().__init__(*args, **kwargs)
        self.nombres_lineales = []
        self.bloques = []
        for indice in range(self._cantidad()):
            self._bloque(indice)

    def _publicado(self, nombre, defecto):
        if self.is_bound:
            return self.data.get(nombre, defecto)
        return self.initial.get(nombre, defecto)

    def _cantidad(self):
        crudo = self._publicado("cantidad", 1)
        try:
            valor = int(crudo)
        except (TypeError, ValueError):
            return 0
        if not 0 <= valor <= MAX_SIMBOLOS:
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

    def _bloque(self, indice):
        tipo = self._publicado(f"tipo_{indice}", "matriz")
        if tipo not in _TIPOS_VALIDOS:
            tipo = "matriz"
        filas = self._entero(f"filas_{indice}", 2)
        columnas = self._entero(f"columnas_{indice}", 2)
        self.fields[f"nombre_{indice}"] = forms.CharField(
            label=f"Nombre del símbolo {indice + 1}", max_length=12,
            initial=self.initial.get(f"nombre_{indice}", "A" if indice == 0 else ""),
            widget=forms.TextInput(attrs={
                "class": "field-input symbol-field-name", "autocomplete": "off",
                "spellcheck": "false", "maxlength": "12", "data-campo": "nombre",
            }),
            error_messages={"required": "Indica el nombre del símbolo."},
        )
        self.fields[f"tipo_{indice}"] = forms.ChoiceField(
            label=f"Tipo del símbolo {indice + 1}", choices=TIPOS,
            initial=self.initial.get(f"tipo_{indice}", "matriz"),
            widget=forms.Select(attrs={"class": "field-input symbol-field-type", "data-campo": "tipo"}),
            error_messages={"invalid_choice": "El tipo debe ser matriz, vector o escalar, matriz desconocida, vector simbólico o vector lineal."},
        )
        bloque = {
            "indice": indice, "tipo": tipo, "filas": filas, "columnas": columnas,
            "nombre": self[f"nombre_{indice}"], "tipo_campo": self[f"tipo_{indice}"],
            "filas_campo": None, "columnas_campo": None, "celdas": [],
            "nota": self._nota(tipo, indice, filas),
            "celdas_visibles": tipo not in _SIN_CELDAS,
        }
        if tipo != "escalar":
            etiqueta = "Componentes" if tipo in _COMPONENTES else "Filas"
            self.fields[f"filas_{indice}"] = campo_dimension(etiqueta)
            self.fields[f"filas_{indice}"].initial = filas
            self.fields[f"filas_{indice}"].widget.attrs["data-campo"] = "filas"
            bloque["filas_campo"] = self[f"filas_{indice}"]
        if tipo in _CON_COLUMNAS:
            self.fields[f"columnas_{indice}"] = campo_dimension("Columnas")
            self.fields[f"columnas_{indice}"].initial = columnas
            self.fields[f"columnas_{indice}"].widget.attrs["data-campo"] = "columnas"
            bloque["columnas_campo"] = self[f"columnas_{indice}"]
        alto, ancho = self._forma(tipo, filas, columnas)
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

    @staticmethod
    def _forma(tipo, filas, columnas):
        if tipo in _SIN_CELDAS:
            return 0, 0
        if tipo == "escalar":
            return 1, 1
        if tipo in ("vector", "vector_lineal"):
            return filas, 1
        return filas, columnas

    def _etiqueta(self, tipo, indice, fila, columna):
        nombre = str(self._publicado(f"nombre_{indice}", "") or "").strip()
        if not nombre and f"nombre_{indice}" in self.fields:
            nombre = str(self.fields[f"nombre_{indice}"].initial or "").strip()
        nombre = nombre or str(indice + 1)
        if tipo == "escalar":
            return f"Valor del escalar {nombre}"
        if tipo == "vector_lineal":
            return f"Vector lineal {nombre}, componente {fila + 1}"
        if tipo == "vector":
            return f"Vector {nombre}, componente {fila + 1}"
        return f"Matriz {nombre}, fila {fila + 1}, columna {columna + 1}"

    def clean(self):
        datos = super().clean()
        self.rechazar_campos_repetidos()
        if self.errors:
            return datos
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
                self.add_error(f"nombre_{indice}", f"El símbolo {nombre} está repetido.")
            vistos.add(nombre)
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
        if self.errors:
            return datos
        if self.accion == "eliminar" and not self._indice_eliminar(len(simbolos)):
            self.add_error(None, "No se puede eliminar ese símbolo.")
            return datos
        if not self._contrato(simbolos):
            self.add_error(None, "Las celdas recibidas no coinciden con los símbolos indicados. Pulsa Aplicar para ajustar la estructura.")
            return datos
        if self.accion:
            datos["estado"] = self._estado(simbolos)
            return datos
        expresion = (datos.get("expresion") or "").strip()
        if not expresion:
            self.add_error("expresion", "Escribe una expresión.")
            return datos
        self.convertir_numeros(datos, self.nombres_celdas)
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
        if self.errors:
            return datos
        entrada = {}
        for simbolo in simbolos:
            indice, tipo = simbolo["indice"], simbolo["tipo"]
            if tipo == "matriz_desconocida":
                entrada[simbolo["nombre"]] = {"tipo": tipo, "filas": simbolo["filas"], "columnas": simbolo["columnas"]}
                continue
            if tipo == "vector_simbolico":
                entrada[simbolo["nombre"]] = {"tipo": tipo, "filas": simbolo["filas"]}
                continue
            if tipo == "escalar":
                valor = datos[f"celda_{indice}_0_0"]
            elif tipo in ("vector", "vector_lineal"):
                valor = [datos[f"celda_{indice}_{fila}_0"] for fila in range(simbolo["filas"])]
            else:
                valor = [
                    [datos[f"celda_{indice}_{fila}_{columna}"] for columna in range(simbolo["columnas"])]
                    for fila in range(simbolo["filas"])
                ]
            entrada[simbolo["nombre"]] = {"tipo": tipo, "valor": valor}
        nodo = (self.data.get("nodo") or "").strip() or None
        datos["entrada"] = {"expresion": expresion, "simbolos": entrada, "nodo": nodo}
        return datos

    def _indice_eliminar(self, cantidad):
        try:
            indice = int(self.data.get("eliminar"))
        except (TypeError, ValueError):
            return False
        return 0 <= indice < cantidad

    def _contrato(self, simbolos):
        recibidos = set(self.data)
        if self.accion:
            conocidos = set(self.fields) | {"csrfmiddlewaretoken", "ajustar", "agregar", "eliminar", "nodo"}
            return all(
                nombre in conocidos or nombre.startswith(("celda_", "filas_", "columnas_"))
                for nombre in recibidos
            )
        esperados = {"expresion", "cantidad", "csrfmiddlewaretoken", "nodo"}
        for simbolo in simbolos:
            indice, tipo = simbolo["indice"], simbolo["tipo"]
            esperados.update((f"nombre_{indice}", f"tipo_{indice}"))
            if tipo != "escalar":
                esperados.add(f"filas_{indice}")
            if tipo in _CON_COLUMNAS:
                esperados.add(f"columnas_{indice}")
            alto, ancho = self._forma(tipo, simbolo["filas"], simbolo["columnas"])
            esperados.update(f"celda_{indice}_{fila}_{columna}" for fila in range(alto) for columna in range(ancho))
        return esperados - {"nodo", "csrfmiddlewaretoken"} <= recibidos <= esperados

    def _estado(self, simbolos):
        lista = []
        for simbolo in simbolos:
            indice, tipo = simbolo["indice"], simbolo["tipo"]
            alto, ancho = self._forma(tipo, simbolo["filas"], simbolo["columnas"])
            lista.append({
                **simbolo,
                "celdas": {
                    (fila, columna): self.data.get(f"celda_{indice}_{fila}_{columna}", "")
                    for fila in range(alto) for columna in range(ancho)
                },
            })
        if self.accion == "eliminar":
            lista.pop(int(self.data.get("eliminar")))
        if self.accion == "agregar" and len(lista) < MAX_SIMBOLOS:
            usados = {simbolo["nombre"] for simbolo in lista}
            nombre = next((letra for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if letra not in usados), "S")
            lista.append({
                "nombre": nombre, "tipo": "matriz", "filas": 2, "columnas": 2,
                "celdas": {(fila, columna): "" for fila in range(2) for columna in range(2)},
            })
        plano = {"expresion": self.data.get("expresion", ""), "cantidad": len(lista)}
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
