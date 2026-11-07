/* Usa formularios Django y scripts de producción, sin un evaluador de pruebas en JS. */
(async () => {
    "use strict";
    const q = (w, selector) => w.document.querySelector(selector);
    const ok = (condicion, mensaje) => { if (!condicion) throw new Error(mensaje); };
    const valor = (w, nombre, texto) => {
        const campo = q(w, `[name="${nombre}"]`);
        campo.value = texto;
        campo.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const post = (frame, selector = '[data-calculo]') => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 15000);
        frame.onload = () => { clearTimeout(timer); resolve(frame.contentWindow); };
        q(frame.contentWindow, selector).click();
    });
    const casos = [
        ["P3 y P4: potencia, pares y recta interactiva exacta", async (w, frame) => {
            valor(w,'expresion','|potencia(A)|'); w = await post(frame);
            ok(q(w,'[data-respuesta-relacion]')?.textContent === '4','Potencia: '+[...w.document.querySelectorAll('.field-error')].map(e=>e.textContent).join(';'));
            valor(w,'expresion','intervalo(0, 2, cerrado, cerrado) ∖ intervalo(1, 1, cerrado, cerrado)');
            valor(w,'punto','1'); w = await post(frame);
            ok(q(w,'[data-consulta-punto]')?.textContent.includes('no pertenece'),'Consulta exacta: '+[...w.document.querySelectorAll('.field-error')].map(e=>e.textContent).join(';'));
            const grafica = q(w,'[data-recta] svg');
            ok(grafica && w.document.querySelectorAll('[data-tramo]').length === 2,'Dos tramos');
            const acercar = [...w.document.querySelectorAll('[data-recta] button')].find(b=>b.textContent === 'Acercar');
            acercar.click(); ok(grafica.getAttribute('viewBox') !== '0 0 100 32','Zoom');
        }],
        ["P5: regiones de Venn y selección desde el motor", async (w, frame) => {
            valor(w,'expresion','A ∖ B'); valor(w,'venn_nombres','A, B'); w = await post(frame);
            ok(w.document.querySelectorAll('[data-region]').length === 4,'Cuatro regiones');
            const datos = JSON.parse(q(w,'#conjuntos-resultado-datos').textContent);
            ok(datos.venn.regiones[1].seleccionada,'Solo A resaltada');
            q(w,'[data-venn] button').click();
            ok(q(w,'[data-venn] [aria-live]').textContent.length > 0,'Detalle accesible');
        }],
        ["P6: cardinalidades editables y validación de coherencia", async (w, frame) => {
            await new Promise(resolve=>{frame.onload=resolve;frame.src='/conjuntos/cardinalidad/';}); w=frame.contentWindow;
            valor(w,'region_1','5'); valor(w,'region_2','3'); valor(w,'region_3','2');
            w=await post(frame); ok(q(w,'[data-cardinalidad]').textContent === '10','Suma exclusiva');
            valor(w,'region_1','7'); ok(q(w,'#resultado').dataset.resultado === 'desactualizado','Cambio invalida el resultado P6');
            w=await post(frame); ok(q(w,'[data-cardinalidad]').textContent === '12','Recalcula');
            valor(w,'universo','1'); w=await post(frame); ok(!q(w,'[data-cardinalidad]'),'Rechaza universo menor');
        }],
        ["P2 calcula operaciones, cardinalidad y relaciones con datos estructurados", async (w, frame) => {
            for (const [expresion, esperado, tipo] of [
                ["A ∪ B", "{1, 2, {1, 2}}", "conjunto"],
                ["∁(A, A ∪ B)", "{{1, 2}}", "conjunto"],
                ["|A ∩ B|", "1", "numero"],
                ["{1,2} ∈ A ∪ B", "Verdadero", "booleano"],
                ["A ∪ B ∖ {2} = {1,{1,2}}", "Verdadero", "booleano"],
            ]) {
                valor(w, "expresion", expresion);
                w = await post(frame);
                ok(q(w, "[data-respuesta-relacion]")?.textContent === esperado, expresion);
                const datos = JSON.parse(q(w, "#conjuntos-resultado-datos").textContent);
                ok(datos.valor.tipo === tipo, "Tipo de resultado explícito");
                ok(datos.procedimiento.length > 0, "Procedimiento estructurado");
                ok(w.document.activeElement === q(w, "#resultado"), "Foco en resultado P2");
            }
        }],
        ["P2 inserta símbolos y rechaza complementos fuera del universo", async (w, frame) => {
            const campo = q(w, '[name="expresion"]');
            valor(w, "expresion", ""); campo.focus();
            await new Promise(resolve => w.requestAnimationFrame(resolve));
            q(w, '[data-insercion="∁(, )"]').click();
            ok(campo.value === "∁(, )" && campo.selectionStart === 2, "Cursor dentro del complemento");
            for (const simbolo of ["∪", "∩", "∖", "||"]) ok(q(w, `[data-insercion="${simbolo}"]`), simbolo);
            valor(w, "expresion", "∁(A,B)");
            w = await post(frame);
            ok(!q(w, "#resultado"), "Sin complemento inválido");
            ok(q(w, '[name="expresion"]').getAttribute("aria-invalid") === "true", "Error P2 accesible");
            ok(w.document.body.textContent.includes("universo explícito"), "Explica el universo");
        }],
        ["Diez casos de aceptación mediante POST real", async (w, frame) => {
            for (const [expresion, esperado] of [
                ["2 ∈ A", "Verdadero"], ["3 ∈ A", "Falso"], ["A ∈ B", "Verdadero"],
                ["A ⊆ B", "Falso"], ["{2} ⊆ B", "Verdadero"], ["A ⊂ A", "Falso"],
                ["∅ ⊆ A", "Verdadero"], ["∅ ∈ A", "Falso"],
                ["{1, 2} = {2, 1, 1}", "Verdadero"], ["{1, 2} ≠ {2, 1}", "Falso"],
            ]) {
                valor(w, "expresion", expresion);
                w = await post(frame);
                ok(q(w, "[data-respuesta-relacion]")?.textContent === esperado, expresion);
                ok(!q(w, "#procedimiento").open, "Procedimiento cerrado");
                ok(w.document.activeElement === q(w, "#resultado"), "Foco en resultado");
            }
        }],
        ["Guiado genera texto editable y calcula con el parser", async (w, frame) => {
            q(w, "#relacion-guiada summary").click();
            valor(w, "izquierdo", "{2}"); valor(w, "derecho", "B");
            q(w, '[name="operador"]').value = "⊆";
            q(w, "[data-construir]").click();
            ok(q(w, '[name="expresion"]').value === "{2} ⊆ B", "Texto generado");
            ok(!q(w, "#resultado"), "Construir no calcula");
            w = await post(frame);
            ok(q(w, "[data-respuesta-relacion]").textContent === "Verdadero", "Parser compartido");
        }],
        ["Teclado contextual inserta operadores, llaves y nombres", async w => {
            const campo = q(w, '[name="expresion"]');
            valor(w, "expresion", ""); campo.focus();
            await new Promise(resolve => w.requestAnimationFrame(resolve));
            for (const texto of ["A", "∈", "B"]) q(w, `[data-insercion="${texto}"]`).click();
            ok(campo.value === "A∈B", "Inserción del teclado");
            q(w, '[name="contenido_0"]').focus();
            await new Promise(resolve => w.requestAnimationFrame(resolve));
            ok(!q(w, '[data-insercion="⊆"]'), "El perfil de literal no ofrece inclusión");
            ok(q(w, '[data-insercion="{}"]'), "Ofrece conjuntos anidados");
        }],
        ["CRUD conserva contenidos y renombra referencias completas", async (w, frame) => {
            valor(w, "nombre_0", "Conjunto1");
            w = await post(frame, '[value="guardar"]');
            ok(q(w, '[name="expresion"]').value === "Conjunto1 ∈ B", "Renombrado");
            ok(q(w, '[name="contenido_0"]').value === "{1, 2}", "Conserva contenido");
            valor(w, "definicion", 'S = {"A", {1}, 1, 1}');
            w = await post(frame, '[value="agregar"]');
            ok(q(w, '[name="nombre_2"]').value === "S", "Creación");
            valor(w, "contenido_2", "∅");
            valor(w, "expresion", "S ⊆ B");
            w = await post(frame);
            ok(q(w, "[data-respuesta-relacion]").textContent === "Verdadero", "Edición");
            w = await post(frame, '[name="eliminar"][value="1"]');
            ok(q(w, '[name="nombre_1"]').value === "S" && !q(w, '[name="nombre_2"]'), "Eliminación intermedia");
        }],
        ["Errores accesibles conservan la entrada", async (w, frame) => {
            valor(w, "contenido_0", "{1,}");
            w = await post(frame);
            const campo = q(w, '[name="contenido_0"]');
            ok(!q(w, "#resultado"), "Sin resultado inválido");
            ok(campo.value === "{1,}" && campo.getAttribute("aria-invalid") === "true", "Dato y error");
            ok(w.document.activeElement === campo, "Foco en el error");
        }],
        ["Una edición invalida el resultado y mantiene un único veredicto", async (w, frame) => {
            w = await post(frame);
            valor(w, "expresion", "∅ ∈ A");
            ok(q(w, "#resultado").dataset.resultado === "desactualizado", "Aviso de resultado anterior");
            w = await post(frame);
            ok(q(w, "[data-respuesta-relacion]").textContent === "Falso", "Resultado actualizado");
            ok(w.document.querySelectorAll(".panel-final").length === 1, "Un resultado");
        }],
    ];
    let aprobados = 0;
    for (const [nombre, prueba] of casos) {
        const item = document.createElement("li");
        document.getElementById("resultados").append(item);
        const frame = document.createElement("iframe");
        frame.title = nombre; frame.style.cssText = "width:100%;height:650px";
        document.body.append(frame);
        try {
            await new Promise((resolve, reject) => {
                const timer = setTimeout(() => reject(new Error("Timeout GET")), 15000);
                frame.onload = () => {
                    if (frame.contentWindow.location.pathname !== '/conjuntos/relaciones/') return;
                    clearTimeout(timer); resolve();
                };
                frame.src = "/conjuntos/relaciones/";
            });
            await prueba(frame.contentWindow, frame);
            item.textContent = `OK: ${nombre}`; aprobados++;
        } catch (error) { item.textContent = `FALLO: ${nombre}: ${error.message}`; }
        frame.remove();
    }
    document.getElementById("total").textContent = `${aprobados}/${casos.length} aprobados`;
})();
