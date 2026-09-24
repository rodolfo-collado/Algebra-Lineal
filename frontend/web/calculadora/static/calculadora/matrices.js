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
    const cantidad = root.querySelector('[name="cantidad"]');
    const agregar = root.querySelector('[data-agregar-matriz]');
    let operacionAnterior = root.querySelector('[name="operacion"]:checked').value;

    function nombreMatriz(indice) {
        let nombre = "";
        for (indice += 1; indice > 0; indice = Math.floor((indice - 1) / 26)) {
            nombre = String.fromCharCode(65 + (indice - 1) % 26) + nombre;
        }
        return nombre;
    }

    function dimensionAdicional(nombre) {
        const clave = `columnas_${nombre.toLowerCase()}`;
        if (!dimensiones[clave]) {
            const campo = dimensiones.columnas_b.cloneNode(true);
            campo.dataset.dimension = clave;
            const input = campo.querySelector('input');
            input.name = clave;
            input.id = `id_${clave}`;
            input.value = "2";
            campo.querySelector('label').htmlFor = input.id;
            campo.querySelectorAll('.errorlist').forEach(nodo => nodo.remove());
            campo.querySelectorAll('button').forEach(button => {
                button.setAttribute('aria-label', `${Number(button.dataset.paso) < 0 ? 'Quitar' : 'Agregar'} una columna de ${nombre}`);
                activarStepper(button);
            });
            input.addEventListener('input', render);
            dimensiones[clave] = campo;
            dimensiones.columnas_b.parentElement.append(campo);
        }
        return clave;
    }

    function entrada(nombre) {
        return dimensiones[nombre].querySelector("input");
    }

    function opcionActual() {
        const operacion = root.querySelector('[name="operacion"]:checked').value;
        const opcion = JSON.parse(JSON.stringify(opciones[operacion]));
        if (opcion.aridad[1] !== null) return opcion;
        const total = Math.max(2, Number(cantidad.value) || 2);
        opcion.matrices = Array.from({length: total}, (_, i) => nombreMatriz(i));
        opcion.matrices.slice(2).forEach((nombre, i) => {
            if (operacion === "producto") {
                const clave = dimensionAdicional(nombre);
                opcion.formas[nombre] = [`columnas_${nombreMatriz(i + 1).toLowerCase()}`, clave];
                opcion.dimensiones.push([clave, `Columnas de ${nombre}`]);
            } else opcion.formas[nombre] = ["filas", "columnas"];
        });
        return opcion;
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
        cantidad.disabled = opcion.aridad[1] !== null;
        agregar.hidden = cantidad.disabled;
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
        if (opcion.matrices.length > 2) {
            return opcion.matrices.map(nombre => `${nombre}: ${forma(opcion, nombre).slice(0, 2).join("×")}`).join(" · ");
        }
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
        controlesOperandos(opcion);
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

    function controlesOperandos(opcion) {
        actualizarEstructura(opcion);
        if (opcion.aridad[1] !== null) return;
        opcion.matrices.slice(2).forEach((nombre, offset) => {
            const quitar = document.createElement('button');
            quitar.type = 'button';
            quitar.className = 'stepper-btn';
            quitar.textContent = '×';
            quitar.setAttribute('aria-label', `Quitar matriz ${nombre}`);
            quitar.addEventListener('click', () => {
                guardar();
                const valores = new Map(memoria);
                const indice = offset + 2;
                for (let i = indice; i < opcion.matrices.length; i += 1) {
                    const actual = opcion.matrices[i];
                    const siguiente = opcion.matrices[i + 1];
                    for (const clave of memoria.keys()) {
                        if (clave.startsWith(`celda_${actual}_`)) memoria.delete(clave);
                    }
                    if (siguiente) {
                        for (const [clave, valor] of valores) {
                            if (clave.startsWith(`celda_${siguiente}_`)) memoria.set(clave.replace(`celda_${siguiente}_`, `celda_${actual}_`), valor);
                        }
                        const destino = dimensiones[`columnas_${actual.toLowerCase()}`];
                        const origen = dimensiones[`columnas_${siguiente.toLowerCase()}`];
                        if (destino && origen) destino.querySelector('input').value = origen.querySelector('input').value;
                    }
                }
                // Evitar que render vuelva a guardar los nombres anteriores.
                lista.replaceChildren();
                cantidad.value = String(opcion.matrices.length - 1);
                render();
            });
            lista.querySelector(`[data-matriz="${nombre}"]`).append(quitar);
        });
    }

    agregar.addEventListener('click', () => {
        cantidad.value = String(Number(cantidad.value) + 1);
        render();
    });
    root.querySelectorAll('[name="operacion"]').forEach(radio => radio.addEventListener("change", () => {
        if (opciones[radio.value].aridad[1] !== null || opciones[operacionAnterior].aridad[1] !== null) cantidad.value = "2";
        operacionAnterior = radio.value;
        render();
    }));
    Object.keys(dimensiones).forEach(nombre => entrada(nombre).addEventListener("input", render));
    function activarStepper(button) {
        button.hidden = false;
        button.addEventListener("click", () => {
            const input = button.closest(".stepper").querySelector("input");
            const actual = dimensionValida(input) ? Number(input.value) : Number(input.min);
            input.value = String(Math.min(Number(input.max), Math.max(Number(input.min), actual + Number(button.dataset.paso))));
            render();
        });
    }
    root.querySelectorAll(".stepper [data-paso]").forEach(activarStepper);
    root.addEventListener("input", ocultarResultado);
    root.querySelector("[data-aplicar]").hidden = true;
    actualizarBotones();
    controlesOperandos(opcionActual());

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
