/* Dibuja datos del motor: regiones, elementos, tramos y cantidades llegan calculados.
   Aquí solo hay geometría (dónde está cada círculo o cada extremo) y estados de resaltado. */
(() => {
    'use strict';
    const NS = 'http://www.w3.org/2000/svg';
    const el = (tipo, attrs = {}, texto) => {
        const nodo = document.createElementNS(NS, tipo);
        for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null) nodo.setAttribute(k, v);
        if (texto !== undefined) nodo.textContent = texto;
        return nodo;
    };
    let secuencia = 0;

    /* —— Geometría fija de Venn (viewBox 320 × 240) ——
       `cajas`: ancho, alto y desplazamiento del campo editable que cabe en cada región. */
    const ANCHO = 320, ALTO = 240, MARCO = { x: 6, y: 6, width: 308, height: 228, rx: 12 };
    const GEOMETRIA = {
        1: { circulos: [[160, 118, 84]], nombres: [[86, 38]], anclas: { 0: [18, 222], 1: [160, 118] }, pequenas: [],
             cajas: { 0: [92, 26], 1: [112, 92] } },
        2: { circulos: [[124, 120, 80], [196, 120, 80]], nombres: [[50, 40], [270, 40]],
             anclas: { 0: [18, 222], 1: [88, 120], 2: [232, 120], 3: [160, 120] }, pequenas: [3],
             cajas: { 0: [92, 26], 1: [58, 92, -5, 0], 2: [58, 92, 5, 0], 3: [62, 84] } },
        3: { circulos: [[130, 94, 70], [190, 94, 70], [160, 148, 70]], nombres: [[56, 30], [264, 30], [252, 214]],
             anclas: { 0: [18, 226], 1: [100, 78], 2: [220, 78], 3: [160, 64], 4: [160, 190], 5: [124, 136], 6: [196, 136], 7: [160, 114] },
             pequenas: [3, 5, 6, 7],
             cajas: { 0: [80, 24], 1: [46, 36, -10, -2], 2: [46, 36, 10, -2], 3: [46, 28], 4: [84, 32, 0, 2],
                      5: [32, 30, -10, 5], 6: [32, 30, 10, 5], 7: [46, 34] } },
    };

    function mascaraEn(geo, x, y) {
        if (x < MARCO.x || y < MARCO.y || x > MARCO.x + MARCO.width || y > MARCO.y + MARCO.height) return null;
        return geo.circulos.reduce((m, [cx, cy, r], i) => (Math.hypot(x - cx, y - cy) <= r ? m | (1 << i) : m), 0);
    }

    // Una región = el marco recortado por los círculos que la contienen y enmascarado por los demás.
    function region(defs, geo, mascara, prefijo, clase) {
        const id = `${prefijo}-${mascara}`;
        const mascaraSvg = el('mask', { id: `${id}-m`, maskUnits: 'userSpaceOnUse', x: 0, y: 0, width: ANCHO, height: ALTO });
        mascaraSvg.append(el('rect', { x: 0, y: 0, width: ANCHO, height: ALTO, fill: 'white' }));
        const raiz = el('g');
        let actual = raiz;
        geo.circulos.forEach(([cx, cy, r], i) => {
            if (mascara & (1 << i)) {
                const clip = el('clipPath', { id: `${id}-c${i}` });
                clip.append(el('circle', { cx, cy, r }));
                defs.append(clip);
                const g = el('g', { 'clip-path': `url(#${id}-c${i})` });
                actual.append(g);
                actual = g;
            } else mascaraSvg.append(el('circle', { cx, cy, r, fill: 'black' }));
        });
        defs.append(mascaraSvg);
        const rect = el('rect', { ...MARCO, mask: `url(#${id}-m)`, class: clase });
        actual.append(rect);
        return { raiz, rect, hoja: actual };
    }

    // Elementos escritos dentro de su región: líneas cortas y «+k» cuando no caben.
    function lineas(etiquetas, pequena) {
        const maximo = pequena ? 8 : 13, filas = pequena ? 2 : 3;
        const cortar = t => (t.length > maximo ? `${t.slice(0, maximo - 1)}…` : t);
        const salida = [];
        let i = 0;
        while (i < etiquetas.length && salida.length < filas) {
            let linea = cortar(etiquetas[i++]);
            while (i < etiquetas.length && `${linea}, ${etiquetas[i]}`.length <= maximo) linea += `, ${etiquetas[i++]}`;
            salida.push(linea);
        }
        if (i < etiquetas.length) {
            const resto = `+${etiquetas.length - i}`;
            if (salida.length === filas) salida[filas - 1] = `${salida[filas - 1].slice(0, Math.max(1, maximo - resto.length - 1))} ${resto}`;
            else salida.push(resto);
        }
        return salida;
    }

    // Base de cualquier diagrama: marco, una región por máscara, círculos y nombres.
    function lienzoVenn(venn, atributos) {
        const geo = GEOMETRIA[venn.nombres.length];
        const prefijo = `venn${++secuencia}`;
        const svg = el('svg', { viewBox: `0 0 ${ANCHO} ${ALTO}`, class: 'venn-lienzo-interactivo', ...atributos });
        const defs = el('defs');
        const trama = el('pattern', { id: `${prefijo}-trama`, width: 7, height: 7, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)', class: 'venn-trama' });
        trama.append(el('line', { x1: 0, y1: 0, x2: 0, y2: 7 }));
        defs.append(trama);
        svg.append(defs, el('rect', { ...MARCO, class: 'venn-marco' }));
        const rellenos = new Map();
        for (const r of venn.regiones) {
            const { raiz, rect, hoja } = region(defs, geo, r.mascara, prefijo, `venn-relleno${r.seleccionada ? ' es-seleccionada' : ''}`);
            rect.dataset.region = r.mascara;
            if (r.seleccionada) hoja.append(el('rect', { ...MARCO, mask: rect.getAttribute('mask'), class: 'venn-relleno-trama', fill: `url(#${prefijo}-trama)` }));
            rellenos.set(r.mascara, rect);
            svg.append(raiz);
        }
        geo.circulos.forEach(([cx, cy, r], i) => {
            svg.append(el('circle', { cx, cy, r, class: 'venn-circulo' }));
            const [x, y] = geo.nombres[i];
            svg.append(el('text', { x, y, 'text-anchor': 'middle', class: 'venn-nombre' }, venn.nombres[i]));
        });
        if (venn.universo || venn.regiones.some(r => r.mascara === 0 && r.exterior_conocido)) {
            svg.append(el('text', { x: 306, y: 26, 'text-anchor': 'end', class: 'venn-nombre' }, venn.universo || 'U'));
        }
        const enPunto = event => {
            const p = svg.createSVGPoint();
            p.x = event.clientX; p.y = event.clientY;
            const local = p.matrixTransform(svg.getScreenCTM().inverse());
            const m = mascaraEn(geo, local.x, local.y);
            return rellenos.has(m) ? m : null;
        };
        return { svg, geo, rellenos, enPunto };
    }

    // Tarjetas, sumandos, términos y filas con data-mascaras iluminan sus regiones al pasar o enfocar.
    function enlazar(nodos, resaltar, reposo) {
        nodos.forEach(nodo => {
            const mascaras = nodo.dataset.mascaras.split(' ').filter(Boolean).map(Number);
            const encender = () => { resaltar(mascaras); nodo.classList.add('es-activa'); };
            const apagar = () => { resaltar(reposo()); nodo.classList.remove('es-activa'); };
            nodo.addEventListener('mouseenter', encender);
            nodo.addEventListener('mouseleave', apagar);
            nodo.addEventListener('focusin', encender);
            nodo.addEventListener('focusout', apagar);
        });
    }

    function dibujarVenn(contenedor, venn, panel) {
        if (!GEOMETRIA[venn.nombres.length]) return;
        const cantidades = Boolean(venn.cantidades);
        const { svg, geo, rellenos, enPunto } = lienzoVenn(venn, { role: 'img',
            'aria-label': `Diagrama de Venn de ${venn.nombres.join(', ')}${venn.universo ? ` dentro de ${venn.universo}` : ''}` });
        for (const r of venn.regiones) {
            const [x, y] = geo.anclas[r.mascara];
            const exterior = r.mascara === 0;
            const ancla = exterior ? 'start' : 'middle';
            if (cantidades || r.cantidad === null) {
                const texto = r.cantidad ?? '?';
                const nodo = el('text', { x, y: y + (exterior ? 0 : 6), 'text-anchor': ancla, class: `venn-texto es-cantidad${r.cantidad === null ? ' es-desconocido' : ''}` }, texto);
                svg.append(nodo);
                continue;
            }
            if (!r.etiquetas.length) continue;
            const filas = lineas(r.etiquetas, geo.pequenas.includes(r.mascara));
            const nodo = el('text', { x, y: exterior ? y : y - (filas.length - 1) * 7 + 4, 'text-anchor': ancla, class: 'venn-texto' });
            filas.forEach((linea, i) => nodo.append(el('tspan', { x, dy: i ? 14 : 0 }, linea)));
            if (exterior) nodo.setAttribute('y', y - (filas.length - 1) * 14);
            svg.append(nodo);
        }
        contenedor.replaceChildren(svg, estadoRegiones());
        const resaltarRegiones = mascaras => {
            for (const [m, rect] of rellenos) rect.classList.toggle('es-activa', mascaras.includes(m));
        };
        const { fijar, reposo, resaltar } = explorarRegiones(venn, panel, resaltarRegiones, contenedor.lastChild);
        svg.addEventListener('pointermove', event => {
            const m = enPunto(event);
            resaltar(m === null ? reposo() : [m]);
        });
        svg.addEventListener('pointerleave', () => resaltar(reposo()));
        svg.addEventListener('click', event => {
            const m = enPunto(event);
            if (m !== null) fijar(m);
        });
        // Sumandos, términos y tarjetas del resultado iluminan su diagrama.
        enlazar([...panel.closest('[data-resultado]').querySelectorAll('[data-mascaras]')], resaltar, reposo);
    }

    function estadoRegiones() {
        const estado = document.createElement('p');
        estado.className = 'field-help';
        estado.setAttribute('role', 'status');
        estado.setAttribute('aria-live', 'polite');
        return estado;
    }

    // Tabla de regiones del resultado: pasar por una fila ilumina su región y pulsarla (o Intro)
    // la fija y anuncia sus elementos. `resaltarRegiones` pinta el diagrama que corresponda.
    function explorarRegiones(venn, panel, resaltarRegiones, estado) {
        const cantidades = Boolean(venn.cantidades);
        const filas = new Map([...panel.querySelectorAll('[data-regiones] tr[data-mascara]')].map(fila => [Number(fila.dataset.mascara), fila]));
        let fija = null;
        const resaltar = mascaras => {
            resaltarRegiones(mascaras);
            for (const [m, fila] of filas) fila.classList.toggle('es-activa', mascaras.includes(m));
        };
        const reposo = () => (fija === null ? [] : [fija]);
        const describir = m => {
            const r = venn.regiones.find(x => x.mascara === m);
            if (!r) return '';
            const contenido = cantidades ? `${r.cantidad ?? 'cantidad desconocida'} elementos`
                : r.etiquetas.length ? `${r.etiquetas.length} elemento${r.etiquetas.length === 1 ? '' : 's'}: ${r.etiquetas.join(', ')}`
                : r.exterior_conocido ? 'vacía' : 'desconocida, porque no hay universo';
            const parte = venn.regiones.some(x => x.seleccionada) || cantidades
                ? (r.seleccionada ? ' Forma parte del resultado.' : ' No forma parte del resultado.') : '';
            return `${r.descripcion} (${r.etiqueta}): ${contenido}.${parte}`;
        };
        const fijar = m => {
            fija = fija === m ? null : m;
            resaltar(reposo());
            estado.textContent = fija === null ? '' : describir(fija);
        };
        for (const [m, fila] of filas) {
            fila.tabIndex = 0;
            fila.addEventListener('click', () => fijar(m));
            fila.addEventListener('keydown', event => {
                if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); fijar(m); }
            });
            fila.addEventListener('mouseenter', () => resaltar([m]));
            fila.addEventListener('mouseleave', () => resaltar(reposo()));
        }
        return { fijar, reposo, resaltar };
    }

    // Diagrama editable: los campos del formulario (uno por región, con su etiqueta) se colocan
    // dentro de su región. Sin JavaScript siguen siendo una lista de campos con nombre.
    // Con `resultado` (su Venn y su panel), sombrea las regiones del resultado sin tocar lo escrito;
    // «Sombrear en el diagrama» lo quita y lo vuelve a poner, y editar cualquier dato lo retira.
    function editorVenn(editor, resultado) {
        const nombres = editor.dataset.nombres.split(',');
        const campos = [...editor.querySelectorAll('[data-mascara]')];
        if (!GEOMETRIA[nombres.length] || !campos.length) return;
        const exterior = campos.some(campo => campo.dataset.mascara === '0');
        const enResultado = new Set((resultado?.venn.regiones || []).filter(r => r.seleccionada).map(r => r.mascara));
        const regiones = Array.from({ length: 1 << nombres.length }, (_, mascara) => ({ mascara, seleccionada: enResultado.has(mascara) }))
            .filter(r => r.mascara || exterior);
        const { svg, geo, rellenos, enPunto } = lienzoVenn(
            { nombres, universo: exterior ? editor.dataset.universo || 'U' : null, regiones }, { 'aria-hidden': 'true', focusable: 'false' });
        const lienzo = document.createElement('div');
        lienzo.className = 'venn-editor-lienzo';
        // Leyenda visual de la región señalada; el lector de pantalla ya oye la etiqueta de cada campo.
        const leyenda = document.createElement('p');
        leyenda.className = 'venn-editor-leyenda';
        leyenda.setAttribute('aria-hidden', 'true');
        const etiquetas = new Map(), controles = new Map();
        let enfocada = null;
        const resaltar = mascaras => {
            for (const [m, rect] of rellenos) rect.classList.toggle('es-activa', mascaras.includes(m));
            leyenda.textContent = mascaras.length === 1 ? etiquetas.get(mascaras[0]) || '' : '';
        };
        const reposo = () => (enfocada === null ? [] : [enfocada]);
        lienzo.append(svg);
        for (const campo of campos) {
            const m = Number(campo.dataset.mascara);
            const [x, y] = geo.anclas[m], [ancho, alto, dx = 0, dy = 0] = geo.cajas[m];
            // El exterior se ancla por su esquina inferior izquierda; las demás regiones, por su centro.
            const estilo = { x: m ? x + dx : x + ancho / 2 - 6, y: m ? y + dy : y - alto / 2 + 6, w: ancho, h: alto };
            for (const [clave, valor] of Object.entries(estilo)) {
                campo.style.setProperty(`--${clave}`, `${valor / ('yh'.includes(clave) ? ALTO : ANCHO) * 100}%`);
            }
            const control = campo.querySelector('textarea, input');
            etiquetas.set(m, campo.querySelector('.cardinalidad-lectura, label').textContent.trim());
            // La región ya dice dónde se escribe: la etiqueta queda para el lector de pantalla.
            if (!campo.matches('.cardinalidad-universo')) campo.querySelector('label').classList.add('sr-only');
            controles.set(m, control);
            control.addEventListener('focus', () => { enfocada = m; resaltar([m]); });
            control.addEventListener('blur', () => { enfocada = null; resaltar([]); });
            lienzo.append(campo);
        }
        lienzo.addEventListener('pointermove', event => {
            const m = enPunto(event);
            resaltar(m === null ? reposo() : [m]);
        });
        lienzo.addEventListener('pointerleave', () => resaltar(reposo()));
        // Pulsar una región lleva el cursor a su campo, aunque el toque caiga fuera de la caja.
        lienzo.addEventListener('click', event => {
            if (!event.target.closest('textarea, input')) controles.get(enPunto(event))?.focus();
        });
        editor.classList.add('es-diagrama');
        editor.replaceChildren(lienzo, leyenda);
        // Las tarjetas de arriba siempre son de este diagrama; las del resultado, solo si no dibuja el suyo.
        enlazar([...document.querySelectorAll('[data-mascaras]')].filter(nodo => resultado || !nodo.closest('[data-resultado]')), resaltar, reposo);
        if (!resultado) return;
        const { panel } = resultado;
        const boton = panel.querySelector('[data-sombreado]');
        const sombrear = visible => {
            lienzo.toggleAttribute('data-con-resultado', visible);
            boton.setAttribute('aria-pressed', String(visible));
        };
        panel.querySelector('[data-con-diagrama]').hidden = false;
        boton.hidden = false;
        boton.addEventListener('click', () => sombrear(boton.getAttribute('aria-pressed') !== 'true'));
        sombrear(true);
        // El resultado deja de corresponder a los datos en cuanto se edita algo.
        editor.closest('form').addEventListener('input', () => { sombrear(false); boton.hidden = true; });
        const estado = estadoRegiones();
        panel.querySelector('.table-wrap').before(estado);
        explorarRegiones(resultado.venn, panel, resaltar, estado);
    }

    // Icono de un dato de cardinalidad: sombrea las regiones que cuenta (0 = todo el universo).
    function miniVenn(contenedor, n, cubre) {
        const geo = GEOMETRIA[n];
        const prefijo = `mini${++secuencia}`;
        const svg = el('svg', { viewBox: `0 0 ${ANCHO} ${ALTO}`, focusable: 'false' });
        const defs = el('defs');
        svg.append(defs);
        if (cubre.includes(0)) svg.append(el('rect', { ...MARCO, class: 'mini-venn-region' }));
        else for (const m of cubre) svg.append(region(defs, geo, m, prefijo, 'mini-venn-region').raiz);
        svg.append(el('rect', { ...MARCO, class: 'mini-venn-marco', 'stroke-width': 10 }));
        geo.circulos.forEach(([cx, cy, r]) => svg.append(el('circle', { cx, cy, r, class: 'mini-venn-circulo', 'stroke-width': 10 })));
        contenedor.replaceChildren(svg);
    }

    /* —— Recta real —— */
    function dibujarRecta(contenedor, datos, panel) {
        const filas = [...datos.filas.map(f => ({ ...f, resultado: false }))];
        if (datos.tramos.length || datos.notacion) filas.push({ etiqueta: datos.relacion ? '' : 'Resultado', notacion: datos.notacion, tramos: datos.tramos, resultado: !datos.relacion });
        const punto = panel.querySelector('[name="punto"]');
        const estado = document.createElement('p');
        estado.className = 'field-help';
        estado.setAttribute('role', 'status');
        estado.setAttribute('aria-live', 'polite');
        const svg = el('svg', { class: 'recta-svg', role: 'img', tabindex: 0,
            'aria-label': 'Recta real. Teclas: + y − para acercar o alejar, flechas para desplazar, 0 para la vista inicial.' });
        let inicio = 0, ancho = 100, activo = null;
        const ALTO_FILA = 64, MARGEN = 18;
        const dibujar = () => {
            const W = Math.max(260, contenedor.clientWidth || 600);
            const H = filas.length * ALTO_FILA + (datos.x_punto !== null ? 18 : 6);
            svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
            svg.setAttribute('width', W);
            svg.setAttribute('height', H);
            const px = x => MARGEN + (x - inicio) / ancho * (W - 2 * MARGEN);
            const izquierda = MARGEN - 4, derecha = W - MARGEN + 4;
            const recorte = el('clipPath', { id: 'recta-recorte' });
            recorte.append(el('rect', { x: 0, y: 0, width: W, height: H }));
            const grupo = el('g', { 'clip-path': 'url(#recta-recorte)' });
            svg.replaceChildren(el('defs'), grupo);
            svg.firstChild.append(recorte);
            const desplazado = datos.x_punto !== null ? 18 : 0;
            filas.forEach((fila, f) => {
                const top = f * ALTO_FILA + desplazado;
                const y = top + 30;
                const g = el('g', { class: `recta-fila${fila.resultado ? ' es-resultado' : ''}` });
                if (fila.etiqueta) g.append(el('text', { x: 6, y: top + 12, class: 'recta-etiqueta' }, fila.etiqueta));
                g.append(el('line', { x1: izquierda, y1: y, x2: derecha, y2: y, class: 'recta-eje' }));
                let ultimo = -Infinity, alterno = false;
                fila.tramos.forEach((t, i) => {
                    const tg = el('g', { class: `recta-tramo-grupo${fila.resultado && activo === i ? ' es-activo' : ''}` });
                    const x1 = t.inferior === null ? izquierda : px(t.x1);
                    const x2 = t.superior === null ? derecha : px(t.x2);
                    tg.append(el('line', { x1, y1: y, x2, y2: y, class: 'recta-tramo' }));
                    for (const [x, valor, cerrado, lado] of [[x1, t.inferior, t.cerrado_inferior, -1], [x2, t.superior, t.cerrado_superior, 1]]) {
                        if (valor === null) {
                            tg.append(el('path', { d: `M ${x - lado * 8} ${y - 6} L ${x} ${y} L ${x - lado * 8} ${y + 6}`, class: 'recta-flecha' }));
                            continue;
                        }
                        if (t.inferior !== null && t.inferior === t.superior && lado === 1) continue;
                        tg.append(el('circle', { cx: x, cy: y, r: 5.5, class: `recta-extremo${cerrado ? ' es-cerrado' : ''}` }));
                        alterno = x - ultimo < 40 ? !alterno : false;
                        ultimo = x;
                        tg.append(el('text', { x, y: y + (alterno ? 32 : 20), 'text-anchor': 'middle', class: 'recta-valor' }, valor));
                    }
                    g.append(tg);
                });
                if (!fila.tramos.length) g.append(el('text', { x: W / 2, y: y - 8, 'text-anchor': 'middle', class: 'recta-valor' }, '∅: ningún punto'));
                grupo.append(g);
            });
            if (datos.x_punto !== null) {
                const x = px(datos.x_punto);
                grupo.append(el('line', { x1: x, y1: 14, x2: x, y2: H - 4, class: 'recta-punto' }));
                grupo.append(el('text', { x: x + 6, y: 12, class: 'recta-punto-texto' }, `x = ${datos.punto}`));
                const fila = filas.length - 1;
                grupo.append(el('circle', { cx: x, cy: fila * ALTO_FILA + desplazado + 30, r: 3.5, class: 'recta-punto-marca' }));
            }
        };
        const mover = (nuevoInicio, nuevoAncho) => {
            ancho = Math.min(400, Math.max(1.5, nuevoAncho));
            inicio = Math.min(100, Math.max(-ancho, nuevoInicio));
            dibujar();
        };
        const zoom = factor => mover(inicio + ancho / 2 - ancho * factor / 2, ancho * factor);
        const boton = (texto, etiqueta, accion) => {
            const b = document.createElement('button');
            b.type = 'button';
            b.className = 'btn btn-secondary';
            b.textContent = texto;
            if (etiqueta) b.setAttribute('aria-label', etiqueta);
            b.addEventListener('click', accion);
            return b;
        };
        const controles = document.createElement('div');
        controles.className = 'recta-controles';
        controles.setAttribute('role', 'group');
        controles.setAttribute('aria-label', 'Vista de la recta');
        controles.append(
            boton('+', 'Acercar', () => zoom(0.5)), boton('−', 'Alejar', () => zoom(2)),
            boton('←', 'Desplazar a la izquierda', () => mover(inicio - ancho / 4, ancho)),
            boton('→', 'Desplazar a la derecha', () => mover(inicio + ancho / 4, ancho)),
            boton('Vista inicial', null, () => { activo = null; tramos.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', 'false')); mover(0, 100); }),
        );
        // Tramos del resultado en notación exacta: elegir uno lo resalta y lo centra.
        const tramos = document.createElement('ul');
        tramos.className = 'recta-tramos';
        const resultado = filas.find(f => f.resultado);
        if (resultado && resultado.tramos.length > 1) {
            resultado.tramos.forEach((t, i) => {
                const li = document.createElement('li');
                const b = boton(t.notacion, `Resaltar el tramo ${t.notacion}`, () => {
                    activo = activo === i ? null : i;
                    tramos.querySelectorAll('button').forEach((x, j) => x.setAttribute('aria-pressed', String(activo === j)));
                    if (activo !== null && t.inferior !== null && t.superior !== null) mover((t.x1 + t.x2) / 2 - ancho / 2, ancho);
                    else dibujar();
                    estado.textContent = activo === null ? '' : `Tramo ${t.notacion} resaltado.`;
                });
                b.className = 'conjuntos-chip-boton conjuntos-math';
                b.setAttribute('aria-pressed', 'false');
                li.append(b);
                tramos.append(li);
            });
        }
        svg.addEventListener('keydown', event => {
            const acciones = { '+': () => zoom(0.5), '=': () => zoom(0.5), '-': () => zoom(2), ArrowLeft: () => mover(inicio - ancho / 8, ancho),
                ArrowRight: () => mover(inicio + ancho / 8, ancho), 0: () => mover(0, 100) };
            if (acciones[event.key]) { event.preventDefault(); acciones[event.key](); }
        });
        // Arrastrar desplaza; un toque sin arrastre propone un punto redondeado a la escala visible.
        let arrastre = null;
        svg.addEventListener('pointerdown', event => {
            arrastre = { x: event.clientX, inicio, movido: false };
            svg.setPointerCapture(event.pointerId);
        });
        svg.addEventListener('pointermove', event => {
            if (!arrastre) return;
            const dx = event.clientX - arrastre.x;
            if (Math.abs(dx) > 4) arrastre.movido = true;
            if (arrastre.movido) mover(arrastre.inicio - dx / svg.getBoundingClientRect().width * ancho, ancho);
        });
        svg.addEventListener('pointerup', event => {
            const proponer = arrastre && !arrastre.movido && punto;
            arrastre = null;
            if (!proponer) return;
            const caja = svg.getBoundingClientRect();
            const W = Number(svg.getAttribute('width'));
            const x = inicio + ((event.clientX - caja.left) / caja.width * W - MARGEN) / (W - 2 * MARGEN) * ancho;
            const [minimo, maximo] = datos.escala;
            const aproximado = minimo + (x - 10) / 80 * (maximo - minimo);
            const paso = 10 ** Math.floor(Math.log10(ancho / 80 * (maximo - minimo) / 20));
            const decimales = Math.max(0, -Math.round(Math.log10(paso)));
            const texto = (Math.round(aproximado / paso) * paso).toFixed(decimales).replace(/^-0(\.0+)?$/, '0');
            punto.value = texto;
            punto.dispatchEvent(new Event('input', { bubbles: true }));
            estado.textContent = `Punto propuesto: ${texto}. Pulsa Comprobar para saber si pertenece.`;
        });
        contenedor.replaceChildren(controles, svg, tramos, estado);
        if (!tramos.childElementCount) tramos.remove();
        dibujar();
        if ('ResizeObserver' in window) new ResizeObserver(() => dibujar()).observe(contenedor);
    }

    /* —— Arranque —— */
    const ajuste = document.querySelector('[data-ajuste-cardinalidades]');
    if (ajuste) {
        // Cambiar número de conjuntos o tipo de datos recompone los campos (sin JavaScript: «Aplicar»).
        ajuste.hidden = true;
        ajuste.form.addEventListener('change', event => {
            if (['numero', 'modo'].includes(event.target.name)) ajuste.form.requestSubmit(ajuste);
        });
    }
    const fuente = document.getElementById('conjuntos-resultado-datos');
    const resultado = fuente ? JSON.parse(fuente.textContent) : null;
    const enDiagrama = document.querySelector('[data-venn-en-diagrama]');
    document.querySelectorAll('[data-venn-editor]').forEach(editor => editorVenn(editor,
        enDiagrama && resultado?.venn ? { venn: resultado.venn, panel: enDiagrama } : null));
    document.querySelectorAll('.cardinalidad-campos[data-conjuntos]:not(.es-diagrama)').forEach(campos => {
        campos.querySelectorAll('[data-cubre]').forEach(dato => {
            miniVenn(dato.querySelector('.cardinalidad-icono'), Number(campos.dataset.conjuntos), dato.dataset.cubre.split(' ').map(Number));
        });
    });
    const atajos = document.querySelector('[data-atajos]');
    if (atajos) {
        atajos.hidden = false;
        const campo = atajos.closest('form').elements.expresion;
        atajos.addEventListener('click', event => {
            const b = event.target.closest('[data-expresion]');
            if (!b) return;
            campo.value = b.dataset.expresion;
            campo.dispatchEvent(new Event('input', { bubbles: true }));
            campo.focus();
        });
    }
    if (!resultado) return;
    const venn = document.querySelector('[data-venn]');
    if (venn && resultado.venn) dibujarVenn(venn, resultado.venn, venn.closest('section'));
    const recta = document.querySelector('[data-recta]');
    if (recta && resultado.recta) dibujarRecta(recta, resultado.recta, recta.closest('section'));
})();
