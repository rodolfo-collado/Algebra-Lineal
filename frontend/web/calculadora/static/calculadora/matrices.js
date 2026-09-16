(() => {
    "use strict";

    const root = document.querySelector("[data-matrices]");
    if (!root) return;
    const opciones = JSON.parse(document.getElementById("matrix-options").textContent);
    const lista = root.querySelector("[data-matrix-list]");
    const escalar = root.querySelector("[data-matrix-scalar]");
    const filas = root.querySelector('[name="filas"]');
    const columnas = root.querySelector('[name="columnas"]');
    const matrizTemplate = document.getElementById("matrix-entry-template");
    const celdaTemplate = document.getElementById("matrix-cell-template");
    const escalarTemplate = document.getElementById("matrix-scalar-template");
    const memoria = new Map();
    let valorEscalar = "";

    function guardar() {
        lista.querySelectorAll("input").forEach(input => memoria.set(input.name, input.value));
        const input = escalar.querySelector("input");
        if (input) valorEscalar = input.value;
    }

    function dimensionValida(input) {
        const valor = Number(input.value);
        return Number.isInteger(valor) && valor >= Number(input.min) && valor <= Number(input.max);
    }

    function ocultarResultado() {
        const resultado = document.getElementById("resultado");
        if (resultado) resultado.hidden = true;
    }

    function crearMatriz(nombre, m, n) {
        // Las plantillas inertes comparten el marcado con la versión del servidor.
        const fragmento = matrizTemplate.content.cloneNode(true);
        const matriz = fragmento.querySelector("fieldset");
        matriz.dataset.matriz = nombre;
        matriz.querySelector("[data-nombre-matriz]").textContent = nombre;
        matriz.querySelector("table").setAttribute("aria-label", `Matriz ${nombre}`);
        matriz.querySelector(".matrix-scroll").setAttribute("aria-label", `Entradas de la matriz ${nombre}`);
        const cuerpo = matriz.querySelector("tbody");
        for (let i = 0; i < m; i += 1) {
            const fila = document.createElement("tr");
            for (let j = 0; j < n; j += 1) {
                const celda = celdaTemplate.content.cloneNode(true);
                const input = celda.querySelector("input");
                input.name = `celda_${nombre}_${i}_${j}`;
                input.id = `id_${input.name}`;
                input.value = memoria.get(input.name) ?? "";
                const label = celda.querySelector("label");
                label.htmlFor = input.id;
                label.textContent = `Matriz ${nombre}, fila ${i + 1}, columna ${j + 1}`;
                fila.append(celda);
            }
            cuerpo.append(fila);
        }
        return fragmento;
    }

    function actualizarBotones() {
        root.querySelectorAll(".stepper").forEach(stepper => {
            const input = stepper.querySelector("input");
            stepper.querySelectorAll("[data-paso]").forEach(button => {
                const limite = Number(button.dataset.paso) < 0 ? input.min : input.max;
                button.disabled = Number(input.value) === Number(limite);
            });
        });
    }

    function render() {
        ocultarResultado();
        // No se corrigen silenciosamente dimensiones inválidas: el servidor
        // muestra el error. Mientras se escribe, se conserva la cuadrícula.
        if (!dimensionValida(filas) || !dimensionValida(columnas)) return;
        guardar();
        const operacion = root.querySelector('[name="operacion"]:checked').value;
        const opcion = opciones[operacion];
        lista.replaceChildren(...opcion.matrices.map(nombre => crearMatriz(nombre, Number(filas.value), Number(columnas.value))));
        escalar.replaceChildren();
        if (opcion.escalar) {
            escalar.append(escalarTemplate.content.cloneNode(true));
            escalar.querySelector("input").value = valorEscalar;
        }
        root.querySelector("[data-operation-help]").textContent = opcion.ayuda;
        root.querySelector("[data-matrix-shape]").textContent = `${filas.value}×${columnas.value} en cada matriz de entrada. De ${filas.min} a ${filas.max} filas y columnas.`;
        actualizarBotones();
    }

    root.querySelectorAll('[name="operacion"]').forEach(radio => radio.addEventListener("change", render));
    [filas, columnas].forEach(input => input.addEventListener("input", render));
    root.querySelectorAll(".stepper [data-paso]").forEach(button => {
        button.hidden = false;
        button.addEventListener("click", () => {
            const input = button.closest(".stepper").querySelector("input");
            const actual = dimensionValida(input) ? Number(input.value) : Number(input.min);
            input.value = String(Math.min(Number(input.max), Math.max(Number(input.min), actual + Number(button.dataset.paso))));
            render();
        });
    });
    root.addEventListener("input", ocultarResultado);
    root.querySelector("[data-aplicar]").hidden = true;
    actualizarBotones();

    // Tab recorre todos los campos. Las flechas verticales cambian de fila;
    // las horizontales solo cambian de celda al llegar al extremo del texto.
    lista.addEventListener("keydown", event => {
        const input = event.target;
        if (input.tagName !== "INPUT" || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
        const deltas = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
        const delta = deltas[event.key];
        if (!delta || input.selectionStart !== input.selectionEnd) return;
        if (event.key === "ArrowLeft" && input.selectionStart !== 0) return;
        if (event.key === "ArrowRight" && input.selectionEnd !== input.value.length) return;
        const [, nombre, i, j] = input.name.split("_");
        const destino = lista.querySelector(`[name="celda_${nombre}_${Number(i) + delta[0]}_${Number(j) + delta[1]}"]`);
        if (destino) {
            event.preventDefault();
            destino.focus();
        }
    });
})();
