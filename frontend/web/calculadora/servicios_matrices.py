"""Escribe procedimientos de matrices a partir de datos exactos ya calculados.

Operaciones con matrices presenta así cada paso de una expresión: suma, resta,
escalar y traspuesta entrada por entrada, y AB o Ax con las lecturas elegidas.
Resolver Ax = b y Matriz inversa reutilizan las utilidades de escritura. Aquí no
se calcula ninguna entrada: toda la matemática llega del backend.
"""

from fractions import Fraction

from backend.matrices import vector_columna
from .presentacion_numerica import formatear_exacto

from .opciones_matrices import ENTRADAS_DESPLEGADAS, METODOS, METODOS_MATRIZ_VECTOR, metodos_a_mostrar
from .servicios import formatear_matriz

SUBINDICES = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_SIGNOS = {"suma": "+", "resta": "−", "escalar": "·", "traspuesta": ""}


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


def operando(texto, valores, simbolo=True, agrupar=False):
    """Un operando de un paso: su texto, cómo se nombran sus entradas y sus valores exactos.

    Las entradas de A son aᵢⱼ; las de una subexpresión, (AB)ᵢⱼ o (A + B)ᵢⱼ. `agrupar`
    pide paréntesis al escribirla junto a otra (una suma o una resta), como en (A + B)c₁.
    """
    return {
        "texto": texto, "valores": valores, "simbolo": simbolo,
        "nombre": f"({texto})" if agrupar else texto,
        "entradas": texto.lower() if len(texto) == 1 else f"({texto})",
    }


def _tabla(valores):
    """Un vector se dibuja como columna; una matriz, tal cual."""
    columna = not isinstance(valores[0], (list, tuple))
    return formatear_matriz(vector_columna(list(valores)) if columna else valores)


def _entrada(operando_):
    return {"nombre": operando_["texto"], "matriz": _tabla(operando_["valores"])}


def _fila_por_columna(calculo, n):
    """Cada entrada como producto punto: nombre = regla = símbolos = sustitución = productos = valor."""
    vector = n["operacion"] == "matriz_vector"
    desarrollo = []
    filas = []
    for pasos_fila in calculo["pasos"]:
        celdas, lineas, resumen = [], [], []
        for paso in pasos_fila:
            i, j = paso["posicion"]
            comunes = len(paso["productos"])
            nombre = f"({n['expresion']}){subindice(i)}" if vector else f"{n['salida']}{subindice(i, j)}"
            regla = f"fila{subindice(i)}({n['izquierda']}) · " + (n["sd"] if vector else f"columna{subindice(j)}({n['derecha']})")
            simbolos = " + ".join(
                f"{n['si']}{subindice(i, k)}{n['sd']}{subindice(k) if vector else subindice(k, j)}" for k in range(1, comunes + 1)
            )
            sustitucion = " + ".join(f"{_operando(a)}·{_operando(b)}" for a, b in zip(paso["fila"], paso["columna"]))
            partes = [f"{nombre} = {regla}", simbolos, sustitucion]
            if comunes > 1:
                partes.append(" + ".join(_sumando(producto) for producto in paso["productos"]))
            partes.append(formatear_exacto(paso["resultado"]))
            celdas.append(sustitucion)
            lineas.append(" = ".join(partes))
            resumen.append(f"{nombre} = {formatear_exacto(paso['resultado'])}")
        desarrollo.append(celdas)
        filas.append({"titulo": f"Fila {pasos_fila[0]['posicion'][0]} de {n['expresion']}", "lineas": lineas, "resumen": ", ".join(resumen)})
    if len(calculo["columnas"]) == 1:
        # Con una sola columna (Ax) cada fila es una entrada: un único grupo con todas.
        filas = [{"titulo": f"Entradas de {n['expresion']}", "lineas": [linea for fila in filas for linea in fila["lineas"]],
                  "resumen": ", ".join(fila["resumen"] for fila in filas)}]
    if vector:
        descripcion = f"Cada entrada de {n['expresion']} es el producto punto de una fila de {n['izq']} con el vector {n['der']}."
        formula = (f"({n['expresion']})ᵢ = filaᵢ({n['izquierda']}) · {n['sd']} = "
                   f"{n['si']}ᵢ₁{n['sd']}₁ + {n['si']}ᵢ₂{n['sd']}₂ + … + {n['si']}ᵢₙ{n['sd']}ₙ")
    else:
        descripcion = f"Cada entrada {n['salida']}ᵢⱼ es el producto punto de la fila i de {n['izq']} con la columna j de {n['der']}."
        formula = f"{n['salida']}ᵢⱼ = filaᵢ({n['izquierda']}) · columnaⱼ({n['derecha']})"
        if n["simple"]:
            formula += f" = {n['si']}ᵢ₁{n['sd']}₁ⱼ + {n['si']}ᵢ₂{n['sd']}₂ⱼ + … + {n['si']}ᵢₙ{n['sd']}ₙⱼ"
    return {
        "clave": "fila_columna", "titulo": n["titulos"]["fila_columna"],
        "descripcion": descripcion, "formula": formula, "desarrollo": desarrollo, "grupos": filas,
    }


def _por_columnas(calculo, n):
    """Cada columna del resultado como combinación lineal de las columnas de la izquierda."""
    vector = n["operacion"] == "matriz_vector"
    columnas_izquierda = [
        {"nombre": f"{n['si']}{subindice(k)}", "matriz": _columna_texto(columna), "etiqueta": f"Columna {k} de {n['izq']}"}
        for k, columna in enumerate(calculo["columnas_a"], start=1)
    ]
    grupos = []
    for columna in calculo["columnas"]:
        j = columna["posicion"]
        nombre = n["expresion"] if vector else f"{n['izq']}{n['sd']}{subindice(j)}"
        simbolica = " + ".join(
            f"{n['sd']}{subindice(k) if vector else subindice(k, j)}{n['si']}{subindice(k)}"
            for k in range(1, len(columna["coeficientes"]) + 1)
        )
        numerica = combinacion_columnas(columna["coeficientes"], n["si"])
        terminos = []
        for k, coeficiente in enumerate(columna["coeficientes"], start=1):
            signo, factor = _coeficiente(coeficiente, k == 1)
            terminos.append({"signo": signo, "factor": factor, "matriz": columnas_izquierda[k - 1]["matriz"], "etiqueta": columnas_izquierda[k - 1]["etiqueta"]})
        grupos.append({
            "titulo": nombre if vector else f"Columna {j} de {n['expresion']}: {nombre}",
            "nombre": nombre, "resumen": f"{nombre} = {numerica}",
            "simbolica": f"{nombre} = {simbolica} = {numerica}",
            "terminos": terminos,
            "escaladas": [
                {"matriz": _columna_texto(escalada), "etiqueta": f"Columna {k} de {n['izq']} multiplicada por {formatear_exacto(coeficiente)}"}
                for k, (coeficiente, escalada) in enumerate(zip(columna["coeficientes"], columna["escaladas"]), start=1)
            ],
            "resultado": _columna_texto(columna["resultado"]),
            "etiqueta_resultado": f"Vector {n['expresion']}" if vector else f"Columna {j} de {n['expresion']}",
        })
    if vector:
        descripcion = f"{n['expresion']} es la combinación lineal de las columnas de {n['izq']} cuyos coeficientes son las componentes de {n['der']}."
        formula = f"{n['expresion']} = {n['sd']}₁{n['si']}₁ + {n['sd']}₂{n['si']}₂ + … + {n['sd']}ₙ{n['si']}ₙ"
        ensamble = ""
    else:
        prefijo = f"{n['izq']}{n['sd']}"
        descripcion = (
            f"Cada columna de {n['expresion']} es {n['izq']} por la columna correspondiente de {n['der']}, y {prefijo}ⱼ es la combinación lineal "
            f"de las columnas de {n['izq']} con los coeficientes de {n['sd']}ⱼ."
        )
        formula = f"{n['expresion']} = [{prefijo}₁ … {prefijo}ₚ]"
        if n["simple"]:
            formula = (f"{n['expresion']} = [{prefijo}₁ {prefijo}₂ … {prefijo}ₚ], con {prefijo}ⱼ = "
                       f"{n['sd']}₁ⱼ{n['si']}₁ + {n['sd']}₂ⱼ{n['si']}₂ + … + {n['sd']}ₙⱼ{n['si']}ₙ")
        ensamble = n["expresion"] + " = [" + " ".join(grupo["nombre"] for grupo in grupos) + "] ="
    return {
        "clave": "columnas", "titulo": n["titulos"]["columnas"],
        "descripcion": descripcion, "formula": formula, "columnas_a": columnas_izquierda,
        "grupos": grupos, "ensamble": ensamble, "izquierda": n["izq"],
    }


def presentar_producto(calculo, metodo, izquierda, derecha, expresion, simple=False):
    """AB o Ax de dos operandos: cada lectura reagrupa los productos que el backend ya calculó.

    No hay una segunda multiplicación: `calculo` trae los productos aᵢₖbₖⱼ una
    sola vez. `simple` marca el producto de dos símbolos que es toda la expresión
    pedida: sus entradas se llaman cᵢⱼ, como en C = AB, salvo que c nombre ya a
    un operando; en cualquier otro caso se llaman como el paso, (AB + C)ᵢⱼ.
    """
    operacion = calculo["operacion"]
    n = {
        "operacion": operacion, "expresion": expresion,
        "izquierda": izquierda["texto"], "derecha": derecha["texto"],
        "izq": izquierda["nombre"], "der": derecha["nombre"],
        "si": izquierda["entradas"], "sd": derecha["entradas"],
        "titulos": dict(METODOS_MATRIZ_VECTOR if operacion == "matriz_vector" else METODOS),
    }
    n["salida"] = "c" if simple and "c" not in (n["si"], n["sd"]) else f"({expresion})"
    n["simple"] = n["salida"] == "c"
    bloques = {"fila_columna": _fila_por_columna, "columnas": _por_columnas}
    metodos = [bloques[clave](calculo, n) for clave in metodos_a_mostrar(metodo)]
    (m, comunes), (_, p) = calculo["dimensiones_entrada"], calculo["dimensiones_b"]
    if operacion == "matriz_vector":
        forma = f"{n['izq']} ({m}×{comunes}) · {n['der']} ({comunes}) → {expresion} ({m})."
    else:
        forma = f"{n['izq']}: {m}×{comunes} · {n['der']}: {comunes}×{p} → {expresion}: {m}×{p}."
    return {
        "operacion": operacion, "expresion": expresion, "simbolo": "·", "factor": None,
        "entradas": [_entrada(izquierda), _entrada(derecha)],
        "matriz": formatear_matriz(calculo["resultado"]),
        "metodos": metodos, "comparando": len(metodos) > 1,
        "abierto": m * p <= ENTRADAS_DESPLEGADAS, "forma": forma,
    }


def presentar_por_entrada(calculo, expresion, operandos, factor=None, simple=False):
    """Suma, resta, escalar o traspuesta de un paso: la regla de cada entrada y la cadena completa.

    `operandos` son las matrices del paso; `factor`, el escalar de kA como operando
    con su valor. Cada celda del desarrollo sale de los operandos que el backend
    guardó para esa entrada.
    """
    operacion = calculo["operacion"]
    signo = _SIGNOS[operacion]
    matriz = operandos[-1]
    resultado = {
        "operacion": operacion, "expresion": expresion, "simbolo": signo,
        "factor": _operando(Fraction(factor["valores"])) if factor else None,
        "entradas": [_entrada(operando_) for operando_ in operandos],
        "matriz": formatear_matriz(calculo["resultado"]),
        "dimensiones_entrada": "×".join(map(str, calculo["dimensiones_entrada"])),
        "dimensiones_resultado": "×".join(map(str, calculo["dimensiones_resultado"])),
        "operando": matriz["nombre"], "traslados": [], "nota": "",
    }
    if operacion == "traspuesta":
        entradas = matriz["entradas"]
        notacion = matriz["texto"] if matriz["simbolo"] else f"({matriz['texto']})"
        resultado.update(
            desarrollo=[[f"{entradas}[{paso['origen'][0]}, {paso['origen'][1]}]" for paso in fila] for fila in calculo["pasos"]],
            traslados=[", ".join(fila) for fila in _tabla(matriz["valores"])],
            formula=f"({expresion})ᵢⱼ = {notacion}ⱼᵢ",
            ayuda=f"Las filas de {matriz['nombre']} pasan a ser las columnas de {expresion}.",
            nota=f"{entradas}[i, j] identifica la entrada de {matriz['nombre']} en la fila i, columna j.",
        )
        return resultado
    resultado["desarrollo"] = [
        [f" {signo} ".join(_operando(numero) for numero in paso["operandos"]) for paso in fila]
        for fila in calculo["pasos"]
    ]
    if operacion == "escalar":
        resultado["formula"] = f"({expresion})ᵢⱼ = {factor['nombre']} · {matriz['entradas']}ᵢⱼ"
        resultado["ayuda"] = f"El escalar {factor['nombre']} multiplica cada entrada de {matriz['nombre']}."
        return resultado
    izquierda, derecha = operandos
    salida = "c" if simple and "c" not in (izquierda["entradas"], derecha["entradas"]) else f"({expresion})"
    resultado["formula"] = f"{salida}ᵢⱼ = {izquierda['entradas']}ᵢⱼ {signo} {derecha['entradas']}ᵢⱼ"
    # Los textos del módulo anterior, sin cambios.
    resultado["ayuda"] = (
        "Suma las entradas en la misma posición. Todas las matrices comparten filas y columnas."
        if operacion == "suma" else
        "Resta las entradas en la misma posición y en el orden indicado. Todas las matrices comparten filas y columnas."
    )
    return resultado
