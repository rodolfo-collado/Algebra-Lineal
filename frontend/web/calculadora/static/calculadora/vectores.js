(() => {
    "use strict";

    // Operaciones con vectores: la operación decide qué vectores se piden y la
    // dimensión n cuántas componentes tiene cada uno. Este script solo redibuja
    // las celdas y atiende los botones de estructura; el servidor vuelve a
    // validar todo al calcular.
    const root = document.querySelector("[data-vectores]");
    if (!root) return;

    const operaciones = root.querySelectorAll('input[name="operacion"]');
    const dimensionInput = document.getElementById("id_dimension");
    const vectoresInput = document.getElementById("id_vectores");
    const lista = document.getElementById("vector-list");
    const boton = root.querySelector("[data-boton-calcular]");
    const initialValuesElement = document.getElementById("vector-initial-values");
    if (!dimensionInput || !vectoresInput || !lista || !operaciones.length) return;

    const initialValues = initialValuesElement ? JSON.parse(initialValuesElement.textContent) : {};
    let primeraCarga = true;
    let operacionAnterior = operacionActual();
    const agregar = root.querySelector("[data-agregar-vector]");
    const OBJETIVO = "b";

    function limite(input, atributo, predeterminado) {
        if (!input.hasAttribute(atributo)) return predeterminado;
        const valor = Number(input.getAttribute(atributo));
        return Number.isInteger(valor) ? valor : predeterminado;
    }

    function valorEntero(input, predeterminado) {
        const valor = Number(input.value);
        if (!Number.isInteger(valor)) return predeterminado;
        return Math.min(Math.max(valor, limite(input, "min", 1)), limite(input, "max", Infinity));
    }

    function operacionActual() {
        const marcada = root.querySelector('input[name="operacion"]:checked');
        return marcada ? marcada.value : "suma";
    }

    function nombresVectores(operacion, cantidad) {
        if (operacion === "combinacion") {
            const nombres = [];
            for (let indice = 1; indice <= cantidad; indice += 1) nombres.push(`v${indice}`);
            nombres.push(OBJETIVO);
            return nombres;
        }
        if (operacion === "escalar") return ["u"];
        return ["u", "v", ...Array.from({length: Math.max(0, cantidad - 2)}, (_, i) => `v${i + 3}`)];
    }

    function valoresActuales() {
        const valores = {};
        lista.querySelectorAll("input[data-cell]").forEach((input) => {
            valores[input.dataset.cell] = input.value;
        });
        return valores;
    }

    function crear(tag, className, texto) {
        const elemento = document.createElement(tag);
        if (className) elemento.className = className;
        if (texto !== undefined) elemento.textContent = texto;
        return elemento;
    }

    function fence(texto) {
        const elemento = crear("span", "vector-fence", texto);
        elemento.setAttribute("aria-hidden", "true");
        return elemento;
    }

    function crearCelda(nombre, indice, esObjetivo, valores) {
        const campo = `${nombre}_${indice}`;
        const input = document.createElement("input");
        input.type = "text";
        input.name = campo;
        input.dataset.cell = campo;
        input.value = valores[campo] ?? (primeraCarga ? initialValues[campo] : "") ?? "";
        input.className = esObjetivo ? "matrix-input independent-input" : "matrix-input";
        input.setAttribute("aria-label", `Componente ${indice + 1} de ${nombre}`);
        input.autocomplete = "off";
        input.spellcheck = false;
        input.inputMode = "text";
        input.required = true;
        return input;
    }

    // Mismo marcado que modules/vectores/_fila.html.
    function crearFila(nombre, dimension, valores) {
        const esObjetivo = nombre === OBJETIVO;
        const fila = crear("div", esObjetivo ? "vector-row vector-row-target" : "vector-row");
        fila.dataset.vector = nombre;
        fila.setAttribute("role", "group");
        fila.setAttribute("aria-label", `Vector ${nombre}`);

        const etiqueta = crear("span", "vector-name", `${nombre} =`);
        etiqueta.setAttribute("aria-hidden", "true");
        fila.appendChild(etiqueta);

        const celdas = crear("div", "vector-inputs");
        celdas.appendChild(fence("("));
        for (let indice = 0; indice < dimension; indice += 1) {
            celdas.appendChild(crearCelda(nombre, indice, esObjetivo, valores));
            if (indice < dimension - 1) {
                const separador = crear("span", "vector-sep", ",");
                separador.setAttribute("aria-hidden", "true");
                celdas.appendChild(separador);
            }
        }
        celdas.appendChild(fence(")"));
        fila.appendChild(celdas);
        return fila;
    }

    function filaEscalar(existente) {
        const fila = crear("div", "vector-row vector-row-scalar");
        fila.dataset.escalar = "";
        fila.setAttribute("role", "group");
        fila.setAttribute("aria-label", "Escalar k");
        const etiqueta = crear("span", "vector-name", "k =");
        etiqueta.setAttribute("aria-hidden", "true");
        fila.appendChild(etiqueta);
        const celdas = crear("div", "vector-inputs");
        let input = existente;
        if (!input) {
            input = document.createElement("input");
            input.type = "text";
            input.name = "escalar";
            input.id = "id_escalar";
            input.className = "matrix-input scalar-input";
            input.setAttribute("aria-label", "Escalar k");
            input.autocomplete = "off";
            input.spellcheck = false;
            input.inputMode = "text";
        }
        celdas.appendChild(input);
        fila.appendChild(celdas);
        return fila;
    }

    function render() {
        const operacion = operacionActual();
        const minimo = operacion === "combinacion" || operacion === "escalar" ? 1 : 2;
        vectoresInput.min = String(minimo);
        vectoresInput.disabled = operacion === "escalar";
        if (operacion !== operacionAnterior) {
            if (![operacion, operacionAnterior].every(op => ["suma", "resta"].includes(op))) {
                vectoresInput.value = String(minimo);
            }
            operacionAnterior = operacion;
        }
        root.querySelector("[data-cantidad-vectores]").hidden = true;
        agregar.hidden = operacion === "escalar";
        const dimension = valorEntero(dimensionInput, 3);
        const cantidad = valorEntero(vectoresInput, 2);
        vectoresInput.value = String(cantidad);
        const valores = valoresActuales();
        // El escalar conserva su nodo (y su valor) entre redibujados.
        const escalarExistente = lista.querySelector('input[name="escalar"]');

        lista.replaceChildren();
        lista.dataset.dimension = String(dimension);
        lista.dataset.vectores = String(cantidad);
        if (operacion === "escalar") {
            lista.appendChild(filaEscalar(escalarExistente));
        }
        const nombres = nombresVectores(operacion, cantidad);
        nombres.forEach((nombre, indice) => {
            const fila = crearFila(nombre, dimension, valores);
            if (nombre !== OBJETIVO && indice >= minimo && operacion !== "escalar") {
                const quitar = crear("button", "stepper-btn", "×");
                quitar.type = "button";
                quitar.setAttribute("aria-label", `Quitar vector ${nombre}`);
                quitar.addEventListener("click", () => {
                    // Desplazar los valores preserva el orden, también en la resta.
                    for (let i = indice; i < cantidad - 1; i += 1) {
                        for (let j = 0; j < dimension; j += 1) {
                            lista.querySelector(`[name="${nombres[i]}_${j}"]`).value = lista.querySelector(`[name="${nombres[i + 1]}_${j}"]`).value;
                        }
                    }
                    vectoresInput.value = String(cantidad - 1);
                    render();
                });
                fila.appendChild(quitar);
            }
            lista.appendChild(fila);
        });
        primeraCarga = false;
        const resultado = document.getElementById("resultado");
        if (resultado && render.iniciado) resultado.hidden = true;
        render.iniciado = true;

        root.querySelectorAll("[data-solo-operacion]").forEach((bloque) => {
            bloque.hidden = bloque.dataset.soloOperacion !== operacion;
        });
        root.querySelectorAll("[data-operacion-hint]").forEach((ayuda) => {
            ayuda.hidden = ayuda.dataset.operacionHint !== operacion;
        });
        root.querySelectorAll("[data-operacion-hint-fields]").forEach((ayuda) => {
            ayuda.hidden = ayuda.dataset.operacionHintFields !== operacion;
        });
        if (boton) {
            boton.textContent = operacion === "combinacion" ? "Comprobar" : "Calcular";
        }
    }

    operaciones.forEach((radio) => radio.addEventListener("change", render));
    dimensionInput.addEventListener("input", render);
    vectoresInput.addEventListener("input", render);
    agregar.addEventListener("click", () => {
        vectoresInput.value = String(valorEntero(vectoresInput, 2) + 1);
        render();
    });

    // Controles de estructura (+/- componente, +/- vector): cambian n y k, no
    // insertan símbolos. El campo numérico sigue siendo el valor que se envía.
    root.querySelectorAll(".stepper[data-estructura]").forEach((stepper) => {
        const input = stepper.querySelector("input");
        if (!input) return;
        stepper.querySelectorAll("button[data-paso]").forEach((button) => {
            button.hidden = false;
            button.addEventListener("click", () => {
                const minimo = limite(input, "min", 1);
                const maximo = limite(input, "max", Infinity);
                const siguiente = valorEntero(input, minimo) + Number(button.dataset.paso);
                input.value = String(Math.min(Math.max(siguiente, minimo), maximo));
                input.dispatchEvent(new Event("input", { bubbles: true }));
            });
        });
    });

    // Flechas: izquierda/derecha entre componentes, arriba/abajo entre vectores.
    lista.addEventListener("keydown", (event) => {
        const deltas = { ArrowLeft: [0, -1], ArrowRight: [0, 1], ArrowUp: [-1, 0], ArrowDown: [1, 0] };
        const delta = deltas[event.key];
        const celda = event.target?.dataset?.cell;
        if (!delta || celda === undefined) return;

        const filas = Array.from(lista.querySelectorAll(".vector-row[data-vector]"));
        const filaActual = event.target.closest(".vector-row");
        const indiceFila = filas.indexOf(filaActual) + delta[0];
        if (indiceFila < 0 || indiceFila >= filas.length) return;
        const celdas = Array.from(filaActual.querySelectorAll("input[data-cell]"));
        const indiceCelda = celdas.indexOf(event.target) + delta[1];
        const destino = Array.from(filas[indiceFila].querySelectorAll("input[data-cell]"))[indiceCelda];
        if (!destino) return;

        event.preventDefault();
        destino.focus();
    });

    render();
})();
