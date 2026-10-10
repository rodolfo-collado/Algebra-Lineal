(() => {
    "use strict";

    const TIPO = "application/x-pygebra-matrix-selection";
    // Reducción admite 12 ecuaciones y 12 variables, más la columna b.
    const MAX_FILAS = 12, MAX_COLUMNAS = 13, MAX_CELDAS = 120, MAX_METADATA = 4096, MAX_TEXTO = 65536;
    const bytes = texto => new TextEncoder().encode(texto).length;
    const escapar = texto => texto.replace(/[&<>"']/g, c =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

    function textoAdmitido(texto) {
        return typeof texto === "string" && texto.length <= MAX_TEXTO && bytes(texto) <= MAX_TEXTO;
    }

    function parsear(metadata, texto) {
        if (typeof metadata !== "string" || metadata.length > MAX_METADATA ||
            bytes(metadata) > MAX_METADATA || !textoAdmitido(texto)) return null;
        let datos;
        try { datos = JSON.parse(metadata); } catch { return null; }
        const campos = ["version", "filas", "columnas", "forma", "celdas"];
        if (!datos || Array.isArray(datos) || typeof datos !== "object" ||
            Object.keys(datos).length !== campos.length || campos.some(c => !Object.hasOwn(datos, c)) ||
            datos.version !== 1 || !Number.isInteger(datos.filas) || !Number.isInteger(datos.columnas) ||
            datos.filas < 1 || datos.filas > MAX_FILAS || datos.columnas < 1 || datos.columnas > MAX_COLUMNAS ||
            datos.filas * datos.columnas > MAX_CELDAS ||
            !["rectangulo", "mascara"].includes(datos.forma) || !Array.isArray(datos.celdas) ||
            !datos.celdas.length || datos.celdas.length > datos.filas * datos.columnas) return null;
        const bloque = window.entradasSeguras.bloqueDeTexto(texto, true);
        if (texto.replace(/\r\n/g, "").includes("\r") || bloque.length !== datos.filas ||
            bloque.some(fila => fila.length !== datos.columnas)) return null;
        let anterior = -1;
        const posiciones = new Set();
        for (const celda of datos.celdas) {
            if (!Array.isArray(celda) || celda.length !== 2) return null;
            const [fila, columna] = celda;
            if (!Number.isInteger(fila) || !Number.isInteger(columna) || fila < 0 || columna < 0 ||
                fila >= datos.filas || columna >= datos.columnas) return null;
            const posicion = fila * datos.columnas + columna;
            if (posicion <= anterior) return null;
            posiciones.add(posicion);
            anterior = posicion;
        }
        const rectangular = posiciones.size === datos.filas * datos.columnas;
        if ((datos.forma === "rectangulo") !== rectangular ||
            Math.min(...datos.celdas.map(c => c[0])) !== 0 || Math.min(...datos.celdas.map(c => c[1])) !== 0 ||
            Math.max(...datos.celdas.map(c => c[0])) !== datos.filas - 1 ||
            Math.max(...datos.celdas.map(c => c[1])) !== datos.columnas - 1 ||
            bloque.some((fila, i) => fila.some((valor, j) =>
                !posiciones.has(i * datos.columnas + j) && valor !== ""))) return null;
        return datos;
    }

    function celdaHTML(valor) {
        const fraccion = /^\s*([+-]?\d{1,100})\s*\/\s*(\d{1,100})\s*$/.exec(valor);
        if (fraccion && /[1-9]/.test(fraccion[2])) return `<td>${escapar(`=${valor}`)}</td>`;
        const numero = /^\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*$/.test(valor);
        // Texto ajeno a números no debe convertirse en una fórmula de la hoja destino.
        return `<td${valor && !numero ? ' style="mso-number-format:\'\\@\'"' : ""}>${escapar(valor)}</td>`;
    }

    function serializar(seleccion) {
        if (!seleccion?.celdas.length || !seleccion.limites) return null;
        const { filaInicio, filaFin, columnaInicio, columnaFin } = seleccion.limites;
        const filas = filaFin - filaInicio + 1, columnas = columnaFin - columnaInicio + 1;
        if (filas < 1 || filas > MAX_FILAS || columnas < 1 || columnas > MAX_COLUMNAS || filas * columnas > MAX_CELDAS) return null;
        if (seleccion.celdas.reduce((total, { input }) => total + input.value.length, filas * columnas - 1) > MAX_TEXTO) return null;
        const bloque = Array.from({ length: filas }, () => Array(columnas).fill(""));
        const celdas = seleccion.celdas.map(({ fila, columna, input }) => {
            bloque[fila - filaInicio][columna - columnaInicio] = input.value;
            return [fila - filaInicio, columna - columnaInicio];
        });
        const texto = bloque.map(fila => fila.join("\t")).join("\n");
        const metadata = JSON.stringify({ version: 1, filas, columnas,
            forma: seleccion.rectangular ? "rectangulo" : "mascara", celdas });
        if (bloque.some(fila => fila.some(valor => /[\t\r\n]/.test(valor))) || !parsear(metadata, texto)) return null;
        const html = `<table>${bloque.map(fila => `<tr>${fila.map(celdaHTML).join("")}</tr>`).join("")}</table>`;
        return { texto, html, metadata };
    }

    window.copiadoMatricial = { TIPO, parsear, serializar, textoAdmitido };

    document.addEventListener("copy", event => {
        if (event.defaultPrevented || !event.cancelable || !event.clipboardData) return;
        const input = document.activeElement;
        if ((input?.selectionStart != null && input.selectionStart !== input.selectionEnd) ||
            (event.target.selectionStart != null && event.target.selectionStart !== event.target.selectionEnd) ||
            window.getSelection()?.toString()) return;
        const seleccion = window.seleccionMatricial?.activa();
        if (!seleccion) return;
        const aviso = document.querySelector("[data-estado-seleccion]");
        const datos = serializar(seleccion);
        if (!datos) {
            aviso.textContent = "No se pudo copiar la selección: supera los límites de tamaño o contiene tabuladores.";
            return;
        }
        try {
            event.clipboardData.setData("text/plain", datos.texto);
            event.clipboardData.setData("text/html", datos.html);
            event.clipboardData.setData(TIPO, datos.metadata);
        } catch {
            event.clipboardData.clearData();
            aviso.textContent = "No se pudo copiar la selección al portapapeles.";
            return;
        }
        event.preventDefault();
        const cantidad = seleccion.celdas.length;
        aviso.textContent = `${cantidad} ${cantidad === 1 ? "celda copiada" : "celdas copiadas"}.`;
    });
})();
