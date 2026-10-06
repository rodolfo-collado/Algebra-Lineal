/* P27.8: celdas, Operaciones, foco al agregar/quitar, nombres por símbolo, ayudas de Inversa,
   desplegables, etiquetas, contraste y foco bajo la cabecera, con la app y sus scripts reales.
   Se comparan medidas entre sí (alineación, orden, contraste calculado), no píxeles fijos. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const todos = (w, s) => [...w.document.querySelectorAll(s)];
    const assert = (ok, mensaje) => { if (!ok) throw new Error(mensaje); };
    // Con la pestaña oculta no corre requestAnimationFrame y los temporizadores se agrupan
    // hasta por minuto; un mensaje entre puertos cede el turno igual (el layout se mide al consultarlo).
    const turno = w => new Promise(resolve => {
        if (!w.document.hidden) return w.requestAnimationFrame(() => w.requestAnimationFrame(resolve));
        const canal = new MessageChannel();
        canal.port1.onmessage = () => resolve();
        canal.port2.postMessage(null);
    });
    const cargar = (frame, url) => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(`Timeout: ${url}`)), 30000);
        frame.onload = async () => { clearTimeout(timer); await turno(frame.contentWindow); resolve(frame.contentWindow); };
        frame.src = url;
    });
    const calcular = frame => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Calcular no navegó")), 30000);
        frame.onload = async () => { clearTimeout(timer); await turno(frame.contentWindow); resolve(frame.contentWindow); };
        const boton = q(frame.contentWindow, "[data-calculo]"); boton.form.requestSubmit(boton);
    });
    const tamano = async (frame, ancho, alto) => {
        frame.style.width = `${ancho}px`; frame.style.height = `${alto}px`; await turno(frame.contentWindow);
    };
    const escribir = (w, campo, valor, tipo = "input") => {
        campo.value = String(valor); campo.dispatchEvent(new w.Event(tipo, { bubbles: true }));
    };
    const visibles = (w, s) => todos(w, s).filter(e => e.getClientRects().length && !e.closest("[hidden], template"));
    const cabecera = w => q(w, ".app-header").getBoundingClientRect().bottom;
    const sinDesborde = w => assert(w.document.documentElement.scrollWidth <= w.document.documentElement.clientWidth + 1,
        `La página desborda: ${w.document.documentElement.scrollWidth}/${w.document.documentElement.clientWidth}`);
    const sinTransiciones = w => {
        const estilo = w.document.createElement("style");
        estilo.textContent = "*, *::before, *::after { transition: none !important; animation: none !important; }";
        w.document.head.append(estilo);
    };

    // Contraste WCAG 2.x calculado sobre los colores efectivos, sin comparar cadenas de color.
    const rgb = c => { const m = c.match(/[\d.]+/g).map(Number); return { r: m[0], g: m[1], b: m[2], a: m.length > 3 ? m[3] : 1 }; };
    const lineal = v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    const luminancia = c => 0.2126 * lineal(c.r) + 0.7152 * lineal(c.g) + 0.0722 * lineal(c.b);
    const sobre = (f, b) => ({ r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a), b: f.b * f.a + b.b * (1 - f.a), a: 1 });
    const contraste = (a, b) => {
        const [x, y] = [luminancia(a), luminancia(b)].sort((p, s) => s - p);
        return (x + 0.05) / (y + 0.05);
    };
    const fondo = (w, elemento) => {
        const capas = [];
        for (let nodo = elemento; nodo; nodo = nodo.parentElement) {
            const color = rgb(w.getComputedStyle(nodo).backgroundColor);
            if (color.a > 0) { capas.push(color); if (color.a === 1) break; }
        }
        const base = capas.length && capas.at(-1).a === 1 ? capas.pop() : { r: 255, g: 255, b: 255, a: 1 };
        return capas.reverse().reduce((abajo, capa) => sobre(capa, abajo), base);
    };
    const bordeContra = (w, campo) => {
        const exterior = fondo(w, campo.parentElement);
        return contraste(sobre(rgb(w.getComputedStyle(campo).borderTopColor), exterior), exterior);
    };

    const HERRAMIENTAS = ["/matrices/reduccion/", "/matrices/operaciones/", "/matrices/ecuaciones/", "/matrices/inversa/",
        "/vectores/operaciones/", "/bases/conversion/", "/romanos/conversion/"];
    const AUMENTADA = "/matrices/reduccion/?tipo_entrada=matriz&ecuaciones=2&variables=2";
    const SISTEMA = "x1+2x2-x3=4\n2x1-x2+3x3=7\nx1+x2+x3=6";
    const casos = [];

    // —— UI-31: celdas ——
    const VALORES = ["-11/13", "123/456", "-123456", "3.14159"];
    for (const ruta of ["/matrices/ecuaciones/", "/matrices/inversa/", "/matrices/operaciones/", AUMENTADA, "/vectores/operaciones/"]) {
        casos.push([`UI-31 ${ruta}: valores largos completos, columnas alineadas y sin desborde`, ruta, async (w, frame) => {
            assert(w.CSS.supports("field-sizing", "content"), "field-sizing disponible en Chromium/WebView2");
            for (const [ancho, alto] of [[1280, 650], [744, 521], [390, 650]]) {
                await tamano(frame, ancho, alto);
                const celdas = visibles(w, "input.matrix-input");
                assert(celdas.length >= 4, "Hay celdas");
                celdas.forEach((celda, i) => escribir(w, celda, VALORES[i % VALORES.length]));
                await turno(w);
                const recortadas = celdas.filter(c => c.scrollWidth > c.clientWidth + 1).map(c => `${c.name}=${c.value}`);
                assert(!recortadas.length, `${ancho}px recorta ${recortadas}`);
                // En tablas y en la cuadrícula aumentada, todas las celdas de una columna miden lo mismo.
                const columnas = new Map();
                for (const celda of celdas) {
                    const td = celda.closest("td");
                    const clave = td ? `${td.closest("[data-simbolo], .matrix-entry")?.getAttribute("aria-label") ?? td.closest("table").getAttribute("aria-label")}#${td.cellIndex}`
                        : celda.closest(".matrix-grid") ? `aumentada#${celda.name.split("_")[2]}` : null;
                    if (!clave) continue;
                    const rect = celda.getBoundingClientRect();
                    if (!columnas.has(clave)) columnas.set(clave, []);
                    columnas.get(clave).push(rect);
                }
                for (const [clave, rects] of columnas) {
                    assert(rects.every(r => Math.abs(r.left - rects[0].left) < 1 && Math.abs(r.width - rects[0].width) < 1),
                        `${ancho}px: la columna ${clave} no está alineada`);
                }
                sinDesborde(w);
            }
        }]);
    }
    casos.push(["UI-31: más allá de 7rem la celda conserva su máximo, el cursor y el scroll local", "/matrices/inversa/", async (w, frame) => {
        await tamano(frame, 390, 650);
        escribir(w, q(w, '[name="orden"]'), 10);
        const celdas = todos(w, '[name^="celda_A_"]');
        assert(celdas.length === 100, "A es 10×10");
        celdas.forEach(celda => escribir(w, celda, "123456789/987654321"));
        await turno(w);
        const maximo = parseFloat(w.getComputedStyle(celdas[0]).maxWidth);
        assert(celdas.every(c => c.getBoundingClientRect().width <= maximo + 1), "Ningún ancho supera el máximo");
        celdas[0].focus(); celdas[0].setSelectionRange(19, 19);
        assert(celdas[0].selectionStart === 19 && celdas[0].scrollWidth > celdas[0].clientWidth, "El input conserva cursor y desplazamiento");
        const scroll = q(w, "#inverse-matrix .matrix-scroll");
        assert(scroll.scrollWidth > scroll.clientWidth, "La matriz se desplaza localmente");
        sinDesborde(w);
    }]);

    // —— UI-32: Operaciones compacta ——
    casos.push(["UI-32: Calcular visible a 1920×1010, expresión sin 138 px y dos tarjetas por fila", "/matrices/operaciones/", async (w, frame) => {
        await tamano(frame, 1920, 1010);
        assert(q(w, "[data-calculo]").getBoundingClientRect().bottom <= w.innerHeight, "Calcular en el primer viewport");
        assert(q(w, '[name="expresion"]').getBoundingClientRect().height < 100, "La expresión no hereda la altura del sistema");
        let [a, b] = todos(w, "[data-simbolo]").map(c => c.getBoundingClientRect());
        assert(Math.abs(a.top - b.top) < 1 && b.left >= a.right, "A y B comparten fila, en el orden del DOM");
        escribir(w, q(w, '[data-campo="columnas"]'), 6); await turno(w);
        [a, b] = todos(w, "[data-simbolo]").map(c => c.getBoundingClientRect());
        assert(b.top >= a.bottom && Math.abs(a.width - q(w, "#symbol-list").getBoundingClientRect().width) < 1, "Una matriz de seis columnas ocupa la fila");
        await tamano(frame, 390, 650);
        const tarjetas = todos(w, "[data-simbolo]").map(c => c.getBoundingClientRect());
        assert(tarjetas.every(r => Math.abs(r.left - tarjetas[0].left) < 1) && tarjetas[1].top >= tarjetas[0].bottom, "Una columna a 390 px");
        sinDesborde(w);
    }]);

    // —— UI-33: agregar y quitar ——
    casos.push(["UI-33: agregar y eliminar símbolos dejan el foco en contexto y lo anuncian", "/matrices/operaciones/", async w => {
        const aviso = q(w, "[data-presupuesto]");
        const nombre = tarjeta => tarjeta.querySelector('[data-campo="nombre"]');
        assert(aviso.getAttribute("role") === "status", "Región de estado existente");
        q(w, "[data-agregar]").click();
        let tarjetas = todos(w, "[data-simbolo]");
        assert(tarjetas.length === 3 && w.document.activeElement === nombre(tarjetas[2]), "Foco en el nombre del nuevo símbolo");
        assert(aviso.textContent === "Se agregó el símbolo C.", `Aviso de alta: ${aviso.textContent}`);
        tarjetas[1].querySelector("[data-eliminar]").click();
        tarjetas = todos(w, "[data-simbolo]");
        assert(w.document.activeElement === nombre(tarjetas[1]) && tarjetas[1].getAttribute("aria-label") === "Símbolo C", "Foco en el símbolo siguiente");
        assert(aviso.textContent === "Se eliminó el símbolo B.", `Aviso de baja: ${aviso.textContent}`);
        tarjetas[1].querySelector("[data-eliminar]").click();
        assert(w.document.activeElement === nombre(todos(w, "[data-simbolo]")[0]), "Sin siguiente, foco en el anterior");
        todos(w, "[data-simbolo]")[0].querySelector("[data-eliminar]").click();
        assert(w.document.activeElement === q(w, "[data-agregar]"), "Sin símbolos, foco en Agregar");
        assert(aviso.textContent === "Se eliminó el símbolo A.", "Último aviso");
    }]);
    casos.push(["UI-33: Vectores — agregar y quitar llevan el foco a una componente y lo anuncian", "/vectores/operaciones/", async w => {
        const estado = q(w, "[data-estado-vectores]");
        assert(estado.getAttribute("role") === "status", "Región de estado");
        q(w, "[data-agregar-vector]").click();
        assert(w.document.activeElement === q(w, '[name="v3_0"]') && estado.textContent === "Se agregó el vector v3.", "Alta con foco en v3");
        q(w, "[data-agregar-vector]").click();
        escribir(w, q(w, '[name="v4_0"]'), 9);
        q(w, '[aria-label="Quitar vector v3"]').click();
        assert(w.document.activeElement === q(w, '[name="v3_0"]') && w.document.activeElement.value === "9", "Foco en la fila que ocupa su lugar");
        assert(estado.textContent === "Se eliminó el vector v3.", `Aviso de baja: ${estado.textContent}`);
        q(w, '[aria-label="Quitar vector v3"]').click();
        assert(w.document.activeElement === q(w, '[name="v_0"]'), "Era la última: foco en la anterior");
        const mas = q(w, '[data-estructura="vectores"] [data-paso="1"]');
        mas.focus(); mas.click();
        assert(w.document.activeElement === mas && estado.textContent === "Se agregó el vector v3.", "El stepper avisa sin mover el foco");
    }]);
    casos.push(["UI-33: el × pertenece a su fila, con borde completo, y los vectores quedan alineados", "/vectores/operaciones/", async (w, frame) => {
        q(w, "[data-agregar-vector]").click();
        for (const [ancho, alto] of [[1280, 650], [390, 650]]) {
            await tamano(frame, ancho, alto);
            const filas = todos(w, ".vector-row[data-vector]");
            const quitar = q(w, ".vector-remove");
            const fila = quitar.closest(".vector-row");
            const rect = quitar.getBoundingClientRect(); const caja = fila.getBoundingClientRect();
            assert(rect.top >= caja.top - 1 && rect.bottom <= caja.bottom + 1, `${ancho}px: × dentro de su fila`);
            assert(rect.left >= fila.querySelector(".vector-inputs").getBoundingClientRect().right - 1, `${ancho}px: × después de las componentes`);
            const css = w.getComputedStyle(quitar);
            assert(["Left", "Right", "Top", "Bottom"].every(lado => parseFloat(css[`border${lado}Width`]) > 0) && parseFloat(css.borderTopLeftRadius) > 0, "Borde y esquinas completos");
            const nombres = filas.map(f => f.querySelector(".vector-name").getBoundingClientRect().right);
            const inicios = filas.map(f => f.querySelector(".vector-inputs").getBoundingClientRect().left);
            assert(nombres.every(x => Math.abs(x - nombres[0]) < 1) && inicios.every(x => Math.abs(x - inicios[0]) < 1), `${ancho}px: nombres y componentes alineados`);
            assert(filas.every(f => { const c = f.querySelector(".vector-inputs"); return c.scrollWidth <= c.clientWidth + 1; }), `${ancho}px: caben tres componentes`);
            sinDesborde(w);
        }
    }]);

    // —— UI-34: nombres accesibles ——
    casos.push(["UI-34: cada control nombra su símbolo y renombrar A → M lo actualiza", "/matrices/operaciones/", async w => {
        const nombres = tarjeta => [tarjeta.getAttribute("aria-label"), ...[...tarjeta.querySelectorAll("button")].map(b => b.getAttribute("aria-label"))];
        const a = todos(w, "[data-simbolo]")[0];
        assert(a.tagName === "FIELDSET", "Cada símbolo es un grupo nativo");
        const esperados = ["Símbolo A", "Quitar una fila de A", "Agregar una fila a A", "Quitar una columna de A", "Agregar una columna a A", "Eliminar símbolo A"];
        assert(JSON.stringify(nombres(a)) === JSON.stringify(esperados), `Nombres: ${nombres(a)}`);
        escribir(w, a.querySelector('[data-campo="nombre"]'), "M");
        assert(nombres(a).every(n => n.endsWith(" M")) && a.querySelector("td label").textContent.startsWith("Matriz M"), "Renombrar actualiza grupo, botones y celdas");
        escribir(w, a.querySelector('[data-campo="tipo"]'), "vector", "change");
        assert(nombres(a).includes("Quitar una componente de M"), "Un vector habla de componentes");
        q(w, "[data-agregar]").click();
        const nueva = todos(w, "[data-simbolo]").at(-1);
        assert(nombres(nueva)[0] === "Símbolo A" && nombres(nueva).at(-1) === "Eliminar símbolo A", "La plantilla también se rotula");
        const botones = visibles(w, "[data-simbolo] button").map(b => b.getAttribute("aria-label"));
        assert(new Set(botones).size === botones.length, "Ningún nombre de botón se repite");
    }]);

    // —— UI-35: ayudas de Inversa ——
    casos.push(["UI-35: cada aplicación de la inversa explica su efecto y lo asocia a su radio", "/matrices/inversa/", async w => {
        q(w, "#aplicaciones").open = true; await turno(w);
        const radios = todos(w, '[name="funcion_adicional"]');
        assert(radios.length === 5, "Cinco opciones");
        for (const radio of radios) {
            const ayuda = w.document.getElementById(radio.getAttribute("aria-describedby").split(" ")[0]);
            assert(ayuda && ayuda.textContent.trim().length > 5 && ayuda.getClientRects().length, `${radio.value}: ayuda visible y asociada`);
        }
        assert(q(w, `#${radios[3].id}_ayuda`).textContent.includes("(AB)⁻¹ = B⁻¹A⁻¹"), "Producto: la propiedad que comprueba");
    }]);

    // —— UI-57: desplegables ——
    casos.push(["UI-57: un solo desplegable en formularios y resultado; abre, cierra y solo el procedimiento es sticky", "/matrices/operaciones/", async (w, frame) => {
        const firmas = new Set(); let total = 0;
        const revisar = (ventana, ruta) => {
            for (const detalle of todos(ventana, "details.disclosure")) {
                const summary = detalle.querySelector(":scope > summary");
                const chevron = summary.firstElementChild;
                assert(chevron.classList.contains("disclosure-chevron"), `${ruta}: chevrón al inicio de «${summary.textContent.trim()}»`);
                const css = ventana.getComputedStyle(chevron);
                firmas.add(`${css.width}|${css.height}|${css.color}`);
                total += 1;
            }
        };
        for (const ruta of ["/matrices/reduccion/", "/matrices/operaciones/", "/matrices/inversa/"]) {
            w = await cargar(frame, ruta); sinTransiciones(w); revisar(w, ruta);
            const summary = q(w, "details.disclosure > summary"); const detalle = summary.parentElement; const abierto = detalle.open;
            summary.click(); await turno(w);
            assert(detalle.open !== abierto, `${ruta}: abre y cierra con su summary`);
            assert(w.getComputedStyle(summary.querySelector(".disclosure-chevron")).transform !== "none" || !detalle.open, "El chevrón gira al abrir");
            assert(summary.getBoundingClientRect().height >= 24, "Área clicable suficiente");
        }
        // Un producto comparado aporta procedimiento, sub-bloques y grupos por fila o columna.
        w = await cargar(frame, "/matrices/operaciones/");
        todos(w, '[data-campo="celda"]').forEach((celda, i) => escribir(w, celda, i + 1));
        escribir(w, q(w, '[name="expresion"]'), "AB");
        q(w, '[name="metodo"][value="comparar"]').checked = true;
        w = await calcular(frame); sinTransiciones(w);
        revisar(w, "resultado AB");
        assert(todos(w, "details.procedure-group").length === 4 && !w.document.body.textContent.includes("▸"), "Grupos con el componente, sin «▸»");
        assert(firmas.size === 1, `Mismo chevrón en ${total} desplegables: ${[...firmas]}`);
        const procedimiento = q(w, "#procedimiento"); procedimiento.open = true;
        todos(w, "#procedimiento details").forEach(d => { d.open = true; });
        await tamano(frame, 744, 521);
        w.scrollTo(0, procedimiento.offsetTop + procedimiento.offsetHeight / 2); await turno(w);
        const principal = q(w, "#procedimiento > summary");
        assert(w.getComputedStyle(principal).position === "sticky" && Math.abs(principal.getBoundingClientRect().top - cabecera(w)) <= 1, "El procedimiento sigue sticky bajo la cabecera");
        assert(todos(w, "#procedimiento details > summary").every(s => w.getComputedStyle(s).position === "static"), "Sub-bloques y grupos no son sticky");
    }]);

    // —— UI-62: etiquetas ——
    casos.push(["UI-62: etiquetas con control asociado, sin «:» y un mismo estilo y separación en las siete herramientas", "/", async (w, frame) => {
        let estilo = null; let separacion = null;
        for (const ruta of HERRAMIENTAS) {
            w = await cargar(frame, ruta);
            const etiquetas = visibles(w, ".workspace label:not(.option, .segment, .sr-only), .workspace legend:not(.sr-only)");
            assert(etiquetas.length >= 2, `${ruta}: etiquetas visibles`);
            for (const etiqueta of etiquetas) {
                const texto = etiqueta.textContent.trim().replace(/\s+/g, " ");
                if (etiqueta.tagName === "LABEL") assert(etiqueta.control, `${ruta}: «${texto}» sin control asociado`);
                assert(!texto.endsWith(":"), `${ruta}: «${texto}» termina en «:»`);
                const css = w.getComputedStyle(etiqueta);
                const firma = `${css.fontSize}|${css.fontWeight}|${css.color}`;
                estilo ??= firma;
                assert(firma === estilo, `${ruta}: «${texto}» ${firma} ≠ ${estilo}`);
                // Hasta su control (o el grupo que lo contiene), salvo cuando sigue una ayuda.
                const siguiente = etiqueta.nextElementSibling;
                if (!siguiente || siguiente.matches(".field-help, .sr-only")) continue;
                const hueco = siguiente.getBoundingClientRect().top - etiqueta.getBoundingClientRect().bottom;
                separacion ??= hueco;
                assert(Math.abs(hueco - separacion) < 1, `${ruta}: «${texto}» separa ${hueco.toFixed(1)} ≠ ${separacion.toFixed(1)}`);
            }
        }
    }]);

    // —— UI-65/66: contraste ——
    casos.push(["UI-65/66: bordes de campos ≥ 3:1 (normal, foco y error) y placeholders ≥ 4.5:1, en claro y oscuro", "/", async (w, frame) => {
        for (const ruta of [...HERRAMIENTAS, AUMENTADA, "/"]) {
            w = await cargar(frame, ruta); sinTransiciones(w);
            for (const tema of ["light", "dark"]) {
                w.document.documentElement.setAttribute("data-theme", tema);
                const campos = visibles(w, 'input:not([type="hidden"], [type="radio"], [type="checkbox"]), select, textarea, .stepper-btn');
                for (const campo of campos) {
                    const nombre = `${ruta} ${tema} ${campo.name || campo.className}`;
                    assert(bordeContra(w, campo) >= 3, `${nombre}: borde ${bordeContra(w, campo).toFixed(2)}:1`);
                    if (campo.placeholder) {
                        const interior = fondo(w, campo);
                        const valor = contraste(sobre(rgb(w.getComputedStyle(campo, "::placeholder").color), interior), interior);
                        assert(valor >= 4.5, `${nombre}: placeholder ${valor.toFixed(2)}:1`);
                    }
                }
                // Error y foco en un campo de cálculo (el buscador nunca es inválido).
                const campo = campos.find(c => c.matches("[data-entrada-calculo] :is(input, textarea)"));
                if (!campo) continue;
                const normal = w.getComputedStyle(campo).borderTopColor;
                campo.setAttribute("aria-invalid", "true");
                assert(w.getComputedStyle(campo).borderTopColor !== normal && bordeContra(w, campo) >= 3, `${ruta} ${tema}: el error se distingue`);
                campo.focus();
                assert(bordeContra(w, campo) >= 3, `${ruta} ${tema}: el error conserva contraste con foco`);
                campo.removeAttribute("aria-invalid");
                assert(bordeContra(w, campo) >= 3, `${ruta} ${tema}: foco ≥ 3:1`);
                campo.blur();
            }
        }
    }]);

    // —— UI-67: foco bajo la cabecera ——
    casos.push(["UI-67: anclas y foco quedan bajo la cabecera fija, también bajo el summary sticky", "/romanos/conversion/", async (w, frame) => {
        await tamano(frame, 744, 521);
        escribir(w, q(w, '[name="numero"]'), 3888);
        w = await calcular(frame);
        const resultado = q(w, "#resultado").getBoundingClientRect().top;
        assert(resultado >= cabecera(w) && resultado <= cabecera(w) + 40, `#resultado bajo la cabecera, sin doble reserva: ${resultado}`);
        q(w, '[name="direccion"]:checked').focus({ preventScroll: true });
        w.scrollTo(0, 40); await turno(w);
        const miga = q(w, ".breadcrumbs a");
        assert(miga.getBoundingClientRect().bottom <= cabecera(w), "La miga empieza detrás de la cabecera");
        miga.focus(); await turno(w);
        assert(miga.getBoundingClientRect().top >= cabecera(w), `La miga enfocada queda visible: ${miga.getBoundingClientRect().top}`);
        w = await cargar(frame, "/matrices/inversa/"); await tamano(frame, 1084, 400);
        const mas = q(w, '[data-dimension="orden"] [data-paso="1"]');
        w.scrollTo(0, mas.getBoundingClientRect().top + w.scrollY - 20); await turno(w);
        assert(mas.getBoundingClientRect().top < cabecera(w), "El + de Inversa empieza detrás de la cabecera");
        mas.focus(); await turno(w);
        assert(mas.getBoundingClientRect().top >= cabecera(w), "El + enfocado queda visible");
        w = await cargar(frame, "/matrices/reduccion/"); await tamano(frame, 744, 521);
        escribir(w, q(w, '[name="sistema"]'), SISTEMA);
        q(w, '[name="metodo"][value="comparar"]').checked = true;
        w = await calcular(frame);
        q(w, "#procedimiento").open = true; await turno(w);
        const gauss = q(w, "#procedimiento .disclosure-nested > summary");
        w.scrollTo(0, gauss.getBoundingClientRect().top + w.scrollY - cabecera(w) - 20); await turno(w);
        const sticky = q(w, "#procedimiento > summary").getBoundingClientRect();
        assert(Math.abs(sticky.top - cabecera(w)) <= 1 && gauss.getBoundingClientRect().top < sticky.bottom, "El sub-bloque empieza bajo el summary sticky");
        gauss.focus(); await turno(w);
        assert(gauss.getBoundingClientRect().top >= q(w, "#procedimiento > summary").getBoundingClientRect().bottom - 1, "Enfocado, queda debajo del sticky");
    }]);

    let fallos = 0;
    for (const [titulo, ruta, prueba] of casos) {
        const frame = document.createElement("iframe"); frame.title = titulo;
        frame.style.cssText = "display:block;width:1084px;height:721px;border:0";
        document.body.append(frame);
        const item = document.createElement("li");
        try {
            const w = await cargar(frame, ruta);
            await prueba(w, frame);
            item.textContent = `PASS · ${titulo}`;
        } catch (error) {
            fallos += 1;
            item.textContent = `FAIL · ${titulo}: ${error.message}`;
        }
        document.getElementById("resultados").append(item);
        frame.remove();
    }
    document.getElementById("total").textContent = `${casos.length - fallos}/${casos.length} PASS`;
})();
