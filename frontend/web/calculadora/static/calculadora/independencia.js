(() => {
    "use strict";

    const entrada = document.querySelector("[data-independencia]");
    if (!entrada) return;
    const { dimensionValida, validarDimension, crearCuadricula, moverEntreCeldas, activarPasos } = window.entradasSeguras;
    const [dimension, cantidad] = ["dimension", "cantidad"].map(nombre => entrada.querySelector(`[name="${nombre}"]`));
    const vectores = entrada.querySelector("#vector-entry");
    const estado = entrada.querySelector("[data-presupuesto-vectores]");
    const maximo = Number(estado.dataset.presupuestoVectores);
    const memoria = new Map();

    function actualizar(redibujar) {
        const correctas = [dimension, cantidad].map(campo => validarDimension(campo)).every(Boolean);
        const componentes = Number(dimension.value);
        const total = Number(cantidad.value);
        const excedido = dimensionValida(dimension) && dimensionValida(cantidad) && componentes * (total + 1) > maximo;
        estado.textContent = excedido
            ? `Reduce la cantidad de vectores o componentes. La matriz aumentada admite hasta ${maximo} celdas.`
            : "";
        if (!correctas || excedido || !redibujar) return;

        const anteriores = [...vectores.querySelectorAll("table")];
        vectores.querySelectorAll("input").forEach(celda => memoria.set(celda.name, celda.value));
        const nuevas = Array.from({ length: total }, (_, indice) =>
            crearCuadricula(`v${indice + 1}`, componentes, 1, memoria, true));
        vectores.replaceChildren(...nuevas);
        nuevas.forEach((vector, indice) => {
            if (anteriores[indice]) {
                window.seleccionMatricial.redimensionar(anteriores[indice], vector.querySelector("table"));
            }
        });
    }

    for (const campo of [dimension, cantidad]) {
        campo.addEventListener("input", () => actualizar(true));
    }
    const aplicar = entrada.querySelector("[data-aplicar]");
    aplicar.disabled = aplicar.hidden = true;
    activarPasos(entrada);
    moverEntreCeldas(vectores);
    actualizar(false);
})();
