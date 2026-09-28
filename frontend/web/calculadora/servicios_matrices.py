"""Adapta datos exactos a textos; toda la matemática se delega al backend."""

from fractions import Fraction

from backend.matrices import resolver_coleccion_matrices, resolver_operacion_matrices, vector_columna
from .presentacion_numerica import formatear_exacto

from .opciones_matrices import CONFIGURACION, ENTRADAS_DESPLEGADAS, es_vector, metodos_a_mostrar, configuracion_operandos
from .servicios import formatear_matriz

SUBINDICES = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def subindice(*indices):
    """c₂₃ con índices de un dígito; c₁₀,₂ cuando alguno llega a 10, para no confundirlos."""
    textos = [str(indice).translate(SUBINDICES) for indice in indices]
    return ",".join(textos) if any(indice >= 10 for indice in indices) else "".join(textos)


def _operando(numero):
    texto = formatear_exacto(numero)
    return f"({texto})" if numero < 0 or numero.denominator != 1 else texto


def _sumando(numero):
    """Dentro de una suma solo los negativos necesitan paréntesis: 6 + (-4) + 5/2."""
    texto = formatear_exacto(numero)
    return f"({texto})" if numero < 0 else texto


def _coeficiente(numero, primero):
    """(signo, factor) de un término de la combinación: 2a₁ − a₂ + (1/2)a₃ − 0a₄."""
    magnitud = formatear_exacto(abs(numero))
    if magnitud == "1":
        factor = ""
    elif numero.denominator != 1:
        factor = f"({magnitud})"
    else:
        factor = magnitud
    if primero:
        return ("−" if numero < 0 else ""), factor
    return ("−" if numero < 0 else "+"), factor


def _termino(numero, nombre, primero):
    signo, factor = _coeficiente(numero, primero)
    return f"{signo}{factor}{nombre}" if primero else f" {signo} {factor}{nombre}"


def _columna_texto(vector):
    return formatear_matriz(vector_columna(list(vector)))


def combinacion_columnas(coeficientes, nombre="a"):
    """«2a₁ − a₂ + (1/2)a₃»: combinación lineal de las columnas de A con coeficientes exactos.

    La comparten Ax por columnas (P13B) y la lectura de Ax = b como combinación
    lineal (P14): la misma escritura para la misma igualdad.
    """
    return "".join(
        _termino(Fraction(coeficiente), f"{nombre}{subindice(k)}", k == 1)
        for k, coeficiente in enumerate(coeficientes, start=1)
    )


# Nombres con los que cada operación describe el mismo producto.
def _nombre_entrada(operacion, i, j, nombre="c"):
    return f"(Ax){subindice(i)}" if operacion == "matriz_vector" else f"{nombre}{subindice(i, j)}"


def _regla_entrada(operacion, i, j, izquierda="A", derecha="B"):
    columna = "x" if operacion == "matriz_vector" else f"columna{subindice(j)}({derecha})"
    return f"fila{subindice(i)}({izquierda}) · {columna}"


def _termino_simbolico(operacion, i, k, j, izquierda="a", derecha="b"):
    factor = f"x{subindice(k)}" if operacion == "matriz_vector" else f"{derecha}{subindice(k, j)}"
    return f"{izquierda}{subindice(i, k)}{factor}"


def _nombre_columna(operacion, j, izquierda="A", derecha="b"):
    return "Ax" if operacion == "matriz_vector" else f"{izquierda}{derecha}{subindice(j)}"


def _coeficiente_simbolico(operacion, k, j, derecha="b"):
    return f"x{subindice(k)}" if operacion == "matriz_vector" else f"{derecha}{subindice(k, j)}"


def _nombres_producto(opcion):
    izquierda, derecha = opcion.get("operandos_producto", ("A", "B"))
    simbolo_izquierda = izquierda.lower() if len(izquierda) == 1 else f"({izquierda})"
    return izquierda, derecha, simbolo_izquierda, derecha.lower()


def _fila_por_columna(calculo, opcion):
    """Cada entrada como producto punto: nombre = regla = símbolos = sustitución = productos = valor."""
    operacion = calculo["operacion"]
    izquierda, derecha, simbolo_i, simbolo_d = _nombres_producto(opcion)
    salida = opcion.get("salida_simbolica", "c")
    desarrollo = []
    filas = []
    for pasos_fila in calculo["pasos"]:
        celdas, lineas, resumen = [], [], []
        for paso in pasos_fila:
            i, j = paso["posicion"]
            comunes = len(paso["productos"])
            sustitucion = " + ".join(f"{_operando(a)}·{_operando(b)}" for a, b in zip(paso["fila"], paso["columna"]))
            partes = [
                f"{_nombre_entrada(operacion, i, j, salida)} = {_regla_entrada(operacion, i, j, izquierda, derecha)}",
                " + ".join(_termino_simbolico(operacion, i, k, j, simbolo_i, simbolo_d) for k in range(1, comunes + 1)),
                sustitucion,
            ]
            if comunes > 1:
                partes.append(" + ".join(_sumando(producto) for producto in paso["productos"]))
            partes.append(formatear_exacto(paso["resultado"]))
            celdas.append(sustitucion)
            lineas.append(" = ".join(partes))
            resumen.append(f"{_nombre_entrada(operacion, i, j, salida)} = {formatear_exacto(paso['resultado'])}")
        desarrollo.append(celdas)
        filas.append({"titulo": f"Fila {pasos_fila[0]['posicion'][0]} de {opcion['expresion']}", "lineas": lineas, "resumen": ", ".join(resumen)})
    if len(calculo["columnas"]) == 1:
        # Con una sola columna (Ax) cada fila es una entrada: un único grupo con todas.
        filas = [{"titulo": f"Entradas de {opcion['expresion']}", "lineas": [linea for fila in filas for linea in fila["lineas"]],
                  "resumen": ", ".join(fila["resumen"] for fila in filas)}]
    return {
        "clave": "fila_columna", "titulo": dict(opcion["metodos"])["fila_columna"],
        "descripcion": (
            "Cada entrada de Ax es el producto punto de una fila de A con el vector x."
            if operacion == "matriz_vector" else
            f"Cada entrada {salida}ᵢⱼ es el producto punto de la fila i de {izquierda} con la columna j de {derecha}."
        ),
        "formula": opcion["formula"], "desarrollo": desarrollo, "grupos": filas,
    }


def _por_columnas(calculo, opcion):
    """Cada columna del resultado como combinación lineal de las columnas de A."""
    operacion = calculo["operacion"]
    expresion = opcion["expresion"]
    izquierda, derecha, simbolo_i, simbolo_d = _nombres_producto(opcion)
    columnas_a = [
        {"nombre": f"{simbolo_i}{subindice(k)}", "matriz": _columna_texto(columna), "etiqueta": f"Columna {k} de {izquierda}"}
        for k, columna in enumerate(calculo["columnas_a"], start=1)
    ]
    grupos = []
    for columna in calculo["columnas"]:
        j = columna["posicion"]
        nombre = _nombre_columna(operacion, j, izquierda, simbolo_d)
        simbolica = " + ".join(
            f"{_coeficiente_simbolico(operacion, k, j, simbolo_d)}{simbolo_i}{subindice(k)}" for k in range(1, len(columna["coeficientes"]) + 1)
        )
        numerica = combinacion_columnas(columna["coeficientes"], simbolo_i)
        terminos = []
        for k, coeficiente in enumerate(columna["coeficientes"], start=1):
            signo, factor = _coeficiente(coeficiente, k == 1)
            terminos.append({"signo": signo, "factor": factor, "matriz": columnas_a[k - 1]["matriz"], "etiqueta": columnas_a[k - 1]["etiqueta"]})
        grupos.append({
            "titulo": nombre if operacion == "matriz_vector" else f"Columna {j} de {expresion}: {nombre}",
            "nombre": nombre, "resumen": f"{nombre} = {numerica}",
            "simbolica": f"{nombre} = {simbolica} = {numerica}",
            "terminos": terminos,
            "escaladas": [
                {"matriz": _columna_texto(escalada), "etiqueta": f"Columna {k} de {izquierda} multiplicada por {formatear_exacto(coeficiente)}"}
                for k, (coeficiente, escalada) in enumerate(zip(columna["coeficientes"], columna["escaladas"]), start=1)
            ],
            "resultado": _columna_texto(columna["resultado"]),
            "etiqueta_resultado": f"Columna {j} de {expresion}" if operacion == "producto" else "Vector Ax",
        })
    if operacion == "matriz_vector":
        descripcion = "Ax es la combinación lineal de las columnas de A cuyos coeficientes son las componentes de x."
        formula = "Ax = x₁a₁ + x₂a₂ + … + xₙaₙ"
        ensamble = ""
    else:
        descripcion = (
            f"Cada columna de {expresion} es {izquierda} por la columna correspondiente de {derecha}, y {izquierda}{simbolo_d}ⱼ es la combinación lineal "
            f"de las columnas de {izquierda} con los coeficientes de {simbolo_d}ⱼ."
        )
        formula = "AB = [Ab₁ Ab₂ … Abₚ], con Abⱼ = b₁ⱼa₁ + b₂ⱼa₂ + … + bₙⱼaₙ"
        ensamble = "AB = [" + " ".join(grupo["nombre"] for grupo in grupos) + "] ="
        if "operandos_producto" in opcion:
            formula = f"{expresion} = [{izquierda}{simbolo_d}₁ … {izquierda}{simbolo_d}ₚ]"
            ensamble = expresion + " = [" + " ".join(grupo["nombre"] for grupo in grupos) + "] ="
    return {
        "clave": "columnas", "titulo": dict(opcion["metodos"])["columnas"],
        "descripcion": descripcion, "formula": formula, "columnas_a": columnas_a,
        "grupos": grupos, "ensamble": ensamble, "izquierda": izquierda,
    }


def _procedimiento_por_entrada(calculo, opcion, matrices):
    """Suma, resta, escalar y traspuesta: el desarrollo de cada entrada (P13A)."""
    operacion = calculo["operacion"]
    desarrollo = []
    for fila in calculo["pasos"]:
        desarrollo.append([
            (f"a[{paso['origen'][0]}, {paso['origen'][1]}]" if operacion == "traspuesta"
             else f" {opcion['simbolo']} ".join(_operando(n) for n in paso["operandos"]))
            for paso in fila
        ])
    return {
        "desarrollo": desarrollo,
        "traslados": [", ".join(fila) for fila in formatear_matriz(matrices["A"])]
                     if operacion == "traspuesta" else [],
    }


def _procedimientos_producto(calculo, opcion, metodo):
    """AB y Ax: el resultado se calculó una vez; cada método es una lectura del mismo producto."""
    bloques = {"fila_columna": _fila_por_columna, "columnas": _por_columnas}
    metodos = [bloques[clave](calculo, opcion) for clave in metodos_a_mostrar(metodo)]
    (m, n), (_, p) = calculo["dimensiones_entrada"], calculo["dimensiones_b"]
    presentacion = {
        "metodos": metodos, "comparando": len(metodos) > 1,
        "abierto": m * p <= ENTRADAS_DESPLEGADAS,
        "forma": opcion["forma_texto"].format(m=m, n=n, p=p),
    }
    if calculo["operacion"] == "matriz_vector":
        # Ax es un vector: se anuncia por componentes, aunque se dibuje como columna.
        presentacion["dimensiones_resultado"] = f"{m} componente{'' if m == 1 else 's'}"
    return presentacion


def operar_matrices(entrada):
    operacion = entrada["operacion"]
    matrices = entrada["matrices"]
    opcion = configuracion_operandos(operacion, len(matrices))
    if operacion == "matriz_vector":
        calculo = resolver_operacion_matrices(operacion, matrices["A"], vector=entrada["vector"])
    elif operacion in ("suma", "resta", "producto"):
        calculo = resolver_coleccion_matrices(operacion, list(matrices.values()))
    else:
        calculo = resolver_operacion_matrices(operacion, matrices["A"], matrices.get("B"), entrada.get("escalar"))
    resultado = {
        **opcion, "operacion": operacion,
        "entradas": [
            {"nombre": nombre, "vector": es_vector(opcion, nombre),
             "matriz": formatear_matriz(vector_columna(entrada["vector"]) if es_vector(opcion, nombre) else matrices[nombre])}
            for nombre in opcion["matrices"]
        ],
        "factor": _operando(Fraction(entrada["escalar"])) if opcion["escalar"] else None,
        "matriz": formatear_matriz(calculo["resultado"]),
        "dimensiones_entrada": "×".join(map(str, calculo["dimensiones_entrada"])),
        "dimensiones_resultado": "×".join(map(str, calculo["dimensiones_resultado"])),
        "metodo": entrada.get("metodo"), "metodos": [], "comparando": False, "desarrollo": [], "traslados": [],
    }
    if opcion["metodos"]:
        resultado.update(_procedimientos_producto(calculo, opcion, entrada["metodo"]))
        if operacion == "producto" and len(matrices) > 2:
            resultado["etapas"] = []
            nombres = list(matrices)
            for i, etapa in enumerate(calculo["etapas"], start=1):
                izquierda = "".join(nombres[:i])
                derecha = nombres[i]
                nombre_resultado = izquierda + derecha
                opcion_etapa = {
                    **CONFIGURACION["producto"], "expresion": nombre_resultado,
                    "operandos_producto": (izquierda, derecha), "salida_simbolica": f"({nombre_resultado})",
                    "formula": f"({nombre_resultado})ᵢⱼ = filaᵢ({izquierda}) · columnaⱼ({derecha})",
                }
                detalle = {
                    **opcion_etapa, "operacion": "producto",
                    "entradas": [{"nombre": izquierda, "matriz": formatear_matriz(etapa["izquierda"])},
                                 {"nombre": derecha, "matriz": formatear_matriz(etapa["derecha"])}],
                    "matriz": formatear_matriz(etapa["calculo"]["resultado"]),
                    **_procedimientos_producto(etapa["calculo"], opcion_etapa, entrada["metodo"]),
                }
                detalle["expresion"] = nombre_resultado
                resultado["etapas"].append({
                    "titulo": f"Paso {i}: {izquierda} · {derecha} = {nombre_resultado}",
                    "asignacion": f"Se usa el resultado intermedio {izquierda}." if i > 1 else "Multiplica las dos primeras matrices.",
                    "resultado": detalle, "nombre": nombre_resultado,
                })
            agrupacion = nombres[0] + nombres[1]
            for nombre in nombres[2:]:
                agrupacion = f"({agrupacion}){nombre}"
            resultado["agrupacion"] = f"{opcion['expresion']} = {agrupacion}"
            resultado["forma"] = "Multiplicación de izquierda a derecha."
    else:
        resultado.update(_procedimiento_por_entrada(calculo, opcion, matrices))
        if len(matrices) > 2:
            resultado["ayuda"] = "Todas las matrices tienen las mismas dimensiones. Se opera cada posición en el orden indicado."
            resultado["formula"] = "cᵢⱼ = " + f" {opcion['simbolo']} ".join(f"{nombre.lower()}ᵢⱼ" for nombre in matrices)
    return resultado
