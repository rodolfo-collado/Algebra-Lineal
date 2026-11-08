"""Navegación con clics reales y mediciones; ejecutor opcional, fuera de unittest.

uv run --locked --with playwright==1.64.1 python -m tests.fluidez_browser --url http://127.0.0.1:8899
Con WebView2 abierto para diagnóstico: --cdp http://127.0.0.1:9333
Ver docs/rendimiento-estudio.md para condiciones y comparación de referencias.
"""

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


INSTRUMENTAR = """(() => {
    const p = window.medicion = {frames: [], tareas: [], transiciones: [], persistida: false};
    new PerformanceObserver(l => p.tareas.push(...l.getEntries().map(e =>
        ({inicio: e.startTime, ms: e.duration})))).observe({type: 'longtask', buffered: true});
    let previo;
    function frame(t) {
        if (previo !== undefined) p.frames.push({t, ms: t - previo});
        previo = t;
        requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
    addEventListener('pageshow', e => {
        p.persistida = e.persisted;
        if (e.persisted) previo = undefined;
    });
    addEventListener('transitionend', e => {
        if (e.target.matches('.escena-camara')) p.camaraFinal = performance.now();
    });
    addEventListener('animationend', e => {
        if (e.target.matches('.app-content')) p.contenidoFinal = performance.now();
    });
    addEventListener('pagereveal', e => {
        const t = {reveal: performance.now(), activa: !!e.viewTransition};
        p.transiciones.push(t);
        if (!e.viewTransition) { t.ready = t.finished = t.reveal; return; }
        e.viewTransition.ready.then(() => t.ready = performance.now(), () => t.omitida = true);
        e.viewTransition.finished.then(() => t.finished = performance.now(), () => {
            t.omitida = true;
            t.finished = performance.now();
        });
    });
})();"""


def clic(page, selector):
    punto = page.locator(selector).first.evaluate("""el => {
        const r = el.getBoundingClientRect();
        const x = r.x + r.width / 2, y = r.y + r.height / 2;
        return {x, y, alcanza: el.contains(document.elementFromPoint(x, y))};
    }""")
    page.mouse.click(punto["x"], punto["y"])
    return punto["alcanza"]


def llegada(page):
    page.wait_for_load_state("load")
    page.wait_for_function("medicion.transiciones.length && (medicion.transiciones.at(-1).ready !== undefined || medicion.transiciones.at(-1).omitida)")
    page.wait_for_timeout(50)


def medir(page, accion, ruta, nombre):
    accion()
    page.wait_for_url(lambda url: urlsplit(str(url)).path == ruta)
    llegada(page)
    # Ventana fija de un segundo desde que la vista puede pintarse, en ambas referencias.
    page.evaluate("""() => new Promise(r => {
        const t = medicion.transiciones.at(-1);
        setTimeout(r, Math.max(0, t.reveal + 1000 - performance.now()));
    })""")
    page.wait_for_function("medicion.transiciones.at(-1).finished !== undefined")
    datos = page.evaluate("""() => {
        const p = medicion, t = p.transiciones.at(-1);
        const frames = p.frames.filter(f => f.t >= t.reveal && f.t < t.reveal + 1000);
        const tareas = p.tareas.filter(f => f.inicio >= (p.persistida ? t.reveal : 0) && f.inicio < t.reveal + 1000);
        const n = performance.getEntriesByType('navigation')[0];
        return {transicion: t.finished - t.reveal,
            vistaFinal: Math.max(t.finished, p.camaraFinal || 0, p.contenidoFinal || 0) - t.reveal,
            omitida: !t.activa || !!t.omitida,
            persistida: p.persistida, ttfb: p.persistida ? null : n.responseStart,
            dom: p.persistida ? null : n.domContentLoadedEventEnd,
            intervaloMaximo: Math.max(0, ...frames.map(f => f.ms)),
            huecosRAF: frames.reduce((n,f) => n + Math.max(0, Math.round(f.ms / (1000/60))-1), 0),
            tareasLargas: tareas.length, msTareasLargas: tareas.reduce((n,f) => n+f.ms, 0),
            musica: window.Musica.pedida()};
    }""")
    return {"recorrido": nombre, **datos}


def ejecutar(args):
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(args.cdp) if args.cdp else pw.chromium.launch(
            channel="msedge", headless=False, args=["--autoplay-policy=no-user-gesture-required"])
        context = browser.contexts[0] if args.cdp else browser.new_context(viewport={"width": 1280, "height": 698}, device_scale_factor=1.5)
        page = context.pages[0] if args.cdp else context.new_page()
        base = args.url or (f"{urlsplit(page.url).scheme}://{urlsplit(page.url).netloc}")
        context.add_init_script(INSTRUMENTAR)
        cdp = context.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send("Network.setCacheDisabled", {"cacheDisabled": False})
        page.goto(base)
        with page.expect_navigation(wait_until="load"):
            cdp.send("Page.reload", {"ignoreCache": True})
        errores, omisiones = [], []

        def registrar_error(error):
            if str(error) == "Transition was aborted because of invalid state. ViewTransition opt-in disabled" and not error.stack:
                omisiones.append(str(error))
            else:
                errores.append(str(error))

        page.on("pageerror", registrar_error)
        resultados = {"motor": browser.version, "webview2": bool(args.cdp), "errores": errores, "omisionesNativas": omisiones, "casos": []}
        for estilo in ("estudio", "minimalista"):
            for tema in ("light", "dark"):
                for musica in (False, True):
                    page.goto(base)
                    page.evaluate("""v => {
                        localStorage.setItem('pygebra-estilo', v.estilo);
                        localStorage.setItem('pygebra-tema', v.tema);
                        localStorage.setItem('pygebra-musica-pieza', 'cafe');
                        localStorage.setItem('pygebra-musica-volumen', '40');
                        localStorage.setItem('pygebra-sonido', 'off');
                        sessionStorage.clear();
                        if (v.musica) sessionStorage.setItem('pygebra-musica', 'on');
                    }""", {"estilo": estilo, "tema": tema, "musica": musica})
                    filas = []
                    for _ in range(args.muestras):
                        page.goto(base)
                        page.locator('.canales').scroll_into_view_if_needed()
                        page.wait_for_timeout(1100)
                        filas.append(medir(page, lambda: clic(page, 'a.canal-enlace[href="/areas/algebra-lineal/"]'), "/areas/algebra-lineal/", "inicio-area"))
                        filas.append(medir(page, lambda: clic(page, 'a.indice-item[href="/matrices/determinantes/"]'), "/matrices/determinantes/", "area-herramienta"))
                        filas.append(medir(page, lambda: clic(page, '#historial-atras'), "/areas/algebra-lineal/", "atras"))
                        filas.append(medir(page, lambda: clic(page, '#historial-adelante'), "/matrices/determinantes/", "adelante"))
                    # Un salto nuevo, seguido de un clic a los ~50 ms de estar lista la captura.
                    page.go_back()
                    llegada(page)
                    temprano = clic(page, '#opciones-toggle')
                    abierto = page.locator('#opciones').evaluate("el => el.matches(':popover-open')")
                    page.keyboard.press("Escape")
                    caso = {"estilo": estilo, "tema": tema, "musica": musica, "clicTemprano": temprano and abierto, "filas": filas}
                    resultados["casos"].append(caso)
                    print(json.dumps({k: v for k, v in caso.items() if k != "filas"}), flush=True)
                    if args.salida:
                        Path(args.salida).write_text(json.dumps(resultados, indent=2), encoding="utf-8")
                    if args.validar:
                        assert caso["clicTemprano"], "Opciones no responde durante la transición"
                        assert all(f["vistaFinal"] < 500 for f in filas), "Transición por encima del presupuesto con margen de ejecución"
                        # Encadenar saltos antes de que termine cada viaje decorativo.
                        assert clic(page, 'a.indice-item[href="/matrices/determinantes/"]')
                        page.wait_for_url("**/matrices/determinantes/")
                        llegada(page)
                        assert clic(page, '#determinant-matrix input')
                        page.keyboard.type("1/2")
                        assert page.locator('#determinant-matrix input').first.input_value() == "1/2"
                        page.wait_for_function("""() => {
                            const k = document.querySelector('.math-keyboard'), r = k.getBoundingClientRect();
                            return !k.hidden && r.height > 0 && r.bottom <= innerHeight + 1;
                        }""")
                        for selector, ruta in (("#historial-atras", "**/areas/algebra-lineal/"),
                                               ("#historial-adelante", "**/matrices/determinantes/")):
                            assert clic(page, selector)
                            page.wait_for_url(ruta)
                            llegada(page)
                        page.emulate_media(reduced_motion="reduce")
                        clic(page, '#historial-atras')
                        page.wait_for_url("**/areas/algebra-lineal/")
                        llegada(page)
                        assert page.evaluate("!document.activeViewTransition && getComputedStyle(document.querySelector('.app-content')).animationName === 'none'")
                        page.emulate_media(reduced_motion="no-preference")
        assert not errores, errores
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp")
    parser.add_argument("--url")
    parser.add_argument("--muestras", type=int, default=3)
    parser.add_argument("--salida", type=Path)
    parser.add_argument("--validar", action="store_true")
    args = parser.parse_args()
    if not (args.cdp or args.url) or args.muestras < 1:
        parser.error("Indica --url o --cdp y al menos una muestra")
    ejecutar(args)
