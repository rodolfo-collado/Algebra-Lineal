(() => {
    "use strict";

    const root = document.querySelector("[data-conversion-bases]");
    if (!root) return;

    const modos = root.querySelectorAll('input[name="modo"]');
    const bases = root.querySelectorAll('input[name="base"]');
    const teclados = root.querySelectorAll("[data-teclado-base]");
    const etiquetasNumero = root.querySelectorAll("[data-number-label-base]");
    const legendDesde = root.querySelector("[data-base-legend-desde]");
    const legendHacia = root.querySelector("[data-base-legend-hacia]");

    function modoActivo() {
        const marcado = root.querySelector('input[name="modo"]:checked');
        return marcado ? marcado.value : "desde_decimal";
    }

    function baseActiva() {
        const marcado = root.querySelector('input[name="base"]:checked');
        return marcado ? Number(marcado.value) : 2;
    }

    // Desde decimal se escribe en base 10; hacia decimal, en la base elegida.
    function baseEntrada() {
        return modoActivo() === "desde_decimal" ? 10 : baseActiva();
    }

    function actualizar() {
        const desde = modoActivo() === "desde_decimal";
        if (legendDesde) legendDesde.hidden = !desde;
        if (legendHacia) legendHacia.hidden = desde;

        const activa = baseEntrada();
        etiquetasNumero.forEach((etiqueta) => {
            etiqueta.hidden = Number(etiqueta.dataset.numberLabelBase) !== activa;
        });
        teclados.forEach((bloque) => {
            const corresponde = Number(bloque.dataset.tecladoBase) === activa;
            bloque.hidden = !corresponde;
            // El teclado interno nace hidden hasta que teclado.js lo revela;
            // al cambiar de base hay que volver a mostrar el contenedor activo.
            const teclado = bloque.querySelector(".math-keyboard");
            if (teclado && corresponde) teclado.hidden = false;
        });
    }

    modos.forEach((input) => input.addEventListener("change", actualizar));
    bases.forEach((input) => input.addEventListener("change", actualizar));
    actualizar();
})();
