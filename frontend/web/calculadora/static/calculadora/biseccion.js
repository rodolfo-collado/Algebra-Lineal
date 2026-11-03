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
    const numero = (x, digitos = 12) => Number(x).toLocaleString("es", { maximumSignificantDigits: digitos });
    const campo = nombre => form.elements.namedItem(nombre);
    const color = nombre => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
    let mutando = false, temporizador, peticion, inicializacion, generacion = 0;
    const ayudaGrafica = document.getElementById("grafica-ayuda");
    const indicacion = "Introduce una función y un intervalo para visualizar su gráfica.";
    ayudaGrafica.hidden = true;

    function presentarNumeros() {
        const controles = document.getElementById("biseccion-formato");
        if (!controles) return;
        const selector = document.getElementById("biseccion-decimales");
        const grupos = [...document.querySelectorAll("[data-biseccion-grupo]")].map(grupo =>
            [...grupo.querySelectorAll("[data-biseccion-numero]")].map(nodo => ({ nodo, valor: Number(nodo.dataset.biseccionNumero) })));
        function completo(x) {
            return x === 0 || (Math.abs(x) >= 1e-16 && Math.abs(x) < 1e12)
                ? x.toLocaleString("en-US", { useGrouping: false, maximumSignificantDigits: 17 }) : String(x);
        }
        function decimal(x, p) {
            if (Math.abs(x) >= 1e12 || (x !== 0 && Math.abs(x) < 1e-16)) return completo(x);
            const texto = x.toFixed(p);
            return texto.includes(".") ? texto.replace(/0+$/, "").replace(/\.$/, "") : texto;
        }
        function aplicar() {
            for (const grupo of grupos) {
                const valores = new Set(grupo.map(d => d.valor));
                let p = Number(selector.value);
                const esCompleto = selector.value === "completa";
                let textos = [];
                for (; !esCompleto && p <= 16; p++) {
                    textos = grupo.map(d => decimal(d.valor, p));
                    if (new Set(textos).size === valores.size && !textos.some((t, i) => Number(t) === 0 && grupo[i].valor !== 0)) break;
                }
                grupo.forEach((d, i) => {
                    const texto = esCompleto || p > 16 ? completo(d.valor) : textos[i];
                    const aproximado = Number(texto) !== d.valor;
                    d.nodo.textContent = (aproximado && !d.nodo.closest(".biseccion-raiz") ? "≈ " : "") + texto;
                    d.nodo.setAttribute("aria-label", aproximado ? `${texto}, redondeado; valor almacenado ${d.valor}` : texto);
                });
            }
        }
        controles.hidden = false;
        selector.addEventListener("change", aplicar);
        aplicar();
    }

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
        const valores = new Set([p.a, p.c, p.b, p.nuevo_a, p.nuevo_b]);
        let digitos = 8;
        // Mostrar los puntos distintos como distintos, incluso con tolerancias muy pequeñas.
        while (digitos < 17 && new Set([...valores].map(x => numero(x, digitos))).size < valores.size) digitos++;
        const n = x => numero(x, digitos);
        const signo = x => x > 0 ? "positivo" : x < 0 ? "negativo" : "cero";
        lectura.querySelector("#paso-valores").textContent = `Iteración ${i}/${pasos.length}. Antes de dividir: a (izquierdo) = ${n(p.a)} · c (punto medio) = ${n(p.c)} · b (derecho) = ${n(p.b)}.`;
        lectura.querySelector("#paso-signos").textContent = `f(a) = ${n(p.fa)} (${signo(p.fa)}) · f(c) = ${n(p.fc)} (${signo(p.fc)}) · f(b) = ${n(p.fb)} (${signo(p.fb)}).`;
        const mitad = (p.fa < 0) !== (p.fc < 0) ? "izquierda [a,c]: f(a) y f(c) tienen signos opuestos" : "derecha [c,b]: f(c) y f(b) tienen signos opuestos";
        lectura.querySelector("#paso-decision").textContent = p.fc === 0
            ? `f(c) = 0 en aritmética de máquina: encontramos una raíz calculada. Después: [${n(p.nuevo_a)}; ${n(p.nuevo_b)}]; no hace falta otra mitad.`
            : `Conservamos la mitad ${mitad}. Después: [${n(p.nuevo_a)}; ${n(p.nuevo_b)}], longitud ${n(p.longitud)}.`;
        filas.forEach(f => f.toggleAttribute("data-activa", Number(f.dataset.iteracion) === i));
        if (!grafica.data) return;
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
            grafica.hidden = false;
            ayudaGrafica.hidden = false;
            await (inicializacion ??= iniciar());
            if (n !== generacion) return;
            await Plotly.restyle(grafica, { x: [puntos.x], y: [puntos.y] }, [0]);
            if (n !== generacion) return;
            const limites = intervalo();
            if (moverEjes && limites) {
                mutando = true;
                await Plotly.relayout(grafica, { "xaxis.range": rango, "yaxis.autorange": true,
                    "shapes[0].x0": limites[0], "shapes[0].x1": limites[0],
                    "shapes[1].x0": limites[1], "shapes[1].x1": limites[1],
                    "shapes[0].y0": 0, "shapes[0].y1": 1, "shapes[1].y0": 0, "shapes[1].y1": 1 });
                mutando = false;
                if (n !== generacion) return;
            }
            estado.textContent = puntos.y.some(y => y === null)
                ? "La curva tiene huecos donde no se pudo verificar el dominio. La gráfica es un muestreo, no una prueba de raíces."
                : "Gráfica muestreada. Resolver comprueba dominio y cambio de signo del intervalo.";
        } catch (error) {
            if (error.name !== "AbortError" && n === generacion) {
                grafica.hidden = true;
                ayudaGrafica.hidden = true;
                estado.textContent = error.message || "No se pudo actualizar la gráfica.";
            }
        }
    }

    function previsualizar() {
        clearTimeout(temporizador);
        // Invalidar también durante la espera evita pintar una respuesta de la entrada anterior.
        generacion++;
        peticion?.abort();
        if (["funcion", "a", "b"].some(n => !campo(n).value.trim())) {
            grafica.hidden = true;
            ayudaGrafica.hidden = true;
            estado.textContent = indicacion;
            return;
        }
        const limites = intervalo();
        if (!limites) {
            grafica.hidden = true;
            ayudaGrafica.hidden = true;
            estado.textContent = "Para visualizar, elige un extremo a menor que b, ambos finitos.";
            return;
        }
        estado.textContent = "Preparando vista previa…";
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
        const deEstaFuncion = registros.filter(r => r.clave === datos.clave);
        if (deEstaFuncion.length < 2) {
            const mensaje = document.createElement("p");
            mensaje.textContent = "Ya tienes un cálculo de esta función. Puedes cambiar los extremos a y b y volver a calcular. Si el nuevo intervalo es válido, aquí podrás comparar las aproximaciones y cuántas iteraciones necesitó cada una.";
            contenedor.replaceChildren(mensaje);
            return;
        }
        const tabla = document.createElement("table");
        tabla.setAttribute("data-biseccion-grupo", "");
        tabla.className = "procedure-table";
        function valor(x) {
            const nodo = document.createElement("span");
            nodo.dataset.biseccionNumero = String(x);
            nodo.title = `Valor almacenado: ${x}`;
            nodo.textContent = String(x);
            return nodo;
        }
        const caption = tabla.createCaption();
        caption.textContent = "Resultados de esta función en la pestaña actual";
        const cabecera = tabla.createTHead().insertRow();
        ["Intervalo inicial", "Aproximación", "Iteraciones", "Comparación con el actual"].forEach(t => {
            const th = document.createElement("th"); th.scope = "col"; th.textContent = t; cabecera.append(th);
        });
        const cuerpo = tabla.createTBody();
        deEstaFuncion.forEach(r => {
            const misma = Math.max(r.a, actual.a) <= Math.min(r.b, actual.b);
            let texto = !r.convergio || !actual.convergio ? "Sin convergencia verificada"
                : misma ? "Compatible con la misma raíz" : "Intervalos finales distintos";
            if (r === actual) texto = r.convergio ? "Actual" : "Actual · Sin convergencia verificada";
            const fila = cuerpo.insertRow();
            fila.insertCell().append("[", valor(r.inicial_a), "; ", valor(r.inicial_b), "]");
            fila.insertCell().append(valor(r.c));
            fila.insertCell().textContent = String(r.iteraciones);
            fila.insertCell().textContent = texto;
        });
        contenedor.replaceChildren(tabla);
    }

    async function iniciar() {
        if (!window.Plotly) {
            throw new Error("No se pudo cargar la gráfica local. El resultado y la tabla siguen disponibles.");
        }
        const limites = intervalo();
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
            if (mutando || grafica.hidden) return;
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
        if (pasos.length) mostrarPaso(Number(slider.value));
        else if (resultado) Plotly.restyle(grafica, { x: [[resultado.c]], y: [[resultado.fc]], text: [["c"]] }, [1]);
    }
    ["funcion", "a", "b"].forEach(n => campo(n).addEventListener("input", previsualizar));
    slider?.addEventListener("input", () => mostrarPaso(Number(slider.value)));
    filas.forEach(fila => {
        ["pointerenter", "focus", "click"].forEach(tipo => fila.addEventListener(tipo, () => mostrarPaso(Number(fila.dataset.iteracion))));
    });
    comparar();
    presentarNumeros();
    if (pasos.length) mostrarPaso(pasos.length);
    previsualizar();
})();
