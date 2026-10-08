(() => {
    "use strict";

    const STORAGE_SECCIONES = "algebra-lineal-menu-secciones";
    const root = document.documentElement;
    const button = document.getElementById("navigation-toggle");
    const sidebar = document.getElementById("navegacion-principal");
    const backdrop = document.getElementById("sidebar-backdrop");
    const closeButton = document.getElementById("sidebar-close");
    const main = document.getElementById("contenido");

    // Un destino (#categoria) dentro de un desplegable cerrado se abre al llegar por la URL,
    // por ejemplo desde los breadcrumbs; sin esto el ancla apuntaría a contenido plegado.
    function revelarDestino() {
        const id = decodeURIComponent(window.location.hash.slice(1));
        if (!id) return;
        let destino = document.getElementById(id);
        while (destino) {
            if (destino.tagName === "DETAILS") destino.open = true;
            destino = destino.parentElement;
        }
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

    if (!button || !sidebar) return;

    // La navegación es un cajón sobre el contenido en cualquier tamaño de pantalla:
    // nace cerrado y un solo botón lo abre y lo cierra.
    let abierto = false;

    // Las categorías abiertas se recuerdan durante la ejecución (sessionStorage), nunca
    // entre aperturas; se retira la copia persistente que guardaban versiones anteriores.
    function leer(clave) {
        try {
            return sessionStorage.getItem(clave);
        } catch (error) {
            return null;
        }
    }

    function guardar(clave, valor) {
        try {
            sessionStorage.setItem(clave, valor);
        } catch (error) {
            // Sin almacenamiento disponible el menú sigue funcionando; solo no recuerda.
        }
    }

    try {
        localStorage.removeItem(STORAGE_SECCIONES);
    } catch (error) {
        // Sin almacenamiento no hay copia antigua que retirar.
    }

    function aplicar() {
        root.toggleAttribute("data-drawer", abierto);
        sidebar.hidden = !abierto;
        if (backdrop) backdrop.hidden = !abierto;
        if (main) main.inert = abierto;
        button.setAttribute("aria-expanded", String(abierto));
    }

    function abrir() {
        abierto = true;
        aplicar();
        // El foco va al primer enlace y no al buscador: en móvil evitaría que el
        // teclado virtual tape el menú recién abierto.
        const primero = sidebar.querySelector(".nav-link");
        if (primero) primero.focus();
    }

    function cerrar() {
        if (!abierto) return;
        abierto = false;
        aplicar();
        button.focus();
    }

    button.hidden = false;
    button.addEventListener("click", () => {
        if (abierto) cerrar();
        else abrir();
    });
    if (closeButton) {
        closeButton.hidden = false;
        closeButton.addEventListener("click", cerrar);
    }
    if (backdrop) backdrop.addEventListener("click", cerrar);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && abierto && !event.defaultPrevented) cerrar();
    });
    // Una página restaurada del historial (bfcache) vuelve con el cajón cerrado y el
    // contenido usable; el foco no queda dentro del cajón oculto.
    window.addEventListener("pageshow", (event) => {
        if (!event.persisted) return;
        const foco = sidebar.contains(document.activeElement);
        abierto = false;
        aplicar();
        if (foco) button.focus();
    });

    // Las categorías abiertas por el usuario se recuerdan; la categoría activa
    // siempre llega abierta desde el servidor.
    const categorias = Array.from(sidebar.querySelectorAll("details[data-categoria]"));
    let abiertas = new Set();
    try {
        abiertas = new Set(JSON.parse(leer(STORAGE_SECCIONES) || "[]"));
    } catch (error) {
        abiertas = new Set();
    }
    categorias.forEach((categoria) => {
        if (abiertas.has(categoria.dataset.categoria)) categoria.open = true;
        categoria.addEventListener("toggle", () => {
            // El filtro del buscador abre categorías por su cuenta; eso no se guarda.
            if (sidebar.querySelector("[data-filtrando]")) return;
            if (categoria.open) abiertas.add(categoria.dataset.categoria);
            else abiertas.delete(categoria.dataset.categoria);
            guardar(STORAGE_SECCIONES, JSON.stringify(Array.from(abiertas)));
        });
    });

    aplicar();
})();
