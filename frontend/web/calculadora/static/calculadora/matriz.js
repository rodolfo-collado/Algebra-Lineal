(() => {
    "use strict";

    const tipoEntrada = document.querySelectorAll(
        'input[name="tipo_entrada"]'
    );
    const systemFields = document.getElementById("system-fields");
    const matrixFields = document.getElementById("matrix-fields");
    const equationsInput = document.getElementById("id_ecuaciones");
    const variablesInput = document.getElementById("id_variables");
    const matrixWrapper = document.getElementById("matrix-grid-wrapper");
    const matrixGrid = document.getElementById("matrix-grid");
    const matrixHelp = document.getElementById("matrix-grid-help");
    const initialValuesElement = document.getElementById(
        "matrix-initial-values"
    );

    if (
        !systemFields ||
        !matrixFields ||
        !equationsInput ||
        !variablesInput ||
        !matrixWrapper ||
        !matrixGrid ||
        !matrixHelp ||
        !initialValuesElement
    ) {
        return;
    }

    const initialValues = JSON.parse(initialValuesElement.textContent);
    const memoria = new Map();
    initialValues.forEach((fila, row) => fila.forEach((value, column) => {
        const clave = column === fila.length - 1 ? `b_${row}` : `a_${row}_${column}`;
        memoria.set(clave, value);
    }));
    const { validarDimension } = window.entradasSeguras;
    const maxCells = Number(matrixFields.dataset.maxCeldas);
    let renderedRows = 0;
    let renderedVariables = 0;
    let matrixVisited = document.querySelector('input[name="tipo_entrada"]:checked')?.value === "matriz";

    function dimensionValue(input) {
        const value = Number(input.value);
        return /^\d+$/.test(input.value) && Number.isSafeInteger(value) ? value : 0;
    }

    function dimensionAllowed(input, value) {
        return Number.isSafeInteger(value) && value >= Number(input.min) &&
            value <= Number(input.max);
    }

    function matrixError(rows, variables) {
        if (!dimensionAllowed(equationsInput, rows) || !dimensionAllowed(variablesInput, variables)) {
            return `Indica entre ${equationsInput.min} y ${equationsInput.max} ecuaciones ` +
                `y entre ${variablesInput.min} y ${variablesInput.max} variables enteras.`;
        }
        if (!Number.isSafeInteger(maxCells) || maxCells < 1 || rows * (variables + 1) > maxCells) {
            return `La matriz aumentada admite hasta ${maxCells} celdas ` +
                "(ecuaciones × (variables + 1)). Reduce las dimensiones.";
        }
        return "";
    }

    function currentValues() {
        matrixGrid.querySelectorAll("input[data-cell]").forEach((input) => {
            memoria.set(input.dataset.memoria, input.value);
        });
        return memoria;
    }

    function createElement(tagName, className, text) {
        const element = document.createElement(tagName);
        element.className = className;
        if (text !== undefined) {
            element.textContent = text;
        }
        return element;
    }

    function createCell(row, column, variables, values) {
        const name = `matriz_${row}_${column}`;
        const isIndependentTerm = column === variables;
        const label = isIndependentTerm
            ? `fila ${row + 1}, término independiente`
            : `fila ${row + 1}, coeficiente de x${column + 1}`;
        const input = document.createElement("input");

        input.type = "text";
        input.name = name;
        input.dataset.cell = name;
        input.dataset.memoria = isIndependentTerm ? `b_${row}` : `a_${row}_${column}`;
        input.value = values.get(input.dataset.memoria) ?? "";
        input.setAttribute("aria-label", label);
        input.autocomplete = "off";
        input.spellcheck = false;
        input.inputMode = "text";
        input.required = true;
        input.className = isIndependentTerm
            ? "matrix-input independent-input"
            : "matrix-input";

        return input;
    }

    function renderMatrix() {
        const rows = dimensionValue(equationsInput);
        const variables = dimensionValue(variablesInput);
        const error = matrixError(rows, variables);
        [equationsInput, variablesInput].forEach(input => validarDimension(input));
        if (dimensionAllowed(equationsInput, rows) && dimensionAllowed(variablesInput, variables) && error) {
            [equationsInput, variablesInput].forEach(input => validarDimension(input, error));
        }
        // Validar antes de leer/copiar celdas, borrar la cuadrícula o crear nodos.
        // Una dimensión transitoria inválida conserva la última entrada válida.
        if (error) {
            matrixWrapper.hidden = !matrixGrid.childElementCount;
            matrixHelp.textContent = error;
            return;
        }

        const values = currentValues();
        matrixGrid.replaceChildren();
        renderedRows = rows;
        renderedVariables = variables;
        matrixWrapper.hidden = false;
        matrixHelp.textContent =
            "Completa todas las celdas con enteros, fracciones o decimales con punto.";
        // Columnas auto: cada una toma el ancho de su valor más largo (field-sizing en CSS).
        matrixGrid.style.gridTemplateColumns =
            `3rem repeat(${variables}, auto) 1.25rem auto`;

        matrixGrid.appendChild(createElement("span", "matrix-corner"));
        for (let column = 0; column < variables; column += 1) {
            matrixGrid.appendChild(
                createElement("span", "matrix-header", `x${column + 1}`)
            );
        }
        matrixGrid.appendChild(
            createElement("span", "matrix-divider-header", "|")
        );
        matrixGrid.appendChild(
            createElement("span", "matrix-header matrix-header-b", "b")
        );

        for (let row = 0; row < rows; row += 1) {
            matrixGrid.appendChild(
                createElement("span", "matrix-row-label", `F${row + 1}`)
            );
            for (let column = 0; column <= variables; column += 1) {
                matrixGrid.appendChild(
                    createCell(row, column, variables, values)
                );
            }
            matrixGrid.insertBefore(
                createElement("span", "matrix-divider-cell", "|"),
                matrixGrid.children[matrixGrid.children.length - 1]
            );
        }
    }

    function focusCell(row, column) {
        const input = matrixGrid.querySelector(
            `[data-cell="matriz_${row}_${column}"]`
        );
        if (input && !input.readOnly && !input.matches(":disabled")) {
            input.focus();
        }
    }

    function setInputMode() {
        const selected = document.querySelector(
            'input[name="tipo_entrada"]:checked'
        );
        const isMatrix = selected?.value === "matriz";

        systemFields.hidden = isMatrix;
        matrixFields.hidden = !isMatrix;
        systemFields.disabled = isMatrix;
        matrixFields.disabled = !isMatrix;
        document.querySelectorAll("[data-input-hint]").forEach((hint) => {
            hint.hidden = hint.dataset.inputHint !== (isMatrix ? "matriz" : "sistema");
        });
        if (isMatrix) {
            // Un POST textual puede omitir dimensiones. Solo la primera visita
            // completa los campos ausentes; un POST matricial conserva sus errores.
            if (!matrixVisited) {
                if (!equationsInput.value) equationsInput.value = matrixFields.dataset.ecuacionesInicial;
                if (!variablesInput.value) variablesInput.value = matrixFields.dataset.variablesInicial;
                matrixVisited = true;
            }
            renderMatrix();
        } else {
            matrixWrapper.hidden = true;
        }
    }

    tipoEntrada.forEach((input) => {
        input.addEventListener("change", setInputMode);
    });

    // La pista del método sigue a la opción elegida; sin JavaScript queda la del servidor.
    function setMethodHint() {
        const selected = document.querySelector('input[name="metodo"]:checked');
        document.querySelectorAll("[data-method-hint]").forEach((hint) => {
            hint.hidden = hint.dataset.methodHint !== selected?.value;
        });
    }
    document.querySelectorAll('input[name="metodo"]').forEach((input) => {
        input.addEventListener("change", setMethodHint);
    });
    setMethodHint();
    equationsInput.addEventListener("input", renderMatrix);
    variablesInput.addEventListener("input", renderMatrix);

    // Controles de estructura (+/- ecuación, +/- variable): cambian las dimensiones,
    // no insertan símbolos. El campo numérico sigue siendo el valor que se envía.
    document.querySelectorAll(".stepper[data-estructura]").forEach((stepper) => {
        const dimensionInput = stepper.querySelector("input");
        if (!dimensionInput) {
            return;
        }
        stepper.querySelectorAll("button[data-paso]").forEach((button) => {
            button.hidden = false;
            button.addEventListener("click", () => {
                const siguiente = Math.min(Number(dimensionInput.max), Math.max(
                    Number(dimensionInput.min),
                    dimensionValue(dimensionInput) + Number(button.dataset.paso)
                ));
                const rows = dimensionInput === equationsInput ? siguiente : dimensionValue(equationsInput);
                const variables = dimensionInput === variablesInput ? siguiente : dimensionValue(variablesInput);
                // Se permite completar una dimensión que todavía está vacía.
                if (rows && variables) {
                    const error = matrixError(rows, variables);
                    if (error) {
                        matrixHelp.textContent = error;
                        return;
                    }
                }
                dimensionInput.value = String(siguiente);
                dimensionInput.dispatchEvent(new Event("input", { bubbles: true }));
            });
        });
    });
    matrixGrid.addEventListener("keydown", (event) => {
        const deltas = {
            ArrowLeft: [0, -1],
            ArrowRight: [0, 1],
            ArrowUp: [-1, 0],
            ArrowDown: [1, 0],
        };
        const delta = deltas[event.key];
        // Alt+←/→ queda para el historial de escritorio, como en las demás cuadrículas.
        if (!delta || !window.entradasSeguras.flechaDeCelda(event) || event.target.dataset?.cell === undefined) {
            return;
        }

        const match = /^matriz_(\d+)_(\d+)$/.exec(event.target.dataset.cell);
        if (!match) {
            return;
        }

        const rows = renderedRows;
        const columns = renderedVariables + 1;
        const row = Number(match[1]) + delta[0];
        const column = Number(match[2]) + delta[1];
        if (row < 0 || column < 0 || row >= rows || column >= columns) {
            return;
        }

        event.preventDefault();
        focusCell(row, column);
    });

    equationsInput.form.addEventListener("submit", (event) => {
        if (matrixFields.disabled) {
            return;
        }
        const error = matrixError(dimensionValue(equationsInput), dimensionValue(variablesInput));
        if (error) {
            event.preventDefault();
            matrixHelp.textContent = error;
        }
    });

    setInputMode();
    // Las celdas se crean en JS: el error del servidor queda junto a su control,
    // manteniendo un solo elemento de la cuadrícula por celda.
    matrixFields.querySelectorAll("[data-error-field]").forEach(error => {
        const nombre = error.dataset.errorField.replace(/^id_/, "");
        const input = [...matrixGrid.querySelectorAll("input")].find(campo => campo.name === nombre);
        if (!input) return;
        const caja = createElement("div", "matrix-grid-cell");
        input.before(caja);
        caja.append(input, error);
    });
})();
