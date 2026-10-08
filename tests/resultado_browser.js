/* P27.6: POST, eventos y geometría reales con los scripts de producción. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const assert = (ok, mensaje) => { if (!ok) throw new Error(mensaje); };
    const turno = w => new Promise(resolve => w.requestAnimationFrame(() => w.requestAnimationFrame(resolve)));
    const valor = (w, campo, value, tipo = "input") => {
        campo.value = String(value);
        campo.dispatchEvent(new w.Event(tipo, { bubbles: true }));
    };
    const cargar = (frame, url) => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(`Timeout: ${url}`)), 30000);
        frame.onload = async () => { clearTimeout(timer); await turno(frame.contentWindow); resolve(frame.contentWindow); };
        frame.src = url;
    });
    const post = frame => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 30000);
        frame.onload = async () => { clearTimeout(timer); await turno(frame.contentWindow); resolve(frame.contentWindow); };
        q(frame.contentWindow, "[data-calculo]").click();
    });
    const pagina = w => assert(w.document.documentElement.scrollWidth <= w.document.documentElement.clientWidth + 1,
        `Página desborda: ${w.document.documentElement.scrollWidth}/${w.document.documentElement.clientWidth}`);
    const casos = [];
    const entradas = {
        reduccion: '[name="matriz_0_0"]', axb: '[name="celda_A_0_0"]', inversa: '[name="celda_A_0_0"]',
        operaciones: '[name="celda_0_0_0"]', vectores: '[name="v1_0"]', bases: '[name="numero"]', romanos: '[name="numero"]',
    };
    for (const [nombre, selector] of Object.entries(entradas)) {
        casos.push([`${nombre}: vigente → entrada anterior → nuevo POST vigente`, nombre, async (w, frame) => {
            const resultado = q(w, "[data-resultado]");
            assert(resultado.dataset.resultado === "vigente", "POST inicial vigente");
            const controls = q(w, "[data-numeric-mode]");
            if (controls) { valor(w, controls, "decimal", "change"); valor(w, controls, "exacto", "change"); }
            q(w, "#procedimiento > summary").click(); q(w, "#procedimiento > summary").click();
            q(w, "#theme-toggle").click();
            assert(resultado.dataset.resultado === "vigente", "Presentación no invalida");
            const panel = q(w, ".panel-final"); const anterior = panel.textContent;
            const campo = q(w, selector); const inicial = Number(campo.value);
            valor(w, campo, inicial + 1);
            assert(!resultado.hidden && resultado.dataset.resultado === "desactualizado", "Resultado visible desactualizado");
            assert(panel.textContent === anterior && panel.getClientRects().length > 0, "Conserva el contenido");
            const aviso = q(w, ".result-notice"); let anuncios = 0;
            const observer = new w.MutationObserver(() => anuncios++);
            observer.observe(aviso, { subtree: true, childList: true, characterData: true });
            valor(w, campo, inicial + 2); await turno(w); observer.disconnect();
            assert(anuncios === 0 && w.document.querySelectorAll(".result-notice").length === 1, "Sin anuncio repetido");
            const range = w.document.createRange(); range.selectNodeContents(panel);
            w.getSelection().removeAllRanges(); w.getSelection().addRange(range);
            assert(w.getSelection().toString().trim().length > 0, "Resultado seleccionable y copiable");
            assert(!q(w, '[aria-busy="true"]'), "Editar no deja busy");
            w = await post(frame);
            assert(q(w, "[data-resultado]")?.dataset.resultado === "vigente", `Nuevo cálculo vigente: ${w.document.title}`);
            assert(q(w, ".result-notice").textContent === "", "Nuevo aviso vacío");
        }]);
    }
    for (const [ancho, alto] of [[1280, 650], [1084, 721], [744, 521], [640, 325], [390, 650]]) {
        for (const nombre of ["inversa-4", "inversa-6", "inversa-8", "inversa-10", "reduccion-8", "bases-largo", "rectangular", "axb"]) {
            casos.push([`${nombre}: geometría ${ancho}×${alto}`, nombre, async (w, frame) => {
                frame.style.width = `${ancho}px`; frame.style.height = `${alto}px`; await turno(w);
                q(w, "#procedimiento > summary").click(); await turno(w); pagina(w);
                const panel = q(w, ".panel-final").getBoundingClientRect();
                assert(panel.left >= 0 && panel.right <= w.innerWidth + 1, "Resultado dentro del viewport");
                for (const scroll of w.document.querySelectorAll(".matrix-scroll")) {
                    if (!scroll.clientWidth || scroll.closest("details:not([open])")) continue;
                    const overflow = scroll.scrollWidth > scroll.clientWidth + 1;
                    const entrada = scroll.closest("form");
                    assert(scroll.hasAttribute("tabindex") === (overflow && !entrada), "Tab solo en scroll real de salida");
                    if (overflow && !entrada) assert(scroll.getAttribute("aria-label")?.includes("desplazamiento horizontal"), "Scroll con nombre");
                    assert(scroll.querySelectorAll(".matrix-fence").length === 2, "Ambos corchetes dentro del scroll");
                    scroll.scrollLeft = scroll.scrollWidth; await turno(w);
                    const cierre = scroll.querySelector(".matrix-fence-end").getBoundingClientRect();
                    assert(cierre.right <= scroll.getBoundingClientRect().right + 1, "Cierre accesible al final");
                    const ultima = scroll.querySelector("tr td:last-child").getBoundingClientRect();
                    assert(ultima.right <= cierre.left + 1, "Última columna antes del cierre");
                    for (let padre = scroll.parentElement; padre; padre = padre.parentElement) {
                        const css = w.getComputedStyle(padre);
                        assert(!(["auto", "scroll"].includes(css.overflowX) && padre.scrollWidth > padre.clientWidth + 1), "Sin scroll horizontal anidado");
                    }
                }
                for (const par of w.document.querySelectorAll(".matrix-pair")) {
                    const items = par.querySelectorAll(".matrix-pair-item");
                    const envuelto = items[1].getBoundingClientRect().top > items[0].getBoundingClientRect().bottom;
                    assert(par.hasAttribute("data-wrapped") === envuelto, "Wrap medido y flecha coherente");
                    const transform = w.getComputedStyle(par.querySelector(".matrix-pair-arrow > span")).transform;
                    assert((transform !== "none") === envuelto, "Dirección de transición");
                    assert(w.getComputedStyle(par.querySelector(".matrix-pair-arrow")).transform === "none", "Sin giro responsive adicional");
                }
            }]);
        }
    }
    casos.push(["Resize: Tab aparece y desaparece al cambiar overflow", "inversa-8", async (w, frame) => {
        const scroll = q(w, ".panel-final .matrix-scroll");
        frame.style.width = "2500px";
        // La app limita el ancho a 1200; decimal corto permite que quepa.
        valor(w, q(w, "[data-numeric-mode]"), "decimal", "change");
        valor(w, q(w, "[data-numeric-precision]"), "2", "change"); await turno(w);
        assert(!scroll.hasAttribute("tabindex"), "Ancho grande sin parada muda");
        frame.style.width = "390px"; await turno(w);
        assert(scroll.tabIndex === 0 && scroll.scrollWidth > scroll.clientWidth, "Estrecho enfocable");
        scroll.focus(); assert(w.document.activeElement === scroll, "Scroll recibe foco");
        frame.style.width = "1280px"; await turno(w);
        assert(!scroll.hasAttribute("tabindex"), "Ancho restaurado retira Tab");
    }]);
    casos.push(["Procedimiento largo: sticky, cierre desde abajo y resultado alcanzable", "reduccion-8", async (w, frame) => {
        frame.style.width = "744px"; frame.style.height = "521px";
        const detalle = q(w, "#procedimiento"); const summary = q(w, "#procedimiento > summary");
        summary.click(); await turno(w);
        assert(detalle.getBoundingClientRect().height > 10000, "Procedimiento realmente largo");
        w.scrollTo(0, detalle.offsetTop + 6000); await turno(w);
        const rect = summary.getBoundingClientRect();
        const header = q(w, ".app-header").getBoundingClientRect();
        assert(w.getComputedStyle(summary).position === "sticky" && Math.abs(rect.top - header.bottom) <= 1, "Summary sigue bajo cabecera");
        assert(w.getComputedStyle(summary).backgroundColor !== "rgba(0, 0, 0, 0)", "Fondo sólido");
        summary.click(); await turno(w);
        const final = q(w, ".panel-final").getBoundingClientRect();
        assert(!detalle.open && final.top >= header.bottom && final.top < w.innerHeight, "Plegar acerca Resultado");
    }]);
    casos.push(["Cambios estructurales y opciones también desactualizan", "operaciones", async (w) => {
        q(w, "[data-agregar]").click(); await turno(w);
        assert(q(w, "[data-resultado]").dataset.resultado === "desactualizado", "Agregar símbolo invalida");
    }]);
    for (const [nombre, selector, value, tipo] of [
        ["reduccion", '[name="metodo"][value="gauss"]', null, "click"],
        ["reduccion", '[name="mostrar"]', null, "click"],
        ["axb", '[data-dimension="columnas"] [data-paso="1"]', null, "click"],
        ["inversa", '[name="verificar"]', null, "click"],
        ["inversa", '[data-dimension="orden"] [data-paso="1"]', null, "click"],
        ["operaciones", '[name="metodo"][value="columnas"]', null, "click"],
        ["operaciones", '[name="expresion"]', "A+B", "input"],
        ["vectores", '[data-agregar-vector]', null, "click"],
        ["vectores", '[name="operacion"][value="resta"]', null, "click"],
        ["bases", '[name="base_origen"]', "8", "change"],
        ["bases", '[name="bases_destino"][value="16"]', null, "click"],
        ["romanos", '[name="direccion"][value="romano_a_decimal"]', null, "click"],
    ]) {
        casos.push([`${nombre}: cambio relevante ${selector}`, nombre, async w => {
            const control = q(w, selector); assert(control, "Control existente");
            for (let padre = control.parentElement; padre; padre = padre.parentElement) {
                if (padre.tagName === "DETAILS") padre.open = true;
            }
            if (tipo === "click") control.click(); else valor(w, control, value, tipo);
            await turno(w);
            assert(q(w, "[data-resultado]").dataset.resultado === "desactualizado", "Opción o estructura invalida");
        }]);
    }
    casos.push(["Calcular desde stale mantiene busy y pageshow compartidos", "inversa", w => {
        valor(w, q(w, '[name="celda_A_0_0"]'), 4);
        const boton = q(w, '[data-calculo]');
        boton.form.dispatchEvent(new w.SubmitEvent('submit', {bubbles: true, cancelable: true, submitter: boton}));
        assert(boton.textContent === "Calculando…" && boton.form.getAttribute('aria-busy') === 'true', "Stale entra en busy");
        w.dispatchEvent(new w.PageTransitionEvent('pageshow', {persisted: true}));
        assert(!boton.form.hasAttribute('aria-busy') && !boton.hasAttribute('aria-busy'), "pageshow existente restaura");
    }]);
    casos.push(["Procedimiento 3×3 pequeño sin contenedores en Tab", "inversa-3", async w => {
        q(w, '#procedimiento > summary').click(); await turno(w);
        assert(!q(w, '#procedimiento .matrix-scroll[tabindex]'), "Sin overflow, sin paradas extra");
    }]);
    casos.push(["Sin JavaScript: no hay paradas mudas de matrices", "axb?sin-js", w => {
        assert(!q(w, '.matrix-scroll[tabindex], .matrix-equation[tabindex]'), "HTML sin tabindex=0");
    }]);
    casos.push(["POST inválido desde stale conserva foco P27.4", "romanos", async (w, frame) => {
        valor(w, q(w, '[name="numero"]'), 0); w = await post(frame);
        assert(!q(w, "[data-resultado]"), "Documento inválido manda");
        assert(w.document.activeElement === q(w, '[name="numero"]'), "Foco en campo inválido");
        assert(!q(w, '[aria-busy="true"]'), "Sin busy residual");
    }]);
    let fallos = 0;
    for (const [titulo, nombre, test] of casos) {
        const frame = document.createElement("iframe"); frame.title = titulo;
        frame.style.cssText = "display:block;width:1084px;height:721px;border:0";
        document.body.append(frame);
        const item = document.createElement("li");
        try {
            const w = await cargar(frame, `/__pruebas/casos/${nombre.replace('?sin-js', '/?sin-js')}`);
            await test(w, frame); item.textContent = `PASS: ${titulo}`;
        } catch (error) { fallos++; item.textContent = `FAIL: ${titulo}: ${error.message}`; }
        document.getElementById("resultados").append(item); frame.remove();
    }
    document.getElementById("total").textContent = `${casos.length - fallos}/${casos.length} correctas; ${fallos} fallos`;
})();
