/* Menú de edición: eventos sintéticos en cada iframe, formularios/POST reales y romanos validados por el backend. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const todos = (w, s) => [...w.document.querySelectorAll(s)];
    const igual = (a, b, contexto = "") => {
        if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${contexto ? `${contexto}: ` : ""}${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    };
    const ok = (condicion, mensaje) => { if (!condicion) throw new Error(mensaje); };
    const turno = w => new Promise(resolve => {
        if (w.document.hidden) setTimeout(resolve, 50);
        else w.requestAnimationFrame(() => w.requestAnimationFrame(resolve));
    });
    const valor = (w, s, v) => {
        const input = q(w, s); input.value = String(v);
        input.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const cambiar = (w, s, v) => {
        const campo = q(w, s); campo.value = v;
        campo.dispatchEvent(new w.Event("change", { bubbles: true }));
    };
    const post = (frame, s = "[data-calculo]") => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 15000);
        frame.onload = () => { clearTimeout(timer); resolve(frame.contentWindow); };
        q(frame.contentWindow, s).click();
    });
    const modo = (w, tipo) => q(w, `[name="tipo_entrada"][value="${tipo}"]`).click();
    const menu = w => q(w, "[data-edicion-menu]");
    const visibles = w => [...menu(w).querySelectorAll('[role="menuitem"]')]
        .filter(item => !item.hidden && !item.closest('[role="group"]')?.hidden);
    const opciones = w => visibles(w).map(item => item.textContent.trim());
    const titulo = w => q(w, "[data-edicion-titulo]").textContent;
    // Como un clic derecho: el campo recibe foco (caret colapsado) y después llega contextmenu.
    // Con button -1 el evento imita Shift+F10 o la tecla Menú en Chromium (Firefox usa 0).
    const abrir = (w, input, { teclado = false, x = 30, y = 30 } = {}) => {
        input.focus();
        try { input.setSelectionRange(input.value.length, input.value.length); } catch { /* radio, number */ }
        const event = new w.MouseEvent("contextmenu", { bubbles: true, cancelable: true, button: teclado ? -1 : 2, clientX: x, clientY: y });
        input.dispatchEvent(event); return event.defaultPrevented;
    };
    const tecla = (w, destino, key, opciones = {}) => {
        const event = new w.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...opciones });
        destino.dispatchEvent(event); return event.defaultPrevented;
    };
    const cerrar = w => tecla(w, w.document.activeElement, "Escape");
    const accion = (w, input, texto) => {
        ok(abrir(w, input), `El menú se abre en ${input.name}`);
        const item = visibles(w).find(i => i.textContent.trim() === texto);
        ok(item, `«${texto}» no está en el menú: ${opciones(w)}`);
        item.click();
    };
    const rellenar = (w, input) => accion(w, input, "Rellenar aleatoriamente");
    const limpiar = (w, input) => accion(w, input, "Limpiar");
    // Lo que el menú edita desde una celda, leído del DOM sin pasar por el módulo.
    const celdasDe = input => [...(input.closest(".vector-row") || input.closest(".matrix-entry-table, #matrix-grid"))
        .querySelectorAll("input.matrix-input")];
    const valores = celdas => celdas.map(c => c.value);
    const entero = v => /^-?\d$/.test(v) && Number(v) >= -9 && Number(v) <= 9;
    const aviso = w => q(w, "[data-estado-pegado]")?.textContent ?? "";
    const conAzar = (w, valorFijo, accionPrueba) => {
        const original = w.Math.random; w.Math.random = () => valorFijo;
        try { accionPrueba(); } finally { w.Math.random = original; }
    };
    const inversa = "/matrices/inversa/", operaciones = "/matrices/operaciones/", reduccion = "/matrices/reduccion/";
    const axb = "/matrices/ecuaciones/", determinantes = "/matrices/determinantes/", vectores = "/vectores/operaciones/";
    const romanos = "/romanos/conversion/";
    const COMANDOS = ["Toda la matriz", "Fila actual", "Columna actual", "Diagonal principal", "Diagonal secundaria",
        "Triangular superior", "Triangular inferior"];
    const ROMANO = /^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$/;
    const casos = [];
    const caso = (nombre, ruta, test) => casos.push({ nombre, ruta, test });

    // —— Alcance: solo sobre entradas donde las acciones tienen sentido ——
    for (const [ruta, preparar, selector, abre] of [
        [inversa, null, '[name="celda_A_0_0"]', true],
        [inversa, null, '[name="orden"]', false],
        [operaciones, null, '[name="celda_0_0_0"]', true],
        [operaciones, null, '[name="nombre_0"]', false],
        [operaciones, null, '[name="expresion"]', false],
        [reduccion, w => modo(w, "matriz"), '[name="matriz_0_0"]', true],
        [reduccion, w => modo(w, "matriz"), '[name="ecuaciones"]', false],
        [reduccion, w => modo(w, "sistema"), '[name="sistema"]', false],
        [axb, null, '[name="celda_A_0_0"]', true],
        [axb, null, '[name="celda_b_0_0"]', true],
        [axb, null, '[name="filas"]', false],
        [determinantes, null, '[name="celda_A_0_0"]', true],
        [vectores, null, '[name="v1_0"]', true],
        [vectores, null, '[name="dimension"]', false],
        [romanos, null, '[name="numero"]', true],
        [romanos, null, '[name="direccion"]', false],
    ]) caso(`Alcance: ${selector} ${abre ? "abre el menú de edición" : "deja el menú del navegador"} (${ruta})`, ruta, w => {
        preparar?.(w);
        igual(abrir(w, q(w, selector)), abre); igual(menu(w).hidden, !abre);
        if (abre) cerrar(w);
    });
    caso("Alcance: un vector lineal (expresiones) deja el menú del navegador", operaciones, w => {
        cambiar(w, '[name="tipo_0"]', "vector_lineal");
        igual(abrir(w, q(w, '[name="celda_0_0_0"]')), false); igual(menu(w).hidden, true);
    });
    for (const ruta of ["/", "/bases/conversion/"]) caso(`Alcance: sin entradas compatibles no se carga el menú (${ruta})`, ruta, w => {
        igual(menu(w), null); igual(q(w, 'script[src*="menu_edicion.js"]'), null);
        const event = new w.MouseEvent("contextmenu", { bubbles: true, cancelable: true, button: 2 });
        q(w, 'input[type="text"], input[type="search"]').dispatchEvent(event); igual(event.defaultPrevented, false);
    });
    caso("Alcance: el resultado no es una entrada", inversa, async (w, frame) => {
        rellenar(w, q(w, '[name="celda_A_0_0"]')); w = await post(frame);
        const event = new w.MouseEvent("contextmenu", { bubbles: true, cancelable: true, button: 2 });
        q(w, "#resultado").dispatchEvent(event); igual(event.defaultPrevented, false); igual(menu(w).hidden, true);
    });

    // —— Opciones según el tipo de entrada ——
    caso("Matriz cuadrada vacía: Rellenar y los siete comandos; sin Limpiar ni Quitar selección", inversa, w => {
        abrir(w, q(w, '[name="celda_A_1_0"]'));
        igual(titulo(w), "Matriz A"); igual(opciones(w), ["Rellenar aleatoriamente", ...COMANDOS]);
        igual(w.document.activeElement === visibles(w)[0], true);
        igual(menu(w).getAttribute("role"), "menu"); igual(menu(w).getAttribute("aria-describedby"), "menu-edicion-gestos");
        igual(w.document.getElementById(menu(w).getAttribute("aria-labelledby")).textContent, "Matriz A");
        igual(visibles(w).every(i => i.getAttribute("role") === "menuitem" && i.type === "button" && i.tabIndex === -1 && !i.name), true);
        igual(q(w, "[data-seleccion-aumentada]").hidden, true);
        cerrar(w);
    });
    caso("Matriz rectangular: solo los comandos posibles", axb, w => {
        valor(w, '[name="columnas"]', 3); abrir(w, q(w, '[name="celda_A_0_0"]'));
        igual(opciones(w), ["Rellenar aleatoriamente", "Toda la matriz", "Fila actual", "Columna actual", "Diagonal principal"]);
        cerrar(w);
    });
    caso("[A | b]: título, ayuda de b y sin Columna actual desde b", reduccion, w => {
        modo(w, "matriz"); abrir(w, q(w, '[name="matriz_0_3"]'));
        igual(titulo(w), "Matriz aumentada [A | b]"); igual(opciones(w).includes("Columna actual"), false);
        igual(q(w, "[data-seleccion-aumentada]").hidden, false);
        igual(menu(w).getAttribute("aria-describedby"), "menu-edicion-gestos menu-edicion-aumentada");
        cerrar(w); abrir(w, q(w, '[name="matriz_0_0"]')); igual(opciones(w).includes("Columna actual"), true); cerrar(w);
    });
    for (const [ruta, preparar, selector, esperado] of [
        [axb, null, '[name="celda_b_0_0"]', "Vector b"],
        [inversa, w => { q(w, "#aplicaciones").open = true; q(w, '[name="funcion_adicional"][value="vector"]').click(); }, '[name="celda_b_0_0"]', "Vector b"],
        [vectores, null, '[name="v2_1"]', "Vector v2"],
        [operaciones, w => cambiar(w, '[name="tipo_1"]', "vector"), '[name="celda_1_0_0"]', "Vector B"],
        [operaciones, w => cambiar(w, '[name="tipo_1"]', "escalar"), '[name="celda_1_0_0"]', "Escalar B"],
        [vectores, w => q(w, '[name="operacion"][value="escalar"]').click(), '[name="escalar"]', "Escalar k"],
        [romanos, null, '[name="numero"]', "Número arábigo"],
        [romanos, w => q(w, '[name="direccion"][value="romano_a_decimal"]').click(), '[name="numero"]', "Número romano"],
    ]) caso(`${esperado}: solo Rellenar y, con valores, Limpiar (${ruta})`, ruta, w => {
        preparar?.(w); const input = q(w, selector);
        abrir(w, input); igual(titulo(w), esperado); igual(opciones(w), ["Rellenar aleatoriamente"]);
        igual(menu(w).hasAttribute("aria-describedby"), false); cerrar(w);
        input.value = "5"; abrir(w, input); igual(opciones(w), ["Rellenar aleatoriamente", "Limpiar"]); cerrar(w);
    });

    // —— Rellenar aleatoriamente ——
    for (const [ruta, preparar, selector] of [
        [inversa, w => valor(w, '[name="orden"]', 3), '[name="celda_A_1_1"]'],
        [determinantes, w => valor(w, '[name="orden"]', 4), '[name="celda_A_0_0"]'],
        [axb, null, '[name="celda_A_0_0"]'],
        [axb, null, '[name="celda_b_1_0"]'],
        [reduccion, w => modo(w, "matriz"), '[name="matriz_2_3"]'],
        [operaciones, null, '[name="celda_0_1_1"]'],
        [operaciones, w => cambiar(w, '[name="tipo_1"]', "vector"), '[name="celda_1_0_0"]'],
        [vectores, null, '[name="v1_0"]'],
    ]) caso(`Rellenar: enteros de −9 a 9 solo en esa entrada, mismas dimensiones y Deshacer (${selector}, ${ruta})`, ruta, w => {
        preparar?.(w);
        const input = q(w, selector), grupo = celdasDe(input);
        const otras = todos(w, "input.matrix-input").filter(c => !grupo.includes(c));
        otras.forEach((c, i) => { c.value = String(i + 1); });
        const antes = valores(grupo), antesOtras = valores(otras), total = todos(w, "input.matrix-input").length;
        const dimensiones = todos(w, ".dimension-field input").map(c => c.value);
        let eventos = 0; input.form.addEventListener("input", () => eventos++);
        rellenar(w, input);
        ok(grupo.every(c => entero(c.value)), `Valores: ${valores(grupo)}`);
        igual(valores(otras), antesOtras, "Otras entradas"); igual(todos(w, "input.matrix-input").length, total, "Celdas");
        igual(todos(w, ".dimension-field input").map(c => c.value), dimensiones, "Dimensiones");
        igual(eventos, grupo.length, "Un input por celda"); igual(w.document.activeElement === input, true, "Foco");
        igual(menu(w).hidden, true);
        igual(aviso(w), `${titulo(w)}: ${grupo.length === 1 ? "1 celda" : `${grupo.length} celdas`} con enteros aleatorios.`);
        q(w, "[data-deshacer-pegado]").click();
        igual(valores(grupo), antes, "Deshacer"); ok(aviso(w).startsWith("Relleno deshecho: "), aviso(w));
    });
    caso("Rellenar: los extremos del intervalo son −9 y 9", inversa, w => {
        const input = q(w, '[name="celda_A_0_0"]'), grupo = celdasDe(input);
        conAzar(w, 0, () => rellenar(w, input)); igual(valores(grupo), ["-9", "-9", "-9", "-9"]);
        conAzar(w, 0.9999999, () => rellenar(w, input)); igual(valores(grupo), ["9", "9", "9", "9"]);
    });
    caso("Rellenar en una sola celda siempre cambia su valor", operaciones, w => {
        cambiar(w, '[name="tipo_0"]', "escalar");
        const input = q(w, '[name="celda_0_0_0"]'), vistos = new Set();
        for (let i = 0; i < 200; i++) {
            const anterior = input.value; rellenar(w, input);
            ok(entero(input.value) && input.value !== anterior, `${anterior} → ${input.value}`); vistos.add(input.value);
        }
        ok(vistos.size >= 15, `Poca variedad: ${[...vistos]}`);
    });
    caso("Rellenar con una confirmación de costo pendiente (Ax=b sin .workspace-actions): aviso y Deshacer", axb, async (w, frame) => {
        valor(w, '[name="filas"]', 6); valor(w, '[name="columnas"]', 6);
        todos(w, '[data-matriz="A"] input.matrix-input').forEach(c => { const [, , i, j] = c.name.split("_"); c.value = i === j ? "2" : "1"; });
        todos(w, '[data-matriz="b"] input.matrix-input').forEach(c => { c.value = "1"; });
        q(w, '[name="metodo"][value="cramer"]').click(); q(w, '[name="metodo_determinante"][value="cofactores"]').click();
        w = await post(frame);
        ok(q(w, "[data-confirmacion]") && !q(w, ".workspace-actions"), "Confirmación pendiente sin .workspace-actions");
        const input = q(w, '[name="celda_A_0_0"]'), antes = valores(celdasDe(input));
        rellenar(w, input); ok(aviso(w).endsWith("con enteros aleatorios."), aviso(w));
        q(w, "[data-deshacer-pegado]").click(); igual(valores(celdasDe(input)), antes);
    });
    caso("Rellenar: el resultado anterior queda desactualizado", inversa, async (w, frame) => {
        rellenar(w, q(w, '[name="celda_A_0_0"]')); w = await post(frame);
        igual(q(w, "[data-resultado]").dataset.resultado, "vigente");
        rellenar(w, q(w, '[name="celda_A_0_0"]'));
        igual(q(w, "[data-resultado]").dataset.resultado, "desactualizado");
    });
    for (const [ruta, preparar, selectores] of [
        [inversa, null, ['[name="celda_A_0_0"]']],
        [determinantes, w => valor(w, '[name="orden"]', 3), ['[name="celda_A_0_0"]']],
        [axb, null, ['[name="celda_A_0_0"]', '[name="celda_b_0_0"]']],
        [reduccion, w => modo(w, "matriz"), ['[name="matriz_0_0"]']],
        [operaciones, w => valor(w, '[name="expresion"]', "A + B"), ['[name="celda_0_0_0"]', '[name="celda_1_0_0"]']],
        [vectores, null, ['[name="v1_0"]', '[name="v2_0"]']],
    ]) caso(`Rellenar: el servidor acepta los valores generados (${ruta})`, ruta, async (w, frame) => {
        preparar?.(w);
        for (const selector of selectores) rellenar(w, q(w, selector));
        w = await post(frame);
        if (ruta === determinantes) {
            ok(q(w, "[data-eleccion]") && !q(w, "#resultado"), "Analiza antes de calcular");
            w = await post(frame);
        }
        ok(q(w, "#resultado"), "Sin resultado");
        igual(todos(w, ".field-error, .alert.error").filter(e => !e.hidden && e.textContent.trim()).map(e => e.textContent.trim()), []);
    });

    // —— Limpiar ——
    for (const [ruta, preparar, selector] of [
        [inversa, null, '[name="celda_A_0_1"]'],
        [operaciones, null, '[name="celda_1_0_0"]'],
        [reduccion, w => modo(w, "matriz"), '[name="matriz_1_1"]'],
        [vectores, null, '[name="v2_0"]'],
    ]) caso(`Limpiar: vacía solo esa entrada, conserva dimensiones y opciones y se deshace (${ruta})`, ruta, w => {
        preparar?.(w);
        todos(w, "input.matrix-input").forEach((c, i) => { c.value = String(i % 9 + 1); });
        const input = q(w, selector), grupo = celdasDe(input);
        const otras = todos(w, "input.matrix-input").filter(c => !grupo.includes(c));
        const antes = valores(grupo), antesOtras = valores(otras);
        const controles = () => todos(w, "form [name]:not(.matrix-input)")
            .map(c => [c.name, ["radio", "checkbox"].includes(c.type) ? c.checked : c.value]);
        const antesControles = controles();
        limpiar(w, input);
        igual(valores(grupo), grupo.map(() => ""), "Vacía"); igual(valores(otras), antesOtras, "Otras entradas");
        igual(controles(), antesControles, "No es un reinicio de la herramienta");
        igual(aviso(w), `${titulo(w)}: ${grupo.length} celdas vaciadas.`); igual(w.document.activeElement === input, true);
        abrir(w, input); igual(opciones(w).includes("Limpiar"), false); cerrar(w);
        q(w, "[data-deshacer-pegado]").click(); igual(valores(grupo), antes, "Deshacer");
        igual(aviso(w), `Limpieza deshecha: ${grupo.length} celdas restauradas.`);
    });
    caso("Limpiar: editar después invalida su Deshacer con un aviso propio", inversa, w => {
        const input = q(w, '[name="celda_A_0_0"]'); celdasDe(input).forEach(c => { c.value = "4"; });
        limpiar(w, input); valor(w, '[name="celda_A_1_1"]', "2");
        igual(aviso(w), "La limpieza ya no puede deshacerse porque la entrada cambió.");
        igual(w.deshacerPegado.deshacer(), false); igual(q(w, '[name="celda_A_1_1"]').value, "2");
    });

    // —— Número arábigo y romano ——
    caso("Número arábigo: enteros del 1 al 3999 escritos con cifras, extremos incluidos", romanos, w => {
        const input = q(w, '[name="numero"]');
        for (let i = 0; i < 300; i++) {
            rellenar(w, input); ok(/^[1-9]\d{0,3}$/.test(input.value) && Number(input.value) <= 3999, input.value);
        }
        conAzar(w, 0, () => rellenar(w, input)); igual(input.value, "1");
        conAzar(w, 0.9999999, () => rellenar(w, input)); igual(input.value, "3999");
    });
    caso("Número romano: cada entero del 1 al 3999 se escribe como lo lee el backend", romanos, async w => {
        q(w, '[name="direccion"][value="romano_a_decimal"]').click();
        const input = q(w, '[name="numero"]'), pares = [];
        for (let n = 1; n <= 3999; n++) {
            conAzar(w, (n - 0.5) / 3999, () => rellenar(w, input)); pares.push([n, input.value]);
        }
        ok(pares.every(([, texto]) => ROMANO.test(texto) && texto.length <= 15), "Forma canónica y 15 símbolos como máximo");
        const respuesta = await fetch("/__pruebas/romanos/", { method: "POST", body: JSON.stringify(pares) });
        igual(await respuesta.json(), []);
    });
    caso("Número: Limpiar vacía el campo y Ctrl+Z (deshacer nativo) recupera el valor", romanos, w => {
        const input = q(w, '[name="numero"]'); input.focus();
        conAzar(w, 0.5, () => rellenar(w, input)); const generado = input.value;
        limpiar(w, input); igual(input.value, ""); igual(w.document.activeElement === input, true);
        igual(w.document.execCommand("undo"), true); igual(input.value, generado);
        igual(q(w, "[data-estado-pegado]"), null); // Un campo suelto no usa el aviso de las cuadrículas.
    });
    for (const direccion of ["decimal_a_romano", "romano_a_decimal"]) caso(`Número (${direccion}): el servidor convierte el valor generado`, romanos, async (w, frame) => {
        q(w, `[name="direccion"][value="${direccion}"]`).click();
        rellenar(w, q(w, '[name="numero"]')); const generado = q(w, '[name="numero"]').value;
        w = await post(frame);
        ok(q(w, "#resultado"), `Sin resultado para ${generado}`);
        igual(todos(w, ".field-error").map(e => e.textContent.trim()).filter(Boolean), []);
    });

    // —— Selección desde el menú ——
    caso("Seleccionar: comandos sobre la celda del clic derecho, Escape del menú no la borra y Quitar selección", inversa, w => {
        valor(w, '[name="orden"]', 3);
        const seleccion = () => w.seleccionMatricial.activa()?.celdas.map(c => [c.fila, c.columna]) ?? [];
        const celda = q(w, '[name="celda_A_1_2"]');
        accion(w, celda, "Fila actual");
        igual(seleccion(), [[1, 0], [1, 1], [1, 2]]); igual(w.document.activeElement === celda, true);
        igual(q(w, "[data-estado-seleccion]").textContent, "Fila actual de A seleccionada: 3 celdas.");
        accion(w, q(w, '[name="celda_A_0_1"]'), "Columna actual"); igual(seleccion(), [[0, 1], [1, 1], [2, 1]]);
        abrir(w, celda); igual(opciones(w).at(-1), "Quitar selección");
        igual(cerrar(w), true); igual(menu(w).hidden, true); igual(seleccion().length, 3);
        accion(w, celda, "Quitar selección"); igual(seleccion(), []);
        igual(q(w, "[data-estado-seleccion]").textContent, "Selección eliminada.");
    });
    caso("Rellenar y Limpiar abarcan toda la matriz y conservan la selección", inversa, w => {
        const celda = q(w, '[name="celda_A_0_0"]'); accion(w, celda, "Diagonal principal");
        rellenar(w, celda); ok(celdasDe(celda).every(c => entero(c.value)), "Toda la matriz");
        igual(w.seleccionMatricial.activa().celdas.map(c => [c.fila, c.columna]), [[0, 0], [1, 1]]);
        limpiar(w, celda); igual(valores(celdasDe(celda)), ["", "", "", ""]);
        igual(w.seleccionMatricial.activa().celdas.length, 2);
    });

    // —— Teclado, foco y teclado matemático ——
    caso("Teclado: Shift+F10 abre junto al campo; flechas, Inicio/Fin, Tab y Escape devuelven el foco", axb, w => {
        const input = q(w, '[name="celda_A_1_1"]');
        igual(abrir(w, input, { teclado: true }), true);
        const campo = input.getBoundingClientRect(), caja = menu(w).getBoundingClientRect();
        ok(caja.top >= campo.bottom || caja.bottom <= campo.top, "El menú no tapa el campo");
        const items = visibles(w); igual(w.document.activeElement === items[0], true);
        tecla(w, w.document.activeElement, "ArrowUp"); igual(w.document.activeElement === items.at(-1), true);
        tecla(w, w.document.activeElement, "ArrowDown"); igual(w.document.activeElement === items[0], true);
        tecla(w, w.document.activeElement, "End"); igual(w.document.activeElement === items.at(-1), true);
        tecla(w, w.document.activeElement, "Home"); igual(w.document.activeElement === items[0], true);
        igual(tecla(w, w.document.activeElement, "Tab"), true); igual(menu(w).hidden, true); igual(w.document.activeElement === input, true);
        abrir(w, input, { teclado: true }); igual(cerrar(w), true); igual(menu(w).hidden, true); igual(w.document.activeElement === input, true);
    });
    caso("Puntero: con texto seleccionado queda el menú del navegador; desde el teclado, el de edición", inversa, w => {
        const input = q(w, '[name="celda_A_0_0"]'); input.value = "123"; input.focus(); input.setSelectionRange(0, 2);
        const raton = new w.MouseEvent("contextmenu", { bubbles: true, cancelable: true, button: 2 });
        input.dispatchEvent(raton); igual(raton.defaultPrevented, false); igual(menu(w).hidden, true);
        input.setSelectionRange(0, 2);
        const teclado = new w.MouseEvent("contextmenu", { bubbles: true, cancelable: true, button: -1 });
        input.dispatchEvent(teclado); igual(teclado.defaultPrevented, true); cerrar(w);
    });
    caso("Pulsar fuera cierra el menú sin devolver el foco al campo", inversa, w => {
        const input = q(w, '[name="celda_A_0_0"]'); abrir(w, input);
        q(w, ".tool-title").dispatchEvent(new w.PointerEvent("pointerdown", { bubbles: true, cancelable: true }));
        igual(menu(w).hidden, true); igual(w.document.activeElement === input, false);
    });
    caso("El teclado matemático sigue abierto mientras se usa el menú", determinantes, async w => {
        const abierto = () => q(w, ".math-keyboard").hasAttribute("data-abierto");
        const input = q(w, '[name="celda_A_0_0"]'); input.focus(); await turno(w); igual(abierto(), true, "Al enfocar");
        abrir(w, input); await turno(w); igual(abierto(), true, "Menú abierto");
        tecla(w, w.document.activeElement, "ArrowDown"); await turno(w); igual(abierto(), true, "Flechas");
        cerrar(w); await turno(w); igual(abierto(), true, "Escape");
        rellenar(w, input); await turno(w); igual(abierto(), true, "Rellenar");
        igual(w.document.activeElement === input, true);
    });

    caso("Posición: si no cabe debajo ni encima del puntero, queda lo más abajo posible dentro de la ventana", reduccion, async (w, frame) => {
        frame.style.height = "600px"; modo(w, "matriz"); await turno(w);
        abrir(w, q(w, '[name="matriz_0_0"]'), { x: 200, y: 300 }); await turno(w);
        const caja = menu(w).getBoundingClientRect(), alto = w.document.documentElement.clientHeight;
        ok(caja.height > 292 && caja.height < alto - 16, `Altura fuera del supuesto de la prueba: ${caja.height}`);
        ok(Math.abs(caja.bottom - (alto - 8)) < 1.5 && caja.top > 8, JSON.stringify(caja));
        cerrar(w);
    });

    // —— Diseño ——
    for (const [ancho, alto] of [[1280, 650], [744, 521], [320, 650]]) for (const tema of ["light", "dark"]) {
        caso(`Diseño ${tema} ${ancho}×${alto}: cabe en la ventana, sobre el teclado y con los tokens del tema`, reduccion, async (w, frame) => {
            frame.style.width = `${ancho}px`; frame.style.height = `${alto}px`; w.document.documentElement.dataset.theme = tema;
            modo(w, "matriz"); await turno(w);
            const doc = w.document.documentElement;
            abrir(w, q(w, '[name="matriz_2_3"]'), { x: ancho - 4, y: alto - 4 }); await turno(w);
            const caja = menu(w).getBoundingClientRect(), estilo = w.getComputedStyle(menu(w));
            ok(caja.left >= 0 && caja.top >= 0 && caja.right <= doc.clientWidth && caja.bottom <= doc.clientHeight, JSON.stringify(caja));
            igual(doc.scrollWidth <= doc.clientWidth + 1, true, "Sin scroll horizontal");
            igual(estilo.position, "fixed");
            ok(Number(estilo.zIndex) > Number(w.getComputedStyle(q(w, ".math-keyboard")).zIndex), "Sobre el teclado matemático");
            const muestra = w.document.createElement("span"); muestra.style.color = "var(--color-surface-raised)";
            w.document.body.append(muestra); igual(estilo.backgroundColor, w.getComputedStyle(muestra).color); muestra.remove();
            tecla(w, w.document.activeElement, "ArrowDown");
            if (w.document.activeElement.matches(":focus-visible")) {
                const foco = w.getComputedStyle(w.document.activeElement);
                igual(foco.outlineStyle, "solid"); ok(parseFloat(foco.outlineWidth) >= 2.5, foco.outlineWidth);
            }
            cerrar(w);
        });
    }

    let passed = 0;
    for (const { nombre, ruta, test } of casos) {
        const frame = document.createElement("iframe");
        frame.style.width = "1100px"; frame.style.height = "760px";
        const loaded = new Promise(resolve => { frame.onload = resolve; });
        frame.src = ruta; document.body.append(frame); await loaded;
        const item = document.createElement("li");
        try { await test(frame.contentWindow, frame); passed++; item.textContent = `PASS · ${nombre}`; }
        catch (error) { item.textContent = `FAIL · ${nombre}: ${error.message}`; }
        document.querySelector("#resultados").append(item); frame.remove();
    }
    document.querySelector("#total").textContent = `${passed}/${casos.length} PASS`;
})();
