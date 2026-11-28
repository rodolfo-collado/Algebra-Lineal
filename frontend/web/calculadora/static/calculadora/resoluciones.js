/* Cuaderno de resoluciones. Solo mejora lo que ya funciona sin JavaScript:
   - en una herramienta, coloca el aviso del cuaderno bajo el encabezado del resultado;
   - en el cuaderno, cuenta lo marcado, marca un ejercicio o un día completo y activa la barra. */
(() => {
    "use strict";

    const aviso = document.getElementById("resolucion-aviso");
    const encabezado = document.querySelector("[data-resultado] .results-heading");
    if (aviso && encabezado) encabezado.after(aviso);

    const form = document.getElementById("cuaderno-seleccion");
    const barra = form?.querySelector("[data-seleccion]");
    if (!form || !barra) return;
    form.setAttribute("data-mejorado", "");
    const cuenta = barra.querySelector("[data-seleccion-cuenta]");
    const marcas = () => [...form.querySelectorAll('input[name="ids"]')];

    function actualizar() {
        const n = marcas().filter(m => m.checked).length;
        barra.toggleAttribute("data-activa", n > 0);
        cuenta.textContent = n ? `${n} marcada${n === 1 ? "" : "s"}:` : "Marca resoluciones para reunirlas en un ejercicio o eliminarlas.";
        barra.querySelectorAll("[data-requiere-seleccion]").forEach(boton => {
            boton.setAttribute("aria-disabled", String(n === 0));
        });
        form.querySelectorAll("[data-grupo]").forEach(grupo => {
            const propias = [...grupo.querySelectorAll('input[name="ids"]')];
            const todas = grupo.querySelector("[data-marcar-grupo]");
            if (!todas || !propias.length) return;
            const marcadas = propias.filter(m => m.checked).length;
            todas.checked = marcadas === propias.length;
            todas.indeterminate = marcadas > 0 && marcadas < propias.length;
        });
    }

    form.querySelectorAll("[data-marcar-grupo]").forEach(todas => {
        // Solo si el grupo tiene algo que marcar (un ejercicio recién creado todavía no).
        todas.hidden = !todas.closest("[data-grupo]").querySelector('input[name="ids"]');
        todas.addEventListener("change", () => {
            todas.closest("[data-grupo]").querySelectorAll('input[name="ids"]').forEach(m => { m.checked = todas.checked; });
            actualizar();
        });
    });
    form.addEventListener("change", actualizar);
    // Sin nada marcado, las acciones explican qué falta en lugar de enviar el formulario.
    form.addEventListener("submit", evento => {
        const boton = evento.submitter;
        if (boton?.hasAttribute("data-requiere-seleccion") && !marcas().some(m => m.checked)) {
            evento.preventDefault();
            cuenta.textContent = "Primero marca al menos una resolución.";
            marcas()[0]?.focus();
        }
    });
    actualizar();
})();
