(() => {
    "use strict";

    function dimensionValida(input) {
        const valor = Number(input.value);
        return /^\d+$/.test(input.value) && Number.isSafeInteger(valor) &&
            valor >= Number(input.min) && valor <= Number(input.max);
    }

    function validarDimension(input, mensaje = "") {
        const valida = input.disabled || dimensionValida(input);
        const caja = input.closest(".dimension-field");
        const servidor = caja?.querySelector("[data-error-field]");
        const errorServidor = servidor && !servidor.hidden && input.value === input.defaultValue && !input.disabled;
        if (servidor && !errorServidor) servidor.hidden = true;
        const error = input.disabled || errorServidor ? "" : mensaje || (valida ? "" :
            `Indica un número entero entre ${input.min} y ${input.max}.`);
        if (caja) {
            let ayuda = caja.querySelector("[data-error-dimension]");
            if (!ayuda) {
                ayuda = document.createElement("p");
                ayuda.className = "field-error";
                ayuda.dataset.errorDimension = "";
                ayuda.setAttribute("role", "status");
                ayuda.setAttribute("aria-live", "polite");
                caja.append(ayuda);
            }
            ayuda.id = `${input.id}_dimension_error`;
            ayuda.textContent = error;
            ayuda.hidden = !error;
            const ids = new Set((input.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
            // Reindexar símbolos también actualiza el identificador de la ayuda.
            for (const id of ids) if (id.endsWith("_dimension_error")) ids.delete(id);
            ids.add(ayuda.id);
            input.setAttribute("aria-describedby", [...ids].join(" "));
            caja.querySelectorAll("[data-paso]").forEach(button => {
                button.disabled = input.disabled || !valida ||
                    (Number(button.dataset.paso) < 0 ? Number(input.value) <= Number(input.min) : Number(input.value) >= Number(input.max));
            });
        }
        input.setAttribute("aria-invalid", String(Boolean(error || errorServidor)));
        return !error && !errorServidor;
    }

    function flechaDeCelda(event) {
        const input = event.target;
        if (event.defaultPrevented || event.isComposing || event.keyCode === 229 ||
            event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
            !input.matches?.('input.matrix-input[type="text"]') || input.readOnly ||
            input.matches(":disabled") || input.selectionStart !== input.selectionEnd) return false;
        if (event.key === "ArrowLeft" && input.selectionStart !== 0) return false;
        if (event.key === "ArrowRight" && input.selectionEnd !== input.value.length) return false;
        return true;
    }

    window.entradasSeguras = { dimensionValida, validarDimension, flechaDeCelda };

    // Solo texto tabulado; las filas/celdas existentes deciden el destino.
    // Las líneas vacías de los extremos (la terminación de una hoja de cálculo o un salto
    // de más al copiar un resultado) no son filas; una línea vacía interior sí lo es.
    document.addEventListener("paste", event => {
        const input = event.target;
        if (event.defaultPrevented || !input.matches?.('input.matrix-input[type="text"]') ||
            input.readOnly || input.matches(":disabled") || input.closest("[hidden], [data-escalar]")) return;
        const form = input.closest("[data-entrada-calculo]");
        const grid = input.closest(".matrix-entry-table, #matrix-grid, #vector-list");
        if (!form || !grid || !event.clipboardData) return;
        const texto = event.clipboardData.getData("text/plain");
        const lineas = texto.split(/\r?\n/);
        while (lineas.length && lineas[0] === "") lineas.shift();
        while (lineas.length && lineas.at(-1) === "") lineas.pop();
        if (!texto.includes("\t") && lineas.length <= 1) return;
        event.preventDefault();

        let estado = form.querySelector('[data-presupuesto], [data-estado-vectores], [data-estado-pegado]');
        if (!estado) {
            estado = document.createElement("p");
            estado.className = "field-help";
            estado.dataset.estadoPegado = "";
            estado.setAttribute("role", "status");
            estado.setAttribute("aria-live", "polite");
            form.querySelector(".workspace-actions").before(estado);
        }
        const bloque = lineas.map(linea => linea.split("\t").map(valor => valor.trim()));
        const alto = bloque.length;
        const ancho = bloque[0].length;
        if (bloque.some(fila => fila.length !== ancho)) {
            estado.textContent = "Cada fila del bloque debe tener la misma cantidad de columnas. No se pegó ningún valor.";
            return;
        }
        let filas;
        if (grid.id === "matrix-grid") {
            filas = [];
            grid.querySelectorAll("input[data-cell]").forEach(celda => {
                const fila = Number(celda.name.split("_")[1]);
                (filas[fila] ??= []).push(celda);
            });
        } else {
            filas = [...grid.querySelectorAll(grid.id === "vector-list" ? ".vector-row[data-vector]" : "tbody tr")]
                .map(fila => [...fila.querySelectorAll("input.matrix-input")]);
        }
        const inicio = filas.findIndex(fila => fila.includes(input));
        if (inicio < 0) return;
        const columna = filas[inicio].indexOf(input);
        const disponibles = filas[inicio].length - columna;
        if (inicio + alto > filas.length || filas.slice(inicio, inicio + alto).some(fila => columna + ancho > fila.length)) {
            estado.textContent = `El bloque no cabe en la cuadrícula. Lo pegado ocupa ${alto}×${ancho} y desde esta celda solo caben ${filas.length - inicio}×${disponibles}. No se pegó ningún valor.`;
            return;
        }
        const cambios = bloque.flatMap((fila, i) => fila.map((valor, j) => [filas[inicio + i][columna + j], valor]));
        if (cambios.some(([celda]) => celda.readOnly || celda.matches(":disabled") || celda.closest("[hidden]"))) {
            estado.textContent = "El bloque incluye celdas que no se pueden editar. No se pegó ningún valor.";
            return;
        }
        if (cambios.some(([celda, valor]) => celda.maxLength >= 0 && valor.length > celda.maxLength)) {
            estado.textContent = "Un valor supera el límite de texto de su celda. No se pegó ningún valor.";
            return;
        }
        // Aplicar todo antes de emitir input: los observadores ven el bloque completo.
        cambios.forEach(([celda, valor]) => { celda.value = valor; });
        cambios.forEach(([celda]) => celda.dispatchEvent(new Event("input", { bubbles: true })));
        estado.textContent = `Se pegaron ${cambios.length} valores.`;
        // Se conserva el campo activo y el perfil del teclado contextual.
    });

    // Desenfocar evita el incremento nativo sin cancelar el desplazamiento.
    document.addEventListener("wheel", event => {
        const input = event.target.closest?.('input[type="number"]');
        if (input && input === document.activeElement) input.blur();
    }, { capture: true, passive: true });

    document.querySelectorAll("#expresiones-form, #ecuacion-form, #inversa-form, #vectores-form, #sistema-form").forEach(form => {
        form.querySelectorAll("[data-aplicar]").forEach(button => {
            button.hidden = true;
            // Un submit oculto todavía puede ser el botón por defecto de Enter.
            button.disabled = true;
        });
        form.addEventListener("keydown", event => {
            const input = event.target;
            if (event.key !== "Enter" || event.isComposing || input.tagName !== "INPUT" ||
                !["text", "number"].includes(input.type)) return;
            event.preventDefault();
            if (input.closest(".dimension-field")) return;
            const calcular = form.querySelector('.workspace-actions button[type="submit"]');
            if (calcular) form.requestSubmit(calcular);
        });
        form.addEventListener("submit", event => {
            const dimensiones = [...form.querySelectorAll('.dimension-field input[type="number"]')]
                .filter(input => !input.disabled && !input.closest("fieldset:disabled"));
            if (dimensiones.some(input => !dimensionValida(input) || input.getAttribute("aria-invalid") === "true")) {
                event.preventDefault();
                dimensiones.forEach(input => {
                    if (!dimensionValida(input)) validarDimension(input);
                });
            }
        });
    });
})();
