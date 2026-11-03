(() => {
    "use strict";
    const form = document.getElementById("biseccion-form");
    const grafica = document.getElementById("biseccion-grafica");
    if (!form || !grafica) return;
    const datos = JSON.parse(document.getElementById("datos-biseccion").textContent);
    const resultado = datos.resultado;
    const pasos = resultado?.iteraciones || [];
    const estado = document.getElementById("grafica-estado");
    const slider = document.getElementById("iteracion-biseccion");
    const lectura = document.getElementById("iteracion-lectura");
    const filas = [...document.querySelectorAll("[data-iteracion]")];
    const numero = x => Number(x).toLocaleString("es", { maximumSignificantDigits: 12 });
    const campo = nombre => form.elements.namedItem(nombre);
    const color = nombre => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
    let mutando = false, temporizador, peticion, generacion = 0;

    function intervalo() {
        if (!campo("a").value.trim() || !campo("b").value.trim()) return null;
        const a = Number(campo("a").value), b = Number(campo("b").value);
        return Number.isFinite(a) && Number.isFinite(b) && a < b ? [a, b] : null;
    }

    function linea(x, nombre) {
        return { type: "line", x0: x, x1: x, y0: 0, y1: 1, yref: "paper", editable: true,
            line: { color: color("--color-brand"), width: 3, dash: "dash" },
            label: { text: nombre, textposition: "top right", font: { color: color("--color-text") } } };
    }

    function franja(a, b) {
        return { type: "rect", x0: a, x1: b, y0: 0, y1: 1, yref: "paper", editable: false,
            fillcolor: color("--color-brand"), opacity: .12, line: { width: 0 }, layer: "below" };
    }

    function mostrarPaso(i) {
        const p = pasos[i - 1];
        if (!p) return;
        slider.value = String(i);
        slider.setAttribute("aria-valuetext", `Iteración ${i} de ${pasos.length}, c = ${numero(p.c)}`);
        lectura.textContent = `Iteración ${i}/${pasos.length}: [${numero(p.a)}, ${numero(p.b)}] · c = ${numero(p.c)} · f(c) = ${numero(p.fc)}`;
        filas.forEach(f => f.toggleAttribute("data-activa", Number(f.dataset.iteracion) === i));
        mutando = true;
        Plotly.update(grafica, { x: [[p.a, p.c, p.b]], y: [[p.fa, p.fc, p.fb]],
            text: [["a", "c (punto medio)", "b"]] }, { "shapes[2].x0": p.a, "shapes[2].x1": p.b }, [1])
            .finally(() => { mutando = false; });
    }

    async function muestrear(rango, moverEjes = false) {
        const n = ++generacion;
        peticion?.abort();
        peticion = new AbortController();
        const post = new URLSearchParams({ funcion: campo("funcion").value,
            a: String(rango[0]), b: String(rango[1]), csrfmiddlewaretoken: campo("csrfmiddlewaretoken").value });
        estado.textContent = "Actualizando gráfica…";
        try {
            const response = await fetch(new URL(datos.grafica_url, window.location.href), {
                method: "POST", body: post, signal: peticion.signal,
                headers: { "X-CSRFToken": campo("csrfmiddlewaretoken").value }, credentials: "same-origin",
            });
            const puntos = await response.json();
            if (n !== generacion) return;
            if (!response.ok) throw new Error(puntos.error);
            await Plotly.restyle(grafica, { x: [puntos.x], y: [puntos.y] }, [0]);
            const limites = intervalo();
            if (moverEjes && limites) {
                mutando = true;
                await Plotly.relayout(grafica, { "xaxis.range": rango, "yaxis.autorange": true,
                    "shapes[0].x0": limites[0], "shapes[0].x1": limites[0],
                    "shapes[1].x0": limites[1], "shapes[1].x1": limites[1],
                    "shapes[0].y0": 0, "shapes[0].y1": 1, "shapes[1].y0": 0, "shapes[1].y1": 1 });
                mutando = false;
            }
            estado.textContent = puntos.y.some(y => y === null)
                ? "La curva tiene huecos donde no se pudo verificar el dominio. La gráfica es un muestreo, no una prueba de raíces."
                : "Gráfica muestreada. Resolver comprueba dominio y cambio de signo del intervalo.";
        } catch (error) {
            if (error.name !== "AbortError" && n === generacion) {
                estado.textContent = `Gráfica anterior: ${error.message || "no se pudo actualizar"}`;
            }
        }
    }

    function previsualizar() {
        clearTimeout(temporizador);
        // Invalidar también durante la espera evita pintar una respuesta de la entrada anterior.
        generacion++;
        peticion?.abort();
        const limites = intervalo();
        if (!limites) {
            estado.textContent = "Gráfica anterior: escribe un intervalo con a menor que b.";
            return;
        }
        const ancho = limites[1] - limites[0];
        temporizador = setTimeout(() => muestrear([limites[0] - ancho / 4, limites[1] + ancho / 4], true), 300);
    }

    function comparar() {
        const contenedor = document.getElementById("biseccion-comparaciones");
        if (!contenedor || !resultado) return;
        const clave = "pygebra-biseccion-v1";
        let anteriores = [];
        try {
            const guardados = JSON.parse(sessionStorage.getItem(clave) || "[]");
            if (Array.isArray(guardados)) anteriores = guardados.filter(r => r && typeof r.clave === "string" &&
                [r.a, r.b, r.c, r.inicial_a, r.inicial_b, r.iteraciones].every(Number.isFinite)).slice(-9);
        } catch { /* La comparación actual sigue disponible si el almacenamiento está desactivado. */ }
        const actual = { clave: datos.clave, a: resultado.a, b: resultado.b, c: resultado.c,
            inicial_a: datos.inicial_a, inicial_b: datos.inicial_b,
            iteraciones: pasos.length, convergio: resultado.convergio };
        const registros = [...anteriores, actual];
        try { sessionStorage.setItem(clave, JSON.stringify(registros)); } catch { /* Sin persistencia entre envíos. */ }
        const tabla = document.createElement("table");
        tabla.className = "procedure-table";
        const caption = tabla.createCaption();
        caption.textContent = "Resultados de esta función en la pestaña actual";
        const cabecera = tabla.createTHead().insertRow();
        ["Intervalo inicial", "Aproximación", "Iteraciones", "Comparación con el actual"].forEach(t => {
            const th = document.createElement("th"); th.scope = "col"; th.textContent = t; cabecera.append(th);
        });
        const cuerpo = tabla.createTBody();
        registros.filter(r => r.clave === datos.clave).forEach(r => {
            const misma = Math.max(r.a, actual.a) <= Math.min(r.b, actual.b);
            const texto = r === actual ? "Actual" : !r.convergio || !actual.convergio ? "Sin convergencia verificada"
                : misma ? "Compatible con la misma raíz" : "Intervalos finales distintos";
            const fila = cuerpo.insertRow();
            [`[${numero(r.inicial_a)}, ${numero(r.inicial_b)}]`, numero(r.c), String(r.iteraciones), texto]
                .forEach(t => { fila.insertCell().textContent = t; });
        });
        contenedor.replaceChildren(tabla);
    }

    async function iniciar() {
        comparar();
        if (!window.Plotly) {
            estado.textContent = "No se pudo cargar la gráfica local. El resultado y la tabla siguen disponibles.";
            return;
        }
        const limites = intervalo() || [.55, 1.1];
        const layout = {
            margin: { t: 28, r: 18, b: 48, l: 60 }, showlegend: false,
            paper_bgcolor: color("--color-surface"), plot_bgcolor: color("--color-surface"),
            font: { family: "Segoe UI, sans-serif", color: color("--color-text") },
            xaxis: { title: { text: "x" }, gridcolor: color("--color-border"), zerolinecolor: color("--color-muted") },
            yaxis: { title: { text: "f(x)" }, gridcolor: color("--color-border"), zerolinecolor: color("--color-muted") },
            shapes: [linea(limites[0], "a"), linea(limites[1], "b"), franja(limites[0], limites[1])],
            dragmode: "pan",
        };
        await Plotly.newPlot(grafica, [
            { x: [], y: [], type: "scatter", mode: "lines", connectgaps: false, name: "f(x)",
                line: { color: color("--color-brand"), width: 2 }, hovertemplate: "x = %{x:.10g}<br>f(x) = %{y:.10g}<extra></extra>" },
            { x: [], y: [], type: "scatter", mode: "markers", name: "Iteración",
                marker: { size: [9, 13, 9], symbol: ["circle", "diamond", "circle"], color: color("--color-text") },
                hovertemplate: "%{text}<br>x = %{x:.12g}<br>f(x) = %{y:.12g}<extra></extra>" },
        ], layout, { responsive: true, locale: "es", displaylogo: false, scrollZoom: false,
            edits: { shapePosition: true },
            modeBarButtons: [["zoom2d", "pan2d", "zoomIn2d", "zoomOut2d", "resetScale2d"]] });
        grafica.on("plotly_relayout", cambio => {
            if (mutando) return;
            let cambioExtremos = false;
            ["a", "b"].forEach((nombre, i) => {
                const x = cambio[`shapes[${i}].x0`] ?? cambio[`shapes[${i}].x1`] ?? cambio.shapes?.[i]?.x0;
                if (!Number.isFinite(x)) return;
                campo(nombre).value = String(x);
                campo(nombre).dispatchEvent(new Event("input", { bubbles: true }));
                cambioExtremos = true;
            });
            if (cambioExtremos) return;
            const rango = cambio["xaxis.range"] || (cambio["xaxis.range[0]"] !== undefined
                ? [cambio["xaxis.range[0]"], cambio["xaxis.range[1]"]] : null);
            if (rango?.every(Number.isFinite) && rango[0] < rango[1]) {
                clearTimeout(temporizador);
                temporizador = setTimeout(() => muestrear(rango), 200);
            }
        });
        ["funcion", "a", "b"].forEach(n => campo(n).addEventListener("input", previsualizar));
        slider?.addEventListener("input", () => mostrarPaso(Number(slider.value)));
        filas.forEach(fila => {
            ["pointerenter", "focus", "click"].forEach(tipo => fila.addEventListener(tipo, () => mostrarPaso(Number(fila.dataset.iteracion))));
        });
        new MutationObserver(() => {
            Plotly.relayout(grafica, { paper_bgcolor: color("--color-surface"), plot_bgcolor: color("--color-surface"),
                "font.color": color("--color-text"), "xaxis.gridcolor": color("--color-border"),
                "yaxis.gridcolor": color("--color-border"), "xaxis.zerolinecolor": color("--color-muted"),
                "yaxis.zerolinecolor": color("--color-muted"), "shapes[0].line.color": color("--color-brand"),
                "shapes[1].line.color": color("--color-brand"), "shapes[2].fillcolor": color("--color-brand"),
                "shapes[0].label.font.color": color("--color-text"), "shapes[1].label.font.color": color("--color-text") });
            Plotly.restyle(grafica, { "line.color": color("--color-brand") }, [0]);
            Plotly.restyle(grafica, { "marker.color": color("--color-text") }, [1]);
        }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
        previsualizar();
        if (pasos.length) mostrarPaso(pasos.length);
        else if (resultado) Plotly.restyle(grafica, { x: [[resultado.c]], y: [[resultado.fc]], text: [["c"]] }, [1]);
    }
    iniciar().catch(() => { estado.textContent = "No se pudo iniciar la gráfica. Consulta el resultado y el procedimiento."; });
})();
