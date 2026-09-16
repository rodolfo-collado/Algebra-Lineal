(() => {
    "use strict";

    const root = document.querySelector("[data-matrices]");
    if (!root) return;
    const opciones = JSON.parse(document.getElementById("matrix-options").textContent);
    const lista = root.querySelector("[data-matrix-list]");
    const escalar = root.querySelector("[data-matrix-scalar]");
    const metodos = root.querySelector("[data-metodos]");
    const dimensiones = {};
    root.querySelectorAll("[data-dimension]").forEach(campo => { dimensiones[campo.dataset.dimension] = campo; });
    const matrizTemplate = document.getElementById("matrix-entry-template");
    const celdaTemplate = document.getElementById("matrix-cell-template");
    const escalarTemplate = document.getElementById("matrix-scalar-template");
    const memoria = new Map();
    let valorEscalar = "";

    function entrada(nombre) {
        return dimensiones[nombre].querySelector("input");
    }

    function opcionActual() {
        return opciones[root.querySelector('[name="operacion"]:checked').value];
    }

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

    // (filas, columnas, es vector) de una entrada según la operación: en AB las
    // filas de B son las columnas de A; el vector x es una columna de n componentes.
    function forma(opcion, nombre) {
        const [campoFilas, campoColumnas] = opcion.formas[nombre];
        const filas = Number(entrada(campoFilas).value);
        return [filas, campoColumnas ? Number(entrada(campoColumnas).value) : 1, !campoColumnas];
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

    // Los controles que la operación no usa se deshabilitan (no viajan en el
    // POST) y se ocultan; las etiquetas cambian: «Filas» en suma, «Filas de A» en AB.
    function actualizarEstructura(opcion) {
        const etiquetas = new Map(opcion.dimensiones);
        Object.entries(dimensiones).forEach(([nombre, campo]) => {
            const activo = etiquetas.has(nombre);
            campo.hidden = !activo;
            entrada(nombre).disabled = !activo;
            if (activo) campo.querySelector("label").textContent = etiquetas.get(nombre);
        });
        const conMetodo = opcion.metodos.length > 0;
        metodos.hidden = !conMetodo;
        metodos.querySelectorAll("input").forEach(radio => { radio.disabled = !conMetodo; });
        opcion.metodos.forEach(([valor, etiqueta]) => {
            const span = metodos.querySelector(`[data-etiqueta-metodo="${valor}"]`);
            if (span) span.textContent = etiqueta;
        });
        metodos.querySelector("[data-metodos-ayuda]").textContent = opcion.ayuda_metodos;
    }

    function textoForma(opcion) {
        const valores = { m: entrada("filas").value, n: entrada("columnas").value, p: entrada("columnas_b").value };
        return opcion.forma_texto.replace(/\{([mnp])\}/g, (_, clave) => valores[clave]);
    }

    function render() {
        ocultarResultado();
        const opcion = opcionActual();
        actualizarEstructura(opcion);
        // No se corrigen silenciosamente dimensiones inválidas: el servidor
        // muestra el error. Mientras se escribe, se conserva la cuadrícula.
        if (!opcion.dimensiones.every(([nombre]) => dimensionValida(entrada(nombre)))) return;
        guardar();
        lista.replaceChildren(...opcion.matrices.map(nombre => crearMatriz(nombre, ...forma(opcion, nombre))));
        escalar.replaceChildren();
        if (opcion.escalar) {
            escalar.append(escalarTemplate.content.cloneNode(true));
            escalar.querySelector("input").value = valorEscalar;
        }
        root.querySelector("[data-operation-help]").textContent = opcion.ayuda;
        const filas = entrada("filas");
        root.querySelector("[data-matrix-shape]").textContent = `${textoForma(opcion)} De ${filas.min} a ${filas.max} filas y columnas.`;
        actualizarBotones();
    }

    root.querySelectorAll('[name="operacion"]').forEach(radio => radio.addEventListener("change", render));
    Object.keys(dimensiones).forEach(nombre => entrada(nombre).addEventListener("input", render));
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
