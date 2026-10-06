/* P27.4: scripts y POST reales, incluidos name/value, foco y páginas sin JavaScript. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const igual = (a, b) => {
        if (a?.nodeType || b?.nodeType) {
            if (a !== b) throw new Error(`${a?.nodeName} != ${b?.nodeName}`);
            return;
        }
        if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    };
    const turno = w => new Promise(resolve => w.requestAnimationFrame(() => w.requestAnimationFrame(resolve)));
    const valor = (w, s, value) => {
        const campo = q(w, s); campo.value = String(value);
        campo.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const post = (frame, boton = "[data-calculo]") => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Sin respuesta al POST")), 15000);
        frame.onload = async () => { clearTimeout(timer); await turno(frame.contentWindow); resolve(frame.contentWindow); };
        q(frame.contentWindow, boton).click();
    });
    const envio = (w, boton = "[data-calculo]") => {
        const b = q(w, boton);
        const e = new w.SubmitEvent("submit", { bubbles: true, cancelable: true, submitter: b });
        b.form.dispatchEvent(e); return e;
    };
    const casos = [
        ["GET conserva el foco y no anuncia destinos", "/bases/conversion/", {}, w => {
            igual(w.document.activeElement, w.document.body);
            igual(q(w, "[data-validacion-destinos]").hidden, true);
            igual(q(w, '[aria-invalid="true"]'), null);
        }],
        ["Busy conserva submitter, bloquea segundo click/Enter y pageshow restaura", "/romanos/conversion/", {}, w => {
            const boton = q(w, "[data-calculo]"); const form = boton.form;
            valor(w, '[name="numero"]', 4);
            let aceptados = 0;
            w.document.addEventListener('submit', e => { if (!e.defaultPrevented) aceptados++; });
            const ancho = boton.getBoundingClientRect().width;
            const primero = envio(w);
            igual(primero.defaultPrevented, false); igual(primero.submitter, boton);
            igual(boton.textContent, "Calculando…"); igual(form.getAttribute("aria-busy"), "true");
            igual(boton.disabled, false); igual(boton.getAttribute("aria-disabled"), "true");
            igual(boton.getBoundingClientRect().width, ancho);
            igual(envio(w).defaultPrevented, true); igual(envio(w).defaultPrevented, true);
            igual(aceptados, 1);
            w.dispatchEvent(new w.PageTransitionEvent("pageshow", { persisted: true }));
            igual(boton.textContent, "Convertir"); igual(form.hasAttribute("aria-busy"), false);
            igual(boton.hasAttribute("aria-disabled"), false); igual(boton.hasAttribute("aria-busy"), false);
            igual(boton.style.minWidth, ""); igual(envio(w).defaultPrevented, false);
        }],
        ["Dimensión inválida cancela antes de busy y se puede corregir", "/matrices/inversa/", {}, w => {
            const input = q(w, '[name="orden"]'); valor(w, '[name="orden"]', 0);
            igual(envio(w).defaultPrevented, true); igual(q(w, '[aria-busy="true"]'), null);
            igual(w.document.activeElement, input); igual(input.getAttribute('aria-invalid'), 'true');
            valor(w, '[name="orden"]', 2); igual(input.getAttribute('aria-invalid'), 'false');
        }],
        ["Acción estructural no entra en busy", "/romanos/conversion/", {}, w => {
            const form = q(w, '#romanos-form'); const secundario = w.document.createElement('button');
            secundario.type = 'submit'; secundario.name = 'ajustar'; secundario.value = '1'; form.append(secundario);
            const e = new w.SubmitEvent('submit', {bubbles: true, cancelable: true, submitter: secundario});
            form.dispatchEvent(e); igual(e.defaultPrevented, false); igual(form.hasAttribute('aria-busy'), false);
        }],
        ["POST inválido #resultado enfoca número y conserva ayuda", "/romanos/conversion/", {}, async (w, frame) => {
            valor(w, '[name="numero"]', 0); w = await post(frame);
            const input = q(w, '[name="numero"]'); igual(w.location.hash, '#resultado');
            igual(q(w, '#resultado'), null); igual(w.document.activeElement, input);
            igual(input.getAttribute('aria-invalid'), 'true');
            igual(input.getAttribute('aria-describedby').split(' '), ['numero-ayuda', 'id_numero_error']);
            igual(q(w, '[aria-busy="true"]'), null); igual(q(w, '[data-calculo]').textContent, 'Convertir');
        }],
        ["POST válido conserva el resultado y no enfoca errores", "/romanos/conversion/", {}, async (w, frame) => {
            valor(w, '[name="numero"]', 4); w = await post(frame);
            igual(w.location.hash, '#resultado'); igual(Boolean(q(w, '#resultado')), true);
            igual(q(w, '[aria-invalid="true"]'), null); igual(q(w, '[aria-busy="true"]'), null);
            igual(w.document.activeElement.matches('[aria-invalid="true"], .alert.error'), false);
        }],
        ["Non-field: un alert navegable", "/romanos/conversion/", {}, async (w, frame) => {
            valor(w, '[name="numero"]', 4);
            const ajeno = w.document.createElement('input'); ajeno.name = 'ajeno'; ajeno.value = '1'; ajeno.type = 'hidden';
            q(w, '#romanos-form').append(ajeno); w = await post(frame);
            igual(w.document.activeElement, q(w, '[data-error-general]'));
            igual(w.document.querySelectorAll('.alert.error').length, 1);
            igual(w.document.querySelectorAll('[role="alert"]').length, 1);
        }],
        ["Celda inválida enfoca esa celda y abre teclado contextual", "/matrices/inversa/", {}, async (w, frame) => {
            w.document.querySelectorAll('[name^="celda_"]').forEach(c => { c.value = '1'; });
            valor(w, '[name="celda_A_1_1"]', 'malo'); w = await post(frame);
            igual(w.document.activeElement, q(w, '[name="celda_A_1_1"]'));
            igual(q(w, '.math-keyboard').hidden, false);
            igual(q(w, '[name="celda_A_1_1"]').getAttribute('aria-describedby'), 'id_celda_A_1_1_error');
        }],
        ["Error de expresión enfoca Expresión", "/matrices/operaciones/", {}, async (w, frame) => {
            w.document.querySelectorAll('[name^="celda_"]').forEach(c => {c.value = '1';});
            w = await post(frame);
            igual(w.document.activeElement, q(w, '[name="expresion"]'));
        }],
        ["Matriz aumentada: error de celda enfoca el control generado", "/matrices/reduccion/", {}, async (w, frame) => {
            q(w, '[name="tipo_entrada"][value="matriz"]').click();
            valor(w, '[name="ecuaciones"]', 2); valor(w, '[name="variables"]', 2);
            w.document.querySelectorAll('[name^="matriz_"]').forEach(c => {c.value = '1';});
            valor(w, '[name="matriz_1_2"]', 'malo'); w = await post(frame);
            igual(w.document.activeElement, q(w, '[name="matriz_1_2"]'));
            igual(w.document.activeElement.getAttribute('aria-describedby'), 'id_matriz_1_2_error');
            igual(w.document.activeElement.parentElement.querySelectorAll('[role="alert"]').length, 1);
        }],
        ["Vectores: error de componente conserva asociación tras render inicial", "/vectores/operaciones/", {}, async (w, frame) => {
            w.document.querySelectorAll('[data-cell]').forEach(c => {c.value = '1';});
            valor(w, '[name="u_1"]', 'malo'); w = await post(frame);
            igual(w.document.activeElement, q(w, '[name="u_1"]'));
            igual(w.document.activeElement.getAttribute('aria-describedby'), 'id_u_1_error');
            igual(q(w, '[name="u_1"]').parentElement.querySelectorAll('[role="alert"]').length, 1);
        }],
        ["Dimensión del servidor se anuncia una vez y enfoca la dimensión", "/matrices/reduccion/", {}, async (w, frame) => {
            q(w, '[name="tipo_entrada"][value="matriz"]').click();
            q(w, '[name="ecuaciones"]').value = '999'; q(w, '[name="variables"]').value = '2';
            const loaded = new Promise(resolve => {frame.onload = async () => {await turno(frame.contentWindow); resolve(frame.contentWindow);};});
            w.HTMLFormElement.prototype.submit.call(q(w, '#sistema-form')); w = await loaded;
            igual(w.document.activeElement, q(w, '[name="ecuaciones"]'));
            igual(q(w, '[data-error-field="id_ecuaciones"]').hidden, false);
            igual(q(w, '[name="ecuaciones"]').closest('.dimension-field').querySelector('[data-error-dimension]').hidden, true);
            valor(w, '[name="ecuaciones"]', 2);
            igual(q(w, '[data-error-field="id_ecuaciones"]').hidden, true);
            igual(q(w, '[name="ecuaciones"]').getAttribute('aria-invalid'), 'false');
        }],
        ["Matriz global: mensaje único y primera celda útil", "/matrices/inversa/", {}, async (w, frame) => {
            w.document.querySelectorAll('[name^="celda_"]').forEach(c => { c.value = '1'; });
            q(w, '[name="celda_A_1_1"]').remove(); w = await post(frame);
            igual(w.document.activeElement, q(w, '[name="celda_A_0_0"]'));
            igual(w.document.querySelectorAll('[data-error-group]').length, 1);
            igual(w.document.querySelectorAll('[role="alert"]').length, 1);
            igual(w.document.activeElement.getAttribute('aria-describedby'), 'errores-grupo');
        }],
        ["Foco omite controles hidden, disabled e inert y abre details", "/romanos/conversion/", {}, async w => {
            const form = q(w, '#romanos-form'); form.dataset.respuestaErrores = '';
            const bloque = w.document.createElement('div');
            bloque.innerHTML = '<input aria-invalid="true" hidden><input aria-invalid="true" disabled><div inert><input aria-invalid="true"></div><input aria-invalid="true" style="display:none"><details><summary>Opciones</summary><input id="error-util" aria-invalid="true"></details>';
            form.prepend(bloque); w.dispatchEvent(new w.Event('load')); await turno(w);
            igual(w.document.activeElement, q(w, '#error-util')); igual(q(w, '#error-util').closest('details').open, true);
        }],
        ["Cambio de origen no muestra error; casillas y submit sí; corregir limpia", "/bases/conversion/", {}, w => {
            const origen = q(w, '[name="base_origen"]'); origen.value = '2';
            origen.dispatchEvent(new w.Event('change', {bubbles: true}));
            igual(q(w, '[name="bases_destino"][value="2"]').disabled, true);
            igual(q(w, '[data-validacion-destinos]').hidden, true);
            const destino = q(w, '[name="bases_destino"][value="8"]');
            destino.click(); igual(q(w, '[data-validacion-destinos]').hidden, true);
            destino.click(); igual(q(w, '[data-validacion-destinos]').hidden, false);
            igual(q(w, '[data-destinos]').getAttribute('aria-invalid'), 'true');
            igual(envio(w).defaultPrevented, true); igual(q(w, '[aria-busy="true"]'), null);
            destino.click(); igual(q(w, '[data-validacion-destinos]').hidden, true);
            igual(q(w, '[data-destinos]').hasAttribute('aria-invalid'), false);
            igual(q(w, '[aria-invalid="true"]'), null);
        }],
        ["Servidor + cliente destinos: no duplican, corrección retira el error", "/bases/conversion/", {}, async (w, frame) => {
            // Envío nativo sin ejecutar el validador JS, como un cliente sin JavaScript.
            q(w, '[name="numero"]').value = '4';
            w.document.querySelectorAll('[name="bases_destino"]').forEach(c => { c.checked = false; });
            const loaded = new Promise(resolve => {frame.onload = async () => {await turno(frame.contentWindow); resolve(frame.contentWindow);};});
            w.HTMLFormElement.prototype.submit.call(q(w, '#conversion-form')); w = await loaded;
            igual(q(w, '[data-validacion-destinos]').hidden, true);
            igual(Boolean(q(w, '[data-error-field="id_bases_destino"]')), true);
            igual(w.document.activeElement, q(w, '[name="bases_destino"]:not(:disabled)'));
            igual(envio(w).defaultPrevented, true); igual(q(w, '[data-validacion-destinos]').hidden, true);
            q(w, '[name="bases_destino"]:not(:disabled)').click();
            igual(q(w, '[data-error-field="id_bases_destino"]').hidden, true);
            igual(q(w, '[aria-invalid="true"]'), null);
        }],
        ["Confirmación visible antes de acción; Continuar conserva firma y POST", "/matrices/operaciones/", {}, async (w, frame) => {
            valor(w, '[name="filas_0"]', 10); valor(w, '[name="columnas_0"]', 1);
            valor(w, '[name="filas_1"]', 1); valor(w, '[name="columnas_1"]', 10);
            w.document.querySelectorAll('[name^="celda_"]').forEach(c => {c.value = '1';});
            valor(w, '[name="expresion"]', '(AB)'.repeat(12)); w = await post(frame);
            const confirmacion = q(w, '[data-confirmacion]'); igual(Boolean(confirmacion), true);
            igual(w.document.activeElement, confirmacion);
            igual(Boolean(confirmacion.compareDocumentPosition(q(w, '.workspace-actions')) & w.Node.DOCUMENT_POSITION_FOLLOWING), true);
            const continuar = q(w, '[name="confirmacion"][data-calculo]');
            const firma = continuar.value; igual(firma.length, 64);
            igual(envio(w, '[name="confirmacion"][data-calculo]').defaultPrevented, false);
            igual(new w.FormData(continuar.form, continuar).get('confirmacion'), firma);
            igual(continuar.disabled, false); igual(continuar.textContent, 'Calculando…');
            w.dispatchEvent(new w.PageTransitionEvent('pageshow', {persisted: true}));
            w = await post(frame, '[name="confirmacion"][data-calculo]');
            igual(Boolean(q(w, '#resultado')), true); igual(q(w, '[data-confirmacion]'), null);
        }],
        ["Sin JS: errores mantienen controles utilizables", "/romanos/conversion/", {sinJS: true}, async (w, frame) => {
            q(w, '[name="numero"]').value = '0'; w = await post(frame);
            igual(Boolean(q(w, '[data-error-field="id_numero"]')), true);
            igual(q(w, '[name="numero"]').getAttribute('aria-invalid'), 'true');
            igual(q(w, '[data-calculo]').disabled, false);
        }],
        ["Sin JS: Aplicar, confirmación y Continuar conservan el POST", "/matrices/operaciones/", {sinJS: true}, async (w, frame) => {
            q(w, '[name="filas_0"]').value = '10'; q(w, '[name="columnas_0"]').value = '1';
            q(w, '[name="filas_1"]').value = '1'; q(w, '[name="columnas_1"]').value = '10';
            q(w, '[name="expresion"]').value = '(AB)'.repeat(12);
            w = await post(frame, '[data-aplicar]');
            w.document.querySelectorAll('[name^="celda_"]').forEach(c => {c.value = '1';});
            w = await post(frame); igual(Boolean(q(w, '[data-confirmacion]')), true);
            igual(q(w, '[name="confirmacion"][data-calculo]').disabled, false);
            w = await post(frame, '[name="confirmacion"][data-calculo]');
            igual(Boolean(q(w, '#resultado')), true);
        }],
    ];
    let passed = 0;
    for (const [nombre, ruta, opciones, test] of casos) {
        const frame = document.createElement('iframe');
        frame.style.cssText = 'width:1280px;height:650px';
        if (opciones.sinJS) frame.setAttribute('sandbox', 'allow-same-origin allow-forms');
        frame.src = ruta; const loaded = new Promise(resolve => {frame.onload = resolve;});
        document.body.append(frame); await loaded; await turno(frame.contentWindow);
        const item = document.createElement('li');
        try { await test(frame.contentWindow, frame); passed++; item.textContent = `PASS · ${nombre}`; }
        catch (error) { item.textContent = `FAIL · ${nombre}: ${error.message}`; }
        document.querySelector('#resultados').append(item); frame.remove();
    }
    document.querySelector('#total').textContent = `${passed}/${casos.length} pruebas DOM correctas`;
})();
