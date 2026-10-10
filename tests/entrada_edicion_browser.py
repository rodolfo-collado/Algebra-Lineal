"""P27.9 y P28.1/P28.2/P28.3 en DOM real: uv run --locked python -m tests.entrada_edicion_browser.

Abrir http://127.0.0.1:8889/__pruebas/. Sin dependencias nuevas.
El ClipboardEvent sintético vive solo en el runner; Ctrl+C/Ctrl+V se validan en Browser.
Con forced-colors activo, abrir /__pruebas/?forced-colors=1 para verificar colores de sistema.
"""

from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from tests.operandos_browser import ServidorConHilos, aplicacion


def pruebas(environ, start_response):
    ruta = environ["PATH_INFO"]
    if ruta == "/__pruebas/":
        contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                     '<link rel="icon" href="/static/calculadora/favicon.svg">'
                     '<title>PyGebra: entrada, selección, copia y pegado</title><h1>Entrada, selección, copia y pegado P27.9 / P28</h1>'
                     '<ol id="resultados"></ol><p id="total">Ejecutando…</p>'
                     '<script src="/__pruebas/pruebas.js"></script></html>').encode()
        tipo = "text/html"
    elif ruta == "/__pruebas/pruebas.js":
        contenido = Path(__file__).with_suffix(".js").read_bytes()
        tipo = "text/javascript"
    elif ruta == "/__pruebas/portapapeles/":
        contenido = '''<!doctype html><html lang="es"><meta charset="utf-8">
<title>PyGebra: receptor de portapapeles</title><h1>Receptor de portapapeles (solo QA)</h1>
<label for="texto">Editor de texto</label><textarea id="texto"></textarea>
<pre id="formatos"></pre><script>
document.addEventListener("paste", event => {
    document.getElementById("formatos").textContent = JSON.stringify(
        [...event.clipboardData.types].map(tipo => [tipo, event.clipboardData.getData(tipo)]));
});
</script></html>'''.encode()
        tipo = "text/html"
    elif ruta == "/__pruebas/visual/":
        ancho, alto = {"desktop": (1280, 650), "minimo": (744, 521), "movil": (320, 650)}.get(
            parse_qs(environ.get("QUERY_STRING", "")).get("tamano", ["desktop"])[0], (1280, 650))
        contenido = (f'<!doctype html><html lang="es"><meta charset="utf-8"><title>PyGebra: QA visual {ancho}×{alto}</title>'
                     f'<iframe id="prueba" title="Matriz inversa {ancho}×{alto}" width="{ancho}" height="{alto}" '
                     'style="border:0" src="/matrices/inversa/"></iframe></html>').encode()
        tipo = "text/html"
    else:
        return aplicacion(environ, start_response)
    start_response("200 OK", [("Content-Type", tipo + "; charset=utf-8"), ("Cache-Control", "no-store")])
    return [contenido]


if __name__ == "__main__":
    print("P27.9/P28: http://127.0.0.1:8889/__pruebas/", flush=True)
    make_server("127.0.0.1", 8889, pruebas, server_class=ServidorConHilos).serve_forever()
