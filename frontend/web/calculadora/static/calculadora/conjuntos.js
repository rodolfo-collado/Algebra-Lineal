/* El editor solo escribe texto: toda evaluación pertenece al parser del servidor. */
(() => {
    "use strict";

    // Copiar el resultado de una tarjeta (Operaciones y Cardinalidad): el botón confirma y vuelve a su texto.
    document.querySelectorAll("[data-copiar]").forEach(boton => {
        const texto = boton.firstChild;
        boton.hidden = false;
        boton.addEventListener("click", async () => {
            let copiado = false;
            try {
                await navigator.clipboard.writeText(boton.dataset.copiar);
                copiado = true;
            } catch {
                // Sin permiso de portapapeles: la selección temporal conserva el gesto del usuario.
                const area = Object.assign(document.createElement("textarea"), { value: boton.dataset.copiar, readOnly: true });
                area.className = "sr-only";
                document.body.append(area);
                area.select();
                try { copiado = document.execCommand("copy"); } catch { /* se informa abajo */ }
                area.remove();
                boton.focus({ preventScroll: true });
            }
            texto.textContent = copiado ? "Copiado" : "No se pudo copiar";
            boton.setAttribute("aria-live", "polite");
            clearTimeout(boton.temporizador);
            boton.temporizador = setTimeout(() => { texto.textContent = "Copiar"; }, 1600);
        });
    });

    const form = document.getElementById("conjuntos-form");
    if (!form) return;
    const expresion = form.elements.expresion;
    const guardar = form.querySelector("[data-guardar]");
    const fuente = form.elements.venn_fuente;
    const aplicar = form.querySelector("[data-aplicar-regiones]");
    const pendiente = form.querySelector("[data-venn-pendiente]");
    const descartar = form.querySelector("[data-descartar-regiones]");
    const editor = form.querySelector("[data-venn-editor]");
    const panorama = form.querySelector("[data-panorama]");
    const nombres = () => [...form.querySelectorAll('[data-campo="nombre"]')].map(campo => campo.value.trim()).filter(Boolean);

    /* —— Barra de símbolos: inserta en el cursor de la expresión y conserva Deshacer —— */
    const barra = form.querySelector("[data-barra]");
    const teclas = () => [...barra.querySelectorAll("button")];
    function actualizarNombres() {
        const grupo = barra.querySelector("[data-barra-nombres]");
        const actuales = [...grupo.children].map(boton => boton.dataset.insercion);
        const lista = [...new Set(nombres())];
        if (lista.length !== actuales.length || lista.some((nombre, i) => nombre !== actuales[i])) {
            grupo.replaceChildren(...lista.map(nombre => {
                const boton = document.createElement("button");
                boton.type = "button";
                boton.className = "math-key";
                boton.tabIndex = -1;
                boton.dataset.insercion = boton.textContent = nombre;
                boton.title = `Conjunto ${nombre}`;
                return boton;
            }));
        }
        grupo.hidden = !lista.length;
        // Un único alto de tabulación para toda la barra.
        if (!teclas().some(boton => boton.tabIndex === 0)) teclas().find(boton => !boton.closest("[hidden]")).tabIndex = 0;
    }
    function insertar(texto, retroceso) {
        expresion.focus({ preventScroll: true });
        if (!document.execCommand("insertText", false, texto)) {
            expresion.setRangeText(texto, expresion.selectionStart, expresion.selectionEnd, "end");
            expresion.dispatchEvent(new Event("input", { bubbles: true }));
        }
        const posicion = expresion.selectionStart - retroceso;
        expresion.setSelectionRange(posicion, posicion);
    }
    barra.hidden = false;
    actualizarNombres();
    // El puntero no le quita el cursor al campo; con teclado, el foco vuelve a la tecla pulsada.
    barra.addEventListener("mousedown", event => { if (event.target.closest("button")) event.preventDefault(); });
    barra.addEventListener("click", event => {
        const tecla = event.target.closest("button[data-insercion]");
        if (!tecla) return;
        insertar(tecla.dataset.insercion, Number(tecla.dataset.retroceso) || 0);
        if (event.detail === 0) tecla.focus({ preventScroll: true });
    });
    barra.addEventListener("keydown", event => {
        const lista = teclas().filter(boton => !boton.closest("[hidden]"));
        const actual = lista.indexOf(document.activeElement);
        const destino = { ArrowRight: actual + 1, ArrowLeft: actual - 1, Home: 0, End: lista.length - 1 }[event.key];
        if (actual < 0 || destino === undefined) return;
        event.preventDefault();
        const tecla = lista[(destino + lista.length) % lista.length];
        lista.forEach(boton => { boton.tabIndex = boton === tecla ? 0 : -1; });
        tecla.focus();
    });

    /* —— Conjuntos y diagrama: dos vistas del mismo modelo; el último lado editado manda —— */
    // «Guardar cambios» y «Actualizar conjuntos» solo aparecen cuando hay algo pendiente (sin JavaScript, siempre).
    function marcar(lado) {
        const diagrama = lado === "regiones";
        if (fuente) fuente.value = diagrama ? "regiones" : "";
        for (const control of [aplicar, descartar, pendiente]) if (control) control.hidden = !diagrama;
        editor?.toggleAttribute("data-desactualizado", lado === "conjuntos");
        if (guardar && lado) guardar.hidden = diagrama;
        if (diagrama) form.querySelectorAll("[data-lectura]").forEach(lectura => lectura.setAttribute("data-desactualizada", ""));
        if (lado && panorama?.querySelector(".tarjetas")) {
            panorama.setAttribute("data-desactualizado", "");
            panorama.querySelector("[data-panorama-aviso]").textContent = diagrama
                ? "Cambiaste el diagrama. Pulsa «Actualizar conjuntos» para recalcular estas tarjetas."
                : "Cambiaste los conjuntos. Pulsa «Guardar cambios» para recalcular estas tarjetas.";
        }
    }
    if (guardar && !form.hasAttribute("data-respuesta-errores")) guardar.hidden = true;
    marcar(fuente?.value === "regiones" ? "regiones" : null);
    // Descartar vuelve a leer el diagrama de los conjuntos: el borrador deja de mandar.
    descartar?.addEventListener("click", () => { fuente.value = ""; });
    form.addEventListener("input", event => {
        if (event.target.closest("[data-venn-editor]")) { marcar("regiones"); return; }
        const fila = event.target.closest("[data-conjunto]");
        if (!fila) return;
        marcar("conjuntos");
        fila.querySelector("[data-lectura]")?.setAttribute("data-desactualizada", "");
        if (event.target.matches('[data-campo="nombre"]')) {
            const nombre = event.target.value.trim() || "sin nombre";
            fila.querySelector('[name="eliminar"]')?.setAttribute("aria-label", `Eliminar el conjunto ${nombre}`);
            actualizarNombres();
        }
    });

    // Intro añade en «Nuevo conjunto» y aplica en una región; en los demás campos, el botón implícito calcula.
    form.addEventListener("keydown", event => {
        if (event.key !== "Enter" || event.isComposing || event.shiftKey) return;
        const boton = event.target === form.elements.definicion ? form.querySelector("[data-agregar]")
            : event.target.closest("[data-venn-editor]") ? aplicar : null;
        if (!boton) return;
        event.preventDefault();
        boton.click();
    });
})();
