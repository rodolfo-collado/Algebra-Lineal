/* Ejecutar en tests.teclado_browser: DOM nativo, sin simulaciones del motor. */
(async () => {
    "use strict";
    if (document.readyState !== 'complete') {
        await new Promise(resolve => window.addEventListener('load', resolve, {once: true}));
    }
    const igual = (actual, esperado) => {
        if (JSON.stringify(actual) !== JSON.stringify(esperado)) {
            throw new Error(`${JSON.stringify(actual)} != ${JSON.stringify(esperado)}`);
        }
    };
    const turno = () => new Promise((resolve) => setTimeout(resolve, 0));
    const casos = [
        ["Un componente, plegado y con botones accesibles", ({d, teclado, desplegable}) => {
            igual(d.querySelectorAll('.math-keyboard').length, 1);
            igual([teclado.hidden, desplegable.hidden, desplegable.open], [false, false, false]);
            igual(teclado.getAttribute('aria-live'), null);
            igual([...teclado.querySelectorAll('button')].every(b => b.type === 'button' && b.getAttribute('aria-label') && b.title), true);
        }],
        ["Etiqueta visible distinta de la inserción", ({tecla, a}) => {
            igual(tecla('x1').textContent, 'x₁');
            a.focus(); tecla('x1').click(); igual(a.value, 'x1');
        }],
        ["Inserción en cursor de textarea y foco de vuelta", ({a, tecla, d}) => {
            a.value = '1234'; a.focus(); a.setSelectionRange(2, 2);
            tecla('x1').focus(); tecla('x1').click();
            igual([a.value, a.selectionStart, a.selectionEnd, d.activeElement === a], ['12x134', 4, 4, true]);
        }],
        ["Reemplazo de selección en textarea", ({a, tecla}) => {
            a.value = '1234'; a.focus(); a.setSelectionRange(1, 3);
            tecla('x2').click(); igual([a.value, a.selectionStart], ['1x24', 3]);
        }],
        ["Reemplazo de selección en celda", ({b, tecla}) => {
            b.value = '1234'; b.focus(); b.setSelectionRange(1, 3);
            tecla('/').click(); igual([b.value, b.selectionStart], ['1/4', 2]);
        }],
        ["Nueva ecuación conserva salto de línea", ({a, tecla}) => {
            a.focus(); tecla(';\n').click(); igual(a.value, ';\n');
        }],
        ["Un solo evento input que burbujea, sin enviar formulario", ({d, a, tecla}) => {
            let entradas = 0, envios = 0, objetivo = null;
            d.querySelector('form').addEventListener('input', e => { objetivo = e.target; entradas++; });
            d.querySelector('form').addEventListener('submit', e => { e.preventDefault(); envios++; });
            a.focus(); tecla('-').click(); igual([entradas, envios, objetivo === a], [1, 0, true]);
        }],
        ["Foco cambia el perfil en la misma instancia", ({a, b, teclado, inserciones}) => {
            a.focus(); igual(inserciones().includes('x1'), true);
            b.focus(); igual(inserciones(), ['-', '/']);
            igual(teclado.isConnected, true); a.focus(); igual(inserciones().includes('x1'), true);
        }],
        ["Conserva el último objetivo al usar otro control", ({d, b, tecla}) => {
            b.focus(); d.getElementById('otro').focus(); tecla('-').click(); igual(b.value, '-');
        }],
        ["Ignora campos sin perfil y perfiles desconocidos", async ({d, b, tecla}) => {
            b.focus(); const ajeno = d.getElementById('ajeno');
            ajeno.dataset.perfil = 'desconocido'; ajeno.focus(); await turno();
            tecla('/').click(); igual([ajeno.value, b.value], ['', '/']);
        }],
        ["Campos agregados heredan perfil sin registrar listeners", ({d, tecla, inserciones}) => {
            const nuevo = d.createElement('input'); nuevo.type = 'text';
            d.getElementById('celdas').append(nuevo); nuevo.focus();
            igual(inserciones(), ['-', '/']); tecla('-').click(); igual(nuevo.value, '-');
        }],
        ["Campo eliminado deja de ser objetivo", async ({d, b, tecla}) => {
            b.focus(); const nuevo = b.cloneNode(); b.replaceWith(nuevo);
            d.getElementById('texto').hidden = true; await turno();
            tecla('-').click(); igual([b.value, nuevo.value], ['', '-']);
        }],
        ["Oculto, readonly y fieldset deshabilitado no reciben inserciones", async ({d, a, b, tecla, desplegable}) => {
            a.focus(); d.getElementById('texto').disabled = true; await turno();
            tecla('-').click(); igual([a.value, b.value], ['', '-']);
            b.readOnly = true; await turno(); igual(desplegable.hidden, true);
            b.readOnly = false; d.getElementById('celdas').hidden = true; await turno(); igual(desplegable.hidden, true);
            d.getElementById('texto').disabled = false; await turno(); igual(desplegable.hidden, false);
        }],
        ["Cambio declarativo de bases 2 → 8 → 10 → 16", async ({d, b, inserciones}) => {
            b.focus();
            for (const [base, esperado] of [[2,'01'], [8,'01234567'], [10,'0123456789'], [16,'0123456789ABCDEF']]) {
                d.getElementById('celdas').dataset.perfil = `base-${base}`;
                await turno(); igual(inserciones().join(''), esperado);
            }
        }],
        ["Perfil nuevo con retroceso sin cambiar el motor", async ({d, b, tecla}) => {
            d.getElementById('celdas').dataset.perfil = 'prueba'; b.focus(); await turno();
            b.value = '12'; b.setSelectionRange(1, 1); tecla('()').click();
            igual([b.value, b.selectionStart, b.selectionEnd], ['1()2', 2, 2]);
        }],
        ["Sin objetivos el teclado se oculta y luego se recupera plegado", async ({d, desplegable}) => {
            d.getElementById('texto').hidden = true; d.getElementById('celdas').hidden = true;
            await turno(); igual(desplegable.hidden, true);
            d.getElementById('celdas').hidden = false; await turno();
            igual([desplegable.hidden, desplegable.open], [false, false]);
        }],
        ["Tecla obsoleta no inserta tras cambio síncrono de perfil", ({d, a, tecla}) => {
            a.focus(); const anterior = tecla('x1');
            d.getElementById('texto').dataset.perfil = 'numerico'; anterior.click(); igual(a.value, '');
        }],
        ["No regenera teclas al insertar ni abre details por su cuenta", async ({a, tecla, desplegable}) => {
            a.focus(); const boton = tecla('-'); boton.click(); await turno();
            igual(tecla('-') === boton, true); igual(desplegable.open, false);
        }],
    ];
    let aprobadas = 0;
    for (const [nombre, probar] of casos) {
        const frame = document.createElement('iframe');
        frame.title = nombre;
        const carga = new Promise(resolve => { frame.onload = resolve; });
        frame.src = '/fixture'; document.body.append(frame); await carga;
        const d = frame.contentDocument;
        const teclado = d.querySelector('.math-keyboard');
        const tecla = texto => [...teclado.querySelectorAll('button')].find(b => b.dataset.insercion === texto);
        const resultado = document.createElement('li');
        try {
            await probar({d, teclado, tecla, desplegable: teclado.closest('details'), a:d.getElementById('a'), b:d.getElementById('b'),
                inserciones: () => [...teclado.querySelectorAll('button')].map(b => b.dataset.insercion)});
            resultado.textContent = `PASS — ${nombre}`; aprobadas++;
        } catch (error) {
            resultado.textContent = `FAIL — ${nombre}: ${error.message}`;
        }
        document.getElementById('resultados').append(resultado); frame.hidden = true;
    }
    document.getElementById('total').textContent = `${aprobadas}/${casos.length} pruebas aprobadas`;
})();
