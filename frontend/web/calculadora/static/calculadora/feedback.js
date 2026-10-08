(() => {
    "use strict";

    const estados = new Map();
    const formularios = 'form[action$="#resultado"]';

    function util(elemento) {
        return elemento && !elemento.matches(':disabled, input[type="hidden"]') &&
            !elemento.closest("[hidden], [inert]");
    }

    function revelar(elemento) {
        if (!util(elemento)) return null;
        for (let padre = elemento.parentElement; padre; padre = padre.parentElement) {
            if (padre.tagName === "DETAILS") padre.open = true;
        }
        return elemento.getClientRects().length && getComputedStyle(elemento).visibility === "visible" ? elemento : null;
    }

    function primerError(form) {
        for (const elemento of form.querySelectorAll('[aria-invalid="true"]')) {
            const control = elemento.matches("input, select, textarea") ? elemento :
                [...elemento.querySelectorAll("input, select, textarea")].find(revelar);
            if (revelar(control)) return control;
        }
        return [...form.querySelectorAll('.alert.error, .field-error[role="alert"]')].find(revelar);
    }

    function enfocar(elemento) {
        if (!revelar(elemento)) return;
        if (!elemento.matches("input, select, textarea, button, [tabindex]")) elemento.tabIndex = -1;
        elemento.focus({ preventScroll: true });
        // El foco puede abrir el dock de P27.3. Medir después incluye su altura real,
        // incluso durante la transición de entrada, sin ocultarlo ni cambiar su foco.
        requestAnimationFrame(() => {
            const header = document.querySelector(".app-header")?.getBoundingClientRect().bottom || 0;
            const dock = document.querySelector('.math-keyboard[data-abierto]');
            const limite = dock ? dock.getBoundingClientRect().top -
                new DOMMatrix(getComputedStyle(dock).transform).m42 - 12 : window.innerHeight - 12;
            const rect = elemento.getBoundingClientRect();
            const margen = header + 12;
            // Alinear arriba deja lugar para leer el mensaje asociado debajo del campo.
            if (rect.top < margen || rect.bottom > limite || elemento.matches("input, textarea, select")) {
                window.scrollBy({ top: rect.top - margen, behavior: "instant" });
            }
        });
    }

    // El guard se ejecuta antes de los validadores de la herramienta en el segundo envío.
    document.addEventListener("submit", event => {
        if (!estados.has(event.target)) return;
        event.preventDefault();
        event.stopImmediatePropagation();
    }, true);

    // Burbujeo hasta document: todos los validadores del formulario ya pudieron cancelar.
    document.addEventListener("submit", event => {
        const form = event.target;
        if (!form.matches(formularios)) return;
        if (event.defaultPrevented) {
            enfocar(primerError(form));
            return;
        }
        const boton = event.submitter;
        if (!boton?.matches("[data-calculo]")) return;
        estados.set(form, { boton, texto: boton.textContent, ancho: boton.style.minWidth });
        boton.style.minWidth = `${boton.getBoundingClientRect().width}px`;
        boton.textContent = "Calculando…";
        boton.setAttribute("aria-disabled", "true");
        boton.setAttribute("aria-busy", "true");
        form.setAttribute("aria-busy", "true");
        // Sigue siendo un successful control: name/value de Continuar viajan en el POST.
    });

    window.addEventListener("pageshow", () => {
        estados.forEach(({ boton, texto, ancho }, form) => {
            boton.textContent = texto;
            boton.style.minWidth = ancho;
            boton.removeAttribute("aria-disabled");
            boton.removeAttribute("aria-busy");
            form.removeAttribute("aria-busy");
        });
        estados.clear();
    });

    window.addEventListener("load", () => {
        document.querySelectorAll(formularios).forEach(form => {
            form.querySelectorAll("[data-error-group]").forEach(error => {
                const grupo = document.getElementById(error.dataset.errorGroup);
                if (!grupo) return;
                if (grupo.tagName !== "FIELDSET" && !grupo.hasAttribute("role")) grupo.setAttribute("role", "group");
                grupo.setAttribute("aria-invalid", "true");
                grupo.setAttribute("aria-describedby", [grupo.getAttribute("aria-describedby"), error.id].filter(Boolean).join(" "));
                const control = [...grupo.querySelectorAll("input, select, textarea")].find(util);
                if (control) {
                    const ids = new Set((control.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
                    ids.add(error.id);
                    control.setAttribute("aria-describedby", [...ids].join(" "));
                }
            });
            // Algunos controles (radios y celdas dinámicas) se crean al iniciar la herramienta.
            form.querySelectorAll("[data-error-field]").forEach(error => {
                const id = error.dataset.errorField;
                const nombre = id.replace(/^id_/, "");
                form.querySelectorAll("input, select, textarea").forEach(control => {
                    if (control.id !== id && control.name !== nombre) return;
                    control.setAttribute("aria-invalid", "true");
                    const ids = new Set((control.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
                    ids.add(error.id);
                    control.setAttribute("aria-describedby", [...ids].join(" "));
                });
            });
        });
        if (document.getElementById("resultado")) return;
        const confirmacion = [...document.querySelectorAll("[data-confirmacion]")].find(revelar);
        if (confirmacion) enfocar(confirmacion);
        else {
            const form = document.querySelector(`${formularios}[data-respuesta-errores]`);
            if (form) enfocar(primerError(form));
        }
    });
})();
