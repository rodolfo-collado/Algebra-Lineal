/* Gráfica, extremos, lectura decimal, reproducción e historial que comparten los métodos de raíces.
   La explicación de cada iteración la aporta el método en window.metodosRaices; aquí solo se
   recorren los datos ya calculados: avanzar, retroceder o reproducir nunca vuelve a calcular. */
(() => {
    "use strict";
    const form = document.getElementById("raices-form");
    const grafica = document.getElementById("raices-grafica");
    if (!form || !grafica) return;
    const datos = JSON.parse(document.getElementById("datos-raices").textContent);
    const metodo = window.metodosRaices[datos.metodo];
    const extremos = metodo.extremos || ["a", "b"];
    const resultado = datos.resultado;
    const pasos = resultado?.iteraciones || [];
    const resumen = resultado?.residuo != null && resultado.clasificacion !== "no_aplicable" ? metodo.resumen(resultado) : null;
    const $ = id => document.getElementById(id);
    const estado = $("grafica-estado");
    const seleccion = $("grafica-seleccion");
    const ayudaGrafica = $("grafica-ayuda");
    const derivada = $("raices-derivada");
    const slider = $("iteracion-raices");
    const contador = $("iteracion-contador");
    const anterior = $("iteracion-anterior");
    const siguiente = $("iteracion-siguiente");
    const reproducir = $("iteracion-reproducir");
    const velocidad = $("iteracion-velocidad");
    const breve = $("paso-breve");
    const marcoTabla = $("raices-tabla-marco");
    const elegir = [...document.querySelectorAll("[data-elegir-extremo]")];
    const filas = [...document.querySelectorAll("[data-iteracion]")];
    // Punto decimal y sin separador de miles, como las tablas y el resultado.
    const numero = (x, digitos = 12) => Number(x).toLocaleString("en-US", { maximumSignificantDigits: digitos, useGrouping: false });
    // En la gráfica: «=» si las cifras mostradas son el valor de la muestra; si no, «≈».
    const etiqueta = (x, digitos) => x === null ? "" : `${Number(x.toPrecision(digitos)) === x ? "=" : "≈"} ${Number(x.toPrecision(digitos))}`;
    const etiquetas = (xs, ys, digitos) => xs.map((x, i) => [etiqueta(x, digitos), etiqueta(ys[i], digitos)]);
    const campo = nombre => form.elements.namedItem(nombre);
    const color = nombre => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
    const valido = r => Array.isArray(r) && r.every(Number.isFinite) && r[0] < r[1];
    let mutando = false, temporizador, peticion, inicializacion, generacion = 0, extremoElegido = null;
    let actual = 0, reloj = null;
    const vistaInicial = [-10, 10];
    const indicacion = metodo.indicacion || "Introduce una función para visualizar su gráfica y elegir un intervalo.";
    ayudaGrafica.hidden = true;

    // Un intervalo con un cuarto de margen a cada lado; Newton aporta su propio encuadre de la tangente.
    function ampliar(a, b) {
        const margen = Math.max((b - a) / 4, Math.abs(a) * 1e-8, 1e-8);
        return [a - margen, b + margen];
    }
    const vistaPaso = p => metodo.vista ? metodo.vista(p) : ampliar(p.a, p.b);
    function vistaEntrada() {
        if (extremos.length === 2) {
            const a = extremo("a"), b = extremo("b");
            return a !== null && b !== null && a < b ? ampliar(a, b) : null;
        }
        const x0 = extremo("x0");
        if (x0 === null) return null;
        const ancho = Math.max(2, Math.abs(x0) * .25);
        return [x0 - ancho, x0 + ancho];
    }
    const anchoInicial = datos.inicial_b - datos.inicial_a;
    const vistaCalculo = !resultado ? null : pasos.length ? vistaPaso(pasos[0])
        : [datos.inicial_a - anchoInicial / 4, datos.inicial_b + anchoInicial / 4];

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
        const controles = $("raices-formato");
        if (!controles) return;
        const selector = $("raices-decimales");
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
        extremos.forEach((nombre, i) => {
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

    // Franja 2: intervalo de la iteración; franja 3, más intensa: el que se conserva después.
    function franja(opacidad) {
        return { type: "rect", x0: 0, x1: 0, y0: 0, y1: 1, yref: "paper", editable: false,
            fillcolor: color("--color-brand"), opacity: opacidad, line: { width: 0 }, layer: "below",
            visible: extremos.length === 2 && pasos.length > 0 };
    }

    // ---- Recorrido: una sola fuente de verdad (actual) para tabla, gráfica y explicación. ----
    function desplazarFila(fila) {
        // Solo el marco de la tabla se desplaza; la página queda donde la dejó el usuario.
        if (!marcoTabla) return;
        const rf = fila.getBoundingClientRect(), rm = marcoTabla.getBoundingClientRect();
        const cabecera = marcoTabla.querySelector("thead")?.getBoundingClientRect().height || 0;
        if (rf.top < rm.top + cabecera) marcoTabla.scrollTop -= rm.top + cabecera - rf.top;
        else if (rf.bottom > rm.bottom) marcoTabla.scrollTop += rf.bottom - rm.bottom;
    }

    function mostrarPaso(i, { enfocarFila = false } = {}) {
        i = Math.min(Math.max(i, 1), pasos.length);
        const p = pasos[i - 1];
        if (!p) return;
        actual = i;
        slider.value = String(i);
        contador.textContent = `${i} / ${pasos.length}`;
        anterior.disabled = i === 1;
        siguiente.disabled = i === pasos.length;
        const paso = metodo.paso(p, { formato, numero, signo }, { ultimo: i === pasos.length, resultado });
        slider.setAttribute("aria-valuetext", `Iteración ${i} de ${pasos.length}, ${paso.aria}`);
        $("paso-titulo").textContent = `Iteración ${i} de ${pasos.length}`;
        breve.replaceChildren(...paso.breve.map((texto, k) => {
            const nodo = document.createElement("p");
            nodo.textContent = texto;
            if (k === paso.breve.length - 1) nodo.className = "raices-paso-cierre";
            return nodo;
        }));
        for (const nombre of ["valores", "signos", "decision", "intervalo", "error", "parada"]) {
            const nodo = $(`paso-${nombre}`);
            if (!nodo) continue;
            const contenido = paso[nombre];
            if (Array.isArray(contenido)) nodo.replaceChildren(...contenido.map(texto => {
                const item = document.createElement("li"); item.textContent = texto; return item;
            }));
            else nodo.textContent = contenido || "";
            nodo.hidden = !contenido;
        }
        for (const fila of filas) {
            const activa = Number(fila.dataset.iteracion) === i;
            fila.toggleAttribute("data-activa", activa);
            fila.tabIndex = activa ? 0 : -1;
            if (activa) {
                fila.setAttribute("aria-current", "step");
                desplazarFila(fila);
                if (enfocarFila) fila.focus({ preventScroll: true });
            } else fila.removeAttribute("aria-current");
        }
        if (!grafica.data) return;
        const { puntos, trazo } = paso;
        mutando = true;
        // Los puntos de la iteración van en la traza 1; la construcción auxiliar, en la 2.
        // Solo cambian datos y franjas: los ejes respetan el zoom que haya elegido el usuario.
        Plotly.restyle(grafica, { x: [trazo?.x || []], y: [trazo?.y || []], text: [trazo?.text || []],
            "marker.size": [trazo?.size || []], textposition: trazo?.posicion || "top center" }, [2]);
        Plotly.update(grafica, { x: [puntos.x], y: [puntos.y], text: [puntos.text],
            customdata: [etiquetas(puntos.x, puntos.y, 12)], "marker.size": [puntos.size], "marker.symbol": [puntos.symbol] },
            extremos.length === 2 ? { "shapes[2].x0": p.a, "shapes[2].x1": p.b,
                "shapes[3].x0": p.nuevo_a ?? p.a, "shapes[3].x1": p.nuevo_b ?? p.b } : {}, [1])
            .finally(() => { mutando = false; });
    }

    const INTERVALO_MS = 1400;
    function pausar() {
        if (!reproducir) return;
        clearTimeout(reloj);
        reloj = null;
        reproducir.removeAttribute("data-reproduciendo");
        reproducir.setAttribute("aria-label", "Reproducir");
        reproducir.title = "Reproducir";
        // Mientras se reproduce no se anuncia cada paso; en pausa, la explicación vuelve a leerse.
        breve.setAttribute("aria-live", "polite");
    }
    function programar() {
        clearTimeout(reloj);
        reloj = setTimeout(() => {
            mostrarPaso(actual + 1);
            if (actual >= pasos.length) pausar(); else programar();
        }, INTERVALO_MS / Number(velocidad.value));
    }
    function alternarReproduccion() {
        if (reloj) return pausar();
        if (actual >= pasos.length) mostrarPaso(1);
        reproducir.setAttribute("data-reproduciendo", "");
        reproducir.setAttribute("aria-label", "Pausar");
        reproducir.title = "Pausar";
        breve.setAttribute("aria-live", "off");
        programar();
    }
    const irA = (i, opciones) => { pausar(); mostrarPaso(i, opciones); };

    // ---- Gráfica ----
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
            if ("derivada" in puntos) mostrarDerivada(puntos.derivada);
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
            const dominio = puntos.y.some(y => y === null)
                ? "La curva tiene huecos donde no se pudo verificar el dominio."
                : metodo.comprobacion || "Gráfica muestreada. Resolver comprueba dominio y cambio de signo del intervalo.";
            const hallazgo = puntos.clasificacion === "indicios_numericos"
                ? "El muestreo encontró indicios numéricos de raíces."
                : "El muestreo no detectó raíces; esto no es concluyente.";
            estado.textContent = dominio + " " + hallazgo;
        } catch (error) {
            if (error.name !== "AbortError" && n === generacion) {
                grafica.hidden = true;
                ayudaGrafica.hidden = true;
                seleccion.hidden = true;
                estado.textContent = error.message || "No se pudo actualizar la gráfica.";
                mostrarDerivada(undefined);
            }
        }
    }

    // f′(x) llega con las muestras: sin peticiones extra ni un segundo motor simbólico en el navegador.
    function mostrarDerivada(texto, vacia = false) {
        if (!derivada) return;
        derivada.toggleAttribute("data-pendiente", !texto);
        if (texto) {
            const expresion = document.createElement("span");
            expresion.className = "raices-expresion";
            expresion.textContent = texto;
            derivada.replaceChildren("f′(x) = ", expresion);
        } else derivada.textContent = vacia ? "" : texto === null
            ? "f′(x): esta expresión no se puede derivar con las reglas disponibles."
            : "f′(x) aparecerá cuando f(x) esté completa.";
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
            mostrarDerivada(undefined, true);
            return;
        }
        estado.textContent = "Preparando vista previa…";
        derivada?.setAttribute("data-pendiente", "");
        const rango = grafica.layout?.xaxis?.range || (valido(vistaCalculo) ? vistaCalculo : vistaInicial);
        temporizador = setTimeout(() => muestrear(rango, !grafica.data), 300);
    }

    async function iniciar() {
        if (!window.Plotly) {
            throw new Error("No se pudo cargar la gráfica local. El resultado y la tabla siguen disponibles.");
        }
        const layout = {
            margin: { t: 24, r: 16, b: 44, l: 56 }, showlegend: false,
            paper_bgcolor: color("--color-surface"), plot_bgcolor: color("--color-surface"),
            font: { family: "Segoe UI, sans-serif", color: color("--color-text") },
            xaxis: { title: { text: "x" }, range: vistaInicial, gridcolor: color("--color-border"), zerolinecolor: color("--color-muted") },
            yaxis: { title: { text: "f(x)" }, gridcolor: color("--color-border"), zerolinecolor: color("--color-muted") },
            shapes: [{ ...linea(extremo(extremos[0]) ?? 0, extremos[0]), visible: extremo(extremos[0]) !== null },
                { ...linea(extremos.length === 2 ? extremo("b") ?? 0 : 0, "b"), visible: extremos.length === 2 && extremo("b") !== null },
                franja(.1), franja(.22)],
            dragmode: "pan",
            separators: ". ", // punto decimal también en los ejes; los textos siguen en español
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
        ], layout, { responsive: true, locale: "es", displaylogo: false, scrollZoom: true,
            edits: { shapePosition: true },
            // Acercar y alejar sin rueda; «Vista inicial» y «Enfocar» sustituyen al reinicio de Plotly.
            modeBarButtons: [["zoomIn2d", "zoomOut2d"]] });
        grafica.on("plotly_relayout", cambio => {
            if (mutando || grafica.hidden) return;
            let cambioExtremos = false;
            extremos.forEach((nombre, i) => {
                const x = cambio[`shapes[${i}].x0`] ?? cambio[`shapes[${i}].x1`] ?? cambio.shapes?.[i]?.x0;
                if (!Number.isFinite(x)) return;
                campo(nombre).value = String(x);
                campo(nombre).dispatchEvent(new Event("input", { bubbles: true }));
                cambioExtremos = true;
            });
            if (cambioExtremos) return;
            const rango = cambio["xaxis.range"] || (cambio["xaxis.range[0]"] !== undefined
                ? [cambio["xaxis.range[0]"], cambio["xaxis.range[1]"]] : null);
            if (valido(rango)) {
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
            estado.textContent = "Punto seleccionado. Puedes arrastrar su línea o ajustar el valor en el formulario.";
        });
        new MutationObserver(() => {
            Plotly.relayout(grafica, { paper_bgcolor: color("--color-surface"), plot_bgcolor: color("--color-surface"),
                "font.color": color("--color-text"), "xaxis.gridcolor": color("--color-border"),
                "yaxis.gridcolor": color("--color-border"), "xaxis.zerolinecolor": color("--color-muted"),
                "yaxis.zerolinecolor": color("--color-muted"), "shapes[0].line.color": color("--color-brand"),
                "shapes[1].line.color": color("--color-brand"), "shapes[2].fillcolor": color("--color-brand"),
                "shapes[3].fillcolor": color("--color-brand"),
                "shapes[0].label.font.color": color("--color-text"), "shapes[1].label.font.color": color("--color-text") });
            Plotly.restyle(grafica, { "line.color": color("--color-brand") }, [0]);
            Plotly.restyle(grafica, { "marker.color": color("--color-text") }, [1]);
            Plotly.restyle(grafica, { "line.color": color("--color-warning"), "marker.color": color("--color-warning"),
                "textfont.color": color("--color-text") }, [2]);
        }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "data-estilo"] });
        if (pasos.length) mostrarPaso(actual || 1);
        else if (resumen) Plotly.restyle(grafica, { x: [[resumen.x]], y: [[resumen.fx]], text: [[resumen.nombre]],
            customdata: [etiquetas([resumen.x], [resumen.fx], 12)] }, [1]);
    }

    // Rueda sobre la gráfica = zoom. Si la rueda ya venía desplazando la página y la gráfica
    // pasa bajo el cursor, la página sigue desplazándose en lugar de atrapar el gesto.
    let ruedaFuera = -Infinity;
    window.addEventListener("wheel", e => { if (!grafica.contains(e.target)) ruedaFuera = e.timeStamp; }, { capture: true, passive: true });
    grafica.addEventListener("wheel", e => {
        if (e.timeStamp - ruedaFuera < 450) { ruedaFuera = e.timeStamp; e.stopPropagation(); }
    }, { capture: true, passive: true });

    // ---- Historial de la sesión: un método por clave y agrupado por función equivalente. ----
    function historial() {
        const seccion = $("raices-historial");
        if (!seccion || !resultado) return;
        const clave = `pygebra-raices-historial-${datos.metodo}`;
        const parametros = extremos.length === 2 ? { a: datos.inicial_a, b: datos.inicial_b } : { x0: resultado.x0 };
        const ajustes = { precision: resultado.precision ?? resultado.tolerancia, max_iteraciones: resultado.max_iteraciones };
        const actualRegistro = { id: JSON.stringify([datos.clave, parametros, ajustes]), clave: datos.clave,
            funcion: datos.funcion, parametros, ajustes, clasificacion: resultado.clasificacion,
            x: resumen?.x ?? null, iteraciones: pasos.length, residuo: resultado.residuo };
        let registros = [];
        try {
            const guardados = JSON.parse(sessionStorage.getItem(clave) || "[]");
            if (Array.isArray(guardados)) registros = guardados.filter(r => r && typeof r.id === "string"
                && typeof r.funcion === "string" && Object.values(r.parametros || {}).every(Number.isFinite));
        } catch { /* Sin almacenamiento, el historial empieza en este cálculo. */ }
        // Volver a una ejecución no la duplica: conserva su lugar y pasa a ser la actual.
        const previo = registros.findIndex(r => r.id === actualRegistro.id);
        if (previo >= 0) registros[previo] = actualRegistro; else registros.push(actualRegistro);
        registros = registros.slice(-12);
        try { sessionStorage.setItem(clave, JSON.stringify(registros)); } catch { /* Solo esta página. */ }
        if (registros.length < 2) return;

        const ESTADOS = { raiz_aproximada: "Raíz aproximada", sin_convergencia: "Sin convergencia",
            no_aplicable: "No aplicable", sin_raices_demostrado: "Sin raíces (demostrado)" };
        const valor = x => {
            if (x === null || x === undefined) return "—";
            const nodo = document.createElement("span");
            nodo.dataset.raicesNumero = String(x);
            nodo.title = `Valor almacenado: ${x}`;
            nodo.textContent = String(x);
            return nodo;
        };
        const tabla = document.createElement("table");
        tabla.className = "procedure-table raices-historial-tabla";
        const leyenda = tabla.createCaption();
        leyenda.className = "sr-only"; // El encabezado visible de la sección ya la nombra.
        leyenda.textContent = "Ejecuciones de esta sesión";
        const cabecera = tabla.createTHead().insertRow();
        [extremos.length === 2 ? "Intervalo inicial" : "x₀", "Estado", "Aproximación", "Iteraciones", "Residuo", ""].forEach(texto => {
            const th = document.createElement("th"); th.scope = "col"; th.textContent = texto; cabecera.append(th);
        });
        for (const funcionClave of new Set(registros.map(r => r.clave))) {
            const grupo = registros.filter(r => r.clave === funcionClave);
            const cuerpo = tabla.createTBody();
            const titulo = document.createElement("th");
            titulo.scope = "rowgroup"; titulo.colSpan = 6;
            titulo.textContent = `f(x) = ${grupo.at(-1).funcion}`;
            cuerpo.insertRow().append(titulo);
            for (const r of grupo) {
                const fila = cuerpo.insertRow();
                const p = r.parametros;
                fila.insertCell().append(...("x0" in p ? [valor(p.x0)] : ["[", valor(p.a), "; ", valor(p.b), "]"]));
                fila.insertCell().textContent = ESTADOS[r.clasificacion] || r.clasificacion;
                fila.insertCell().append(valor(r.x));
                fila.insertCell().textContent = String(r.iteraciones);
                fila.insertCell().append(valor(r.residuo));
                const accion = fila.insertCell();
                if (r.id === actualRegistro.id) {
                    fila.setAttribute("aria-current", "true");
                    accion.textContent = "Actual";
                    continue;
                }
                const ver = document.createElement("button");
                ver.type = "button";
                ver.className = "btn btn-secondary";
                ver.textContent = "Ver";
                ver.setAttribute("aria-label", `Ver la ejecución con ${"x0" in p ? `x₀ = ${p.x0}` : `[${p.a}; ${p.b}]`}`);
                ver.addEventListener("click", () => {
                    pausar();
                    for (const [nombre, dato] of Object.entries({ funcion: r.funcion, ...p, ...r.ajustes })) {
                        if (campo(nombre)) campo(nombre).value = String(dato);
                    }
                    form.requestSubmit();
                });
                accion.append(ver);
            }
        }
        $("raices-historial-tabla").replaceChildren(tabla);
        seccion.hidden = false;
    }

    // ---- Eventos ----
    campo("funcion").addEventListener("input", previsualizar);
    extremos.forEach(n => campo(n).addEventListener("input", sincronizarExtremos));
    elegir.forEach(boton => boton.addEventListener("click", () => {
        extremoElegido = extremoElegido === boton.dataset.elegirExtremo ? null : boton.dataset.elegirExtremo;
        elegir.forEach(b => b.setAttribute("aria-pressed", String(b.dataset.elegirExtremo === extremoElegido)));
        estado.textContent = extremoElegido ? `Pulsa sobre la curva para elegir ${extremoElegido}. También puedes escribirlo en el formulario.` : "Selección cancelada.";
    }));
    $("grafica-restablecer").addEventListener("click", () => muestrear(vistaInicial, true));
    $("grafica-enfocar").addEventListener("click", () => {
        const rango = pasos.length ? vistaPaso(pasos[actual - 1]) : vistaEntrada();
        if (valido(rango)) muestrear(rango, true);
        else estado.textContent = extremos.length === 2 ? "Escribe a y b, con a < b, para enfocar su intervalo." : "Escribe x₀ para enfocar su entorno.";
    });
    if (pasos.length) {
        slider.closest(".raices-recorrido").hidden = false;
        slider.addEventListener("input", () => irA(Number(slider.value)));
        anterior.addEventListener("click", () => irA(actual - 1));
        siguiente.addEventListener("click", () => irA(actual + 1));
        $("iteracion-reiniciar").addEventListener("click", () => irA(1));
        reproducir.addEventListener("click", alternarReproduccion);
        velocidad.addEventListener("change", () => { if (reloj) programar(); });
        filas.forEach(fila => {
            const i = Number(fila.dataset.iteracion);
            fila.addEventListener("click", () => irA(i, { enfocarFila: true }));
            fila.addEventListener("focus", () => { if (actual !== i) irA(i); });
            fila.addEventListener("keydown", evento => {
                const destino = { ArrowDown: i + 1, ArrowUp: i - 1, Home: 1, End: pasos.length,
                    PageDown: i + 5, PageUp: i - 5 }[evento.key];
                if (destino === undefined) return;
                evento.preventDefault();
                irA(destino, { enfocarFila: true });
            });
        });
        // La reproducción nunca sigue sola al cambiar de cálculo, de página o de pestaña.
        form.addEventListener("input", pausar);
        form.addEventListener("submit", pausar);
        window.addEventListener("pagehide", pausar);
        document.addEventListener("visibilitychange", () => { if (document.hidden) pausar(); });
        mostrarPaso(1);
    }
    historial();
    presentarNumeros();
    previsualizar();
})();
