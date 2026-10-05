/* DOM nativo y componente real: uv run --locked python -m tests.teclado_browser. */
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
    const turno = () => new Promise(resolve => setTimeout(resolve, 0));
    const animar = async d => {
        const enlace = d.createElement('link'); enlace.rel = 'stylesheet'; enlace.href = '/dock.css';
        const carga = new Promise(resolve => {enlace.onload = resolve;});
        d.head.append(enlace); await carga;
    };
    const finalizar = async teclado => {
        teclado.getAnimations().forEach(animacion => animacion.finish()); await turno();
    };
    const casos = [
        ["Carga oculta, sin disclosure ni destino implícito", ({d, teclado}) => {
            igual(d.querySelectorAll('.math-keyboard').length, 1);
            igual(teclado.hidden, true); igual(d.querySelector('details'), null);
            igual(teclado.querySelectorAll('button').length, 0);
        }],
        ["Nombres empiezan con etiqueta visible y teclas fuera de Tab", ({a, teclado}) => {
            a.focus(); igual(teclado.hidden, false);
            igual(teclado.getAttribute('aria-live'), null);
            igual([...teclado.querySelectorAll('button')].every(b => b.type === 'button' && b.tabIndex === -1
                && b.getAttribute('aria-label').startsWith(b.textContent) && b.title), true);
        }],
        ["Etiqueta visible distinta de inserción; seis variables", ({tecla, a, inserciones}) => {
            a.focus(); igual(tecla('x1').textContent, 'x₁');
            igual(inserciones().slice(0, 6), ['x1','x2','x3','x4','x5','x6']);
            tecla('x6').click(); igual(a.value, 'x6');
        }],
        ["Cursor en medio y mousedown conserva foco sin blur", ({a, tecla, d}) => {
            a.value = '1234'; a.focus(); a.setSelectionRange(2, 2);
            let salidas = 0; a.addEventListener('blur', () => salidas++);
            const evento = new d.defaultView.MouseEvent('mousedown', {bubbles:true, cancelable:true});
            tecla('x1').dispatchEvent(evento); tecla('x1').click();
            igual([a.value, a.selectionStart, d.activeElement === a, salidas, evento.defaultPrevented], ['12x134',4,true,0,true]);
        }],
        ["Reemplazo de selección en textarea", ({a, tecla}) => {
            a.value = '1234'; a.focus(); a.setSelectionRange(1, 3);
            tecla('x2').click(); igual([a.value, a.selectionStart], ['1x24',3]);
        }],
        ["Reemplazo de selección en celda", ({b, tecla}) => {
            b.value = '1234'; b.focus(); b.setSelectionRange(1, 3);
            tecla('/').click(); igual([b.value, b.selectionStart], ['1/4',2]);
        }],
        ["Nueva ecuación inserta solo salto, nunca punto y coma", ({a, tecla}) => {
            a.focus(); tecla('\n').click(); igual(a.value, '\n');
        }],
        ["Un input que burbujea, sin enviar formulario", ({d, a, tecla}) => {
            let entradas = 0, envios = 0, objetivo = null;
            d.querySelector('form').addEventListener('input', e => {objetivo = e.target; entradas++;});
            d.querySelector('form').addEventListener('submit', e => {e.preventDefault(); envios++;});
            a.focus(); tecla('-').click(); igual([entradas,envios,objetivo === a], [1,0,true]);
        }],
        ["Undo nativo atraviesa escritura, dock y escritura sin cambiar foco", ({d, a, tecla}) => {
            a.focus(); d.execCommand('insertText', false, 'x1 '); tecla('+').click();
            d.execCommand('insertText', false, ' x2'); igual(a.value, 'x1 + x2');
            for (const esperado of ['x1 +','x1 ','']) {
                d.execCommand('undo'); igual([a.value,d.activeElement === a], [esperado,true]);
            }
        }],
        ["Foco directo cambia perfil sin ocultar el dock", ({a, b, teclado, inserciones}) => {
            a.focus(); b.focus(); igual([teclado.hidden,inserciones()], [false,['-','/']]);
            a.focus(); igual([teclado.hidden,inserciones().includes('x1')], [false,true]);
        }],
        ["Otro botón elimina objetivo; una tecla antigua no escribe", ({d, a, b, tecla, teclado}) => {
            b.focus(); const anterior = tecla('-'); d.getElementById('otro').focus(); anterior.click();
            igual([teclado.hidden,a.value,b.value], [true,'','']);
        }],
        ["Campos sin perfil o desconocidos no reciben teclado", async ({d, b, tecla, teclado}) => {
            b.focus(); const anterior = tecla('/'); const ajeno = d.getElementById('ajeno');
            ajeno.focus(); anterior.click(); igual([teclado.hidden,ajeno.value,b.value], [true,'','']);
            ajeno.dataset.perfil = 'desconocido'; ajeno.blur(); ajeno.focus(); await turno();
            igual(teclado.hidden, true);
        }],
        ["Radio, checkbox, select y enlace ocultan", ({d, b, teclado}) => {
            for (const id of ['radio','checkbox','select','enlace']) {
                b.focus(); igual(teclado.hidden, false); d.getElementById(id).focus(); igual(teclado.hidden, true);
            }
        }],
        ["Escape oculta sin editar y no revive por mutaciones", async ({d, a, teclado}) => {
            a.value = 'x1'; a.focus();
            a.dispatchEvent(new d.defaultView.KeyboardEvent('keydown', {key:'Escape',bubbles:true}));
            d.getElementById('celdas').dataset.perfil = 'base-2'; await turno();
            igual([teclado.hidden,a.value,d.activeElement === a], [true,'x1',true]);
        }],
        ["Blur a body elimina destino", async ({b, teclado}) => {
            b.focus(); b.blur(); await turno(); igual(teclado.hidden, true);
        }],
        ["La etiqueta del campo activo conserva el contexto", ({d, a, teclado}) => {
            a.focus(); d.querySelector('label[for=a]').dispatchEvent(
                new d.defaultView.PointerEvent('pointerdown', {bubbles:true}));
            igual([teclado.hidden,d.activeElement === a], [false,true]);
        }],
        ["Campos dinámicos heredan perfil sin listeners individuales", ({d, tecla, inserciones}) => {
            const nuevo = d.createElement('input'); nuevo.type = 'text';
            d.getElementById('celdas').append(nuevo); nuevo.focus();
            igual(inserciones(), ['-','/']); tecla('-').click(); igual(nuevo.value, '-');
        }],
        ["Eliminar objetivo no escribe en reemplazo ni primer campo", async ({b, a, tecla, teclado}) => {
            b.focus(); const anterior = tecla('-'); const nuevo = b.cloneNode(); b.replaceWith(nuevo);
            await turno(); anterior.click(); igual([teclado.hidden,a.value,b.value,nuevo.value], [true,'','','']);
        }],
        ["Disabled, readonly, hidden e inert invalidan sin fallback", async ({d, a, b, teclado}) => {
            a.focus(); d.getElementById('texto').disabled = true; await turno(); igual(teclado.hidden, true);
            b.focus(); b.readOnly = true; await turno(); igual(teclado.hidden, true);
            b.readOnly = false; b.blur(); b.focus(); d.getElementById('celdas').hidden = true;
            await turno(); igual(teclado.hidden, true);
            d.getElementById('celdas').hidden = false; b.blur(); b.focus();
            d.getElementById('celdas').inert = true; await turno(); igual(teclado.hidden, true);
        }],
        ["Bases incluyen dígitos, punto y signo: expectativa P17 corregida", async ({d, b, inserciones}) => {
            b.focus();
            for (const [base, digitos] of [[2,'01'],[8,'01234567'],[10,'0123456789'],[16,'0123456789ABCDEF']]) {
                d.getElementById('celdas').dataset.perfil = `base-${base}`;
                await turno(); igual(inserciones().join(''), digitos + '.-');
            }
        }],
        ["Expresión: paréntesis con retroceso y traspuesta ^T", async ({d, b, tecla, inserciones}) => {
            d.getElementById('celdas').dataset.perfil = 'expresion'; b.focus(); await turno();
            igual(inserciones(), ['()','^T','+','-','=','/']);
            b.value = 'AB'; b.setSelectionRange(1,1); tecla('()').click();
            igual([b.value,b.selectionStart,b.selectionEnd], ['A()B',2,2]);
            tecla('^T').click(); igual(b.value, 'A(^T)B');
        }],
        ["Lineal: seis variables, signos y fracción", async ({d, b, inserciones}) => {
            d.getElementById('celdas').dataset.perfil = 'lineal'; b.focus(); await turno();
            igual(inserciones(), ['x1','x2','x3','x4','x5','x6','+','-','/']);
        }],
        ["Extensión declarativa conserva retroceso", async ({d, b, tecla}) => {
            d.getElementById('celdas').dataset.perfil = 'prueba'; b.focus(); await turno();
            b.value = '12'; b.setSelectionRange(1,1); tecla('()').click();
            igual([b.value,b.selectionStart,b.selectionEnd], ['1()2',2,2]);
        }],
        ["Mostrar campos sin enfocar no crea objetivo", async ({d, teclado}) => {
            d.getElementById('celdas').hidden = true; await turno();
            d.getElementById('celdas').hidden = false; await turno(); igual(teclado.hidden, true);
        }],
        ["Tecla obsoleta no inserta tras cambiar perfil síncronamente", ({d, a, tecla}) => {
            a.focus(); const anterior = tecla('x1');
            d.getElementById('texto').dataset.perfil = 'numerico'; anterior.click(); igual(a.value, '');
        }],
        ["Insertar no regenera teclas ni produce ciclos", async ({a, tecla}) => {
            a.focus(); const boton = tecla('-'); boton.click(); await turno(); igual(tecla('-') === boton, true);
        }],
        ["Fallback sin execCommand respeta selección y un input", ({d, b, tecla}) => {
            d.execCommand = () => false; let eventos = 0; b.addEventListener('input', () => eventos++);
            b.value = '123'; b.focus(); b.setSelectionRange(1,2); tecla('/').click();
            igual([b.value,b.selectionStart,eventos], ['1/3',2,1]);
        }],
        ["Salida conserva las teclas, pierde interacción y termina en hidden", async ({d, a, teclado, tecla}) => {
            await animar(d); a.focus(); await finalizar(teclado); const anterior = tecla('-');
            d.getElementById('otro').focus();
            igual([teclado.hidden,teclado.inert,teclado.hasAttribute('data-abierto')], [false,true,false]);
            igual(teclado.contains(anterior), true); anterior.click(); igual(a.value, '');
            igual(teclado.getAnimations().length > 0, true); await finalizar(teclado);
            igual([teclado.hidden,teclado.querySelectorAll('button').length], [true,0]);
        }],
        ["Cambio directo no reinicia entrada y reapertura invalida cierre anterior", async ({d, a, b, teclado}) => {
            await animar(d); a.focus(); const entrada = teclado.getAnimations();
            igual(entrada.length > 0, true); b.focus();
            const siguientes = teclado.getAnimations();
            igual(siguientes.length === entrada.length && siguientes.every(animacion => entrada.includes(animacion)), true);
            await finalizar(teclado); d.getElementById('otro').focus();
            const cierre = Promise.allSettled(teclado.getAnimations().map(animacion => animacion.finished));
            a.focus(); await finalizar(teclado); await cierre;
            igual([teclado.hidden,teclado.inert,teclado.hasAttribute('data-abierto'),d.activeElement === a], [false,false,true,true]);
        }],
        ["Escape durante entrada oculta sin editar ni revivir por mutaciones", async ({d, a, teclado, tecla}) => {
            await animar(d); a.value = 'x1'; a.focus();
            teclado.getAnimations().forEach(animacion => {animacion.currentTime = animacion.effect.getTiming().duration / 2;});
            const anterior = tecla('-');
            a.dispatchEvent(new d.defaultView.KeyboardEvent('keydown', {key:'Escape',bubbles:true}));
            anterior.click(); d.getElementById('celdas').dataset.perfil = 'base-2';
            await finalizar(teclado);
            igual([teclado.hidden,a.value,d.activeElement === a], [true,'x1',true]);
        }],
    ];
    let aprobadas = 0;
    for (const [nombre, probar] of casos) {
        const frame = document.createElement('iframe'); frame.title = nombre;
        const carga = new Promise(resolve => {frame.onload = resolve;});
        frame.src = '/fixture'; document.body.append(frame); await carga;
        const d = frame.contentDocument; const teclado = d.querySelector('.math-keyboard');
        const tecla = texto => [...teclado.querySelectorAll('button')].find(b => b.dataset.insercion === texto);
        const resultado = document.createElement('li');
        try {
            await probar({d,teclado,tecla,a:d.getElementById('a'),b:d.getElementById('b'),
                inserciones: () => [...teclado.querySelectorAll('button')].map(b => b.dataset.insercion)});
            resultado.textContent = `PASS — ${nombre}`; aprobadas++;
        } catch (error) {resultado.textContent = `FAIL — ${nombre}: ${error.message}`;}
        document.getElementById('resultados').append(resultado); frame.hidden = true;
    }
    document.getElementById('total').textContent = `${aprobadas}/${casos.length} pruebas aprobadas`;
})();
