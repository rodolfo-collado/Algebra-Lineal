(() => {
    "use strict";

    // Navegación sin cajón: Inicio y las áreas en la cabecera (nav_areas.html), migas,
    // herramientas hermanas y el buscador de Inicio. Aquí solo quedan sus ayudas.
    const root = document.documentElement;

    // Un destino (#categoria) dentro de un desplegable cerrado se abre al llegar por la URL,
    // por ejemplo desde los breadcrumbs; sin esto el ancla apuntaría a contenido plegado.
    function revelarDestino() {
        let id;
        try {
            id = decodeURIComponent(window.location.hash.slice(1));
        } catch {
            return;
        }
        if (!id) return;
        let destino = document.getElementById(id);
        while (destino) {
            if (destino.tagName === "DETAILS") destino.open = true;
            destino = destino.parentElement;
        }
    }

    // En pantallas estrechas las herramientas hermanas son una fila desplazable: la actual
    // queda a la vista sin mover la página.
    const hermana = document.querySelector('.rail [aria-current="page"]');
    if (hermana) {
        const rail = hermana.closest(".rail");
        const a = hermana.getBoundingClientRect();
        const r = rail.getBoundingClientRect();
        rail.scrollLeft += a.left - r.left - (r.width - a.width) / 2;
    }

    window.addEventListener("hashchange", revelarDestino);
    revelarDestino();

    // La app de escritorio no tiene barra del navegador: Alt+←/→ recorren el historial
    // de WebView2 (los botones laterales del ratón ya lo hacen). En la web, el navegador decide.
    if (root.hasAttribute("data-desktop")) {
        document.addEventListener("keydown", (event) => {
            if (!event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
                event.isComposing || event.defaultPrevented) return;
            if (event.key === "ArrowLeft") history.back();
            else if (event.key === "ArrowRight") history.forward();
            else return;
            event.preventDefault();
        });
    }

    // Riel de BelugaCalc: el botón muestra u oculta los nombres de las áreas. Abierto aparta
    // el contenido (no lo tapa); se recuerda durante la visita, nunca entre aperturas.
    const plegar = document.getElementById("areas-plegar");
    if (plegar) {
        const sincronizar = () => plegar.setAttribute("aria-expanded", String(root.hasAttribute("data-riel-abierto")));
        plegar.hidden = false;
        plegar.addEventListener("click", () => {
            const abierto = !root.hasAttribute("data-riel-abierto");
            root.toggleAttribute("data-riel-abierto", abierto);
            try {
                sessionStorage.setItem("pygebra-riel", abierto ? "abierto" : "compacto");
            } catch (_) { /* Vale para esta página. */ }
            sincronizar();
        });
        sincronizar();
        // Una página restaurada del historial (bfcache) toma lo elegido en otra página.
        window.addEventListener("pageshow", (event) => {
            if (!event.persisted) return;
            let guardado = null;
            try { guardado = sessionStorage.getItem("pygebra-riel"); } catch (_) { /* Queda como estaba. */ }
            if (guardado) root.toggleAttribute("data-riel-abierto", guardado === "abierto");
            sincronizar();
        });
    }

    // Copias antiguas del estado del cajón retirado.
    try {
        localStorage.removeItem("algebra-lineal-menu-secciones");
        sessionStorage.removeItem("algebra-lineal-menu-secciones");
    } catch (_) { /* Sin almacenamiento no hay copia que retirar. */ }
})();
