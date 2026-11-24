/* Jacobi y Gauss-Seidel: una sola iteración elegida (k) para la gráfica, la sustitución y la tabla.
   La tabla del servidor es la fuente: data-valor (valor almacenado) para dibujar y copiar; su texto,
   con el formato global vigente (numeros.js), para leer. Recorrer iteraciones nunca recalcula. */
(() => {
    "use strict";
    const resultado = document.querySelector("#resultado.iterativos-resultado");
    if (!resultado) return;
    const tolerancia = Number(resultado.dataset.tolerancia);
    const css = nombre => getComputedStyle(resultado).getPropertyValue(nombre).trim();
    const serie = j => css(`--serie-${j % 10 + 1}`);
    // Forma además de color: las incógnitas se distinguen también sin percibir el tono.
    const SIMBOLOS = ["circle", "square", "diamond", "triangle-up", "x", "triangle-down", "star", "cross", "pentagon", "hexagon"];
    const leer = celda => celda.textContent.trim();
    const numero = celda => celda.dataset.valor === "" ? null : Number(celda.dataset.valor);
    const positivo = x => x > 0 ? x : null; // el eje logarítmico no admite ceros
    const graficas = []; // [{div, trazas, layout}] para redibujar con el tema o el formato

    // «=» si se lee el valor almacenado; «≈» si el formato vigente lo redondea.
    function relaciones(raiz) {
        raiz.querySelectorAll("[data-relacion]").forEach(relacion => {
            const redondeado = [...relacion.nextElementSibling.querySelectorAll("[data-numeric]")]
                .some(nodo => leer(nodo) !== JSON.parse(nodo.dataset.numeric).exacto);
            relacion.textContent = redondeado ? "≈" : "=";
        });
    }

    function layout(alto, eje) {
        const rejilla = css("--color-border");
        return {
            height: alto, margin: { t: 8, r: 12, b: 42, l: 58 },
            paper_bgcolor: css("--color-surface-raised"), plot_bgcolor: css("--color-surface-raised"),
            font: { family: getComputedStyle(document.body).fontFamily, color: css("--color-text"), size: 12 },
            xaxis: { title: { text: "Iteración k" }, gridcolor: rejilla, zeroline: false, tickformat: "d", rangemode: "tozero" },
            yaxis: { gridcolor: rejilla, zerolinecolor: css("--color-border-strong"), automargin: true, ...eje },
            legend: { orientation: "h", x: 0, y: 1, yanchor: "bottom", font: { size: 12 } },
            hovermode: "closest", separators: ". ", dragmode: "zoom",
            // 0: tramo de k − 1 a k (la iteración elegida); 1: x⁽ᵏ⁾.
            shapes: [
                { type: "rect", xref: "x", yref: "paper", x0: 0, x1: 0, y0: 0, y1: 1, layer: "below",
                    fillcolor: css("--color-brand"), opacity: .1, line: { width: 0 }, visible: false },
                { type: "line", xref: "x", yref: "paper", x0: 0, x1: 0, y0: 0, y1: 1,
                    line: { color: css("--color-brand"), width: 1.5, dash: "dot" }, visible: false },
            ],
        };
    }
    // En pantallas estrechas la barra de zoom taparía la leyenda; ahí se amplía con los dedos.
    const CONFIG = { responsive: true, locale: "es", displaylogo: false,
        displayModeBar: matchMedia("(min-width: 40rem)").matches ? "hover" : false,
        modeBarButtons: [["zoomIn2d", "zoomOut2d", "resetScale2d"]] };

    function dibujar(div, trazas, alto, eje) {
        if (!window.Plotly || !div) return null;
        const grafica = { div, trazas, alto, eje };
        div.hidden = false;
        Plotly.newPlot(div, trazas(), layout(alto, eje), CONFIG);
        graficas.push(grafica);
        return grafica;
    }

    function marcarK(grafica, k) {
        if (!grafica) return;
        Plotly.relayout(grafica.div, { "shapes[0].x0": k - 1, "shapes[0].x1": k, "shapes[0].visible": k > 0,
            "shapes[1].x0": k, "shapes[1].x1": k, "shapes[1].visible": true });
    }

    // Tolerancia como referencia horizontal con nombre propio en la leyenda.
    const trazaTolerancia = ultima => ({ x: [0, Math.max(ultima, 1)], y: [tolerancia, tolerancia], type: "scatter", mode: "lines",
        name: "Tolerancia ε", line: { color: css("--color-muted"), dash: "dash", width: 1.5 }, hoverinfo: "skip" });

    function iniciar(articulo) {
        const filas = [...articulo.querySelectorAll("tbody tr[data-iteracion]")];
        const nombres = [...articulo.querySelectorAll("thead .iterativo-x")].map(leer);
        const n = nombres.length;
        const ultima = Number(articulo.dataset.ultima);
        const ks = filas.map((_, k) => k);
        const celda = (k, j) => filas[k].cells[j + 1]; // j = n: cambio; j = n + 1: residuo
        const marco = articulo.querySelector(".iterativo-tabla-marco");
        const rango = articulo.querySelector("[data-k]");
        let k = ultima ? 1 : 0;

        const variables = dibujar(articulo.querySelector('[data-grafica="variables"]'), () => [
            ...nombres.map((nombre, j) => ({
                x: ks, y: ks.map(i => numero(celda(i, j))), type: "scatter", mode: "lines+markers", name: nombre,
                line: { color: serie(j), width: 2 }, marker: { color: serie(j), size: 6, symbol: SIMBOLOS[j % 10] },
                customdata: ks.map(i => leer(celda(i, j))), hovertemplate: `${nombre}⁽%{x}⁾ = %{customdata}<extra></extra>`,
            })),
            { x: nombres.map(() => k), y: nombres.map((_, j) => numero(celda(k, j))), type: "scatter", mode: "markers",
                showlegend: false, hoverinfo: "skip", name: "k elegida",
                marker: { size: 12, color: nombres.map((_, j) => serie(j)), line: { width: 2, color: css("--color-surface-raised") } } },
        ], 300, {});
        const errores = dibujar(articulo.querySelector('[data-grafica="error"]'), () => [
            { x: ks.slice(1), y: ks.slice(1).map(i => positivo(numero(celda(i, n)))), type: "scatter", mode: "lines+markers",
                name: "Cambio máximo", line: { color: css("--color-brand"), width: 2 }, marker: { size: 5 },
                customdata: ks.slice(1).map(i => leer(celda(i, n))), hovertemplate: "Cambio⁽%{x}⁾ = %{customdata}<extra></extra>" },
            { x: ks, y: ks.map(i => positivo(numero(celda(i, n + 1)))), type: "scatter", mode: "lines+markers",
                name: "Residuo ‖r‖∞", line: { color: css("--color-warning"), width: 2 }, marker: { size: 5, symbol: "square" },
                customdata: ks.map(i => leer(celda(i, n + 1))), hovertemplate: "‖r⁽%{x}⁾‖∞ = %{customdata}<extra></extra>" },
            trazaTolerancia(ultima),
        ], 190, { type: "log", exponentformat: "power", title: { text: "escala log" } });
        for (const grafica of [variables, errores]) {
            grafica?.div.on("plotly_click", evento => {
                const x = evento.points?.[0]?.x;
                if (Number.isInteger(x) && x >= 1) mostrar(x);
            });
        }

        // Valores de la sustitución: copia de la celda de la tabla (k − 1 o k), con su formato vigente.
        function sustituir() {
            articulo.querySelectorAll(".iterativo-valor[data-columna]").forEach(valor => {
                const origen = celda(valor.dataset.origen === "nuevo" ? k : k - 1, Number(valor.dataset.columna));
                valor.replaceChildren(...origen.cloneNode(true).childNodes);
            });
            relaciones(articulo);
            articulo.querySelector('[data-medida="cambio"]')?.replaceChildren(...celda(k, n).cloneNode(true).childNodes);
            articulo.querySelector('[data-medida="norma"]')?.replaceChildren(...celda(k, n + 1).cloneNode(true).childNodes);
        }

        function mostrar(nuevo, { enfocar = false } = {}) {
            if (!ultima) return;
            k = Math.min(Math.max(nuevo, 1), ultima);
            rango.value = String(k);
            articulo.querySelectorAll("[data-k-texto], [data-k-nuevo]").forEach(nodo => { nodo.textContent = k; });
            articulo.querySelectorAll("[data-k-anterior]").forEach(nodo => { nodo.textContent = k - 1; });
            sustituir();
            filas.forEach((fila, i) => {
                fila.toggleAttribute("aria-current", i === k);
                if (i === k) fila.setAttribute("aria-current", "true");
                fila.toggleAttribute("data-anterior", i === k - 1);
                fila.tabIndex = i === k ? 0 : -1;
            });
            // Solo el marco de la tabla se desplaza; la página se queda donde está.
            const fila = filas[k], rf = fila.getBoundingClientRect(), rm = marco.getBoundingClientRect();
            const cabecera = marco.querySelector("thead").offsetHeight;
            if (rf.top < rm.top + cabecera) marco.scrollTop -= rm.top + cabecera - rf.top;
            else if (rf.bottom > rm.bottom) marco.scrollTop += rf.bottom - rm.bottom;
            if (enfocar) fila.focus({ preventScroll: true });
            if (variables) {
                Plotly.restyle(variables.div, { x: [nombres.map(() => k)], y: [nombres.map((_, j) => numero(celda(k, j)))] }, [n]);
            }
            marcarK(variables, k);
            marcarK(errores, k);
        }

        if (ultima) {
            articulo.querySelector("[data-control]").hidden = false;
            rango.addEventListener("input", () => mostrar(Number(rango.value)));
            articulo.querySelectorAll("[data-paso]").forEach(boton =>
                boton.addEventListener("click", () => mostrar(k + Number(boton.dataset.paso))));
            const tbody = marco.querySelector("tbody");
            tbody.addEventListener("click", evento => {
                const i = filas.indexOf(evento.target.closest("tr"));
                if (i >= 1) mostrar(i, { enfocar: true });
            });
            tbody.addEventListener("keydown", evento => {
                const destino = { ArrowDown: k + 1, ArrowUp: k - 1, Home: 1, End: ultima }[evento.key];
                if (destino === undefined) return;
                evento.preventDefault();
                mostrar(destino, { enfocar: true });
            });
            // Gauss-Seidel: señalar un valor muestra de dónde viene (la fila ya calculada o la tabla).
            const lista = articulo.querySelector(".iterativo-sustituciones");
            lista.addEventListener("pointerover", evento => {
                const valor = evento.target.closest(".iterativo-valor[data-columna]");
                lista.querySelectorAll(".iterativo-fuente").forEach(nodo => nodo.classList.remove("iterativo-fuente"));
                marco.querySelector(".iterativo-fuente")?.classList.remove("iterativo-fuente");
                if (!valor) return;
                const { columna, origen } = valor.dataset;
                lista.querySelectorAll(`.iterativo-valor[data-columna="${columna}"][data-origen="${origen}"]`)
                    .forEach(nodo => nodo.classList.add("iterativo-fuente"));
                celda(origen === "nuevo" ? k : k - 1, Number(columna)).classList.add("iterativo-fuente");
            });
            lista.addEventListener("pointerleave", () => lista.dispatchEvent(new PointerEvent("pointerover")));
            mostrar(1);
        }

        // CSV con las cifras almacenadas (no las redondeadas) y una tabla HTML para hojas de cálculo.
        const copiar = articulo.querySelector("[data-copiar-tabla]");
        copiar.hidden = false;
        copiar.querySelector("button").addEventListener("click", async () => {
            const encabezado = ["k", ...nombres.map(nombre => nombre.normalize("NFKC")), "cambio_maximo", "residuo_infinito"];
            const datos = filas.map((fila, i) => [String(i), ...[...fila.cells].slice(1).map(td => td.dataset.valor)]);
            const csv = [encabezado, ...datos].map(linea => linea.join(",")).join("\r\n");
            const html = `<table>${[encabezado, ...datos].map(linea => `<tr>${linea.map(v => `<td>${v}</td>`).join("")}</tr>`).join("")}</table>`;
            const estado = copiar.querySelector("[data-estado-copia]");
            let copiado = false;
            const alCopiar = evento => {
                evento.clipboardData.setData("text/plain", csv);
                evento.clipboardData.setData("text/html", html);
                evento.preventDefault();
                evento.stopImmediatePropagation();
                copiado = true;
            };
            window.addEventListener("copy", alCopiar, { capture: true, once: true });
            try { document.execCommand("copy"); } catch { /* se intenta abajo */ }
            window.removeEventListener("copy", alCopiar, { capture: true });
            if (!copiado) {
                try { await navigator.clipboard.writeText(csv); copiado = true; } catch { /* se informa */ }
            }
            estado.textContent = copiado ? `Tabla copiada: ${filas.length} filas en CSV.` : "No se pudo copiar la tabla.";
        });

        return { articulo, mostrar: x => mostrar(x), k: () => k, ultima, filas, celda, n };
    }

    const metodos = [...resultado.querySelectorAll("[data-iterativo]")].map(iniciar);
    relaciones(resultado.querySelector(".iterativos-cabecera"));

    // Comparación: el residuo de ambos métodos sobre los mismos ejes, con la tolerancia.
    const comparacion = resultado.querySelector('[data-grafica="comparacion"]');
    if (comparacion) {
        const ultima = Math.max(...metodos.map(m => m.filas.length - 1));
        const graficaComparacion = dibujar(comparacion, () => [
            ...metodos.map((m, i) => ({
                x: m.filas.map((_, k) => k), y: m.filas.map((_, k) => positivo(numero(m.celda(k, m.n + 1)))),
                type: "scatter", mode: "lines+markers", name: m.articulo.querySelector(".iterativo-titulo").textContent.trim(),
                line: { color: css(`--metodo-${i + 1}`), width: 2 }, marker: { size: 6, symbol: i ? "square" : "circle" },
                customdata: m.filas.map((_, k) => leer(m.celda(k, m.n + 1))),
                hovertemplate: "‖r⁽%{x}⁾‖∞ = %{customdata}<extra>%{fullData.name}</extra>",
            })),
            trazaTolerancia(ultima),
        ], 220, { type: "log", exponentformat: "power", title: { text: "‖r‖∞ (log)" } });
        // Las líneas de la k elegida no aplican a dos métodos a la vez.
        if (graficaComparacion) Plotly.relayout(comparacion, { shapes: [] });

        // Un método a la vez en la zona de estudio; la k elegida pasa al otro (acotada a sus iteraciones).
        const selector = resultado.querySelector("[data-selector-metodo]");
        const botones = [...selector.querySelectorAll("[data-mostrar]")];
        function elegir(clave) {
            const actual = metodos.find(m => !m.articulo.hidden);
            botones.forEach(boton => boton.setAttribute("aria-pressed", String(boton.dataset.mostrar === clave)));
            metodos.forEach(m => { m.articulo.hidden = m.articulo.dataset.iterativo !== clave; });
            const destino = metodos.find(m => m.articulo.dataset.iterativo === clave);
            if (actual && actual !== destino && destino.ultima) destino.mostrar(actual.k());
            destino.articulo.querySelectorAll(".js-plotly-plot").forEach(div => Plotly.Plots.resize(div));
        }
        selector.hidden = false;
        botones.forEach(boton => boton.addEventListener("click", () => elegir(boton.dataset.mostrar)));
        elegir(botones[0].dataset.mostrar);
    }

    // El formato global (numeros.js, cargado antes) ya cambió el texto de la tabla al llegar aquí el mismo
    // change o pageshow: las sustituciones y las etiquetas de las gráficas lo copian.
    function seguirFormato() {
        metodos.forEach(m => { if (m.ultima) m.mostrar(m.k()); });
        relaciones(resultado.querySelector(".iterativos-cabecera"));
        if (window.Plotly) graficas.forEach(g => Plotly.restyle(g.div, { customdata: g.trazas().map(t => t.customdata ?? null) }));
    }
    resultado.querySelector("[data-numeric-controls]")?.addEventListener("change", seguirFormato);
    window.addEventListener("pageshow", evento => { if (evento.persisted) seguirFormato(); });
    // Tema o estilo: colores nuevos sin perder el zoom ni la k elegida.
    if (window.Plotly) {
        new MutationObserver(() => graficas.forEach(g => {
            const rangos = { x: g.div.layout.xaxis.range, y: g.div.layout.yaxis.range };
            const nuevo = layout(g.alto, g.eje);
            nuevo.shapes = g.div.layout.shapes.map((forma, i) => ({ ...forma, ...nuevo.shapes[i], x0: forma.x0, x1: forma.x1, visible: forma.visible }));
            if (!g.div.layout.xaxis.autorange) Object.assign(nuevo.xaxis, { range: rangos.x, autorange: false });
            if (!g.div.layout.yaxis.autorange) Object.assign(nuevo.yaxis, { range: rangos.y, autorange: false });
            Plotly.react(g.div, g.trazas(), nuevo, CONFIG);
        })).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "data-estilo"] });
    }
})();
