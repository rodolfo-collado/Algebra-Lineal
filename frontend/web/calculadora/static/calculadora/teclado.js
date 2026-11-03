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
        let cambioVisual = 0;
        let superindice = false;
        let insertando = false;
        // El menú de edición (clic derecho) prolonga la edición del campo: no cierra el dock.
        const enMenuEdicion = (nodo) => Boolean(nodo?.closest?.("[data-edicion-menu]"));

        function crearTecla(tecla) {
            const boton = plantillaTecla.content.firstElementChild.cloneNode(true);
            boton.textContent = tecla.etiqueta;
            boton.setAttribute("data-insercion", tecla.insercion);
            boton.setAttribute("data-retroceso", tecla.retroceso || 0);
            boton.toggleAttribute("data-exponente-entero", Boolean(tecla.exponente_entero));
            if (tecla.exponente_entero) boton.setAttribute("aria-pressed", "false");
            boton.setAttribute("aria-label", `${tecla.etiqueta} — ${tecla.nombre}`);
            boton.title = `${tecla.etiqueta} — ${tecla.nombre}`;
            return boton;
        }

        function activarSuperindice(activo) {
            const tecla = grupos.querySelector("[data-exponente-entero]");
            superindice = Boolean(activo && tecla && objetivo);
            if (!tecla) return;
            tecla.setAttribute("aria-pressed", String(superindice));
            ayuda.textContent = superindice
                ? "Superíndice activo: escribe dígitos y un signo inicial. Pulsa aⁿ para volver a escritura normal."
                : perfiles[perfilActual].ayuda;
        }

        function textoDeEntrada(texto, campo) {
            if (!superindice) return texto;
            const prefijo = campo.value.slice(0, campo.selectionStart);
            if (!/^[+-]?[0-9]*$/.test(texto) ||
                (/^[+-]/.test(texto) && !/[0-9xeiπ)]$/.test(prefijo))) {
                activarSuperindice(false);
                return texto;
            }
            return [...texto].map(c => "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻"["0123456789+-".indexOf(c)]).join("");
        }

        function sincronizarOperandos() {
            const selector = objetivo?.closest("[data-operandos]")?.dataset.operandos;
            const fuente = selector ? contenedor.querySelector(selector) : null;
            const nombres = fuente ? [...fuente.querySelectorAll('[data-campo="nombre"]')]
                .map(campo => campo.value.trim()).filter(Boolean) : [];
            let bloque = grupos.querySelector(".math-keyboard-operands");
            if (!nombres.length) {
                bloque?.remove();
                return;
            }
            if (!bloque) {
                bloque = plantillaGrupo.content.firstElementChild.cloneNode(true);
                bloque.classList.add("math-keyboard-operands");
                bloque.setAttribute("aria-label", "Operandos");
                bloque.querySelector(".math-keyboard-group-name").textContent = "Operandos";
                grupos.prepend(bloque);
            }
            const teclas = bloque.querySelector(".math-keys");
            // El DOM de entrada es la fuente; conservar botones sin cambios preserva la pulsación.
            const actuales = [...teclas.children].map(boton => boton.dataset.insercion);
            if (nombres.length === actuales.length && nombres.every((nombre, i) => nombre === actuales[i])) return;
            teclas.replaceChildren(...nombres.map(nombre => crearTecla({
                etiqueta: nombre, insercion: nombre, nombre: `Operando ${nombre}`,
            })));
        }

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
            activarSuperindice(false);
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
                    teclas.appendChild(crearTecla(tecla));
                });
                grupos.appendChild(bloque);
            });
            if (grupos.querySelector("[data-exponente-entero]")) {
                ayuda.setAttribute("role", "status");
                ayuda.setAttribute("aria-live", "polite");
            } else {
                ayuda.removeAttribute("role");
                ayuda.removeAttribute("aria-live");
            }
        }

        function mostrarDock(abierto) {
            if (abierto === teclado.hasAttribute("data-abierto")) return;
            const cambio = ++cambioVisual;
            if (abierto) {
                teclado.hidden = false;
                // Medir el estado inicial permite entrar desde hidden sin una espera.
                teclado.getBoundingClientRect();
            }
            teclado.toggleAttribute("data-abierto", abierto);
            teclado.inert = !abierto;
            teclado.setAttribute("aria-hidden", String(!abierto));
            if (abierto) return;

            function terminarCierre() {
                // Un foco nuevo invalida cualquier finalización del cierre anterior.
                if (cambio !== cambioVisual) return;
                teclado.hidden = true;
                mostrarPerfil(null);
            }
            const transiciones = teclado.getAnimations();
            if (transiciones.length) {
                Promise.allSettled(transiciones.map(animacion => animacion.finished)).then(terminarCierre);
            } else {
                terminarCierre(); // Sin movimiento o CSS: cierre inmediato.
            }
        }

        function sincronizar() {
            if (!esValido(objetivo) || (document.activeElement !== objetivo && !enMenuEdicion(document.activeElement))) objetivo = null;
            if (objetivo) {
                mostrarPerfil(perfilDe(objetivo));
                sincronizarOperandos();
            }
            if (!objetivo) activarSuperindice(false);
            mostrarDock(Boolean(objetivo));
        }

        function revelarCampo() {
            if (!objetivo || teclado.hidden) return;
            const campo = objetivo.getBoundingClientRect();
            const desplazamiento = new DOMMatrix(getComputedStyle(teclado).transform).m42;
            const limite = teclado.getBoundingClientRect().top - desplazamiento - 8;
            const cabecera = document.querySelector(".app-header")?.getBoundingClientRect().bottom || 0;
            if (campo.bottom > limite || campo.top < cabecera + 8) {
                objetivo.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "instant" });
                const visible = objetivo.getBoundingClientRect();
                if (visible.bottom > limite) window.scrollBy({ top: visible.bottom - limite, behavior: "instant" });
            }
        }

        // Delegación: los campos nuevos heredan el perfil de su contenedor.
        document.addEventListener("focusin", (event) => {
            if (teclado.contains(event.target) || enMenuEdicion(event.target)) return;
            if (event.target !== objetivo) activarSuperindice(false);
            objetivo = esValido(event.target) ? event.target : null;
            sincronizar();
            requestAnimationFrame(revelarCampo);
        });
        document.addEventListener("focusout", () => queueMicrotask(sincronizar));
        contenedor.addEventListener("input", sincronizar);
        contenedor.addEventListener("change", sincronizar);
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && !event.defaultPrevented) {
                objetivo = null;
                sincronizar();
            }
        });
        // También cubre controles que no toman foco al pulsarlos (por ejemplo, un label).
        document.addEventListener("pointerdown", (event) => {
            const campo = event.target.closest("label")?.control || event.target;
            if (!teclado.contains(event.target) && !enMenuEdicion(event.target) && !esValido(campo)) {
                objetivo = null;
                sincronizar();
            }
        });
        teclado.addEventListener("mousedown", (event) => {
            if (event.target.closest("button[data-insercion]")) event.preventDefault();
        });

        function insertar(campo, texto, retroceso = 0) {
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
            insertando = true;
            try {
                insertado = document.execCommand("insertText", false, texto);
            } catch (_) { /* El fallback conserva cursor y selección. */ }
            campo.removeEventListener("input", registrar);
            if (!insertado) campo.setRangeText(texto, inicio, fin, "end");
            const posicion = campo.selectionStart - retroceso;
            campo.setSelectionRange(posicion, posicion);
            if (!emitido) campo.dispatchEvent(new Event("input", { bubbles: true }));
            insertando = false;
        }

        contenedor.addEventListener("beforeinput", event => {
            if (!superindice || insertando || event.target !== objetivo || event.isComposing) return;
            if (event.inputType.startsWith("delete") || event.inputType.startsWith("history")) return;
            if (event.inputType !== "insertText" || !event.data || !event.cancelable) {
                activarSuperindice(false);
                return;
            }
            const texto = textoDeEntrada(event.data, objetivo);
            if (texto === event.data) return;
            event.preventDefault();
            insertar(objetivo, texto);
        });
        contenedor.addEventListener("compositionstart", () => activarSuperindice(false));

        teclado.addEventListener("click", event => {
            const tecla = event.target.closest("button[data-insercion]");
            if (!tecla || !teclado.contains(tecla)) return;
            sincronizar();
            if (teclado.hidden || !objetivo || !teclado.contains(tecla)) return;
            if (tecla.hasAttribute("data-exponente-entero")) {
                activarSuperindice(!superindice);
                return;
            }
            insertar(objetivo, textoDeEntrada(tecla.dataset.insercion, objetivo), Number(tecla.dataset.retroceso) || 0);
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
