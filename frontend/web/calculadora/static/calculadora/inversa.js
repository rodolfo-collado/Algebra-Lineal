(() => {
    "use strict";

    // Solo interacción: el servidor valida y realiza toda la aritmética. A fija
    // el tamaño de B/b y el método solo se elige en 2×2. Las plantillas inertes
    // comparten el marcado del flujo sin JavaScript mediante Aplicar.
    const root = document.querySelector("[data-inversa]");
    if (!root) return;
    const entrada = root.querySelector("[data-inverse-entry]");
    const orden = root.querySelector('[data-dimension="orden"] input');
    const metodos = root.querySelector("[data-inverse-method]");
    const adicional = root.querySelector("[data-inverse-additional-entry]");
    const metodoTemplate = document.getElementById("inverse-method-template");
    const matrizTemplate = document.getElementById("matrix-entry-template");
    const celdaTemplate = document.getElementById("matrix-cell-template");
    const memoria = new Map();
    const { dimensionValida, validarDimension } = window.entradasSeguras;

    function guardar() {
        root.querySelectorAll('[name^="celda_"]').forEach(input => memoria.set(input.name, input.value));
    }

    function ordenValido() {
        return dimensionValida(orden);
    }

    function ocultarConfirmacion() {
        document.querySelectorAll("[data-confirmacion]").forEach(nodo => { nodo.hidden = true; });
    }

    function crearMatriz(nombre, n, vector = false) {
        // Las plantillas inertes comparten el marcado con la versión del servidor.
        const fragmento = matrizTemplate.content.cloneNode(true);
        const matriz = fragmento.querySelector("fieldset");
        matriz.dataset.matriz = nombre;
        if (vector) matriz.dataset.vector = "";
        matriz.querySelector("[data-tipo-matriz]").textContent = vector ? "Vector" : "Matriz";
        matriz.querySelector("[data-nombre-matriz]").textContent = nombre;
        matriz.querySelector("table").setAttribute("aria-label", `${vector ? "Vector" : "Matriz"} ${nombre}`);
        matriz.querySelector(".matrix-scroll").setAttribute("aria-label", `${vector ? "Componentes del vector" : "Entradas de la matriz"} ${nombre}`);
        const cuerpo = matriz.querySelector("tbody");
        for (let i = 0; i < n; i += 1) {
            const fila = document.createElement("tr");
            for (let j = 0; j < (vector ? 1 : n); j += 1) {
                const celda = celdaTemplate.content.cloneNode(true);
                const input = celda.querySelector("input");
                input.name = `celda_${nombre}_${i}_${j}`;
                input.id = `id_${input.name}`;
                input.value = memoria.get(input.name) ?? "";
                const label = celda.querySelector("label");
                label.htmlFor = input.id;
                label.textContent = vector
                    ? `Vector ${nombre}, componente ${i + 1}`
                    : `Matriz ${nombre}, fila ${i + 1}, columna ${j + 1}`;
                fila.append(celda);
            }
            cuerpo.append(fila);
        }
        return matriz;
    }

    function actualizarMetodos(n) {
        if (n !== 2) {
            // Eliminar los radios evita controles ocultos enfocables y hace
            // imposible restaurar el método directo al regresar a 2×2.
            const automatico = document.createElement("input");
            automatico.type = "hidden";
            automatico.name = "metodo";
            automatico.value = "gauss_jordan";
            metodos.replaceChildren(automatico);
            metodos.hidden = true;
        } else {
            if (!metodos.querySelector('[name="metodo"][value="directo_2x2"]')) {
                metodos.replaceChildren(metodoTemplate.content.cloneNode(true));
                metodos.querySelectorAll('[name="metodo"]').forEach((radio, i) => {
                    const label = metodos.querySelector(`label[for="${radio.id}"]`);
                    radio.id = `id_metodo_${i}`;
                    if (label) label.htmlFor = radio.id;
                });
                metodos.querySelector('[name="metodo"][value="gauss_jordan"]').checked = true;
                metodos.querySelector('[name="metodo"][value="directo_2x2"]').checked = false;
            }
            metodos.hidden = false;
        }
    }

    function actualizarAdicional(n) {
        const funcion = root.querySelector('[name="funcion_adicional"]:checked')?.value ?? "ninguna";
        // Se retiran las entradas inactivas del DOM y del POST. La memoria
        // local permite recuperar lo escrito al cambiar temporalmente de radio.
        adicional.replaceChildren();
        if (funcion === "producto") adicional.append(crearMatriz("B", n));
        if (funcion === "vector") adicional.append(crearMatriz("b", n, true));
        adicional.hidden = funcion !== "producto" && funcion !== "vector";
    }

    function actualizarBotones() {
        validarDimension(orden);
    }

    function render() {
        ocultarConfirmacion();
        actualizarBotones();
        // No se corrige en silencio un tamaño inválido: el servidor muestra el error.
        if (!ordenValido()) return;
        guardar();
        const n = Number(orden.value);
        entrada.querySelector('[data-matriz="A"]').replaceWith(crearMatriz("A", n));
        actualizarAdicional(n);
        actualizarMetodos(n);
        root.querySelector("[data-inverse-shape]").textContent = `A es ${n}×${n}. De ${orden.min} a ${orden.max} filas y columnas.`;
        actualizarBotones();
    }

    orden.addEventListener("input", render);
    root.addEventListener("change", event => {
        ocultarConfirmacion();
        if (event.target.name !== "funcion_adicional" || !ordenValido()) return;
        guardar();
        actualizarAdicional(Number(orden.value));
    });
    root.querySelectorAll(".stepper [data-paso]").forEach(button => {
        button.hidden = false;
        button.addEventListener("click", () => {
            const actual = ordenValido() ? Number(orden.value) : Number(orden.min);
            orden.value = String(Math.min(Number(orden.max), Math.max(Number(orden.min), actual + Number(button.dataset.paso))));
            orden.dispatchEvent(new Event("input", { bubbles: true }));
        });
    });
    root.addEventListener("input", ocultarConfirmacion);
    root.querySelectorAll("[data-aplicar]").forEach(button => { button.hidden = true; button.disabled = true; });
    if (ordenValido()) actualizarMetodos(Number(orden.value));
    actualizarBotones();

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
