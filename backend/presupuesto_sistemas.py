"""Presupuesto de entrada de Resolver un sistema (web y aplicación desktop).

El procedimiento guarda dos matrices por operación de fila y las convierte a
HTML. Por eso el límite es menor que el de las operaciones básicas de matrices:
admite un sistema cuadrado de 10 variables y rectangulares de hasta 120 celdas.
Con CSRF y las cuatro opciones de resultado, el POST usa 130 campos (de 1000).
Un literal se inspecciona como texto antes de Fraction: 100 dígitos por
componente y sin notación científica.
"""

ECUACIONES_MAXIMAS = 12
VARIABLES_MAXIMAS = 12
CELDAS_MAXIMAS = 120
LONGITUD_SISTEMA_MAXIMA = 10_000
DIGITOS_MAXIMOS = 100

MENSAJE_NUMERO_GRANDE = "El número es demasiado grande para esta herramienta."
MENSAJE_NOTACION_CIENTIFICA = (
    "Esta herramienta no admite notación científica. "
    "Escribe el número como entero, fracción o decimal."
)


def validar_dimensiones(ecuaciones, variables):
    """Rechaza dimensiones sin recorrerlas ni construir estructuras proporcionales."""
    if type(ecuaciones) is not int or not 1 <= ecuaciones <= ECUACIONES_MAXIMAS:
        raise ValueError(f"Indica entre 1 y {ECUACIONES_MAXIMAS} ecuaciones.")
    if type(variables) is not int or not 1 <= variables <= VARIABLES_MAXIMAS:
        raise ValueError(f"Indica entre 1 y {VARIABLES_MAXIMAS} variables.")
    if ecuaciones * (variables + 1) > CELDAS_MAXIMAS:
        raise ValueError(
            f"La matriz aumentada admite hasta {CELDAS_MAXIMAS} celdas "
            "(ecuaciones × (variables + 1)). Reduce las dimensiones."
        )


def dimensiones_admitidas(ecuaciones, variables):
    """Para reconstrucción y GET: una estructura inválida se ignora."""
    try:
        validar_dimensiones(ecuaciones, variables)
    except ValueError:
        return False
    return True


def validar_longitud_sistema(texto):
    if len(texto) > LONGITUD_SISTEMA_MAXIMA:
        raise ValueError(
            f"El sistema admite hasta {LONGITUD_SISTEMA_MAXIMA} caracteres."
        )


def _es_notacion_cientifica(cuerpo):
    # Un dígito antes de e/E basta. No se lee el exponente: ni int() ni 10**n.
    hubo_digito = False
    for caracter in cuerpo:
        if caracter in "eE" and hubo_digito:
            return True
        if caracter.isdigit():
            hubo_digito = True
    return False


def _exigir_digitos(parte):
    if len(parte) > DIGITOS_MAXIMOS:
        raise ValueError(MENSAJE_NUMERO_GRANDE)


def _rechazar_digitos_excesivos(cuerpo):
    if "_" in cuerpo:
        # Fraction admite separadores "_"; se cuentan solo los dígitos para aplicar el presupuesto.
        if sum(caracter.isdigit() for caracter in cuerpo) > DIGITOS_MAXIMOS:
            raise ValueError(MENSAJE_NUMERO_GRANDE)
        return

    if "/" in cuerpo:
        numerador, barra, denominador = cuerpo.partition("/")
        if barra and numerador.isdigit() and denominador.isdigit():
            _exigir_digitos(numerador)
            _exigir_digitos(denominador)
        return

    if "." in cuerpo:
        entera, punto, fraccion = cuerpo.partition(".")
        if (
            punto
            and "." not in fraccion
            and (not entera or entera.isdigit())
            and (not fraccion or fraccion.isdigit())
            and (entera or fraccion)
        ):
            _exigir_digitos(entera)
            _exigir_digitos(fraccion)
        return

    if cuerpo.isdigit():
        _exigir_digitos(cuerpo)


def validar_literal_numerico(texto):
    """Rechaza un literal caro. No llama a Fraction ni convierte el exponente."""
    if not isinstance(texto, str):
        return
    compacto = "".join(texto.split())
    if not compacto:
        return
    cuerpo = compacto[1:] if compacto[0] in "+-" else compacto
    if not cuerpo:
        return
    if _es_notacion_cientifica(cuerpo):
        raise ValueError(MENSAJE_NOTACION_CIENTIFICA)
    _rechazar_digitos_excesivos(cuerpo)
