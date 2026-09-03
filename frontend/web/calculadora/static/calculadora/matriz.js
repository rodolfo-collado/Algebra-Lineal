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

    function dimensionValue(input) {
        const value = Number(input.value);
        return Number.isInteger(value) && value > 0 ? value : 0;
    }

    function currentValues() {
        const values = {};
        matrixGrid.querySelectorAll("input[data-cell]").forEach((input) => {
            values[input.dataset.cell] = input.value;
        });
        return values;
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
        input.value = values[name] ?? initialValues[row]?.[column] ?? "";
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
        const values = currentValues();

        matrixGrid.replaceChildren();
        if (!rows || !variables) {
            matrixWrapper.hidden = true;
            matrixHelp.textContent =
                "Indica un número positivo de ecuaciones y variables para generar la cuadrícula.";
            return;
        }

        matrixWrapper.hidden = false;
        matrixHelp.textContent =
            "Completa todas las celdas con números, enteros o fracciones.";
        matrixGrid.style.gridTemplateColumns =
            `3rem repeat(${variables}, 4.25rem) 1.25rem 4.25rem`;

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
        if (input) {
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
        if (isMatrix) {
            renderMatrix();
        } else {
            matrixWrapper.hidden = true;
        }
    }

    tipoEntrada.forEach((input) => {
        input.addEventListener("change", setInputMode);
    });
    equationsInput.addEventListener("input", renderMatrix);
    variablesInput.addEventListener("input", renderMatrix);
    matrixGrid.addEventListener("keydown", (event) => {
        const deltas = {
            ArrowLeft: [0, -1],
            ArrowRight: [0, 1],
            ArrowUp: [-1, 0],
            ArrowDown: [1, 0],
        };
        const delta = deltas[event.key];
        if (!delta || event.target.dataset?.cell === undefined) {
            return;
        }

        const match = /^matriz_(\d+)_(\d+)$/.exec(event.target.dataset.cell);
        if (!match) {
            return;
        }

        const rows = dimensionValue(equationsInput);
        const columns = dimensionValue(variablesInput) + 1;
        const row = Number(match[1]) + delta[0];
        const column = Number(match[2]) + delta[1];
        if (row < 0 || column < 0 || row >= rows || column >= columns) {
            return;
        }

        event.preventDefault();
        focusCell(row, column);
    });

    setInputMode();
})();
