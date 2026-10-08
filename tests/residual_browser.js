/* Contratos renderizados compartidos P27.10. Tab real y forced-colors: QA complementaria. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const all = (w, s) => [...w.document.querySelectorAll(s)];
    const assert = (ok, mensaje) => { if (!ok) throw new Error(mensaje); };
    const style = (w, n) => w.getComputedStyle(n);
    const input = (w, s, value) => {
        const n = q(w, s); n.value = String(value); n.dispatchEvent(new w.Event("input", {bubbles:true}));
    };
    const viewport = async (frame, width, height) => {
        frame.style.width = `${width}px`; frame.style.height = `${height}px`;
        await new Promise(resolve => setTimeout(resolve, 40));
    };
    const load = (frame, url) => new Promise(resolve => { frame.onload = () => resolve(frame.contentWindow); frame.src = url; });
    const pageFits = w => assert(w.document.documentElement.scrollWidth <= w.document.documentElement.clientWidth + 1, "Desborde de página");
    const rect = n => n.getBoundingClientRect();
    function aligned(w) {
        const rows = all(w, ".vector-row[data-vector]");
        const cells = rows.map(n => [...n.querySelectorAll("input")]);
        for (let col = 0; col < cells[0].length; col++) {
            assert(cells.every(row => Math.abs(rect(row[col]).left - rect(cells[0][col]).left) < 1), `Columna ${col + 1} desalineada`);
        }
        assert(rows.every(n => Math.abs(rect(n.querySelector(".vector-name")).right - rect(rows[0].querySelector(".vector-name")).right) < 1), "Nombres desalineados");
    }
    const casos = [];
    const viewports = [[1280,650],[900,650],[760,560],[480,650],[390,650]];
    for (const op of ["suma", "resta"]) for (const dimension of [2,3,10]) for (const [width,height] of viewports) {
        casos.push([`UI-45 ${op}, n=${dimension}, ${width}×${height}`, "/vectores/operaciones/", async (w, frame) => {
            await viewport(frame,width,height);
            q(w, `[name="operacion"][value="${op}"]`).click();
            input(w,"#id_dimension",dimension);
            q(w,"[data-agregar-vector]").click();
            const list = q(w,"#vector-list");
            assert(style(w,list).overflowX === "auto", "La lista es el único scroll");
            assert(all(w,".vector-inputs").every(n => style(w,n).overflowX === "visible" && n.scrollLeft === 0), "Una fila tiene scroll propio");
            assert(all(w,".vector-row[data-vector]").length === 3, "Tres vectores");
            assert(w.document.activeElement.name === "v3_0", "Foco al agregar");
            // Un valor largo en una sola fila también comparte el ancho de su columna.
            input(w,'[name="v2_0"]',"-123456");
            aligned(w); pageFits(w);
            q(w,`[name="v1_${dimension - 1}"]`).focus();
            aligned(w);
            list.scrollLeft = list.scrollWidth;
            aligned(w); pageFits(w);
            const remove = q(w,".vector-remove");
            const last = q(w,`[name="v3_${dimension - 1}"]`);
            assert(rect(remove).left > rect(last).right, "× no tapa la última componente");
            assert(rect(remove).right <= rect(list).right + 1, "× accesible al final del scroll");
            remove.click();
            assert(all(w,".vector-row[data-vector]").length === 2 && w.document.activeElement.name === "v2_0", "Eliminar y foco contextual");
        }]);
    }
    for (const ruta of ["/matrices/reduccion/","/matrices/ecuaciones/","/matrices/inversa/","/bases/conversion/","/romanos/conversion/"]) {
        casos.push([`UI-68/64 ${ruta}: foco único y segmentos móviles en ambos temas`,ruta,async (w,frame) => {
            await viewport(frame,390,650);
            for (const theme of ["light","dark"]) {
                w.document.documentElement.dataset.theme = theme;
                for (const radio of all(w,'.option input[type="radio"],.segment input[type="radio"]')) {
                    if (radio.disabled || !radio.getClientRects().length || radio.closest("details:not([open]), [hidden], [inert]")) continue;
                    radio.focus();
                    assert(radio.matches(":focus-visible"),`Foco de teclado representado: ${radio.id}`);
                    assert(style(w,radio).outlineStyle === "none","Sin outline interno");
                    assert(style(w,radio.closest(".option,.segment")).outlineStyle !== "none","Pastilla conserva foco");
                }
                for (const group of all(w,".segmented")) {
                    assert(style(w,group).borderRadius === style(w,q(w,".panel")).getPropertyValue("--radius-md").trim(),"Radio compartido móvil");
                }
                pageFits(w);
            }
        }]);
    }
    casos.push(["UI-68: Tema acción, nombres y pageshow; Menú con tres bordes", "/", async (w,frame) => {
        const theme = q(w,"#theme-toggle");
        assert(!theme.hidden && !theme.hasAttribute("aria-pressed"),"Tema operativo sin estado contradictorio");
        for (let i=0;i<2;i++) {
            const dark = w.document.documentElement.dataset.theme === "dark";
            assert(theme.getAttribute("aria-label") === `Cambiar a tema ${dark ? "claro" : "oscuro"}`,"Nombre anuncia acción");
            theme.click();
            assert((w.document.documentElement.dataset.theme === "dark") !== dark,"Tema cambia");
        }
        w.dispatchEvent(new w.PageTransitionEvent("pageshow",{persisted:true}));
        assert(!theme.hasAttribute("aria-pressed"),"pageshow mantiene semántica");
        for (const [width,height] of viewports) {
            await viewport(frame,width,height);
            const icon = q(w,".navigation-toggle-icon");
            for (const pseudo of [null,"::before","::after"]) {
                const css = w.getComputedStyle(icon,pseudo);
                assert(css.borderTopStyle === "solid" && parseFloat(css.borderTopWidth) > 0,"Línea por borde compatible con forced-colors");
            }
            pageFits(w);
        }
    }]);
    casos.push(["Header: identidad visible con colores del sistema en forced-colors", "/matrices/reduccion/", async (w,frame) => {
        const brand = q(w,".app-brand"), mark = q(w,".app-mark"), path = mark.querySelector("path");
        const probe = w.document.createElement("span");
        w.document.body.append(probe);
        for (const theme of ["light","dark"]) {
            w.document.documentElement.dataset.theme = theme;
            for (const width of [390,760,1280]) {
                await viewport(frame,width,650);
                assert(brand.tagName === "A" && brand.getAttribute("href") === "/", "Identidad conserva enlace a Inicio");
                assert(rect(mark).width > 0 && path.getBBox().width > 0 && style(w,path).fill !== "none", "SVG conserva representación");
                assert(style(w,brand).forcedColorAdjust !== "none" && style(w,mark).forcedColorAdjust !== "none", "Adaptación del sistema activa");
                probe.style.color = w.matchMedia("(forced-colors: active)").matches ? "CanvasText" : "var(--color-mark)";
                const expected = style(w,probe).color;
                assert(style(w,mark).color === expected && style(w,path).fill === expected, "Marca respeta color de sistema o tema normal");
                if (w.matchMedia("(forced-colors: active)").matches) {
                    assert(style(w,brand).color === expected && style(w,q(w,".app-name")).color === expected, "Identidad usa CanvasText");
                    probe.style.color = "LinkText";
                    assert(style(w,q(w,".breadcrumbs a")).color === style(w,probe).color, "Navegación convencional conserva LinkText");
                }
                brand.focus(); assert(style(w,brand).outlineStyle !== "none", "Enlace conserva foco visible");
                pageFits(w);
            }
        }
        probe.remove();
    }]);
    casos.push(["UI-68.4: sin JS, Tema oculto y navegación disponible", "/", (w) => {
        assert(q(w,"#theme-toggle").hidden && style(w,q(w,"#theme-toggle")).display === "none","Sin acción falsa");
        assert(q(w,"#navigation-toggle").hidden,"Menú conserva mejora progresiva");
        assert(!q(w,"#navegacion-principal").hidden,"Navegación sin JS usable");
    }, true]);
    casos.push(["UI-20: enlaces compartidos del estado vacío en ambos temas", "/?q=zzzz", async (w,frame) => {
        await viewport(frame,390,650);
        const links = all(w,"#resultados-busqueda .search-suggestions a");
        assert(links.length === 3,"Tres enlaces sin cambiar copy");
        for (const theme of ["light","dark"]) {
            w.document.documentElement.dataset.theme = theme;
            for (const link of links) {
                assert(link.classList.contains("text-link") && link.href.includes("?q="),"Contrato compartido y destino");
                assert(style(w,link).textDecorationLine.includes("underline"),"Enlace inequívoco");
                link.focus(); assert(style(w,link).outlineStyle !== "none","Foco visible");
            }
            pageFits(w);
        }
    }]);
    let passed = 0;
    for (const [name,ruta,test,nojs] of casos) {
        const frame = document.createElement("iframe"); frame.title = name;
        frame.style.cssText = "display:block;width:1280px;height:650px;border:0";
        if (nojs) frame.setAttribute("sandbox","allow-same-origin");
        document.body.append(frame);
        const item = document.createElement("li");
        try { await test(await load(frame,ruta),frame); passed++; item.textContent = `PASS · ${name}`; }
        catch(error) { item.textContent = `FAIL · ${name}: ${error.message}`; }
        q(window,"#resultados").append(item); frame.remove();
    }
    q(window,"#total").textContent = `${passed}/${casos.length} PASS`;
})();
