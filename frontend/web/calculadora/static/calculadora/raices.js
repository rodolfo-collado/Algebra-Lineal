/* Gráfica, extremos, lectura decimal y recorrido que comparten los métodos de raíces.
   La explicación de cada iteración la aporta el método en window.metodosRaices. */
(() => {
    "use strict";
    const form = document.getElementById("raices-form");
    const grafica = document.getElementById("raices-grafica");
    if (!form || !grafica) return;
    const datos = JSON.parse(document.getElementById("datos-raices").textContent);
    const metodo = window.metodosRaices[datos.metodo];
    const resultado = datos.resultado;
    const pasos = resultado?.iteraciones || [];
    const resumen = resultado ? metodo.resumen(resultado) : null;
    const estado = document.getElementById("grafica-estado");
    const slider = document.getElementById("iteracion-raices");
    const lectura = document.getElementById("iteracion-lectura");
    const anterior = document.getElementById("iteracion-anterior");
    const siguiente = document.getElementById("iteracion-siguiente");
    const detallesPaso = document.getElementById("paso-detalles");
    if (detallesPaso) detallesPaso.open = window.matchMedia("(min-width: 768px)").matches;
    const seleccion = document.getElementById("grafica-seleccion");
    const elegir = [...document.querySelectorAll("[data-elegir-extremo]")];
    const filas = [...document.querySelectorAll("[data-iteracion]")];
    // Punto decimal y sin separador de miles, como las tablas y el resultado.
    const numero = (x, digitos = 12) => Number(x).toLocaleString("en-US", { maximumSignificantDigits: digitos, useGrouping: false });
    // En la gráfica: «=» si las cifras mostradas son el valor de la muestra; si no, «≈».
    const etiqueta = (x, digitos) => x === null ? "" : `${Number(x.toPrecision(digitos)) === x ? "=" : "≈"} ${Number(x.toPrecision(digitos))}`;
    const etiquetas = (xs, ys, digitos) => xs.map((x, i) => [etiqueta(x, digitos), etiqueta(ys[i], digitos)]);
    const campo = nombre => form.elements.namedItem(nombre);
    const color = nombre => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
    let mutando = false, temporizador, peticion, inicializacion, generacion = 0, extremoElegido = null;
    const vistaInicial = [-10, 10];
    const anchoInicial = datos.inicial_b - datos.inicial_a;
    const vistaCalculo = resultado ? [datos.inicial_a - anchoInicial / 4, datos.inicial_b + anchoInicial / 4] : null;
    const ayudaGrafica = document.getElementById("grafica-ayuda");
    const indicacion = "Introduce una función para visualizar su gráfica y elegir un intervalo.";
    ayudaGrafica.hidden = true;

    // Cifras suficientes para que valores distintos no se lean como iguales.
    function formato(valores, digitos = 8) {
        const distintos = new Set(valores);
        while (digitos < 17 && new Set([...distintos].map(x => numero(x, digitos))).size < distintos.size) digitos++;
        // «=» solo si las cifras mostradas son el valor almacenado; si no, «≈».
        return { n: x => numero(x, digitos),
            r: x => `${Number(x.toPrecision(digitos)) === x ? "=" : "≈"} ${numero(x, digitos)}` };
    }
    const signo = x => x > 0 ? "positivo" : x < 0 ? "negativo" : "cero";

    function presentarNumeros() {
        const controles = document.getElementById("raices-formato");
        if (!controles) return;
        const selector = document.getElementById("raices-decimales");
        const grupos = [...document.querySelectorAll("[data-raices-grupo]")].map(grupo =>
            [...grupo.querySelectorAll("[data-raices-numero]")].map(nodo => ({ nodo, valor: Number(nodo.dataset.raicesNumero) })));
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
                    // Tras un «=» escrito, el redondeo cambia ese signo por «≈» en vez de sumar otro.
                    const relacion = d.nodo.previousElementSibling?.matches("[data-raices-relacion]") ? d.nodo.previousElementSibling : null;
                    if (relacion) relacion.textContent = aproximado ? "≈" : "=";
                    d.nodo.textContent = (aproximado && !relacion && !d.nodo.closest(".raices-raiz") ? "≈ " : "") + texto;
                    d.nodo.setAttribute("aria-label", aproximado ? `${texto}, redondeado; valor almacenado ${d.valor}` : texto);
                });
            }
        }
        controles.hidden = false;
        selector.addEventListener("change", aplicar);
        aplicar();
    }

    function extremo(nombre) {
        return campo(nombre).value.trim() && Number.isFinite(Number(campo(nombre).value)) ? Number(campo(nombre).value) : null;
    }

    function sincronizarExtremos() {
        if (!grafica.data) return;
        const cambios = {};
        ["a", "b"].forEach((nombre, i) => {
            const x = extremo(nombre);
            cambios[`shapes[${i}].visible`] = x !== null;
            cambios[`shapes[${i}].x0`] = cambios[`shapes[${i}].x1`] = x ?? 0;
            cambios[`shapes[${i}].y0`] = 0;
            cambios[`shapes[${i}].y1`] = 1;
        });
        mutando = true;
        return Plotly.relayout(grafica, cambios).finally(() => { mutando = false; });
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
        slider.closest(".raices-recorrido").hidden = false;
        slider.value = String(i);
        anterior.disabled = i === 1;
        siguiente.disabled = i === pasos.length;
        const paso = metodo.paso(p, { formato, numero, signo }, { ultimo: i === pasos.length, resultado });
        slider.setAttribute("aria-valuetext", `Iteración ${i} de ${pasos.length}, ${paso.aria}`);
        lectura.querySelector("#paso-titulo").textContent = `Iteración ${i} de ${pasos.length}`;
        detallesPaso.querySelector("#paso-valores").textContent = paso.valores;
        detallesPaso.querySelector("#paso-signos").textContent = paso.signos;
        lectura.querySelector("#paso-decision").textContent = paso.decision;
        lectura.querySelector("#paso-intervalo").textContent = paso.intervalo;
        const parada = lectura.querySelector("#paso-parada");
        parada.textContent = paso.parada || "";
        parada.hidden = !paso.parada;
        filas.forEach(f => f.toggleAttribute("data-activa", Number(f.dataset.iteracion) === i));
        if (!grafica.data) return;
        const { puntos, trazo } = paso;
        mutando = true;
        // Los puntos de la iteración van en la traza 1; la construcción auxiliar (secante), en la 2.
        Plotly.restyle(grafica, { x: [trazo?.x || []], y: [trazo?.y || []], text: [trazo?.text || []],
            "marker.size": [trazo?.size || []], textposition: trazo?.posicion || "top center" }, [2]);
        Plotly.update(grafica, { x: [puntos.x], y: [puntos.y], text: [puntos.text],
            customdata: [etiquetas(puntos.x, puntos.y, 12)], "marker.size": [puntos.size], "marker.symbol": [puntos.symbol] },
            { "shapes[2].x0": p.a, "shapes[2].x1": p.b }, [1])
            .finally(() => { mutando = false; });
    }

    async function muestrear(rango, moverEjes = false) {
        clearTimeout(temporizador);
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
            await Plotly.restyle(grafica, { x: [puntos.x], y: [puntos.y], customdata: [etiquetas(puntos.x, puntos.y, 10)] }, [0]);
            if (n !== generacion) return;
            if (moverEjes) {
                mutando = true;
                await Plotly.relayout(grafica, { "xaxis.range": rango, "yaxis.autorange": true });
                mutando = false;
                if (n !== generacion) return;
            }
            await sincronizarExtremos();
            if (n !== generacion) return;
            seleccion.hidden = false;
            estado.textContent = puntos.y.some(y => y === null)
                ? "La curva tiene huecos donde no se pudo verificar el dominio. La gráfica es un muestreo, no una prueba de raíces."
                : "Gráfica muestreada. Resolver comprueba dominio y cambio de signo del intervalo.";
        } catch (error) {
            if (error.name !== "AbortError" && n === generacion) {
                grafica.hidden = true;
                ayudaGrafica.hidden = true;
                seleccion.hidden = true;
                estado.textContent = error.message || "No se pudo actualizar la gráfica.";
            }
        }
    }

    function previsualizar() {
        clearTimeout(temporizador);
        // Invalidar también durante la espera evita pintar una respuesta de la entrada anterior.
        generacion++;
        peticion?.abort();
        if (!campo("funcion").value.trim()) {
            grafica.hidden = true;
            ayudaGrafica.hidden = true;
            seleccion.hidden = true;
            estado.textContent = indicacion;
            return;
        }
        estado.textContent = "Preparando vista previa…";
        const rango = grafica.layout?.xaxis?.range || (vistaCalculo?.every(Number.isFinite) ? vistaCalculo : vistaInicial);
        temporizador = setTimeout(() => muestrear(rango, !grafica.data), 300);
    }

    function comparar() {
        const contenedor = document.getElementById("raices-comparaciones");
        if (!contenedor || !resultado) return;
        const clave = `pygebra-${datos.metodo}-v1`;
        let anteriores = [];
        try {
            const guardados = JSON.parse(sessionStorage.getItem(clave) || "[]");
            if (Array.isArray(guardados)) anteriores = guardados.filter(r => r && typeof r.clave === "string" &&
                [r.a, r.b, r.c, r.inicial_a, r.inicial_b, r.iteraciones].every(Number.isFinite)).slice(-9);
        } catch { /* La comparación actual sigue disponible si el almacenamiento está desactivado. */ }
        // [a, b] es el intervalo donde cada cálculo localiza su raíz; c, la aproximación.
        const actual = { clave: datos.clave, a: resumen.certeza[0], b: resumen.certeza[1], c: resumen.x,
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
        tabla.setAttribute("data-raices-grupo", "");
        tabla.className = "procedure-table";
        function valor(x) {
            const nodo = document.createElement("span");
            nodo.dataset.raicesNumero = String(x);
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
                : misma ? "Compatible con la misma raíz" : metodo.distintas;
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
        const layout = {
            margin: { t: 28, r: 18, b: 48, l: 60 }, showlegend: false,
            paper_bgcolor: color("--color-surface"), plot_bgcolor: color("--color-surface"),
            font: { family: "Segoe UI, sans-serif", color: color("--color-text") },
            xaxis: { title: { text: "x" }, range: vistaInicial, gridcolor: color("--color-border"), zerolinecolor: color("--color-muted") },
            yaxis: { title: { text: "f(x)" }, gridcolor: color("--color-border"), zerolinecolor: color("--color-muted") },
            shapes: [{ ...linea(extremo("a") ?? 0, "a"), visible: extremo("a") !== null },
                { ...linea(extremo("b") ?? 0, "b"), visible: extremo("b") !== null },
                { ...franja(0, 0), visible: pasos.length > 0 }],
            dragmode: "pan",
            separators: ". ", // punto decimal también en los ejes; los textos siguen en español
        };
        await Plotly.newPlot(grafica, [
            { x: [], y: [], type: "scatter", mode: "lines", connectgaps: false, name: "f(x)",
                line: { color: color("--color-brand"), width: 2 }, hovertemplate: "x %{customdata[0]}<br>f(x) %{customdata[1]}<extra></extra>" },
            { x: [], y: [], type: "scatter", mode: "markers", name: "Iteración",
                marker: { color: color("--color-text") },
                hovertemplate: "%{text}<br>x %{customdata[0]}<br>f(x) %{customdata[1]}<extra></extra>" },
            { x: [], y: [], type: "scatter", mode: "lines+markers+text", connectgaps: false, name: "Construcción",
                hoverinfo: "skip", cliponaxis: false, line: { color: color("--color-warning"), width: 2, dash: "dot" },
                marker: { symbol: "diamond", color: color("--color-warning") }, textfont: { color: color("--color-text") } },
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
        grafica.on("plotly_click", evento => {
            if (!extremoElegido) return;
            const punto = evento.points?.find(p => p.curveNumber === 0);
            if (!punto || !Number.isFinite(punto.x)) return;
            const input = campo(extremoElegido);
            input.value = String(punto.x);
            input.dispatchEvent(new Event("input", { bubbles: true }));
            extremoElegido = null;
            elegir.forEach(b => b.setAttribute("aria-pressed", "false"));
            estado.textContent = "Extremo seleccionado. Puedes arrastrar su línea o ajustar el valor en el formulario. Resolver validará el intervalo.";
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
            Plotly.restyle(grafica, { "line.color": color("--color-warning"), "marker.color": color("--color-warning"),
                "textfont.color": color("--color-text") }, [2]);
        }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "data-estilo"] });
        if (pasos.length) mostrarPaso(Number(slider.value));
        else if (resultado) Plotly.restyle(grafica, { x: [[resumen.x]], y: [[resumen.fx]], text: [[resumen.nombre]],
            customdata: [etiquetas([resumen.x], [resumen.fx], 12)] }, [1]);
    }
    campo("funcion").addEventListener("input", previsualizar);
    ["a", "b"].forEach(n => campo(n).addEventListener("input", sincronizarExtremos));
    elegir.forEach(boton => boton.addEventListener("click", () => {
        extremoElegido = extremoElegido === boton.dataset.elegirExtremo ? null : boton.dataset.elegirExtremo;
        elegir.forEach(b => b.setAttribute("aria-pressed", String(b.dataset.elegirExtremo === extremoElegido)));
        estado.textContent = extremoElegido ? `Pulsa sobre la curva para elegir ${extremoElegido}. También puedes escribirlo en el formulario.` : "Selección cancelada.";
    }));
    document.getElementById("grafica-restablecer").addEventListener("click", () => muestrear(vistaInicial, true));
    document.getElementById("grafica-intervalo")?.addEventListener("click", () => {
        muestrear(vistaCalculo.every(Number.isFinite) ? vistaCalculo : [datos.inicial_a, datos.inicial_b], true);
    });
    slider?.addEventListener("input", () => mostrarPaso(Number(slider.value)));
    anterior?.addEventListener("click", () => mostrarPaso(Number(slider.value) - 1));
    siguiente?.addEventListener("click", () => mostrarPaso(Number(slider.value) + 1));
    filas.forEach(fila => {
        ["pointerenter", "focus", "click"].forEach(tipo => fila.addEventListener(tipo, () => mostrarPaso(Number(fila.dataset.iteracion))));
    });
    comparar();
    presentarNumeros();
    if (pasos.length) mostrarPaso(pasos.length);
    previsualizar();
})();
