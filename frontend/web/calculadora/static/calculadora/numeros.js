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

    try {
        const savedMode = localStorage.getItem("pygebra-formato-numerico");
        const savedPrecision = localStorage.getItem("pygebra-precision-decimal");
        if (savedMode === "decimal") mode.value = savedMode;
        if (["2", "4", "6", "8"].includes(savedPrecision)) precision.value = savedPrecision;
    } catch (_) {
        // El HTML y la preferencia predeterminada son exactos.
    }

    function apply() {
        const decimal = mode.value === "decimal";
        let approximate = false;
        function text(data) {
            if (!decimal) return data.exacto;
            approximate ||= data.aproximados.includes(precision.value);
            return data.decimales[precision.value];
        }
        numbers.forEach(({node, data}) => { node.textContent = text(data); });
        attributes.forEach(({node, data}) => {
            Object.entries(data).forEach(([attribute, value]) => node.setAttribute(attribute, text(value)));
        });
        label.hidden = precision.hidden = !decimal;
        notice.textContent = approximate
            ? `Valores decimales aproximados a ${precision.value} decimales. Los cálculos conservan su valor exacto.`
            : "";
    }
    function change() {
        apply();
        try {
            localStorage.setItem("pygebra-formato-numerico", mode.value);
            localStorage.setItem("pygebra-precision-decimal", precision.value);
        } catch (_) {
            // El cambio visible funciona aunque la preferencia no pueda guardarse.
        }
    }
    controls.hidden = false;
    mode.addEventListener("change", change);
    precision.addEventListener("change", change);
    apply();
})();
