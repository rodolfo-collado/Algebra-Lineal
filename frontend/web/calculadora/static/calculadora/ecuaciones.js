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
    const memoria = new Map();
    const { dimensionValida, validarDimension, crearCuadricula, moverEntreCeldas, activarPasos } = window.entradasSeguras;
    const SUBINDICES = "₀₁₂₃₄₅₆₇₈₉";
    const cramer = root.querySelector('[name="metodo"][value="cramer"]');
    const metodosDeterminantes = root.querySelector("[data-cramer-methods]");

    function actualizarMetodos() {
        if (!cramer) return;
        if (!Object.keys(dimensiones).every(nombre => dimensionValida(campo(nombre)))) return;
        const m = Number(campo("filas").value);
        const n = Number(campo("columnas").value);
        cramer.disabled = m !== n;
        if (cramer.disabled && cramer.checked) root.querySelector('[name="metodo"][value="gauss_jordan"]').checked = true;
        metodosDeterminantes.hidden = !cramer.checked;
        window.metodosDeterminantes.actualizar([...metodosDeterminantes.querySelectorAll("input")], m);
    }

    function campo(nombre) {
        return dimensiones[nombre].querySelector("input");
    }

    function subindice(numero) {
        return String(numero).replace(/\d/g, digito => SUBINDICES[Number(digito)]);
    }

    function guardar() {
        entrada.querySelectorAll("input").forEach(input => memoria.set(input.name, input.value));
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
        const anterior = entrada.querySelector('[data-matriz="A"]');
        const nueva = crearCuadricula("A", m, n, memoria);
        anterior.replaceWith(nueva);
        window.seleccionMatricial.redimensionar(anterior.querySelector("table"), nueva.querySelector("table"));
        entrada.querySelector('[data-matriz="b"]').replaceWith(crearCuadricula("b", m, 1, memoria, true));
        actualizarIncognita(n);
        root.querySelector("[data-equation-shape]").textContent = `A (${m}×${n}) · x (${n}) = b (${m}). De ${campo("filas").min} a ${campo("filas").max} filas y columnas.`;
        actualizarBotones();
        actualizarMetodos();
    }

    Object.keys(dimensiones).forEach(nombre => campo(nombre).addEventListener("input", render));
    activarPasos(root);
    root.querySelector("[data-aplicar]").hidden = true;
    root.querySelector("[data-aplicar]").disabled = true;
    actualizarBotones();
    actualizarMetodos();
    root.addEventListener("change", event => {
        if (event.target.name === "metodo") actualizarMetodos();
    });

    moverEntreCeldas(entrada);
})();
