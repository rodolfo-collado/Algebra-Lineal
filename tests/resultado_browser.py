"""P27.6: uv run --locked python -m tests.resultado_browser; abrir :8883/__pruebas/.

Los casos renderizan POST reales de Django; sus formularios siguen enviando a
las rutas de producción. Sin dependencia de automatización ni aritmética duplicada.
"""

import re
from secrets import token_hex
from functools import lru_cache
from pathlib import Path
from wsgiref.simple_server import make_server

from tests.operandos_browser import aplicacion, ServidorConHilos
from django.test import Client
from tests.test_ecuaciones_matriciales_web import datos_ecuacion
from tests.test_matriz_inversa_web import datos_inversa
from tests.test_expresiones_matriciales_web import datos_expresion
from tests.test_vectores_web import datos_vectores
from tests.test_web import datos_matriz
from tests.test_expresiones_lineales_web import PRINCIPAL, datos as datos_lineales

CSRF_TOKEN = token_hex(16)


def matriz(n):
    return [[101 + 3 * i if i == j else (7 * i + 5 * j) % 13 + 1
             for j in range(n)] for i in range(n)]


CASOS = {
    "reduccion": ("/matrices/reduccion/", datos_matriz([[1, 1, 3], [1, -1, 1]], "gauss_jordan")),
    "axb": ("/matrices/ecuaciones/", datos_ecuacion()),
    "inversa": ("/matrices/inversa/", datos_inversa(verificar="on")),
    "operaciones": ("/matrices/operaciones/", datos_expresion("AB", (
        {"nombre": "A", "tipo": "matriz", "valor": [[1, 2], [3, 4]]},
        {"nombre": "B", "tipo": "matriz", "valor": [[2, 0], [0, 3]]}))),
    "vectores": ("/vectores/operaciones/", datos_vectores("suma", vectores=2, v1=[1, 2], v2=[3, 4])),
    "bases": ("/bases/conversion/", {"numero": "123", "base_origen": "10", "bases_destino": ["2", "16"]}),
    "romanos": ("/romanos/conversion/", {"numero": "24", "direccion": "decimal_a_romano"}),
    "inversa-4": ("/matrices/inversa/", datos_inversa([[f"{v}/7" for v in fila] for fila in matriz(4)])),
    "inversa-3": ("/matrices/inversa/", datos_inversa([[0, 1, 2], [1, 0, 3], [4, -3, 8]])),
    "inversa-6": ("/matrices/inversa/", datos_inversa(matriz(6))),
    "inversa-8": ("/matrices/inversa/", datos_inversa(matriz(8), verificar="on")),
    "inversa-10": ("/matrices/inversa/", datos_inversa([[2 if i == j else 1 for j in range(10)] for i in range(10)])),
    "reduccion-8": ("/matrices/reduccion/", datos_matriz([
        [2 if i == j else 1 for j in range(8)] + [9] for i in range(8)], "gauss_jordan")),
    "bases-largo": ("/bases/conversion/", {"numero": "123456789" * 4 + "123", "base_origen": "10", "bases_destino": ["2", "16"]}),
    "rectangular": ("/matrices/operaciones/", datos_expresion("A", (
        {"nombre": "A", "tipo": "matriz", "valor": [[f"{i + j + 1}/123456789" for j in range(10)] for i in range(2)]},))),
}

# P28.5: valores calculados por Django, incluyendo resultados con varios paneles.
A = {"nombre": "A", "tipo": "matriz", "valor": [["1/3", -2, 0], [5, "7/2", -1]]}
B = {"nombre": "B", "tipo": "matriz", "valor": [[0, 1, 2], [-5, "1/2", 3]]}
for nombre, expresion in (("suma", "A+B"), ("resta", "A-B"), ("expresion", "2A-B"), ("igualdad", "A=B")):
    CASOS["p28-" + nombre] = ("/matrices/operaciones/", datos_expresion(expresion, (A, B)))
CASOS.update({
    "p28-producto": ("/matrices/operaciones/", datos_expresion("AB", (A,
        {"nombre": "B", "tipo": "matriz", "valor": [[1, 0], [0, 1], [0, 1]]}))),
    "p28-determinacion": ("/matrices/operaciones/", datos_lineales("Ax=b", PRINCIPAL)),
    "p28-inversa": ("/matrices/inversa/", datos_inversa([[3, 0], [0, -2]], verificar="on")),
    "p28-operaciones-10": ("/matrices/operaciones/", datos_expresion("A", (
        {"nombre": "A", "tipo": "matriz", "valor": matriz(10)},))),
    "p28-reduccion-12": ("/matrices/reduccion/", datos_matriz([
        [int(i == j) for j in range(9)] + ["1/3" if i < 9 else 0] for i in range(12)], "gauss_jordan")),
    "p28-reduccion-13": ("/matrices/reduccion/", datos_matriz([
        [int(i == j) for j in range(12)] + ["-2/3"] for i in range(9)], "gauss_jordan")),
})
for metodo in ("gauss", "gauss_jordan", "comparar"):
    CASOS["p28-" + metodo] = ("/matrices/reduccion/", datos_matriz([[1, 1, "1/3"], [0, 1, "-2/3"]], metodo))
for funcion in ("inversa_inversa", "traspuesta", "producto", "vector"):
    datos = datos_inversa([[3, 0], [0, -2]], funcion_adicional=funcion)
    if funcion == "producto":
        datos |= {f"celda_B_{i}_{j}": str(int(i == j)) for i in range(2) for j in range(2)}
    if funcion == "vector":
        datos |= {"celda_b_0_0": "1", "celda_b_1_0": "2"}
    CASOS["p28-inversa-" + funcion] = ("/matrices/inversa/", datos)


@lru_cache(maxsize=None)
def caso(nombre, sin_js=False):
    ruta, datos = CASOS[nombre]
    client = Client()
    # Los casos comparten origen/cookie aunque se revisen en varias pestañas.
    client.cookies["csrftoken"] = CSRF_TOKEN
    respuesta = client.post(ruta, datos)
    html = respuesta.content.decode()
    if 'data-confirmacion' in html:
        firma = re.search(r'name="confirmacion" value="([^"]+)"', html)
        if firma:
            respuesta = client.post(ruta, datos | {"confirmacion": firma[1]})
            html = respuesta.content.decode()
    assert 'data-resultado="vigente"' in html, nombre
    if sin_js:
        html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.S)
    return html.encode(), client.cookies.output(header="").strip()


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    cookie = None
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<title>PyGebra: resultado P27.6</title><h1>Resultado P27.6</h1>'
                     '<ol id="resultados"></ol><p id="total">Ejecutando…</p>'
                     '<script src="/__pruebas/pruebas.js"></script></html>').encode()
        tipo = "text/html"
    elif ruta == "/__pruebas/pruebas.js":
        contenido = Path(__file__).with_suffix(".js").read_bytes()
        tipo = "text/javascript"
    elif ruta.startswith("/__pruebas/casos/"):
        contenido, cookie = caso(ruta.rstrip("/").split("/")[-1], environ.get("QUERY_STRING") == "sin-js")
        tipo = "text/html"
    elif ruta in ("/__pruebas/portapapeles/", "/__pruebas/visual/"):
        # Reutiliza el receptor TSV y los viewports de P28.2/P28.4.
        from tests.entrada_edicion_browser import pruebas as entrada_pruebas
        return entrada_pruebas(environ, start_response)
    else:
        return aplicacion(environ, start_response)
    headers = [("Content-Type", tipo + "; charset=utf-8"), ("Cache-Control", "no-store")]
    if cookie:
        headers.append(("Set-Cookie", cookie))
    start_response("200 OK", headers)
    return [contenido]


if __name__ == "__main__":
    print("P27.6: http://127.0.0.1:8883/__pruebas/", flush=True)
    make_server("127.0.0.1", 8883, pruebas, server_class=ServidorConHilos).serve_forever()
