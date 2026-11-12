/* Piezas que comparten Newton-Raphson y Secante en la pizarra del paso activo: valores, fracciones
   apiladas y comprobación de la tolerancia, como nodos DOM pequeños (sin un motor de fórmulas).
   También carga los ejemplos (data-ejemplo) y lleva la función escrita al cambiar de método. */
"use strict";
window.metodosAbiertos = (() => {
    const subindice = k => String(k).replace(/\d/g, d => "₀₁₂₃₄₅₆₇₈₉"[d]);
    const nodo = (etiqueta, clase, ...hijos) => {
        const elemento = document.createElement(etiqueta);
        if (clase) elemento.className = clase;
        elemento.append(...hijos);
        return elemento;
    };
    const menos = texto => texto.replace(/^-/, "−");
    // Un número negativo dentro de una operación va entre paréntesis: 4 − (−2).
    const operando = texto => texto.startsWith("−") ? `(${texto})` : texto;
    // «=» si lo mostrado es exactamente el valor almacenado; si no, «≈».
    const relacion = (n, x) => Number(n(x)) === x ? "=" : "≈";
    // Apilada a la vista; lineal para lectores de pantalla.
    function fraccion(arriba, abajo) {
        const visual = nodo("span", "raices-fraccion", nodo("span", "", arriba), nodo("span", "", abajo));
        visual.setAttribute("aria-hidden", "true");
        return [nodo("span", "sr-only", `(${arriba})/(${abajo})`), visual];
    }
    const bloque = (titulo, ...contenido) => nodo("div", "abierto-bloque", nodo("p", "abierto-etiqueta", titulo), ...contenido);
    const valores = (pares, { n }) => nodo("dl", "abierto-valores", ...pares.map(([nombre, x]) => nodo("div", "",
        nodo("dt", "", nombre), nodo("dd", "", `${relacion(n, x)} ${menos(n(x))}`))));
    // Cada medida se compara con la tolerancia; el color solo acompaña a «cumple» / «no cumple».
    function comprobacion(medidas, tolerancia, { n }) {
        return nodo("ul", "abierto-comprobacion", ...medidas.map(([nombre, x]) => {
            const cumple = x <= tolerancia;
            const item = nodo("li", "", nodo("span", "", nombre),
                nodo("span", "abierto-linea", `${relacion(n, x)} ${menos(n(x))} ${cumple ? "≤" : ">"} ${n(tolerancia)} · `,
                    nodo("strong", "", cumple ? "cumple" : "no cumple")));
            item.dataset.cumple = cumple;
            return item;
        }));
    }
    // Una igualdad con fracción: el prefijo no se parte; si no cabe, la fracción baja entera al renglón siguiente.
    // El espacio queda fuera del prefijo: es el único punto donde la línea puede partirse.
    const linea = (prefijo, ...resto) => nodo("p", "abierto-linea", nodo("span", "abierto-prefijo", prefijo.trimEnd()), " ", ...resto);
    const nueva = (nombre, x, { n }) => nodo("p", "abierto-linea abierto-nueva", `${nombre} ${relacion(n, x)} `, nodo("strong", "", menos(n(x))));
    return { subindice, nodo, menos, operando, relacion, fraccion, bloque, valores, comprobacion, linea, nueva };
})();

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("raices-form");
    if (!form) return;
    // Ejemplos precargados: cada botón trae sus campos; los ajustes que no nombra vuelven a su valor inicial.
    document.querySelectorAll("[data-ejemplo]").forEach(boton => boton.addEventListener("click", () => {
        const campos = { precision: "0.0001", ...JSON.parse(boton.dataset.ejemplo) };
        for (const [nombre, valor] of Object.entries(campos)) {
            const campo = form.elements.namedItem(nombre);
            if (!campo) continue;
            campo.value = valor;
            campo.dispatchEvent(new Event("input", { bubbles: true }));
        }
        document.getElementById("grafica-estado").textContent = "Ejemplo cargado. Puedes modificarlo o resolver.";
    }));
    // Cambiar de método conserva la función escrita: el otro método la recibe como ?funcion=…
    const funcion = form.elements.namedItem("funcion");
    const enlaces = [...document.querySelectorAll("[data-metodo-abierto]")];
    const actualizar = () => enlaces.forEach(enlace => {
        const destino = new URL(enlace.href, window.location.href);
        destino.search = funcion.value.trim() ? new URLSearchParams({ funcion: funcion.value.trim() }) : "";
        enlace.href = destino.pathname + destino.search;
    });
    funcion.addEventListener("input", actualizar);
    actualizar();
});
