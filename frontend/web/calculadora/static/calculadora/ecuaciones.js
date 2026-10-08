(() => {
    "use strict";

    // Resolver Ax = b: A (m×n) y b (m) se editan; x (n) solo se muestra. Al cambiar
    // las dimensiones de A se regeneran las tres piezas con el mismo marcado que
    // entrega el servidor al pulsar Aplicar, conservando las celdas escritas.
    const root = document.querySelector("[data-ecuacion]");
    if (!root) return;
    const entrada = root.querySelector("[data-equation-entry]");
    const incognita = root.querySelector("[data-unknown]");
    const dimensiones = {};
    root.querySelectorAll("[data-dimension]").forEach(campo => { dimensiones[campo.dataset.dimension] = campo; });
    const matrizTemplate = document.getElementById("matrix-entry-template");
    const celdaTemplate = document.getElementById("matrix-cell-template");
    const memoria = new Map();
    const { dimensionValida, validarDimension } = window.entradasSeguras;
    const SUBINDICES = "₀₁₂₃₄₅₆₇₈₉";

    function campo(nombre) {
        return dimensiones[nombre].querySelector("input");
    }

    function subindice(numero) {
        return String(numero).replace(/\d/g, digito => SUBINDICES[Number(digito)]);
    }

    function guardar() {
        entrada.querySelectorAll("input").forEach(input => memoria.set(input.name, input.value));
    }

    function crearMatriz(nombre, m, n, vector) {
        // Las plantillas inertes comparten el marcado con la versión del servidor.
        const fragmento = matrizTemplate.content.cloneNode(true);
        const matriz = fragmento.querySelector("fieldset");
        const tipo = vector ? "Vector" : "Matriz";
        matriz.dataset.matriz = nombre;
        matriz.toggleAttribute("data-vector", vector);
        matriz.querySelector("[data-tipo-matriz]").textContent = tipo;
        matriz.querySelector("[data-nombre-matriz]").textContent = nombre;
        matriz.querySelector("table").setAttribute("aria-label", `${tipo} ${nombre}`);
        matriz.querySelector(".matrix-scroll").setAttribute("aria-label", vector ? `Componentes del vector ${nombre}` : `Entradas de la matriz ${nombre}`);
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
                label.textContent = vector ? `Vector ${nombre}, componente ${i + 1}` : `Matriz ${nombre}, fila ${i + 1}, columna ${j + 1}`;
                fila.append(celda);
            }
            cuerpo.append(fila);
        }
        return matriz;
    }

    // El vector incógnita no tiene celdas: una fila x₁, x₂, … por columna de A.
    function actualizarIncognita(n) {
        const cuerpo = incognita.querySelector("tbody");
        cuerpo.replaceChildren();
        for (let k = 1; k <= n; k += 1) {
            const fila = document.createElement("tr");
            const celda = document.createElement("td");
            celda.textContent = `x${subindice(k)}`;
            fila.append(celda);
            cuerpo.append(fila);
        }
        const ayuda = incognita.querySelector("[data-unknown-help]");
        if (ayuda) ayuda.textContent = `x tiene ${n} componente${n === 1 ? "" : "s"} desconocida${n === 1 ? "" : "s"}; se determinan al resolver.`;
    }

    function actualizarBotones() {
        Object.keys(dimensiones).forEach(nombre => validarDimension(campo(nombre)));
    }

    function render() {
        actualizarBotones();
        // No se corrigen silenciosamente dimensiones inválidas: el servidor
        // muestra el error. Mientras se escribe, se conserva la ecuación.
        if (!Object.keys(dimensiones).every(nombre => dimensionValida(campo(nombre)))) return;
        guardar();
        const m = Number(campo("filas").value);
        const n = Number(campo("columnas").value);
        entrada.querySelector('[data-matriz="A"]').replaceWith(crearMatriz("A", m, n, false));
        entrada.querySelector('[data-matriz="b"]').replaceWith(crearMatriz("b", m, 1, true));
        actualizarIncognita(n);
        root.querySelector("[data-equation-shape]").textContent = `A (${m}×${n}) · x (${n}) = b (${m}). De ${campo("filas").min} a ${campo("filas").max} filas y columnas.`;
        actualizarBotones();
    }

    Object.keys(dimensiones).forEach(nombre => campo(nombre).addEventListener("input", render));
    root.querySelectorAll(".stepper [data-paso]").forEach(button => {
        button.hidden = false;
        button.addEventListener("click", () => {
            const input = button.closest(".stepper").querySelector("input");
            const actual = dimensionValida(input) ? Number(input.value) : Number(input.min);
            input.value = String(Math.min(Number(input.max), Math.max(Number(input.min), actual + Number(button.dataset.paso))));
            input.dispatchEvent(new Event("input", { bubbles: true }));
        });
    });
    root.querySelector("[data-aplicar]").hidden = true;
    root.querySelector("[data-aplicar]").disabled = true;
    actualizarBotones();

    // Tab recorre todos los campos. Las flechas verticales cambian de fila;
    // las horizontales solo cambian de celda al llegar al extremo del texto.
    entrada.addEventListener("keydown", event => {
        const input = event.target;
        if (!window.entradasSeguras.flechaDeCelda(event)) return;
        const deltas = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
        const delta = deltas[event.key];
        if (!delta) return;
        const [, nombre, i, j] = input.name.split("_");
        const destino = entrada.querySelector(`[name="celda_${nombre}_${Number(i) + delta[0]}_${Number(j) + delta[1]}"]`);
        if (destino && !destino.readOnly && !destino.matches(":disabled")) {
            event.preventDefault();
            destino.focus();
        }
    });
})();
