(() => {
    "use strict";

    function esCampo(elemento) {
        if (!elemento) return false;
        if (elemento.tagName === "TEXTAREA") return true;
        return elemento.tagName === "INPUT" && elemento.type === "text";
    }

    // Cada teclado inserta en el campo activo de su contenedor (data-teclado-para).
    // La etiqueta muestra notación matemática; data-insercion lleva la sintaxis del parser.
    document.querySelectorAll(".math-keyboard[data-teclado-para]").forEach((teclado) => {
        const contenedor = document.getElementById(teclado.dataset.tecladoPara);
        if (!contenedor) return;

        let objetivo = null;
        contenedor.addEventListener("focusin", (event) => {
            if (esCampo(event.target)) objetivo = event.target;
        });

        teclado.addEventListener("click", (event) => {
            const tecla = event.target.closest("button[data-insercion]");
            if (!tecla) return;

            const vigente = objetivo && contenedor.contains(objetivo) && !objetivo.disabled;
            const campo = vigente ? objetivo : contenedor.querySelector('textarea, input[type="text"]');
            if (!campo) return;

            const texto = tecla.dataset.insercion;
            const retroceso = Number(tecla.dataset.retroceso) || 0;
            const inicio = campo.selectionStart ?? campo.value.length;
            const fin = campo.selectionEnd ?? inicio;

            campo.focus();
            campo.setRangeText(texto, inicio, fin, "end");
            if (retroceso > 0) {
                const posicion = campo.selectionStart - retroceso;
                campo.setSelectionRange(posicion, posicion);
            }
            campo.dispatchEvent(new Event("input", { bubbles: true }));
        });

        teclado.hidden = false;
    });
})();
