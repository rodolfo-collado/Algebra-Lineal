/* Usa formularios Django y scripts de producción, sin un evaluador de pruebas en JS. */
(async () => {
    "use strict";
    const q = (w, selector) => w.document.querySelector(selector);
    const qa = (w, selector) => [...w.document.querySelectorAll(selector)];
    const ok = (condicion, mensaje) => { if (!condicion) throw new Error(mensaje); };
    const errores = w => qa(w, ".field-error, [role=alert]").map(e => e.textContent.trim()).join("; ");
    const valor = (w, nombre, texto) => {
        const campo = q(w, `[name="${nombre}"]`);
        campo.value = texto;
        campo.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const cargar = (frame, ruta) => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout GET")), 15000);
        frame.onload = () => { clearTimeout(timer); resolve(frame.contentWindow); };
        frame.src = ruta;
    });
    const post = (frame, selector = '[data-calculo]') => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 15000);
        frame.onload = () => { clearTimeout(timer); resolve(frame.contentWindow); };
        q(frame.contentWindow, selector).click();
    });
    const cuadro = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    // Coordenadas de pantalla de un punto del viewBox del diagrama (geometría, no matemáticas).
    const enPantalla = (svg, x, y) => {
        const p = svg.createSVGPoint();
        p.x = x; p.y = y;
        return p.matrixTransform(svg.getScreenCTM());
    };
    const casos = [
        ["El editor empieza vacío y ofrece ejemplos opcionales", async (w, frame) => {
            w = await cargar(frame, "/conjuntos/relaciones/");
            ok(q(w, '[name="cantidad"]').value === "0" && !q(w, '[name="nombre_0"]'), "Sin conjuntos precargados");
            ok(!q(w, "#guia-conjuntos") && q(w, "#conjuntos-operacion"), "Operaciones compactas");
            q(w, "[data-edicion-abrir]").click();
            ok(q(w, "[data-edicion-menu]").hidden === false, "Edición accesible por botón");
            const enlace = qa(w, "[data-edicion-menu] a").find(a => a.textContent.includes("Venn"));
            w = await cargar(frame, enlace.href);
            ok(q(w, '[name="nombre_3"]').value === "C" && q(w, '[name="venn_universo"]').value === "U", "Ejemplo cargado");
            ok(!q(w, ".conjuntos-ejemplo-lista"), "Sin bloque de ejemplos");
            ok(qa(w, "[data-lectura]").length === 4 && q(w, "[data-lectura]").textContent.includes("10 elementos"), "Lectura de cada conjunto");
        }],
        ["Editar marca la lectura pendiente y muestra Guardar cambios", async (w, frame) => {
            const guardar = q(w, "[data-guardar]");
            ok(!guardar.getClientRects().length, "Guardar oculto sin cambios");
            valor(w, "contenido_0", "{1, 2, 3}");
            ok(guardar.getClientRects().length && q(w, "[data-lectura]").hasAttribute("data-desactualizada"), "Cambios pendientes visibles");
            w = await post(frame, "[data-guardar]");
            ok(q(w, "[data-lectura]").textContent.includes("3 elementos") && q(w, "[data-guardar]").hidden, "Guardado sin calcular");
            ok(!q(w, "#resultado"), "Guardar no calcula");
        }],
        ["Intro en Nuevo conjunto lo añade; en la expresión, calcula", async (w, frame) => {
            valor(w, "definicion", "S = {1, {1}, {{1}}}");
            const cargado = new Promise(resolve => { frame.onload = () => resolve(frame.contentWindow); });
            q(w, '[name="definicion"]').dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }));
            w = await cargado;
            ok(q(w, '[name="nombre_2"]').value === "S" && q(w, '[name="definicion"]').value === "", "Añadido por Intro: " + errores(w));
            ok(qa(w, "[data-lectura]").at(-1).textContent.includes("3 elementos"), "Anidados como elementos completos");
            ok(q(w, "#conjuntos-form button[type=submit]").classList.contains("conjuntos-envio-implicito"), "El primer botón calcula, no elimina");
        }],
        ["La guía escribe operaciones con los nombres definidos", async (w, frame) => {
            const inclusion = q(w, 'option[data-plantilla="{a} ⊆ {b}"]');
            ok(inclusion.textContent.includes("A ⊆ B"), "Plantilla con nombres reales");
            valor(w, "nombre_0", "P");
            ok(q(w, '[data-plantilla="{a} ∪ {b}"]').textContent.includes("P ∪ B"), "Sigue los cambios de nombre");
            valor(w, "nombre_0", "A");
            valor(w, "expresion", "antes A ∈ B después");
            q(w, '[name="expresion"]').setSelectionRange(6, 11);
            q(w, '#conjuntos-operacion').value = inclusion.value;
            q(w, '[data-insertar-operacion]').click();
            ok(q(w, '[name="expresion"]').value === "antes A ⊆ B después", "Sustituye solo la selección");
            q(w, '[name="expresion"]').select();
            q(w, '[data-insertar-operacion]').click();
            ok(q(w, '[name="expresion"]').value === "A ⊆ B" && w.document.activeElement === q(w, '[name="expresion"]'), "Texto generado y foco");
            ok(!q(w, "#resultado"), "Escribir no calcula");
            w = await post(frame);
            ok(q(w, "[data-respuesta-relacion]").textContent === "Falso", "Parser compartido");
            ok(q(w, ".conjuntos-motivo").textContent.includes("está en A pero no en B"), "Motivo desde los hechos del motor");
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
                ok(q(w, "[data-respuesta-relacion]")?.textContent === esperado, expresion + ": " + errores(w));
                const datos = JSON.parse(q(w, "#conjuntos-resultado-datos").textContent);
                ok(datos.valor.tipo === tipo, "Tipo de resultado explícito");
                ok(datos.procedimiento.length > 0 && qa(w, ".conjuntos-paso").length === datos.procedimiento.length, "Un paso por evidencia");
                ok(!q(w, "#procedimiento").open, "Procedimiento cerrado");
                ok(w.document.activeElement === q(w, "#resultado"), "Foco en resultado P2");
            }
        }],
        ["P2 inserta símbolos y rechaza complementos fuera del universo", async (w, frame) => {
            const campo = q(w, '[name="expresion"]');
            valor(w, "expresion", ""); campo.focus();
            await cuadro();
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
        ["P3 y P4: potencia, pares y recta interactiva exacta", async (w, frame) => {
            valor(w, "expresion", "potencia(A)"); w = await post(frame);
            ok(q(w, ".conjuntos-tamanos"), "Subconjuntos agrupados por tamaño: " + errores(w));
            valor(w, "expresion", "intervalo(0, 2, cerrado, cerrado) ∖ intervalo(1, 1, cerrado, cerrado)"); w = await post(frame);
            ok(q(w, "[data-respuesta-relacion]").textContent === "[0, 1) ∪ (1, 2]", "Notación de intervalos");
            const svg = q(w, "[data-recta] svg");
            ok(svg && qa(w, ".recta-fila").length === 3 && qa(w, ".recta-fila.es-resultado .recta-tramo").length === 2, "Operandos y resultado alineados");
            const vista = svg.getAttribute("viewBox"), antes = q(w, ".recta-fila.es-resultado .recta-tramo").getAttribute("x1");
            q(w, '[aria-label="Acercar"]').click();
            ok(q(w, ".recta-fila.es-resultado .recta-tramo").getAttribute("x1") !== antes && svg.getAttribute("viewBox") === vista, "Zoom");
            const tramo = qa(w, ".recta-tramos button")[1];
            tramo.click();
            ok(tramo.getAttribute("aria-pressed") === "true" && q(w, ".recta-tramo-grupo.es-activo"), "Tramo resaltado");
            q(w, ".recta-controles button:last-child").click();
            const caja = svg.getBoundingClientRect();
            for (const tipo of ["pointerdown", "pointerup"]) svg.dispatchEvent(new w.PointerEvent(tipo, { clientX: caja.left + caja.width / 2, clientY: caja.top + 40, bubbles: true, pointerId: 1 }));
            ok(q(w, '[name="punto"]').value !== "" && q(w, "[data-recta] [role=status]").textContent.includes("Comprobar"), "Pulsar propone un punto");
            valor(w, "punto", "1");
            w = await post(frame, "[data-consultar]");
            ok(q(w, "[data-consulta-punto]")?.textContent.includes("no pertenece"), "Consulta exacta: " + errores(w));
            ok(q(w, ".recta-punto"), "Punto dibujado");
            valor(w, "punto", "uno");
            w = await post(frame, "[data-consultar]");
            ok(q(w, "#resultado") && q(w, '[name="punto"]').getAttribute("aria-invalid") === "true", "Error junto al punto, con resultado");
        }],
        ["P5: Venn automático, regiones y selección desde el motor", async (w, frame) => {
            valor(w, "expresion", "A ∖ B"); w = await post(frame);
            ok(qa(w, "[data-region]").length === 4, "Cuatro regiones sin pedir nombres");
            const datos = JSON.parse(q(w, "#conjuntos-resultado-datos").textContent);
            ok(datos.venn.regiones[1].seleccionada && !datos.venn.regiones[3].seleccionada, "Solo A resaltada");
            ok(q(w, '[data-region="1"]').classList.contains("es-seleccionada"), "Sombreado del motor");
            const fila = q(w, '[data-regiones] tr[data-mascara="3"]');
            fila.focus(); fila.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
            const estado = q(w, "[data-venn] [role=status]");
            ok(fila.classList.contains("es-activa") && estado.textContent.includes("En A y B") && estado.textContent.includes("1 elemento: 2."), "Fila por teclado: " + estado.textContent);
            const svg = q(w, "[data-venn] svg");
            const p = enPantalla(svg, 88, 120);
            svg.dispatchEvent(new w.MouseEvent("click", { clientX: p.x, clientY: p.y, bubbles: true }));
            ok(estado.textContent.startsWith("Solo en A") && q(w, '[data-region="1"]').classList.contains("es-activa"), "Clic en la región");
        }],
        ["P6: cardinalidades editables y validación de coherencia", async (w, frame) => {
            w = await cargar(frame, "/conjuntos/cardinalidad/");
            ok(qa(w, ".cardinalidad-icono svg").length === 4 && !q(w, "[data-ajuste-cardinalidades]").getClientRects().length, "Iconos de región y ajuste automático");
            valor(w, "region_1", "5"); valor(w, "region_2", "3"); valor(w, "region_3", "2");
            w = await post(frame); ok(q(w, "[data-cardinalidad]").textContent === "10", "Suma exclusiva");
            const sumando = q(w, ".cardinalidad-sumandos li");
            sumando.dispatchEvent(new w.FocusEvent("focusin", { bubbles: true }));
            ok(q(w, '[data-region="1"]').classList.contains("es-activa"), "El sumando ilumina su región");
            valor(w, "region_1", "7"); ok(q(w, "#resultado").dataset.resultado === "desactualizado", "Cambio invalida el resultado P6");
            w = await post(frame); ok(q(w, "[data-cardinalidad]").textContent === "12", "Recalcula");
            valor(w, "universo", "1"); w = await post(frame); ok(!q(w, "[data-cardinalidad]"), "Rechaza universo menor");
            const tres = q(w, '[name="numero"][value="3"]');
            const recarga = new Promise(resolve => { frame.onload = () => resolve(frame.contentWindow); });
            tres.click();
            w = await recarga;
            ok(q(w, '[name="region_7"]') && qa(w, ".cardinalidad-icono svg").length === 8, "Cambiar a tres conjuntos recompone los campos");
            q(w, '[data-expresion="A ∩ B ∩ C"]').click();
            ok(q(w, '[name="expresion"]').value === "A ∩ B ∩ C", "Atajo escribe la expresión");
        }],
        ["Regiones manuales generan conjuntos y el Venn vuelve a leerlos", async (w, frame) => {
            valor(w, "venn_nombres", "A, B, C"); valor(w, "venn_universo", "U");
            w = await post(frame, '[value="editar_regiones"]');
            ok(qa(w, '[data-regiones-editor] textarea').length === 8 && qa(w, '[data-regiones-editor] svg').length === 8, "Ocho regiones con sus iconos");
            for (let m = 0; m < 8; m++) valor(w, `venn_region_${m}`, m === 7 ? '{1/2, "común"}' : m === 0 ? '{9}' : '∅');
            w = await post(frame, '.btn[value="aplicar_regiones"]');
            ok(!q(w, '[data-regiones-editor]') && !q(w, '#resultado'), "Aplicar escribe definiciones sin calcular");
            valor(w, "expresion", "A ∩ B ∩ C"); w = await post(frame);
            const datos = JSON.parse(q(w, '#conjuntos-resultado-datos').textContent);
            ok(datos.venn.regiones[7].etiquetas.join('|') === '1/2|"común"' && datos.venn.regiones[0].etiquetas[0] === '9', "Intersección y exterior desde el modelo");
            w = await post(frame, '[value="editar_regiones"]');
            ok(q(w, '[name="venn_region_7"]').value === '{1/2, "común"}', "Reabrir lee los conjuntos aplicados");
        }],
        ["Regiones rechazan duplicados sin perder el borrador", async (w, frame) => {
            w = await post(frame, '[value="editar_regiones"]');
            valor(w, "venn_region_1", "{1/2}"); valor(w, "venn_region_2", "{0.5}");
            w = await post(frame, '.btn[value="aplicar_regiones"]');
            ok(errores(w).includes("regiones distintas") && q(w, '[name="venn_region_2"]').value === "{0.5}", "Error conserva entradas");
            w = await post(frame, '[value="guardar"]');
            ok(!q(w, '[data-regiones-editor]') && q(w, '[name="contenido_0"]').value === '{1, 2}', "Cancelar conserva conjuntos originales");
        }],
        ["Relleno de regiones aleatorio es disjunto y pasa por Aplicar", async (w, frame) => {
            w = await post(frame, '[value="editar_regiones"]');
            w = await post(frame, '[value="azar_regiones"]');
            const textos = qa(w, '[data-regiones-editor] textarea').map(c => c.value);
            const valores = textos.flatMap(t => t.slice(1, -1).split(',').map(Number));
            ok(new Set(valores).size === valores.length && !q(w, '#resultado'), "Regiones disjuntas pendientes de aplicar");
            w = await post(frame, '.btn[value="aplicar_regiones"]');
            ok(w.document.body.textContent.includes('Regiones aplicadas a los conjuntos'), "Aplicación confirmada");
            w = await post(frame);
            const distribucion = JSON.parse(q(w, '#conjuntos-resultado-datos').textContent).venn;
            ok(!distribucion.resalta && q(w, '[name="expresion"]').value === 'A ∈ B', "Relación conservada y distribución sin sombreado");
            valor(w, "expresion", "A ∪ B"); w = await post(frame);
            ok(q(w, '[data-respuesta-relacion]').textContent !== '∅', "Calcula desde las definiciones generadas");
        }],
        ["Teclado contextual inserta operadores, llaves y nombres", async w => {
            const campo = q(w, '[name="expresion"]');
            valor(w, "expresion", ""); campo.focus();
            await cuadro();
            for (const texto of ["A", "∈", "B"]) q(w, `[data-insercion="${texto}"]`).click();
            ok(campo.value === "A∈B", "Inserción del teclado");
            q(w, '[name="contenido_0"]').focus();
            await cuadro();
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
            const w = await cargar(frame, "/conjuntos/relaciones/?ejemplo=relaciones");
            await prueba(w, frame);
            item.textContent = `OK: ${nombre}`; aprobados++;
        } catch (error) { item.textContent = `FALLO: ${nombre}: ${error.message}`; }
        frame.remove();
    }
    document.getElementById("total").textContent = `${aprobados}/${casos.length} aprobados`;
})();
