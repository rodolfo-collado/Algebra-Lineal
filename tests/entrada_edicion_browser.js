/* P27.9: eventos de portapapeles solo en el runner, formularios/POST reales. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const todos = (w, s) => [...w.document.querySelectorAll(s)];
    const igual = (a, b) => {
        if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    };
    const valor = (w, s, v) => {
        const input = q(w, s); input.value = String(v);
        input.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const pegar = (w, input, texto, html = "") => {
        const data = new w.DataTransfer();
        data.setData("text/plain", texto); if (html) data.setData("text/html", html);
        const event = new w.ClipboardEvent("paste", { clipboardData: data, bubbles: true, cancelable: true });
        input.dispatchEvent(event); return event.defaultPrevented;
    };
    const post = (frame, s = "[data-calculo]") => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 10000);
        frame.onload = () => { clearTimeout(timer); resolve(frame.contentWindow); };
        q(frame.contentWindow, s).click();
    });
    const turno = w => new Promise(resolve => {
        // Los iframes fuera de la pestaña visible también deben avanzar.
        if (w.document.hidden) setTimeout(resolve, 50);
        else w.requestAnimationFrame(() => w.requestAnimationFrame(resolve));
    });
    const inversa = "/matrices/inversa/";
    const operaciones = "/matrices/operaciones/";
    const reduccion = "/matrices/reduccion/";
    const axb = "/matrices/ecuaciones/";
    const vectores = "/vectores/operaciones/";
    const A = '[data-matriz="A"] input.matrix-input';
    const modo = (w, tipo) => q(w, `[name="tipo_entrada"][value="${tipo}"]`).click();
    const casos = [];
    const caso = (nombre, ruta, test, sinJS = false) => casos.push({ nombre, ruta, test, sinJS });

    for (const [nombre, texto, esperado] of [
        ["3×3 exacto", "1\t2\t3\n4\t5\t6\n7\t8\t9", ["1", "2", "3", "4", "5", "6", "7", "8", "9"]],
        ["CRLF y terminación de hoja", "1\t2\t3\r\n4\t5\t6\r\n7\t8\t9\r\n", ["1", "2", "3", "4", "5", "6", "7", "8", "9"]],
        ["fila TAB", "1\t2\t3", ["1", "2", "3", "", "", "", "", "", ""]],
        ["columna LF", "1\n2\n3", ["1", "", "", "2", "", "", "3", "", ""]],
        ["signos, fracciones, decimales y espacios internos", " -11/13 \t3.14\t-2\n100\t1/2\t1 / 2", ["-11/13", "3.14", "-2", "100", "1/2", "1 / 2", "", "", ""]],
    ]) caso(`Paste: ${nombre}`, inversa, w => {
        valor(w, '[name="orden"]', 3);
        const celdas = todos(w, A); celdas[0].focus();
        let eventos = 0; let envios = 0; const observados = [];
        celdas[0].form.addEventListener("submit", e => { e.preventDefault(); envios++; });
        celdas[0].form.addEventListener("input", () => {
            eventos++; observados.push(celdas.map(c => c.value));
        });
        igual(pegar(w, celdas[0], texto), true);
        igual(celdas.map(c => c.value), esperado);
        observados.forEach(valores => igual(valores, esperado)); // Observadores ven el bloque completo.
        igual(eventos, texto.trimEnd().split(/\r?\n|\t/).length);
        igual(envios, 0); igual(w.document.activeElement === celdas[0], true);
        igual(q(w, '[data-estado-pegado]').textContent, `Se pegaron ${eventos} valores.`);
        igual(q(w, '[data-estado-pegado]').getAttribute("role"), "status");
    });
    caso("Paste: 2×2 desde celda interior de 4×4", inversa, w => {
        valor(w, '[name="orden"]', 4);
        const celdas = todos(w, A);
        pegar(w, celdas[5], "1\t2\n3\t4");
        igual([5, 6, 9, 10].map(i => celdas[i].value), ["1", "2", "3", "4"]);
        igual(celdas.filter((c, i) => ![5, 6, 9, 10].includes(i)).every(c => c.value === ""), true);
    });
    for (const texto of ["-11/13", "-11/13\r\n", "1,2,3"]) caso(`Paste nativo de una celda: ${JSON.stringify(texto)}`, inversa, w => {
        const input = q(w, A); input.value = "anterior";
        igual(pegar(w, input, texto), false); igual(input.value, "anterior");
        igual(q(w, '[data-estado-pegado]'), null);
    });
    for (const [nombre, texto] of [["no cabe", "1\t2\t3\n4\t5\t6"], ["filas desiguales", "1\t2\n3"]]) {
        caso(`Paste: ${nombre}, todo o nada`, inversa, w => {
            const celdas = todos(w, A); celdas.forEach(c => { c.value = "7"; });
            let eventos = 0; celdas[0].form.addEventListener("input", () => eventos++);
            igual(pegar(w, celdas[0], texto), true);
            igual(celdas.map(c => c.value), ["7", "7", "7", "7"]); igual(eventos, 0);
            igual(q(w, '[name="orden"]').value, "2");
            igual(q(w, '[data-estado-pegado]').textContent.includes(nombre === "no cabe" ? "2×3" : "misma cantidad"), true);
        });
    }
    caso("Paste: maxlength real de vector lineal, también después de reconstruir", operaciones, w => {
        const tipo = q(w, '[name="tipo_0"]'); tipo.value = "vector_lineal";
        tipo.dispatchEvent(new w.Event("change", { bubbles: true }));
        const celdas = todos(w, '[data-simbolo] [data-campo="celda"]').slice(0, 2);
        igual(celdas[0].maxLength, 200); celdas.forEach(c => { c.value = "3x1 - 2x2"; });
        pegar(w, celdas[0], `x1\n${"x".repeat(201)}`);
        igual(celdas.map(c => c.value), ["3x1 - 2x2", "3x1 - 2x2"]);
        igual(q(w, '[data-presupuesto]').textContent.includes("límite de texto"), true);
    });
    for (const propiedad of ["readOnly", "disabled"]) {
        caso(`Paste: origen ${propiedad} no interceptado`, inversa, w => {
            const input = q(w, A); input[propiedad] = true;
            igual(pegar(w, input, "1\t2"), false); igual(input.value, "");
        });
        caso(`Paste: destino ${propiedad}, aborta bloque entero`, inversa, w => {
            const celdas = todos(w, A); celdas[1][propiedad] = true;
            pegar(w, celdas[0], "1\t2"); igual(celdas.map(c => c.value), ["", "", "", ""]);
            igual(q(w, '[data-estado-pegado]').textContent.includes("no se pueden editar"), true);
        });
    }
    caso("Paste: solo text/plain, sin ejecutar HTML ni parser", inversa, w => {
        const celdas = todos(w, A);
        pegar(w, celdas[0], "<img src=x onerror=alert(1)>\t1,2", "<table><tr><td>999</td></tr></table>");
        igual(celdas[0].value, "<img src=x onerror=alert(1)>"); igual(celdas[1].value, "1,2");
        igual(q(w, '[data-matriz="A"] img'), null);
    });
    caso("Paste: Ax=b, A y b separados, x sin entradas", axb, w => {
        valor(w, '[name="filas"]', 3); valor(w, '[name="columnas"]', 3);
        pegar(w, q(w, A), "1\t2\t3\n4\t5\t6\n7\t8\t9");
        pegar(w, q(w, '[data-matriz="b"] input'), "-1\r\n1/2\r\n3.14");
        igual(todos(w, '[data-matriz="b"] input').map(c => c.value), ["-1", "1/2", "3.14"]);
        igual(todos(w, A).map(c => c.value), ["1", "2", "3", "4", "5", "6", "7", "8", "9"]);
        igual(q(w, '[data-unknown] input'), null);
    });
    caso("Paste: Reducción 3 ecuaciones × 3 variables, incluye b", reduccion, w => {
        modo(w, "matriz");
        pegar(w, q(w, '#matrix-grid input'), "1\t2\t3\t4\n5\t6\t7\t8\n9\t10\t11\t12");
        igual(todos(w, '#matrix-grid input').map(c => c.value), Array.from({ length: 12 }, (_, i) => String(i + 1)));
    });
    caso("Paste: Operaciones, no cruza símbolos, dinámicos incluidos", operaciones, w => {
        pegar(w, q(w, '[name="celda_0_0_0"]'), "1\t2\n3\t4");
        igual(q(w, '[name="celda_1_0_0"]').value, "");
        q(w, '[data-agregar]').click();
        pegar(w, q(w, '[name="celda_2_0_0"]'), "-1\t1/2\n3.14\t100");
        igual(q(w, '[name="celda_2_1_1"]').value, "100");
    });
    caso("Paste: Vectores según filas/componentes visibles", vectores, w => {
        pegar(w, q(w, '[name="u_0"]'), "1\t2\t3\n4\t5\t6");
        igual(todos(w, '#vector-list input[data-cell]').map(c => c.value), ["1", "2", "3", "4", "5", "6"]);
        pegar(w, q(w, '[name="u_1"]'), "-11/13\n3.14");
        igual([q(w, '[name="u_1"]').value, q(w, '[name="v_1"]').value], ["-11/13", "3.14"]);
        igual(q(w, '[data-estado-vectores]').textContent, "Se pegaron 2 valores.");
    });
    caso("Paste: resultado visible → stale compartido, teclado/foco y errores numéricos", inversa, async (w, frame) => {
        pegar(w, q(w, A), "1\t0\n0\t1"); w = await post(frame);
        const resultado = q(w, '[data-resultado]'); const anterior = q(w, '.panel-final').textContent;
        const input = q(w, A); input.focus(); const teclado = q(w, '.math-keyboard');
        igual(teclado.hasAttribute("data-abierto"), true);
        pegar(w, input, "2\t0\n0\t2");
        igual(resultado.dataset.resultado, "desactualizado"); igual(resultado.hidden, false);
        igual(q(w, '.panel-final').textContent, anterior);
        igual(q(w, '.result-notice').textContent.includes("Vuelve a calcular"), true);
        igual(w.document.activeElement === input, true); igual(teclado.hasAttribute("data-abierto"), true);
        igual(q(w, '[aria-busy="true"]'), null);
        pegar(w, input, `${"9".repeat(101)}\t0\n0\t2`); w = await post(frame);
        igual(q(w, '[data-respuesta-errores]') !== null, true); // Límite numérico del servidor intacto.
    });
    caso("UI-28: defaults, escritura, dimensiones y memoria al alternar", reduccion, w => {
        igual(q(w, '#system-fields').hidden, false); modo(w, "matriz");
        igual([q(w, '[name="ecuaciones"]').value, q(w, '[name="variables"]').value], ["3", "3"]);
        igual(todos(w, '#matrix-grid input').length, 12);
        valor(w, '[name="matriz_0_3"]', "17");
        valor(w, '[name="ecuaciones"]', 5); valor(w, '[name="variables"]', 4);
        valor(w, '[name="matriz_4_3"]', "1/2"); modo(w, "sistema"); modo(w, "matriz");
        igual([q(w, '[name="ecuaciones"]').value, q(w, '[name="variables"]').value], ["5", "4"]);
        igual(q(w, '[name="matriz_0_4"]').value, "17"); igual(q(w, '[name="matriz_4_3"]').value, "1/2");
        valor(w, '[name="variables"]', ""); modo(w, "sistema"); modo(w, "matriz");
        igual(q(w, '[name="variables"]').value, ""); // No sustituir edición inválida con defaults.
    });
    caso("UI-28: POST con error preserva dimensiones y celdas", reduccion, async (w, frame) => {
        modo(w, "matriz"); valor(w, '[name="ecuaciones"]', 5); valor(w, '[name="variables"]', 4);
        todos(w, '#matrix-grid input').forEach(c => { c.value = "0"; });
        valor(w, '[name="matriz_4_4"]', "1/"); w = await post(frame);
        igual([q(w, '[name="ecuaciones"]').value, q(w, '[name="variables"]').value], ["5", "4"]);
        igual(q(w, '[name="matriz_4_4"]').value, "1/"); igual(todos(w, '#matrix-grid input').length, 25);
    });
    caso("UI-28: primera elección tras POST textual también lista", reduccion, async (w, frame) => {
        valor(w, '[name="sistema"]', "X1=2"); w = await post(frame); modo(w, "matriz");
        igual(todos(w, '#matrix-grid input').length, 12);
    });
    caso("Sin JS: Reducción escrita y Aplicar de Ax=b funcionales", reduccion, async (w, frame) => {
        valor(w, '[name="sistema"]', "2x1 - x2 = 3; x1 + 4x2 = 7"); w = await post(frame);
        igual(q(w, '#resultado') !== null, true);
    }, true);
    caso("Sin JS: Aplicar conserva datos sin calcular", axb, async (w, frame) => {
        valor(w, '[name="filas"]', 3); valor(w, '[name="celda_A_0_0"]', "1/");
        w = await post(frame, '[data-aplicar]');
        igual(q(w, '[name="celda_A_0_0"]').value, "1/"); igual(q(w, '[name="celda_A_2_0"]') !== null, true);
        igual(q(w, '#resultado'), null);
    }, true);

    for (const ruta of [reduccion, axb]) caso(`UI-30: extremos, interior, selección, modificadores, IME, ${ruta}`, ruta, w => {
        if (ruta === reduccion) modo(w, "matriz");
        const celda = q(w, ruta === reduccion ? '[name="matriz_1_1"]' : '[name="celda_A_1_1"]');
        celda.value = "-12/7";
        const tecla = (key, inicio, fin = inicio, opciones = {}) => {
            celda.focus(); celda.setSelectionRange(inicio, fin);
            const event = new w.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...opciones });
            celda.dispatchEvent(event); return event.defaultPrevented;
        };
        igual(tecla("ArrowLeft", 0), true); igual(w.document.activeElement.name.endsWith("_1_0"), true);
        if (ruta === axb) valor(w, '[name="columnas"]', 3);
        const actual = q(w, ruta === reduccion ? '[name="matriz_1_1"]' : '[name="celda_A_1_1"]');
        // Ax=b reconstruye al cambiar columnas: los casos siguientes usan el nodo vigente.
        const comprobar = (key, inicio, fin = inicio, opciones = {}) => {
            actual.focus(); actual.setSelectionRange(inicio, fin);
            const event = new w.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...opciones });
            actual.dispatchEvent(event); return event.defaultPrevented;
        };
        igual(comprobar("ArrowRight", 5), true); igual(w.document.activeElement.name.endsWith("_1_2"), true);
        for (const key of ["ArrowLeft", "ArrowRight"]) {
            for (const [inicio, fin] of [[3, 3], [1, 3]]) {
                igual(comprobar(key, inicio, fin), false); igual(w.document.activeElement === actual, true);
            }
            for (const opciones of [{ctrlKey: true}, {shiftKey: true}, {altKey: true}, {metaKey: true},
                {ctrlKey: true, altKey: true}, {isComposing: true}, {keyCode: 229}]) {
                igual(comprobar(key, key === "ArrowLeft" ? 0 : 5, undefined, opciones), false);
                igual(w.document.activeElement === actual, true);
            }
        }
        actual.addEventListener("keydown", event => event.preventDefault(), { once: true });
        comprobar("ArrowLeft", 0); igual(w.document.activeElement === actual, true);
        igual(comprobar("ArrowUp", 3), true); igual(w.document.activeElement.name.endsWith("_0_1"), true);
    });
    for (const [ancho, alto] of [[1280, 650], [744, 521], [390, 650], [760, 560]]) {
        caso(`P27.8: fracciones largas, alineación, 7rem y scroll ${ancho}×${alto}`, reduccion, async (w, frame) => {
            frame.style.width = `${ancho}px`; frame.style.height = `${alto}px`;
            modo(w, "matriz"); valor(w, '[name="variables"]', 8);
            const texto = Array.from({ length: 3 }, () => Array.from({ length: 9 }, () => "-12345678901234567890/123456789").join("\t")).join("\n");
            pegar(w, q(w, '#matrix-grid input'), texto); await turno(w);
            const doc = w.document.documentElement;
            igual(doc.scrollWidth <= doc.clientWidth + 1, true);
            const inputs = todos(w, '#matrix-grid input');
            const maximo = parseFloat(w.getComputedStyle(doc).fontSize) * 7;
            igual(inputs.every(c => c.getBoundingClientRect().width <= maximo + 1), true);
            igual(w.getComputedStyle(inputs[0]).fieldSizing, "content");
            igual(inputs[0].getBoundingClientRect().left, inputs[9].getBoundingClientRect().left);
            const scroll = q(w, '.matrix-grid-frame');
            igual(scroll.scrollWidth > scroll.clientWidth, true);
        });
    }
    let passed = 0;
    for (const {nombre, ruta, test, sinJS} of casos) {
        const frame = document.createElement("iframe");
        if (sinJS) frame.setAttribute("sandbox", "allow-same-origin allow-forms");
        const loaded = new Promise(resolve => { frame.onload = resolve; });
        frame.src = ruta; document.body.append(frame); await loaded;
        const item = document.createElement("li");
        try { await test(frame.contentWindow, frame); passed++; item.textContent = `PASS · ${nombre}`; }
        catch (error) { item.textContent = `FAIL · ${nombre}: ${error.message}`; }
        document.querySelector("#resultados").append(item); frame.remove();
    }
    document.querySelector("#total").textContent = `${passed}/${casos.length} PASS`;
})();
