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
        const desplegable = teclado.closest("details.disclosure");
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
                    boton.setAttribute("aria-label", tecla.nombre);
                    boton.title = tecla.nombre;
                    teclas.appendChild(boton);
                });
                grupos.appendChild(bloque);
            });
        }

        function sincronizar() {
            if (esValido(document.activeElement)) objetivo = document.activeElement;
            if (!esValido(objetivo)) {
                objetivo = Array.from(contenedor.querySelectorAll('textarea, input[type="text"]')).find(esValido) || null;
            }
            mostrarPerfil(objetivo ? perfilDe(objetivo) : null);
            teclado.hidden = !objetivo;
            if (desplegable) desplegable.hidden = !objetivo;
        }

        // Delegación: los campos nuevos heredan el perfil de su contenedor.
        contenedor.addEventListener("focusin", (event) => {
            if (esValido(event.target)) {
                objetivo = event.target;
                sincronizar();
            }
        });

        teclado.addEventListener("click", (event) => {
            const tecla = event.target.closest("button[data-insercion]");
            if (!tecla || !teclado.contains(tecla)) return;
            sincronizar();
            // Si cambió el contexto, no insertar una tecla del perfil anterior.
            if (!objetivo || !teclado.contains(tecla)) return;
            const campo = objetivo;

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

        // Cambios de perfil, visibilidad o estructura invalidan objetivos antiguos.
        // Ignorar el propio render evita ciclos y trabajo al pulsar las teclas.
        new MutationObserver((cambios) => {
            if (cambios.some((cambio) => !teclado.contains(cambio.target) && cambio.target !== desplegable)) {
                sincronizar();
            }
        }).observe(contenedor, {
            subtree: true, childList: true, attributes: true,
            attributeFilter: ["data-perfil", "hidden", "disabled", "readonly", "inert"],
        });
        sincronizar();
    });
})();
