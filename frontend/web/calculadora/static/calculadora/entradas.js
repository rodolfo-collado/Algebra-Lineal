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

    // Cuadrículas con celdas `celda_<matriz>_<i>_<j>` (Determinantes, Inversa y Ax=b). La matriz
    // aumentada (`data-cell`) y Operaciones (`data-campo`) siguen otras convenciones y no las usan.

    // Mismo marcado que components/matriz_entrada.html y matriz_celda.html entregan con
    // Aplicar sin JavaScript. `memoria` (nombre del campo → texto) restaura lo escrito.
    function crearCuadricula(nombre, filas, columnas, memoria, vector = false) {
        const matriz = document.getElementById("matrix-entry-template").content.cloneNode(true).querySelector("fieldset");
        const celdaTemplate = document.getElementById("matrix-cell-template");
        const tipo = vector ? "Vector" : "Matriz";
        matriz.dataset.matriz = nombre;
        matriz.toggleAttribute("data-vector", vector);
        matriz.querySelector("[data-tipo-matriz]").textContent = tipo;
        matriz.querySelector("[data-nombre-matriz]").textContent = nombre;
        matriz.querySelector("table").setAttribute("aria-label", `${tipo} ${nombre}`);
        matriz.querySelector(".matrix-scroll").setAttribute("aria-label",
            vector ? `Componentes del vector ${nombre}` : `Entradas de la matriz ${nombre}`);
        const cuerpo = matriz.querySelector("tbody");
        for (let i = 0; i < filas; i += 1) {
            const fila = document.createElement("tr");
            for (let j = 0; j < columnas; j += 1) {
                const celda = celdaTemplate.content.cloneNode(true);
                const input = celda.querySelector("input");
                input.name = `celda_${nombre}_${i}_${j}`;
                input.id = `id_${input.name}`;
                input.value = memoria.get(input.name) ?? "";
                const label = celda.querySelector("label");
                label.htmlFor = input.id;
                label.textContent = vector ? `Vector ${nombre}, componente ${i + 1}` : `Matriz ${nombre}, fila ${i + 1}, columna ${j + 1}`;
                fila.append(celda);
            }
            cuerpo.append(fila);
        }
        return matriz;
    }

    const DESPLAZAMIENTOS = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };

    // Tab recorre todos los campos. Las flechas verticales cambian de fila; las horizontales
    // solo cambian de celda al llegar al extremo del texto. El destino conserva el nombre de
    // la matriz: desde el borde de A no se salta a B ni a b.
    function moverEntreCeldas(ambito) {
        ambito.addEventListener("keydown", event => {
            const input = event.target;
            const delta = DESPLAZAMIENTOS[event.key];
            if (!delta || !flechaDeCelda(event) || !input.name.startsWith("celda_")) return;
            const [, nombre, i, j] = input.name.split("_");
            const destino = ambito.querySelector(`[name="celda_${nombre}_${Number(i) + delta[0]}_${Number(j) + delta[1]}"]`);
            if (destino && !destino.readOnly && !destino.matches(":disabled")) {
                event.preventDefault();
                destino.focus();
            }
        });
    }

    // Botones − y + de matrices/_dimension.html, ocultos sin JavaScript. Desde un valor
    // inválido parten del mínimo; el evento input deja que la herramienta redibuje.
    function activarPasos(ambito) {
        ambito.querySelectorAll(".stepper [data-paso]").forEach(button => {
            button.hidden = false;
            button.addEventListener("click", () => {
                const input = button.closest(".stepper").querySelector("input");
                const actual = dimensionValida(input) ? Number(input.value) : Number(input.min);
                input.value = String(Math.min(Number(input.max), Math.max(Number(input.min), actual + Number(button.dataset.paso))));
                input.dispatchEvent(new Event("input", { bubbles: true }));
            });
        });
    }

    window.entradasSeguras = { dimensionValida, validarDimension, flechaDeCelda, filasDeMatriz,
        bloqueDeTexto, aplicarPegado, crearCuadricula, moverEntreCeldas, activarPasos };

    // Solo texto tabulado; las filas/celdas existentes deciden el destino.
    // Las líneas vacías de los extremos (la terminación de una hoja de cálculo o un salto
    // de más al copiar un resultado) no son filas; una línea vacía interior sí lo es.
    document.addEventListener("paste", event => {
        const input = event.target;
        if (event.defaultPrevented || !input.matches?.('input.matrix-input[type="text"]') ||
            input.closest("[hidden], [data-escalar]")) return;
        const form = input.closest("[data-entrada-calculo]");
        const grid = input.closest(".matrix-entry-table, #matrix-grid, #vector-list");
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
        if (!nuevo && (input.readOnly || input.matches(":disabled") ||
            (!texto.includes("\t") && bloque.length <= 1))) return;
        event.preventDefault();

        const estado = window.deshacerPegado.estado(form);
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
        if (input.readOnly || input.matches(":disabled") || cambios.some(([celda]) =>
            !celda?.isConnected || celda.closest(".matrix-entry-table, #matrix-grid, #vector-list") !== grid ||
            celda.readOnly || celda.matches(":disabled") || celda.closest("[hidden]"))) {
            estado.textContent = "El bloque incluye celdas que no se pueden editar. No se pegó ningún valor.";
            return;
        }
        if (cambios.some(([celda, valor]) => celda.maxLength >= 0 && valor.length > celda.maxLength)) {
            estado.textContent = "Un valor supera el límite de texto de su celda. No se pegó ningún valor.";
            return;
        }
        window.deshacerPegado.pegar(cambios, grid, input);
        // Se conserva el campo activo y el perfil del teclado contextual.
    });

    // Desenfocar evita el incremento nativo sin cancelar el desplazamiento.
    document.addEventListener("wheel", event => {
        const input = event.target.closest?.('input[type="number"]');
        if (input && input === document.activeElement) input.blur();
    }, { capture: true, passive: true });

    document.querySelectorAll("#expresiones-form, #ecuacion-form, #inversa-form, #determinantes-form, #vectores-form, #sistema-form").forEach(form => {
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
