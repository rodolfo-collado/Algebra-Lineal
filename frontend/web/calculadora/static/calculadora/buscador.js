(() => {
    "use strict";

    // Misma normalización que catalogo.normalizar: minúsculas y sin acentos.
    function terminosDe(texto) {
        return texto
            .normalize("NFD")
            .replace(/[̀-ͯ]/g, "")
            .toLowerCase()
            .split(/\s+/)
            .filter(Boolean);
    }

    function describir(visibles, consulta) {
        if (visibles === 0) return `Sin coincidencias para «${consulta}».`;
        if (visibles === 1) return "1 herramienta coincide.";
        return `${visibles} herramientas coinciden.`;
    }

    document.querySelectorAll("form[data-buscador]").forEach((form) => {
        const input = form.querySelector('input[type="search"]');
        const status = form.querySelector(".search-status");
        const lista = document.getElementById(form.dataset.buscador);
        if (!input || !lista) return;

        const items = Array.from(lista.querySelectorAll("[data-indice]"));
        const grupos = Array.from(lista.querySelectorAll("[data-grupo]"));
        let estadoInicial = new Map();
        let filtrando = false;

        function restaurar() {
            items.forEach((item) => { item.hidden = false; });
            grupos.forEach((grupo) => {
                grupo.hidden = false;
                if (grupo.tagName === "DETAILS") grupo.open = estadoInicial.get(grupo);
            });
            lista.removeAttribute("data-filtrando");
            filtrando = false;
        }

        function filtrar() {
            const consulta = input.value.trim();
            const terminos = terminosDe(consulta);
            if (terminos.length === 0) {
                if (filtrando) restaurar();
                if (status) status.textContent = "";
                return;
            }

            if (!filtrando) {
                // Se recuerda qué estaba abierto para devolverlo al limpiar la búsqueda.
                estadoInicial = new Map(
                    grupos.filter((g) => g.tagName === "DETAILS").map((g) => [g, g.open])
                );
                lista.setAttribute("data-filtrando", "");
                filtrando = true;
            }

            let visibles = 0;
            items.forEach((item) => {
                const indice = item.dataset.indice || "";
                const coincide = terminos.every((termino) => indice.includes(termino));
                item.hidden = !coincide;
                if (coincide) visibles += 1;
            });

            // De dentro hacia fuera: una categoría sin coincidencias se oculta y su área también.
            grupos.slice().reverse().forEach((grupo) => {
                const tiene = grupo.querySelector("[data-indice]:not([hidden])") !== null;
                grupo.hidden = !tiene;
                if (grupo.tagName === "DETAILS" && tiene) grupo.open = true;
            });

            if (status) status.textContent = describir(visibles, consulta);
        }

        input.addEventListener("input", filtrar);
        input.addEventListener("search", filtrar);
        if (input.value) filtrar();
    });
})();
