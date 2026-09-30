"""Benchmark reproducible del presupuesto computacional. Manual: CI no lo ejecuta.

Mide Gauss, Gauss-Jordan y el producto de matrices con entradas deterministas
y compara los pasos reales con la cota estimada. Los tiempos dependen del
equipo: sirven para comparar tamaños y valores entre sí y para recalibrar las
referencias de backend/presupuesto_computacional.py, no como promesa.

    uv run python -m scripts.benchmark_presupuesto
    uv run python -m scripts.benchmark_presupuesto --tamanos 14 16 20 --digitos 30
    uv run python -m scripts.benchmark_presupuesto --web
"""

import argparse
import os
import random
import statistics
import time
from fractions import Fraction

from backend.gauss import aplicar_gauss
from backend.gauss_jordan import aplicar_gauss_jordan
from backend.matrices import multiplicar_matrices, resolver_operacion_matrices
from backend.presupuesto_computacional import (
    estimar_gauss,
    estimar_gauss_jordan,
    estimar_producto,
    perfil_numerico,
)
from backend.presupuesto_sistemas import dimensiones_admitidas
from frontend.web.calculadora.servicios import adaptar_pasos

TAMANOS = (2, 4, 6, 8, 10, 12)
DIGITOS = 10
ANCHOS = (30, 12, 10, 12, 7, 7, 8, 10)


def matriz(filas, columnas, digitos, semilla=42):
    """Densa y siempre la misma. Sin dígitos: enteros entre −5 y 5 con 30 en la
    diagonal, como las mediciones históricas; con dígitos: fracciones cuyo
    numerador y denominador tienen esa cantidad de cifras."""
    rng = random.Random(semilla)
    if not digitos:
        return [[rng.randint(-5, 5) + (30 if i == j else 0) for j in range(columnas)] for i in range(filas)]
    minimo, maximo = 10 ** (digitos - 1), 10 ** digitos
    return [
        [Fraction(rng.randrange(minimo, maximo) * rng.choice((1, -1)), rng.randrange(minimo, maximo)) for _ in range(columnas)]
        for _ in range(filas)
    ]


def numero(valor, decimales):
    return f"{valor:.{decimales}f}".replace(".", ",")


def fila(*columnas):
    print("".join(
        str(texto).rjust(ancho) if i else str(texto).ljust(ancho)
        for i, (texto, ancho) in enumerate(zip(columnas, ANCHOS))
    ))


def medir(funcion, repeticiones, *identificacion):
    """(mediana en segundos, último resultado), o None si la operación no termina."""
    tiempos = []
    try:
        for _ in range(repeticiones):
            inicio = time.perf_counter()
            resultado = funcion()
            tiempos.append(time.perf_counter() - inicio)
    except ValueError as error:
        # También en la aplicación: Python no pasa a texto enteros de más de 4300 cifras.
        fila(*identificacion, f"  no terminó: {error}"[:70])
        return None
    return statistics.median(tiempos), resultado


def motores(tamanos, digitos, repeticiones):
    """Cálculo y registro de pasos; µs/unidad = mediana / cálculo estimado."""
    fila("Motor", "dimensiones", "valores", "mediana ms", "pasos", "cota", "factor", "µs/unidad")
    for cifras in (0, digitos):
        valores = f"{cifras} cifras" if cifras else "enteros"
        for n in tamanos:
            sistema = matriz(n, n + 1, cifras)
            perfil = perfil_numerico(sistema)
            for nombre, motor, estimar in (
                ("Gauss", aplicar_gauss, estimar_gauss),
                ("Gauss-Jordan", aplicar_gauss_jordan, estimar_gauss_jordan),
            ):
                medida = medir(lambda: motor(sistema, n), repeticiones, nombre, f"{n}×{n + 1}", valores)
                if medida:
                    segundos, (_, pasos, _) = medida
                    estimacion = estimar(n, n + 1, columnas_pivote=n, perfil=perfil)
                    fila(nombre, f"{n}×{n + 1}", valores, numero(segundos * 1e3, 3), len(pasos), estimacion.pasos,
                         numero(estimacion.factor_numerico, 2), numero(segundos / estimacion.calculo * 1e6, 2))
            a, b = matriz(n, n, cifras, 1), matriz(n, n, cifras, 2)
            medida = medir(lambda: multiplicar_matrices(a, b), repeticiones, "Producto AB", f"{n}×{n}·{n}×{n}", valores)
            if medida:
                estimacion = estimar_producto(n, n, n, perfil=perfil_numerico(a, b))
                fila("Producto AB", f"{n}×{n}·{n}×{n}", valores, numero(medida[0] * 1e3, 3), "", estimacion.pasos,
                     numero(estimacion.factor_numerico, 2), numero(medida[0] / estimacion.calculo * 1e6, 2))


def procedimientos(tamanos, digitos, repeticiones):
    """Conservar y presentar pasos; µs/celda = mediana / procedimiento estimado."""
    fila("Procedimiento", "dimensiones", "valores", "mediana ms", "", "celdas", "", "µs/celda")
    for cifras in (0, digitos):
        valores = f"{cifras} cifras" if cifras else "enteros"
        for n in tamanos:
            sistema = matriz(n, n + 1, cifras)
            estimacion = estimar_gauss_jordan(n, n + 1, columnas_pivote=n, perfil=perfil_numerico(sistema))
            nombre = "Pasos de Gauss-Jordan a texto"
            motor = medir(lambda: aplicar_gauss_jordan(sistema, n), 1, nombre, f"{n}×{n + 1}", valores)
            medida = motor and medir(lambda: adaptar_pasos(motor[1][1]), repeticiones, nombre, f"{n}×{n + 1}", valores)
            if medida:
                fila(nombre, f"{n}×{n + 1}", valores, numero(medida[0] * 1e3, 3), "",
                     round(estimacion.procedimiento), "", numero(medida[0] / estimacion.procedimiento * 1e6, 2))
            a, b = matriz(n, n, cifras, 1), matriz(n, n, cifras, 2)
            estimacion = estimar_producto(n, n, n, perfil=perfil_numerico(a, b))
            nombre = "Producto AB con evidencia"
            medida = medir(lambda: resolver_operacion_matrices("producto", a, b), repeticiones, nombre, f"{n}×{n}·{n}×{n}", valores)
            if medida:
                fila(nombre, f"{n}×{n}·{n}×{n}", valores, numero(medida[0] * 1e3, 3), "",
                     round(estimacion.procedimiento), "", numero(medida[0] / estimacion.procedimiento * 1e6, 2))


def web(tamanos, digitos, repeticiones):
    """POST completo de «Comparar ambos» en Resolver un sistema: motor, adaptación y HTML."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
    import django

    django.setup()
    from django.test import Client

    cliente = Client()
    fila("POST /sistemas/ (comparar)", "dimensiones", "valores", "mediana ms", "", "celdas", "HTML KiB", "µs/celda")
    for cifras in (0, digitos):
        valores = f"{cifras} cifras" if cifras else "enteros"
        for n in tamanos:
            if not dimensiones_admitidas(n, n):
                fila("", f"{n}×{n + 1}", valores, "  fuera del presupuesto de entrada")
                continue
            sistema = matriz(n, n + 1, cifras)
            datos = {"tipo_entrada": "matriz", "metodo": "comparar", "ecuaciones": n, "variables": n}
            datos.update({f"matriz_{i}_{j}": str(valor) for i, fila_sistema in enumerate(sistema) for j, valor in enumerate(fila_sistema)})
            segundos, respuesta = medir(lambda: cliente.post("/sistemas/", datos), repeticiones)
            if b'id="resultado"' not in respuesta.content:
                # La vista convierte los errores en mensajes: un tiempo sin resultado no sirve.
                fila("", f"{n}×{n + 1}", valores, "  sin resultado: la página muestra un error")
                continue
            perfil = perfil_numerico(sistema)
            celdas = sum(
                estimar(n, n + 1, columnas_pivote=n, perfil=perfil).procedimiento
                for estimar in (estimar_gauss, estimar_gauss_jordan)
            )
            fila("", f"{n}×{n + 1}", valores, numero(segundos * 1e3, 1), "", round(celdas),
                 numero(len(respuesta.content) / 1024, 0), numero(segundos / celdas * 1e6, 2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tamanos", type=int, nargs="+", default=TAMANOS, help="n de los sistemas n×(n+1) y de los productos n×n·n×n")
    parser.add_argument("--digitos", type=int, default=DIGITOS, help="cifras del numerador y del denominador en la segunda serie")
    parser.add_argument("--repeticiones", type=int, default=3)
    parser.add_argument("--web", action="store_true", help="mide además el POST completo de Resolver un sistema")
    args = parser.parse_args()
    if min(args.tamanos) < 1 or args.digitos < 1 or args.repeticiones < 1:
        parser.error("tamaños, cifras y repeticiones deben ser positivos")

    motores(args.tamanos, args.digitos, args.repeticiones)
    print()
    procedimientos(args.tamanos, args.digitos, args.repeticiones)
    if args.web:
        print()
        web(args.tamanos, args.digitos, args.repeticiones)


if __name__ == "__main__":
    main()
