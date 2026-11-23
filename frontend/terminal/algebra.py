"""Diálogos de álgebra lineal y traducción de bloques pegados a campos web."""

from dataclasses import replace

from django import forms
from django.template.loader import render_to_string

from backend.expresiones_matriciales.lexer import tokenizar
from backend.expresiones_matriciales.lineal import analizar_lineal
from backend.expresiones_matriciales.parser import analizar_entrada, nombre_valido
from backend.operandos import ARIDAD_VECTORES, OPERANDOS_MAXIMOS, exigir_aridad, nombre_matriz
from backend.parser_sistemas import convertir_a_numero, parsear_sistema
from backend.presupuesto_sistemas import validar_dimensiones
from backend.sistemas_iterativos import ITERACIONES_MAXIMAS
from backend.vectores import nombres_generadores
from frontend.web.calculadora.forms import SistemaForm
from frontend.web.calculadora.forms_determinantes import (
    DeterminantesForm, metodo_disponible, metodo_sugerido, opciones_expansion,
)
from frontend.web.calculadora.forms_ecuaciones import EcuacionMatricialForm
from frontend.web.calculadora.forms_expresiones import ExpresionMatricialForm, TIPOS
from frontend.web.calculadora.forms_inversa import InversaForm
from frontend.web.calculadora.forms_iterativos import SistemasIterativosForm
from frontend.web.calculadora.forms_matrices import campo_dimension
from frontend.web.calculadora.opciones_matrices import DIMENSION_MAXIMA
from frontend.web.calculadora.servicios_determinantes import firmar_matriz
from frontend.web.calculadora.servicios_vectores import presentar_combinacion

from .adaptador import ProcedimientoHTML
from .dialogos import Campo, ErrorEntrada, campo


def _filas(texto):
    filas = texto.replace(";", "\n").strip().splitlines()
    return tuple(fila.strip() for fila in filas if fila.strip())


def _celdas(texto):
    if "\t" in texto:
        return tuple(celda.strip() for celda in texto.split("\t"))
    return tuple(texto.replace("|", " ").split())


def _matriz(texto):
    return tuple(_celdas(fila) for fila in _filas(texto))


def _vector(texto):
    return tuple(c for fila in _matriz(texto) for c in fila)


def _normalizar(texto, decimal):
    return texto.replace(",", ".") if decimal == "," else texto


def _numero(texto, decimal):
    if not texto:
        raise ValueError("Falta un número.")
    convertir_a_numero(_normalizar(texto, decimal), limitar_entrada=True)


def _escribir_grid(datos, filas, clave, decimal):
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            datos[f"{clave}_{i}_{j}"] = _normalizar(valor, decimal)


def _dimensiones(filas, nombre, *, cuadrada=False, forma=None):
    if not filas or not filas[0]:
        raise ErrorEntrada(nombre, "Escribe al menos una fila con números.")
    alto, ancho = len(filas), len(filas[0])
    for indice, fila in enumerate(filas[1:], 2):
        if len(fila) != ancho:
            celdas = "celda" if len(fila) == 1 else "celdas"
            raise ErrorEntrada(nombre, f"La fila {indice} tiene {len(fila)} {celdas}. Debe tener {ancho}, como la primera fila.")
    if nombre == "@matriz":
        if ancho < 2:
            raise ErrorEntrada(nombre, "Incluye las columnas de coeficientes y una última columna de términos independientes.")
        try:
            validar_dimensiones(alto, ancho - 1)
        except ValueError as error:
            raise ErrorEntrada(nombre, str(error)) from error
    elif max(alto, ancho) > DIMENSION_MAXIMA:
        raise ErrorEntrada(nombre, f"La matriz admite hasta {DIMENSION_MAXIMA} filas y {DIMENSION_MAXIMA} columnas.")
    if cuadrada and alto != ancho:
        raise ErrorEntrada(nombre, "A debe ser cuadrada. Escribe tantas filas como columnas.")
    if forma is not None and (alto, ancho) != forma:
        raise ErrorEntrada(nombre, f"{nombre.removeprefix('@')} debe tener tamaño {forma[0]}×{forma[1]}.")
    return alto, ancho


def _orden(datos):
    filas = _matriz(datos.get("@A", ""))
    return len(filas) if len(filas) <= DIMENSION_MAXIMA else 0


def _comprobar_cantidad(vector, nombre, componentes):
    if componentes is not None and len(vector) != componentes:
        etiqueta = nombre.removeprefix("@")
        unidad = "componente" if componentes == 1 else "componentes"
        raise ErrorEntrada(nombre, f"Escribe {componentes} {unidad} para {etiqueta}. Hay {len(vector)}.")


def _validar_vector(texto, decimal, nombre, componentes, lineal):
    vector = _filas(texto) if lineal else _vector(texto)
    if len(vector) > (componentes if componentes is not None else DIMENSION_MAXIMA):
        _comprobar_cantidad(vector, nombre, componentes)
        raise ValueError(f"El vector admite hasta {DIMENSION_MAXIMA} componentes.")
    for indice, valor in enumerate(vector, 1):
        try:
            if lineal:
                analizar_lineal(_normalizar(valor, decimal))
            else:
                _numero(valor, decimal)
        except ValueError as error:
            raise ValueError(f"Componente {indice} de {nombre.removeprefix('@')}: {error}") from error
    _comprobar_cantidad(vector, nombre, componentes)
    if not vector:
        raise ValueError("Escribe al menos una componente.")


def _validar_matriz(texto, decimal, nombre, cuadrada, forma):
    filas = _matriz(texto)
    _dimensiones(filas, nombre, cuadrada=cuadrada, forma=forma)
    for i, fila in enumerate(filas, 1):
        for j, valor in enumerate(fila, 1):
            try:
                _numero(valor, decimal)
            except ValueError as error:
                raise ValueError(f"Fila {i}, columna {j}: {error}") from error


def _bloque(nombre, titulo, *, vector=False, lineal=False, componentes=None, cuadrada=False, forma=None):
    if lineal:
        ayuda = "Una expresión por línea, por ejemplo 3x1 - 2x2."
    elif vector:
        ayuda = "Componentes separados por espacios, tabulaciones o saltos de línea."
    else:
        ayuda = "Separa las celdas con espacios o tabulaciones y las filas con Enter o ;."

    def verificar(texto, decimal):
        if vector or lineal:
            _validar_vector(texto, decimal, nombre, componentes, lineal)
        else:
            _validar_matriz(texto, decimal, nombre, cuadrada, forma)

    if componentes is not None:
        ayuda = f"Dimensión: {componentes}. {ayuda}"
    return Campo(nombre, titulo, ayuda=ayuda, multilinea=True, verificar=verificar)


def reduccion(datos):
    form = SistemaForm()
    matriz = datos.get("tipo_entrada") == "matriz"
    return (
        campo(form, "tipo_entrada"),
        _bloque("@matriz", "Matriz aumentada [A | b]") if matriz else
        campo(form, "sistema", ayuda="Separa ecuaciones con Enter o ;. Ejemplo: x1+2x2=4; 2x1+5x2=9.",
              verificar=lambda texto, decimal: parsear_sistema(_normalizar(texto, decimal), limitar_entrada=True)),
        campo(form, "metodo"),
        campo(form, "mostrar"),
    )


class FormularioVectores(forms.Form):
    operacion = forms.ChoiceField(label="Operación", initial="suma", choices=(
        ("suma", "Suma"), ("resta", "Resta"), ("escalar", "Multiplicación por escalar"),
        ("combinacion", "Combinación lineal"),
    ))
    dimension = campo_dimension("Dimensión")
    vectores = forms.IntegerField(label="Número de vectores", initial=2, required=False, max_value=OPERANDOS_MAXIMOS)
    escalar = forms.CharField(label="Escalar", required=False)


def _estructura_vectores(datos):
    operacion = datos.get("operacion", "suma")
    dimension = int(datos.get("dimension") or 3)
    cantidad = 1 if operacion == "escalar" else int(datos.get("vectores") or 2)
    nombres = nombres_generadores(cantidad)
    if operacion == "combinacion":
        nombres.append("b")
    return dimension, nombres


def vectores(datos):
    form = FormularioVectores()
    operacion = datos.get("operacion", "suma")
    if operacion == "combinacion":
        form.fields["vectores"].required = True
        form.fields["vectores"].error_messages["required"] = "Indica cuántos vectores generadores hay."

    def validar_cantidad(cantidad, _decimal):
        if cantidad is not None:
            exigir_aridad(cantidad, ARIDAD_VECTORES[operacion])

    cantidad = () if operacion == "escalar" else (campo(form, "vectores", verificar=validar_cantidad),)
    escalar = (campo(form, "escalar", ayuda="Ejemplo: -3/2.", verificar=_numero),) if operacion == "escalar" else ()
    dimension, nombres = _estructura_vectores(datos)
    entradas = tuple(_bloque("@" + nombre, f"Componentes de {nombre}", vector=True, componentes=dimension)
                     for nombre in nombres)
    return (campo(form, "operacion"), campo(form, "dimension", inicial="3"), *cantidad, *escalar, *entradas)


def combinacion_vectores_maxima(entrada):
    """Conserva 50 generadores en la consola: el formulario unificado cuenta b como otro operando."""
    dimension, nombres = _estructura_vectores(entrada)
    vectores = [(nombre, [convertir_a_numero(entrada[f"{nombre}_{i}"], limitar_entrada=True)
                          for i in range(dimension)]) for nombre in nombres]
    incognitas = [f"x{i}" for i in range(1, len(nombres))]
    texto = " + ".join(f"{x} {v}" for x, v in zip(incognitas, nombres)) + " = b"
    resultado = presentar_combinacion({
        "generadores": vectores[:-1], "objetivo": vectores[-1], "incognitas": incognitas, "texto": texto,
    })
    html = render_to_string("calculadora/modules/expresiones/_combinacion.html", {"resultado": resultado})
    parser = ProcedimientoHTML()
    parser.feed(f'<section id="resultado"><h2>Combinación lineal</h2>{html}</section>')
    parser.close()
    return tuple(parser.bloques)


def ecuaciones(datos):
    alto, ancho = (0, 0)
    filas = _matriz(datos.get("@A", ""))
    if filas:
        alto, ancho = (min(DIMENSION_MAXIMA, n) for n in (len(filas), len(filas[0])))
    cuadrada = alto == ancho
    form = EcuacionMatricialForm(initial={"filas": alto or 2, "columnas": ancho or 2})
    campos = [
        _bloque("@A", "Matriz A"),
        _bloque("@b", "Vector b", vector=True, componentes=alto or None),
        campo(form, "metodo", omitir=() if cuadrada else ("lu", "cramer")),
    ]
    if datos.get("metodo") == "cramer":
        campo_det = campo(form, "metodo_determinante", omitir=tuple(
            clave for clave, _ in form.fields["metodo_determinante"].choices if not metodo_disponible(clave, alto)
        ))
        campos.append(campo_det)
    return tuple(campos)


def iterativos(datos):
    orden = _orden(datos)
    form = SistemasIterativosForm(initial={"filas": orden or 2, "columnas": orden or 2})

    def validar_inicial(texto, decimal):
        if texto:
            _validar_vector(texto, decimal, "inicial_iterativo", orden or None, False)

    def validar_tolerancia(texto, decimal):
        if texto and convertir_a_numero(_normalizar(texto, decimal), limitar_entrada=True) <= 0:
            raise ValueError("La tolerancia debe ser positiva.")

    def validar_iteraciones(texto, _decimal):
        if not texto:
            return
        try:
            if 1 <= int(texto) <= ITERACIONES_MAXIMAS:
                return
        except ValueError:
            pass
        raise ValueError(f"Escribe un entero de 1 a {ITERACIONES_MAXIMAS}.")

    return (
        _bloque("@A", "Matriz cuadrada A", cuadrada=True),
        _bloque("@b", "Vector b", vector=True, componentes=orden or None),
        campo(form, "metodo"),
        campo(form, "inicial_iterativo", ayuda="Opcional. Vacío: vector de ceros.", verificar=validar_inicial),
        campo(form, "tolerancia_iterativa", verificar=validar_tolerancia),
        campo(form, "max_iteraciones", verificar=validar_iteraciones),
    )


def inversa(datos):
    form = InversaForm()
    orden = _orden(datos)
    campos = [_bloque("@A", "Matriz cuadrada A", cuadrada=True)]
    if orden == 2:
        campos.append(campo(form, "metodo"))
    campos.extend((campo(form, "verificar"), campo(form, "funcion_adicional")))
    if datos.get("funcion_adicional") == "producto":
        campos.append(_bloque("@B", "Matriz B", forma=(orden, orden) if orden else None))
    if datos.get("funcion_adicional") == "vector":
        campos.append(_bloque("@b", "Vector b", vector=True, componentes=orden or None))
    return tuple(campos)


def determinantes(datos):
    orden = _orden(datos)
    campos = [_bloque("@A", "Matriz cuadrada A", cuadrada=True)]
    if orden > 1:
        form = DeterminantesForm(initial={"orden": orden})
        campos.append(campo(form, "metodo", inicial=metodo_sugerido(orden)))
        if datos.get("metodo") == "cofactores":
            campos.append(Campo("expansion", "Desarrollar por", tuple(opciones_expansion(orden)), "auto"))
    return tuple(campos)


def _validar_expresion(texto, _decimal):
    if not texto:
        raise ValueError("Escribe una expresión.")
    # Los operandos todavía no se han declarado; aquí solo se comprueba la sintaxis.
    nombres = {t.valor for t in tokenizar(texto) if t.tipo == "nombre"}
    analizar_entrada(texto, nombres)


def _verificar_nombre(datos, indice):
    def verificar(nombre, _decimal):
        if not nombre_valido(nombre):
            raise ValueError("Usa una letra seguida de letras o dígitos, como A, u o k.")
        if any(nombre == datos.get(f"nombre_{i}") for i in range(indice)):
            raise ValueError(f"El operando {nombre} está repetido.")
    return verificar


def _dimension_simbolica(nombre, titulo):
    control = campo_dimension(titulo)
    return Campo(nombre, titulo, inicial="2", verificar=lambda texto, _: str(control.clean(texto)))


def expresiones(datos):
    form = ExpresionMatricialForm(initial={"cantidad": 0})
    cantidad = min(form.fields["cantidad"].max_value, int(datos.get("cantidad") or 0))
    campos = [
        campo(form, "expresion", ayuda="Ejemplos: A(B+C), 2A, A^T, Ax=b.", verificar=_validar_expresion),
        replace(campo(form, "cantidad"), titulo="Cantidad de operandos"),
    ]
    for i in range(cantidad):
        tipo = datos.get(f"tipo_{i}", "matriz")
        simbolo = datos.get(f"nombre_{i}", nombre_matriz(i))
        campos.extend((
            Campo(f"nombre_{i}", f"Nombre del operando {i + 1}", inicial=nombre_matriz(i),
                  verificar=_verificar_nombre(datos, i)),
            Campo(f"tipo_{i}", f"Tipo de {simbolo}", tuple(opcion for _, grupo in TIPOS for opcion in grupo), "matriz"),
        ))
        if tipo in {"matriz_desconocida", "vector_simbolico"}:
            campos.append(_dimension_simbolica(f"filas_{i}", f"Filas o componentes de {simbolo}"))
            if tipo == "matriz_desconocida":
                campos.append(_dimension_simbolica(f"columnas_{i}", f"Columnas de {simbolo}"))
        elif tipo == "escalar":
            campos.append(Campo(f"@operando_{i}", f"Valor de {simbolo}", verificar=_numero))
        else:
            campos.append(_bloque(f"@operando_{i}", f"Valores de {simbolo}", vector=tipo == "vector",
                                  lineal=tipo == "vector_lineal"))
    campos.append(campo(form, "metodo", ayuda="Elige cómo explicar los productos."))
    return tuple(campos)


def preparar_algebra(herramienta, datos, decimal):
    salida = {k: v for k, v in datos.items() if not k.startswith("@")}
    if herramienta == "reduccion-filas":
        if datos["tipo_entrada"] == "matriz":
            matriz = _matriz(datos["@matriz"])
            m, n = _dimensiones(matriz, "@matriz")
            salida.update(ecuaciones=m, variables=n - 1)
            _escribir_grid(salida, matriz, "matriz", decimal)
        elif decimal == ",":
            salida["sistema"] = salida["sistema"].replace(",", ".")
        salida["mostrar_definido"] = "si"
    elif herramienta == "operaciones-vectores":
        dimension, nombres = _estructura_vectores(datos)
        for nombre in nombres:
            vector = _vector(datos["@" + nombre])
            _comprobar_cantidad(vector, "@" + nombre, dimension)
            for indice, valor in enumerate(vector):
                salida[f"{nombre}_{indice}"] = _normalizar(valor, decimal)
        if decimal == "," and "escalar" in salida:
            salida["escalar"] = salida["escalar"].replace(",", ".")
    elif herramienta == "operaciones-matrices":
        for i in range(int(datos["cantidad"])):
            tipo = datos[f"tipo_{i}"]
            clave = f"@operando_{i}"
            if tipo in {"matriz_desconocida", "vector_simbolico"}:
                continue
            valor = datos[clave]
            if tipo == "escalar":
                matriz = ((valor,),)
            elif tipo == "vector_lineal":
                matriz = tuple((linea,) for linea in _filas(valor))
            elif tipo == "vector":
                matriz = tuple((v,) for v in _vector(valor))
            else:
                matriz = _matriz(valor)
            alto, ancho = _dimensiones(matriz, clave)
            if tipo != "escalar":
                salida[f"filas_{i}"] = alto
            if tipo == "matriz":
                salida[f"columnas_{i}"] = ancho
            _escribir_grid(salida, matriz, f"celda_{i}", decimal)
    else:
        matriz = _matriz(datos["@A"])
        alto, ancho = _dimensiones(matriz, "@A", cuadrada=herramienta != "ecuaciones-matriciales")
        _escribir_grid(salida, matriz, "celda_A", decimal)
        if herramienta in {"ecuaciones-matriciales", "metodos-iterativos"}:
            salida.update(filas=alto, columnas=ancho)
        else:
            salida["orden"] = alto
        if "@b" in datos:
            vector = _vector(datos["@b"])
            _comprobar_cantidad(vector, "@b", alto)
            _escribir_grid(salida, tuple((v,) for v in vector), "celda_b", decimal)
        if "@B" in datos:
            b = _matriz(datos["@B"])
            _dimensiones(b, "@B", forma=(alto, ancho))
            _escribir_grid(salida, b, "celda_B", decimal)
        if herramienta == "determinantes":
            salida["eleccion"] = firmar_matriz({k: str(v) for k, v in salida.items()})
        elif herramienta == "metodos-iterativos":
            salida["inicial_iterativo"] = " ".join(_vector(_normalizar(datos.get("inicial_iterativo", ""), decimal)))
            salida["tolerancia_iterativa"] = _normalizar(datos.get("tolerancia_iterativa", ""), decimal)
    return salida


def campo_de_error(nombre):
    if nombre.startswith("matriz_"):
        return "@matriz"
    if nombre.startswith("celda_"):
        bloque = nombre.split("_")[1]
        return "@operando_" + bloque if bloque.isdigit() else "@" + bloque
    if (nombre.startswith("v") and nombre.split("_")[0][1:].isdigit()) or nombre.startswith("b_"):
        return "@" + nombre.split("_")[0]
    return nombre


DIALOGOS_ALGEBRA = {
    "reduccion-filas": reduccion,
    "operaciones-vectores": vectores,
    "ecuaciones-matriciales": ecuaciones,
    "metodos-iterativos": iterativos,
    "matriz-inversa": inversa,
    "determinantes": determinantes,
    "operaciones-matrices": expresiones,
}
