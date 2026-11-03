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
                frame.onload = () => { clearTimeout(timer); resolve(); };
                frame.src = "/conjuntos/relaciones/";
            });
            await prueba(frame.contentWindow, frame);
            item.textContent = `OK: ${nombre}`; aprobados++;
        } catch (error) { item.textContent = `FALLO: ${nombre}: ${error.message}`; }
        frame.remove();
    }
    document.getElementById("total").textContent = `${aprobados}/${casos.length} aprobados`;
})();
