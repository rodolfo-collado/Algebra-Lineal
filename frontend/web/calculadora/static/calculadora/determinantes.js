(() => {
    "use strict";

    // Solo interacción: el servidor valida y calcula. Igual que inversa.js, A
    // se redibuja con las plantillas inertes. Editar A invalida la elección;
    // «Desarrollar por» solo acompaña a Cofactores.
    const root = document.querySelector("[data-determinantes]");
    if (!root) return;
    const entrada = root.querySelector("[data-determinant-entry]");
    const orden = root.querySelector('[data-dimension="orden"] input');
    const radios = [...root.querySelectorAll('[name="metodo"]')];
    const eleccion = root.querySelector("[data-eleccion]");
    const boton = root.querySelector("[data-boton-determinante]");
    const expansion = root.querySelector("[data-expansion]");
    const selectorExpansion = expansion?.querySelector("select");
    const memoria = new Map();
    const { dimensionValida, validarDimension, crearCuadricula, moverEntreCeldas, activarPasos } = window.entradasSeguras;

    function guardar() {
        root.querySelectorAll('[name^="celda_"]').forEach(input => memoria.set(input.name, input.value));
    }

    function ocultarConfirmacion() {
        document.querySelectorAll("[data-confirmacion]").forEach(nodo => { nodo.hidden = true; });
    }

    function invalidarEleccion() {
        ocultarConfirmacion();
        const unicoElemento = Number(orden.value) === 1;
        boton.setAttribute("formaction", `${boton.form.action.split("#")[0]}#${unicoElemento ? "resultado" : "eleccion-determinante"}`);
        if (!eleccion || eleccion.hidden) return;
        eleccion.hidden = true;
        eleccion.querySelectorAll("input, select").forEach(campo => { campo.disabled = true; });
        boton.textContent = "Calcular determinante";
        root.querySelector("[data-estado-eleccion]").textContent = unicoElemento
            ? "Cambiaste A. Pulsa Calcular determinante para obtener su única entrada."
            : "Cambiaste A. Pulsa Calcular determinante para volver a analizarla.";
    }

    function actualizarExpansion() {
        if (!expansion || eleccion.hidden) return;
        const cofactores = radios.some(radio => radio.checked && radio.value === "cofactores");
        // Fuera de Cofactores no se envía: no es una decisión de ese método.
        expansion.hidden = !cofactores;
        selectorExpansion.disabled = !cofactores;
    }

    function render() {
        ocultarConfirmacion();
        invalidarEleccion();
        validarDimension(orden);
        // No se corrige en silencio un tamaño inválido: el servidor muestra el error.
        if (!dimensionValida(orden)) return;
        guardar();
        const n = Number(orden.value);
        const anterior = entrada.querySelector('[data-matriz="A"]');
        const nueva = crearCuadricula("A", n, n, memoria);
        anterior.replaceWith(nueva);
        window.seleccionMatricial.redimensionar(anterior.querySelector("table"), nueva.querySelector("table"));
        root.querySelector("[data-determinant-shape]").textContent = `A es ${n}×${n}. De ${orden.min} a ${orden.max} filas y columnas.`;
        validarDimension(orden);
    }

    orden.addEventListener("input", render);
    root.addEventListener("change", event => {
        ocultarConfirmacion();
        if (event.target.name === "metodo") actualizarExpansion();
        if (event.target === orden || event.target.name?.startsWith("celda_")) invalidarEleccion();
    });
    activarPasos(root);
    root.addEventListener("input", event => {
        ocultarConfirmacion();
        if (event.target === orden || event.target.name?.startsWith("celda_")) {
            invalidarEleccion();
        }
    });
    root.addEventListener("entrada-cambiada", invalidarEleccion);
    root.querySelectorAll("[data-aplicar]").forEach(button => { button.hidden = true; button.disabled = true; });
    actualizarExpansion();
    validarDimension(orden);

    window.addEventListener("load", () => {
        if (eleccion && !root.querySelector("[data-respuesta-errores]") &&
            !document.querySelector("[data-confirmacion], [data-resultado]")) {
            eleccion.focus({ preventScroll: true });
            eleccion.scrollIntoView({ block: "start" });
        }
    });

    moverEntreCeldas(root);
})();
