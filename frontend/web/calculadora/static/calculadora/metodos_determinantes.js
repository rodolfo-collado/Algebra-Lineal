(() => {
    "use strict";

    // Disponibilidad y sugerencia vienen de RadiosPorTamano, compartido por ambos formularios.
    window.metodosDeterminantes = {
        actualizar(radios, n) {
            radios.forEach(radio => {
                const disponible = radio.dataset.orden ? Number(radio.dataset.orden) === n :
                    !radio.dataset.ordenMaximo || n <= Number(radio.dataset.ordenMaximo);
                radio.disabled = !disponible;
                radio.closest("label").hidden = !disponible;
            });
            if (!radios.some(radio => radio.checked && !radio.disabled)) {
                radios.find(radio => radio.dataset.sugerido.split(",").includes(String(n))).checked = true;
            }
        },
    };
})();
