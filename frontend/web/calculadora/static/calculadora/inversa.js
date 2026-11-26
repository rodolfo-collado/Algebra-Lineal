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
    const memoria = new Map();
    const { dimensionValida, validarDimension, crearCuadricula, moverEntreCeldas, activarPasos } = window.entradasSeguras;

    function guardar() {
        root.querySelectorAll('[name^="celda_"]').forEach(input => memoria.set(input.name, input.value));
    }

    function ordenValido() {
        return dimensionValida(orden);
    }

    function ocultarConfirmacion() {
        document.querySelectorAll("[data-confirmacion]").forEach(nodo => { nodo.hidden = true; });
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

    function actualizarAdicional(n, conservar = false) {
        const funcion = root.querySelector('[name="funcion_adicional"]:checked')?.value ?? "ninguna";
        // Se retiran las entradas inactivas del DOM y del POST. La memoria
        // local permite recuperar lo escrito al cambiar temporalmente de radio.
        const anterior = adicional.querySelector("table");
        adicional.replaceChildren();
        if (funcion === "producto") adicional.append(crearCuadricula("B", n, n, memoria));
        if (funcion === "vector") adicional.append(crearCuadricula("b", n, 1, memoria, true));
        adicional.hidden = funcion !== "producto" && funcion !== "vector";
        const nueva = adicional.querySelector("table");
        if (conservar && anterior && nueva) window.seleccionMatricial.redimensionar(anterior, nueva);
        else window.seleccionMatricial.sincronizar();
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
        const anterior = entrada.querySelector('[data-matriz="A"]');
        const nueva = crearCuadricula("A", n, n, memoria);
        anterior.replaceWith(nueva);
        window.seleccionMatricial.redimensionar(anterior.querySelector("table"), nueva.querySelector("table"));
        actualizarAdicional(n, true);
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
    activarPasos(root);
    root.addEventListener("input", ocultarConfirmacion);
    root.querySelectorAll("[data-aplicar]").forEach(button => { button.hidden = true; button.disabled = true; });
    if (ordenValido()) actualizarMetodos(Number(orden.value));
    actualizarBotones();

    moverEntreCeldas(root);
})();
