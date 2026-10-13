/* P27.9/P28: eventos de portapapeles solo en el runner, formularios/POST reales. */
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
    const pegarDatos = (w, input, data) => {
        const event = new w.ClipboardEvent("paste", { clipboardData: data, bubbles: true, cancelable: true });
        input.dispatchEvent(event); return event.defaultPrevented;
    };
    const pegar = (w, input, texto, html = "", metadata = "") => {
        const data = new w.DataTransfer();
        data.setData("text/plain", texto); if (html) data.setData("text/html", html);
        if (metadata) data.setData(w.copiadoMatricial.TIPO, metadata);
        return pegarDatos(w, input, data);
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
        igual(q(w, '[data-estado-pegado]').textContent, `${eventos} celdas pegadas.`);
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
        igual(q(w, '[data-estado-pegado]').textContent, "4 celdas pegadas.");
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
        igual(q(w, '[data-estado-pegado]').textContent, "2 celdas pegadas.");
    });
    caso("Paste: maxlength real de vector lineal, también después de reconstruir", operaciones, w => {
        const tipo = q(w, '[name="tipo_0"]'); tipo.value = "vector_lineal";
        tipo.dispatchEvent(new w.Event("change", { bubbles: true }));
        const celdas = todos(w, '[data-simbolo] [data-campo="celda"]').slice(0, 2);
        igual(celdas[0].maxLength, 200); celdas.forEach(c => { c.value = "3x1 - 2x2"; });
        pegar(w, celdas[0], `x1\n${"x".repeat(201)}`);
        igual(celdas.map(c => c.value), ["3x1 - 2x2", "3x1 - 2x2"]);
        igual(q(w, '[data-estado-pegado]').textContent.includes("límite de texto"), true);
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
        igual(q(w, '[data-estado-pegado]').textContent, "2 celdas pegadas.");
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
    // Los comandos viven en el menú de edición: clic derecho (caret colapsado, como un clic real)
    // sobre la celda actual de esa matriz o la primera. elegir() dice si el comando estaba disponible.
    const abrirMenu = (w, input) => {
        input.focus(); input.setSelectionRange(input.value.length, input.value.length);
        const event = new w.MouseEvent("contextmenu", { bubbles: true, cancelable: true, button: 2 });
        input.dispatchEvent(event); return event.defaultPrevented;
    };
    const menuVisible = w => [...q(w, "[data-edicion-menu]").querySelectorAll('[role="menuitem"]')]
        .filter(item => !item.hidden && !item.closest('[role="group"]')?.hidden);
    const elegir = (w, comando, indice = 0) => {
        const g = matriz(w, indice), f = filas(w, g), actual = w.seleccionMatricial.obtener(g).celdaActual;
        abrirMenu(w, actual ? f[actual.fila][actual.columna] : f[0][0]);
        const item = menuVisible(w).find(i => i.dataset.seleccionar === comando);
        if (item) item.click(); else key(w, w.document.activeElement, "Escape");
        return Boolean(item);
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
            igual(elegir(w, comando), true); igual(seleccion(w), esperado);
            const estado = w.seleccionMatricial.obtener(g);
            igual(estado.tipo, "comando"); igual(estado.comando, comando);
            igual(estado.columnasA, 3); igual(estado.columnas, ruta === inversa ? 3 : 4);
            igual(todos(w, "input.independent-input[data-celda-seleccionada]").length, 0);
            igual(q(w, "[data-estado-seleccion]").getAttribute("role"), "status");
            igual(q(w, "[data-estado-seleccion]").textContent.includes(`${esperado.length} celdas.`), true);
            igual(w.document.activeElement === filas(w, g)[1][1], true); // El comando devuelve el foco a la celda.
            igual(q(w, "[data-edicion-menu]").hidden, true);
        });
    }
    for (const [m, n] of [[2, 4], [4, 2]]) caso(`P28.1 rectangular ${m}×${n}: principal min y opciones imposibles`, axb, w => {
        valor(w, '[name="filas"]', m); valor(w, '[name="columnas"]', n);
        elegir(w, "principal"); igual(seleccion(w), [[0, 0], [1, 1]]);
        for (const comando of ["secundaria", "superior", "inferior"]) igual(elegir(w, comando), false);
        igual(seleccion(w), [[0, 0], [1, 1]]);
        // b y x no son matrices seleccionables: el menú de b no ofrece comandos de selección.
        abrirMenu(w, q(w, '[data-matriz="b"] input.matrix-input'));
        igual(menuVisible(w).map(i => i.textContent.trim()), ["Rellenar aleatoriamente"]);
        key(w, w.document.activeElement, "Escape"); igual(seleccion(w), [[0, 0], [1, 1]]);
    });
    caso("P28.1 fila/columna solo con celda actual y Ctrl único", inversa, w => {
        const comandos = w.seleccionMatricial.obtener(matriz(w)).comandos;
        igual([comandos.includes("fila"), comandos.includes("columna")], [false, false]);
        const input = filas(w)[0][0]; mouse(w, input, { ctrlKey: true });
        igual(seleccion(w), [[0, 0]]); igual(w.seleccionMatricial.obtener(matriz(w)).rectangular, true);
        mouse(w, input, { ctrlKey: true }); igual(w.seleccionMatricial.activa(), null);
        igual(w.seleccionMatricial.obtener(matriz(w)).tipo, null);
    });
    caso("P28.1 [A|b]: manual incluye b, comandos solo A", reduccion, w => {
        modo(w, "matriz"); const f = filas(w);
        mouse(w, f[0][3], { ctrlKey: true }); igual(seleccion(w), [[0, 3]]);
        igual(elegir(w, "columna"), false);
        elegir(w, "fila"); igual(seleccion(w), [[0, 0], [0, 1], [0, 2]]);
        mouse(w, f[1][3], { shiftKey: true }); igual(seleccion(w).some(c => c[1] === 3), true);
        abrirMenu(w, f[1][3]); igual(q(w, "[data-seleccion-aumentada]").hidden, false);
        key(w, w.document.activeElement, "Escape");
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
        // El nombre sigue al símbolo: el menú se titula con el nombre vigente y ofrece quitar la selección.
        abrirMenu(w, filas(w, a)[0][1]); igual(q(w, "[data-edicion-titulo]").textContent, "Matriz C");
        igual(menuVisible(w).some(i => i.dataset.accion === "deseleccionar"), true);
        key(w, w.document.activeElement, "Escape");
        q(w, '[data-eliminar]').click(); await turno(w);
        igual(w.seleccionMatricial.obtener(a), null); igual(w.seleccionMatricial.obtener(b).nombre, "B");
        igual(q(w, '[name="celda_0_0_0"]').closest("table") === b, true);
        q(w, '[data-eliminar]').click(); await turno(w);
        igual(w.seleccionMatricial.obtener(b), null); igual(w.seleccionMatricial.activa(), null);
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
        igual(w.seleccionMatricial.activa(), null); igual(w.seleccionMatricial.obtener(q(w, '[data-matriz="b"] table')), null);
    });
    caso("P28.1 sin selección en Vectores", vectores, w => {
        igual(w.seleccionMatricial, undefined); abrirMenu(w, q(w, '[name="v1_0"]'));
        igual(menuVisible(w).some(i => i.dataset.seleccionar), false); igual(q(w, "[data-seleccion-menu]").hidden, true);
        key(w, w.document.activeElement, "Escape");
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
                abrirMenu(w, input); await turno(w);
                const menu = q(w, "[data-edicion-menu]"), caja = menu.getBoundingClientRect();
                const doc = w.document.documentElement; igual(doc.scrollWidth <= doc.clientWidth + 1, true);
                igual(caja.left >= 0 && caja.right <= doc.clientWidth && caja.top >= 0 && caja.bottom <= doc.clientHeight, true);
                igual([...menu.querySelectorAll("button")].every(b => b.type === "button" && !b.name), true);
                igual(todos(w, ".matrix-entry-table[role=grid]").length, 0);
                key(w, w.document.activeElement, "Escape");
            });
        }
    }
    // Sin chip: el menú contextual flota sin mover la matriz, la celda elegida cambia de fondo sin
    // cambiar de tamaño y «Quitar selección» solo aparece cuando hay una selección.
    for (const ruta of [inversa, operaciones, axb, reduccion]) {
        caso(`UX selección desde el menú contextual, estado visible y Quitar selección: ${ruta}`, ruta, async w => {
            if (ruta === reduccion) modo(w, "matriz");
            const g = matriz(w); const celda = filas(w, g)[0][0]; const menu = q(w, "[data-edicion-menu]");
            igual(menu.hidden, true); igual(g.closest("form").querySelector("details.matrix-selection, summary[aria-label^='Seleccionar']"), null);
            celda.focus(); await turno(w); // El foco puede desplazar la página; abrir el menú no.
            const antes = g.getBoundingClientRect();
            abrirMenu(w, celda); await turno(w);
            igual(w.getComputedStyle(menu).position, "fixed");
            igual(menuVisible(w).some(i => i.dataset.accion === "deseleccionar"), false);
            const despues = g.getBoundingClientRect();
            igual([despues.top, despues.left], [antes.top, antes.left]);
            key(w, w.document.activeElement, "Escape");
            const normal = w.getComputedStyle(celda).backgroundColor;
            const tamano = [celda.offsetWidth, celda.offsetHeight];
            elegir(w, "principal"); await turno(w);
            igual(celda.hasAttribute("data-celda-seleccionada"), true);
            igual(w.getComputedStyle(celda).backgroundColor !== normal, true);
            igual(w.getComputedStyle(celda).borderStyle, "double");
            igual([celda.offsetWidth, celda.offsetHeight], tamano);
            abrirMenu(w, celda);
            const quitar = menuVisible(w).find(i => i.dataset.accion === "deseleccionar");
            igual(quitar.textContent.trim(), "Quitar selección"); quitar.click(); await turno(w);
            igual(seleccion(w), []); igual(g.querySelector("[data-celda-seleccionada]"), null);
            igual(menu.hidden, true); igual(w.document.activeElement === celda, true);
            igual(q(w, "[data-estado-seleccion]").textContent, "Selección eliminada.");
        });
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
        igual(q(w, "#resultado [data-celda-seleccionada]"), null);
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
    const copiar = (w, destino = w.document.activeElement, preparar = () => {}) => {
        const data = new w.DataTransfer();
        const event = new w.ClipboardEvent("copy", { clipboardData: data, bubbles: true, cancelable: true });
        preparar(event); destino.dispatchEvent(event);
        return { data, impedido: event.defaultPrevented };
    };
    const comprobarCopia = (w, esperado, coordenadas, forma = "rectangulo") => {
        const api = w.copiadoMatricial;
        const antes = w.seleccionMatricial.activa();
        const foco = w.document.activeElement;
        let cambios = 0;
        antes.matriz.closest("form").addEventListener("input", () => cambios++);
        const { data, impedido } = copiar(w);
        const valores = api.serializarValores({ ...antes,
            celdas: antes.celdas.map(({ fila, columna, input }) => ({ fila, columna, valor: input.value })) });
        igual(valores, api.serializar(antes));
        igual(impedido, true); igual(data.getData("text/plain"), esperado);
        igual([...data.types], ["text/plain", "text/html", api.TIPO]);
        igual(api.TIPO, "application/x-pygebra-matrix-selection");
        const metadata = api.parsear(data.getData(api.TIPO), esperado);
        igual(metadata, { version: 1, filas: esperado.split("\n").length,
            columnas: esperado.split("\n")[0].split("\t").length, forma, celdas: coordenadas });
        const tabla = new w.DOMParser().parseFromString(data.getData("text/html"), "text/html");
        igual([...tabla.querySelectorAll("tr")].map(tr => tr.querySelectorAll("td").length),
            Array(metadata.filas).fill(metadata.columnas));
        igual(cambios, 0); igual(w.document.activeElement === foco, true);
        igual(seleccion(w), antes.celdas.map(c => [c.fila, c.columna]));
        igual(q(w, "[data-estado-seleccion]").textContent,
            `${coordenadas.length} ${coordenadas.length === 1 ? "celda copiada" : "celdas copiadas"}.`);
        igual(q(w, "[data-estado-seleccion]").getAttribute("role"), "status");
        return data;
    };
    for (const ruta of [inversa, operaciones, axb, reduccion]) caso(`P28.2 Toda desde menú: ${ruta}`, ruta, w => {
        if (ruta === reduccion) modo(w, "matriz");
        const f = filas(w); f.flat().forEach((c, i) => { c.value = String(i + 1); });
        elegir(w, "toda"); const seleccionada = w.seleccionMatricial.activa();
        const texto = f.map(fila => fila.slice(0, seleccionada.columnasA).map(c => c.value).join("\t")).join("\n");
        comprobarCopia(w, texto, seleccion(w)); // Solo el modelo decide si b pertenece al bloque.
        igual(w.document.activeElement.matches("input.matrix-input"), true);
    });
    for (const [comando, texto, coords, forma] of [
        ["fila", "4\t5\t6", [[0,0],[0,1],[0,2]], "rectangulo"],
        ["columna", "2\n5\n8", [[0,0],[1,0],[2,0]], "rectangulo"],
        ["principal", "1\t\t\n\t5\t\n\t\t9", [[0,0],[1,1],[2,2]], "mascara"],
        ["secundaria", "\t\t3\n\t5\t\n7\t\t", [[0,2],[1,1],[2,0]], "mascara"],
        ["superior", "1\t2\t3\n\t5\t6\n\t\t9", [[0,0],[0,1],[0,2],[1,1],[1,2],[2,2]], "mascara"],
        ["inferior", "1\t\t\n4\t5\t\n7\t8\t9", [[0,0],[1,0],[1,1],[2,0],[2,1],[2,2]], "mascara"],
    ]) caso(`P28.2 ${comando}: TSV, HTML y round-trip`, inversa, w => {
        valor(w, '[name="orden"]', 3); const f = filas(w);
        f.flat().forEach((c, i) => { c.value = String(i + 1); });
        f[1][1].focus(); elegir(w, comando);
        comprobarCopia(w, texto, coords, forma);
    });
    caso("P28.2 una celda vacía seleccionada: tres formatos 1×1", inversa, w => {
        const f = filas(w); mouse(w, f[1][1], {ctrlKey:true});
        const data = comprobarCopia(w, "", [[0,0]]);
        igual(data.getData("text/html"), "<table><tr><td></td></tr></table>");
        const antes = q(w, "[data-estado-seleccion]").textContent;
        copiar(w); igual(q(w, "[data-estado-seleccion]").textContent, antes);
    });
    caso("P28.2 Ctrl+clic inverso: orden, hueco y celda seleccionada vacía", inversa, w => {
        const f = filas(w); f[1][1].value = "9";
        mouse(w, f[1][1], {ctrlKey:true}); mouse(w, f[0][0], {ctrlKey:true});
        comprobarCopia(w, "\t\n\t9", [[0,0],[1,1]], "mascara");
    });
    caso("P28.2 Shift+clic: rectángulo interior y coordenadas relativas", inversa, w => {
        valor(w, '[name="orden"]', 4); const f = filas(w);
        f.flat().forEach((c, i) => { c.value = String(i + 1); });
        mouse(w, f[2][2]); mouse(w, f[1][1], {shiftKey:true});
        f[1][1].setSelectionRange(0,0);
        comprobarCopia(w, "6\t7\n10\t11", [[0,0],[0,1],[1,0],[1,1]]);
    });
    caso("P28.2 Shift+flechas: copia no altera Escape ni teclado matemático", inversa, w => {
        const f = filas(w); mouse(w, f[0][0], {ctrlKey:true});
        key(w, f[0][0], "ArrowRight", {shiftKey:true});
        comprobarCopia(w, "\t", [[0,0],[0,1]]);
        igual(q(w, ".math-keyboard").hasAttribute("data-abierto"), true);
        igual(key(w, f[0][1], "Escape"), true); igual(seleccion(w), []);
        igual(copiar(w).impedido, false);
        igual(q(w, ".math-keyboard").hasAttribute("data-abierto"), true);
        key(w, f[0][1], "Escape"); igual(q(w, ".math-keyboard").hasAttribute("data-abierto"), false);
    });
    caso("P28.2 [A | b]: manual incluye b, comandos excluyen b", reduccion, w => {
        modo(w, "matriz"); const f = filas(w);
        f[0][2].value = "2/4"; f[0][3].value = "13/2";
        mouse(w, f[0][2]); mouse(w, f[0][3], {shiftKey:true});
        f[0][3].setSelectionRange(0,0);
        comprobarCopia(w, "2/4\t13/2", [[0,0],[0,1]]);
        elegir(w, "fila"); comprobarCopia(w, "\t\t2/4", [[0,0],[0,1],[0,2]]);
    });
    caso("P28.2 matriz rectangular y principal", axb, w => {
        valor(w, '[name="filas"]', 2); valor(w, '[name="columnas"]', 3);
        const f = filas(w); f.flat().forEach((c,i) => { c.value = String(i+1); });
        elegir(w,"toda"); comprobarCopia(w,"1\t2\t3\n4\t5\t6",[[0,0],[0,1],[0,2],[1,0],[1,1],[1,2]]);
        elegir(w,"principal"); comprobarCopia(w,"1\t\n\t5",[[0,0],[1,1]],"mascara");
    });
    caso("P28.2 HTML exacto: enteros, decimales, fracciones, espacios, escape y fórmulas ajenas", inversa, w => {
        valor(w, '[name="orden"]', 3); const f = filas(w);
        const valores = ["1/2","3/2","2/4","13/2"," -11 / 13 ","3.1400","-2",'<&>"\'',"=1+2"];
        f.flat().forEach((c,i) => { c.value = valores[i]; }); elegir(w,"toda");
        const data = comprobarCopia(w, "1/2\t3/2\t2/4\n13/2\t -11 / 13 \t3.1400\n-2\t<&>\"'\t=1+2", seleccion(w));
        const html = data.getData("text/html");
        igual(html.includes("<td>=1/2</td><td>=3/2</td><td>=2/4</td>"), true);
        igual(html.includes("<td>=13/2</td><td>= -11 / 13 </td><td>3.1400</td>"), true);
        igual(html.includes("&lt;&amp;&gt;&quot;&#39;"), true);
        const dom = new w.DOMParser().parseFromString(html,"text/html");
        igual([...dom.querySelectorAll("td")].map(c => c.textContent), valores.map((v,i) => i<5 ? `=${v}` : v));
        igual(dom.querySelectorAll("td")[8].getAttribute("style"), "mso-number-format:'\\@'");
        igual(dom.querySelectorAll("td")[7].childElementCount, 0);
    });
    for (const texto of ["1/0","1/000","1/2+WEBSERVICE(\"https://example.com\")","1 2/3","9".repeat(101)+"/2"]) {
        caso(`P28.2 HTML: fracción inválida no genera fórmula: ${texto.slice(0,35)}`, inversa, w => {
            const f = filas(w); f[0][0].value = texto; mouse(w, f[0][0], {ctrlKey:true}); f[0][0].setSelectionRange(0,0);
            const data = comprobarCopia(w, texto, [[0,0]]);
            const td = new w.DOMParser().parseFromString(data.getData("text/html"),"text/html").querySelector("td");
            igual(td.textContent,texto); igual(td.getAttribute("style"),"mso-number-format:'\\@'");
        });
    }
    for (const destino of ["celda", "textarea", "otro input", "texto DOM"]) caso(`P28.2 prioridad textual: ${destino}`, inversa, w => {
        elegir(w,"toda"); const f = filas(w);
        let target = f[0][0];
        if (destino === "texto DOM") {
            // Seleccionar texto de la página con el ratón saca el foco de la celda a la que volvió el comando.
            w.document.activeElement.blur();
            const p = w.document.createElement("p"); p.textContent = "texto normal"; w.document.body.append(p);
            // addRange no reemplaza un rango existente (el caret de la celda): se vacía antes.
            const range = w.document.createRange(); range.selectNodeContents(p); w.getSelection().removeAllRanges(); w.getSelection().addRange(range);
            target = p;
        } else {
            if (destino !== "celda") { target = w.document.createElement(destino === "textarea" ? "textarea" : "input"); w.document.body.append(target); }
            target.value = "-11/13"; target.focus(); target.setSelectionRange(1,3);
        }
        const antes = q(w,"[data-estado-seleccion]").textContent;
        const resultado = copiar(w,target); igual(resultado.impedido,false); igual([...resultado.data.types],[]);
        igual(q(w,"[data-estado-seleccion]").textContent,antes);
    });
    caso("P28.2 copy normal, cut, evento cancelado y clipboardData ausente", inversa, w => {
        const f = filas(w); f[0][0].focus(); igual(copiar(w).impedido,false);
        elegir(w,"toda"); igual(copiar(w,undefined,e => e.preventDefault()).data.types.length,0);
        const sinDatos = new w.ClipboardEvent("copy",{bubbles:true,cancelable:true});
        f[0][0].dispatchEvent(sinDatos); igual(sinDatos.defaultPrevented,false);
        const cut = new w.ClipboardEvent("cut",{clipboardData:new w.DataTransfer(),bubbles:true,cancelable:true});
        f[0][0].dispatchEvent(cut); igual(cut.defaultPrevented,false);
    });
    caso("P28.2 metadata inválida sin selección: conserva destino y bloque P27", inversa, w => {
        const f = filas(w);
        const data = new w.DataTransfer(); data.setData("text/plain","7\t8");
        data.setData(w.copiadoMatricial.TIPO,JSON.stringify({version:99,filas:1000}));
        const event = new w.ClipboardEvent("paste",{clipboardData:data,bubbles:true,cancelable:true});
        f[1][0].dispatchEvent(event);
        igual(f.flat().map(c=>c.value),["","","7","8"]); igual(seleccion(w),[]);
    });
    caso("P28.2 copia solo matriz activa e inputs actuales al redimensionar", inversa, w => {
        elegir(w,"toda"); valor(w,'[name="orden"]',3); const f = filas(w);
        f[0][0].value = "nuevo"; comprobarCopia(w,"nuevo\t\n\t",[[0,0],[0,1],[1,0],[1,1]]);
    });
    caso("P28.2 dos matrices: solo se copia el conjunto activo", operaciones, w => {
        const a = filas(w,matriz(w,0)), b = filas(w,matriz(w,1));
        a[0][0].value = "A"; b[1][1].value = "B";
        mouse(w,a[0][0],{ctrlKey:true}); mouse(w,b[1][1],{ctrlKey:true});
        comprobarCopia(w,"B",[[0,0]]);
        a[0][0].focus(); a[0][0].setSelectionRange(0,0); comprobarCopia(w,"A",[[0,0]]);
    });
    caso("P28.2 fallo setData: limpia datos parciales y no anuncia éxito", inversa, w => {
        elegir(w,"toda");
        const resultado = copiar(w,undefined,event => {
            const data = event.clipboardData, escribir = data.setData.bind(data);
            data.setData = (tipo,texto) => { if (tipo === w.copiadoMatricial.TIPO) throw new Error("denegado"); escribir(tipo,texto); };
        });
        igual(resultado.impedido,false); igual([...resultado.data.types],[]);
        igual(q(w,"[data-estado-seleccion]").textContent,"No se pudo copiar la selección al portapapeles.");
    });
    const baseMetadata = {version:1,filas:2,columnas:2,forma:"mascara",celdas:[[0,0],[1,1]]};
    for (const [nombre, cambio, texto = "1\t\n\t4"] of [
        ["versión",{version:2}], ["versión string",{version:"1"}], ["dimensión cero",{filas:0}],
        ["dimensión negativa",{columnas:-1}], ["dimensión fraccionaria",{filas:1.5}],
        ["filas excesivas",{filas:13}], ["columnas excesivas",{columnas:14}], ["booleano",{filas:true}],
        ["área excesiva",{filas:12,columnas:13}],
        ["coordenada negativa",{celdas:[[-1,0],[1,1]]}], ["coordenada fuera",{celdas:[[0,0],[2,1]]}],
        ["coordenada no entera",{celdas:[[0,0],[1,1.1]]}], ["coordenada string",{celdas:[[0,"0"],[1,1]]}],
        ["duplicadas",{celdas:[[0,0],[0,0]]}], ["sin orden",{celdas:[[1,1],[0,0]]}],
        ["demasiadas posiciones",{celdas:Array(5).fill([0,0])}], ["sin posiciones",{celdas:[]}],
        ["celda con extra",{celdas:[[0,0,0],[1,1]]}], ["celdas objeto",{celdas:{}}],
        ["celda objeto",{celdas:[{fila:0,columna:0}]}], ["forma falsa",{forma:"rectangulo"}],
        ["forma desconocida",{forma:"principal"}], ["rectángulo no mínimo",{celdas:[[0,0]]}],
        ["máscara sin huecos",{celdas:[[0,0],[0,1],[1,0],[1,1]]}],
        ["campo extra",{html:"<table>"}], ["columna TSV de más",{},"1\t\t\n\t4"],
        ["fila TSV de más",{},"1\t\n\t4\n"], ["fila desigual",{},"1\t\n4"],
        ["hueco con valor",{},"1\t2\n\t4"], ["CR aislado",{},"1\r\t\n\t4"],
    ]) caso(`P28.2 validador rechaza ${nombre}`, inversa, w => {
        const metadata = JSON.stringify({...baseMetadata,...cambio});
        igual(w.copiadoMatricial.parsear(metadata,texto),null);
        const f = filas(w); elegir(w,"toda");
        f.flat().forEach(c=>{c.value="7";});
        pegar(w,f[0][0],texto,"",metadata);
        const compatible = !["columna TSV de más","fila desigual"].includes(nombre);
        igual(f.flat().map(c=>c.value), compatible ? ["1", nombre === "hueco con valor" ? "2" : "", "", "4"] : ["7","7","7","7"]);
        igual(seleccion(w),[[0,0],[0,1],[1,0],[1,1]]);
    });
    for (const metadata of ["{", "null", "[]", "1", '"texto"', "{}", JSON.stringify({...baseMetadata,celdas:null})]) {
        caso(`P28.2 JSON/estructura corrupta ${metadata}`, inversa, w => {
            igual(w.copiadoMatricial.parsear(metadata,"1\t\n\t4"),null);
            const f=filas(w); elegir(w,"toda"); pegar(w,f[0][0],"1\t\n\t4","",metadata);
            igual(f.flat().map(c=>c.value),["1","","","4"]);
        });
    }
    caso("P28.2 límites UTF-8, máximo 120 celdas, vacíos y CRLF sin recorte", reduccion, w => {
        modo(w,"matriz"); valor(w,'[name="ecuaciones"]',12); valor(w,'[name="variables"]',9);
        const f = filas(w); const coords = f.flatMap((fila,i)=>fila.map((c,j)=>({fila:i,columna:j})));
        w.seleccionMatricial.reemplazar(matriz(w),coords); f[11][9].focus(); f[11][9].setSelectionRange(0,0);
        const texto = f.map(fila=>fila.map(()=>"").join("\t")).join("\n");
        const data = comprobarCopia(w,texto,coords.map(c=>[c.fila,c.columna])); const api = w.copiadoMatricial;
        igual(api.parsear(data.getData(api.TIPO),texto.replace(/\n/g,"\r\n")) !== null,true);
        const m = JSON.stringify(baseMetadata);
        igual(api.parsear(m.padEnd(4096," "),"1\t\n\t4") !== null,true);
        igual(api.parsear(m.padEnd(4097," "),"1\t\n\t4"),null);
        igual(api.parsear(m+"\u2000".repeat(1500),"1\t\n\t4"),null);
        const uno = JSON.stringify({version:1,filas:1,columnas:1,forma:"rectangulo",celdas:[[0,0]]});
        igual(api.parsear(uno,"x".repeat(65536)) !== null,true);
        igual(api.parsear(uno,"x".repeat(65537)),null); igual(api.parsear(uno,"é".repeat(32769)),null);
        igual(api.parsear(undefined,"1"),null); igual(api.parsear(uno,null),null);
    });
    caso("P28.2 máximo 13 columnas aumentadas: copia manual", reduccion, w => {
        modo(w,"matriz"); valor(w,'[name="ecuaciones"]',9); valor(w,'[name="variables"]',12);
        const f = filas(w); const coords = f.flatMap((fila,i)=>fila.map((c,j)=>({fila:i,columna:j})));
        w.seleccionMatricial.reemplazar(matriz(w),coords);
        const texto = f.map(fila=>fila.map(()=>"").join("\t")).join("\n");
        comprobarCopia(w,texto,coords.map(c=>[c.fila,c.columna]));
    });
    caso("P28.2 valores excesivos/tabulador: sin copia parcial ni anuncio de éxito", inversa, w => {
        const f = filas(w); elegir(w,"toda");
        for (const texto of ["x".repeat(65537),"valor\tinterior"]) {
            f[0][0].value = texto; const resultado = copiar(w);
            igual(resultado.impedido,false); igual([...resultado.data.types],[]);
            igual(q(w,"[data-estado-seleccion]").textContent.startsWith("No se pudo copiar"),true);
        }
        f.flat().forEach(c=>{c.value="x".repeat(17000);});
        const resultado = copiar(w); igual(resultado.impedido,false); igual([...resultado.data.types],[]);
    });
    // P28.3 usa la selección y el copy reales; solo el transporte de paste es sintético.
    const sustituir = (w, coords, g = matriz(w)) => {
        igual(w.seleccionMatricial.reemplazar(g, coords.map(([fila,columna])=>({fila,columna}))),true);
    };
    const avisoPegado = w => q(w,'[data-estado-pegado]').textContent;
    const copiarCoords = (w, coords, g = matriz(w)) => {
        sustituir(w,coords,g);
        const input = filas(w,g)[coords[0][0]][coords[0][1]];
        input.focus(); input.setSelectionRange(0,0);
        const resultado = copiar(w); igual(resultado.impedido,true);
        return resultado.data;
    };
    for (const ruta of [inversa, operaciones, axb, reduccion]) caso(`P28.3 rectangular 2×2 → Shift+clic: ${ruta}`, ruta, w => {
        if (ruta===reduccion) modo(w,"matriz");
        const f=filas(w); mouse(w,f[0][0]); mouse(w,f[1][1],{shiftKey:true});
        const foco=w.document.activeElement, antes=seleccion(w);
        const esperado=f.flat().map(c=>c.value); [0,1,2,3].forEach((i)=>{esperado[i<2?i:f[0].length+i-2]=String(i+1);});
        let eventos=0, envios=0, changes=0;
        foco.form.addEventListener("input",()=>{eventos++; igual(f.flat().map(c=>c.value),esperado);});
        foco.form.addEventListener("change",()=>changes++);
        foco.form.addEventListener("submit",e=>{e.preventDefault();envios++;});
        igual(pegar(w,foco,"1\t2\n3\t4"),true);
        igual(f.flat().map(c=>c.value),esperado); igual(eventos,4); igual(changes,0); igual(envios,0);
        igual(seleccion(w),antes); igual(w.document.activeElement===foco,true);
        igual(avisoPegado(w),"4 celdas pegadas.");
    });
    for (const [m,n,ok] of [[2,3,true],[3,2,false]]) caso(`P28.3 2×3 → ${m}×${n}, dimensiones exactas`, inversa,w=>{
        valor(w,'[name="orden"]',3); const f=filas(w);
        f.flat().forEach(c=>{c.value="7";});
        const coords=Array.from({length:m},(_,i)=>Array.from({length:n},(_,j)=>[i,j])).flat();
        sustituir(w,coords); f[0][0].focus();
        pegar(w,f[0][0],"1\t2\t3\n4\t5\t6");
        igual(f.flat().map(c=>c.value),ok ? ["1","2","3","4","5","6","7","7","7"] : Array(9).fill("7"));
        igual(seleccion(w),coords);
        if(!ok) igual(avisoPegado(w),"El bloque copiado es de 2×3 y la selección es de 3×2. No se pegó ningún valor.");
    });
    caso("P28.3 rectangular → arbitraria de igual cardinal: rechaza, sin mosaico", inversa,w=>{
        valor(w,'[name="orden"]',3); const f=filas(w); f.flat().forEach(c=>{c.value="7";});
        sustituir(w,[[0,0],[0,2],[1,1],[2,2]]); const antes=seleccion(w);
        pegar(w,f[0][0],"1\t2\n3\t4"); igual(f.flat().map(c=>c.value),Array(9).fill("7"));
        igual(seleccion(w),antes); igual(avisoPegado(w).includes("no son compatibles"),true);
        elegir(w,"toda"); pegar(w,f[0][0],"1\t2\n3\t4"); igual(f.flat().map(c=>c.value),Array(9).fill("7"));
    });
    for(const [comando] of comandos) caso(`P28.3 valor único → ${comando}, desde la celda de contexto`,inversa,w=>{
        valor(w,'[name="orden"]',3); const f=filas(w); f.flat().forEach(c=>{c.value="7";});
        f[1][1].focus(); elegir(w,comando); const coords=seleccion(w), foco=w.document.activeElement;
        igual(pegar(w,foco,"-11/13"),true);
        igual(f.flat().map(c=>c.value),f.flatMap((fila,i)=>fila.map((c,j)=>coords.some(([a,b])=>a===i&&b===j)?"-11/13":"7")));
        igual(seleccion(w),coords); igual(w.document.activeElement===foco,true);
    });
    for(const gesto of ["Shift","Ctrl"]) caso(`P28.3 valor único → selección manual ${gesto}`,inversa,w=>{
        valor(w,'[name="orden"]',3); const f=filas(w);
        if(gesto==="Shift"){mouse(w,f[0][0]);mouse(w,f[1][2],{shiftKey:true});}
        else{mouse(w,f[2][2],{ctrlKey:true});mouse(w,f[0][0],{ctrlKey:true});mouse(w,f[1][2],{ctrlKey:true});}
        const coords=seleccion(w); pegar(w,w.document.activeElement,"0");
        igual(coords.map(([i,j])=>f[i][j].value),Array(coords.length).fill("0")); igual(seleccion(w),coords);
    });
    caso("P28.3 [A | b]: rango, valor único y máscara cerca de b",reduccion,w=>{
        modo(w,"matriz"); const f=filas(w);
        mouse(w,f[0][2]);mouse(w,f[1][3],{shiftKey:true}); pegar(w,f[1][3],"1\t2\n3\t4");
        igual([f[0][2].value,f[0][3].value,f[1][2].value,f[1][3].value],["1","2","3","4"]);
        pegar(w,f[1][3],"0"); igual(seleccion(w).map(([i,j])=>f[i][j].value),Array(4).fill("0"));
        f[0][0].value="1";f[1][1].value="9";
        const data=copiarCoords(w,[[0,0],[1,1]]); w.seleccionMatricial.limpiar();
        f.flat().forEach(c=>{c.value="7";});
        pegarDatos(w,f[1][2],data); igual([f[1][2].value,f[2][3].value],["1","9"]);
        const antes=f.flat().map(c=>c.value);pegarDatos(w,f[1][3],data);igual(f.flat().map(c=>c.value),antes);
        igual(avisoPegado(w).includes("no cabe"),true);
    });
    for(const [nombre,coords] of [
        ["diagonal",[[0,0],[1,1],[2,2]]],
        ["triangular",[[0,0],[1,0],[1,1],[2,0],[2,1],[2,2]]],
        ["arbitraria",[[0,2],[1,0],[2,1]]],
    ]) caso(`P28.3 máscara ${nombre} → celda interior, huecos intactos`,inversa,w=>{
        valor(w,'[name="orden"]',4); const f=filas(w);
        f.flat().forEach((c,i)=>{c.value=String(i+1);}); const data=copiarCoords(w,coords);
        const valores=coords.map(([i,j])=>f[i][j].value); w.seleccionMatricial.limpiar();
        f.flat().forEach(c=>{c.value="7";}); f[1][1].focus();
        let eventos=0;f[1][1].form.addEventListener("input",()=>eventos++);
        pegarDatos(w,f[1][1],data);
        igual(coords.map(([i,j])=>f[i+1][j+1].value),valores);
        igual(f.flatMap((fila,i)=>fila.filter((c,j)=>!coords.some(([a,b])=>a+1===i&&b+1===j))).every(c=>c.value==="7"),true);
        igual(eventos,coords.length);igual(w.document.activeElement===f[1][1],true);igual(seleccion(w),[]);
        const antes=f.flat().map(c=>c.value); pegarDatos(w,f[2][2],data);
        igual(f.flat().map(c=>c.value),antes);igual(eventos,coords.length);
    });
    for(const destino of ["celda","selección"]) caso(`P28.3 hueco ≠ celda seleccionada vacía → ${destino}`,inversa,w=>{
        const f=filas(w);f[1][1].value=" 2/4 ";const data=copiarCoords(w,[[0,0],[1,1]]);
        w.seleccionMatricial.limpiar(); f.flat().forEach(c=>{c.value="7";});
        if(destino==="selección") sustituir(w,[[0,1],[1,0]]);
        pegarDatos(w,f[0][0],data);
        igual(f.flat().map(c=>c.value),destino==="celda"?["","7","7"," 2/4 "]:["7",""," 2/4 ","7"]);
    });
    caso("P28.3 una celda vacía copiada → cualquier selección",inversa,w=>{
        const f=filas(w), data=copiarCoords(w,[[0,0]]);
        f.flat().forEach(c=>{c.value="7";});elegir(w,"principal");pegarDatos(w,w.document.activeElement,data);
        igual(f.flat().map(c=>c.value),["","7","7",""]);igual(seleccion(w),[[0,0],[1,1]]);
    });
    caso("P28.3 rectangular propio: filas vacías exteriores se conservan en selección",axb,w=>{
        valor(w,'[name="filas"]',3);valor(w,'[name="columnas"]',1);const f=filas(w);
        f[1][0].value="2";const data=copiarCoords(w,[[0,0],[1,0],[2,0]]);
        f.flat().forEach(c=>{c.value="7";});pegarDatos(w,f[0][0],data);
        igual(f.flat().map(c=>c.value),["","2",""]);
        w.seleccionMatricial.limpiar();f.flat().forEach(c=>{c.value="7";});
        pegarDatos(w,f[0][0],data);igual(f.flat().map(c=>c.value),["7","7","7"]); // P27 delega 1 valor nativamente.
    });
    caso("P28.3 máscara triangular inferior → superior: orden por filas, no trasposición",inversa,w=>{
        valor(w,'[name="orden"]',3);const f=filas(w);f.flat().forEach((c,i)=>{c.value=String(i+1);});
        elegir(w,"inferior");const data=copiar(w).data;elegir(w,"superior");
        f.flat().forEach(c=>{c.value="7";});pegarDatos(w,w.document.activeElement,data);
        igual(f.flat().map(c=>c.value),["1","4","5","7","7","8","7","7","9"]);
        igual(seleccion(w).length,6);
    });
    for(const cardinal of [3,2]) caso(`P28.3 máscara → selección arbitraria de ${cardinal} celdas`,inversa,w=>{
        valor(w,'[name="orden"]',3);const f=filas(w);f.flat().forEach((c,i)=>{c.value=String(i+1);});
        const data=copiarCoords(w,[[0,0],[1,1],[2,2]]);const coords=[[0,2],[1,0],[2,1]].slice(0,cardinal);
        sustituir(w,coords);f.flat().forEach(c=>{c.value="7";});pegarDatos(w,f[0][2],data);
        igual(coords.map(([i,j])=>f[i][j].value),cardinal===3?["1","5","9"]:["7","7"]);
        igual(seleccion(w),coords);
        if(cardinal===2) igual(avisoPegado(w),"Se copiaron 3 celdas, pero hay 2 seleccionadas. No se pegó ningún valor.");
    });
    caso("P28.3 máscara → selección rectangular con igual cardinal",inversa,w=>{
        valor(w,'[name="orden"]',3);const f=filas(w);f.flat().forEach((c,i)=>{c.value=String(i+1);});
        const data=copiarCoords(w,[[0,0],[1,0],[1,1],[2,2]]);sustituir(w,[[0,1],[0,2],[1,1],[1,2]]);
        pegarDatos(w,f[0][0],data);igual([f[0][1].value,f[0][2].value,f[1][1].value,f[1][2].value],["1","4","5","9"]);
    });
    for(const defecto of ["readOnly","disabled","fieldset","hidden","maxLength","falta"]) {
        for(const origen of ["valor","máscara"]) caso(`P28.3 atomicidad ${origen}, destino ${defecto}`,inversa,async w=>{
            const f=filas(w);f[0][0].value="1";f[1][1].value="999";
            const data=copiarCoords(w,[[0,0],[1,1]]);f.flat().forEach(c=>{c.value="7";});
            const coords=seleccion(w);f[0][0].focus();
            if(defecto==="fieldset"){const field=w.document.createElement("fieldset");field.disabled=true;f[1][1].before(field);field.append(f[1][1]);}
            else if(defecto==="hidden") f[1][1].parentElement.hidden=true;
            else if(defecto==="falta") f[1][1].remove();
            else f[1][1][defecto]=defecto==="maxLength"?2:true;
            let eventos=0;f[0][0].form.addEventListener("input",()=>eventos++);
            if(origen==="valor") pegar(w,f[0][0],"999");else pegarDatos(w,f[0][0],data);
            igual(f.flat().map(c=>c.value),Array(4).fill("7"));igual(eventos,0);
            igual(w.seleccionMatricial.obtener(matriz(w),false).celdas.map(c=>[c.fila,c.columna]),coords);
            igual(w.document.activeElement===f[0][0],true);igual(avisoPegado(w).includes("No se pegó ningún valor"),true);
            if(defecto!=="falta") {
                await turno(w);
                igual(w.seleccionMatricial.obtener(matriz(w),false).celdas.map(c=>[c.fila,c.columna]),coords);
            }
        });
    }
    caso("P28.3 matrices independientes: falla en A, nunca continúa en B",operaciones,w=>{
        const a=filas(w,matriz(w)),b=filas(w,matriz(w,1));const data=copiarCoords(w,[[0,0],[1,1]]);
        w.seleccionMatricial.limpiar();a.flat().forEach(c=>{c.value="A";});b.flat().forEach(c=>{c.value="B";});
        pegarDatos(w,a[1][1],data);igual(a.flat().map(c=>c.value),Array(4).fill("A"));igual(b.flat().map(c=>c.value),Array(4).fill("B"));
        pegar(w,a[1][1],"1\t2\n3\t4");igual(a.flat().map(c=>c.value),Array(4).fill("A"));
        sustituir(w,[[0,0],[1,1]],matriz(w,1));pegar(w,a[0][0],"1\t2");
        igual(a[0].map(c=>c.value),["1","2"]);igual(b.flat().map(c=>c.value),Array(4).fill("B"));
    });
    for(const propiedad of ["readOnly","disabled"]) caso(`P28.3 origen seleccionado ${propiedad}: cero cambios`,inversa,async w=>{
        const f=filas(w);elegir(w,"toda");f.flat().forEach(c=>{c.value="7";});f[0][0][propiedad]=true;
        pegar(w,f[0][0],"9");await turno(w);
        igual(f.flat().map(c=>c.value),Array(4).fill("7"));igual(seleccion(w).length,4);
        igual(avisoPegado(w).includes("no se pueden editar"),true);
    });
    caso("P28.3 huecos readonly/disabled no son destinos de la máscara",inversa,w=>{
        const f=filas(w);f[0][0].value="1";f[1][1].value="4";const data=copiarCoords(w,[[0,0],[1,1]]);
        w.seleccionMatricial.limpiar();f.flat().forEach(c=>{c.value="7";});f[0][1].readOnly=true;f[1][0].disabled=true;
        pegarDatos(w,f[0][0],data);igual(f.flat().map(c=>c.value),["1","7","7","4"]);
    });
    caso("P28.3 Inversa B adicional: selección independiente",inversa,w=>{
        q(w,'#aplicaciones').open=true;q(w,'[name="funcion_adicional"][value="producto"]').click();
        const g=matriz(w,1);igual(Boolean(g),true);sustituir(w,[[0,0],[0,1],[1,0],[1,1]],g);
        pegar(w,filas(w,g)[0][0],"1\t2\n3\t4");igual(filas(w,g).flat().map(c=>c.value),["1","2","3","4"]);
        igual(filas(w,matriz(w)).flat().map(c=>c.value),Array(4).fill(""));
    });
    caso("P28.3 metadata falsa externa válida: datos literales, sin ejecutar HTML",inversa,w=>{
        const f=filas(w);const texto='<img src=x onerror=alert(1)>\t\n\t=1+2';
        pegar(w,f[0][0],texto,'<script>alert(1)</script>',JSON.stringify(baseMetadata));
        igual(f.flat().map(c=>c.value),['<img src=x onerror=alert(1)>',"","","=1+2"]);igual(q(w,".matrix img"),null);
    });
    caso("P28.3 sin text/plain, cancelado o sin clipboardData: conserva selección y valores",inversa,w=>{
        const f=filas(w);elegir(w,"toda");f.flat().forEach(c=>{c.value="7";});
        const data=new w.DataTransfer();data.setData("text/html","<table></table>");
        igual(pegarDatos(w,f[0][0],data),false);
        for(const conDatos of [true,false]) {
            const event=new w.ClipboardEvent("paste",{bubbles:true,cancelable:true,clipboardData:conDatos?data:null});
            if(conDatos) event.preventDefault();f[0][0].dispatchEvent(event);
        }
        igual(f.flat().map(c=>c.value),Array(4).fill("7"));igual(seleccion(w).length,4);
    });
    for(const metadata of ["{",JSON.stringify({...baseMetadata,version:99}),JSON.stringify(baseMetadata).padEnd(4097," "),JSON.stringify(baseMetadata)+"\u2000".repeat(1500)]) {
        caso(`P28.3 fallback metadata corrupta/excesiva (${metadata.length})`,inversa,w=>{
            const f=filas(w);elegir(w,"toda");pegar(w,f[0][0],"1\t2\n3\t4","",metadata);
            igual(f.flat().map(c=>c.value),["1","2","3","4"]);
            f.flat().forEach(c=>{c.value="7";});pegar(w,f[0][0],"1\t2\n3","",metadata);
            igual(f.flat().map(c=>c.value),Array(4).fill("7"));
        });
    }
    for(const [texto,ok] of [["x".repeat(65536),true],["x".repeat(65537),false],["é".repeat(32768),true],["é".repeat(32769),false]]) {
        caso(`P28.3 límite texto UTF-8 ${texto.length}/${ok}`,inversa,w=>{
            const f=filas(w);elegir(w,"principal");pegar(w,f[0][0],texto);
            igual([f[0][0].value,f[1][1].value],ok?[texto,texto]:["",""]);
        });
    }
    for(const [m,n] of [[12,9],[9,12]]) caso(`P28.3 máximo real ${m}×${n+1}, texto/metadata/llenado`,reduccion,w=>{
        modo(w,"matriz");valor(w,'[name="ecuaciones"]',m);valor(w,'[name="variables"]',n);const f=filas(w);
        const coords=f.flatMap((fila,i)=>fila.map((c,j)=>[i,j]));sustituir(w,coords);
        const texto=f.map(fila=>fila.map(()=>"1").join("\t")).join("\n");pegar(w,f[0][0],texto);
        igual(f.flat().every(c=>c.value==="1"),true);const data=copiar(w,f[0][0]).data;
        f.flat().forEach(c=>{c.value="7";});pegarDatos(w,f[0][0],data);igual(f.flat().every(c=>c.value==="1"),true);
        pegar(w,f[0][0],"0");igual(f.flat().every(c=>c.value==="0"),true);
        valor(w,'[name="ecuaciones"]',12);valor(w,'[name="variables"]',12);
        igual(filas(w).flat().length<=120,true);igual(q(w,"#matrix-grid-help").textContent.includes("120"),true);
    });
    for(const ruta of [inversa,operaciones,axb,reduccion]) caso(`P28.3 dimensiones después de paste: ${ruta}`,ruta,async w=>{
        if(ruta===reduccion) modo(w,"matriz");const f=filas(w);elegir(w,"toda");const coords=seleccion(w);
        pegar(w,w.document.activeElement,"5");
        const campo=ruta===inversa?'[name="orden"]':ruta===operaciones?'[name="filas_0"]':ruta===axb?'[name="filas"]':'[name="ecuaciones"]';
        const sobrevivientes=coords.filter(([i,j])=>i===0&&(ruta!==inversa||j===0));
        valor(w,campo,1);await turno(w);igual(seleccion(w),sobrevivientes);
        igual(filas(w)[0].slice(0,sobrevivientes.length).every(c=>c.value==="5"),true);
        valor(w,campo,3);igual(seleccion(w).every(([i])=>i===0),true);
        igual(f[0][0].value,"5");
    });
    caso("P28.3 resultado stale, foco, eventos completos, flechas, Escape y teclado",inversa,async(w,frame)=>{
        pegar(w,q(w,A),"1\t0\n0\t1");w=await post(frame);const f=filas(w);
        const resultado=q(w,'[data-resultado]'),anterior=q(w,'.panel-final').textContent;
        elegir(w,"principal");f[0][0].focus();const coords=seleccion(w);let eventos=0;
        f[0][0].form.addEventListener("input",()=>{eventos++;igual([f[0][0].value,f[1][1].value],["2","2"]);});
        pegar(w,f[0][0],"2");igual(eventos,2);igual(resultado.dataset.resultado,"desactualizado");
        igual(q(w,'.panel-final').textContent,anterior);igual(seleccion(w),coords);igual(w.document.activeElement===f[0][0],true);
        igual(q(w,'.math-keyboard').hasAttribute("data-abierto"),true);
        f[0][0].setSelectionRange(1,1);igual(key(w,f[0][0],"ArrowRight"),true);igual(w.document.activeElement===f[0][1],true);
        igual(key(w,f[0][1],"Escape"),true);igual(seleccion(w),[]);igual(q(w,'.math-keyboard').hasAttribute("data-abierto"),true);
        key(w,f[0][1],"Escape");igual(q(w,'.math-keyboard').hasAttribute("data-abierto"),false);
    });
    caso("P28.3 máscara marca stale; rechazo conserva resultado vigente y selección",inversa,async(w,frame)=>{
        pegar(w,q(w,A),"1\t0\n0\t1");w=await post(frame);const f=filas(w);elegir(w,"principal");
        const data=copiar(w).data;const resultado=q(w,'[data-resultado]');
        const antes=f.flat().map(c=>c.value),coords=seleccion(w);
        pegar(w,f[0][0],"2\t0\n0\t2");igual(resultado.dataset.resultado,"vigente");
        igual(f.flat().map(c=>c.value),antes);igual(seleccion(w),coords);
        data.setData("text/plain","2\t\n\t2");pegarDatos(w,f[0][0],data);
        igual(resultado.dataset.resultado,"desactualizado");igual(f.flat().map(c=>c.value),["2","0","0","2"]);
        igual(seleccion(w),coords);
    });
    caso("P28.3 aplicación común devuelve valores antes/después, sin historial",inversa,w=>{
        const f=filas(w);f[0][0].value="7";f[1][1].value="8";
        const registro=w.entradasSeguras.aplicarPegado([[f[0][0],"1"],[f[1][1],""]]);
        igual(registro.map(({anterior,nuevo})=>[anterior,nuevo]),[["7","1"],["8",""]]);
        igual(registro.map(({input})=>input.value),["1",""]);
    });
    // P28.4: un único registro, sin historial de edición ni Ctrl+Z propio.
    const accionUndo = w => q(w, "[data-deshacer-pegado]");
    const disponible = w => w.deshacerPegado.puedeDeshacer();
    const valores = (w, g = matriz(w)) => filas(w, g).flat().map(c => c.value);
    const restaurar = (w, esperado, g = matriz(w)) => {
        igual(disponible(w), true);
        accionUndo(w).focus(); accionUndo(w).click();
        igual(valores(w, g), esperado); igual(disponible(w), false);
        igual(accionUndo(w).hidden, true);
        igual(w.getComputedStyle(accionUndo(w)).display, "none");
        igual(w.deshacerPegado.deshacer(), false);
        accionUndo(w).click(); igual(valores(w, g), esperado);
    };
    for (const ruta of [inversa, operaciones, axb, reduccion]) {
        caso(`P28.4 rectangular, valores exactos, eventos atómicos y un solo uso: ${ruta}`, ruta, w => {
            if (ruta === reduccion) modo(w, "matriz");
            const g = matriz(w), f = filas(w, g);
            ["", "-11/13", "3.14", "2"].forEach((v, i) => { f[Math.floor(i / 2)][i % 2].value = v; });
            const antes = valores(w), coords = [[0,0],[0,1],[1,0],[1,1]];
            mouse(w, f[0][0]); mouse(w, f[1][1], { shiftKey: true });
            const foco = w.document.activeElement;
            pegar(w, foco, "5\t6\n7\t8");
            const eventos = []; let envios = 0, changes = 0;
            foco.form.addEventListener("input", e => {
                eventos.push(e.target); igual(valores(w), antes);
            });
            foco.form.addEventListener("submit", e => { e.preventDefault(); envios++; });
            foco.form.addEventListener("change", () => changes++);
            restaurar(w, antes); igual(eventos.map(c => c.name), coords.map(([i,j]) => f[i][j].name));
            igual(envios, 0); igual(changes, 0); igual(seleccion(w), coords);
            igual(w.document.activeElement === foco, true);
            igual(avisoPegado(w), "Pegado deshecho: 4 celdas restauradas.");
        });
        caso(`P28.4 bloque tradicional P27 sin selección: ${ruta}`, ruta, w => {
            if (ruta === reduccion) modo(w, "matriz");
            const antes = valores(w), input = filas(w)[0][0];
            pegar(w, input, "-1/2\t3.14\n4\t5"); restaurar(w, antes);
            igual(w.document.activeElement === input, true); igual(seleccion(w), []);
        });
        caso(`P28.4 cambio de dimensión invalida sin restaurar estructura: ${ruta}`, ruta, async w => {
            if (ruta === reduccion) modo(w, "matriz");
            pegar(w, filas(w)[0][0], "1\t2\n3\t4");
            const campo = ruta === inversa ? '[name="orden"]' : ruta === operaciones ? '[name="filas_0"]' :
                ruta === axb ? '[name="filas"]' : '[name="ecuaciones"]';
            valor(w, campo, 1); await turno(w);
            const antes = valores(w); igual(disponible(w), false); igual(accionUndo(w).hidden, true);
            igual(w.deshacerPegado.deshacer(), false); igual(valores(w), antes); igual(filas(w).length, 1);
        });
    }
    for (const [comando] of comandos) caso(`P28.4 valor único sobre ${comando}`, inversa, w => {
        valor(w, '[name="orden"]', 3); const antes = valores(w), contexto = filas(w)[0][0]; contexto.focus(); elegir(w, comando);
        const coords = seleccion(w); pegar(w, w.document.activeElement, "1");
        igual(avisoPegado(w), `${coords.length} celdas pegadas.`); restaurar(w, antes);
        igual(seleccion(w), coords); igual(w.document.activeElement === contexto, true);
    });
    caso("P28.4 Ctrl+clic inverso: orden de input fila por fila", inversa, w => {
        const f = filas(w), antes = valores(w);
        mouse(w, f[1][1], { ctrlKey: true }); mouse(w, f[0][0], { ctrlKey: true });
        pegar(w, f[0][0], "3.14"); const eventos = [];
        f[0][0].form.addEventListener("input", e => eventos.push(e.target));
        restaurar(w, antes); igual(eventos.map(c => c.name), [f[0][0].name, f[1][1].name]); igual(seleccion(w), [[0,0],[1,1]]);
    });
    for (const [nombre, coords] of [["diagonal", [[0,0],[1,1],[2,2]]],
        ["triangular", [[0,0],[1,0],[1,1],[2,0],[2,1],[2,2]]], ["irregular", [[0,1],[1,0],[2,2]]]]) {
        for (const destino of ["celda", "selección"]) caso(`P28.4 máscara ${nombre} → ${destino}, huecos y vacíos`, inversa, w => {
            valor(w, '[name="orden"]', 3); const f = filas(w);
            f.flat().forEach((c, i) => { c.value = i === 4 ? "" : i === 0 ? "-1/2" : String(i + 1); });
            const data = copiarCoords(w, coords);
            w.seleccionMatricial.limpiar(); f.flat().forEach(c => { c.value = "3.14"; });
            if (destino === "selección") sustituir(w, coords);
            const antes = valores(w), actual = seleccion(w);
            pegarDatos(w, f[0][0], data); restaurar(w, antes); igual(seleccion(w), actual);
        });
    }
    caso("P28.4 selección manual aumentada incluye b", reduccion, w => {
        modo(w, "matriz"); const f = filas(w), antes = valores(w);
        mouse(w, f[0][2]); mouse(w, f[1][3], { shiftKey: true }); const coords = seleccion(w);
        pegar(w, f[1][3], "1\t2\n3\t4"); restaurar(w, antes); igual(seleccion(w), coords);
    });
    caso("P28.4 Ax=b: bloque P27 del vector b separado", axb, w => {
        const g = q(w, '[data-matriz="b"] table'), antes = valores(w, g);
        pegar(w, filas(w, g)[0][0], "1/2\n3.14"); restaurar(w, antes, g);
    });
    caso("P28.4 Inversa B adicional independiente", inversa, w => {
        q(w, '#aplicaciones').open = true; q(w, '[name="funcion_adicional"][value="producto"]').click();
        const g = matriz(w, 1), antes = valores(w, g);
        elegir(w, "toda", 1); pegar(w, w.document.activeElement, "1/2"); restaurar(w, antes, g);
    });
    caso("P28.4 foco en B vuelve a abrir Aplicaciones si se cerró después del paste", inversa, w => {
        const aplicaciones=q(w,'#aplicaciones'); aplicaciones.open=true;
        q(w,'[name="funcion_adicional"][value="producto"]').click();
        const g=matriz(w,1),input=filas(w,g)[0][0],antes=valores(w,g);
        pegar(w,input,"1\t2\n3\t4"); aplicaciones.open=false;
        restaurar(w,antes,g); igual(aplicaciones.open,true); igual(w.document.activeElement===input,true);
    });
    caso("P28.4 P27 Vectores usa la misma aplicación atómica", vectores, w => {
        const g = q(w, '#vector-list'), antes = valores(w, g);
        pegar(w, filas(w, g)[0][0], "1\t2"); restaurar(w, antes, g);
    });
    caso("P28.4 vacío sobre selección restaura literales exactos", inversa, w => {
        const f = filas(w); ["1/2", "", "3.14", "-2"].forEach((v, i) => { f.flat()[i].value = v; });
        const antes = valores(w); elegir(w, "toda"); pegar(w, w.document.activeElement, "");
        igual(avisoPegado(w), "3 celdas pegadas."); restaurar(w, antes);
    });
    caso("P28.4 solo celdas modificadas y cantidad coherente", inversa, w => {
        const f = filas(w); ["1", "", "3", ""].forEach((v, i) => { f.flat()[i].value = v; });
        const antes = valores(w); pegar(w, f[0][0], "1\t2\n3\t4");
        igual(avisoPegado(w), "2 celdas pegadas."); const eventos = [];
        f[0][0].form.addEventListener("input", e => eventos.push(e.target));
        restaurar(w, antes); igual(eventos.map(c => c.name), [f[0][1].name, f[1][1].name]);
    });
    caso("P28.4 valor idéntico: no crea acción y reemplaza el registro previo", inversa, w => {
        const f = filas(w); elegir(w, "principal"); pegar(w, w.document.activeElement, "1");
        igual(disponible(w), true); pegar(w, w.document.activeElement, "1");
        igual(avisoPegado(w), "Pegado sin cambios."); igual(disponible(w), false);
        // La celda conserva foco; la acción anterior ya no es accesible.
        igual(accionUndo(w).hidden, true); igual(w.getComputedStyle(accionUndo(w)).display,"none");
        igual(w.deshacerPegado.deshacer(), false);
        igual([f[0][0].value, f[1][1].value], ["1", "1"]);
    });
    caso("P28.4 una celda modificada genera mensaje singular", inversa, w => {
        sustituir(w, [[0,0]]); const input = filas(w)[0][0]; pegar(w, input, "5");
        igual(avisoPegado(w), "1 celda pegada."); restaurar(w, Array(4).fill(""));
        igual(avisoPegado(w), "Pegado deshecho: 1 celda restaurada.");
    });
    caso("P28.4 paste A → paste B: solo B, sin volver al registro A", operaciones, w => {
        const a = matriz(w), b = matriz(w, 1), antesB = valores(w, b);
        pegar(w, filas(w, a)[0][0], "1\t2\n3\t4"); const despuesA = valores(w, a);
        pegar(w, filas(w, b)[0][0], "5\t6\n7\t8"); restaurar(w, antesB, b); igual(valores(w, a), despuesA);
    });
    caso("P28.4 nuevo paste en A sustituye el anterior, un solo nivel", inversa, w => {
        const input = filas(w)[0][0]; pegar(w, input, "1\t2\n3\t4"); const primero = valores(w);
        pegar(w, input, "5\t6\n7\t8"); restaurar(w, primero);
    });
    caso("P28.4 segundo paste anuncia solo el éxito, sin invalidación redundante", inversa, async w => {
        elegir(w,"principal"); const input=w.document.activeElement; pegar(w,input,"1");
        const anuncios=[], observador=new w.MutationObserver(mutaciones=>{
            mutaciones.forEach(m=>anuncios.push(...[...m.addedNodes].map(n=>n.textContent)));
        });
        observador.observe(q(w,'[data-estado-pegado]'),{childList:true});
        pegar(w,input,"2"); await turno(w); observador.disconnect(); igual(anuncios,["2 celdas pegadas."]);
    });
    caso("P28.4 paste rechazado conserva undo previo", inversa, w => {
        const input = filas(w)[0][0], antes = valores(w); pegar(w, input, "1\t2\n3\t4");
        pegar(w, input, "1\t2\t3\n4\t5\t6"); restaurar(w, antes);
    });
    for (const [i,j] of [[0,0],[1,1]]) caso(`P28.4 edición posterior de la misma matriz (${i},${j}) invalida sin robar foco`, inversa, w => {
        const f = filas(w); sustituir(w, [[0,0]]); pegar(w, f[0][0], "5");
        f[i][j].focus(); valor(w, `#${f[i][j].id}`, "8");
        const antes = valores(w); igual(disponible(w), false); igual(accionUndo(w).hidden, true);
        igual(w.document.activeElement === f[i][j], true); igual(w.deshacerPegado.deshacer(), false); igual(valores(w), antes);
    });
    caso("P28.4 edición independiente de B conserva undo de A", operaciones, async w => {
        const a = matriz(w), b = matriz(w, 1), antes = valores(w, a);
        pegar(w, filas(w, a)[0][0], "1\t2\n3\t4"); const inputB = filas(w, b)[0][0];
        valor(w, `#${inputB.id}`, "8"); await turno(w); restaurar(w, antes, a); igual(inputB.value, "8");
    });
    const defectosUndo = [
        ["valor incoherente sin input", (w, f) => { f[1][1].value = "9"; }],
        ["readonly", (w, f) => { f[1][1].readOnly = true; }],
        ["disabled", (w, f) => { f[1][1].disabled = true; }],
        ["fieldset disabled", (w, f) => { f[1][1].closest("fieldset").disabled = true; }],
        ["hidden", (w, f) => { f[1][1].parentElement.hidden = true; }],
        ["maxlength incompatible", (w, f) => { f[1][1].maxLength = 1; }],
        ["celda inexistente", (w, f) => f[1][1].remove()],
        ["input reconstruido", (w, f) => f[1][1].replaceWith(f[1][1].cloneNode(true))],
        ["cuadrícula reconstruida", (w, f, g) => g.replaceChildren(...[...g.children].map(c => c.cloneNode(true)))],
        ["matriz reemplazada", (w, f, g) => g.replaceWith(g.cloneNode(true))],
        ["matriz eliminada", (w, f, g) => g.remove()],
        ["matriz retirada y reinsertada", (w, f, g) => { const p = g.parentElement, n = g.nextSibling; g.remove(); p.insertBefore(g,n); }],
        ["filas movidas", (w, f, g) => g.querySelector("tbody").prepend(g.querySelector("tbody tr:last-child"))],
    ];
    for (const [nombre, defecto] of defectosUndo) {
        for (const esperar of [false, true]) caso(`P28.4 atomicidad ${nombre}, observer ${esperar ? "entregado" : "pendiente"}`, inversa, async w => {
            const g = matriz(w), f = filas(w); f.flat().forEach(c => { c.value = "123"; });
            pegar(w, f[0][0], "5\t6\n7\t8"); let eventos = 0;
            f[0][0].form.addEventListener("input", () => eventos++); defecto(w, f, g);
            const esperado = f.flat().map(c => c.value);
            if (esperar) await turno(w);
            igual(w.deshacerPegado.deshacer(), false); igual(f.flat().map(c => c.value), esperado);
            igual(eventos, 0); igual(disponible(w), false); igual(accionUndo(w).hidden, true);
            igual(w.getComputedStyle(accionUndo(w)).display,"none");
            igual(avisoPegado(w).includes("ya no puede deshacerse"), true);
        });
    }
    for (const tipo of ["vector", "escalar", "matriz_desconocida"]) caso(`P28.4 cambio de tipo ${tipo} invalida`, operaciones, async w => {
        pegar(w, filas(w)[0][0], "1\t2\n3\t4"); const input = q(w, '[data-campo="tipo"]');
        input.value = tipo; input.dispatchEvent(new w.Event("change", { bubbles: true })); await turno(w);
        igual(disponible(w), false); igual(accionUndo(w).hidden, true); igual(w.deshacerPegado.deshacer(), false);
    });
    caso("P28.4 eliminación real de operando no restaura sobre B reindexada", operaciones, async w => {
        pegar(w, filas(w)[0][0], "1\t2\n3\t4"); const b = matriz(w,1), antes = valores(w,b);
        q(w, '[data-eliminar]').click(); await turno(w); igual(disponible(w), false);
        igual(valores(w,matriz(w)), antes); igual(w.document.activeElement !== w.document.body, true);
    });
    caso("P28.4 Inversa: retirar B al cambiar aplicación", inversa, async w => {
        q(w, '#aplicaciones').open = true; q(w, '[name="funcion_adicional"][value="producto"]').click();
        pegar(w, filas(w,matriz(w,1))[0][0], "1\t2\n3\t4");
        q(w, '[name="funcion_adicional"][value="vector"]').click(); await turno(w); igual(disponible(w), false);
    });
    caso("P28.4 selección nueva conservada, Escape y flechas no invalidan", inversa, w => {
        const f = filas(w), antes = valores(w); pegar(w,f[0][0],"1\t2\n3\t4");
        f[0][0].focus(); f[0][0].setSelectionRange(1,1); key(w,f[0][0],"ArrowRight");
        igual(w.document.activeElement === f[0][1], true); igual(disponible(w),true);
        elegir(w,"secundaria"); const coords = seleccion(w); restaurar(w,antes); igual(seleccion(w),coords);
        pegar(w,f[0][0],"9"); key(w,f[0][0],"Escape"); igual(seleccion(w),[]); igual(disponible(w),true);
        restaurar(w,antes);
    });
    caso("P28.4 foco vuelve a la celda de contexto; control fuera de live region", inversa, w => {
        const f=filas(w); f[1][1].focus(); elegir(w,"principal"); pegar(w,w.document.activeElement,"5");
        const boton=accionUndo(w), aviso=q(w,'[data-estado-pegado]');
        igual(boton.type,"button"); igual(boton.textContent,"Deshacer"); igual(boton.closest('[role="status"], [aria-live]'),null);
        igual(aviso.getAttribute("aria-live"),"polite"); igual(aviso.getAttribute("aria-atomic"),"true");
        restaurar(w,Array(4).fill("")); igual(w.document.activeElement===f[1][1],true);
    });
    caso("P28.4 invalidación pasiva con botón enfocado mantiene un foco válido", inversa, async w => {
        pegar(w,filas(w)[0][0],"1\t2\n3\t4"); const boton=accionUndo(w); boton.focus();
        filas(w)[1][1].readOnly=true; await turno(w);
        igual(w.document.activeElement===boton,true); igual(boton.hidden,false); igual(boton.getAttribute("aria-disabled"),"true");
        boton.click(); igual(valores(w),["1","2","3","4"]); filas(w)[0][0].focus(); igual(boton.hidden,true);
    });
    caso("P28.4 comprobación final incoherente devuelve foco seguro al activarse", inversa, w => {
        pegar(w,filas(w)[0][0],"1\t2\n3\t4"); const boton=accionUndo(w); boton.focus();
        filas(w)[1][1].value="8"; boton.click(); igual(valores(w),["1","2","3","8"]);
        igual(w.document.activeElement===filas(w)[0][0],true); igual(boton.hidden,true);
    });
    caso("P28.4 fallback seguro con todas las celdas bloqueadas y Calcular disabled", inversa, w => {
        const f=filas(w); pegar(w,f[0][0],"1\t2\n3\t4"); accionUndo(w).focus();
        f.flat().forEach(c=>{c.readOnly=true;}); q(w,'[data-calculo]').disabled=true; accionUndo(w).click();
        igual(valores(w),["1","2","3","4"]); igual(w.document.activeElement===q(w,'[name="orden"]'),true);
        igual(w.getComputedStyle(accionUndo(w)).display,"none");
    });
    caso("P28.4 editar con teclado matemático invalida, Ctrl+Z queda nativo", inversa, async w => {
        const f=filas(w); pegar(w,f[0][0],"1\t2\n3\t4"); f[0][0].focus();
        igual(key(w,f[0][0],"z",{ctrlKey:true}),false); igual(disponible(w),true);
        f[0][0].setSelectionRange(1,1); const tecla=q(w,'.math-keyboard [data-insercion="-"]');
        tecla.dispatchEvent(new w.MouseEvent("mousedown",{bubbles:true,cancelable:true})); tecla.click(); await turno(w);
        igual(disponible(w),false); igual(f[0][0].value,"1-");
    });
    caso("P28.4 borrar manualmente no crea undo", inversa, w => {
        const input=filas(w)[0][0]; valor(w,`#${input.id}`,"2"); valor(w,`#${input.id}`,"");
        igual(disponible(w),false); igual(q(w,'[data-deshacer-pegado]'),null);
    });
    caso("P28.4 stale sigue stale al restaurar entradas originales", inversa, async(w,frame) => {
        pegar(w,q(w,A),"1\t0\n0\t1"); w=await post(frame);
        const resultado=q(w,'[data-resultado]'),contenido=q(w,'.panel-final').textContent,antes=valores(w);
        elegir(w,"principal"); pegar(w,w.document.activeElement,"2"); igual(resultado.dataset.resultado,"desactualizado");
        restaurar(w,antes); igual(resultado.dataset.resultado,"desactualizado"); igual(q(w,'.panel-final').textContent,contenido);
        igual(q(w,'.result-notice').textContent.includes("Vuelve a calcular"),true);
        igual(q(w,'.math-keyboard').hasAttribute("data-abierto"),true);
    });
    caso("P28.4 POST/navegación no conservan undo", inversa, async(w,frame) => {
        pegar(w,q(w,A),"1\t0\n0\t1"); w=await post(frame); igual(disponible(w),false);
        igual(q(w,'[data-deshacer-pegado]'),null); pegar(w,q(w,A),"2\t0\n0\t2");
        const loaded=new Promise(resolve=>{frame.onload=resolve;}); frame.src=operaciones; await loaded;
        igual(disponible(frame.contentWindow),false); igual(q(frame.contentWindow,'[data-deshacer-pegado]'),null);
    });
    caso("P28.4 pagehide descarta el registro incluso con bfcache", inversa, w => {
        pegar(w,filas(w)[0][0],"1\t2\n3\t4"); const antes=valores(w);
        w.dispatchEvent(new w.PageTransitionEvent("pagehide",{persisted:true}));
        igual(disponible(w),false); igual(valores(w),antes); igual(avisoPegado(w),"");
        igual(w.getComputedStyle(accionUndo(w)).display,"none");
    });
    for (const [ancho,alto] of [[1280,650],[744,521],[320,650]]) {
        for (const theme of ["light","dark"]) for (const ruta of [inversa,operaciones,axb,reduccion]) {
            caso(`P28.4 feedback y foco ${theme} ${ancho}×${alto}: ${ruta}`,ruta,async(w,frame)=>{
                frame.width=ancho; frame.height=alto; w.document.documentElement.dataset.theme=theme;
                if(ruta===reduccion) modo(w,"matriz"); elegir(w,"toda");
                pegar(w,w.document.activeElement,"1"); accionUndo(w).focus(); await turno(w);
                const pagina=w.document.documentElement, rect=accionUndo(w).getBoundingClientRect();
                igual(pagina.scrollWidth<=pagina.clientWidth,true); igual(rect.left>=0&&rect.right<=ancho,true);
                const estilo=w.getComputedStyle(accionUndo(w)); igual(estilo.outlineStyle,"solid");
                igual(parseFloat(estilo.outlineWidth)>0,true); accionUndo(w).click();
                igual(w.document.activeElement.matches('input.matrix-input'),true);
                igual(pagina.scrollWidth<=pagina.clientWidth,true);
            });
        }
    }
    if (new URLSearchParams(location.search).has("forced-colors")) {
        for (const ruta of [inversa,operaciones,axb,reduccion]) caso(`P28.4 forced-colors control, foco y live region: ${ruta}`,ruta,async w=>{
            igual(w.matchMedia("(forced-colors: active)").matches,true);
            if(ruta===reduccion) modo(w,"matriz"); pegar(w,filas(w)[0][0],"1\t2\n3\t4");
            const boton=accionUndo(w); boton.focus(); await turno(w); const estilo=w.getComputedStyle(boton);
            igual(estilo.borderStyle,"solid"); igual(parseFloat(estilo.borderWidth)>0,true);
            igual(estilo.outlineStyle,"solid"); igual(parseFloat(estilo.outlineWidth)>0,true);
            igual(estilo.color!==estilo.backgroundColor,true); boton.click(); igual(disponible(w),false);
        });
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
