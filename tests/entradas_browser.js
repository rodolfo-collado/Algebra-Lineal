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
        ["Vectores: dimensión, cantidad, Suma → Escalar → Suma y escalar recuperado", "/vectores/operaciones/", {}, w => {
            click(w, '[data-agregar-vector]');
            valor(w, '[name="v2_2"]', '8'); valor(w, '[name="v3_2"]', '9');
            valor(w, '[name="dimension"]', 1); valor(w, '[name="vectores"]', 2);
            valor(w, '[name="dimension"]', 3); valor(w, '[name="vectores"]', 3);
            igual(q(w, '[name="v3_2"]').value, '9');
            click(w, '[name="operacion"][value="escalar"]'); valor(w, '[name="escalar"]', '4');
            click(w, '[name="operacion"][value="suma"]');
            igual(q(w, '[name="vectores"]').value, '3');
            igual(q(w, '[name="v2_2"]').value, '8'); igual(q(w, '[name="v3_2"]').value, '9');
            igual(new w.FormData(q(w, 'form#vectores-form')).has('escalar'), false);
            click(w, '[name="operacion"][value="escalar"]'); igual(q(w, '[name="escalar"]').value, '4');
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
        ["Sin JS: Aplicar vectores conserva entradas incompletas y rechaza dimensiones inválidas", "/vectores/operaciones/", { sinJS: true }, async (w, frame) => {
            valor(w, '[name="v1_0"]', '1/'); valor(w, '[name="dimension"]', 4);
            w = await post(frame, '[name="ajustar"]');
            igual(q(w, '[name="v1_0"]').value, '1/'); igual(Boolean(q(w, '[name="v2_3"]')), true);
            valor(w, '[name="dimension"]', 11);
            w = await post(frame, '[name="ajustar"]');
            igual(q(w, '[name="dimension"]').value, '11');
            igual(q(w, '[name="dimension"]').getAttribute('aria-invalid'), 'true');
            igual(q(w, '[name="v1_0"]').value, '1/');
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
        ['/vectores/operaciones/', 'dimension', 'v1_0', null],
        ['/vectores/operaciones/', 'vectores', 'v1_0', null],
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
        ['/matrices/inversa/', 'celda_A_0_0'], ['/vectores/operaciones/', 'v1_0'],
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
