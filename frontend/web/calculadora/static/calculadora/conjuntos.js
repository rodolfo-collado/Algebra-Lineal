/* El editor solo escribe texto: toda evaluación pertenece al parser del servidor. */
(() => {
    "use strict";
    const form = document.getElementById("conjuntos-form");
    if (!form) return;
    const expresion = form.elements.expresion;
    const guia = form.querySelector(".conjuntos-guia");
    const operacion = form.elements.plantilla;
    const guardar = form.querySelector("[data-guardar]");
    const nombres = () => [...form.querySelectorAll('[data-campo="nombre"]')].map(campo => campo.value.trim()).filter(Boolean);

    // Mismo criterio que elegir_nombres() del servidor: si existe U, se reserva como universo.
    function elegir(lista) {
        const otros = lista.filter(nombre => nombre !== "U");
        const base = otros.length ? otros : lista;
        const a = base[0] || "A";
        const b = base[1] || (base.length ? "{1}" : "B");
        const u = lista.includes("U") && a !== "U" && b !== "U" ? "U" : (a !== b ? `${a} ∪ ${b}` : a);
        return { a, b, u };
    }

    function rellenar(plantilla) {
        const { a, b, u } = elegir(nombres());
        return plantilla.replaceAll("{a}", a).replaceAll("{b}", b).replaceAll("{u}", u)
            .replaceAll("{x}", guia?.dataset.elemento || "1");
    }

    function actualizarGuia() {
        guia?.querySelectorAll("[data-plantilla]").forEach(opcion => {
            opcion.textContent = `${opcion.dataset.nombre} · ${rellenar(opcion.dataset.plantilla)}`;
        });
    }

    operacion.addEventListener("change", () => {
        document.getElementById("operacion-ayuda").textContent = operacion.selectedOptions[0].dataset.descripcion ||
            "Inserta en el cursor o sustituye el texto seleccionado.";
    });
    guia.querySelector("[data-insertar-operacion]").addEventListener("click", event => {
        event.preventDefault();
        const opcion = operacion.selectedOptions[0];
        if (!opcion.dataset.plantilla) { operacion.focus(); return; }
        expresion.focus();
        const texto = rellenar(opcion.dataset.plantilla);
        if (!document.execCommand("insertText", false, texto)) {
            expresion.setRangeText(texto, expresion.selectionStart, expresion.selectionEnd, "end");
            expresion.dispatchEvent(new Event("input", { bubbles: true }));
        }
    });

    // «Guardar cambios» solo aparece cuando hay algo que guardar (sin JavaScript, siempre).
    if (guardar && !form.hasAttribute("data-respuesta-errores")) guardar.hidden = true;
    form.addEventListener("input", event => {
        const fila = event.target.closest("[data-conjunto]");
        if (!fila) return;
        if (guardar) guardar.hidden = false;
        fila.querySelector("[data-lectura]")?.setAttribute("data-desactualizada", "");
        if (event.target.matches('[data-campo="nombre"]')) {
            const nombre = event.target.value.trim() || "sin nombre";
            fila.querySelector('[name^="eliminar"], [name="eliminar"]')?.setAttribute("aria-label", `Eliminar el conjunto ${nombre}`);
            actualizarGuia();
        }
    });

    // Intro en «Nuevo conjunto» lo añade; en los demás campos, el botón implícito calcula.
    const definicion = form.elements.definicion;
    definicion?.addEventListener("keydown", event => {
        if (event.key !== "Enter" || event.isComposing) return;
        event.preventDefault();
        form.querySelector("[data-agregar]").click();
    });
})();
