(() => {
    "use strict";

    document.querySelectorAll(".math-keyboard[data-perfiles]").forEach((teclado) => {
        const contenedor = teclado.closest("form");
        const datos = document.getElementById(teclado.dataset.perfiles);
        const plantillaTecla = document.getElementById("math-key-template");
        const plantillaGrupo = document.getElementById("math-key-group-template");
        if (!contenedor || !datos || !plantillaTecla || !plantillaGrupo) return;

        const perfiles = JSON.parse(datos.textContent);
        const grupos = teclado.querySelector(".math-keyboard-groups");
        const ayuda = teclado.querySelector(".math-keyboard-help");
        let objetivo = null;
        let perfilActual = null;

        function perfilDe(campo) {
            return campo?.closest("[data-perfil]")?.dataset.perfil;
        }

        function esValido(campo) {
            return campo && contenedor.contains(campo)
                && campo.matches('textarea, input[type="text"]')
                && !campo.matches(":disabled") && !campo.readOnly
                && !campo.closest("[hidden], [inert]") && campo.getClientRects().length > 0
                && Object.hasOwn(perfiles, perfilDe(campo));
        }

        function mostrarPerfil(id) {
            if (id === perfilActual) return;
            perfilActual = id;
            grupos.replaceChildren();
            ayuda.textContent = id ? perfiles[id].ayuda : "";
            if (!id) return;
            perfiles[id].grupos.forEach((grupo) => {
                const bloque = plantillaGrupo.content.firstElementChild.cloneNode(true);
                bloque.setAttribute("aria-label", grupo.nombre);
                bloque.querySelector(".math-keyboard-group-name").textContent = grupo.nombre;
                const teclas = bloque.querySelector(".math-keys");
                grupo.teclas.forEach((tecla) => {
                    const boton = plantillaTecla.content.firstElementChild.cloneNode(true);
                    boton.textContent = tecla.etiqueta;
                    boton.setAttribute("data-insercion", tecla.insercion);
                    boton.setAttribute("data-retroceso", tecla.retroceso);
                    boton.setAttribute("aria-label", `${tecla.etiqueta} — ${tecla.nombre}`);
                    boton.title = `${tecla.etiqueta} — ${tecla.nombre}`;
                    teclas.appendChild(boton);
                });
                grupos.appendChild(bloque);
            });
        }

        function sincronizar() {
            if (!esValido(objetivo) || document.activeElement !== objetivo) objetivo = null;
            mostrarPerfil(objetivo ? perfilDe(objetivo) : null);
            teclado.hidden = !objetivo;
        }

        function revelarCampo() {
            if (!objetivo || teclado.hidden) return;
            const campo = objetivo.getBoundingClientRect();
            const limite = teclado.getBoundingClientRect().top - 8;
            const cabecera = document.querySelector(".app-header")?.getBoundingClientRect().bottom || 0;
            if (campo.bottom > limite || campo.top < cabecera + 8) {
                objetivo.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "instant" });
            }
        }

        // Delegación: los campos nuevos heredan el perfil de su contenedor.
        document.addEventListener("focusin", (event) => {
            if (teclado.contains(event.target)) return;
            objetivo = esValido(event.target) ? event.target : null;
            sincronizar();
            requestAnimationFrame(revelarCampo);
        });
        document.addEventListener("focusout", () => queueMicrotask(sincronizar));
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                objetivo = null;
                sincronizar();
            }
        });
        // También cubre controles que no toman foco al pulsarlos (por ejemplo, un label).
        document.addEventListener("pointerdown", (event) => {
            const campo = event.target.closest("label")?.control || event.target;
            if (!teclado.contains(event.target) && !esValido(campo)) {
                objetivo = null;
                sincronizar();
            }
        });
        teclado.addEventListener("mousedown", (event) => {
            if (event.target.closest("button[data-insercion]")) event.preventDefault();
        });

        teclado.addEventListener("click", (event) => {
            const tecla = event.target.closest("button[data-insercion]");
            if (!tecla || !teclado.contains(tecla)) return;
            sincronizar();
            // Si cambió el contexto, no insertar una tecla del perfil anterior.
            if (teclado.hidden || !objetivo || !teclado.contains(tecla)) return;
            const campo = objetivo;

            const texto = tecla.dataset.insercion;
            const retroceso = Number(tecla.dataset.retroceso) || 0;
            const inicio = campo.selectionStart ?? campo.value.length;
            const fin = campo.selectionEnd ?? inicio;

            // Delimitar la edición del dock frente a la escritura física, sin cambiar foco.
            campo.setSelectionRange(inicio, fin);
            // insertText conserva el historial nativo de edición, también para Ctrl+Z.
            // Detectar input evita duplicarlo en navegadores que ya lo emiten.
            let emitido = false;
            const registrar = () => { emitido = true; };
            campo.addEventListener("input", registrar);
            let insertado = false;
            try {
                insertado = document.execCommand("insertText", false, texto);
            } catch (_) { /* El fallback conserva cursor y selección. */ }
            campo.removeEventListener("input", registrar);
            if (!insertado) campo.setRangeText(texto, inicio, fin, "end");
            const posicion = campo.selectionStart - retroceso;
            campo.setSelectionRange(posicion, posicion);
            if (!emitido) campo.dispatchEvent(new Event("input", { bubbles: true }));
        });

        // Cambios de perfil, visibilidad o estructura invalidan objetivos antiguos.
        // Ignorar el propio render evita ciclos y trabajo al pulsar las teclas.
        new MutationObserver((cambios) => {
            if (cambios.some((cambio) => !teclado.contains(cambio.target))) {
                sincronizar();
                requestAnimationFrame(revelarCampo);
            }
        }).observe(contenedor, {
            subtree: true, childList: true, attributes: true,
            attributeFilter: ["data-perfil", "hidden", "disabled", "readonly", "inert"],
        });
        window.addEventListener("resize", revelarCampo);
        sincronizar();
    });
})();
