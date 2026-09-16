(() => {
    "use strict";

    const root = document.querySelector("[data-conversion-bases]");
    if (!root) return;

    const origen = root.querySelector('select[name="base_origen"]');
    const destino = root.querySelector('select[name="base_destino"]');
    const campo = root.querySelector('input[name="numero"]');
    const intercambiar = root.querySelector("[data-intercambiar-bases]");
    const aviso = root.querySelector("[data-validacion-cliente]");
    const teclados = root.querySelectorAll("[data-teclado-base]");
    const etiquetasNumero = root.querySelectorAll("[data-number-label-base]");
    if (!origen || !destino || !campo) return;

    let origenAnterior = origen.value;
    let destinoAnterior = destino.value;

    function bloqueActivo() {
        return Array.from(teclados).find((bloque) => bloque.dataset.tecladoBase === origen.value) || null;
    }

    // Los dígitos válidos salen de las teclas del teclado activo: una sola fuente de verdad.
    function digitosValidos() {
        const bloque = bloqueActivo();
        if (!bloque) return null;
        return new Set(Array.from(bloque.querySelectorAll("button[data-insercion]"), (tecla) => tecla.dataset.insercion));
    }

    function mensajeInvalido(texto) {
        const bloque = bloqueActivo();
        const validos = digitosValidos();
        if (!bloque || !validos) return "";
        const limpio = texto.trim();
        if (!limpio) return "";
        if (limpio[0] === "+" || limpio[0] === "-") {
            return "Este módulo convierte solo números enteros no negativos.";
        }
        if (/\s/.test(limpio)) return "El número no debe contener espacios en medio.";
        for (const caracter of limpio) {
            const simbolo = caracter.toUpperCase();
            if (validos.has(simbolo)) continue;
            if (origen.value === "16") return `${simbolo} no es un dígito hexadecimal válido.`;
            return `El dígito ${caracter} no es válido en un número ${bloque.dataset.nombreBase}.`;
        }
        return "";
    }

    function validar() {
        if (!aviso) return;
        const mensaje = mensajeInvalido(campo.value);
        aviso.textContent = mensaje;
        aviso.hidden = !mensaje;
        if (mensaje) {
            campo.setAttribute("aria-invalid", "true");
        } else {
            campo.removeAttribute("aria-invalid");
        }
    }

    // Una base no puede ser origen y destino a la vez: se apaga en el otro selector.
    function sincronizarOpciones() {
        Array.from(destino.options).forEach((opcion) => { opcion.disabled = opcion.value === origen.value; });
        Array.from(origen.options).forEach((opcion) => { opcion.disabled = opcion.value === destino.value; });
    }

    function actualizar() {
        teclados.forEach((bloque) => {
            const corresponde = bloque.dataset.tecladoBase === origen.value;
            bloque.hidden = !corresponde;
            // El teclado interno nace hidden hasta que teclado.js lo revela;
            // al cambiar de base hay que volver a mostrar el contenedor activo.
            const teclado = bloque.querySelector(".math-keyboard");
            if (teclado && corresponde) teclado.hidden = false;
        });
        etiquetasNumero.forEach((etiqueta) => {
            etiqueta.hidden = etiqueta.dataset.numberLabelBase !== origen.value;
        });
        sincronizarOpciones();
        validar();
    }

    origen.addEventListener("change", () => {
        // Elegir como origen la base de destino equivale a intercambiarlas.
        if (origen.value === destino.value) destino.value = origenAnterior;
        origenAnterior = origen.value;
        destinoAnterior = destino.value;
        actualizar();
    });

    destino.addEventListener("change", () => {
        if (destino.value === origen.value) origen.value = destinoAnterior;
        origenAnterior = origen.value;
        destinoAnterior = destino.value;
        actualizar();
    });

    if (intercambiar) {
        intercambiar.hidden = false;
        intercambiar.addEventListener("click", () => {
            const valorOrigen = origen.value;
            origen.value = destino.value;
            destino.value = valorOrigen;
            origenAnterior = origen.value;
            destinoAnterior = destino.value;
            actualizar();
            campo.focus();
        });
    }

    campo.addEventListener("input", validar);
    actualizar();
})();
