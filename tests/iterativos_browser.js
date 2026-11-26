/* DOM, formato global y Plotly reales en Métodos iterativos; los eventos sintéticos viven solo en las pruebas. */
(async () => {
    "use strict";
    const RUTA = "/metodos-numericos/metodos-iterativos/";
    const q = (w, s) => w.document.querySelector(s);
    const qa = (w, s) => [...w.document.querySelectorAll(s)];
    const ok = (v, m) => { if (!v) throw new Error(m); };
    const esperar = async (f, m = "Espera agotada") => { const fin = Date.now() + 15000; while (!f()) {
        if (Date.now() > fin) throw new Error(m); await new Promise(r => setTimeout(r, 40)); } };
    const navegar = (frame, accion) => new Promise(r => { frame.onload = r; accion(); });
    const texto = n => n.textContent.trim();
    async function resolver(frame, ejemplo = "clase", metodo = null) {
        await navegar(frame, () => { frame.src = `${RUTA}?ejemplo=${ejemplo}`; });
        let w = frame.contentWindow;
        if (metodo) q(w, `[name="metodo"][value="${metodo}"]`).click();
        await navegar(frame, () => q(w, "[data-calculo]").click());
        w = frame.contentWindow;
        await esperar(() => qa(w, ".iterativo-grafica:not([hidden]) .main-svg").length, "Gráficas dibujadas");
        return w;
    }
    const articulo = (w, clave) => q(w, `[data-iterativo="${clave}"]`);
    const celda = (a, k, j) => a.querySelector(`tr[data-iteracion="${k}"]`).cells[j + 1];
    const formato = (w, modo, precision) => {
        const p = q(w, "[data-numeric-precision]"); if (precision) p.value = precision;
        const m = q(w, "[data-numeric-mode]"); m.value = modo; m.dispatchEvent(new w.Event("change", { bubbles: true }));
    };
    // Cada valor de la sustitución es el de la tabla: k para «nuevo», k − 1 para «anterior».
    function sustitucionCoincide(a, k) {
        return [...a.querySelectorAll(".iterativo-valor[data-columna]")].every(v =>
            texto(v) === texto(celda(a, v.dataset.origen === "nuevo" ? k : k - 1, Number(v.dataset.columna))));
    }

    const casos = [
        ["Comparar: mismas condiciones, un método a la vez y la k pasa al otro", async (w, frame) => {
            w = await resolver(frame);
            const jacobi = articulo(w, "jacobi"), seidel = articulo(w, "gauss_seidel");
            ok(!q(w, "[data-selector-metodo]").hidden && !jacobi.hidden && seidel.hidden, "Jacobi visible; Gauss-Seidel oculto");
            const comparacion = q(w, '[data-grafica="comparacion"]');
            ok(comparacion.data.map(t => t.name).join() === "Jacobi,Gauss-Seidel,Tolerancia ε", "Residuo de ambos y tolerancia");
            ok(comparacion.data[0].x.length === 16 && comparacion.data[1].x.length === 7, "15 y 6 iteraciones (más x⁽⁰⁾)");
            ok(comparacion.data[2].y.every(y => y === 1e-4) && comparacion.layout.yaxis.type === "log", "ε en escala logarítmica");
            q(w, '[data-iterativo="jacobi"] tr[data-iteracion="9"]').click();
            q(w, '[data-mostrar="gauss_seidel"]').click();
            ok(jacobi.hidden && !seidel.hidden && q(w, '[data-mostrar="gauss_seidel"]').getAttribute("aria-pressed") === "true", "Cambia de método");
            ok(seidel.querySelector("[data-k]").value === "6", "k = 9 se acota a la última de Gauss-Seidel");
            q(w, '[data-iterativo="gauss_seidel"] tr[data-iteracion="3"]').click();
            q(w, '[data-mostrar="jacobi"]').click();
            ok(jacobi.querySelector("[data-k]").value === "3", "Jacobi recibe k = 3");
            ok(seidel.querySelector(".iterativo-grafica .main-svg").getBoundingClientRect().width === 0, "La oculta no ocupa espacio");
        }],
        ["Gráfica, sustitución y tabla comparten la k elegida", async (w, frame) => {
            w = await resolver(frame, "clase", "gauss_seidel");
            const a = articulo(w, "gauss_seidel"), g = a.querySelector('[data-grafica="variables"]'), e = a.querySelector('[data-grafica="error"]');
            ok(g.data.slice(0, 4).map(t => t.name).join() === "x₁,x₂,x₃,x₄", "Una traza por incógnita");
            ok(new Set(g.data.slice(0, 4).map(t => t.line.color)).size === 4 && new Set(g.data.slice(0, 4).map(t => t.marker.symbol)).size === 4, "Color y marcador propios");
            ok(g.data[0].y.join() === [...a.querySelectorAll("tbody tr")].map(f => Number(f.cells[1].dataset.valor)).join(), "La gráfica dibuja los valores almacenados");
            ok(e.data.map(t => t.name).join() === "Cambio máximo,Residuo ‖r‖∞,Tolerancia ε", "Gráfica secundaria con tolerancia");
            const comprobar = k => {
                ok(a.querySelector("[data-k]").value === String(k), "Control en " + k);
                ok(texto(a.querySelector("[data-k-texto]")) === String(k), "Título " + k);
                ok(a.querySelector(`tr[data-iteracion="${k}"]`).getAttribute("aria-current") === "true", "Fila actual " + k);
                ok(a.querySelector(`tr[data-iteracion="${k - 1}"]`).hasAttribute("data-anterior"), "Fila anterior " + k);
                ok(a.querySelectorAll("tr[aria-current]").length === 1 && a.querySelectorAll("tr[data-anterior]").length === 1, "Una sola fila marcada");
                ok(sustitucionCoincide(a, k), "Sustitución de la iteración " + k);
                ok([...a.querySelectorAll("[data-k-anterior]")].every(s => texto(s) === String(k - 1)), "Superíndices k − 1");
                ok(g.layout.shapes[0].x0 === k - 1 && g.layout.shapes[0].x1 === k && g.layout.shapes[1].x0 === k, "Tramo y línea en la gráfica " + k);
                ok(g.data[4].x.every(x => x === k) && g.data[4].y.join() === [0, 1, 2, 3].map(j => Number(celda(a, k, j).dataset.valor)).join(), "Puntos de x⁽ᵏ⁾");
                ok(e.layout.shapes[1].x0 === k, "Gráfica secundaria " + k);
                ok(texto(a.querySelector('[data-medida="cambio"]')) === texto(celda(a, k, 4)), "Cambio de la iteración " + k);
            };
            comprobar(1);
            a.querySelector('tr[data-iteracion="4"]').click(); comprobar(4);
            ok(w.document.activeElement === a.querySelector('tr[data-iteracion="4"]'), "Foco en la fila elegida");
            a.querySelector('[data-paso="-1"]').click(); comprobar(3);
            const r = a.querySelector("[data-k]"); r.value = "6"; r.dispatchEvent(new w.Event("input")); comprobar(6);
            a.querySelector('[data-paso="1"]').click(); comprobar(6);
            g.emit("plotly_click", { points: [{ x: 2 }] }); comprobar(2);
            g.emit("plotly_click", { points: [{ x: 0 }] }); comprobar(2);
            a.querySelector('tr[data-iteracion="2"]').dispatchEvent(new w.KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true })); comprobar(3);
            a.querySelector('tr[data-iteracion="3"]').dispatchEvent(new w.KeyboardEvent("keydown", { key: "End", bubbles: true })); comprobar(6);
            a.querySelector('tr[data-iteracion="0"]').click(); comprobar(6);
        }],
        ["Jacobi lee solo x⁽ᵏ⁻¹⁾; Gauss-Seidel usa x⁽ᵏ⁾ en j < i", async (w, frame) => {
            w = await resolver(frame);
            const origenes = clave => [...articulo(w, clave).querySelectorAll(".iterativo-sustituciones li")].map(li =>
                [...li.querySelectorAll(".iterativo-fraccion:not(.iterativo-despeje) .iterativo-valor")].map(v => v.dataset.origen[0] + v.dataset.columna).join(" "));
            ok(origenes("jacobi").join("|") === "a1 a2|a0 a2 a3|a0 a1 a3|a1 a2", "Jacobi: todo anterior");
            ok(origenes("gauss_seidel").join("|") === "a1 a2|n0 a2 a3|n0 n1 a3|n1 n2", "Gauss-Seidel: nuevo antes de la diagonal");
            const s = articulo(w, "gauss_seidel");
            const despeje = texto(s.querySelector('li[data-fila="1"] .iterativo-despeje')).replace(/\s+/g, " ");
            ok(despeje === "25 + x₁(1) + x₃(0) − 3x₄(0) 11", "Despeje de x₂: " + despeje);
            // Señalar x₁⁽ᵏ⁾ en la fila 2 resalta su origen: el resultado de la fila 1 y la celda de la tabla.
            q(w, '[data-mostrar="gauss_seidel"]').click();
            s.querySelector('li[data-fila="1"] .iterativo-valor[data-origen="nuevo"]').dispatchEvent(new w.PointerEvent("pointerover", { bubbles: true }));
            ok(s.querySelector('li[data-fila="0"] strong').classList.contains("iterativo-fuente") && celda(s, 1, 0).classList.contains("iterativo-fuente"), "Origen del valor nuevo");
            s.querySelector(".iterativo-sustituciones").dispatchEvent(new w.PointerEvent("pointerleave"));
            ok(!s.querySelector(".iterativo-fuente"), "Sin resaltado al salir");
        }],
        ["Formato global: Exacto/Decimal en tabla, sustitución, ≈ y gráficas", async (w, frame) => {
            w = await resolver(frame, "clase", "jacobi");
            const a = articulo(w, "jacobi"), g = a.querySelector('[data-grafica="variables"]');
            formato(w, "exacto");
            ok(texto(celda(a, 1, 1)) === String(25 / 11), "Exacto: valor almacenado");
            ok(texto(a.querySelector('li[data-fila="1"] [data-relacion]')) === "=", "= con el valor almacenado");
            formato(w, "decimal", "4");
            ok(texto(celda(a, 1, 1)) === "2.2727", "Decimal con 4");
            ok(sustitucionCoincide(a, 1), "La sustitución sigue el formato");
            ok(texto(a.querySelector('li[data-fila="1"] [data-relacion]')) === "≈", "≈ al redondear");
            ok(g.data[1].customdata[1] === "2.2727", "Etiquetas de la gráfica con el formato");
            ok(!/\de[-+]?\d/.test(texto(q(w, "#resultado"))), "Sin exponentes");
            ok(qa(w, "#resultado tbody td").every(td => td.dataset.valor === "" || Number(td.dataset.valor) === 0 || texto(td) !== "0"), "Nunca 0 falso");
            a.querySelector('tr[data-iteracion="5"]').click(); ok(sustitucionCoincide(a, 5), "Otra k con decimales");
            formato(w, "decimal", "8"); ok(texto(celda(a, 1, 1)) === "2.27272727" && sustitucionCoincide(a, 5), "8 decimales");
            ok(texto(q(w, ".iterativos-solucion [data-relacion]")) === "≈", "≈ en el vector final");
            formato(w, "exacto"); ok(texto(q(w, ".iterativos-solucion [data-relacion]")) === "=", "= en Exacto");
        }],
        ["Copiar la tabla en CSV con las cifras almacenadas", async (w, frame) => {
            w = await resolver(frame, "diapositiva-28", "gauss_seidel");
            let copiado = null;
            w.document.execCommand = () => false;
            Object.defineProperty(w.navigator, "clipboard", { value: { writeText: async t => { copiado = t; } } });
            const a = articulo(w, "gauss_seidel");
            formato(w, "decimal", "2");
            a.querySelector("[data-copiar-csv]").click();
            await esperar(() => copiado !== null && texto(a.querySelector("[data-estado-copia]")), "Copia");
            const lineas = copiado.split("\r\n");
            ok(lineas[0] === "k,x1,x2,x3,x4,cambio_maximo,residuo_infinito", "Encabezado: " + lineas[0]);
            ok(lineas.length === 5 && lineas[1] === "0,0.0,0.0,0.0,0.0,,8.0", "x⁽⁰⁾ sin cambio: " + lineas[1]);
            ok(lineas[4].split(",")[1] === celda(a, 3, 0).dataset.valor, "Precisión completa aunque se lean 2 decimales");
            ok(texto(a.querySelector("[data-estado-copia]")) === "Tabla copiada: 4 filas en CSV.", "Aviso");
        }],
        ["Ejemplos en el menú de edición de A y b", async (w, frame) => {
            const celdaA = q(w, "#equation-entry input.matrix-input");
            celdaA.dispatchEvent(new w.MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: 40, clientY: 40 }));
            const menu = q(w, "[data-edicion-menu]");
            await esperar(() => !menu.hidden, "Menú abierto");
            const grupo = menu.querySelector("[data-ejemplos-menu]");
            ok(!grupo.hidden && texto(grupo.querySelector("p")) === "Cargar ejemplo · sustituye el sistema", "Grupo de ejemplos");
            ok([...grupo.querySelectorAll("a")].map(a => a.getAttribute("href")).join() === "?ejemplo=clase,?ejemplo=diapositiva-28,?ejemplo=sin-dominancia", "Tres ejemplos");
            await navegar(frame, () => grupo.querySelector('a[href="?ejemplo=diapositiva-28"]').click());
            w = frame.contentWindow;
            ok(q(w, '[name="celda_A_0_0"]').value === "8" && q(w, '[name="max_iteraciones"]').value === "3", "Carga la práctica");
        }],
        ["Sistema de ecuaciones: alterna con CSS, teclado de sistema y mismo resultado que A y b", async (w, frame) => {
            const visible = s => q(w, s).getClientRects().length > 0;
            ok(q(w, '[name="tipo_entrada"]:checked').value === "matriz" && visible("#equation-entry") && !visible("#system-fields"), "Matriz por omisión");
            q(w, '[name="tipo_entrada"][value="sistema"]').click();
            ok(visible("#system-fields") && !visible("#equation-entry") && !visible("[data-aplicar]"), "Ecuaciones en lugar de A y b");
            ok(visible('[data-input-hint="sistema"]') && !visible('[data-input-hint="matriz"]'), "Pista del tipo elegido");
            const campo = q(w, "#id_sistema"), perfiles = JSON.parse(q(w, "#math-keyboard-profiles").textContent);
            campo.focus();
            await esperar(() => !q(w, ".math-keyboard").hidden, "Teclado al enfocar las ecuaciones");
            ok(texto(q(w, ".math-keyboard-help")) === perfiles.sistema.ayuda, "Perfil de sistema, como en Reducción por filas");
            campo.value = "10x1 - x2 + 2x3 = 6; -x1 + 11x2 - x3 + 3x4 = 25; 2x1 - x2 + 10x3 - x4 = -11; 3x2 - x3 + 8x4 = 15";
            q(w, '[name="metodo"][value="comparar_iterativos"]').click();
            await navegar(frame, () => q(w, "[data-calculo]").click()); w = frame.contentWindow;
            await esperar(() => qa(w, ".iterativo-grafica:not([hidden]) .main-svg").length, "Gráficas dibujadas");
            const desdeTexto = texto(q(w, "#results-title"));
            ok(desdeTexto === "Gauss-Seidel converge en 6 y Jacobi en 15 iteraciones", desdeTexto);
            ok(q(w, '[name="tipo_entrada"]:checked').value === "sistema" && visible("#system-fields"), "Conserva el tipo de entrada");
            const matricial = await resolver(frame);
            ok(texto(q(matricial, "#results-title")) === desdeTexto, "Igual que el ejemplo de clase en A y b");
        }],
        ["Sin dominancia: crece sin converger; vector inicial exacto", async (w, frame) => {
            w = await resolver(frame, "sin-dominancia", "jacobi");
            ok(q(w, ".iterativos-cabecera").dataset.tono === "aviso" && texto(q(w, ".iterativos-estado")).includes("El cambio máximo crece"), "Aviso de crecimiento");
            ok(q(w, '[data-dominancia="no-estricta"]'), "Sin dominancia");
            const e = q(w, '[data-grafica="error"]');
            ok(e.data[0].y.at(-1) > e.data[0].y[1] && e.data[2].y[0] === 1e-4, "El cambio crece por encima de ε");
            await navegar(frame, () => { frame.src = `${RUTA}?ejemplo=clase`; });
            w = frame.contentWindow;
            q(w, '[name="metodo"][value="jacobi"]').click(); q(w, '[name="inicial_iterativo"]').value = "1 2 -1 1";
            await navegar(frame, () => q(w, "[data-calculo]").click()); w = frame.contentWindow;
            ok(texto(q(w, "#results-title")) === "Jacobi converge en 1 iteración" && texto(q(w, ".iterativos-estado")).startsWith("x⁽⁰⁾ ya satisface"), "Inicial exacto");
        }],
        ["Temas, estilos y anchos sin desborde; la k sobrevive al cambio de tema", async (w, frame) => {
            w = await resolver(frame);
            const raiz = w.document.documentElement, a = articulo(w, "jacobi"), g = a.querySelector('[data-grafica="variables"]');
            a.querySelector('tr[data-iteracion="7"]').click();
            for (const estilo of ["estudio", "minimalista"]) for (const tema of ["light", "dark"]) for (const ancho of [1280, 744, 390]) {
                raiz.dataset.estilo = estilo; raiz.dataset.theme = tema; frame.style.width = ancho + "px";
                await esperar(() => g.layout.paper_bgcolor === w.getComputedStyle(q(w, "#resultado")).getPropertyValue("--color-surface-raised").trim(), "Colores del tema");
                await Promise.all(qa(w, ".js-plotly-plot").map(div => w.Plotly.Plots.resize(div)));
                ok(raiz.scrollWidth <= raiz.clientWidth + 1, `Sin desborde ${estilo} ${tema} ${ancho}`);
                ok(g.layout.shapes[1].x0 === 7 && g.data[4].x[0] === 7, "Conserva k = 7");
                const caja = s => a.querySelector(s).getBoundingClientRect(), gv = caja('[data-grafica="variables"]'), p = caja(".iterativo-paso"), t = caja(".iterativo-tabla");
                if (ancho === 1280) ok(p.left >= gv.right && Math.abs(p.top - gv.top) < 2 && t.top >= p.bottom, "Gráfica y sustitución lado a lado, tabla debajo");
                else ok(p.top >= gv.bottom && t.top >= p.bottom, "Columna única " + ancho);
            }
        }],
    ];
    let aprobados = 0;
    for (const [nombre, probar] of casos) {
        const item = document.createElement("li"); document.getElementById("resultados").append(item);
        localStorage.setItem("pygebra-formato-numerico", "exacto");
        const frame = document.createElement("iframe"); frame.title = nombre; frame.style.cssText = "width:1280px;height:900px"; document.body.append(frame);
        try { await new Promise(r => { frame.onload = r; frame.src = RUTA; }); await probar(frame.contentWindow, frame); item.textContent = "OK: " + nombre; aprobados++; }
        catch (e) { item.textContent = "FALLO: " + nombre + ": " + e.message; } frame.remove();
    }
    document.getElementById("total").textContent = `${aprobados}/${casos.length} aprobados`;
})();
