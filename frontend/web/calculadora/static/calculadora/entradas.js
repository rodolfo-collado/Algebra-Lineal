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

    function filasDeMatriz(grid) {
        if (grid.id === "matrix-grid") {
            const filas = [];
            grid.querySelectorAll("input[data-cell]").forEach(celda => {
                const fila = Number(celda.name.split("_")[1]);
                (filas[fila] ??= []).push(celda);
            });
            return filas;
        }
        return [...grid.querySelectorAll(grid.id === "vector-list" ? ".vector-row[data-vector]" : "tbody tr")]
            .map(fila => [...fila.querySelectorAll("input.matrix-input")]);
    }

    function bloqueDeTexto(texto, conservar = false) {
        const lineas = texto.split(/\r?\n/);
        if (!conservar) {
            while (lineas.length && lineas[0] === "") lineas.shift();
            while (lineas.length && lineas.at(-1) === "") lineas.pop();
        }
        return lineas.map(linea => linea.split("\t").map(valor => conservar ? valor : valor.trim()));
    }

    function aplicarPegado(cambios) {
        const registro = cambios.map(([input, nuevo]) => ({ input, anterior: input.value, nuevo }));
        // Aplicar todo antes de emitir input: los observadores ven el bloque completo.
        registro.forEach(({ input, nuevo }) => { input.value = nuevo; });
        registro.forEach(({ input }) => input.dispatchEvent(new Event("input", { bubbles: true })));
        return registro;
    }

    window.entradasSeguras = { dimensionValida, validarDimension, flechaDeCelda, filasDeMatriz,
        bloqueDeTexto, aplicarPegado };

    // Solo texto tabulado; las filas/celdas existentes deciden el destino.
    // Las líneas vacías de los extremos (la terminación de una hoja de cálculo o un salto
    // de más al copiar un resultado) no son filas; una línea vacía interior sí lo es.
    document.addEventListener("paste", event => {
        const input = event.target;
        const esCelda = input.matches?.('input.matrix-input[type="text"]');
        const esControl = input.matches?.(".matrix-selection summary");
        if (event.defaultPrevented || (!esCelda && !esControl) || input.closest("[hidden], [data-escalar]")) return;
        const form = input.closest("[data-entrada-calculo]");
        const grid = esCelda ? input.closest(".matrix-entry-table, #matrix-grid, #vector-list") :
            input.closest(".matrix, #matrix-grid-wrapper")?.querySelector(".matrix-entry-table, #matrix-grid");
        if (!form || !grid || !event.clipboardData) return;
        const texto = event.clipboardData.getData("text/plain");
        // Consultar sin recortar readonly/disabled: un fallo no debe cambiar la selección.
        const snapshot = window.seleccionMatricial?.obtener(grid, false);
        const seleccion = snapshot?.activa ? snapshot : null;
        const copia = window.copiadoMatricial;
        const propio = copia && event.clipboardData.getData(copia.TIPO);
        const metadata = propio ? copia.parsear(propio, texto) : null;
        if (!texto && !metadata && ![...event.clipboardData.types].includes("text/plain")) return;
        const mascara = snapshot && metadata?.forma === "mascara" ? metadata : null;
        const nuevo = Boolean(seleccion || mascara);
        const textoValido = !nuevo || copia.textoAdmitido(texto);
        const bloque = textoValido ? bloqueDeTexto(texto, nuevo && Boolean(metadata)) : [];
        if (!nuevo && (!esCelda || input.readOnly || input.matches(":disabled") ||
            (!texto.includes("\t") && bloque.length <= 1))) return;
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
        if (!textoValido) {
            estado.textContent = "Los datos copiados superan el límite de 64 KiB. No se pegó ningún valor.";
            return;
        }
        if (nuevo && texto === "" && !bloque.length) bloque.push([""]);
        const alto = bloque.length;
        const ancho = bloque[0]?.length;
        if (!alto || bloque.some(fila => fila.length !== ancho)) {
            estado.textContent = "Cada fila del bloque debe tener la misma cantidad de columnas. No se pegó ningún valor.";
            return;
        }
        const filas = filasDeMatriz(grid);
        let cambios;
        if (seleccion) {
            let valores;
            if (alto === 1 && ancho === 1) {
                valores = seleccion.celdas.map(() => bloque[0][0]);
            } else if (mascara) {
                if (mascara.celdas.length !== seleccion.celdas.length) {
                    estado.textContent = `Se copiaron ${mascara.celdas.length} celdas, pero hay ${seleccion.celdas.length} seleccionadas. No se pegó ningún valor.`;
                    return;
                }
                valores = mascara.celdas.map(([i, j]) => bloque[i][j]);
            } else {
                if (!seleccion.rectangular) {
                    estado.textContent = "Los datos copiados no son compatibles con esta selección. No se pegó ningún valor.";
                    return;
                }
                const { filaInicio, filaFin, columnaInicio, columnaFin } = seleccion.limites;
                const m = filaFin - filaInicio + 1, n = columnaFin - columnaInicio + 1;
                if (alto !== m || ancho !== n) {
                    estado.textContent = `El bloque copiado es de ${alto}×${ancho} y la selección es de ${m}×${n}. No se pegó ningún valor.`;
                    return;
                }
                valores = bloque.flat();
            }
            cambios = seleccion.celdas.map(({ fila, columna }, i) => [filas[fila]?.[columna], valores[i]]);
        } else {
            const inicio = filas.findIndex(fila => fila.includes(input));
            if (inicio < 0) return;
            const columna = filas[inicio].indexOf(input);
            const disponibles = filas[inicio].length - columna;
            if (inicio + alto > filas.length || filas.slice(inicio, inicio + alto).some(fila => columna + ancho > fila.length)) {
                estado.textContent = mascara ? "La selección copiada no cabe desde esta celda. No se pegó ningún valor." :
                    `El bloque no cabe en la cuadrícula. Lo pegado ocupa ${alto}×${ancho} y desde esta celda solo caben ${filas.length - inicio}×${disponibles}. No se pegó ningún valor.`;
                return;
            }
            cambios = mascara ? mascara.celdas.map(([i, j]) => [filas[inicio + i][columna + j], bloque[i][j]]) :
                bloque.flatMap((fila, i) => fila.map((valor, j) => [filas[inicio + i][columna + j], valor]));
        }
        if ((esCelda && (input.readOnly || input.matches(":disabled"))) || cambios.some(([celda]) =>
            !celda?.isConnected || celda.closest(".matrix-entry-table, #matrix-grid, #vector-list") !== grid ||
            celda.readOnly || celda.matches(":disabled") || celda.closest("[hidden]"))) {
            estado.textContent = "El bloque incluye celdas que no se pueden editar. No se pegó ningún valor.";
            return;
        }
        if (cambios.some(([celda, valor]) => celda.maxLength >= 0 && valor.length > celda.maxLength)) {
            estado.textContent = "Un valor supera el límite de texto de su celda. No se pegó ningún valor.";
            return;
        }
        aplicarPegado(cambios);
        estado.textContent = cambios.length === 1 ? "Se pegó 1 valor." : `Se pegaron ${cambios.length} valores.`;
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
