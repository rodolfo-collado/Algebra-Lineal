/* P27.11: claridad de entrada con formularios, CSS y scripts reales. Tab real: QA complementaria. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const todos = (w, s) => [...w.document.querySelectorAll(s)];
    const igual = (a, b, mensaje = "") => {
        if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${mensaje} ${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    };
    const cierto = (ok, mensaje) => { if (!ok) throw new Error(mensaje); };
    const valor = (w, s, v) => {
        const input = q(w, s); input.value = String(v);
        input.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const elegir = (w, s, v) => {
        const select = q(w, s); select.value = String(v);
        select.dispatchEvent(new w.Event("change", { bubbles: true }));
    };
    const visibles = (w, s) => todos(w, `${s} [data-direccion]`)
        .filter(n => w.getComputedStyle(n).display !== "none").map(n => n.textContent);
    const tamano = async (frame, ancho, alto) => {
        frame.style.width = `${ancho}px`; frame.style.height = `${alto}px`;
        await new Promise(resolve => setTimeout(resolve, 40));
    };
    const cabe = w => cierto(w.document.documentElement.scrollWidth <= w.document.documentElement.clientWidth + 1, "Desborde de página");
    const herramientas = ["/matrices/reduccion/", "/vectores/operaciones/", "/matrices/operaciones/",
        "/matrices/ecuaciones/", "/matrices/inversa/", "/bases/conversion/", "/romanos/conversion/"];
    const casos = [];
    const caso = (nombre, ruta, test, sinJS = false) => casos.push({ nombre, ruta, test, sinJS });

    caso("UI-21/UI-07: Inicio abre los temas de una herramienta y nombra «Álgebra lineal»", "/", w => {
        const abiertos = todos(w, "details.topic").filter(d => d.open).map(d => d.id);
        igual(abiertos, ["vectores", "bases-numericas", "numeracion-romana"]);
        igual(q(w, "#matrices").open, false, "Matrices sigue plegado");
        igual(todos(w, "details.home-area").some(d => d.open), false, "Las áreas siguen plegadas");
        igual(q(w, "#area-algebra-lineal").textContent, "Álgebra lineal");
        cierto(q(w, '#vectores a.tool-link[href="/vectores/operaciones/"]'), "La herramienta única está dentro del tema abierto");
    });
    caso("UI-21: el filtro en vivo restaura lo que el usuario abrió o cerró", "/", w => {
        q(w, "#vectores").open = false; q(w, "#matrices").open = true;
        const estado = () => todos(w, "#catalogo-inicio details").map(d => `${d.id}:${d.open}`);
        const antes = estado();
        valor(w, "#buscador-inicio", "gauss");
        igual(todos(w, "#catalogo-inicio [data-grupo]").every(g => g.hidden), true);
        valor(w, "#buscador-inicio", "");
        igual(estado(), antes);
    });
    for (const ruta of herramientas) caso(`UI-72: ${ruta} sin kicker, con migas, h1 y descripción`, ruta, w => {
        igual(q(w, ".tool-kicker"), null);
        igual([...q(w, ".tool-header").children].map(n => n.className), ["tool-title", "tool-lead"]);
        const migas = todos(w, ".breadcrumbs li").map(n => n.textContent.trim());
        igual(migas.length, 4); igual(migas[3], q(w, "h1").textContent.trim());
        cierto(["Álgebra lineal", "Sistemas numéricos"].includes(migas[1]), `Área: ${migas[1]}`);
        cierto(q(w, ".breadcrumbs").compareDocumentPosition(q(w, "h1")) & w.Node.DOCUMENT_POSITION_FOLLOWING, "Migas antes del título");
    });
    for (const [ancho, alto] of [[1280, 650], [390, 650]]) caso(`UI-43: «Ecuaciones» y separación tras las pistas, ${ancho}×${alto}`, "/matrices/reduccion/", async (w, frame) => {
        await tamano(frame, ancho, alto);
        igual(q(w, 'label[for="id_sistema"]').textContent.trim(), "Ecuaciones");
        igual(todos(w, '[name="tipo_entrada"]').map(i => i.closest("label").textContent.trim()), ["Sistema de ecuaciones", "Matriz aumentada"]);
        const gap = () => {
            const pista = Math.max(...todos(w, ".choice-row .option-help").filter(p => !p.hidden).map(p => p.getBoundingClientRect().bottom));
            const campo = todos(w, ".input-mode").find(f => !f.hidden).getBoundingClientRect().top;
            return campo - pista;
        };
        const fuente = parseFloat(w.getComputedStyle(w.document.documentElement).fontSize);
        for (const tipo of ["sistema", "matriz"]) {
            q(w, `[name="tipo_entrada"][value="${tipo}"]`).click();
            cierto(gap() >= fuente * 0.75 && gap() <= fuente * 2, `Separación ${tipo}: ${gap()}`);
        }
        cabe(w);
    });
    caso("UI-40: etiqueta y ayuda siguen a la dirección", "/romanos/conversion/", w => {
        const input = q(w, "#id_numero");
        igual(visibles(w, 'label[for="id_numero"]'), ["Número arábigo"]);
        igual(visibles(w, "#numero-ayuda"), ["Un entero del 1 al 3999, escrito con cifras."]);
        q(w, '[name="direccion"][value="romano_a_decimal"]').click();
        igual(input.labels[0].innerText.trim(), "Número romano");
        cierto(w.document.getElementById(input.getAttribute("aria-describedby")).innerText.startsWith("Escrito con I, V, X, L, C, D y M"), "Ayuda romana");
        q(w, '[name="direccion"][value="decimal_a_romano"]').click();
        igual(input.labels[0].innerText.trim(), "Número arábigo");
    });
    caso("UI-40 sin JS: el CSS cambia la etiqueta igual", "/romanos/conversion/", w => {
        q(w, '[name="direccion"][value="romano_a_decimal"]').click();
        igual(visibles(w, 'label[for="id_numero"]'), ["Número romano"]);
    }, true);
    for (const [direccion, numero, esperado] of [
        ["decimal_a_romano", "XIV", "XIV parece un número romano. Cambia a Romano → arábigo."],
        ["romano_a_decimal", "14", "14 está escrito con cifras arábigas. Cambia a Arábigo → romano."],
        ["decimal_a_romano", "IIII", "Ingresa un número entero entre 1 y 3999, escrito solo con dígitos."],
    ]) caso(`UI-40: error de ${numero} en ${direccion}`, "/romanos/conversion/", async (w, frame) => {
        q(w, `[name="direccion"][value="${direccion}"]`).click(); valor(w, "#id_numero", numero);
        w = await new Promise(resolve => { frame.onload = () => resolve(frame.contentWindow); q(w, "[data-calculo]").click(); });
        igual(todos(w, ".errorlist li").map(n => n.textContent), [esperado]);
        igual(q(w, "#id_numero").value, numero); // Nada se convierte por su cuenta.
    });
    caso("UI-41: base de origen antes del número y teclado según la base", "/bases/conversion/", w => {
        const orden = todos(w, "#conversion-form select, #conversion-form input:not([type=hidden])").map(n => n.name);
        igual(orden.slice(0, 2), ["base_origen", "numero"]);
        igual(orden.slice(2).every(n => n === "bases_destino"), true);
        // La validación en vivo sigue a la base elegida: 1A no vale en decimal y sí en hexadecimal.
        valor(w, "#id_numero", "1A");
        igual(q(w, "#numero-aviso").textContent, "El dígito A no es válido en un número decimal.");
        elegir(w, "#id_base_origen", "16");
        igual(q(w, "#number-fields").dataset.perfil, "base-16");
        igual(q(w, "#id_numero").labels[0].innerText.trim(), "Número hexadecimal");
        igual(q(w, "#numero-aviso").hidden, true, "1A vale en hexadecimal");
        // El teclado del campo es el perfil de su contenedor; abrirlo con foco real se comprueba en Browser.
        const perfiles = JSON.parse(q(w, "#math-keyboard-profiles").textContent);
        const teclas = perfiles[q(w, "#number-fields").dataset.perfil].grupos.flatMap(g => g.teclas.map(t => t.etiqueta));
        cierto(["A", "B", "C", "D", "E", "F"].every(t => teclas.includes(t)), `Teclas: ${teclas}`);
        elegir(w, "#id_base_origen", "10");
        igual(q(w, "#numero-aviso").hidden, false, "Al volver a decimal, A ya no vale");
        igual(todos(w, "[data-destino-base]").filter(o => !o.hidden).map(o => o.dataset.destinoBase), ["2", "8", "16"]);
    });
    caso("UI-41: convertir 1A desde hexadecimal", "/bases/conversion/", async (w, frame) => {
        elegir(w, "#id_base_origen", "16"); valor(w, "#id_numero", "1A");
        w = await new Promise(resolve => { frame.onload = () => resolve(frame.contentWindow); q(w, "[data-calculo]").click(); });
        cierto(q(w, ".panel-final").textContent.includes("11010"), "1A₁₆ = 11010₂");
        igual([q(w, "#id_base_origen").value, q(w, "#id_numero").value], ["16", "1A"]);
    });
    caso("UI-42: v1, v2 desde el principio; agregar y quitar no renombran", "/vectores/operaciones/", w => {
        const filas = () => todos(w, ".vector-row[data-vector]").map(f => f.dataset.vector);
        const estado = () => q(w, "[data-estado-vectores]").textContent;
        igual(filas(), ["v1", "v2"]);
        igual(q(w, '[data-vector="v1"]').getAttribute("aria-label"), "Vector v1");
        igual(q(w, '[name="v1_0"]').getAttribute("aria-label"), "Componente 1 de v1");
        valor(w, '[name="v1_0"]', "1"); valor(w, '[name="v2_0"]', "2");
        q(w, "[data-agregar-vector]").click();
        igual([filas(), estado(), w.document.activeElement.name], [["v1", "v2", "v3"], "Se agregó el vector v3.", "v3_0"]);
        q(w, "[data-agregar-vector]").click();
        igual([filas(), estado()], [["v1", "v2", "v3", "v4"], "Se agregó el vector v4."]);
        igual([q(w, '[name="v1_0"]').value, q(w, '[name="v2_0"]').value], ["1", "2"]);
        q(w, '[aria-label="Quitar vector v4"]').click();
        igual([filas(), estado()], [["v1", "v2", "v3"], "Se eliminó el vector v4."]);
        q(w, '[name="operacion"][value="escalar"]').click();
        igual([filas(), q(w, '[name="v1_0"]').value], [["v1"], "1"]);
        q(w, '[name="operacion"][value="combinacion"]').click();
        igual(filas()[0], "v1"); igual(filas().at(-1), "b");
        q(w, '[name="operacion"][value="suma"]').click();
        valor(w, "#id_dimension", 10);
        igual(todos(w, '.vector-row[data-vector="v1"] input').length, 10);
        igual(q(w, '[name="v3_9"]').getAttribute("aria-label"), "Componente 10 de v3");
    });
    caso("UI-42: ayudas con decimales y resultado sin kicker repetido", "/vectores/operaciones/", async (w, frame) => {
        cierto(q(w, ".vector-help:not([data-operacion-hint-fields])").textContent.includes("decimales con punto"), "Ayuda de Vectores");
        valor(w, '[name="v1_0"]', "0.5"); valor(w, '[name="v1_1"]', "1"); valor(w, '[name="v1_2"]', "1/2");
        valor(w, '[name="v2_0"]', "1"); valor(w, '[name="v2_1"]', "2"); valor(w, '[name="v2_2"]', "3");
        w = await new Promise(resolve => { frame.onload = () => resolve(frame.contentWindow); q(w, "[data-calculo]").click(); });
        igual(q(w, "#resultado .section-kicker"), null);
        cierto(q(w, ".panel-final").textContent.includes("v1 + v2"), "Expresión v1 + v2");
    });
    for (const ruta of ["/matrices/ecuaciones/", "/matrices/inversa/"]) caso(`UI-42: ayuda numérica de ${ruta}`, ruta, w => {
        cierto(todos(w, ".field-help").some(p => /enteros, fracciones como 1\/2 o decimales con punto/.test(p.textContent)), "Ayuda con decimales");
    });
    for (const tema of ["light", "dark"]) for (const ruta of ["/bases/conversion/", "/romanos/conversion/", "/matrices/reduccion/", "/vectores/operaciones/"]) {
        caso(`Responsive 390×650 ${tema}: ${ruta}`, ruta, async (w, frame) => {
            await tamano(frame, 390, 650);
            w.document.documentElement.dataset.theme = tema;
            cabe(w);
            const select = q(w, "#id_base_origen");
            if (select) cierto(select.getBoundingClientRect().right <= w.document.documentElement.clientWidth, "Selector dentro del ancho");
        });
    }

    let passed = 0;
    for (const {nombre, ruta, test, sinJS} of casos) {
        const frame = document.createElement("iframe");
        frame.style.width = "1280px"; frame.style.height = "650px";
        if (sinJS) frame.setAttribute("sandbox", "allow-same-origin allow-forms");
        const loaded = new Promise(resolve => { frame.onload = resolve; });
        frame.src = ruta; document.body.append(frame); await loaded;
        const item = document.createElement("li");
        try { await test(frame.contentWindow, frame); passed++; item.textContent = `PASS · ${nombre}`; }
        catch (error) { item.textContent = `FAIL · ${nombre}: ${error.message}`; }
        document.querySelector("#resultados").append(item); frame.remove();
    }
    document.querySelector("#total").textContent = `${passed}/${casos.length} PASS`;
})();
