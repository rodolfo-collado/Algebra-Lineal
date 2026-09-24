/* Regresiones de interacción sobre formularios reales y scripts de producción. */
(async () => {
    const igual = (a, b) => {
        if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    };
    const click = (w, selector) => w.document.querySelector(selector).click();
    const valor = (w, selector, value) => {
        const input = w.document.querySelector(selector);
        input.value = String(value);
        input.dispatchEvent(new w.Event("input", {bubbles: true}));
    };
    const cantidad = (w, selector) => w.document.querySelectorAll(selector).length;
    const enviar = frame => new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error("Sin respuesta al calcular")), 10000);
        frame.onload = () => { clearTimeout(timeout); resolve(frame.contentWindow); };
        click(frame.contentWindow, '.workspace-actions button');
    });
    const casos = [
        ["Vectores: agregar, eliminar intermedio, conservar orden y mínimo", "vectores", w => {
            igual(cantidad(w, '[data-vector]'), 2);
            igual(cantidad(w, '[aria-label^="Quitar vector"]'), 0);
            click(w, '[data-agregar-vector]'); click(w, '[data-agregar-vector]');
            click(w, '[name="operacion"][value="resta"]');
            igual(cantidad(w, '[data-vector]'), 4);
            valor(w, '[name="v3_0"]', 3); valor(w, '[name="v4_0"]', 4);
            click(w, '[aria-label="Quitar vector v3"]');
            igual(w.document.querySelector('[name="v3_0"]').value, '4');
            click(w, '[aria-label="Quitar vector v3"]');
            igual(cantidad(w, '[data-vector]'), 2);
            igual(cantidad(w, '[aria-label^="Quitar vector"]'), 0);
            click(w, '[data-agregar-vector]');
            igual(w.document.querySelector('[name="v3_0"]').value, '');
        }],
        ["Vectores: suma real de tres y procedimiento", "vectores", async (w, frame) => {
            click(w, '[data-agregar-vector]');
            for (const [n, valores] of [['u',[1,2,3]],['v',[4,5,6]],['v3',[7,8,9]]]) {
                valores.forEach((v, i) => valor(w, `[name="${n}_${i}"]`, v));
            }
            w = await enviar(frame);
            igual(w.document.querySelector('#resultado').textContent.includes('(12, 15, 18)'), true);
            igual(w.document.querySelector('#procedimiento').textContent.includes('1 + 4 + 7'), true);
        }],
        ["Vectores: escalar unario y combinación con mínimo uno", "vectores", w => {
            click(w, '[data-agregar-vector]');
            click(w, '[name="operacion"][value="escalar"]');
            igual(cantidad(w, '[data-vector]'), 1);
            igual(w.document.querySelector('[data-agregar-vector]').hidden, true);
            igual(w.document.querySelector('[name="vectores"]').disabled, true);
            click(w, '[name="operacion"][value="combinacion"]');
            const quitar = w.document.querySelector('[aria-label="Quitar vector v2"]');
            if (quitar) quitar.click();
            igual(cantidad(w, '[data-vector]'), 2); // generador + objetivo
            igual(cantidad(w, '[aria-label^="Quitar vector"]'), 0);
            for (let i = 0; i < 11; i++) click(w, '[data-agregar-vector]');
            igual(cantidad(w, '[data-vector]'), 13);
        }],
        ["Matrices: agregar, quitar intermedia, conservar valores y mínimo", "matrices", w => {
            igual(cantidad(w, '[data-matrix-list] fieldset'), 2);
            click(w, '[data-agregar-matriz]'); click(w, '[data-agregar-matriz]');
            click(w, '[name="operacion"][value="resta"]');
            igual(cantidad(w, '[data-matrix-list] fieldset'), 4);
            valor(w, '[name="celda_C_0_0"]', 3); valor(w, '[name="celda_D_0_0"]', 4);
            click(w, '[aria-label="Quitar matriz C"]');
            igual(w.document.querySelector('[name="celda_C_0_0"]').value, '4');
            click(w, '[aria-label="Quitar matriz C"]');
            igual(cantidad(w, '[data-matrix-list] fieldset'), 2);
            igual(cantidad(w, '[aria-label^="Quitar matriz"]'), 0);
            click(w, '[data-agregar-matriz]');
            igual(w.document.querySelector('[name="celda_C_0_0"]').value, '');
        }],
        ["Matrices: resta real de tres", "matrices", async (w, frame) => {
            click(w, '[name="operacion"][value="resta"]');
            valor(w, '[name="filas"]', 1); valor(w, '[name="columnas"]', 1);
            click(w, '[data-agregar-matriz]');
            for (const [n, v] of [['A',10], ['B',3], ['C',2]]) valor(w, `[name="celda_${n}_0_0"]`, v);
            w = await enviar(frame);
            igual(w.document.querySelector('.panel-final td').textContent.trim(), '5');
            igual(w.document.querySelector('#procedimiento').textContent.includes('10 − 3 − 2'), true);
        }],
        ["Matrices: traspuesta unaria y Ax binario tras cambiar operación", "matrices", w => {
            click(w, '[data-agregar-matriz]');
            click(w, '[name="operacion"][value="traspuesta"]');
            igual(cantidad(w, '[data-matrix-list] fieldset'), 1);
            igual(w.document.querySelector('[data-agregar-matriz]').hidden, true);
            click(w, '[name="operacion"][value="matriz_vector"]');
            igual(cantidad(w, '[data-matrix-list] fieldset'), 2);
            igual(w.document.querySelector('[name="cantidad"]').disabled, true);
            igual(cantidad(w, '[aria-label^="Quitar matriz"]'), 0);
        }],
        ["Matrices: más de diez operandos y nombres después de Z", "matrices", w => {
            valor(w, '[name="filas"]', 1); valor(w, '[name="columnas"]', 1);
            for (let i = 2; i < 28; i++) click(w, '[data-agregar-matriz]');
            igual(cantidad(w, '[data-matrix-list] fieldset'), 28);
            igual(cantidad(w, '[name="celda_AB_0_0"]'), 1);
        }],
    ];
    for (const metodo of ['fila_columna', 'columnas', 'comparar']) {
        casos.push([`Producto rectangular de cuatro: ${metodo}`, 'matrices', async (w, frame) => {
            click(w, '[name="operacion"][value="producto"]');
            click(w, `[name="metodo"][value="${metodo}"]`);
            valor(w, '[name="filas"]', 1); valor(w, '[name="columnas_b"]', 3);
            click(w, '[data-agregar-matriz]'); click(w, '[data-agregar-matriz]');
            valor(w, '[name="columnas_d"]', 1);
            const matrices = {A:[[1,2]], B:[[1,0,2],[0,1,3]], C:[[1,2],[3,4],[5,6]], D:[[1],[2]]};
            for (const [nombre, matriz] of Object.entries(matrices)) matriz.forEach((fila,i) => fila.forEach((v,j) => valor(w, `[name="celda_${nombre}_${i}_${j}"]`, v)));
            w = await enviar(frame);
            igual(w.document.querySelector('.panel-final td').textContent.trim(), '163');
            const texto = w.document.querySelector('#procedimiento').textContent;
            igual(texto.includes('ABCD = ((AB)C)D'), true);
            igual(texto.includes('Resultado intermedio ABC:'), true);
            igual(cantidad(w, '#numeric-mode'), 1);
        }]);
    }
    let passed = 0;
    for (const [nombre, modulo, test] of casos) {
        const frame = document.createElement('iframe');
        frame.src = `/${modulo}/operaciones/`;
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
