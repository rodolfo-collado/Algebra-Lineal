(() => {
    "use strict";

    document.querySelectorAll("[data-iterativo]").forEach(panel => {
        const control = panel.querySelector("[data-iterativo-selector]");
        if (!control) return;
        const filas = JSON.parse(document.getElementById(panel.dataset.iterativo).textContent);
        const selector = control.querySelector("select");
        const tabla = panel.querySelector(".iterativo-tabla");
        const operandos = panel.querySelectorAll("[data-valor]");
        const componentes = panel.querySelectorAll("[data-componente]");

        function mostrar() {
            const k = Number(selector.value);
            const anterior = filas[k - 1];
            const actual = filas[k];
            operandos.forEach(operando => {
                const usaNuevo = operando.closest("[data-origen]").dataset.origen === "nueva";
                operando.textContent = (usaNuevo ? actual : anterior).x[operando.dataset.valor];
            });
            componentes.forEach(componente => {
                componente.textContent = actual.x[componente.dataset.componente];
            });
            tabla.querySelector("[aria-current]")?.removeAttribute("aria-current");
            const fila = tabla.querySelector(`[data-iteracion="${k}"]`);
            fila.setAttribute("aria-current", "true");
            const visible = tabla.getBoundingClientRect();
            const actualRect = fila.getBoundingClientRect();
            if (actualRect.bottom > visible.bottom || actualRect.top < visible.top) {
                tabla.scrollTop += actualRect.top - visible.top - tabla.clientHeight / 2;
            }
        }

        control.hidden = false;
        mostrar();
        selector.addEventListener("change", mostrar);
    });
})();
