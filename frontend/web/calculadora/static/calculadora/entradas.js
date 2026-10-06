(() => {
    "use strict";

    function dimensionValida(input) {
        const valor = Number(input.value);
        return /^\d+$/.test(input.value) && Number.isSafeInteger(valor) &&
            valor >= Number(input.min) && valor <= Number(input.max);
    }

    function validarDimension(input, mensaje = "") {
        const valida = input.disabled || dimensionValida(input);
        const caja = input.closest(".dimension-field");
        const servidor = caja?.querySelector("[data-error-field]");
        const errorServidor = servidor && !servidor.hidden && input.value === input.defaultValue && !input.disabled;
        if (servidor && !errorServidor) servidor.hidden = true;
        const error = input.disabled || errorServidor ? "" : mensaje || (valida ? "" :
            `Indica un número entero entre ${input.min} y ${input.max}.`);
        if (caja) {
            let ayuda = caja.querySelector("[data-error-dimension]");
            if (!ayuda) {
                ayuda = document.createElement("p");
                ayuda.className = "field-error";
                ayuda.dataset.errorDimension = "";
                ayuda.setAttribute("role", "status");
                ayuda.setAttribute("aria-live", "polite");
                caja.append(ayuda);
            }
            ayuda.id = `${input.id}_dimension_error`;
            ayuda.textContent = error;
            ayuda.hidden = !error;
            const ids = new Set((input.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
            // Reindexar símbolos también actualiza el identificador de la ayuda.
            for (const id of ids) if (id.endsWith("_dimension_error")) ids.delete(id);
            ids.add(ayuda.id);
            input.setAttribute("aria-describedby", [...ids].join(" "));
            caja.querySelectorAll("[data-paso]").forEach(button => {
                button.disabled = input.disabled || !valida ||
                    (Number(button.dataset.paso) < 0 ? Number(input.value) <= Number(input.min) : Number(input.value) >= Number(input.max));
            });
        }
        input.setAttribute("aria-invalid", String(Boolean(error || errorServidor)));
        return !error && !errorServidor;
    }

    window.entradasSeguras = { dimensionValida, validarDimension };

    // Desenfocar evita el incremento nativo sin cancelar el desplazamiento.
    document.addEventListener("wheel", event => {
        const input = event.target.closest?.('input[type="number"]');
        if (input && input === document.activeElement) input.blur();
    }, { capture: true, passive: true });

    document.querySelectorAll("#expresiones-form, #ecuacion-form, #inversa-form, #vectores-form, #sistema-form").forEach(form => {
        form.querySelectorAll("[data-aplicar]").forEach(button => {
            button.hidden = true;
            // Un submit oculto todavía puede ser el botón por defecto de Enter.
            button.disabled = true;
        });
        form.addEventListener("keydown", event => {
            const input = event.target;
            if (event.key !== "Enter" || event.isComposing || input.tagName !== "INPUT" ||
                !["text", "number"].includes(input.type)) return;
            event.preventDefault();
            if (input.closest(".dimension-field")) return;
            const calcular = form.querySelector('.workspace-actions button[type="submit"]');
            if (calcular) form.requestSubmit(calcular);
        });
        form.addEventListener("submit", event => {
            const dimensiones = [...form.querySelectorAll('.dimension-field input[type="number"]')]
                .filter(input => !input.disabled && !input.closest("fieldset:disabled"));
            if (dimensiones.some(input => !dimensionValida(input) || input.getAttribute("aria-invalid") === "true")) {
                event.preventDefault();
                dimensiones.forEach(input => {
                    if (!dimensionValida(input)) validarDimension(input);
                });
            }
        });
    });
})();
