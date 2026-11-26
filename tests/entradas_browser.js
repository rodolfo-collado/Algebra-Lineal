/* P27.1: formularios y scripts de producción, incluida la recuperación de celdas ocultas. */
(async () => {
    const q = (w, selector) => w.document.querySelector(selector);
    const igual = (a, b) => {
        if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    };
    const valor = (w, selector, value) => {
        const input = q(w, selector);
        input.value = String(value);
        input.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const tipo = (w, value) => {
        const input = q(w, '[name="tipo_0"]');
        input.value = value;
        input.dispatchEvent(new w.Event("change", { bubbles: true }));
    };
    const click = (w, selector) => q(w, selector).click();
    const post = (frame, selector) => new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error("Sin respuesta al enviar")), 10000);
        frame.onload = () => { clearTimeout(timeout); resolve(frame.contentWindow); };
        click(frame.contentWindow, selector);
    });
    const casos = [
        ["Matrices: reducir y recuperar filas/columnas, también un valor borrado", "/matrices/operaciones/", {}, w => {
            valor(w, '[name="celda_0_1_1"]', '1/2');
            valor(w, '[name="filas_0"]', 1); valor(w, '[name="columnas_0"]', 1);
            valor(w, '[name="filas_0"]', 2); valor(w, '[name="columnas_0"]', 2);
            igual(q(w, '[name="celda_0_1_1"]').value, '1/2');
            valor(w, '[name="celda_0_1_1"]', '');
            valor(w, '[name="filas_0"]', 1); valor(w, '[name="filas_0"]', 2);
            igual(q(w, '[name="celda_0_1_1"]').value, '');
        }],
        ["Matrices: memoria independiente por tipo y símbolo reindexado", "/matrices/operaciones/", {}, w => {
            valor(w, '[name="celda_0_0_0"]', '7'); valor(w, '[name="celda_0_1_1"]', '9');
            tipo(w, 'escalar'); igual(q(w, '[name="celda_0_0_0"]').value, '');
            valor(w, '[name="celda_0_0_0"]', '3'); tipo(w, 'matriz');
            igual(q(w, '[name="celda_0_0_0"]').value, '7'); igual(q(w, '[name="celda_0_1_1"]').value, '9');
            tipo(w, 'escalar'); igual(q(w, '[name="celda_0_0_0"]').value, '3');
            valor(w, '[name="celda_1_1_1"]', '11'); click(w, '[data-eliminar]');
            valor(w, '[name="filas_0"]', 1); valor(w, '[name="filas_0"]', 2);
            igual(q(w, '[name="celda_0_1_1"]').value, '11');
        }],
        ["Aumentada: b no cambia de significado al aumentar/reducir variables", "/matrices/reduccion/", {}, w => {
            click(w, '[name="tipo_entrada"][value="matriz"]');
            valor(w, '[name="ecuaciones"]', 2); valor(w, '[name="variables"]', 2);
            valor(w, '[name="matriz_1_1"]', '5'); valor(w, '[name="matriz_1_2"]', '17');
            valor(w, '[name="variables"]', 3);
            igual(q(w, '[name="matriz_1_2"]').value, ''); igual(q(w, '[name="matriz_1_3"]').value, '17');
            valor(w, '[name="matriz_1_2"]', '7'); valor(w, '[name="variables"]', 1);
            igual(q(w, '[name="matriz_1_1"]').value, '17');
            valor(w, '[name="ecuaciones"]', 1); valor(w, '[name="ecuaciones"]', 2);
            valor(w, '[name="variables"]', 3);
            igual(['matriz_1_1', 'matriz_1_2', 'matriz_1_3'].map(n => q(w, `[name="${n}"]`).value), ['5', '7', '17']);
            click(w, '[name="tipo_entrada"][value="sistema"]'); click(w, '[name="tipo_entrada"][value="matriz"]');
            igual(q(w, '[name="matriz_1_3"]').value, '17');
        }],
        ["Aumentada: presupuesto conserva nodos y anuncia error junto a dimensiones", "/matrices/reduccion/", {}, w => {
            click(w, '[name="tipo_entrada"][value="matriz"]');
            valor(w, '[name="ecuaciones"]', 12); valor(w, '[name="variables"]', 9);
            const celda = q(w, '[name="matriz_0_0"]'); valor(w, '[name="matriz_0_0"]', '42');
            valor(w, '[name="variables"]', 10);
            igual(q(w, '[name="matriz_0_0"]') === celda, true);
            igual(q(w, '[name="variables"]').getAttribute('aria-invalid'), 'true');
            igual(q(w, '[name="variables"]').closest('.dimension-field').textContent.includes('120 celdas'), true);
            valor(w, '[name="variables"]', 9); igual(q(w, '[name="matriz_0_0"]').value, '42');
        }],
        ["Aumentada: redimensionar mantiene los términos independientes en el POST real", "/matrices/reduccion/", {}, async (w, frame) => {
            click(w, '[name="tipo_entrada"][value="matriz"]');
            valor(w, '[name="ecuaciones"]', 2); valor(w, '[name="variables"]', 2);
            [[1, 0, 2], [0, 1, 3]].forEach((fila, i) => fila.forEach((v, j) => valor(w, `[name="matriz_${i}_${j}"]`, v)));
            valor(w, '[name="variables"]', 3);
            valor(w, '[name="matriz_0_2"]', '99'); valor(w, '[name="matriz_1_2"]', '77');
            valor(w, '[name="variables"]', 2);
            w = await post(frame, '.workspace-actions button');
            const texto = q(w, '#resultado').textContent;
            igual(texto.includes('x₁ = 2'), true); igual(texto.includes('x₂ = 3'), true);
            valor(w, '[name="variables"]', 3);
            igual(q(w, '[name="matriz_0_3"]').value, '2'); igual(q(w, '[name="matriz_1_3"]').value, '3');
        }],
        ["Sin JS: Aplicar matrices conserva valores; Agregar/Eliminar siguen operativos", "/matrices/operaciones/", { sinJS: true }, async (w, frame) => {
            igual(q(w, '[data-aplicar]').hidden, false);
            valor(w, '[name="celda_0_0_0"]', '1/'); valor(w, '[name="filas_0"]', 3);
            w = await post(frame, '[data-aplicar]');
            igual(q(w, '[name="celda_0_0_0"]').value, '1/'); igual(Boolean(q(w, '[name="celda_0_2_1"]')), true);
            w = await post(frame, '[data-agregar]'); igual(q(w, '[name="cantidad"]').value, '3');
            w = await post(frame, '[data-eliminar]'); igual(q(w, '[name="cantidad"]').value, '2');
        }],
        ["Rueda: no cancela el scroll, desenfoca números originales y dinámicos", "/matrices/operaciones/", {}, w => {
            const rueda = input => {
                input.focus();
                const value = input.value;
                const event = new w.WheelEvent('wheel', { deltaY: 100, bubbles: true, cancelable: true });
                input.dispatchEvent(event);
                igual(input.value, value);
                igual(w.document.activeElement === input, false);
                igual(event.defaultPrevented, false);
            };
            rueda(q(w, '[name="filas_0"]'));
            click(w, '[data-agregar]'); rueda(q(w, '[name="columnas_2"]'));
        }],
    ];
    const dimensiones = [
        ['/matrices/operaciones/', 'filas_0', 'celda_0_0_0', null],
        ['/matrices/ecuaciones/', 'filas', 'celda_A_0_0', null],
        ['/matrices/inversa/', 'orden', 'celda_A_0_0', null],
        ['/matrices/reduccion/', 'variables', 'matriz_0_0', '[name="tipo_entrada"][value="matriz"]'],
    ];
    for (const [ruta, dimension, nombreCelda, modo] of dimensiones) {
        casos.push([`${ruta}: dimensiones inválidas conservan nodos, límites y Enter seguro`, ruta, {}, w => {
            if (modo) click(w, modo);
            const input = q(w, `[name="${dimension}"]`);
            const celda = q(w, `[name="${nombreCelda}"]`);
            const stepper = input.closest('.stepper');
            let envios = 0;
            q(w, 'form[id$="-form"]').addEventListener('submit', e => { e.preventDefault(); envios++; });
            for (const invalida of ['', '0', String(Number(input.max) + 1), '1.5']) {
                valor(w, `[name="${dimension}"]`, invalida);
                igual(q(w, `[name="${nombreCelda}"]`) === celda, true);
                igual(input.getAttribute('aria-invalid'), 'true');
                igual(input.closest('.dimension-field').querySelector('[data-error-dimension]').hidden, false);
                input.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
                igual(envios, 0);
            }
            valor(w, `[name="${dimension}"]`, input.min);
            igual(stepper.querySelector('[data-paso="-1"]').disabled, true);
            valor(w, `[name="${dimension}"]`, input.max);
            igual(stepper.querySelector('[data-paso="1"]').disabled, true);
            igual(input.getAttribute('aria-invalid'), 'false');
        }]);
    }
    for (const [ruta, campo] of [
        ['/matrices/operaciones/', 'celda_0_0_0'], ['/matrices/ecuaciones/', 'celda_A_0_0'],
        ['/matrices/inversa/', 'celda_A_0_0'],
    ]) {
        casos.push([`${ruta}: Enter elige Calcular sin activar secundarios`, ruta, {}, w => {
            let submitter;
            const form = q(w, 'form[id$="-form"]');
            form.addEventListener('submit', e => { e.preventDefault(); submitter = e.submitter; });
            q(w, `[name="${campo}"]`).dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
            igual(submitter === form.querySelector('.workspace-actions button'), true);
            w.document.querySelectorAll('[data-aplicar]').forEach(button => igual([button.hidden, button.disabled], [true, true]));
            if (ruta === '/matrices/operaciones/') igual(q(w, '[name="cantidad"]').value, '2');
        }]);
    }
    // Cuadrículas `celda_<matriz>_<i>_<j>` de Determinantes, Inversa y Ax=b: el JS construye
    // el mismo marcado que Aplicar sin JavaScript y las flechas no salen de la matriz.
    const descriptor = fieldset => ({
        matriz: fieldset.dataset.matriz, vector: fieldset.hasAttribute("data-vector"),
        leyenda: fieldset.querySelector("legend").textContent.replace(/\s+/g, " ").trim(),
        region: fieldset.querySelector(".matrix-scroll").getAttribute("aria-label"),
        tabla: fieldset.querySelector("table").getAttribute("aria-label"),
        celdas: [...fieldset.querySelectorAll("tbody tr")].map(tr => [...tr.children].map(td => {
            const input = td.querySelector("input");
            const label = td.querySelector("label");
            return {
                atributos: [...input.attributes].filter(a => a.name !== "value").map(a => `${a.name}=${a.value}`).sort(),
                valor: input.value, etiqueta: label.textContent.trim(), para: label.htmlFor === input.id,
            };
        })),
    });
    const servidor = async (w, form) => {
        // El mismo POST que Aplicar en el flujo sin JavaScript.
        const datos = new w.FormData(form);
        datos.append("ajustar", "1");
        const respuesta = await w.fetch(form.action, { method: "POST", body: datos });
        return new w.DOMParser().parseFromString(await respuesta.text(), "text/html");
    };
    const tecla = (w, input, key, { inicio = 0, fin = inicio, ...opciones } = {}) => {
        input.focus(); input.setSelectionRange(inicio, fin);
        const event = new w.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...opciones });
        input.dispatchEvent(event);
        return event.defaultPrevented;
    };
    const DIRECCIONES = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
    const abrirAplicaciones = w => { if (!q(w, "#aplicaciones").open) click(w, "#aplicaciones > summary"); };
    const cuadriculas = [
        ["Determinantes", "/matrices/determinantes/", w => valor(w, '[name="orden"]', 3),
            [["A", 3, 3]], '[name="orden"]', null],
        ["Inversa con B", "/matrices/inversa/", w => {
            valor(w, '[name="orden"]', 3); abrirAplicaciones(w);
            click(w, '[name="funcion_adicional"][value="producto"]');
        }, [["A", 3, 3], ["B", 3, 3]], '[name="orden"]', '[name="funcion_adicional"][value="producto"]'],
        ["Inversa con b", "/matrices/inversa/", w => {
            valor(w, '[name="orden"]', 2); abrirAplicaciones(w);
            click(w, '[name="funcion_adicional"][value="vector"]');
        }, [["A", 2, 2], ["b", 2, 1]], '[name="orden"]', '[name="funcion_adicional"][value="vector"]'],
        ["Ax=b rectangular", "/matrices/ecuaciones/", w => {
            valor(w, '[name="filas"]', 2); valor(w, '[name="columnas"]', 3);
        }, [["A", 2, 3], ["b", 2, 1]], '[name="columnas"]', '[name="metodo"][value="gauss_jordan"]'],
    ];
    for (const [titulo, ruta, preparar, matrices, dimension, radio] of cuadriculas) {
        casos.push([`${titulo}: el JS construye el marcado de Aplicar y restaura lo escrito`, ruta, {}, async w => {
            preparar(w);
            const form = q(w, 'form[id$="-form"]');
            for (const [nombre, m, n] of matrices) {
                for (let i = 0; i < m; i++) for (let j = 0; j < n; j++) valor(w, `[name="celda_${nombre}_${i}_${j}"]`, `${nombre}${i}${j}`);
            }
            // Reducir y volver a crecer redibuja todas las celdas desde la memoria local.
            const campo = q(w, dimension);
            const tamano = Number(campo.value);
            valor(w, dimension, tamano - 1); valor(w, dimension, tamano);
            const html = await servidor(w, form);
            for (const [nombre] of matrices) {
                const local = q(w, `[data-matriz="${nombre}"]`);
                igual(descriptor(local), descriptor(html.querySelector(`[data-matriz="${nombre}"]`)));
            }
            igual(q(w, `[name="celda_${matrices[0][0]}_0_0"]`).value, `${matrices[0][0]}00`);
        }]);
        casos.push([`${titulo}: flechas dentro de cada matriz, sin cruzar a la vecina`, ruta, {}, w => {
            preparar(w);
            for (const [nombre, m, n] of matrices) {
                for (let i = 0; i < m; i++) for (let j = 0; j < n; j++) {
                    for (const [key, [di, dj]] of Object.entries(DIRECCIONES)) {
                        const origen = q(w, `[name="celda_${nombre}_${i}_${j}"]`);
                        origen.value = "-1/2";
                        const destino = q(w, `[name="celda_${nombre}_${i + di}_${j + dj}"]`);
                        const movido = tecla(w, origen, key, { inicio: key === "ArrowRight" ? 4 : 0 });
                        igual([`${nombre}${i}${j}${key}`, movido, w.document.activeElement === (destino ?? origen)],
                            [`${nombre}${i}${j}${key}`, Boolean(destino), true]);
                    }
                }
            }
        }]);
        casos.push([`${titulo}: cursor, selección, modificadores, IME y destinos inactivos`, ruta, {}, w => {
            preparar(w);
            const [nombre] = matrices[0];
            const origen = q(w, `[name="celda_${nombre}_1_0"]`);
            origen.value = "-12/7";
            for (const [key, extremo] of [["ArrowLeft", 0], ["ArrowRight", 5]]) {
                for (const opciones of [{ inicio: 2 }, { inicio: 1, fin: 3 }, { inicio: 0, fin: 5 },
                    ...[{ ctrlKey: true }, { shiftKey: true }, { altKey: true }, { metaKey: true },
                        { isComposing: true }, { keyCode: 229 }].map(o => ({ inicio: extremo, ...o }))]) {
                    igual([key, opciones, tecla(w, origen, key, opciones)], [key, opciones, false]);
                    igual(w.document.activeElement === origen, true);
                }
            }
            origen.addEventListener("keydown", event => event.preventDefault(), { once: true });
            tecla(w, origen, "ArrowUp");
            igual(w.document.activeElement === origen, true);
            const arriba = q(w, `[name="celda_${nombre}_0_0"]`);
            for (const inactivo of ["disabled", "readOnly"]) {
                arriba[inactivo] = true;
                igual([inactivo, tecla(w, origen, "ArrowUp"), w.document.activeElement === origen], [inactivo, false, true]);
                arriba[inactivo] = false;
            }
            const mismo = q(w, `[name="celda_${nombre}_1_0"]`);
            mismo.readOnly = true;
            igual(tecla(w, mismo, "ArrowUp"), false);
            mismo.readOnly = false;
            igual(tecla(w, origen, "ArrowUp"), true);
            igual(w.document.activeElement === arriba, true);
            // Las flechas de otros controles siguen siendo suyas.
            for (const otro of [dimension, radio].filter(Boolean)) {
                const control = q(w, otro);
                control.focus();
                const event = new w.KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true, cancelable: true });
                control.dispatchEvent(event);
                igual([otro, event.defaultPrevented, w.document.activeElement === control], [otro, false, true]);
            }
        }]);
    }
    casos.push(["Ax=b: tras redimensionar, las flechas usan las celdas nuevas y b sigue aparte", "/matrices/ecuaciones/", {}, w => {
        valor(w, '[name="filas"]', 2); valor(w, '[name="columnas"]', 2);
        click(w, '.stepper [data-paso="1"]');
        igual([q(w, '[name="filas"]').value, Boolean(q(w, '[name="celda_A_2_1"]')), Boolean(q(w, '[name="celda_b_2_0"]'))], ["3", true, true]);
        const ultima = q(w, '[name="celda_A_2_1"]');
        igual(tecla(w, ultima, "ArrowRight"), false);
        igual(tecla(w, ultima, "ArrowUp"), true);
        igual(w.document.activeElement.name, "celda_A_1_1");
        igual(tecla(w, q(w, '[name="celda_b_2_0"]'), "ArrowUp"), true);
        igual(w.document.activeElement.name, "celda_b_1_0");
        igual(tecla(w, q(w, '[name="celda_b_1_0"]'), "ArrowLeft"), false);
    }]);
    let passed = 0;
    for (const [nombre, ruta, opciones, test] of casos) {
        const frame = document.createElement('iframe');
        if (opciones.sinJS) frame.setAttribute('sandbox', 'allow-same-origin allow-forms');
        frame.src = ruta;
        const loaded = new Promise(resolve => { frame.onload = resolve; });
        document.body.append(frame); await loaded;
        const item = document.createElement('li');
        try { await test(frame.contentWindow, frame); passed++; item.textContent = `PASS · ${nombre}`; }
        catch (error) { item.textContent = `FAIL · ${nombre}: ${error.message}`; }
        document.querySelector('#resultados').append(item); frame.remove();
    }
    document.querySelector('#total').textContent = `${passed}/${casos.length} PASS`;
})();
