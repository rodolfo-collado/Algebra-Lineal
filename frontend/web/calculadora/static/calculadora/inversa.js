(() => {
    "use strict";

    // Matriz inversa: A es n×n. Al cambiar n se regenera la cuadrícula con el mismo
    // marcado que entrega el servidor al pulsar Aplicar, conservando lo escrito, y el
    // método para matrices 2×2 solo queda disponible con n = 2 (el servidor también
    // lo exige). Editar oculta el resultado y el aviso de espera: ya no corresponden.
    const root = document.querySelector("[data-inversa]");
    if (!root) return;
    const entrada = root.querySelector("[data-inverse-entry]");
    const orden = root.querySelector('[data-dimension="orden"] input');
    const metodo2x2 = root.querySelector('[name="metodo"][value="directo_2x2"]');
    const gaussJordan = root.querySelector('[name="metodo"][value="gauss_jordan"]');
    const matrizTemplate = document.getElementById("matrix-entry-template");
    const celdaTemplate = document.getElementById("matrix-cell-template");
    const memoria = new Map();

    function guardar() {
        entrada.querySelectorAll("input").forEach(input => memoria.set(input.name, input.value));
    }

    function ordenValido() {
        const valor = Number(orden.value);
        return Number.isInteger(valor) && valor >= Number(orden.min) && valor <= Number(orden.max);
    }

    function ocultarSalida() {
        document.querySelectorAll("#resultado, [data-confirmacion]").forEach(nodo => { nodo.hidden = true; });
    }

    function crearMatriz(n) {
        // Las plantillas inertes comparten el marcado con la versión del servidor.
        const fragmento = matrizTemplate.content.cloneNode(true);
        const matriz = fragmento.querySelector("fieldset");
        matriz.dataset.matriz = "A";
        matriz.querySelector("[data-tipo-matriz]").textContent = "Matriz";
        matriz.querySelector("[data-nombre-matriz]").textContent = "A";
        matriz.querySelector("table").setAttribute("aria-label", "Matriz A");
        matriz.querySelector(".matrix-scroll").setAttribute("aria-label", "Entradas de la matriz A");
        const cuerpo = matriz.querySelector("tbody");
        for (let i = 0; i < n; i += 1) {
            const fila = document.createElement("tr");
            for (let j = 0; j < n; j += 1) {
                const celda = celdaTemplate.content.cloneNode(true);
                const input = celda.querySelector("input");
                input.name = `celda_A_${i}_${j}`;
                input.id = `id_${input.name}`;
                input.value = memoria.get(input.name) ?? "";
                const label = celda.querySelector("label");
                label.htmlFor = input.id;
                label.textContent = `Matriz A, fila ${i + 1}, columna ${j + 1}`;
                fila.append(celda);
            }
            cuerpo.append(fila);
        }
        return matriz;
    }

    // Una opción desactivada no viaja en el POST; si estaba elegida, vuelve Gauss-Jordan.
    function actualizarMetodos(n) {
        metodo2x2.disabled = n !== 2;
        if (metodo2x2.disabled && metodo2x2.checked) gaussJordan.checked = true;
    }

    function actualizarBotones() {
        root.querySelectorAll(".stepper [data-paso]").forEach(button => {
            const limite = Number(button.dataset.paso) < 0 ? orden.min : orden.max;
            button.disabled = Number(orden.value) === Number(limite);
        });
    }

    function render() {
        ocultarSalida();
        // No se corrige en silencio un tamaño inválido: el servidor muestra el error.
        if (!ordenValido()) return;
        guardar();
        const n = Number(orden.value);
        entrada.querySelector('[data-matriz="A"]').replaceWith(crearMatriz(n));
        actualizarMetodos(n);
        root.querySelector("[data-inverse-shape]").textContent = `A es ${n}×${n}. De ${orden.min} a ${orden.max} filas y columnas.`;
        actualizarBotones();
    }

    orden.addEventListener("input", render);
    root.querySelectorAll(".stepper [data-paso]").forEach(button => {
        button.hidden = false;
        button.addEventListener("click", () => {
            const actual = ordenValido() ? Number(orden.value) : Number(orden.min);
            orden.value = String(Math.min(Number(orden.max), Math.max(Number(orden.min), actual + Number(button.dataset.paso))));
            render();
        });
    });
    root.addEventListener("input", ocultarSalida);
    root.querySelector("[data-aplicar]").hidden = true;
    actualizarBotones();

    // Tab recorre todos los campos. Las flechas verticales cambian de fila;
    // las horizontales solo cambian de celda al llegar al extremo del texto.
    entrada.addEventListener("keydown", event => {
        const input = event.target;
        if (input.tagName !== "INPUT" || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
        const deltas = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
        const delta = deltas[event.key];
        if (!delta || input.selectionStart !== input.selectionEnd) return;
        if (event.key === "ArrowLeft" && input.selectionStart !== 0) return;
        if (event.key === "ArrowRight" && input.selectionEnd !== input.value.length) return;
        const [, , i, j] = input.name.split("_");
        const destino = entrada.querySelector(`[name="celda_A_${Number(i) + delta[0]}_${Number(j) + delta[1]}"]`);
        if (destino) {
            event.preventDefault();
            destino.focus();
        }
    });
})();
