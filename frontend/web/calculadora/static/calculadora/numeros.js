(() => {
    "use strict";
    const controls = document.querySelector("[data-numeric-controls]");
    if (!controls) return;
    const result = controls.closest("#resultado");
    const mode = controls.querySelector("[data-numeric-mode]");
    const precision = controls.querySelector("[data-numeric-precision]");
    const label = controls.querySelector("[data-numeric-precision-label]");
    const notice = controls.querySelector("[data-numeric-notice]");
    const numbers = Array.from(result.querySelectorAll("[data-numeric]"), node =>
        ({node, data: JSON.parse(node.dataset.numeric)}));
    const attributes = Array.from(result.querySelectorAll("[data-numeric-attributes]"), node =>
        ({node, data: JSON.parse(node.dataset.numericAttributes)}));
    // tema_inicial.html: localStorage en la sesión y, en escritorio, el archivo propio.
    const preferencias = window.preferencias;

    function apply() {
        const decimal = mode.value === "decimal";
        let approximate = false;
        function text(data) {
            if (!decimal) return data.exacto;
            approximate ||= data.aproximados.includes(precision.value);
            return data.decimales[precision.value];
        }
        numbers.forEach(({node, data}) => {
            const valor = text(data);
            if (node.textContent !== valor) node.textContent = valor;
        });
        attributes.forEach(({node, data}) => {
            Object.entries(data).forEach(([attribute, value]) => node.setAttribute(attribute, text(value)));
        });
        label.hidden = precision.hidden = !decimal;
        const aviso = approximate
            ? `Valores decimales aproximados a ${precision.value} decimales. Los cálculos conservan su valor exacto.`
            : "";
        // Repetir el mismo texto en la región viva lo volvería a anunciar.
        if (notice.textContent !== aviso) notice.textContent = aviso;
    }
    // Solo representación: no envía formularios, no recalcula ni emite input/change.
    function sincronizar() {
        const savedMode = preferencias.leer("pygebra-formato-numerico");
        const savedPrecision = preferencias.leer("pygebra-precision-decimal");
        if (["exacto", "decimal"].includes(savedMode)) mode.value = savedMode;
        if (["2", "4", "6", "8"].includes(savedPrecision)) precision.value = savedPrecision;
        apply();
    }
    function change() {
        apply();
        preferencias.guardar("pygebra-formato-numerico", mode.value);
        preferencias.guardar("pygebra-precision-decimal", precision.value);
    }
    controls.hidden = false;
    mode.addEventListener("change", change);
    precision.addEventListener("change", change);
    // Una página restaurada del historial vuelve con la preferencia vigente, no con la de entonces.
    window.addEventListener("pageshow", event => {
        if (event.persisted) sincronizar();
    });
    sincronizar();
})();
