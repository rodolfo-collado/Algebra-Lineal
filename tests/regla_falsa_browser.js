/* Django y Plotly reales; sin sustituir el algoritmo ni el muestreo. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const ok = (valor, mensaje) => { if (!valor) throw new Error(mensaje); };
    const esperar = async (condicion, mensaje = "Espera agotada") => {
        const limite = Date.now() + 15000;
        while (!condicion()) {
            if (Date.now() > limite) throw new Error(mensaje);
            await new Promise(r => setTimeout(r, 40));
        }
    };
    const grafica = w => q(w, "#raices-grafica");
    const datos = w => JSON.parse(q(w, "#datos-raices").textContent).resultado;
    const lista = w => grafica(w)?.data?.[0]?.x?.length === 801 &&
        q(w, "#grafica-estado").textContent.startsWith("Gráfica muestreada");
    const valor = (w, nombre, texto) => {
        const campo = q(w, `[name="${nombre}"]`);
        campo.value = texto;
        campo.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const post = frame => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 15000);
        frame.onload = () => { clearTimeout(timer); resolve(frame.contentWindow); };
        q(frame.contentWindow, "[data-calculo]").click();
    });
    const resolver = async (frame, cambios = {}) => {
        const w = frame.contentWindow;
        for (const [n, v] of Object.entries({funcion: "x²-2", a: "1", b: "2", ...cambios})) valor(w, n, v);
        const nuevo = await post(frame);
        await esperar(() => lista(nuevo));
        return nuevo;
    };
    const final = w => {
        const s = q(w, "#iteracion-raices");
        s.value = s.max; s.dispatchEvent(new w.Event("input", {bubbles: true}));
    };
    const casos = [
        ["Vista previa sin extremos y selección de a/b", async w => {
            ok(!q(w, "#resultado") && grafica(w).hidden, "Empieza sin resultado ni curva");
            valor(w, "funcion", "x²-2");
            await esperar(() => lista(w));
            ok(grafica(w).data[0].x[0] === -10 && grafica(w).data[0].x.at(-1) === 10, "Ventana independiente");
            ok(!q(w, '[name="a"]').value && !q(w, '[name="b"]').value, "No inventa extremos");
            for (const [nombre, x] of [["a", 1], ["b", 2]]) {
                q(w, `[data-elegir-extremo="${nombre}"]`).click();
                grafica(w).emit("plotly_click", {points: [{curveNumber: 0, x}]});
                await esperar(() => Number(q(w, `[name="${nombre}"]`).value) === x);
            }
            ok(!q(w, "#resultado"), "Elegir extremos no resuelve");
            await w.Plotly.relayout(grafica(w), {"shapes[0].x0": .5, "shapes[0].x1": .5});
            await esperar(() => q(w, '[name="a"]').value === "0.5");
        }],
        ["Secante, corte y recorrido coinciden con cada fila sin peticiones", async (w, frame) => {
            w = await resolver(frame);
            const resultado = datos(w), g = grafica(w);
            ok([...w.document.querySelectorAll(".regla-falsa-paso h5")].map(n => n.textContent).join("|") ===
                "Aproximación|Signos|Actualización del intervalo|Error|Decisión", "Cinco bloques visibles");
            ok([...w.document.querySelectorAll(".raices-tabla thead th")].map(n => n.textContent).join("|") ===
                "i|a|b|xr|f(a)|f(b)|f(xr)|Error absoluto Ea|xr sustituye a", "Orden de columnas");
            for (const p of resultado.iteraciones) {
                const celdas = q(w, `[data-iteracion="${p.i}"]`).cells;
                const valores = [...celdas].slice(1, 7).map(c => Number(c.querySelector("[data-raices-numero]").dataset.raicesNumero));
                ok(JSON.stringify(valores) === JSON.stringify([p.a, p.b, p.xr, p.fa, p.fb, p.fxr]), "Mismos datos bajo cada encabezado");
            }

            let peticiones = 0;
            const fetchOriginal = w.fetch;
            w.fetch = (...args) => { peticiones++; return fetchOriginal(...args); };
            q(w, "#procedimiento-raices").open = true;
            for (const p of resultado.iteraciones) {
                q(w, `[data-iteracion="${p.i}"]`).focus();
                await esperar(() => g.data[1].x[1] === p.xr);
                ok(g.data[2].x[0] === p.a && g.data[2].x[1] === p.b && g.data[2].x[3] === p.xr, "Secante y corte");
                ok(q(w, "#paso-valores li").textContent.startsWith("xr "), "Aproximación breve");
                ok(q(w, "#paso-error").children.length === 2, "Ea y tolerancia separados");
                ok(g.data[2].y[0] === p.fa && g.data[2].y[1] === p.fb && g.data[2].y[3] === 0, "Alturas de la secante");
                ok(g.layout.shapes[2].x0 === p.a && g.layout.shapes[2].x1 === p.b, "Intervalo anterior");
                ok(g.layout.shapes[3].x0 === p.nuevo_a && g.layout.shapes[3].x1 === p.nuevo_b, "Intervalo actualizado");
                ok(q(w, "#paso-breve").textContent.includes("secante") && q(w, `[data-iteracion="${p.i}"]`).getAttribute("aria-current") === "step", "Paso breve y fila activa");
                ok(q(w, "#paso-decision").textContent.includes("xr sustituye al extremo a"), "Explica el signo");
                ok(q(w, "#iteracion-raices").getAttribute("aria-valuetext").includes("xr"), "Lectura accesible");
            }
            ok(q(w, "#iteracion-siguiente").disabled, "No sobrepasa última fila");
            q(w, "#iteracion-anterior").click();
            ok(Number(q(w, "#iteracion-raices").value) === resultado.iteraciones.length-1, "Anterior");
            const slider = q(w, "#iteracion-raices");
            slider.value = "1"; slider.dispatchEvent(new w.Event("input", {bubbles: true}));
            ok(q(w, "#iteracion-anterior").disabled, "Primera fila");
            ok(q(w, "#paso-error").textContent.includes("Ea no disponible"), "No inventa primer error");
            q(w, "#iteracion-siguiente").click();
            ok(slider.value === "2", "Siguiente");
            ok(peticiones === 0, "Recorrer no solicita muestras ni recalcula");
        }],
        ["La secante también sustituye b y distingue raíz exacta", async (w, frame) => {
            w = await resolver(frame, {funcion: "2-x²", a: "-2", b: "-1"});
            ok(q(w, "#paso-decision").textContent.includes("xr sustituye al extremo b"), "Sustituye b");
            w = await resolver(frame, {funcion: "x", a: "-1", b: "2"});
            ok(datos(w).estado === "exacta", "Raíz exacta");
            ok(q(w, "#paso-decision").textContent.includes("No hace falta sustituir"), "No inventa sustitución");
            w = await resolver(frame, {funcion: "x", a: "0", b: "2"});
            ok(!q(w, "#iteracion-raices") && grafica(w).data[1].x[0] === 0, "Extremo sin iteraciones");
        }],
        ["Ea pequeño sin confirmación no anuncia convergencia", async (w, frame) => {
            w = await resolver(frame, {funcion: "1e-200*(x^20-1)", a: "0"});
            final(w);
            const r = datos(w), texto = q(w, "#paso-parada").textContent;
            ok(r.estado === "estancamiento" && !r.convergio, "Sin convergencia");
            ok(texto.includes("tampoco descarta raíces") && texto.includes("máximo de iteraciones"), "Explica límite y signos");
            ok(!texto.includes("Continúa.") && !texto.includes("La raíz está más lejos"), "No promete continuar ni excluir raíces");
            ok(q(w, "#paso-intervalo").textContent.includes("200 iteraciones sin moverse"), "Extremo fijo");
        }],
        ["Máximo y límite de máquina terminan sin éxito falso", async (w, frame) => {
            for (const [cambios, estado, mensaje] of [
                [{max_iteraciones: "1"}, "limite", "máximo de iteraciones"],
                [{max_iteraciones: "200", precision: "1e-30"}, "maquina", "números de máquina"],
            ]) {
                w = await resolver(frame, cambios);
                final(w);
                ok(datos(w).estado === estado && !datos(w).convergio, "Estado correcto");
                ok(q(w, "#paso-breve").textContent.includes(mensaje), "La explicación breve también cierra sin éxito");
                ok(q(w, ".raices-cabecera").dataset.tono === "aviso", "Tono de aviso, no de error");
                ok(q(w, "#paso-parada").textContent.includes(mensaje), "Cierre del recorrido");
            }
        }],
        ["Teclado conserva cursor, superíndice, deshacer y foco", async w => {
            const f = q(w, '[name="funcion"]');
            f.focus();
            await esperar(() => q(w, ".math-keyboard").hasAttribute("data-abierto"));
            q(w, '[data-insercion="x²"]').click();
            ok(f.value === "x²" && w.document.activeElement === f, "Inserción y foco");
            valor(w, "funcion", "x"); f.setSelectionRange(1, 1);
            q(w, "[data-exponente-entero]").click();
            q(w, '[data-insercion="3"]').click();
            ok(f.value === "x³", "Exponente");
            w.document.execCommand("undo");
            ok(f.value === "x", "Deshacer nativo");
            q(w, '[name="a"]').focus();
            ok(!q(w, ".math-keyboard").hasAttribute("data-abierto"), "Teclado se oculta en extremo");
        }],
        ["Zoom, vista inicial e intervalo conservan cálculo y secante", async (w, frame) => {
            w = await resolver(frame);
            const original = JSON.stringify(datos(w)), g = grafica(w);
            await w.Plotly.relayout(g, {"xaxis.range": [1.3, 1.5]});
            await esperar(() => g.data[0].x[0] === 1.3);
            q(w, "#grafica-restablecer").click();
            await esperar(() => g.data[0].x[0] === -10 && g.layout.xaxis.range[0] === -10);
            q(w, "#grafica-enfocar").click();
            await esperar(() => g.layout.xaxis.range[0] === .75 && g.data[0].x[0] === .75);
            ok(JSON.stringify(datos(w)) === original && g.data[2].x.length === 5, "Mismo cálculo y secante");
        }],
        ["Estudio/Minimalista y día/noche colorean también la secante", async (w, frame) => {
            w = await resolver(frame);
            const raiz = w.document.documentElement, g = grafica(w);
            const token = nombre => w.getComputedStyle(raiz).getPropertyValue(nombre).trim();
            for (const estilo of ["estudio", "minimalista"]) for (const tema of ["light", "dark"]) {
                raiz.dataset.estilo = estilo; raiz.dataset.theme = tema;
                await esperar(() => g.data[2].line.color === token("--color-warning") &&
                    g.layout.paper_bgcolor === token("--color-surface") && g.data[0].line.color === token("--color-brand"));
                ok(g.data[2].marker.color === token("--color-warning"), "Corte visible con color del tema");
            }
        }],
        ["Decimales distinguen Ea y tolerancia sin alterar JSON", async (w, frame) => {
            w = await resolver(frame, {precision: "1e-12"});
            const original = q(w, "#datos-raices").textContent;
            const selector = q(w, "#raices-decimales");
            for (const precision of ["4", "16", "completa"]) {
                selector.value = precision; selector.dispatchEvent(new w.Event("change", {bubbles: true}));
                const numeros = [...w.document.querySelectorAll("[data-raices-numero]")];
                ok(numeros.every(n => Number(n.dataset.raicesNumero) === 0 || Number(n.textContent.replace("≈ ", "")) !== 0), "Sin ceros falsos");
                if (precision === "completa") ok(numeros.every(n => Number(n.textContent) === Number(n.dataset.raicesNumero)), "Valor completo");
            }
            ok(q(w, "#datos-raices").textContent === original, "JSON intacto");
        }],
        ["Historial de intervalos separado de Bisección, con estados y residuo", async (w, frame) => {
            w.sessionStorage.removeItem("pygebra-raices-historial-regla_falsa");
            w.sessionStorage.setItem("pygebra-raices-historial-biseccion", "[]");
            w = await resolver(frame);
            ok(q(w, "#raices-historial").hidden, "Una ejecución: sin historial");
            w = await resolver(frame, {a: "1.2", b: "1.6"});
            w = await resolver(frame, {a: "-2", b: "-1"});
            w = await resolver(frame, {max_iteraciones: "1"});
            const filas = [...w.document.querySelectorAll("#raices-historial tbody tr:not(:first-child)")];
            ok(!q(w, "#raices-historial").hidden && filas.length === 4, "Cuatro ejecuciones de la misma función");
            ok(filas[1].cells[0].textContent.replace(/\s/g, "") === "[1.2;1.6]", "Intervalo inicial");
            ok(filas[3].getAttribute("aria-current") === "true" && filas[3].cells[3].textContent === "No cumplido: máximo de iteraciones", "Actual sin convergencia");
            ok(filas[0].cells[3].textContent === "Cumplido" && filas[0].cells[6].textContent === "0.0001", "Criterio y tolerancia");
            ok([...q(w, "#raices-historial thead tr").cells].map(c => c.textContent).includes("Error absoluto"), "Error absoluto con su nombre");
            ok(filas.every(f => f.cells[5].querySelector("[data-raices-numero]")), "Residuo de cada ejecución");
            ok(w.sessionStorage.getItem("pygebra-raices-historial-biseccion") === "[]", "Bisección intacta");
        }],
        ["Mismo signo conserva la gráfica sin inventar una secante", async (w, frame) => {
            for (const [funcion, clasificacion] of [["x²+1", "sin_raices_demostrado"], ["x²", "no_aplicable"]]) {
                w = await resolver(frame, {funcion, a: "-1", b: "1"});
                ok(datos(w).clasificacion === clasificacion, "Distingue demostración y falta de aplicabilidad");
                ok(grafica(w).data[1].x.length === 0 && grafica(w).data[2].x.length === 0, "Sin candidato ni secante");
                ok(!q(w, "#iteracion-raices") && !q(w, "[data-respuesta-errores]"), "Sin recorrido ni error de entrada");
            }
        }],
        ["Intervalo no aplicable conserva entradas y explica el dominio", async (w, frame) => {
            valor(w, "funcion", "1/x"); valor(w, "a", "-1"); valor(w, "b", "1");
            w = await post(frame);
            ok(q(w, "#resultado") && !q(w, "[data-respuesta-errores]"), "Resultado informativo en discontinuidad");
            ok(datos(w).clasificacion === "no_aplicable" && datos(w).xr === null, "Sin aproximación en discontinuidad");
            ok(!q(w, "#iteracion-raices"), "Sin recorrido");
            ok(q(w, '[name="funcion"]').value === "1/x", "Conserva función");
            w = await resolver(frame);
            ok(datos(w).convergio, "Se recupera corrigiendo la función");
        }],
    ];
    let aprobados = 0;
    for (const [nombre, probar] of casos) {
        const item = document.createElement("li"); document.getElementById("resultados").append(item);
        (window.preferencias ? window.preferencias.guardar("pygebra-raices-decimales", "6") : localStorage.setItem("pygebra-raices-decimales", "6")); // Cada caso parte de 6 decimales.
        const frame = document.createElement("iframe"); frame.title = nombre; frame.style.cssText = "width:100%;height:700px";
        document.body.append(frame);
        try {
            await new Promise(resolve => { frame.onload = resolve; frame.src = "/metodos-numericos/regla-falsa/"; });
            await probar(frame.contentWindow, frame);
            item.textContent = `OK: ${nombre}`; aprobados++;
        } catch (e) { item.textContent = `FALLO: ${nombre}: ${e.message}`; }
        frame.remove();
    }
    document.getElementById("total").textContent = `${aprobados}/${casos.length} aprobados`;
})();
