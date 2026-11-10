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
    // Espera la recarga que provoca una acción (clic, Intro, cambio de opción).
    const recarga = (frame, accion) => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 15000);
        frame.onload = () => { clearTimeout(timer); resolve(frame.contentWindow); };
        accion();
    });
    const post = (frame, selector = '[data-calculo]') => recarga(frame, () => q(frame.contentWindow, selector).click());
    const cuadro = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    // Coordenadas de pantalla de un punto del viewBox del diagrama (geometría, no matemáticas).
    const enPantalla = (svg, x, y) => {
        const p = svg.createSVGPoint();
        p.x = x; p.y = y;
        return p.matrixTransform(svg.getScreenCTM());
    };
    const filas = w => qa(w, "[data-conjunto]").map(fila =>
        `${fila.querySelector('[data-campo="nombre"]').value} = ${fila.querySelector("textarea").value}`);
    const tarjeta = (w, clave) => q(w, `[name="tarjeta"][value="${clave}"]`)?.closest(".tarjeta");
    const tecla = (w, simbolo) => q(w, `[data-barra] [data-insercion="${simbolo}"]`);
    const casos = [
        ["El editor empieza vacío: diagrama en blanco, ejemplos en el menú", async (w, frame) => {
            w = await cargar(frame, "/conjuntos/relaciones/");
            ok(q(w, '[name="cantidad"]').value === "0" && !q(w, '[name="nombre_0"]'), "Sin conjuntos precargados");
            ok(!q(w, "[data-barra]").hidden && !q(w, "#conjuntos-operacion"), "Barra de símbolos en lugar del selector");
            ok(qa(w, ".venn-editor-lienzo textarea").length === 4 && !q(w, ".tarjetas"), "Diagrama de A y B listo para escribir, sin tarjetas");
            ok(q(w, '[name="venn_region_0"]').placeholder === "?" && q(w, '[name="venn_region_3"]').placeholder === "∅", "El exterior aún es desconocido");
            ok(!q(w, "[data-aplicar-regiones]").getClientRects().length, "Nada pendiente al empezar");
            q(w, "[data-edicion-abrir]").click();
            ok(q(w, "[data-edicion-menu]").hidden === false, "Edición accesible por botón");
            const enlace = qa(w, "[data-edicion-menu] a").find(a => a.textContent.includes("Venn"));
            w = await cargar(frame, enlace.href);
            ok(q(w, '[name="nombre_3"]').value === "C" && q(w, '[name="venn_universo"]').value === "U", "Ejemplo cargado");
            ok(!q(w, ".conjuntos-ejemplo-lista"), "Sin bloque de ejemplos");
            ok(qa(w, "[data-lectura]").length === 4 && q(w, "[data-lectura]").textContent.includes("10 elementos"), "Lectura de cada conjunto");
            ok(qa(w, ".venn-editor-lienzo textarea").length === 8 && q(w, '[name="venn_region_7"]').value === "5", "El diagrama lee las ocho regiones del modelo");
        }],
        ["Editar un conjunto marca lo pendiente; guardar actualiza diagrama y tarjetas", async (w, frame) => {
            const guardar = q(w, "[data-guardar]");
            ok(!guardar.getClientRects().length, "Guardar oculto sin cambios");
            valor(w, "contenido_0", "{1, 2, 3}");
            ok(guardar.getClientRects().length && q(w, "[data-lectura]").hasAttribute("data-desactualizada"), "Cambios pendientes visibles");
            ok(q(w, "[data-venn-editor]").hasAttribute("data-desactualizado") && q(w, "[data-panorama-aviso]").textContent.includes("Guardar cambios"), "Diagrama y tarjetas avisan de que esperan");
            w = await post(frame, "[data-guardar]");
            ok(q(w, "[data-lectura]").textContent.includes("3 elementos") && q(w, "[data-guardar]").hidden, "Guardado sin calcular");
            ok(q(w, '[name="venn_region_1"]').value === "1, 3" && tarjeta(w, "diferencia_0").querySelector(".tarjeta-valor").textContent === "{1, 3}", "Conjuntos → diagrama → tarjetas");
            ok(!q(w, "#resultado"), "Guardar no calcula");
        }],
        ["Intro en Nuevo conjunto lo añade; el primer botón calcula", async (w, frame) => {
            valor(w, "definicion", "S = {1, {1}, {{1}}}");
            w = await recarga(frame, () => q(w, '[name="definicion"]').dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true })));
            ok(q(w, '[name="nombre_2"]').value === "S" && q(w, '[name="definicion"]').value === "", "Añadido por Intro: " + errores(w));
            ok(qa(w, "[data-lectura]").at(-1).textContent.includes("3 elementos"), "Anidados como elementos completos");
            ok(q(w, "#conjuntos-form button[type=submit]").classList.contains("conjuntos-envio-implicito"), "El primer botón calcula, no elimina");
        }],
        ["La barra inserta símbolos y nombres en el cursor, sin calcular", async (w, frame) => {
            const campo = q(w, '[name="expresion"]');
            const nombres = () => qa(w, "[data-barra-nombres] button").map(b => b.textContent).join(",");
            ok(nombres() === "A,B", "Los conjuntos definidos son teclas");
            valor(w, "nombre_0", "P");
            ok(nombres() === "P,B", "Sigue los cambios de nombre");
            valor(w, "nombre_0", "A");
            valor(w, "expresion", "antes A ∈ B después");
            campo.focus(); campo.setSelectionRange(8, 9);
            tecla(w, "⊆").click();
            ok(campo.value === "antes A ⊆ B después", "Sustituye solo la selección: " + campo.value);
            campo.select();
            // Con el puntero (detail 1), el cursor se queda en la expresión.
            for (const simbolo of ["A", "⊆", "B"]) tecla(w, simbolo).dispatchEvent(new w.MouseEvent("click", { bubbles: true, detail: 1 }));
            ok(campo.value === "A⊆B" && w.document.activeElement === campo, "Texto generado y foco en la expresión: " + campo.value);
            campo.select();
            tecla(w, "∁(, )").click();
            ok(campo.value === "∁(, )" && campo.selectionStart === 2, "Cursor dentro del complemento");
            for (const simbolo of ["∪", "∩", "∖", "||", "()", "×", "potencia()", "∈", "∉", "⊂", "=", "≠", "∅", "{}"]) ok(tecla(w, simbolo), simbolo);
            // Un único alto de tabulación; las flechas recorren las teclas y Intro inserta sin perder la tecla.
            const teclas = qa(w, "[data-barra] button");
            ok(teclas.filter(b => b.tabIndex === 0).length === 1 && teclas[0].tabIndex === 0, "Una sola tecla en el orden de tabulación");
            teclas[0].focus();
            teclas[0].dispatchEvent(new w.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true, cancelable: true }));
            ok(w.document.activeElement === teclas[1] && teclas[1].tabIndex === 0 && teclas[0].tabIndex === -1, "Flecha derecha");
            teclas[1].dispatchEvent(new w.KeyboardEvent("keydown", { key: "End", bubbles: true, cancelable: true }));
            ok(w.document.activeElement === teclas.at(-1), "Fin");
            valor(w, "expresion", "");
            tecla(w, "∅").click();   // click() sin puntero equivale a activarla con el teclado
            ok(campo.value === "∅" && w.document.activeElement === tecla(w, "∅"), "Con teclado, el foco sigue en la tecla");
            ok(!q(w, "#resultado") && !q(w, ".math-keyboard").hasAttribute("data-abierto"), "Ni calcula ni abre el dock");
            valor(w, "expresion", "A ⊆ B");
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
        ["Un complemento fuera del universo se explica y conserva diagrama y tarjetas", async (w, frame) => {
            valor(w, "expresion", "∁(A,B)");
            w = await post(frame);
            ok(!q(w, "#resultado"), "Sin complemento inválido");
            ok(q(w, '[name="expresion"]').getAttribute("aria-invalid") === "true", "Error P2 accesible");
            ok(w.document.body.textContent.includes("universo explícito"), "Explica el universo");
            ok(q(w, ".tarjetas") && q(w, '[name="venn_region_3"]').value === "2", "El error de la expresión no borra lo demás");
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
            w = await cargar(frame, "/conjuntos/relaciones/?ejemplo=intervalos");
            ok(!q(w, "[data-venn-editor]") && !q(w, ".tarjetas") && q(w, ".conjuntos-diagrama").textContent.includes("recta real"), "Con intervalos no hay diagrama ni tarjetas, y se dice por qué");
        }],
        ["P5: el resultado sombrea su propio Venn desde el motor", async (w, frame) => {
            valor(w, "expresion", "A ∖ B"); w = await post(frame);
            ok(qa(w, "[data-venn] [data-region]").length === 4, "Cuatro regiones sin pedir nombres");
            const datos = JSON.parse(q(w, "#conjuntos-resultado-datos").textContent);
            ok(datos.venn.regiones[1].seleccionada && !datos.venn.regiones[3].seleccionada, "Solo A resaltada");
            ok(q(w, '[data-venn] [data-region="1"]').classList.contains("es-seleccionada"), "Sombreado del motor");
            ok(!q(w, ".venn-editor-lienzo .es-seleccionada"), "El diagrama editable no se sombrea");
            const fila = q(w, '[data-regiones] tr[data-mascara="3"]');
            fila.focus(); fila.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
            const estado = q(w, "[data-venn] [role=status]");
            ok(fila.classList.contains("es-activa") && estado.textContent.includes("En A y B") && estado.textContent.includes("1 elemento: 2."), "Fila por teclado: " + estado.textContent);
            const svg = q(w, "[data-venn] svg");
            const p = enPantalla(svg, 88, 120);
            svg.dispatchEvent(new w.MouseEvent("click", { clientX: p.x, clientY: p.y, bubbles: true }));
            ok(estado.textContent.startsWith("Solo en A") && q(w, '[data-venn] [data-region="1"]').classList.contains("es-activa"), "Clic en la región");
        }],
        ["Escribir en las regiones crea los conjuntos; el exterior crea el universo", async (w, frame) => {
            w = await cargar(frame, "/conjuntos/relaciones/");
            valor(w, "venn_region_1", "1, 2"); valor(w, "venn_region_3", "3");
            ok(q(w, '[name="venn_fuente"]').value === "regiones" && q(w, "[data-aplicar-regiones]").getClientRects().length && q(w, "[data-descartar-regiones]").getClientRects().length, "El diagrama queda pendiente de aplicar");
            w = await recarga(frame, () => q(w, '[name="venn_region_3"]').dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true })));
            ok(filas(w).join("; ") === "A = {1, 2, 3}; B = {3}", "Intro aplica; sin exterior no se inventa U: " + filas(w).join("; ") + errores(w));
            ok(q(w, "#conjuntos-form [role=status]").textContent.includes("Conjuntos actualizados") && !q(w, "#resultado"), "Aplicar no calcula");
            ok(q(w, '[name="venn_region_1"]').value === "1, 2" && q(w, '[name="expresion"]').value === "A ∪ B", "Regiones normalizadas y unión propuesta");
            ok(tarjeta(w, "simetrica").querySelector(".tarjeta-valor").textContent === "{1, 2}" && !tarjeta(w, "complemento_0"), "Tarjetas sin complementos mientras no hay universo");
            ok(q(w, ".tarjeta-hechos").textContent.includes("B ⊂ A"), "Relación leída de las regiones");
            valor(w, "venn_region_0", '9, "z"');
            w = await post(frame, "[data-aplicar-regiones]");
            ok(filas(w).at(-1) === 'U = {1, 2, 3, 9, "z"}', "El exterior define el universo: " + filas(w).at(-1));
            ok(tarjeta(w, "complemento_union").querySelector(".tarjeta-valor").textContent === '{9, "z"}', "Complementos con universo");
            valor(w, "venn_region_2", "{3}");
            w = await post(frame, "[data-aplicar-regiones]");
            ok(errores(w).includes("regiones distintas") && q(w, '[name="venn_region_2"]').value === "{3}", "Un elemento en dos regiones se rechaza y el borrador se conserva");
            ok(q(w, '[name="venn_region_2"]').getAttribute("aria-invalid") !== "true" && q(w, ".alert.error"), "Incoherencia entre regiones: aviso general");
            w = await post(frame, "[data-descartar-regiones]");
            ok(!errores(w) && q(w, '[name="venn_region_2"]').value === "" && filas(w)[1] === "B = {3}", "Descartar vuelve al modelo");
        }],
        ["El último lado editado manda, también al calcular", async (w, frame) => {
            valor(w, "venn_region_1", "1, 7");
            valor(w, "expresion", "A");
            w = await post(frame);
            ok(q(w, "[data-respuesta-relacion]").textContent === "{1, 2, 7}" && filas(w)[0] === "A = {1, 2, 7}", "Calcular aplica antes el diagrama editado: " + errores(w));
            valor(w, "venn_region_1", "{99}");
            valor(w, "contenido_0", "{1, 2}");
            ok(q(w, '[name="venn_fuente"]').value === "" && !q(w, "[data-aplicar-regiones]").getClientRects().length && q(w, "[data-guardar]").getClientRects().length, "Editar después un conjunto le devuelve el mando");
            w = await post(frame);
            ok(q(w, "[data-respuesta-relacion]").textContent === "{1, 2}" && q(w, '[name="venn_region_1"]').value === "1", "Mandan los conjuntos y el diagrama los vuelve a leer");
        }],
        ["Tres conjuntos, opciones del diagrama y relleno al azar", async (w, frame) => {
            valor(w, "venn_nombres", "A, B, C"); valor(w, "venn_universo", "U");
            w = await post(frame, '[value="editar_regiones"]');
            ok(qa(w, ".venn-editor-lienzo textarea").length === 8 && !q(w, "#resultado"), "Ocho regiones dentro del diagrama: " + errores(w));
            for (let m = 0; m < 8; m++) valor(w, `venn_region_${m}`, m === 7 ? '1/2, "común"' : m === 0 ? "{9}" : "");
            w = await post(frame, "[data-aplicar-regiones]");
            ok(filas(w).includes('C = {1/2, "común"}') && filas(w).includes('U = {1/2, 9, "común"}'), "Conjuntos nuevos desde las regiones: " + filas(w).join("; "));
            valor(w, "expresion", "A ∩ B ∩ C"); w = await post(frame);
            const datos = JSON.parse(q(w, "#conjuntos-resultado-datos").textContent);
            ok(datos.venn.regiones[7].etiquetas.join("|") === '1/2|"común"' && datos.venn.regiones[0].etiquetas[0] === "9", "Intersección y exterior desde el modelo");
            ok(q(w, '[name="venn_region_7"]').value === '1/2, "común"', "El diagrama relee los conjuntos aplicados");
            w = await post(frame, '[value="azar_regiones"]');
            const textos = qa(w, ".venn-editor-lienzo textarea").map(c => c.value);
            const valores = textos.flatMap(t => t.split(",").map(Number));
            ok(valores.length === 16 && new Set(valores).size === 16 && !q(w, "#resultado"), "Regiones al azar, disjuntas y sin aplicar");
            ok(q(w, "[data-aplicar-regiones]").getClientRects().length && filas(w).includes('C = {1/2, "común"}'), "Quedan pendientes: los conjuntos no cambian todavía");
            w = await post(frame, "[data-aplicar-regiones]");
            ok(w.document.body.textContent.includes("Conjuntos actualizados") && !filas(w).includes('C = {1/2, "común"}'), "Aplicación confirmada");
            valor(w, "expresion", "A ∈ B"); w = await post(frame);
            const distribucion = JSON.parse(q(w, "#conjuntos-resultado-datos").textContent).venn;
            ok(distribucion && !distribucion.resalta, "Una relación muestra la distribución pedida, sin sombreado");
            valor(w, "venn_nombres", "A, A");
            w = await post(frame, '[value="editar_regiones"]');
            ok(q(w, '[name="venn_nombres"]').getAttribute("aria-invalid") === "true" && q(w, "#opciones-venn").open, "Opciones inválidas: error junto al campo, con el plegable abierto");
        }],
        ["Tarjetas: valores del modelo, copiar, desplegar y ver pasos", async (w, frame) => {
            w = await cargar(frame, "/conjuntos/relaciones/?ejemplo=venn");
            ok(qa(w, ".tarjeta").length === 15, "Doce operaciones y tres propiedades: " + qa(w, ".tarjeta").length);
            const union = tarjeta(w, "union");
            ok(union.querySelector(".tarjeta-notacion").textContent === "A ∪ B ∪ C" && union.querySelector(".tarjeta-valor").textContent === "{1, 2, 3, 4, 5, 6, 7, 9}" && union.textContent.includes("8 elementos"), "Unión con cardinalidad");
            ok(tarjeta(w, "solo_0").querySelector(".tarjeta-valor").textContent === "{1, 3}" && tarjeta(w, "complemento_union").querySelector(".tarjeta-valor").textContent === "{8, 10}", "Zonas exclusivas y exterior");
            ok(q(w, ".tarjeta-datos").textContent.replace(/\s+/g, "").includes("|A|5|B|4|C|4|U|10") &&q(w, ".tarjeta-ancha .tarjeta-valor").textContent === "8 = 5 + 4 + 4 − 2 − 2 − 2 + 1", "Cardinalidades e inclusión-exclusión");
            const centro = tarjeta(w, "interseccion");
            centro.dispatchEvent(new w.MouseEvent("mouseenter"));
            ok(q(w, '.venn-editor-lienzo [data-region="7"]').classList.contains("es-activa") && qa(w, ".venn-editor-lienzo .es-activa").length === 1, "La tarjeta ilumina su región en el diagrama");
            centro.dispatchEvent(new w.MouseEvent("mouseleave"));
            ok(!q(w, ".venn-editor-lienzo .es-activa"), "Y la apaga al salir");
            let copiado = null;
            Object.defineProperty(w.navigator, "clipboard", { configurable: true, value: { writeText: async texto => { copiado = texto; } } });
            const boton = union.querySelector("[data-copiar]");
            ok(boton.getClientRects().length, "Copiar visible con JavaScript");
            boton.click();
            await cuadro();
            ok(copiado === "{1, 2, 3, 4, 5, 6, 7, 9}" && boton.textContent.startsWith("Copiado"), "Copia el resultado y lo confirma: " + copiado);
            valor(w, "definicion", "D = {" + Array.from({ length: 20 }, (_, i) => i + 20).join(", ") + "}");
            w = await post(frame, "[data-agregar]");
            valor(w, "venn_nombres", "A, D"); valor(w, "venn_universo", "");
            w = await post(frame, '[value="editar_regiones"]');
            ok(!q(w, '[name="venn_region_0"]'), "Un U que no contiene a D no es su universo: sin exterior");
            const larga = tarjeta(w, "union"), mas = larga.querySelector("details.tarjeta-mas");
            ok(larga.querySelector(".tarjeta-valor").textContent.endsWith("…}") && mas && !mas.open && mas.querySelector("summary").textContent.trim() === "Ver los 25 elementos", "Resultado extenso plegado: " + errores(w));
            ok(larga.querySelector("[data-copiar]").dataset.copiar.endsWith("38, 39}"), "Copiar lleva el resultado completo");
            w = await post(frame, '[name="tarjeta"][value="simetrica"]');
            ok(q(w, '[name="expresion"]').value === "(A ∖ D) ∪ (D ∖ A)" && qa(w, ".conjuntos-paso").length === 3 && w.document.activeElement === q(w, "#resultado"), "Ver pasos calcula la expresión de la tarjeta: " + errores(w));
            ok(q(w, "[data-respuesta-relacion]").textContent.startsWith("{1, 2, 3, 4, 5, 20"), "Con su procedimiento y resultado");
        }],
        ["El diagrama señala cada región y lleva el cursor a su campo", async (w, frame) => {
            const campo = q(w, '[name="venn_region_3"]'), leyenda = q(w, ".venn-editor-leyenda");
            ok(campo.labels[0].textContent === "En A y B" && campo.labels[0].classList.contains("sr-only"), "Cada campo conserva su etiqueta accesible");
            campo.focus();
            ok(q(w, '.venn-editor-lienzo [data-region="3"]').classList.contains("es-activa") && leyenda.textContent === "En A y B", "El foco ilumina la región y la nombra");
            campo.blur();
            ok(!q(w, ".venn-editor-lienzo .es-activa") && leyenda.textContent === "", "Sin foco, nada resaltado");
            const svg = q(w, ".venn-editor-lienzo svg"), lienzo = q(w, ".venn-editor-lienzo");
            const p = enPantalla(svg, 70, 90);
            lienzo.dispatchEvent(new w.MouseEvent("click", { clientX: p.x, clientY: p.y, bubbles: true }));
            ok(w.document.activeElement === q(w, '[name="venn_region_1"]'), "Pulsar la región enfoca su campo");
            const fuera = enPantalla(svg, 300, 120);
            lienzo.dispatchEvent(new w.MouseEvent("click", { clientX: fuera.x, clientY: fuera.y, bubbles: true }));
            ok(w.document.activeElement === q(w, '[name="venn_region_0"]'), "También el exterior");
            await cuadro();
            ok(q(w, ".math-keyboard").hasAttribute("data-abierto") && q(w, '.math-keyboard [data-insercion="{}"]'), "El teclado de elementos acompaña a la región");
            const cantidades = q(w, "a.venn-modo-opcion");
            ok(q(w, ".venn-modo [aria-current]").textContent === "Elementos" && /numero=2&region_1=1&region_2=1&region_3=1$/.test(cantidades.search), "El modo de cantidades recibe solo cuántos hay: " + cantidades.search);
        }],
        ["Cantidades: regiones dentro del diagrama, sin elementos, y tarjetas numéricas", async (w, frame) => {
            w = await cargar(frame, q(w, "a.venn-modo-opcion").href);
            ok(q(w, ".venn-modo [aria-current]").textContent === "Cantidades" && q(w, '[name="region_3"]').value === "1" && q(w, '[name="universo"]').value === "", "Cantidades contadas desde el diagrama de elementos");
            w = await cargar(frame, "/conjuntos/cardinalidad/");
            ok(q(w, ".cardinalidad-campos.es-diagrama") && qa(w, ".venn-editor-lienzo input").length === 4 && !q(w, ".cardinalidad-icono svg"), "Tres regiones y |U| dentro del diagrama");
            ok(!q(w, "[data-ajuste-cardinalidades]").getClientRects().length && q(w, '[name="region_1"]').labels[0].classList.contains("sr-only") && q(w, '[name="universo"]').labels[0].getClientRects().length, "Etiquetas: accesibles en las regiones, visible en |U|");
            valor(w, "region_1", "5"); valor(w, "region_2", "3"); valor(w, "region_3", "2");
            w = await post(frame); ok(q(w, "[data-cardinalidad]").textContent === "10", "Suma exclusiva");
            const sumando = q(w, ".cardinalidad-sumandos li");
            sumando.dispatchEvent(new w.FocusEvent("focusin", { bubbles: true }));
            ok(q(w, '[data-venn] [data-region="1"]').classList.contains("es-activa"), "El sumando ilumina su región");
            const numeros = Object.fromEntries(qa(w, ".tarjeta[data-mascaras]").map(t => [t.querySelector(".tarjeta-notacion").textContent, t.querySelector(".tarjeta-valor").textContent]));
            ok(numeros["|A ∪ B|"] === "10" && numeros["|A ∩ B|"] === "2" && numeros["|A ∖ B|"] === "5" && numeros["|A △ B|"] === "8", "Tarjetas con cantidades: " + JSON.stringify(numeros));
            ok(!q(w, ".tarjeta-cantidad") && !q(w, '[name="tarjeta"]') && !/[{}]/.test(q(w, ".tarjetas").textContent), "Ninguna tarjeta escribe elementos");
            ok(q(w, ".tarjeta-ancha .tarjeta-valor").textContent === "10 = 7 + 5 − 2" && q(w, ".tarjeta-hechos").textContent.includes("Comparten 2 elementos"), "Inclusión-exclusión y relación");
            const centro = qa(w, ".tarjeta[data-mascaras]").find(t => t.dataset.mascaras === "3");
            centro.dispatchEvent(new w.MouseEvent("mouseenter"));
            ok(q(w, '[data-venn] [data-region="3"]').classList.contains("es-activa") && !q(w, ".venn-editor-lienzo .es-activa"), "Las tarjetas del resultado iluminan el diagrama del resultado");
            valor(w, "region_1", "7"); ok(q(w, "#resultado").dataset.resultado === "desactualizado", "Cambio invalida el resultado P6");
            w = await post(frame); ok(q(w, "[data-cardinalidad]").textContent === "12", "Recalcula");
            valor(w, "universo", "1"); w = await post(frame); ok(!q(w, "[data-cardinalidad]") && errores(w).includes("Universo:"), "Rechaza universo menor, nombrando el campo");
            valor(w, "region_2", ""); w = await post(frame);
            ok(errores(w).includes("Solo en B: Indica esta cardinalidad") && q(w, '[name="region_2"]').getAttribute("aria-invalid") === "true", "El error nombra la región: " + errores(w));
            w = await recarga(frame, () => q(w, '[name="numero"][value="3"]').click());
            ok(q(w, '[name="region_7"]') && qa(w, ".venn-editor-lienzo input").length === 8, "Cambiar a tres conjuntos recompone el diagrama");
            q(w, '[data-expresion="A ∩ B ∩ C"]').click();
            ok(q(w, '[name="expresion"]').value === "A ∩ B ∩ C", "Atajo escribe la expresión");
            w = await recarga(frame, () => q(w, '[name="modo"][value="intersecciones"]').click());
            ok(!q(w, ".es-diagrama") && qa(w, ".cardinalidad-icono svg").length === 8, "Con intersecciones, cada dato dibuja las regiones que cuenta");
        }],
        ["Teclado contextual: elementos en conjuntos y regiones, no en la expresión", async w => {
            q(w, '[name="contenido_0"]').focus();
            await cuadro();
            ok(q(w, ".math-keyboard").hasAttribute("data-abierto") && q(w, '.math-keyboard [data-insercion="{}"]'), "Ofrece conjuntos anidados");
            ok(!q(w, '.math-keyboard [data-insercion="⊆"]'), "El perfil de literal no ofrece inclusión");
            q(w, '.math-keyboard [data-insercion="∅"]').click();
            ok(q(w, '[name="contenido_0"]').value.includes("∅"), "Inserción del teclado");
            q(w, '[name="expresion"]').focus();
            await cuadro();
            ok(!q(w, ".math-keyboard").hasAttribute("data-abierto"), "La expresión usa su barra, no el dock");
        }],
        ["CRUD conserva contenidos y renombra referencias completas", async (w, frame) => {
            valor(w, "nombre_0", "Conjunto1");
            w = await post(frame, "[data-guardar]");
            ok(q(w, '[name="expresion"]').value === "Conjunto1 ∈ B", "Renombrado");
            ok(q(w, '[name="contenido_0"]').value === "{1, 2}", "Conserva contenido");
            ok(q(w, "[data-venn-editor]").dataset.nombres === "Conjunto1,B" && tarjeta(w, "union").querySelector(".tarjeta-notacion").textContent === "Conjunto1 ∪ B", "Diagrama y tarjetas siguen el nombre nuevo");
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
            ok(!q(w, ".tarjetas") && q(w, "[data-panorama]").textContent.includes("Corrige"), "Las tarjetas esperan a que se corrija");
            valor(w, "contenido_0", "{1, 2}");
            valor(w, "venn_region_1", "{1,}");
            w = await post(frame, "[data-aplicar-regiones]");
            ok(errores(w).includes("Solo en A:") && q(w, '[name="venn_region_1"]').getAttribute("aria-invalid") === "true" && q(w, '[name="venn_region_1"]').value === "{1,}", "El error de una región la nombra y conserva el borrador: " + errores(w));
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
