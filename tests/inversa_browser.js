/* P26.9: DOM con scripts y formulario de producción; no duplica aritmética. */
(async () => {
    const igual = (a, b) => {
        if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    };
    const q = (w, selector) => w.document.querySelector(selector);
    const cantidad = (w, selector) => w.document.querySelectorAll(selector).length;
    const click = (w, selector) => q(w, selector).click();
    const valor = (w, selector, value) => {
        const input = q(w, selector);
        input.value = String(value);
        input.dispatchEvent(new w.Event("input", {bubbles: true}));
    };
    const funcion = (w, value) => {
        // Se sigue el recorrido visible: los radios de una sección plegada
        // no son interactuables por teclado ni dejan enfocar sus entradas.
        if (!q(w, '[data-inverse-function]').open) click(w, '[data-inverse-function] > summary');
        click(w, `[name="funcion_adicional"][value="${value}"]`);
    };
    const matriz = (w, nombre, valores) => valores.forEach((fila, i) => fila.forEach((v, j) => valor(w, `[name="celda_${nombre}_${i}_${j}"]`, v)));
    const vector = (w, valores) => valores.forEach((v, i) => valor(w, `[name="celda_b_${i}_0"]`, v));
    const post = (frame, selector = ".workspace-actions button") => new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error("Sin respuesta al enviar formulario")), 10000);
        frame.onload = () => { clearTimeout(timeout); resolve(frame.contentWindow); };
        click(frame.contentWindow, selector);
    });
    const casos = [
        ["2×2: selector visible; 2→3→2 elimina directo y vuelve Gauss-Jordan", {}, w => {
            igual([...w.document.querySelectorAll('[data-aplicar]')].every(button => button.hidden), true);
            igual(q(w, '[data-inverse-method]').hidden, false);
            igual(cantidad(w, '[name="metodo"][type="radio"]'), 2);
            click(w, '[name="metodo"][value="directo_2x2"]');
            valor(w, '[name="orden"]', 3);
            igual(q(w, '[data-inverse-method]').hidden, true);
            igual(cantidad(w, '[name="metodo"][type="radio"]'), 0);
            igual(new w.FormData(q(w, '#inversa-form')).get('metodo'), 'gauss_jordan');
            valor(w, '[name="orden"]', 2);
            igual(q(w, '[data-inverse-method]').hidden, false);
            igual(q(w, '[name="metodo"]:checked').value, 'gauss_jordan');
        }],
        ["Documento inicial 3×3: sin selector, plantilla permite pasar a 2×2", {ruta: '/__pruebas/inicial-3/'}, w => {
            igual(cantidad(w, '[name="metodo"][type="radio"]'), 0);
            igual(q(w, '[data-inverse-method]').hidden, true);
            valor(w, '[name="orden"]', 2);
            igual(cantidad(w, '[name="metodo"][type="radio"]'), 2);
            igual(q(w, '[name="metodo"]:checked').value, 'gauss_jordan');
            igual(q(w, '[name="metodo"][value="directo_2x2"]').disabled, false);
        }],
        ["B/b condicionales: supervivientes, dimensiones heredadas y POST limpio", {}, w => {
            igual(cantidad(w, '[name^="celda_B_"], [name^="celda_b_"]'), 0);
            funcion(w, 'producto');
            igual(cantidad(w, '[name^="celda_B_"]'), 4);
            valor(w, '[name="celda_B_1_0"]', '1/2');
            valor(w, '[name="orden"]', 3);
            igual(cantidad(w, '[name^="celda_B_"]'), 9);
            igual(q(w, '[name="celda_B_1_0"]').value, '1/2');
            funcion(w, 'vector');
            igual(cantidad(w, '[name^="celda_B_"]'), 0);
            igual(cantidad(w, '[name^="celda_b_"]'), 3);
            valor(w, '[name="celda_b_1_0"]', '-3');
            valor(w, '[name="orden"]', 2);
            igual(cantidad(w, '[name^="celda_b_"]'), 2);
            igual(q(w, '[name="celda_b_1_0"]').value, '-3');
            funcion(w, 'producto');
            igual(q(w, '[name="celda_B_1_0"]').value, '1/2');
            funcion(w, 'ninguna');
            igual(cantidad(w, '[name^="celda_B_"], [name^="celda_b_"]'), 0);
            igual([...new w.FormData(q(w, '#inversa-form')).keys()].some(k => k.startsWith('celda_B_') || k.startsWith('celda_b_')), false);
        }],
        ["Radios y entradas adicionales tienen labels; flechas respetan B/b", {}, w => {
            for (const radio of w.document.querySelectorAll('[name="funcion_adicional"]')) {
                igual(Boolean(q(w, `label[for="${radio.id}"]`)), true);
            }
            funcion(w, 'producto');
            const inicio = q(w, '[name="celda_B_0_0"]');
            igual(q(w, `label[for="${inicio.id}"]`).textContent, 'Matriz B, fila 1, columna 1');
            inicio.focus();
            inicio.dispatchEvent(new w.KeyboardEvent('keydown', {key: 'ArrowDown', bubbles: true}));
            igual(w.document.activeElement.name, 'celda_B_1_0');
            funcion(w, 'vector');
            const componente = q(w, '[name="celda_b_0_0"]');
            igual(q(w, `label[for="${componente.id}"]`).textContent, 'Vector b, componente 1');
            componente.focus();
            componente.dispatchEvent(new w.KeyboardEvent('keydown', {key: 'ArrowDown', bubbles: true}));
            igual(w.document.activeElement.name, 'celda_b_1_0');
        }],
        ["Aplicación real Ax=b: x columna [5, −3] y salida obsoleta al editar", {}, async (w, frame) => {
            matriz(w, 'A', [[3, 4], [5, 6]]);
            funcion(w, 'vector'); vector(w, [3, 7]);
            click(w, '[name="verificar"]');
            w = await post(frame);
            igual(cantidad(w, '.panel-final'), 1);
            igual([...w.document.querySelectorAll('.panel-final td')].map(td => td.textContent.trim()), ['5', '-3']);
            igual(q(w, '#procedimiento').compareDocumentPosition(q(w, '.panel-final')) & 4, 4);
            valor(w, '[name="celda_b_0_0"]', 4);
            igual(q(w, '#resultado').hidden, false);
            igual(q(w, '#resultado').dataset.resultado, 'desactualizado');
        }],
        ["Cambio de función invalida resultado anterior", {}, async (w, frame) => {
            matriz(w, 'A', [[3, 4], [5, 6]]);
            w = await post(frame);
            igual(q(w, '#resultado').hidden, false);
            funcion(w, 'traspuesta');
            igual(q(w, '#resultado').hidden, false);
            igual(q(w, '#resultado').dataset.resultado, 'desactualizado');
        }],
        ["Sin JS: Aplicar cambia función y tamaño, conserva B y normaliza método", {sinJS: true}, async (w, frame) => {
            igual(q(w, '[data-aplicar]').hidden, false);
            funcion(w, 'producto');
            w = await post(frame, '[data-aplicar]');
            igual(cantidad(w, '[name^="celda_B_"]'), 4);
            valor(w, '[name="celda_B_1_0"]', '1/2');
            click(w, '[name="metodo"][value="directo_2x2"]');
            valor(w, '[name="orden"]', 3);
            w = await post(frame, '[data-aplicar]');
            igual(cantidad(w, '[name="metodo"][type="radio"]'), 0);
            igual(cantidad(w, '[name^="celda_B_"]'), 9);
            igual(q(w, '[name="celda_B_1_0"]').value, '1/2');
            funcion(w, 'vector');
            w = await post(frame, '[data-aplicar]');
            igual(cantidad(w, '[name^="celda_B_"]'), 0);
            igual(cantidad(w, '[name^="celda_b_"]'), 3);
            valor(w, '[name="orden"]', 2);
            w = await post(frame, '[data-aplicar]');
            igual(q(w, '[name="metodo"]:checked').value, 'gauss_jordan');
        }],
    ];
    let passed = 0;
    for (const [nombre, opciones, test] of casos) {
        const frame = document.createElement('iframe');
        if (opciones.sinJS) frame.setAttribute('sandbox', 'allow-same-origin allow-forms');
        frame.src = opciones.ruta ?? '/matrices/inversa/';
        const loaded = new Promise(resolve => { frame.onload = resolve; });
        document.body.append(frame);
        await loaded;
        const item = document.createElement('li');
        try { await test(frame.contentWindow, frame); passed++; item.textContent = `PASS · ${nombre}`; }
        catch (error) { item.textContent = `FAIL · ${nombre}: ${error.message}`; }
        document.querySelector('#resultados').append(item);
        frame.remove();
    }
    document.querySelector('#total').textContent = `${passed}/${casos.length} PASS`;
})();
