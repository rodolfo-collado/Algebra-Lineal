(() => {
    "use strict";

    const plantilla = document.getElementById("matrix-selection-template");
    const aviso = document.querySelector("[data-estado-seleccion]");
    if (!plantilla || !aviso) return;
    const forms = [...document.querySelectorAll("#expresiones-form, #inversa-form, #ecuacion-form, #sistema-form")];
    const estados = new Map();
    const { filasDeMatriz } = window.entradasSeguras;
    const clave = ({ fila, columna }) => `${fila}_${columna}`;
    const deltas = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
    let actual = null;
    let enGesto = false;
    let contador = 0;

    function esMatriz(matriz) {
        if (!matriz.isConnected || matriz.closest("[hidden], [data-vector]")) return false;
        const operando = matriz.closest("[data-simbolo]");
        return !operando || operando.querySelector('[data-campo="tipo"]').value === "matriz";
    }

    function nombre(estado) {
        return estado.matriz.closest("[data-simbolo]")?.querySelector('[data-campo="nombre"]').value ||
            estado.matriz.closest("[data-matriz]")?.dataset.matriz || "A";
    }

    function existe(estado, celda) {
        if (!Number.isInteger(celda?.fila) || !Number.isInteger(celda?.columna)) return false;
        const input = celda && estado.filas[celda.fila]?.[celda.columna];
        return Boolean(input && !input.readOnly && !input.matches(":disabled"));
    }

    function coordenadas(estado, input) {
        const fila = estado.filas.findIndex(f => f.includes(input));
        return fila < 0 ? null : { fila, columna: estado.filas[fila].indexOf(input) };
    }

    function celdas(estado) {
        return estado.filas.flatMap((fila, i) => fila.flatMap((input, j) =>
            estado.celdas.has(`${i}_${j}`) ? [{ fila: i, columna: j, input }] : []));
    }

    function pintar(estado) {
        estado.matriz.toggleAttribute("data-seleccion-activa", actual === estado && estado.celdas.size > 0);
        estado.filas.forEach((fila, i) => fila.forEach((input, j) => {
            const seleccionada = estado.celdas.has(`${i}_${j}`);
            input.toggleAttribute("data-celda-seleccionada", seleccionada);
            const ids = new Set((input.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
            for (const id of ids) if (id.startsWith("seleccion-celda-")) ids.delete(id);
            if (seleccionada) ids.add(estado.descripcion.id);
            if (ids.size) input.setAttribute("aria-describedby", [...ids].join(" "));
            else input.removeAttribute("aria-describedby");
        }));
        const cuadrada = estado.filas.length === estado.columnasA;
        const referencia = estado.celdaActual;
        estado.menu.querySelector("summary").setAttribute("aria-label", `Seleccionar celdas de ${nombre(estado)}`);
        estado.menu.querySelectorAll("[data-seleccionar]").forEach(boton => {
            const comando = boton.dataset.seleccionar;
            boton.setAttribute("aria-label", `${boton.textContent} de ${nombre(estado)}`);
            boton.disabled = (["secundaria", "superior", "inferior"].includes(comando) && !cuadrada) ||
                (["fila", "columna"].includes(comando) && !referencia) ||
                (comando === "columna" && referencia?.columna >= estado.columnasA);
        });
        estado.menu.querySelector("[data-seleccion-aumentada]").hidden = !estado.aumentada;
    }

    function registrar(matriz) {
        const menu = plantilla.content.firstElementChild.cloneNode(true);
        const descripcion = document.createElement("span");
        descripcion.id = `seleccion-celda-${++contador}`;
        descripcion.className = "sr-only";
        descripcion.textContent = "Celda incluida en la selección matricial.";
        menu.append(descripcion);
        const caja = matriz.id === "matrix-grid" ? matriz.closest("#matrix-grid-wrapper") : matriz.closest(".matrix");
        caja.prepend(menu);
        const estado = { matriz, menu, descripcion, celdas: new Set(), referencia: null, extremo: null, celdaActual: null,
            tipo: null, comando: null, filas: [] };
        estados.set(matriz, estado);
        menu.addEventListener("toggle", () => {
            if (menu.open) for (const otro of estados.values()) if (otro !== estado) otro.menu.open = false;
        });
        menu.addEventListener("click", event => {
            const boton = event.target.closest("[data-seleccionar]");
            if (!boton || boton.disabled) return;
            seleccionarComando(estado, boton.dataset.seleccionar, boton.textContent);
            menu.open = false;
            menu.querySelector("summary").focus();
        });
        return estado;
    }

    function limpiarEstado(estado) {
        estado.celdas.clear();
        estado.tipo = null;
        estado.comando = null;
        estado.extremo = null;
    }

    function sincronizar() {
        const matrices = forms.flatMap(form => [...form.querySelectorAll(".matrix-entry-table, #matrix-grid")])
            .filter(matriz => esMatriz(matriz) && filasDeMatriz(matriz).some(f => f.length));
        for (const [matriz, estado] of estados) {
            if (matrices.includes(matriz)) continue;
            const habia = actual === estado && estado.celdas.size > 0;
            limpiarEstado(estado);
            if (habia) anunciar(estado);
            pintar(estado);
            estado.menu.remove();
            estados.delete(matriz);
            if (actual === estado) actual = null;
        }
        matrices.forEach(matriz => {
            const estado = estados.get(matriz) || registrar(matriz);
            estado.filas = filasDeMatriz(matriz);
            estado.aumentada = matriz.id === "matrix-grid";
            estado.columnasA = estado.filas[0].length - Number(estado.aumentada);
            const cantidad = estado.celdas.size;
            // Bloquear una celda existente no cambia el destino de un paste pendiente.
            const validas = celdas(estado).filter(c => estado.tipo !== "comando" || c.columna < estado.columnasA);
            estado.celdas = new Set(validas.map(clave));
            if (!estado.celdas.size) {
                limpiarEstado(estado);
                if (cantidad) estado.referencia = estado.celdaActual = null;
            }
            if (!existe(estado, estado.referencia)) estado.referencia = validas[0] ?
                { fila: validas[0].fila, columna: validas[0].columna } : null;
            if (!existe(estado, estado.extremo)) estado.extremo = estado.referencia;
            if (!existe(estado, estado.celdaActual)) estado.celdaActual = estado.referencia;
            pintar(estado);
            if (cantidad !== estado.celdas.size && actual === estado) anunciar(estado);
        });
    }

    function activar(estado) {
        const anterior = actual;
        actual = estado;
        if (anterior && anterior !== estado) pintar(anterior);
        pintar(estado);
    }

    function anunciar(estado, etiqueta = "") {
        const cantidad = estado.celdas.size;
        const celdas = `${cantidad} ${cantidad === 1 ? "celda" : "celdas"}`;
        aviso.textContent = cantidad ?
            (etiqueta ? `${etiqueta} de ${nombre(estado)} seleccionada: ${celdas}.` :
                `${celdas} ${cantidad === 1 ? "seleccionada" : "seleccionadas"}.`) :
            "Selección eliminada.";
    }

    function rango(inicio, fin) {
        const seleccion = [];
        for (let fila = Math.min(inicio.fila, fin.fila); fila <= Math.max(inicio.fila, fin.fila); fila++) {
            for (let columna = Math.min(inicio.columna, fin.columna); columna <= Math.max(inicio.columna, fin.columna); columna++) {
                seleccion.push({ fila, columna });
            }
        }
        return seleccion;
    }

    function reemplazar(matriz, seleccion, opciones = {}) {
        sincronizar();
        const estado = estados.get(matriz);
        if (!estado || !Array.isArray(seleccion) || seleccion.some(c =>
            !existe(estado, c) || (opciones.tipo === "comando" && c.columna >= estado.columnasA))) return false;
        const referencia = opciones.referencia ?? estado.referencia ?? seleccion[0] ?? null;
        const extremo = opciones.extremo ?? referencia;
        const celdaActual = opciones.extremo ?? opciones.referencia ?? estado.celdaActual ?? referencia;
        if ((referencia && !existe(estado, referencia)) || (extremo && !existe(estado, extremo))) return false;
        estado.celdas = new Set(seleccion.map(clave));
        estado.referencia = referencia ? { fila: referencia.fila, columna: referencia.columna } : null;
        estado.extremo = extremo ? { fila: extremo.fila, columna: extremo.columna } : null;
        estado.celdaActual = celdaActual ? { fila: celdaActual.fila, columna: celdaActual.columna } : null;
        estado.tipo = estado.celdas.size ? opciones.tipo || "arbitraria" : null;
        estado.comando = estado.celdas.size ? opciones.comando || null : null;
        activar(estado);
        anunciar(estado, opciones.etiqueta);
        return true;
    }

    function seleccionarComando(estado, comando, etiqueta) {
        sincronizar();
        const referencia = estado.celdaActual;
        const n = estado.columnasA;
        const seleccion = estado.filas.flatMap((fila, i) => fila.flatMap((input, j) => {
            if (j >= n) return [];
            const incluir = { toda: true, fila: i === referencia?.fila, columna: j === referencia?.columna,
                principal: i === j, secundaria: i + j === n - 1, superior: j >= i, inferior: i >= j }[comando];
            return incluir ? [{ fila: i, columna: j }] : [];
        }));
        reemplazar(estado.matriz, seleccion, { tipo: "comando", comando, etiqueta });
    }

    function obtener(matriz, actualizar = true) {
        if (actualizar) sincronizar();
        const estado = estados.get(matriz);
        if (!estado) return null;
        const seleccion = celdas(estado);
        const limites = seleccion.length ? {
            filaInicio: Math.min(...seleccion.map(c => c.fila)), filaFin: Math.max(...seleccion.map(c => c.fila)),
            columnaInicio: Math.min(...seleccion.map(c => c.columna)), columnaFin: Math.max(...seleccion.map(c => c.columna)),
        } : null;
        return { matriz, nombre: nombre(estado), activa: actual === estado && seleccion.length > 0,
            filas: estado.filas.length, columnas: estado.filas[0].length, columnasA: estado.columnasA,
            referencia: estado.referencia && { ...estado.referencia }, extremo: estado.extremo && { ...estado.extremo },
            celdaActual: estado.celdaActual && { ...estado.celdaActual },
            tipo: estado.tipo, comando: estado.comando, celdas: seleccion, limites,
            rectangular: Boolean(limites && seleccion.length ===
                (limites.filaFin - limites.filaInicio + 1) * (limites.columnaFin - limites.columnaInicio + 1)) };
    }

    function limpiar(matriz = actual?.matriz) {
        sincronizar();
        const estado = estados.get(matriz);
        if (!estado) return;
        const habia = estado.celdas.size > 0;
        limpiarEstado(estado);
        pintar(estado);
        if (habia) anunciar(estado);
    }

    // Solo el renderizador de dimensiones transfiere coordenadas; reemplazos ajenos se limpian.
    function redimensionar(anterior, nueva) {
        const previo = estados.get(anterior);
        if (previo && esMatriz(nueva)) {
            const estado = registrar(nueva);
            for (const propiedad of ["celdas", "referencia", "extremo", "celdaActual", "tipo", "comando"]) estado[propiedad] = previo[propiedad];
            if (actual === previo) actual = estado;
            estados.delete(anterior);
            previo.menu.remove();
        }
        sincronizar();
    }

    window.seleccionMatricial = { obtener, reemplazar, limpiar, redimensionar, sincronizar,
        activa() { sincronizar(); return actual?.celdas.size ? obtener(actual.matriz) : null; } };

    function estadoDe(input) {
        if (!input.matches?.('input.matrix-input[type="text"]')) return null;
        sincronizar();
        return estados.get(input.closest(".matrix-entry-table, #matrix-grid")) || null;
    }

    document.addEventListener("focusin", event => {
        const estado = estadoDe(event.target);
        if (!estado || enGesto) return;
        estado.celdaActual = coordenadas(estado, event.target);
        if (!estado.celdas.size) estado.referencia = coordenadas(estado, event.target);
        activar(estado);
    });

    // Antes del foco nativo: Shift+clic necesita la referencia de la celda anterior.
    document.addEventListener("mousedown", event => {
        if (event.defaultPrevented || event.button !== 0 || event.altKey || event.metaKey) return;
        const estado = estadoDe(event.target);
        if (!estado || !existe(estado, coordenadas(estado, event.target))) return;
        const destino = coordenadas(estado, event.target);
        if (event.shiftKey && event.target === document.activeElement && !event.ctrlKey) return;
        if (event.ctrlKey) {
            const seleccion = celdas(estado).filter(c => clave(c) !== clave(destino));
            if (!estado.celdas.has(clave(destino))) seleccion.push(destino);
            reemplazar(estado.matriz, seleccion, { tipo: "arbitraria", extremo: destino });
        } else if (event.shiftKey && estado.referencia) {
            reemplazar(estado.matriz, rango(estado.referencia, destino), { tipo: "rango", extremo: destino });
        } else {
            limpiar(estado.matriz);
            estado.referencia = destino;
            estado.extremo = destino;
            estado.celdaActual = destino;
            activar(estado);
            return;
        }
        event.preventDefault();
        enGesto = true;
        event.target.focus();
        enGesto = false;
    }, true);

    document.addEventListener("keydown", event => {
        if (event.defaultPrevented || event.isComposing || event.keyCode === 229) return;
        if (event.key !== "Escape" && !(event.shiftKey && deltas[event.key])) return;
        sincronizar();
        if (event.key === "Escape") {
            if (actual?.celdas.size) {
                limpiar();
                event.preventDefault();
            } else {
                const menu = event.target.closest(".matrix-selection[open]");
                if (menu) { menu.open = false; event.preventDefault(); menu.querySelector("summary").focus(); }
            }
            return;
        }
        const delta = deltas[event.key];
        if (!delta || !event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) return;
        const estado = estadoDe(event.target);
        if (!estado || actual !== estado || !estado.celdas.size) return;
        const desde = coordenadas(estado, event.target);
        const destino = { fila: desde.fila + delta[0], columna: desde.columna + delta[1] };
        event.preventDefault();
        if (!existe(estado, destino)) return;
        reemplazar(estado.matriz, rango(estado.referencia, destino), { tipo: "rango", extremo: destino });
        enGesto = true;
        estado.filas[destino.fila][destino.columna].focus();
        enGesto = false;
    }, true);

    document.addEventListener("pointerdown", event => {
        for (const estado of estados.values()) if (!estado.menu.contains(event.target)) estado.menu.open = false;
    });
    sincronizar();
    const observador = new MutationObserver(sincronizar);
    forms.forEach(form => observador.observe(form, { childList: true, subtree: true }));
})();
