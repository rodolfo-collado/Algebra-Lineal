(() => {
    "use strict";

    const datos = document.getElementById("datos-buscador");
    if (!datos) return;
    const { palabras_vacias: vacias, herramientas, separador } = JSON.parse(datos.textContent);
    const ignoradas = new Set(vacias);
    const espacios = new RegExp(separador, "u");

    // catalogo.normalizar / terminos_de: NFD, sin marcas, minúsculas y términos por espacios.
    function terminosDe(texto) {
        return texto.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase()
            .split(espacios).filter((t) => t && !ignoradas.has(t));
    }

    function buscar(consulta) {
        const terminos = terminosDe(consulta);
        if (!terminos.length) return [];
        return herramientas.map((h, orden) => ({ ...h, orden,
            aciertos: terminos.filter((t) => h.nombre.includes(t)).length,
        })).filter((h) => terminos.every((t) => h.indice.includes(t)))
            .sort((a, b) => Number(b.disponible) - Number(a.disponible)
                || b.aciertos - a.aciertos || a.orden - b.orden);
    }

    document.querySelectorAll("form[data-buscador]").forEach((form) => {
        const input = form.querySelector('input[type="search"]');
        const status = form.querySelector(".search-status");
        const sugerencias = form.querySelector("[data-busqueda-sugerencias]");
        const lista = document.getElementById(form.dataset.buscador);
        if (!input || !lista) return;

        const principal = form.hasAttribute("data-buscador-inicio");
        // Al enfocar resultados, las sugerencias vacías quedan en el recorrido de lectura.
        if (principal) lista.before(sugerencias);
        const servidor = principal ? document.querySelector("[data-busqueda-servidor]") : null;
        const originales = Array.from(lista.querySelectorAll("[data-herramienta]")).map((item) => ({
            item, padre: item.parentElement, oculto: item.hidden,
        }));
        const porId = new Map(originales.map(({ item }) => [item.dataset.herramienta, item]));
        const grupos = Array.from(lista.querySelectorAll("[data-grupo]"));
        const ocultos = new Map(grupos.map((g) => [g, g.hidden]));
        const sugerenciasIniciales = sugerencias.hidden;
        let abiertos = new Map();
        let filtrando = false;
        let resultados = lista;

        if (principal && grupos.length) {
            // Se trasladan las mismas filas para poder respetar el orden global del GET.
            resultados = document.createElement("ul");
            resultados.className = "tool-list";
            resultados.hidden = true;
            lista.append(resultados);
        }

        function restaurar() {
            originales.forEach(({ item, padre, oculto }) => {
                padre.append(item);
                item.hidden = oculto;
            });
            grupos.forEach((grupo) => {
                grupo.hidden = ocultos.get(grupo);
                if (grupo.tagName === "DETAILS") grupo.open = abiertos.get(grupo);
            });
            if (resultados !== lista) resultados.hidden = true;
            lista.removeAttribute("data-filtrando");
            filtrando = false;
        }

        function filtrar() {
            const consulta = input.value.split(espacios).filter(Boolean).join(" ");
            const original = principal && input.value === input.defaultValue;
            if (original || (!principal && !consulta)) {
                if (filtrando) restaurar();
                if (servidor) servidor.hidden = false;
                status.textContent = "";
                sugerencias.hidden = sugerenciasIniciales;
                return;
            }

            if (!filtrando) {
                // La memoria se captura al empezar, después de navigation.js.
                abiertos = new Map(grupos.map((g) => [g, g.open]));
                lista.setAttribute("data-filtrando", "");
                filtrando = true;
            }

            const coincidencias = consulta ? buscar(consulta) : herramientas;
            const ids = new Set(coincidencias.map((h) => h.id));
            originales.forEach(({ item }) => { item.hidden = !ids.has(item.dataset.herramienta); });

            if (principal) {
                originales.forEach(({ item }) => resultados.append(item));
                coincidencias.forEach((h) => resultados.append(porId.get(h.id)));
                grupos.forEach((g) => { g.hidden = true; });
                resultados.hidden = false;
                servidor.hidden = true;
            } else {
                // El Menú conserva el árbol; abre solo los grupos con coincidencias.
                grupos.slice().reverse().forEach((grupo) => {
                    const tiene = grupo.querySelector("[data-herramienta]:not([hidden])") !== null;
                    grupo.hidden = !tiene;
                    if (grupo.tagName === "DETAILS" && tiene) grupo.open = true;
                });
            }
            const cantidad = coincidencias.length;
            status.textContent = !consulta ? "Explora las herramientas."
                : cantidad === 0 ? `Sin coincidencias para «${consulta}».`
                : `${cantidad} herramienta${cantidad === 1 ? " coincide" : "s coinciden"} con «${consulta}».`;
            sugerencias.hidden = !consulta || cantidad !== 0;
        }

        input.addEventListener("input", filtrar);
        input.addEventListener("search", filtrar);
        if (!principal) input.addEventListener("keydown", (event) => {
            if (event.key !== "Escape" || !input.value) return;
            event.preventDefault();
            event.stopPropagation();
            input.value = "";
            filtrar();
        });
    });

    const llegada = document.querySelector("[data-busqueda-get]");
    if (llegada) llegada.focus();
})();
