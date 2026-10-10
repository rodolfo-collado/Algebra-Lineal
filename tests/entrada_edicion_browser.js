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
    // P27.11: las líneas vacías de los extremos no son filas; una interior sí.
    for (const [nombre, texto] of [
        ["LF con líneas vacías al inicio y al final", "\n1\t2\n3\t4\n"],
        ["CRLF con líneas vacías al inicio y al final", "\r\n1\t2\r\n3\t4\r\n"],
        ["varias líneas vacías exteriores", "\n\r\n\n1\t2\n3\t4\n\n\r\n"],
    ]) caso(`Paste P27.11: ${nombre}`, inversa, w => {
        const celdas = todos(w, A); celdas[0].focus();
        let eventos = 0; celdas[0].form.addEventListener("input", () => eventos++);
        igual(pegar(w, celdas[0], texto), true);
        igual(celdas.map(c => c.value), ["1", "2", "3", "4"]); igual(eventos, 4);
        igual(q(w, '[data-estado-pegado]').textContent, "Se pegaron 4 valores.");
        igual(w.document.activeElement === celdas[0], true);
    });
    caso("Paste P27.11: una fila vacía interior sigue siendo una fila, todo o nada", inversa, w => {
        const celdas = todos(w, A); celdas.forEach(c => { c.value = "7"; });
        let eventos = 0; celdas[0].form.addEventListener("input", () => eventos++);
        igual(pegar(w, celdas[0], "1\t2\n\n3\t4"), true);
        igual(celdas.map(c => c.value), ["7", "7", "7", "7"]); igual(eventos, 0);
        igual(q(w, '[data-estado-pegado]').textContent.includes("misma cantidad"), true);
        igual(pegar(w, celdas[0], "\n1\t2\r\n\r\n3\t4\n"), true); // Recortar extremos no borra la interior.
        igual(celdas.map(c => c.value), ["7", "7", "7", "7"]);
    });
    caso("Paste P27.11: un valor rodeado de líneas vacías sigue siendo paste nativo", inversa, w => {
        const input = q(w, A); input.value = "anterior";
        igual(pegar(w, input, "\n-11/13\r\n\n"), false); igual(input.value, "anterior");
        igual(q(w, '[data-estado-pegado]'), null);
    });
    caso("Paste P27.11: columna de Vectores con salto de más", vectores, w => {
        pegar(w, q(w, '[name="v1_1"]'), "\n-11/13\n3.14\n");
        igual([q(w, '[name="v1_1"]').value, q(w, '[name="v2_1"]').value], ["-11/13", "3.14"]);
        igual(q(w, '[data-estado-vectores]').textContent, "Se pegaron 2 valores.");
    });
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
        pegar(w, q(w, '[name="v1_0"]'), "1\t2\t3\n4\t5\t6");
        igual(todos(w, '#vector-list input[data-cell]').map(c => c.value), ["1", "2", "3", "4", "5", "6"]);
        pegar(w, q(w, '[name="v1_1"]'), "-11/13\n3.14");
        igual([q(w, '[name="v1_1"]').value, q(w, '[name="v2_1"]').value], ["-11/13", "3.14"]);
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
    // P28.1 amplía este runner de edición: mismas páginas, inputs y navegación de P27.
    const matriz = (w, indice = 0) => todos(w, ".matrix-entry-table, #matrix-grid")
        .filter(g => !g.closest("[data-vector], [hidden]") &&
            (!g.closest("[data-simbolo]") || g.closest("[data-simbolo]").querySelector('[data-campo="tipo"]').value === "matriz"))[indice];
    const seleccion = w => w.seleccionMatricial.activa()?.celdas.map(c => [c.fila, c.columna]) ?? [];
    const mouse = (w, input, opciones = {}) => {
        const event = new w.MouseEvent("mousedown", { bubbles: true, cancelable: true, button: 0, ...opciones });
        input.dispatchEvent(event); if (!event.defaultPrevented) input.focus();
        return event.defaultPrevented;
    };
    const key = (w, input, tecla, opciones = {}) => {
        const event = new w.KeyboardEvent("keydown", { key: tecla, bubbles: true, cancelable: true, ...opciones });
        input.dispatchEvent(event); return event.defaultPrevented;
    };
    const elegir = (w, comando, indice = 0) => {
        const menu = todos(w, ".matrix-selection")[indice]; menu.open = true;
        const boton = menu.querySelector(`[data-seleccionar="${comando}"]`); boton.click();
        return boton;
    };
    const filas = (w, g = matriz(w)) => w.entradasSeguras.filasDeMatriz(g);

    for (const ruta of [inversa, operaciones, axb, reduccion]) {
        caso(`P28.1 gestos y Escape contextual: ${ruta}`, ruta, w => {
            if (ruta === reduccion) modo(w, "matriz");
            const g = matriz(w); const f = filas(w, g); const input = f[0][0]; input.value = "-12/7";
            igual(mouse(w, input), false); igual(seleccion(w), []);
            igual(w.seleccionMatricial.obtener(g).referencia, { fila: 0, columna: 0 });
            igual(w.document.activeElement === input, true);
            input.setSelectionRange(2, 4);
            igual(mouse(w, input, { shiftKey: true }), false); igual([input.selectionStart, input.selectionEnd], [2, 4]);
            igual(key(w, input, "ArrowRight", { shiftKey: true }), false); igual(seleccion(w), []);
            igual(mouse(w, f[1][1], { shiftKey: true }), true);
            igual(seleccion(w), [[0, 0], [0, 1], [1, 0], [1, 1]]);
            igual(w.seleccionMatricial.obtener(g).tipo, "rango");
            igual(w.seleccionMatricial.obtener(g).rectangular, true);
            igual(key(w, f[1][1], "ArrowLeft", { shiftKey: true }), true);
            igual(seleccion(w), [[0, 0], [1, 0]]); igual(w.document.activeElement === f[1][0], true);
            igual(key(w, f[1][0], "ArrowRight", { shiftKey: true }), true);
            igual(seleccion(w).length, 4);
            igual(mouse(w, f[0][1], { ctrlKey: true }), true); igual(seleccion(w), [[0, 0], [1, 0], [1, 1]]);
            igual(w.seleccionMatricial.obtener(g).tipo, "arbitraria"); igual(w.seleccionMatricial.obtener(g).rectangular, false);
            igual(mouse(w, f[0][1], { ctrlKey: true }), true); igual(seleccion(w).length, 4);
            igual(q(w, ".math-keyboard").hasAttribute("data-abierto"), true);
            igual(key(w, w.document.activeElement, "Escape"), true); igual(seleccion(w), []);
            igual(q(w, ".math-keyboard").hasAttribute("data-abierto"), true);
            igual(q(w, "[data-estado-seleccion]").textContent, "Selección eliminada.");
            igual(key(w, w.document.activeElement, "Escape"), false);
            igual(q(w, ".math-keyboard").hasAttribute("data-abierto"), false);
            mouse(w, input); const anterior = q(w, "[data-estado-seleccion]").textContent;
            input.setSelectionRange(3, 3); igual(key(w, input, "ArrowLeft"), false);
            input.setSelectionRange(5, 5); igual(key(w, input, "ArrowRight"), true);
            igual(w.document.activeElement === f[0][1], true);
            igual(q(w, "[data-estado-seleccion]").textContent, anterior); // Foco sin anuncios de selección.
            igual(input.value, "-12/7");
        });
    }
    for (const ruta of [inversa, operaciones, axb, reduccion]) caso(`P28.1 fila/columna siguen la celda actual, Shift conserva referencia: ${ruta}`, ruta, w => {
        if (ruta === reduccion) modo(w, "matriz");
        const g = matriz(w); const f = filas(w, g);
        mouse(w, f[0][0]); mouse(w, f[1][1], {shiftKey:true});
        igual(w.seleccionMatricial.obtener(g).referencia, {fila:0,columna:0});
        igual(w.seleccionMatricial.obtener(g).celdaActual, {fila:1,columna:1});
        elegir(w, "fila");
        igual(seleccion(w), ruta === reduccion ? [[1,0],[1,1],[1,2]] : [[1,0],[1,1]]);
        elegir(w, "columna");
        igual(seleccion(w), ruta === reduccion ? [[0,1],[1,1],[2,1]] : [[0,1],[1,1]]);
        f[0][0].focus();
        igual(w.seleccionMatricial.obtener(g).referencia, {fila:0,columna:0});
        igual(w.seleccionMatricial.obtener(g).celdaActual, {fila:0,columna:0});
        elegir(w, "fila");
        igual(seleccion(w), ruta === reduccion ? [[0,0],[0,1],[0,2]] : [[0,0],[0,1]]);
        const copia = w.seleccionMatricial.obtener(g); copia.celdaActual.fila = 99;
        igual(w.seleccionMatricial.obtener(g).celdaActual.fila, 0);
    });
    const comandos = [
        ["toda", [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]]],
        ["fila", [[1, 0], [1, 1], [1, 2]]], ["columna", [[0, 1], [1, 1], [2, 1]]],
        ["principal", [[0, 0], [1, 1], [2, 2]]], ["secundaria", [[0, 2], [1, 1], [2, 0]]],
        ["superior", [[0, 0], [0, 1], [0, 2], [1, 1], [1, 2], [2, 2]]],
        ["inferior", [[0, 0], [1, 0], [1, 1], [2, 0], [2, 1], [2, 2]]],
    ];
    for (const ruta of [inversa, reduccion]) for (const [comando, esperado] of comandos) {
        caso(`P28.1 comando ${comando}, A y [A|b]: ${ruta}`, ruta, w => {
            if (ruta === inversa) valor(w, '[name="orden"]', 3); else modo(w, "matriz");
            const g = matriz(w); mouse(w, filas(w, g)[1][1]);
            const boton = elegir(w, comando); igual(boton.disabled, false); igual(seleccion(w), esperado);
            const estado = w.seleccionMatricial.obtener(g);
            igual(estado.tipo, "comando"); igual(estado.comando, comando);
            igual(estado.columnasA, 3); igual(estado.columnas, ruta === inversa ? 3 : 4);
            igual(todos(w, "input.independent-input[data-celda-seleccionada]").length, 0);
            igual(q(w, "[data-estado-seleccion]").getAttribute("role"), "status");
            igual(q(w, "[data-estado-seleccion]").textContent.includes(`${esperado.length} celdas.`), true);
            igual(w.document.activeElement.matches(".matrix-selection summary"), true);
            igual(q(w, ".matrix-selection").open, false);
        });
    }
    for (const [m, n] of [[2, 4], [4, 2]]) caso(`P28.1 rectangular ${m}×${n}: principal min y opciones imposibles`, axb, w => {
        valor(w, '[name="filas"]', m); valor(w, '[name="columnas"]', n);
        elegir(w, "principal"); igual(seleccion(w), [[0, 0], [1, 1]]);
        for (const comando of ["secundaria", "superior", "inferior"]) igual(elegir(w, comando).disabled, true);
        igual(seleccion(w), [[0, 0], [1, 1]]);
        igual(todos(w, ".matrix-selection").length, 1); // b y x no son matrices seleccionables.
    });
    caso("P28.1 fila/columna sin referencia y Ctrl único", inversa, w => {
        igual(elegir(w, "fila").disabled, true); igual(elegir(w, "columna").disabled, true);
        const input = filas(w)[0][0]; mouse(w, input, { ctrlKey: true });
        igual(seleccion(w), [[0, 0]]); igual(w.seleccionMatricial.obtener(matriz(w)).rectangular, true);
        mouse(w, input, { ctrlKey: true }); igual(w.seleccionMatricial.activa(), null);
        igual(w.seleccionMatricial.obtener(matriz(w)).tipo, null);
    });
    caso("P28.1 [A|b]: manual incluye b, comandos solo A", reduccion, w => {
        modo(w, "matriz"); const f = filas(w);
        mouse(w, f[0][3], { ctrlKey: true }); igual(seleccion(w), [[0, 3]]);
        igual(elegir(w, "columna").disabled, true);
        elegir(w, "fila"); igual(seleccion(w), [[0, 0], [0, 1], [0, 2]]);
        mouse(w, f[1][3], { shiftKey: true }); igual(seleccion(w).some(c => c[1] === 3), true);
        igual(q(w, "[data-seleccion-aumentada]").hidden, false);
    });
    caso("P28.1 API: orden, límites, sustitución atómica y limpieza", inversa, w => {
        const g = matriz(w); const api = w.seleccionMatricial;
        igual(api.reemplazar(g, [{fila: 1, columna: 1}, {fila: 0, columna: 0}, {fila: 1, columna: 1}]), true);
        igual(seleccion(w), [[0, 0], [1, 1]]);
        igual(api.obtener(g).limites, {filaInicio: 0, filaFin: 1, columnaInicio: 0, columnaFin: 1});
        igual(api.obtener(g).rectangular, false);
        for (const celda of [{fila: -1, columna: 0}, {fila: 2, columna: 0}, {fila: 0.5, columna: 0}, null]) {
            igual(api.reemplazar(g, [{fila: 0, columna: 0}, celda]), false); igual(seleccion(w).length, 2);
        }
        const copia = api.obtener(g); copia.referencia.fila = 99; copia.celdas.length = 0;
        igual(api.obtener(g).referencia.fila, 1); igual(seleccion(w).length, 2);
        igual(api.obtener(g).celdas.every(c => c.input.isConnected), true);
        api.limpiar(g); igual(api.activa(), null); igual(api.obtener(g).limites, null);
    });
    for (const ruta of [inversa, operaciones, axb, reduccion]) caso(`P28.1 dimensiones y referencias vigentes: ${ruta}`, ruta, async w => {
        if (ruta === reduccion) modo(w, "matriz");
        const campo = ruta === inversa ? '[name="orden"]' : ruta === operaciones ? '[name="filas_0"]' :
            ruta === axb ? '[name="filas"]' : '[name="ecuaciones"]';
        valor(w, campo, 3); elegir(w, "toda");
        const anterior = matriz(w); valor(w, campo, 1); await turno(w);
        const g = matriz(w); const estado = w.seleccionMatricial.obtener(g);
        igual(estado.filas, 1); igual(estado.celdas.every(c => c.fila === 0 && c.input.isConnected), true);
        igual(estado.referencia.fila, 0); igual(estado.extremo.fila, 0);
        if (anterior !== g) igual(w.seleccionMatricial.obtener(anterior), null);
        valor(w, campo, 3); igual(w.seleccionMatricial.obtener(matriz(w)).celdas.every(c => c.fila === 0), true);
        w.seleccionMatricial.reemplazar(matriz(w), [{fila: 2, columna: 0}]); valor(w, campo, 1);
        igual(w.seleccionMatricial.activa(), null); igual(w.seleccionMatricial.obtener(matriz(w)).referencia, null);
    });
    caso("P28.1 dos matrices: selección propia, una activa, reindexado y baja", operaciones, async w => {
        const [a, b] = [matriz(w), matriz(w, 1)];
        elegir(w, "principal"); elegir(w, "secundaria", 1);
        igual(w.seleccionMatricial.obtener(a).activa, false); igual(w.seleccionMatricial.obtener(a).celdas.length, 2);
        igual(w.seleccionMatricial.obtener(b).activa, true); igual(todos(w, "[data-seleccion-activa]").length, 1);
        mouse(w, filas(w, a)[0][1], { ctrlKey: true }); igual(w.seleccionMatricial.activa().matriz === a, true);
        igual(w.seleccionMatricial.obtener(b).celdas.length, 2);
        q(w, '[name="nombre_0"]').value = "C"; valor(w, '[name="nombre_0"]', "C");
        igual(todos(w, ".matrix-selection summary")[0].getAttribute("aria-label"), "Seleccionar celdas de C");
        q(w, '[data-eliminar]').click(); await turno(w);
        igual(w.seleccionMatricial.obtener(a), null); igual(w.seleccionMatricial.obtener(b).nombre, "B");
        igual(q(w, '[name="celda_0_0_0"]').closest("table") === b, true);
        q(w, '[data-eliminar]').click(); await turno(w);
        igual(w.seleccionMatricial.obtener(b), null); igual(w.seleccionMatricial.activa(), null);
        igual(todos(w, ".matrix-selection").length, 0);
    });
    for (const tipo of ["vector", "vector_lineal", "escalar", "matriz_desconocida", "vector_simbolico"]) {
        caso(`P28.1 cambio de tipo ${tipo} limpia selección sin volver a restaurarla`, operaciones, async w => {
            const g = matriz(w); elegir(w, "toda"); const campo = q(w, '[name="tipo_0"]');
            campo.value = tipo; campo.dispatchEvent(new w.Event("change", {bubbles: true})); await turno(w);
            igual(w.seleccionMatricial.obtener(g), null); igual(g.querySelector("[data-celda-seleccionada]"), null);
            campo.value = "matriz"; campo.dispatchEvent(new w.Event("change", {bubbles: true}));
            igual(w.seleccionMatricial.obtener(g).celdas.length, 0);
        });
    }
    caso("P28.1 reemplazo ajeno y ocultación: no quedan selecciones huérfanas", inversa, async w => {
        const g = matriz(w); elegir(w, "toda"); g.replaceWith(g.cloneNode(true)); await turno(w);
        igual(w.seleccionMatricial.obtener(g), null); igual(w.seleccionMatricial.activa(), null);
        igual(w.seleccionMatricial.obtener(matriz(w)).celdas.length, 0);
    });
    caso("P28.1 Reducción: alternar entrada elimina selección", reduccion, w => {
        modo(w, "matriz"); elegir(w, "toda"); modo(w, "sistema");
        igual(w.seleccionMatricial.activa(), null); modo(w, "matriz"); igual(seleccion(w), []);
    });
    caso("P28.1 B adicional de inversa: redimensionar y reemplazar por vector", inversa, async w => {
        q(w, '#aplicaciones').open = true; q(w, '[name="funcion_adicional"][value="producto"]').click();
        elegir(w, "toda", 1); valor(w, '[name="orden"]', 1);
        igual(w.seleccionMatricial.activa().nombre, "B"); igual(seleccion(w), [[0, 0]]);
        q(w, '[name="funcion_adicional"][value="vector"]').click(); await turno(w);
        igual(w.seleccionMatricial.activa(), null); igual(todos(w, ".matrix-selection").length, 1);
    });
    caso("P28.1 sin selección en Vectores", vectores, w => {
        igual(w.seleccionMatricial, undefined); igual(q(w, ".matrix-selection"), null);
    });
    for (const theme of ["light", "dark"]) for (const ruta of [inversa, operaciones, axb, reduccion]) {
        for (const [ancho, alto] of [[1280, 650], [744, 521], [320, 650]]) {
            caso(`P28.1 menú/selección/foco ${theme} ${ancho}×${alto}: ${ruta}`, ruta, async (w, frame) => {
                frame.style.width = `${ancho}px`; frame.style.height = `${alto}px`;
                w.document.documentElement.dataset.theme = theme;
                if (ruta === reduccion) modo(w, "matriz");
                elegir(w, "principal"); const input = filas(w)[0][0]; input.focus(); await turno(w);
                igual(w.getComputedStyle(input).borderStyle, "double");
                igual(w.getComputedStyle(input).outlineStyle, "solid");
                igual(Math.abs(parseFloat(w.getComputedStyle(input).outlineWidth) - 3) < 0.5, true); // Redondeo físico con zoom/DPR.
                igual(input.getAttribute("aria-describedby").includes("seleccion-celda-"), true);
                const menu = q(w, ".matrix-selection"); menu.open = true; await turno(w);
                const doc = w.document.documentElement; igual(doc.scrollWidth <= doc.clientWidth + 1, true);
                igual(menu.getBoundingClientRect().width <= doc.clientWidth, true);
                igual(todos(w, ".matrix-selection button").every(b => b.type === "button" && !b.name), true);
                igual(todos(w, ".matrix-entry-table[role=grid]").length, 0);
            });
        }
    }
    caso("P28.1 columnas: recortar selección y referencia de A sin seguir a b", reduccion, w => {
        modo(w, "matriz"); const g = matriz(w);
        w.seleccionMatricial.reemplazar(g, [{fila: 1, columna: 1}, {fila: 0, columna: 3}],
            {referencia: {fila: 0, columna: 3}, extremo: {fila: 0, columna: 3}});
        valor(w, '[name="variables"]', 1);
        igual(seleccion(w), [[1, 1]]); igual(w.seleccionMatricial.obtener(g).referencia, {fila: 1, columna: 1});
        valor(w, '[name="variables"]', 3); igual(seleccion(w), [[1, 1]]);
        elegir(w, "toda"); valor(w, '[name="variables"]', 1);
        igual(seleccion(w), [[0,0],[1,0],[2,0]]); // Una columna de A que pasa a ser b sale del comando.
    });
    caso("P28.1 Shift: límites, cuatro direcciones y modificadores", inversa, w => {
        valor(w, '[name="orden"]', 3); const f = filas(w); mouse(w, f[1][1], {ctrlKey:true});
        for (const [desde, tecla, destino] of [
            [[1,1], "ArrowUp", [0,1]], [[0,1], "ArrowDown", [1,1]],
            [[1,1], "ArrowDown", [2,1]], [[2,1], "ArrowUp", [1,1]],
            [[1,1], "ArrowRight", [1,2]], [[1,2], "ArrowLeft", [1,1]],
        ]) {
            igual(key(w, f[desde[0]][desde[1]], tecla, {shiftKey:true}), true);
            igual(w.document.activeElement === f[destino[0]][destino[1]], true);
        }
        for (const opciones of [{shiftKey:true,ctrlKey:true}, {shiftKey:true,altKey:true},
            {shiftKey:true,metaKey:true}, {shiftKey:true,isComposing:true}, {shiftKey:true,keyCode:229}]) {
            igual(key(w, f[1][1], "ArrowLeft", opciones), false);
        }
        mouse(w, f[0][0]); mouse(w, f[0][0], {ctrlKey:true});
        igual(key(w, f[0][0], "ArrowLeft", {shiftKey:true}), true); igual(seleccion(w), [[0,0]]);
    });
    caso("P28.1 selección no edita, no envía, no marca resultado stale ni persiste en POST", inversa, async (w, frame) => {
        pegar(w, q(w, A), "1\t0\n0\t1"); w = await post(frame);
        let cambios = 0; q(w, "#inversa-form").addEventListener("input", () => cambios++);
        elegir(w, "principal"); igual(cambios, 0); igual(q(w, "[data-resultado]").dataset.resultado, "vigente");
        igual(q(w, "#resultado .matrix-selection"), null);
        const input = filas(w)[0][0]; input.focus();
        const tecla = q(w, '.math-keyboard [data-insercion="-"]');
        tecla.dispatchEvent(new w.MouseEvent("mousedown", {bubbles:true,cancelable:true})); tecla.click();
        igual(cambios, 1); igual(seleccion(w), [[0,0],[1,1]]);
        igual(w.document.activeElement === input, true); igual(q(w, "[data-resultado]").dataset.resultado, "desactualizado");
        input.value = "1"; w = await post(frame); igual(seleccion(w), []);
    });
    caso("P28.1 Escape respetado por buscador y cajón", inversa, w => {
        elegir(w, "toda"); q(w, "#navigation-toggle").click();
        const buscar = q(w, '.app-sidebar input[type="search"]'); buscar.value = "matriz";
        buscar.dispatchEvent(new w.Event("input", {bubbles:true})); buscar.focus();
        igual(w.seleccionMatricial.activa() !== null, true);
        igual(key(w, buscar, "Escape"), true); igual(buscar.value, "matriz");
        igual(q(w, "#navigation-toggle").getAttribute("aria-expanded"), "true");
        igual(key(w, buscar, "Escape"), true); igual(buscar.value, "");
        igual(q(w, "#navigation-toggle").getAttribute("aria-expanded"), "true");
        key(w, buscar, "Escape"); igual(q(w, "#navigation-toggle").getAttribute("aria-expanded"), "false");
    });
    if (new URLSearchParams(location.search).has("forced-colors")) {
        for (const ruta of [inversa, operaciones, axb, reduccion]) caso(`P28.1 forced-colors: ${ruta}`, ruta, async w => {
            igual(w.matchMedia("(forced-colors: active)").matches, true);
            if (ruta === reduccion) modo(w, "matriz");
            elegir(w, "principal"); const input = filas(w)[0][0]; input.focus(); await turno(w);
            const style = w.getComputedStyle(input);
            const probe = w.document.createElement("span"); w.document.body.append(probe);
            probe.style.color = "Highlight"; igual(style.borderColor, w.getComputedStyle(probe).color);
            probe.style.color = "CanvasText"; igual(style.outlineColor, w.getComputedStyle(probe).color);
            igual(style.borderStyle, "double"); igual(style.outlineStyle, "solid"); probe.remove();
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
