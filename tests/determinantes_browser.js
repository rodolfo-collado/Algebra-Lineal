/* Formularios y POST reales; los eventos sintéticos solo simulan la interacción. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const todos = (w, s) => [...w.document.querySelectorAll(s)];
    const ok = (condicion, mensaje) => { if (!condicion) throw new Error(mensaje); };
    const valor = (w, s, v) => {
        const input = q(w, s); input.value = String(v);
        input.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const cargar = (w, a) => {
        valor(w, '[name="orden"]', a.length);
        a.forEach((fila, i) => fila.forEach((v, j) => valor(w, `[name="celda_A_${i}_${j}"]`, v)));
    };
    const post = (frame, s = "[data-boton-determinante]") => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 15000);
        frame.onload = () => { clearTimeout(timer); resolve(frame.contentWindow); };
        q(frame.contentWindow, s).click();
    });
    const A = [[1, 2, 3], [4, 5, 6], [7, 8, 10]];
    const elegir = async (w, frame, a = A) => { cargar(w, a); return post(frame); };
    const invalida = w => {
        ok(q(w, "[data-eleccion]").hidden, "La etapa anterior se oculta");
        ok(todos(w, "[data-eleccion] input, [data-eleccion] select").every(c => c.disabled), "La elección anterior no se envía");
        ok(q(w, "[data-boton-determinante]").textContent === "Calcular determinante", "Vuelve al análisis");
        ok(q(w, "[data-estado-eleccion]").textContent.includes("volver a analizarla"), "Anuncia el cambio");
    };
    const casos = [
        ["Inicio simple", w => {
            ok(!q(w, '[name="metodo"], [data-eleccion], [name="expansion"]'), "Sin elección anticipada");
            ok(todos(w, "[data-calculo]").length === 1, "Un botón principal");
            ok(!w.document.body.textContent.includes("Recomendar método"), "Sin acción secundaria");
        }],
        ["1×1 calcula con un clic y conserva el procedimiento", async (w, frame) => {
            cargar(w, [["-2/3"]]);
            ok(q(w, "[data-boton-determinante]").formAction.endsWith("#resultado"), "Destino del cálculo directo");
            w = await post(frame);
            ok(q(w, "[data-determinante]").textContent.trim() === "det(A) = -2/3", "Valor exacto con un clic");
            ok(!q(w, '[data-eleccion], [data-recomendacion], [name="metodo"], [name="expansion"]'), "Sin elección artificial");
            ok(q(w, "#procedimiento").textContent.includes("En una matriz 1×1, el determinante es su única entrada: -2/3."), "Explicación didáctica");
            ok(!q(w, "#procedimiento").open, "Procedimiento plegable");
            ok(w.document.activeElement === q(w, "#resultado"), "Foco en resultado");
            w = await elegir(w, frame, [[1, 2], [3, 4]]);
            ok(q(w, '[name="metodo"]:checked').value === "directo_2x2", "Al crecer vuelve a elegir");
            valor(w, '[name="orden"]', 1);
            ok(q(w, "[data-estado-eleccion]").textContent.includes("obtener su única entrada"), "Anuncia el cálculo directo");
            valor(w, '[name="celda_A_0_0"]', 0);
            w = await post(frame);
            ok(q(w, "[data-determinante]").textContent.trim() === "det(A) = 0", "Al reducir a 1×1 vuelve a calcular directo");
        }],
        ["Análisis, recomendación, foco y métodos disponibles", async (w, frame) => {
            w = await elegir(w, frame);
            ok(!q(w, "#resultado, [data-confirmacion]"), "Todavía no calcula ni presupuesta");
            ok(q(w, '[name="metodo"]:checked').value === "sarrus", "Preselecciona Sarrus");
            ok(todos(w, '[name="metodo"]').map(c => c.value).join() === "sarrus,cofactores,lu,reduccion", "Todas las alternativas");
            ok(todos(w, '[name="metodo"]').every(c => !c.disabled), "Todas habilitadas");
            ok(w.document.activeElement === q(w, "[data-eleccion]"), "Foco en la nueva etapa");
            ok(!q(w, "#razon-determinante"), "Sin disclosure redundante");
            ok(todos(w, "[data-recomendacion] p").length === 1, "Una explicación compacta");
            ok(q(w, "[data-recomendacion]").textContent.includes("Puedes elegir cualquier otro método disponible"), "Elección libre");
            ok(q(w, "[data-expansion]").hidden, "Cofactores oculto con Sarrus");
        }],
        ["Otro método y desarrollo por columna se respetan", async (w, frame) => {
            w = await elegir(w, frame);
            const firma = q(w, '[name="eleccion"]').value;
            q(w, '[name="metodo"][value="cofactores"]').click();
            ok(!q(w, "[data-expansion]").hidden && !q(w, '[name="expansion"]').disabled, "Desarrollar por visible");
            q(w, '[name="expansion"]').value = "columna_2";
            q(w, '[name="expansion"]').dispatchEvent(new w.Event("change", { bubbles: true }));
            ok(q(w, '[name="eleccion"]').value === firma, "Cambiar método no invalida A");
            w = await post(frame);
            ok(q(w, "[data-determinante]").textContent.trim() === "det(A) = -3", "Determinante exacto");
            ok(!q(w, '[data-eleccion], [data-recomendacion], [name="metodo"], [name="expansion"]'), "Resultado sin etapa de elección");
            ok(q(w, ".section-kicker").textContent.includes("Cofactores"), "Encabezado identifica el método usado");
            ok(q(w, "#procedimiento").textContent.includes("columna 2, la que se eligió"), "Conserva expansión");
        }],
        ["LU se detiene sin permutar y permite volver a elegir", async (w, frame) => {
            w = await elegir(w, frame, [[0, 1], [1, 0]]);
            q(w, '[name="metodo"][value="lu"]').click();
            w = await post(frame);
            ok(q(w, "#resultado").textContent.includes("no implementa PA = LU"), "Explica el límite del procedimiento");
            ok(!q(w, "[data-determinante], [data-eleccion], [data-recomendacion]"), "Sin determinante inventado ni elección residual");
            w = await post(frame);
            ok(q(w, "[data-eleccion]") && !q(w, "#resultado"), "Reabre la elección");
            q(w, '[name="metodo"][value="reduccion"]').click();
            w = await post(frame);
            ok(q(w, "[data-determinante]").textContent.trim() === "det(A) = -1", "Reducción resuelve con intercambio");
        }],
        ["Editar celda invalida y exige otro análisis", async (w, frame) => {
            w = await elegir(w, frame);
            const firma = q(w, '[name="eleccion"]').value;
            const input = q(w, '[name="celda_A_0_0"]'); input.focus();
            valor(w, '[name="celda_A_0_0"]', 9); invalida(w);
            ok(w.document.activeElement === input, "Conserva foco en la celda");
            w = await post(frame);
            ok(q(w, "[data-eleccion]") && !q(w, "#resultado"), "Vuelve a elegir antes del cálculo");
            ok(q(w, '[name="eleccion"]').value !== firma, "Firma de la nueva A");
        }],
        ["Dimensión inválida o nueva invalida la elección", async (w, frame) => {
            w = await elegir(w, frame);
            valor(w, '[name="orden"]', ""); invalida(w);
            valor(w, '[name="orden"]', 4);
            ok(todos(w, "input.matrix-input").length === 16, "Redibuja A");
            ok(q(w, '[name="celda_A_0_0"]').value === "1", "Conserva celdas");
            invalida(w);
        }],
        ["Menú contextual y Deshacer no recuperan la elección antigua", async (w, frame) => {
            w = await elegir(w, frame);
            const input = q(w, '[name="celda_A_0_0"]'); input.focus(); input.setSelectionRange(1, 1);
            input.dispatchEvent(new w.MouseEvent("contextmenu", { bubbles: true, cancelable: true, button: -1 }));
            ok(!q(w, "[data-edicion-menu]").hidden, "El menú sigue disponible");
            q(w, '[data-edicion-menu] [data-accion="limpiar"]').click(); invalida(w);
            ok(todos(w, "input.matrix-input").every(c => c.value === ""), "Limpiar funciona");
            q(w, "[data-deshacer-pegado]").click(); invalida(w);
            ok(q(w, '[name="celda_A_0_0"]').value === "1", "Deshacer restaura valores");
        }],
        ["Presupuesto posterior de Cofactores y cambio manual", async (w, frame) => {
            const a = Array.from({ length: 6 }, (_, i) => Array.from({ length: 6 }, (_, j) => i === j ? `1${"0".repeat(99)}` : 1));
            w = await elegir(w, frame, a);
            ok(!q(w, "[data-confirmacion]"), "Analizar no pide presupuesto");
            ok(q(w, '[name="metodo"][value="cofactores"]'), `Elección de Cofactores disponible: ${todos(w, '.field-error').map(e => e.textContent).join()}`);
            q(w, '[name="metodo"][value="cofactores"]').click();
            w = await post(frame);
            ok(q(w, "[data-confirmacion]") && !q(w, "#resultado"), "Pide confirmación del elegido");
            ok(q(w, '[name="metodo"]:checked').value === "cofactores", "No sustituye Cofactores");
            ok(q(w, '[name="metodo"][value="reduccion"]'), "Reducción sigue disponible después del presupuesto");
            q(w, '[name="metodo"][value="reduccion"]').click();
            ok(q(w, "[data-confirmacion]").hidden, "Cambiar método oculta confirmación antigua");
            ok(!q(w, "[data-eleccion]").hidden, "Conserva análisis de A");
        }],
    ];
    let passed = 0;
    for (const [nombre, test] of casos) {
        const frame = document.createElement("iframe"); frame.style.width = "1100px"; frame.style.height = "760px";
        const loaded = new Promise(resolve => { frame.onload = resolve; });
        frame.src = "/matrices/determinantes/"; document.body.append(frame); await loaded;
        const item = document.createElement("li");
        try { await test(frame.contentWindow, frame); passed++; item.textContent = `PASS · ${nombre}`; }
        catch (error) { item.textContent = `FAIL · ${nombre}: ${error.message}`; }
        document.querySelector("#resultados").append(item); frame.remove();
    }
    document.querySelector("#total").textContent = `${passed}/${casos.length} PASS`;
})();
