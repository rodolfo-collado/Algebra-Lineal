/* El guiado solo escribe texto: toda evaluación pertenece al parser del servidor. */
(() => {
    "use strict";
    const form = document.getElementById("conjuntos-form");
    if (!form) return;
    const expresion = form.elements.expresion;
    const nombres = document.getElementById("nombres-conjuntos");
    function actualizarNombres() {
        nombres.replaceChildren(...[...form.querySelectorAll('[data-campo="nombre"]')].map(campo => {
            const opcion = document.createElement("option");
            opcion.value = campo.value.trim();
            return opcion;
        }));
    }
    form.addEventListener("input", event => {
        if (event.target.matches('[data-campo="nombre"]')) actualizarNombres();
    });
    form.querySelector("[data-construir]").addEventListener("click", event => {
        event.preventDefault();
        expresion.value = `${form.elements.izquierdo.value.trim()} ${form.elements.operador.value} ${form.elements.derecho.value.trim()}`;
        expresion.dispatchEvent(new Event("input", { bubbles: true }));
        expresion.focus();
    });
    actualizarNombres();
})();
