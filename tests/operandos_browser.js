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
            for (const [n, valores] of [['v1',[1,2,3]],['v2',[4,5,6]],['v3',[7,8,9]]]) {
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
        // Operaciones con matrices (P26.6): símbolos con nombre y una expresión; el presupuesto común vive en expresiones.js.
        ["Matrices: agregar, eliminar uno intermedio, conservar valores y nombres", "matrices", w => {
            igual(cantidad(w, '[data-simbolo]'), 2);
            click(w, '[data-agregar]'); click(w, '[data-agregar]');
            igual(cantidad(w, '[data-simbolo]'), 4);
            igual([...w.document.querySelectorAll('[data-campo="nombre"]')].map(i => i.value), ['A', 'B', 'C', 'D']);
            valor(w, '[name="celda_2_0_0"]', 3); valor(w, '[name="celda_3_0_0"]', 4);
            w.document.querySelectorAll('[data-eliminar]')[2].click();
            // D conserva su nombre y sus valores; solo cambia su posición en el envío.
            igual(w.document.querySelector('[name="nombre_2"]').value, 'D');
            igual(w.document.querySelector('[name="celda_2_0_0"]').value, '4');
            igual(w.document.querySelector('[name="cantidad"]').value, '3');
            w.document.querySelectorAll('[data-eliminar]')[2].click();
            igual(cantidad(w, '[data-simbolo]'), 2);
            click(w, '[data-agregar]');
            igual(w.document.querySelector('[name="nombre_2"]').value, 'C');
            igual(w.document.querySelector('[name="celda_2_0_0"]').value, '');
        }],
        ["Matrices: resta real de tres, agrupada por la izquierda", "matrices", async (w, frame) => {
            click(w, '[data-agregar]');
            for (let i = 0; i < 3; i++) { valor(w, `[name="filas_${i}"]`, 1); valor(w, `[name="columnas_${i}"]`, 1); }
            for (const [i, v] of [[0, 10], [1, 3], [2, 2]]) valor(w, `[name="celda_${i}_0_0"]`, v);
            valor(w, '[name="expresion"]', 'A - B - C');
            w = await enviar(frame);
            igual(w.document.querySelector('.panel-final td').textContent.trim(), '5');
            const texto = w.document.querySelector('#procedimiento').textContent;
            igual([texto.includes('10 − 3'), texto.includes('7 − 2')], [true, true]);
        }],
        ["Matrices: más de diez símbolos y nombres después de Z", "matrices", w => {
            for (let i = 2; i < 28; i++) click(w, '[data-agregar]');
            igual(cantidad(w, '[data-simbolo]'), 28);
            igual(w.document.querySelector('[name="nombre_26"]').value, 'A1');
            igual(w.document.querySelector('[name="nombre_27"]').value, 'B1');
            igual(cantidad(w, '[name="celda_27_1_1"]'), 1);
        }],
        ["Matrices: tope de 50 símbolos", "matrices", w => {
            for (let i = 2; i < 60; i++) click(w, '[data-agregar]');
            igual(cantidad(w, '[data-simbolo]'), 50);
            igual(w.document.querySelector('[data-agregar]').disabled, true);
            igual(w.document.querySelector('[name="cantidad"]').value, '50');
            w.document.querySelectorAll('[data-eliminar]')[49].click();
            igual(w.document.querySelector('[data-agregar]').disabled, false);
        }],
        ["Matrices: el presupuesto de celdas detiene Agregar", "matrices", w => {
            for (let i = 2; i < 9; i++) click(w, '[data-agregar]');
            for (let i = 0; i < 9; i++) { valor(w, `[name="filas_${i}"]`, 10); valor(w, `[name="columnas_${i}"]`, 10); }
            igual(cantidad(w, '[name^="celda_"]'), 900);
            click(w, '[data-agregar]');
            igual(cantidad(w, '[data-simbolo]'), 9);
            igual(w.document.querySelector('[data-presupuesto]').textContent.includes('Los 10 símbolos sumarían 904 celdas'), true);
            valor(w, '[name="filas_8"]', 9);
            click(w, '[data-agregar]');
            igual(cantidad(w, '[data-simbolo]'), 10);
        }],
        ["Matrices: una dimensión o un tipo que no caben conservan la cuadrícula", "matrices", w => {
            for (let i = 2; i < 10; i++) click(w, '[data-agregar]');
            for (let i = 0; i < 9; i++) { valor(w, `[name="filas_${i}"]`, 10); valor(w, `[name="columnas_${i}"]`, i === 8 ? 9 : 10); }
            igual(cantidad(w, '[name^="celda_"]'), 894);
            valor(w, '[name="filas_9"]', 10);
            igual(cantidad(w, '[name^="celda_9_"]'), 4);
            igual(w.document.querySelector('[data-presupuesto]').textContent.includes('sumarían 910 celdas'), true);
            // Con el presupuesto justo (900), un stepper que no cabe tampoco cambia el número.
            valor(w, '[name="filas_9"]', 2); valor(w, '[name="columnas_9"]', 5);
            igual(cantidad(w, '[name^="celda_"]'), 900);
            const mas = nombre => w.document.querySelector(`[name="${nombre}"]`).closest('.stepper').querySelector('[data-paso="1"]');
            mas('columnas_9').click(); mas('filas_9').click();
            igual(['filas_9', 'columnas_9'].map(n => w.document.querySelector(`[name="${n}"]`).value), ['2', '5']);
            igual(cantidad(w, '[name^="celda_"]'), 900);
            // Una matriz desconocida no dibuja celdas; volverla matriz 10×10 no cabe y recupera el tipo.
            valor(w, '[name="filas_9"]', 2); valor(w, '[name="columnas_9"]', 3);
            const tipo = w.document.querySelector('[name="tipo_9"]');
            tipo.value = 'matriz_desconocida'; tipo.dispatchEvent(new w.Event('change', {bubbles: true}));
            valor(w, '[name="filas_9"]', 10); valor(w, '[name="columnas_9"]', 10);
            igual(cantidad(w, '[name^="celda_9_"]'), 0);
            tipo.value = 'matriz'; tipo.dispatchEvent(new w.Event('change', {bubbles: true}));
            igual(tipo.value, 'matriz_desconocida');
            igual(cantidad(w, '[name^="celda_9_"]'), 0);
        }],
        ["Matrices: las flechas recorren la cuadrícula de un símbolo", "matrices", w => {
            const tecla = (selector, key) => w.document.querySelector(selector).dispatchEvent(new w.KeyboardEvent('keydown', {key, bubbles: true}));
            w.document.querySelector('[name="celda_0_0_0"]').focus();
            tecla('[name="celda_0_0_0"]', 'ArrowRight');
            igual(w.document.activeElement.name, 'celda_0_0_1');
            tecla('[name="celda_0_0_1"]', 'ArrowDown');
            igual(w.document.activeElement.name, 'celda_0_1_1');
            // El borde no salta a otro símbolo.
            tecla('[name="celda_0_1_1"]', 'ArrowDown');
            igual(w.document.activeElement.name, 'celda_0_1_1');
        }],
        ["Matrices: cantidad manipulada vuelve a una estructura segura", "matrices", async (w, frame) => {
            w.document.querySelector('[name="cantidad"]').value = '100000';
            w = await enviar(frame);
            igual(w.document.querySelector('.alert.error').textContent.includes('hasta 50 símbolos'), true);
            igual(cantidad(w, '[data-simbolo]'), 0);
            click(w, '[data-agregar]');
            igual(cantidad(w, '[data-simbolo]'), 1);
            igual(w.document.querySelector('[name="cantidad"]').value, '1');
        }],
        ["Vectores: tope de 50 vectores con aviso", "vectores", w => {
            for (let i = 2; i < 60; i++) click(w, '[data-agregar-vector]');
            igual(cantidad(w, '[data-vector]'), 50);
            igual(w.document.querySelector('[data-agregar-vector]').disabled, true);
            igual(w.document.querySelector('[data-limite-operandos]').hidden, false);
            click(w, '[name="operacion"][value="escalar"]');
            igual(w.document.querySelector('[data-limite-operandos]').hidden, true);
        }],
    ];
    for (const metodo of ['fila_columna', 'columnas', 'comparar']) {
        casos.push([`Producto rectangular de cuatro: ${metodo}`, 'matrices', async (w, frame) => {
            click(w, '[data-agregar]'); click(w, '[data-agregar]');
            const matrices = [[[1, 2]], [[1, 0, 2], [0, 1, 3]], [[1, 2], [3, 4], [5, 6]], [[1], [2]]];
            matrices.forEach((matriz, k) => {
                valor(w, `[name="filas_${k}"]`, matriz.length); valor(w, `[name="columnas_${k}"]`, matriz[0].length);
                matriz.forEach((fila, i) => fila.forEach((v, j) => valor(w, `[name="celda_${k}_${i}_${j}"]`, v)));
            });
            valor(w, '[name="expresion"]', 'ABCD');
            click(w, `[name="metodo"][value="${metodo}"]`);
            w = await enviar(frame);
            igual(w.document.querySelector('.panel-final td').textContent.trim(), '163');
            const texto = w.document.querySelector('#procedimiento').textContent;
            // El árbol agrupa ((AB)C)D: cada producto intermedio cierra con su valor.
            igual(['AB =', 'ABC ='].map(t => texto.includes(t)), [true, true]);
            if (metodo !== 'columnas') igual(texto.includes('(ABCD)₁₁ = fila₁(ABC) · columna₁(D)'), true);
            if (metodo !== 'fila_columna') igual(texto.includes('ABCD = [ABCd₁'), true);
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
