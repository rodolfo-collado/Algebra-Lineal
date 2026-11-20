"""Diálogos de álgebra lineal y traducción de bloques pegados a campos web."""

from dataclasses import replace

from django.core.exceptions import ValidationError

from backend.operandos import nombre_matriz
from backend.presupuesto_sistemas import dimensiones_admitidas
from frontend.web.calculadora.forms import SistemaForm, VectoresForm
from frontend.web.calculadora.forms_determinantes import (
    DeterminantesForm, metodo_disponible, metodo_sugerido, opciones_expansion,
)
from frontend.web.calculadora.forms_ecuaciones import EcuacionMatricialForm
from frontend.web.calculadora.forms_expresiones import ExpresionMatricialForm, TIPOS
from frontend.web.calculadora.forms_inversa import InversaForm
from frontend.web.calculadora.opciones_matrices import DIMENSION_MAXIMA
from frontend.web.calculadora.servicios_determinantes import firmar_matriz

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


def _escribir_grid(datos, filas, clave, decimal):
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            datos[f"{clave}_{i}_{j}"] = valor.replace(",", ".") if decimal == "," else valor


def _dimensiones(filas, nombre, limite=DIMENSION_MAXIMA):
    if not filas or not filas[0] or any(len(f) != len(filas[0]) for f in filas):
        raise ErrorEntrada(nombre, "Escribe una matriz rectangular con el mismo número de celdas en cada fila.")
    alto, ancho = len(filas), len(filas[0])
    if limite is not None and max(alto, ancho) > limite:
        raise ErrorEntrada(nombre, f"La matriz admite hasta {limite} filas y {limite} columnas.")
    return alto, ancho


def _orden(datos):
    filas = _matriz(datos.get("@A", ""))
    return len(filas) if len(filas) <= DIMENSION_MAXIMA else 0


def _bloque(nombre, titulo, *, vector=False, lineal=False):
    if lineal:
        ayuda = "Una expresión por línea, por ejemplo 3x1 - 2x2."
    elif vector:
        ayuda = "Componentes separados por espacios, tabulaciones o saltos de línea."
    else:
        ayuda = "Separa las celdas con espacios o tabulaciones y las filas con Enter o ;."
    return Campo(nombre, titulo, ayuda=ayuda, multilinea=True)


def reduccion(datos):
    form = SistemaForm()
    matriz = datos.get("tipo_entrada") == "matriz"
    return (
        campo(form, "tipo_entrada"),
        _bloque("@matriz", "Matriz aumentada [A | b]") if matriz else
        campo(form, "sistema", ayuda="Separa ecuaciones con Enter o ;. Ejemplo: x1+2x2=4; 2x1+5x2=9."),
        campo(form, "metodo"),
        campo(form, "mostrar"),
    )


def vectores(datos):
    form = VectoresForm(datos, ajustar=True)
    operacion = datos.get("operacion", "suma")
    cantidad = () if operacion == "escalar" else (campo(form, "vectores"),)
    escalar = (campo(form, "escalar", ayuda="Ejemplo: -3/2."),) if operacion == "escalar" else ()
    entradas = tuple(_bloque("@" + f["nombre"], f"Componentes de {f['nombre']}", vector=True)
                     for f in form.estructura()["filas"])
    return (campo(form, "operacion"), campo(form, "dimension"), *cantidad, *escalar, *entradas)


def ecuaciones(datos):
    alto, ancho = (0, 0)
    filas = _matriz(datos.get("@A", ""))
    if filas:
        alto, ancho = (min(DIMENSION_MAXIMA, n) for n in (len(filas), len(filas[0])))
    cuadrada = alto == ancho
    form = EcuacionMatricialForm(initial={"filas": alto or 2, "columnas": ancho or 2})
    campos = [
        _bloque("@A", "Matriz A"),
        _bloque("@b", "Vector b", vector=True),
        campo(form, "metodo", omitir=() if cuadrada else ("lu", "cramer")),
    ]
    if datos.get("metodo") == "cramer":
        campo_det = campo(form, "metodo_determinante", omitir=tuple(
            clave for clave, _ in form.fields["metodo_determinante"].choices if not metodo_disponible(clave, alto)
        ))
        campos.append(campo_det)
    return tuple(campos)


def inversa(datos):
    form = InversaForm()
    campos = [_bloque("@A", "Matriz cuadrada A")]
    if _orden(datos) == 2:
        campos.append(campo(form, "metodo"))
    campos.extend((campo(form, "verificar"), campo(form, "funcion_adicional")))
    if datos.get("funcion_adicional") == "producto":
        campos.append(_bloque("@B", "Matriz B"))
    if datos.get("funcion_adicional") == "vector":
        campos.append(_bloque("@b", "Vector b", vector=True))
    return tuple(campos)


def determinantes(datos):
    orden = _orden(datos)
    campos = [_bloque("@A", "Matriz cuadrada A")]
    if orden > 1:
        form = DeterminantesForm(initial={"orden": orden})
        campos.append(campo(form, "metodo", inicial=metodo_sugerido(orden)))
        if datos.get("metodo") == "cofactores":
            campos.append(Campo("expansion", "Desarrollar por", tuple(opciones_expansion(orden)), "auto"))
    return tuple(campos)


def expresiones(datos):
    form = ExpresionMatricialForm(initial={"cantidad": 0})
    cantidad = min(form.fields["cantidad"].max_value, int(datos.get("cantidad") or 0))
    campos = [
        campo(form, "expresion", ayuda="Ejemplos: A(B+C), 2A, A^T, Ax=b."),
        replace(campo(form, "cantidad"), titulo="Cantidad de operandos"),
    ]
    for i in range(cantidad):
        tipo = datos.get(f"tipo_{i}", "matriz")
        simbolo = datos.get(f"nombre_{i}", nombre_matriz(i))
        campos.extend((
            Campo(f"nombre_{i}", f"Nombre del operando {i + 1}", inicial=nombre_matriz(i)),
            Campo(f"tipo_{i}", f"Tipo de {simbolo}", tuple(opcion for _, grupo in TIPOS for opcion in grupo), "matriz"),
        ))
        if tipo in {"matriz_desconocida", "vector_simbolico"}:
            campos.append(Campo(f"filas_{i}", f"Filas o componentes de {simbolo}", inicial="2"))
            if tipo == "matriz_desconocida":
                campos.append(Campo(f"columnas_{i}", f"Columnas de {simbolo}", inicial="2"))
        elif tipo == "escalar":
            campos.append(Campo(f"@operando_{i}", f"Valor de {simbolo}"))
        else:
            campos.append(_bloque(f"@operando_{i}", f"Valores de {simbolo}", vector=tipo == "vector",
                                  lineal=tipo == "vector_lineal"))
    campos.append(campo(form, "metodo", ayuda="Elige cómo explicar los productos."))
    return tuple(campos)


def validar_cantidad_matricial(texto):
    control = ExpresionMatricialForm.base_fields["cantidad"]
    try:
        return str(control.clean(texto))
    except ValidationError as error:
        raise ErrorEntrada("cantidad", error.messages[0]) from error


def preparar_algebra(herramienta, datos, decimal):
    salida = {k: v for k, v in datos.items() if not k.startswith("@")}
    if herramienta == "reduccion-filas":
        if datos["tipo_entrada"] == "matriz":
            matriz = _matriz(datos["@matriz"])
            m, n = _dimensiones(matriz, "@matriz", limite=None)
            if not dimensiones_admitidas(m, n - 1):
                raise ErrorEntrada("@matriz", "Incluye las columnas de coeficientes y una última columna de términos independientes.")
            salida.update(ecuaciones=m, variables=n - 1)
            _escribir_grid(salida, matriz, "matriz", decimal)
        elif decimal == ",":
            salida["sistema"] = salida["sistema"].replace(",", ".")
        salida["mostrar_definido"] = "si"
    elif herramienta == "operaciones-vectores":
        form = VectoresForm(salida)
        for fila in form.estructura()["filas"]:
            nombre = fila["nombre"]
            vector = _vector(datos["@" + nombre])
            if len(vector) != len(fila["componentes"]):
                raise ErrorEntrada("@" + nombre, f"Escribe {len(fila['componentes'])} componentes para {nombre}.")
            for componente, valor in zip(fila["componentes"], vector):
                salida[componente["campo"]] = valor.replace(",", ".") if decimal == "," else valor
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
        alto, ancho = _dimensiones(matriz, "@A")
        _escribir_grid(salida, matriz, "celda_A", decimal)
        if herramienta == "ecuaciones-matriciales":
            salida.update(filas=alto, columnas=ancho)
        else:
            if alto != ancho:
                raise ErrorEntrada("@A", "A debe ser cuadrada. Escribe tantas filas como columnas.")
            salida["orden"] = alto
        if "@b" in datos:
            vector = _vector(datos["@b"])
            if len(vector) != alto:
                raise ErrorEntrada("@b", f"Escribe {alto} componentes para el vector b.")
            _escribir_grid(salida, tuple((v,) for v in vector), "celda_b", decimal)
        if "@B" in datos:
            b = _matriz(datos["@B"])
            if _dimensiones(b, "@B") != (alto, ancho):
                raise ErrorEntrada("@B", f"B debe tener tamaño {alto}×{ancho}.")
            _escribir_grid(salida, b, "celda_B", decimal)
        if herramienta == "determinantes":
            salida["eleccion"] = firmar_matriz({k: str(v) for k, v in salida.items()})
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
    "matriz-inversa": inversa,
    "determinantes": determinantes,
    "operaciones-matrices": expresiones,
}
