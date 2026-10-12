(() => {
    "use strict";

    const GRID = ".matrix-entry-table, #matrix-grid, #vector-list";
    const { filasDeMatriz, aplicarPegado } = window.entradasSeguras;
    let registro = null;
    const botonDe = estado => estado.parentElement.querySelector("[data-deshacer-pegado]");
    const editable = input => input?.isConnected && input.matches('input.matrix-input[type="text"]') &&
        !input.readOnly && !input.matches(":disabled") && !input.closest("[hidden], [data-escalar]");

    function estado(form) {
        let aviso = form.querySelector("[data-estado-pegado]");
        if (aviso) return aviso;
        const caja = document.createElement("div");
        caja.className = "paste-feedback";
        aviso = document.createElement("p");
        aviso.className = "field-help";
        aviso.dataset.estadoPegado = "";
        aviso.setAttribute("role", "status");
        aviso.setAttribute("aria-live", "polite");
        aviso.setAttribute("aria-atomic", "true");
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = "btn btn-secondary";
        boton.dataset.deshacerPegado = "";
        boton.textContent = "Deshacer";
        boton.hidden = true;
        boton.addEventListener("click", deshacer);
        boton.addEventListener("blur", () => {
            if (!registro || registro.estado !== aviso) boton.hidden = true;
        });
        caja.append(aviso, boton);
        form.querySelector(".workspace-actions").before(caja);
        return aviso;
    }

    function consumir() {
        const anterior = registro;
        registro = null;
        observador.disconnect();
        if (anterior) {
            const boton = botonDe(anterior.estado);
            // Una invalidación pasiva no retira el control que aún tiene foco.
            boton.hidden = document.activeElement !== boton;
            boton.setAttribute("aria-disabled", "true");
        }
        return anterior;
    }

    function invalidar() {
        const anterior = consumir();
        if (anterior) anterior.estado.textContent = "El pegado ya no puede deshacerse porque cambió su destino.";
    }

    function cambioEstructural(mutaciones) {
        if (!registro) return false;
        const { matriz } = registro;
        return mutaciones.some(m => matriz.contains(m.target) ||
            (m.type === "attributes" && m.target.contains(matriz)) ||
            [...m.removedNodes].some(n => n.contains(matriz)));
    }

    const observador = new MutationObserver(mutaciones => {
        if (cambioEstructural(mutaciones)) invalidar();
    });

    function coherente() {
        const { matriz, form, dimensiones, cambios, tipo } = registro;
        if (!matriz.isConnected || matriz.closest("[data-entrada-calculo]") !== form ||
            matriz.closest("[hidden], [data-escalar]") ||
            matriz.closest("[data-simbolo]")?.querySelector('[data-campo="tipo"]')?.value !== tipo) return false;
        const filas = filasDeMatriz(matriz);
        return filas.length === dimensiones.length && filas.every((fila, i) => fila.length === dimensiones[i]) &&
            cambios.every(({ input, fila, columna, nuevo, anterior }) =>
                filas[fila]?.[columna] === input && input.closest(GRID) === matriz && input.form === form &&
                editable(input) && input.value === nuevo && (input.maxLength < 0 || anterior.length <= input.maxLength));
    }

    function puedeDeshacer() {
        if (!registro) return false;
        // También revisar mutaciones pendientes: no depender del turno del observer.
        if (cambioEstructural(observador.takeRecords()) || !coherente()) invalidar();
        return Boolean(registro);
    }

    function pegar(destinos, matriz, contexto) {
        // Consumir antes de input evita anunciar invalidación y éxito para el mismo paste.
        consumir();
        const cambios = aplicarPegado(destinos);
        const form = matriz.closest("[data-entrada-calculo]");
        if (!form) return;
        const aviso = estado(form);
        const filas = filasDeMatriz(matriz);
        const modificadas = cambios.filter(c => c.anterior !== c.nuevo).map(c => {
            const fila = filas.findIndex(f => f.includes(c.input));
            return { ...c, fila, columna: filas[fila]?.indexOf(c.input) };
        });
        if (!modificadas.length) {
            aviso.textContent = "Pegado sin cambios.";
            return;
        }
        const fila = filas.findIndex(f => f.includes(contexto));
        const foco = fila >= 0 ? { fila, columna: filas[fila].indexOf(contexto) } :
            window.seleccionMatricial?.obtener(matriz, false)?.celdaActual || modificadas[0];
        registro = { matriz, form, dimensiones: filas.map(f => f.length), cambios: modificadas,
            tipo: matriz.closest("[data-simbolo]")?.querySelector('[data-campo="tipo"]')?.value,
            foco: { fila: foco.fila, columna: foco.columna }, estado: aviso };
        aviso.textContent = modificadas.length === 1 ? "1 celda pegada." : `${modificadas.length} celdas pegadas.`;
        if (!puedeDeshacer()) return;
        const boton = botonDe(aviso);
        boton.removeAttribute("aria-disabled");
        boton.hidden = false;
        observador.observe(document.body, { subtree: true, childList: true, attributes: true,
            attributeFilter: ["readonly", "disabled", "hidden", "type", "maxlength"] });
    }

    function recuperarFoco(anterior) {
        const filas = filasDeMatriz(anterior.matriz);
        const preferida = filas[anterior.foco.fila]?.[anterior.foco.columna];
        const fallback = [...anterior.form.querySelectorAll('.dimension-field input, .matrix-selection summary, input.matrix-input[type="text"], .workspace-actions button')]
            .find(input => input.isConnected && !input.matches(':disabled, [aria-disabled="true"]') &&
                !input.closest("[hidden]") && !input.readOnly);
        const destino = editable(preferida) ? preferida : filas.flat().find(editable) || fallback;
        // B puede seguir existiendo dentro de Aplicaciones y propiedades cerrado.
        for (let padre = destino?.parentElement; padre; padre = padre.parentElement) {
            if (padre.tagName === "DETAILS") padre.open = true;
        }
        destino?.focus();
    }

    function deshacer() {
        const anterior = registro;
        if (!puedeDeshacer()) {
            if (anterior && document.activeElement === botonDe(anterior.estado)) {
                recuperarFoco(anterior);
                botonDe(anterior.estado).hidden = true;
            }
            return false;
        }
        consumir();
        aplicarPegado(anterior.cambios.map(({ input, anterior: valor }) => [input, valor]));
        recuperarFoco(anterior);
        botonDe(anterior.estado).hidden = true;
        anterior.estado.textContent = anterior.cambios.length === 1 ? "Pegado deshecho: 1 celda restaurada." :
            `Pegado deshecho: ${anterior.cambios.length} celdas restauradas.`;
        return true;
    }

    ["input", "change"].forEach(tipo => document.addEventListener(tipo, event => {
        if (registro && event.target.closest?.(GRID) === registro.matriz) invalidar();
    }, true));
    window.addEventListener("pagehide", () => {
        const anterior = consumir();
        if (anterior) {
            botonDe(anterior.estado).hidden = true;
            anterior.estado.textContent = "";
        }
    });
    window.deshacerPegado = { estado, pegar, puedeDeshacer, deshacer, invalidar };
})();
