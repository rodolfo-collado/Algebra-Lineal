/* Cuaderno de resoluciones con los scripts y formularios de producción, en iframes. */
(async () => {
    const igual = (a, b, mensaje = "") => {
        if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${mensaje} ${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    };
    const cierto = (valor, mensaje) => { if (!valor) throw new Error(mensaje); };
    const q = (w, selector) => w.document.querySelector(selector);
    const todos = (w, selector) => [...w.document.querySelectorAll(selector)];
    const texto = (w, selector) => q(w, selector)?.textContent.replace(/\s+/g, " ").trim() ?? "";
    const valor = (w, selector, v) => {
        const input = q(w, selector);
        input.value = String(v);
        input.dispatchEvent(new w.Event("input", {bubbles: true}));
    };
    const marcar = (w, selector, estado = true) => {
        const casilla = q(w, selector);
        if (casilla.checked !== estado) casilla.click();
    };
    // Espera la página siguiente del iframe tras una acción (clic, envío, enlace).
    const navegar = (frame, accion) => new Promise((resolve, reject) => {
        const limite = setTimeout(() => reject(new Error("La página no respondió")), 15000);
        frame.onload = () => { clearTimeout(limite); resolve(frame.contentWindow); };
        accion(frame.contentWindow);
    });
    const abrir = (frame, url) => navegar(frame, w => { w.location.href = url; });
    const calcularInversa = async (frame, filas) => {
        let w = await abrir(frame, "/matrices/inversa/");
        filas.forEach((fila, i) => fila.forEach((v, j) => valor(w, `[name="celda_A_${i}_${j}"]`, v)));
        return navegar(frame, w => q(w, "[data-calculo]").click());
    };
    const reiniciar = () => fetch("/__pruebas/reiniciar", {cache: "no-store"});

    const casos = [
        ["Calcular anota la resolución y el aviso queda bajo el encabezado del resultado", {}, async (w, frame) => {
            w = await calcularInversa(frame, [[2, 1], [5, 3]]);
            const aviso = q(w, "#resolucion-aviso");
            igual(aviso.dataset.estado, "guardada");
            igual(aviso.previousElementSibling, q(w, "[data-resultado] .results-heading"), "posición del aviso:");
            cierto(texto(w, "#resolucion-aviso").includes("Anotada en tu cuaderno como Matriz inversa · 2×2"), texto(w, "#resolucion-aviso"));
            w = await navegar(frame, w => q(w, "[data-calculo]").click());
            igual(q(w, "#resolucion-aviso").dataset.estado, "existente", "recalcular lo mismo:");
        }],
        ["Añadir a un ejercicio desde la herramienta vuelve a la resolución, ya agrupada", {}, async (w, frame) => {
            w = await calcularInversa(frame, [[1, 2], [3, 4]]);
            q(w, ".resolucion-agrupar > summary").click();
            cierto(q(w, ".resolucion-agrupar .cuaderno-nombre-nuevo").getClientRects().length, "nombre visible para un ejercicio nuevo");
            valor(w, '.resolucion-agrupar [name="nombre_ejercicio"]', "Tarea 3");
            w = await navegar(frame, w => q(w, ".resolucion-agrupar-form button").click());
            igual(new URL(w.location.href).searchParams.has("resolucion"), true);
            igual(q(w, "#resolucion-aviso").dataset.estado, "abierta");
            cierto(texto(w, "#resolucion-aviso").includes("ejercicio Tarea 3"), texto(w, "#resolucion-aviso"));
            igual(todos(w, ".resolucion-agrupar").length, 0, "ya agrupada, no se ofrece otra vez:");
        }],
        ["Reabrir desde el cuaderno muestra datos y resultado; editar lo marca desactualizado", {}, async (w, frame) => {
            w = await calcularInversa(frame, [[4, 7], [2, 6]]);
            w = await abrir(frame, "/resoluciones/");
            w = await navegar(frame, w => q(w, ".hoja-nombre a").click());
            igual(q(w, '[name="celda_A_0_1"]').value, "7");
            igual(q(w, "#resultado").dataset.resultado, "vigente");
            cierto(texto(w, "#resultado").includes("A es invertible"), "resultado restaurado");
            valor(w, '[name="celda_A_0_1"]', "8");
            igual(q(w, "#resultado").dataset.resultado, "desactualizado");
        }],
        ["Selección: recuento, marcar un día completo y acciones que piden algo marcado", {}, async (w, frame) => {
            await calcularInversa(frame, [[1, 1], [0, 1]]);
            await calcularInversa(frame, [[3, 1], [2, 1]]);
            w = await abrir(frame, "/resoluciones/");
            const barra = q(w, "[data-seleccion]");
            igual(barra.hasAttribute("data-activa"), false);
            w.document.querySelector('[data-requiere-seleccion][value="agrupar"]').click();
            cierto(texto(w, "[data-seleccion-cuenta]").includes("Primero marca"), "aviso sin selección");
            const dia = q(w, ".hoja-dia [data-marcar-grupo]");
            igual(dia.hidden, false);
            dia.click();
            igual(texto(w, "[data-seleccion-cuenta]"), "2 marcadas:");
            igual(barra.hasAttribute("data-activa"), true);
            igual(getComputedStyle(barra).position, "sticky");
            todos(w, '.hoja-dia input[name="ids"]')[0].click();
            igual(dia.indeterminate, true);
            dia.click();
            w = await navegar(frame, w => q(w, '[data-requiere-seleccion][value="agrupar"]').click());
            cierto(texto(w, ".cuaderno-hecho").startsWith("Reuniste 2 resoluciones en «Ejercicio 1»"), texto(w, ".cuaderno-hecho"));
            igual(todos(w, "ol.hoja-pasos > .hoja-entrada").length, 2);
            cierto(w.getComputedStyle(q(w, "ol.hoja-pasos .hoja-nombre"), "::before").content.includes("counter(paso"), "pasos numerados");
        }],
        ["Renombrar con Enter solo envía su propio formulario", {}, async (w, frame) => {
            await calcularInversa(frame, [[5, 2], [2, 1]]);
            w = await abrir(frame, "/resoluciones/");
            q(w, ".hoja-entrada .hoja-editar > summary").click();
            const campo = q(w, '.hoja-entrada [name="nombre"]');
            valor(w, '.hoja-entrada [name="nombre"]', "Inversa de la tarea");
            w = await navegar(frame, () => campo.form.requestSubmit());
            igual(texto(w, ".cuaderno-hecho"), "Cambiaste el nombre de la resolución.");
            igual(texto(w, ".hoja-nombre"), "Inversa de la tarea");
        }],
        ["Eliminar pide confirmación y Cancelar no borra nada", {}, async (w, frame) => {
            await calcularInversa(frame, [[6, 1], [5, 1]]);
            w = await abrir(frame, "/resoluciones/");
            marcar(w, '.hoja-entrada input[name="ids"]');
            w = await navegar(frame, w => q(w, '[data-requiere-seleccion][value="eliminar"]').click());
            cierto(texto(w, ".confirmation").includes("¿Eliminar esta resolución?"), texto(w, ".confirmation"));
            w = await navegar(frame, w => q(w, ".confirmation a.btn").click());
            igual(todos(w, ".hoja-entrada").length, 1);
            marcar(w, '.hoja-entrada input[name="ids"]');
            w = await navegar(frame, w => q(w, '[data-requiere-seleccion][value="eliminar"]').click());
            w = await navegar(frame, w => q(w, '.confirmation [value="eliminar_confirmado"]').click());
            igual(texto(w, ".cuaderno-hecho"), "Eliminaste 1 resolución del cuaderno.");
            cierto(q(w, ".cuaderno-blanco"), "vuelve el cuaderno en blanco");
        }],
        ["Sin JavaScript: la barra se ve siempre y reunir funciona con el formulario", {sinJS: true}, async (w, frame) => {
            await reiniciar();
            w = await abrir(frame, "/resoluciones/");
            cierto(q(w, ".cuaderno-blanco"), "en blanco al empezar");
            w = await abrir(frame, "/romanos/conversion/");
            valor(w, '[name="numero"]', "1963");
            w = await navegar(frame, w => q(w, 'form[action$="#resultado"] [type="submit"]:not([formnovalidate])').click());
            igual(q(w, "#resolucion-aviso").dataset.estado, "guardada");
            w = await abrir(frame, "/resoluciones/");
            igual(getComputedStyle(q(w, "[data-seleccion]")).display, "flex");
            igual(q(w, "[data-marcar-grupo]").hidden, true);
            marcar(w, '.hoja-entrada input[name="ids"]');
            w = await navegar(frame, w => q(w, '[data-requiere-seleccion][value="agrupar"]').click());
            cierto(texto(w, ".cuaderno-hecho").startsWith("Reuniste 1 resolución"), texto(w, ".cuaderno-hecho"));
        }],
    ];

    // Coherencia en los cinco estilos y los dos temas: la cabecera no se solapa y el cuaderno no se desborda.
    for (const estilo of ["estudio", "minimalista", "chocolab", "belugacalc", "heyalgb"]) {
        for (const tema of ["light", "dark"]) {
            casos.push([`${estilo} · ${tema}: cabecera sin solapes, aviso y hoja legibles`, {estilo, tema, ancho: 1280}, async (w, frame) => {
                await calcularInversa(frame, [[2, 0], [0, 2]]);
                w = frame.contentWindow;
                igual(w.document.documentElement.dataset.estilo, estilo);
                const acciones = q(w, ".header-actions").getBoundingClientRect();
                const areas = todos(w, ".nav-areas a").filter(a => a.getClientRects().length);
                for (const enlace of areas) {
                    cierto(enlace.getBoundingClientRect().right <= acciones.left + 1, `«${enlace.textContent.trim()}» queda bajo las acciones`);
                }
                const aviso = q(w, "#resolucion-aviso");
                cierto(getComputedStyle(aviso).color !== getComputedStyle(aviso).backgroundColor, "texto del aviso visible");
                w = await abrir(frame, "/resoluciones/");
                igual(q(w, ".header-resoluciones").getAttribute("aria-current"), "page");
                cierto(w.document.documentElement.scrollWidth <= w.innerWidth, "sin desbordamiento horizontal");
            }]);
        }
    }
    casos.push(["Móvil (390 px): filtros, hoja y barra caben sin desbordar", {ancho: 390}, async (w, frame) => {
        await calcularInversa(frame, [[1, 3], [2, 7]]);
        w = await abrir(frame, "/resoluciones/");
        cierto(w.document.documentElement.scrollWidth <= w.innerWidth, `desborda: ${w.document.documentElement.scrollWidth}`);
        marcar(w, '.hoja-entrada input[name="ids"]');
        const barra = q(w, "[data-seleccion]").getBoundingClientRect();
        cierto(barra.right <= w.innerWidth && barra.left >= 0, "barra dentro de la pantalla");
    }]);

    let pasadas = 0;
    for (const [nombre, opciones, prueba] of casos) {
        await reiniciar();
        localStorage.setItem("pygebra-estilo", opciones.estilo ?? "estudio");
        localStorage.setItem("pygebra-tema", opciones.tema ?? "light");
        const frame = document.createElement("iframe");
        frame.style.width = `${opciones.ancho ?? 1100}px`;
        frame.style.height = "800px";
        if (opciones.sinJS) frame.setAttribute("sandbox", "allow-same-origin allow-forms");
        frame.src = "/resoluciones/";
        const cargado = new Promise(resolve => { frame.onload = resolve; });
        document.body.append(frame);
        await cargado;
        const item = document.createElement("li");
        try { await prueba(frame.contentWindow, frame); pasadas++; item.textContent = `PASS · ${nombre}`; }
        catch (error) { item.textContent = `FAIL · ${nombre}: ${error.message}`; }
        document.querySelector("#resultados").append(item);
        frame.remove();
    }
    localStorage.removeItem("pygebra-estilo");
    localStorage.removeItem("pygebra-tema");
    document.querySelector("#total").textContent = `${pasadas}/${casos.length} PASS`;
})();
