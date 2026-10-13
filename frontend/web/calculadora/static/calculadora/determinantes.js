(() => {
    "use strict";

    // Solo interacción: el servidor valida y calcula. Igual que inversa.js, A
    // se redibuja con las plantillas inertes; aquí además cada método se
    // muestra solo si existe para el tamaño de A (data-orden, data-orden-maximo)
    // y «Desarrollar por» solo acompaña a Cofactores.
    const root = document.querySelector("[data-determinantes]");
    if (!root) return;
    const entrada = root.querySelector("[data-determinant-entry]");
    const orden = root.querySelector('[data-dimension="orden"] input');
    const radios = [...root.querySelectorAll('[name="metodo"]')];
    const expansion = root.querySelector("[data-expansion]");
    const selectorExpansion = expansion.querySelector("select");
    const matrizTemplate = document.getElementById("matrix-entry-template");
    const celdaTemplate = document.getElementById("matrix-cell-template");
    const memoria = new Map();
    const { dimensionValida, validarDimension } = window.entradasSeguras;

    function guardar() {
        root.querySelectorAll('[name^="celda_"]').forEach(input => memoria.set(input.name, input.value));
    }

    function ocultarConfirmacion() {
        document.querySelectorAll("[data-confirmacion]").forEach(nodo => { nodo.hidden = true; });
    }

    function crearMatriz(n) {
        const matriz = matrizTemplate.content.cloneNode(true).querySelector("fieldset");
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

    function actualizarMetodos(n) {
        window.metodosDeterminantes.actualizar(radios, n);
    }

    function actualizarExpansion(n) {
        if (n !== undefined && selectorExpansion.options.length !== 2 * n + 1) {
            const anterior = selectorExpansion.value;
            const opciones = [["auto", "Automático"]];
            for (const eje of ["fila", "columna"]) {
                for (let i = 1; i <= n; i += 1) opciones.push([`${eje}_${i}`, `${eje === "fila" ? "Fila" : "Columna"} ${i}`]);
            }
            selectorExpansion.replaceChildren(...opciones.map(([valor, texto]) => new Option(texto, valor)));
            selectorExpansion.value = opciones.some(([valor]) => valor === anterior) ? anterior : "auto";
        }
        const cofactores = radios.some(radio => radio.checked && radio.value === "cofactores");
        // Fuera de Cofactores no se envía: no es una decisión de ese método.
        expansion.hidden = !cofactores;
        selectorExpansion.disabled = !cofactores;
    }

    function render() {
        ocultarConfirmacion();
        validarDimension(orden);
        // No se corrige en silencio un tamaño inválido: el servidor muestra el error.
        if (!dimensionValida(orden)) return;
        guardar();
        const n = Number(orden.value);
        const anterior = entrada.querySelector('[data-matriz="A"]');
        const nueva = crearMatriz(n);
        anterior.replaceWith(nueva);
        window.seleccionMatricial.redimensionar(anterior.querySelector("table"), nueva.querySelector("table"));
        actualizarMetodos(n);
        actualizarExpansion(n);
        root.querySelector("[data-determinant-shape]").textContent = `A es ${n}×${n}. De ${orden.min} a ${orden.max} filas y columnas.`;
        validarDimension(orden);
    }

    orden.addEventListener("input", render);
    root.addEventListener("change", event => {
        ocultarConfirmacion();
        if (event.target.name === "metodo") actualizarExpansion();
    });
    root.querySelectorAll(".stepper [data-paso]").forEach(button => {
        button.hidden = false;
        button.addEventListener("click", () => {
            const actual = dimensionValida(orden) ? Number(orden.value) : Number(orden.min);
            orden.value = String(Math.min(Number(orden.max), Math.max(Number(orden.min), actual + Number(button.dataset.paso))));
            orden.dispatchEvent(new Event("input", { bubbles: true }));
        });
    });
    root.addEventListener("input", ocultarConfirmacion);
    root.querySelectorAll("[data-aplicar]").forEach(button => { button.hidden = true; button.disabled = true; });
    actualizarExpansion();
    validarDimension(orden);

    // Tab recorre todos los campos. Las flechas verticales cambian de fila;
    // las horizontales solo cambian de celda al llegar al extremo del texto.
    root.addEventListener("keydown", event => {
        const input = event.target;
        if (!window.entradasSeguras.flechaDeCelda(event) || !input.name.startsWith("celda_")) return;
        const deltas = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
        const delta = deltas[event.key];
        if (!delta) return;
        const [, nombre, i, j] = input.name.split("_");
        const destino = root.querySelector(`[name="celda_${nombre}_${Number(i) + delta[0]}_${Number(j) + delta[1]}"]`);
        if (destino && !destino.readOnly && !destino.matches(":disabled")) {
            event.preventDefault();
            destino.focus();
        }
    });
})();
