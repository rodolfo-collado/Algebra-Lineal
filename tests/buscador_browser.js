/* P27.5: catálogo Django y scripts de producción; la tabla de orden viene de Python. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const todos = (w, s) => Array.from(w.document.querySelectorAll(s));
    const igual = (a, b) => {
        if (a?.nodeType || b?.nodeType) {
            if (a !== b) throw new Error(`${a?.nodeName} != ${b?.nodeName}`);
        } else if (JSON.stringify(a) !== JSON.stringify(b)) {
            throw new Error(`${JSON.stringify(a)} != ${JSON.stringify(b)}`);
        }
    };
    const turno = w => new Promise(r => w.requestAnimationFrame(() => w.requestAnimationFrame(r)));
    const valor = (w, texto, lateral = false) => {
        const input = q(w, lateral ? "#buscador-lateral" : "#buscador-inicio");
        input.value = texto;
        input.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const ids = w => todos(w, "#catalogo-inicio [data-herramienta]:not([hidden])")
        .filter(n => n.getClientRects().length).map(n => n.dataset.herramienta);
    const menu = w => q(w, "#navigation-toggle").click();
    // El universo es el catálogo publicado por Django, no un número fijo de herramientas.
    const universo = w => JSON.parse(q(w, "#datos-buscador").textContent).herramientas.length;
    const escape = w => q(w, "#buscador-lateral").dispatchEvent(new w.KeyboardEvent(
        "keydown", { key: "Escape", bubbles: true, cancelable: true }));
    const casos = [
        ["GET tiene todo el universo, solo Gauss visible y un recuento estático", "/?q=gauss", w => {
            igual(todos(w, "#catalogo-inicio [data-herramienta]").length, universo(w));
            igual(ids(w), ["reduccion-filas"]);
            igual(q(w, "[data-busqueda-servidor]").hidden, false);
            todos(w, ".search-status").forEach(n => igual(n.textContent, ""));
            todos(w, "form[data-buscador]").forEach(n => igual(n.querySelectorAll('[aria-live="polite"]').length, 1));
        }],
        ["gauss → inversa → vectores → límites no envía GET ni duplica filas", "/?q=gauss", w => {
            const documento = w.document;
            for (const [texto, esperado] of [["inversa", ["matriz-inversa"]],
                ["vectores", ["operaciones-vectores", "operaciones-matrices"]], ["límites", ["limites-funciones"]]]) {
                valor(w, texto); igual(ids(w), esperado);
                igual(w.document, documento); igual(w.location.search, "?q=gauss");
                igual(q(w, "[data-busqueda-servidor]").hidden, true);
                igual(todos(w, "#catalogo-inicio [data-herramienta]").length, universo(w));
            }
            igual(q(w, '#catalogo-inicio [data-herramienta="limites-funciones"] .badge').textContent, "Próximamente");
        }],
        ["Editar y volver al GET restaura heading y vacía live", "/?q=gauss", w => {
            valor(w, "inversa"); igual(q(w, "#buscador-inicio-estado").textContent.includes("inversa"), true);
            valor(w, "gauss"); igual(ids(w), ["reduccion-filas"]);
            igual(q(w, "[data-busqueda-servidor]").hidden, false);
            igual(q(w, "#buscador-inicio-estado").textContent, "");
            valor(w, " gauss"); igual(q(w, "[data-busqueda-servidor]").hidden, true);
        }],
        ["Limpiar GET y volver a buscar no limita el universo", "/?q=gauss", w => {
            valor(w, ""); igual(ids(w).length, universo(w));
            valor(w, "invertir matriz"); igual(ids(w), ["matriz-inversa"]);
        }],
        ["GET vacío sin heading huérfano tiene sugerencias funcionales", "/?q=zzz", async (w, frame) => {
            igual(q(w, "#resultados-title"), null); igual(ids(w), []);
            const link = q(w, '#resultados-busqueda [data-busqueda-sugerencias] a');
            igual(link.getClientRects().length > 0, true);
            const carga = new Promise(r => { frame.onload = () => r(frame.contentWindow); });
            link.click(); w = await carga; await turno(w);
            igual(w.location.search, "?q=gauss"); igual(ids(w), ["reduccion-filas"]);
        }],
        ["Live vacío oculta heading, anuncia una vez y ofrece enlaces", "/?q=gauss", w => {
            valor(w, "zzz"); igual(ids(w), []);
            igual(q(w, "[data-busqueda-servidor]").hidden, true);
            igual(q(w, "#buscador-inicio-estado").textContent, "Sin coincidencias para «zzz».");
            igual(q(w, "#resultados-busqueda [data-busqueda-sugerencias]").hidden, false);
            valor(w, "calcular la"); igual(ids(w), []);
        }],
        ["GET sin coincidencias también permite buscar y restaurar el vacío", "/?q=zzz", w => {
            valor(w, "inversa"); igual(ids(w), ["matriz-inversa"]);
            valor(w, "zzz"); igual(ids(w), []);
            igual(q(w, "#buscador-inicio-estado").textContent, "");
            igual(q(w, "[data-busqueda-servidor]").hidden, false);
            igual(q(w, "#resultados-busqueda [data-busqueda-sugerencias]").hidden, false);
        }],
        ["GET con búsqueda enfoca resultados con contorno visible", "/?q=inversa", w => {
            const destino = q(w, "#resultados-busqueda");
            igual(w.document.activeElement, destino);
            igual(w.getComputedStyle(destino).outlineStyle, "solid");
            // El escalado de pantalla puede resolver 3px como 2.66667px: importa que el contorno exista.
            igual(parseFloat(w.getComputedStyle(destino).outlineWidth) > 0, true);
        }],
        ["GET normal conserva foco; live no provoca salto de foco", "/", w => {
            igual(w.document.activeElement, w.document.body);
            const input = q(w, "#buscador-inicio"); input.focus();
            valor(w, "inversa"); igual(w.document.activeElement, input);
        }],
        ["Inicio conserva mismas filas y canales al buscar y limpiar", "/", w => {
            const filas = todos(w, "#catalogo-inicio [data-herramienta]");
            valor(w, "límites"); igual(ids(w), ["limites-funciones"]);
            igual(todos(w, "#catalogo-inicio .canal").every(c => c.hidden), true);
            valor(w, ""); igual(ids(w), []);
            igual(todos(w, "#catalogo-inicio .canal").some(c => c.hidden), false);
            igual(q(w, "#calculo").classList.contains("es-pronto"), true);
            todos(w, "#catalogo-inicio [data-herramienta]").forEach((n, i) => {
                igual(n, filas[i]); igual(n.closest(".canal-herramientas").hidden, true);
            });
        }],
        ["Menú: Cálculo próximo, límites abre área y categoría", "/", w => {
            menu(w); valor(w, "límites", true);
            const area = q(w, "#nav-area-calculo").parentElement;
            igual(area.hidden, false); igual(area.open, true);
            igual(q(w, '[data-categoria="limites"]').open, true);
            igual(q(w, "#nav-area-calculo .nav-badge").textContent, "Próximamente");
            igual(q(w, '#arbol-herramientas [data-herramienta="limites-funciones"] .nav-badge').textContent, "Próximamente");
            igual(q(w, "#nav-area-algebra-lineal .nav-badge"), null);
            igual(q(w, "#nav-area-sistemas-numericos .nav-badge"), null);
        }],
        ["Escape con texto limpia sin cerrar, Escape vacío cierra", "/", w => {
            menu(w); valor(w, "inversa", true); q(w, "#buscador-lateral").focus();
            escape(w); igual(q(w, "#buscador-lateral").value, "");
            igual(q(w, "#navegacion-principal").hidden, false);
            igual(q(w, "#buscador-lateral-estado").textContent, "");
            escape(w); igual(q(w, "#navegacion-principal").hidden, true);
            igual(w.document.activeElement, q(w, "#navigation-toggle"));
        }],
        ["Menú restaura grupos y memoria sin guardar aperturas de filtro", "/matrices/inversa/", async w => {
            menu(w); const categoria = q(w, '[data-categoria="vectores"]'); categoria.open = true;
            const area = q(w, "#nav-area-calculo").parentElement; area.open = false;
            await turno(w);
            const memoria = w.sessionStorage.getItem("algebra-lineal-menu-secciones");
            igual(JSON.parse(memoria).includes("vectores"), true); igual(w.localStorage.getItem("algebra-lineal-menu-secciones"), null);
            const abiertos = todos(w, "#arbol-herramientas details").map(n => n.open);
            valor(w, "límites", true); await turno(w);
            igual(w.sessionStorage.getItem("algebra-lineal-menu-secciones"), memoria);
            valor(w, "", true); await turno(w);
            igual(todos(w, "#arbol-herramientas details").map(n => n.open), abiertos);
            igual(w.sessionStorage.getItem("algebra-lineal-menu-secciones"), memoria);
        }],
        ["Explorador del área: una parada de Tab, flechas y panel sin guardar nada", "/areas/algebra-lineal/", w => {
            const items = todos(w, "a.indice-item");
            const claves = Object.keys(w.localStorage).sort();
            const tecla = key => w.document.activeElement.dispatchEvent(new w.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }));
            const visible = () => todos(w, ".destacado-cuerpo").filter(c => !c.hidden).map(c => c.dataset.id);
            igual(items.filter(a => a.tabIndex === 0).length, 1);
            items[0].focus(); tecla("End"); igual(w.document.activeElement, items.at(-1));
            igual(visible(), ["determinantes"]);
            tecla("ArrowUp"); igual(visible(), ["matriz-inversa"]);
            tecla("ArrowRight"); igual(w.document.activeElement.matches(".destacado-abrir"), true);
            igual(w.document.activeElement.getAttribute("href"), "/matrices/inversa/");
            tecla("ArrowLeft"); igual(w.document.activeElement, items[4]);
            igual(items.map(a => a.tabIndex), [-1, -1, -1, -1, 0, -1]);
            igual(Object.keys(w.localStorage).sort(), claves);
        }],
        ["Grupos y herramientas ocultos no se pueden enfocar", "/", w => {
            menu(w); valor(w, "inversa", true); const input = q(w, "#buscador-lateral"); input.focus();
            const oculto = q(w, '#arbol-herramientas [data-herramienta="conversion-bases"] a');
            igual(oculto.getClientRects().length, 0); oculto.focus(); igual(w.document.activeElement, input);
        }],
    ];
    const tabla = await (await fetch("/__pruebas/contrato.json")).json();
    for (const ruta of ["/", "/?q=gauss"]) {
        casos.push([`Orden/semántica Python = JS: ${tabla.length} consultas desde ${ruta}`, ruta, w => {
            for (const { consulta, ids: esperados } of tabla) {
                valor(w, consulta); igual(ids(w), esperados);
            }
        }]);
    }
    let aprobados = 0;
    for (const [nombre, ruta, probar] of casos) {
        const fila = document.createElement("li");
        document.getElementById("resultados").append(fila);
        const frame = document.createElement("iframe"); frame.style.cssText = "width:100%;height:600px";
        const errores = [];
        const carga = new Promise(r => { frame.onload = () => r(frame.contentWindow); });
        frame.src = ruta; document.body.append(frame);
        try {
            const w = await carga;
            w.addEventListener("error", e => errores.push(e.message)); await turno(w);
            await probar(w, frame); igual(errores, []);
            fila.textContent = `OK: ${nombre}`; fila.dataset.resultado = "ok"; aprobados++;
        } catch (error) {
            fila.textContent = `FALLO: ${nombre}: ${error.message}`; fila.dataset.resultado = "fallo";
        } finally { frame.remove(); }
    }
    document.getElementById("total").textContent = `${aprobados}/${casos.length} pruebas DOM correctas.`;
})();
