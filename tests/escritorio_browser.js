/* P27.7: historial de escritorio, restauración (pageshow), Menú, preferencias y errores. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const todos = (w, s) => [...w.document.querySelectorAll(s)];
    const igual = (a, b, contexto = "") => {
        if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${contexto} ${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    };
    // Con la pestaña oculta requestAnimationFrame no corre: basta un temporizador.
    const turno = w => new Promise(resolve => w.document.hidden ? setTimeout(resolve, 60)
        : w.requestAnimationFrame(() => w.requestAnimationFrame(resolve)));
    const espera = ms => new Promise(resolve => setTimeout(resolve, ms));
    // Resuelve con la ventana del documento siguiente tras una acción que navega.
    const navegar = (frame, accion) => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("La acción no navegó")), 15000);
        frame.addEventListener("load", async () => {
            clearTimeout(timer); await turno(frame.contentWindow); resolve(frame.contentWindow);
        }, { once: true });
        accion();
    });
    const sinNavegar = async (frame, accion) => {
        frame.contentWindow.__marca = true; accion(); await espera(500);
        igual(frame.contentWindow.__marca, true, "navegó");
    };
    const tecla = (w, key, opciones = {}, destino = w.document.activeElement || w.document.body) => {
        const evento = new w.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...opciones });
        destino.dispatchEvent(evento);
        return evento;
    };
    const restaurar = w => w.dispatchEvent(new w.PageTransitionEvent("pageshow", { persisted: true }));
    const archivo = async () => (await fetch("/__pruebas/preferencias")).json();
    const calcular = (frame, sistema = "x1+x2=1;x1-2x2=0") => navegar(frame, () => {
        const w = frame.contentWindow;
        q(w, '[name="sistema"]').value = sistema;
        const boton = q(w, "[data-calculo]"); boton.form.requestSubmit(boton);
    });
    const sinDesborde = w => igual(w.document.documentElement.scrollWidth <= w.document.documentElement.clientWidth, true, "desborde horizontal");

    const casos = [
        ["Escritorio: Alt+←/→ recorren GET y POST sin controles nuevos ni reenvío", "/", {}, async (w, frame) => {
            igual(w.document.documentElement.hasAttribute("data-desktop"), true);
            igual(todos(w, ".app-header button").map(b => b.id), ["navigation-toggle", "theme-toggle"]);
            w = await navegar(frame, () => { w.location.href = "/matrices/reduccion/"; });
            w = await calcular(frame);
            igual(Boolean(q(w, "#resultado")), true);
            // Reducción por filas propone «También puedes explorar» (GET con el sistema).
            const enlace = q(w, ".explore-link, .related-link"); const destino = new URL(enlace.href);
            w = await navegar(frame, () => enlace.click());
            igual(w.location.pathname + w.location.search, destino.pathname + destino.search);
            // Volver a un resultado POST lo recupera de la caché del historial, sin reenviar.
            w = await navegar(frame, () => igual(tecla(w, "ArrowLeft", { altKey: true }).defaultPrevented, true));
            igual(w.location.pathname, "/matrices/reduccion/");
            igual(Boolean(q(w, "#resultado")), true);
            igual(q(w, '[name="sistema"]').value, "x1+x2=1;x1-2x2=0");
            igual(w.performance.getEntriesByType("navigation")[0].type, "back_forward");
            w = await navegar(frame, () => tecla(w, "ArrowRight", { altKey: true }));
            igual(w.location.pathname + w.location.search, destino.pathname + destino.search);
        }],
        ["Escritorio: Alt+← desde una celda navega; flechas y Ctrl/Shift/AltGr/IME no", "/", {}, async (w, frame) => {
            w = await navegar(frame, () => { w.location.href = "/matrices/reduccion/?tipo_entrada=matriz&ecuaciones=2&variables=2"; });
            const celda = q(w, '[data-cell="matriz_0_0"]'); celda.focus(); celda.value = "";
            const derecha = tecla(w, "ArrowRight");
            igual(derecha.defaultPrevented, true); igual(w.document.activeElement.dataset.cell, "matriz_0_1");
            // Fuera de las celdas, solo Alt sin otros modificadores ni composición navega.
            for (const opciones of [{ ctrlKey: true }, { altKey: true, shiftKey: true }, { altKey: true, ctrlKey: true }, { altKey: true, isComposing: true }]) {
                await sinNavegar(frame, () => igual(tecla(w, "ArrowLeft", opciones, w.document.body).defaultPrevented, false, JSON.stringify(opciones)));
            }
            celda.focus();
            w = await navegar(frame, () => igual(tecla(w, "ArrowLeft", { altKey: true }).defaultPrevented, true));
            igual(w.location.pathname, "/");
        }],
        ["Web: Alt+←/→ y el menú contextual quedan para el navegador", "/matrices/reduccion/", { web: true }, async (w, frame) => {
            igual(w.document.documentElement.hasAttribute("data-desktop"), false);
            await sinNavegar(frame, () => {
                igual(tecla(w, "ArrowLeft", { altKey: true }).defaultPrevented, false);
                igual(tecla(w, "ArrowRight", { altKey: true }).defaultPrevented, false);
            });
            const menu = new w.MouseEvent("contextmenu", { bubbles: true, cancelable: true });
            q(w, '[name="sistema"]').dispatchEvent(menu);
            igual(menu.defaultPrevented, false);
            igual(todos(w, ".app-header button").map(b => b.id), ["navigation-toggle", "theme-toggle"]);
        }],
        ["pageshow restaurado: cajón cerrado, main usable y foco fuera del cajón", "/matrices/inversa/", {}, async w => {
            q(w, "#navigation-toggle").click(); await turno(w);
            igual(w.document.documentElement.hasAttribute("data-drawer"), true);
            igual(q(w, "#contenido").inert, true);
            igual(w.document.activeElement.closest("#navegacion-principal") !== null, true);
            restaurar(w); await turno(w);
            igual(w.document.documentElement.hasAttribute("data-drawer"), false);
            igual(q(w, "#navegacion-principal").hidden, true);
            igual(q(w, "#sidebar-backdrop").hidden, true);
            igual(q(w, "#contenido").inert, false);
            igual(q(w, "#navigation-toggle").getAttribute("aria-expanded"), "false");
            igual(w.document.activeElement, q(w, "#navigation-toggle"));
            // Escape del Menú sigue funcionando tras restaurar.
            q(w, "#navigation-toggle").click(); tecla(w, "Escape");
            igual(q(w, "#navegacion-principal").hidden, true);
        }],
        ["pageshow restaurado: tema vigente con su estado accesible", "/", {}, async w => {
            const boton = q(w, "#theme-toggle");
            w.localStorage.setItem("pygebra-tema", "dark"); restaurar(w);
            igual(w.document.documentElement.dataset.theme, "dark");
            igual([boton.getAttribute("aria-label"), boton.getAttribute("aria-pressed")], ["Cambiar a tema claro", "true"]);
            w.localStorage.setItem("pygebra-tema", "light"); restaurar(w);
            igual(w.document.documentElement.dataset.theme, "light");
            igual([boton.getAttribute("aria-label"), boton.getAttribute("aria-pressed")], ["Cambiar a tema oscuro", "false"]);
        }],
        ["pageshow restaurado: Exacto/Decimal y precisión sin recalcular, stale ni anuncios", "/matrices/reduccion/", {}, async (w, frame) => {
            w = await calcular(frame);
            const resultado = q(w, "[data-resultado]"); const aviso = q(w, "[data-numeric-notice]");
            const valor = q(w, "[data-numeric]"); const exacto = valor.textContent;
            let eventos = 0; let anuncios = 0;
            ["input", "change", "submit"].forEach(tipo => w.document.addEventListener(tipo, () => eventos++, true));
            new w.MutationObserver(() => anuncios++).observe(aviso, { childList: true, characterData: true, subtree: true });
            w.localStorage.setItem("pygebra-formato-numerico", "decimal");
            w.localStorage.setItem("pygebra-precision-decimal", "8");
            restaurar(w); await turno(w);
            igual([q(w, "[data-numeric-mode]").value, q(w, "[data-numeric-precision]").value], ["decimal", "8"]);
            igual(valor.textContent !== exacto, true, "sigue exacto");
            igual(anuncios, 1); restaurar(w); await turno(w); igual(anuncios, 1, "anuncio repetido");
            igual(resultado.dataset.resultado, "vigente"); igual(eventos, 0);
            w.localStorage.setItem("pygebra-formato-numerico", "exacto"); restaurar(w); await turno(w);
            igual(valor.textContent, exacto); igual(q(w, "[data-numeric-precision]").hidden, true);
            igual(resultado.dataset.resultado, "vigente");
        }],
        ["pageshow restaurado: espera de P27.4 y cajón se restauran juntos", "/romanos/conversion/", {}, async w => {
            const boton = q(w, "[data-calculo]"); q(w, '[name="numero"]').value = "4";
            boton.form.dispatchEvent(new w.SubmitEvent("submit", { bubbles: true, cancelable: true, submitter: boton }));
            q(w, "#navigation-toggle").click(); await turno(w);
            restaurar(w); await turno(w);
            igual(boton.hasAttribute("aria-busy"), false); igual(q(w, "#navegacion-principal").hidden, true);
        }],
        ["Menú: categorías solo durante la ejecución; nada en localStorage", "/", {}, async (w, frame) => {
            w.localStorage.setItem("algebra-lineal-menu-secciones", '["vectores"]');
            w = await navegar(frame, () => w.location.reload());
            igual(w.localStorage.getItem("algebra-lineal-menu-secciones"), null);
            igual(q(w, '[data-categoria="vectores"]').open, false);
            q(w, "#navigation-toggle").click();
            const categoria = q(w, '[data-categoria="vectores"]'); categoria.open = true; await turno(w);
            igual(JSON.parse(w.sessionStorage.getItem("algebra-lineal-menu-secciones")), ["vectores"]);
            w = await navegar(frame, () => w.location.reload());
            igual(q(w, '[data-categoria="vectores"]').open, true);
            igual(q(w, "#navegacion-principal").hidden, true);
            // Un arranque nuevo es una sesión nueva: categorías limpias, cajón cerrado.
            w.sessionStorage.clear();
            w = await navegar(frame, () => w.location.reload());
            igual(q(w, '[data-categoria="vectores"]').open, false);
            igual(Object.keys(w.localStorage).filter(k => k.includes("menu")), []);
        }],
        ["Escritorio: tema, formato y precisión vuelven en un arranque nuevo", "/", {}, async (w, frame) => {
            const inicial = w.document.documentElement.dataset.theme;
            const otro = inicial === "dark" ? "light" : "dark";
            q(w, "#theme-toggle").click(); await espera(400);
            igual(await archivo(), { "pygebra-tema": otro });
            w = await navegar(frame, () => { w.location.href = "/matrices/reduccion/"; });
            w = await calcular(frame);
            const modo = q(w, "[data-numeric-mode]"); modo.value = "decimal"; modo.dispatchEvent(new w.Event("change"));
            const precision = q(w, "[data-numeric-precision]"); precision.value = "8"; precision.dispatchEvent(new w.Event("change"));
            await espera(400);
            igual(await archivo(), { "pygebra-tema": otro, "pygebra-formato-numerico": "decimal", "pygebra-precision-decimal": "8" });
            // Arranque nuevo: el modo privado de WebView2 empieza sin localStorage ni sessionStorage.
            w.localStorage.clear(); w.sessionStorage.clear();
            w = await navegar(frame, () => { w.location.href = "/"; });
            igual(w.document.documentElement.dataset.theme, otro);
            igual(w.document.documentElement.getAttribute("data-pygebra-tema"), otro);
            igual(q(w, "#navegacion-principal").hidden, true);
            w = await navegar(frame, () => { w.location.href = "/matrices/reduccion/"; });
            w = await calcular(frame);
            igual([q(w, "[data-numeric-mode]").value, q(w, "[data-numeric-precision]").value], ["decimal", "8"]);
            igual(q(w, "[data-numeric-precision]").hidden, false);
        }],
        ["Web: las preferencias siguen en localStorage y no tocan el archivo", "/", { web: true }, async w => {
            q(w, "#theme-toggle").click(); await espera(400);
            igual(await archivo(), {});
            igual(["light", "dark"].includes(w.localStorage.getItem("pygebra-tema")), true);
        }],
        ...[["404", "/no-existe/", "No encontramos esta página."],
            ["400", "/__pruebas/error/400/", "No pudimos procesar esta solicitud."],
            ["403", "/__pruebas/error/403/", "No se pudo completar esta acción."],
            ["CSRF", "/__pruebas/error/csrf/", "No se pudo completar esta acción."],
            ["500", "/__pruebas/error/500/", "PyGebra encontró un problema al procesar esta página."]]
            .flatMap(([codigo, ruta, mensaje]) => [1280, 744, 390].map(ancho => [
                `Error ${codigo} propio a ${ancho} px`, ruta, { ancho, alto: ancho === 744 ? 521 : 650 }, w => {
                    igual(q(w, "h1").textContent.trim(), mensaje);
                    igual(q(w, ".app-name").textContent, "PyGebra");
                    const inicio = [...todos(w, "a")].find(a => a.textContent.trim() === "Ir al inicio");
                    igual(inicio.getAttribute("href"), "/"); inicio.focus(); igual(w.document.activeElement, inicio);
                    igual(/Traceback|Not Found|Forbidden|Server Error|CSRF|detalle interno/.test(w.document.body.textContent), false);
                    sinDesborde(w);
                    if (codigo === "404") igual(Boolean(q(w, "#navigation-toggle")), true);
                }])),
    ];

    let passed = 0;
    for (const [nombre, ruta, opciones, test] of casos) {
        localStorage.clear(); sessionStorage.clear();
        await fetch("/__pruebas/reiniciar");
        document.cookie = opciones.web ? "p277=web; path=/" : "p277=; path=/; max-age=0";
        const frame = document.createElement("iframe");
        frame.style.cssText = `width:${opciones.ancho || 1280}px;height:${opciones.alto || 650}px`;
        frame.src = ruta; const cargado = new Promise(resolve => { frame.onload = resolve; });
        document.body.append(frame); await cargado; frame.onload = null; await turno(frame.contentWindow);
        const item = document.createElement("li");
        try { await test(frame.contentWindow, frame); passed++; item.textContent = `PASS · ${nombre}`; }
        catch (error) { item.textContent = `FAIL · ${nombre}: ${error.message}`; }
        document.querySelector("#resultados").append(item); frame.remove();
    }
    document.cookie = "p277=; path=/; max-age=0";
    document.querySelector("#total").textContent = `${passed}/${casos.length} pruebas DOM correctas`;
})();
