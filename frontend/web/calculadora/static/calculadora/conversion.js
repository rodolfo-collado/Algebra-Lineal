(() => {
    "use strict";

    const root = document.querySelector("[data-conversion-bases]");
    if (!root) return;

    const origen = root.querySelector('select[name="base_origen"]');
    const campo = root.querySelector('input[name="numero"]');
    const destinos = root.querySelectorAll('input[name="bases_destino"]');
    const aviso = root.querySelector("[data-validacion-cliente]");
    const avisoDestinos = root.querySelector("[data-validacion-destinos]");
    const datos = document.getElementById("bases-digitos");
    const contexto = campo?.closest("[data-perfil]");
    const etiquetasNumero = root.querySelectorAll("[data-number-label-base]");
    if (!origen || !campo || !destinos.length || !datos || !contexto) return;
    const bases = JSON.parse(datos.textContent);

    function mensajeInvalido(texto) {
        const base = bases[origen.value];
        if (!base) return "";
        const validos = new Set(base.digitos);
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
            return `El dígito ${caracter} no es válido en un número ${base.nombre}.`;
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

    // Hace falta al menos un destino; el servidor lo vuelve a comprobar al convertir.
    function validarDestinos() {
        if (!avisoDestinos) return;
        const alguno = Array.from(destinos).some((casilla) => !casilla.disabled && casilla.checked);
        avisoDestinos.textContent = alguno ? "" : "Elige al menos una base de destino.";
        avisoDestinos.hidden = alguno;
    }

    // La base de origen nunca es destino: su casilla se apaga, se desmarca y se oculta.
    function sincronizarDestinos() {
        destinos.forEach((casilla) => {
            const esOrigen = casilla.value === origen.value;
            casilla.disabled = esOrigen;
            if (esOrigen) casilla.checked = false;
            const opcion = casilla.closest("[data-destino-base]");
            if (opcion) opcion.hidden = esOrigen;
        });
    }

    function actualizar() {
        if (bases[origen.value]) contexto.dataset.perfil = bases[origen.value].perfil;
        etiquetasNumero.forEach((etiqueta) => {
            etiqueta.hidden = etiqueta.dataset.numberLabelBase !== origen.value;
        });
        sincronizarDestinos();
        validar();
    }

    // El aviso de destinos solo aparece tras interactuar: al cargar, el error lo pone el servidor.
    origen.addEventListener("change", () => {
        actualizar();
        validarDestinos();
    });
    destinos.forEach((casilla) => casilla.addEventListener("change", validarDestinos));
    campo.addEventListener("input", validar);
    actualizar();
})();
